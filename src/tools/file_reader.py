"""File reader tool — reads text from local paths or remote URLs.

Approach B tool — the LLM decides when to call it.  Supports PDF, DOCX,
plain text, and HTML, accepting either a local filesystem path or an
HTTP(S) URL.

Security: extracted content is sanitised and truncated before being
injected into the LLM context to mitigate indirect prompt injection.
The returned text is explicitly framed as source material, not as
instructions, to reduce the risk of injected directives being acted on.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from pathlib import Path

import docx
import pypdf
import trafilatura

from src.tools.registry import REGISTRY, ToolDefinition
from src.tools.url_reader import _sanitise, _validate_url

_MAX_CONTENT = 4000

_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "path_or_url": {
            "type": "string",
            "description": (
                "Local filesystem path or HTTP(S) URL of the file to read. "
                "Supported formats: PDF, DOCX, TXT, HTML."
            ),
        }
    },
    "required": ["path_or_url"],
    "additionalProperties": False,
}

_TEXT_EXTENSIONS = {".txt", ".text", ".md", ".rst", ".csv", ".log"}
_HTML_EXTENSIONS = {".htm", ".html", ".xhtml"}
_PDF_EXTENSIONS = {".pdf"}
_DOCX_EXTENSIONS = {".docx", ".doc"}


def _read_pdf_bytes(data: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    import io

    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _read_docx_bytes(data: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    import io

    doc = docx.Document(io.BytesIO(data))
    return "\n".join(para.text for para in doc.paragraphs)


def _read_local(path: str) -> str:
    """Read text content from a local filesystem path.

    Args:
        path: Absolute or relative filesystem path.

    Returns:
        Extracted text string, or an error message.
    """
    p = Path(path)
    if not p.exists():
        return f"File not found: {path!r}"
    if not p.is_file():
        return f"Not a file: {path!r}"

    suffix = p.suffix.lower()
    try:
        if suffix in _PDF_EXTENSIONS:
            return _read_pdf_bytes(p.read_bytes())
        if suffix in _DOCX_EXTENSIONS:
            return _read_docx_bytes(p.read_bytes())
        if suffix in _HTML_EXTENSIONS:
            html = p.read_text(encoding="utf-8", errors="replace")
            text = trafilatura.extract(html) or ""
            return text
        # Plain text (and any unknown extension)
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logging.warning("Local file read failed for %r: %s", path, exc)
        return f"(Read error: {exc})"


def _read_remote(url: str) -> str:
    """Download and extract text from a remote URL.

    HTML is extracted with trafilatura.  PDF, DOCX, and TXT are
    downloaded to a temporary file then parsed.

    Args:
        url: A validated HTTP(S) URL.

    Returns:
        Extracted text string, or an error message.
    """
    suffix = Path(url.split("?")[0]).suffix.lower()

    # HTML — let trafilatura handle the full fetch + extraction
    if suffix in _HTML_EXTENSIONS or suffix not in (
        _PDF_EXTENSIONS | _DOCX_EXTENSIONS | _TEXT_EXTENSIONS
    ):
        try:
            downloaded = trafilatura.fetch_url(url)
        except Exception as exc:
            return f"(URL fetch error: {exc})"
        if not downloaded:
            return f"Could not fetch content from {url!r}"
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        return text or f"No readable text could be extracted from {url!r}"

    # Non-HTML: download to temp file and parse
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310
            data = resp.read()
    except Exception as exc:
        logging.warning("Remote file download failed for %r: %s", url, exc)
        return f"(Download error: {exc})"

    try:
        if suffix in _PDF_EXTENSIONS:
            return _read_pdf_bytes(data)
        if suffix in _DOCX_EXTENSIONS:
            return _read_docx_bytes(data)
        # Plain text
        return data.decode("utf-8", errors="replace")
    except Exception as exc:
        logging.warning("Remote file parse failed for %r: %s", url, exc)
        return f"(Parse error: {exc})"


def read_file(path_or_url: str) -> str:
    """Read text content from a local path or remote URL.

    Detects whether the input is a URL (http/https) or a local path,
    dispatches to the appropriate reader, then sanitises and truncates
    the result before returning it framed as source material.

    Args:
        path_or_url: A local filesystem path or an HTTP(S) URL.

    Returns:
        Framed content string ready for LLM context injection, or an
        error message if the file could not be read.
    """
    source = path_or_url.strip()
    validated_url = _validate_url(source)

    if validated_url:
        raw = _read_remote(validated_url)
        label = validated_url
    else:
        raw = _read_local(source)
        label = source

    _err_prefixes = ("(", "File not found", "Not a file")
    if any(raw.startswith(p) for p in _err_prefixes):
        return raw  # propagate error messages unchanged

    content = _sanitise(raw, _MAX_CONTENT)
    if not content:
        return f"No readable text could be extracted from {label!r}"

    return f"Content from {label}:\n\n{content}\n\n(Source: {label})"


def _file_reader_callable(args_json: str) -> str | None:
    """Approach B callable — parses JSON args and calls read_file.

    Args:
        args_json: JSON string with a ``path_or_url`` key.

    Returns:
        Extracted content string, or ``None`` if arguments are invalid.
    """
    try:
        args = json.loads(args_json)
        path_or_url = args.get("path_or_url", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return None

    if not path_or_url:
        return None

    return read_file(path_or_url)


REGISTRY.register(
    ToolDefinition(
        name="file_reader",
        router_tier="file_reader",
        label="Tool: File reader",
        description=(
            "read the text content of a local file or remote URL "
            "(PDF, DOCX, TXT, or HTML)"
        ),
        examples=[
            "read this PDF: /home/user/report.pdf",
            "summarise the contents of https://example.com/doc.pdf",
            "what does my_notes.txt say",
            "extract text from https://example.com/paper.docx",
        ],
        default_enabled=True,
        min_tier="advanced_llm",
        approach="B",
        callable=_file_reader_callable,
        category="files",
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)

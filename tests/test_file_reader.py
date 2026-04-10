"""Unit tests for the file_reader tool.

All I/O and network calls are mocked; no filesystem or HTTP access occurs.
"""

import json
from unittest.mock import MagicMock, patch

from src.tools.file_reader import (
    _file_reader_callable,
    _read_docx_bytes,
    _read_local,
    _read_pdf_bytes,
    _read_remote,
    read_file,
)
from src.tools.registry import REGISTRY

# ---------------------------------------------------------------------------
# PDF byte parsing
# ---------------------------------------------------------------------------


class TestReadPdfBytes:
    def test_extracts_text_from_pages(self):
        page1 = MagicMock()
        page1.extract_text.return_value = "Page one text."
        page2 = MagicMock()
        page2.extract_text.return_value = "Page two text."
        mock_reader = MagicMock()
        mock_reader.pages = [page1, page2]

        with patch("src.tools.file_reader.pypdf") as mock_pypdf:
            mock_pypdf.PdfReader.return_value = mock_reader
            result = _read_pdf_bytes(b"fake-pdf")

        assert "Page one text." in result
        assert "Page two text." in result

    def test_handles_empty_page(self):
        page = MagicMock()
        page.extract_text.return_value = None
        mock_reader = MagicMock()
        mock_reader.pages = [page]

        with patch("src.tools.file_reader.pypdf") as mock_pypdf:
            mock_pypdf.PdfReader.return_value = mock_reader
            result = _read_pdf_bytes(b"fake-pdf")

        assert result == ""


# ---------------------------------------------------------------------------
# DOCX byte parsing
# ---------------------------------------------------------------------------


class TestReadDocxBytes:
    def test_extracts_paragraph_text(self):
        para1 = MagicMock()
        para1.text = "First paragraph."
        para2 = MagicMock()
        para2.text = "Second paragraph."
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para1, para2]

        with patch("src.tools.file_reader.docx") as mock_docx:
            mock_docx.Document.return_value = mock_doc
            result = _read_docx_bytes(b"fake-docx")

        assert "First paragraph." in result
        assert "Second paragraph." in result

    def test_empty_document(self):
        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        with patch("src.tools.file_reader.docx") as mock_docx:
            mock_docx.Document.return_value = mock_doc
            result = _read_docx_bytes(b"fake-docx")

        assert result == ""


# ---------------------------------------------------------------------------
# Local file reading
# ---------------------------------------------------------------------------


class TestReadLocal:
    def test_reads_txt_file(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("Hello world.", encoding="utf-8")
        result = _read_local(str(f))
        assert "Hello world." in result

    def test_missing_file_returns_error(self):
        result = _read_local("/nonexistent/path/file.txt")
        assert "not found" in result.lower()

    def test_directory_returns_error(self, tmp_path):
        result = _read_local(str(tmp_path))
        assert "not a file" in result.lower()

    def test_reads_pdf_local(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"fake-pdf-content")
        page = MagicMock()
        page.extract_text.return_value = "PDF content"
        mock_reader = MagicMock()
        mock_reader.pages = [page]
        with patch("src.tools.file_reader.pypdf") as mock_pypdf:
            mock_pypdf.PdfReader.return_value = mock_reader
            result = _read_local(str(f))
        assert "PDF content" in result

    def test_reads_docx_local(self, tmp_path):
        f = tmp_path / "doc.docx"
        f.write_bytes(b"fake-docx-content")
        para = MagicMock()
        para.text = "DOCX content"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para]
        with patch("src.tools.file_reader.docx") as mock_docx:
            mock_docx.Document.return_value = mock_doc
            result = _read_local(str(f))
        assert "DOCX content" in result

    def test_reads_html_local(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_text(
            "<html><body><p>HTML content</p></body></html>",
            encoding="utf-8",
        )
        with patch("src.tools.file_reader.trafilatura") as mock_traf:
            mock_traf.extract.return_value = "HTML content"
            result = _read_local(str(f))
        assert "HTML content" in result

    def test_read_error_returns_message(self, tmp_path):
        f = tmp_path / "bad.pdf"
        f.write_bytes(b"bad-pdf")
        with patch("src.tools.file_reader.pypdf") as mock_pypdf:
            mock_pypdf.PdfReader.side_effect = Exception("corrupt")
            result = _read_local(str(f))
        assert "Read error" in result


# ---------------------------------------------------------------------------
# Remote file reading
# ---------------------------------------------------------------------------


class TestReadRemote:
    def test_fetches_html_via_trafilatura(self):
        with patch("src.tools.file_reader.trafilatura") as mock_traf:
            mock_traf.fetch_url.return_value = "<html>content</html>"
            mock_traf.extract.return_value = "Extracted text"
            result = _read_remote("https://example.com/page.html")
        assert "Extracted text" in result

    def test_html_fetch_failure(self):
        with patch("src.tools.file_reader.trafilatura") as mock_traf:
            mock_traf.fetch_url.side_effect = Exception("timeout")
            result = _read_remote("https://example.com/page.html")
        assert "URL fetch error" in result

    def test_unknown_extension_treated_as_html(self):
        with patch("src.tools.file_reader.trafilatura") as mock_traf:
            mock_traf.fetch_url.return_value = "<html>something</html>"
            mock_traf.extract.return_value = "some text"
            result = _read_remote("https://example.com/resource")
        assert "some text" in result

    def test_downloads_pdf_remote(self):
        page = MagicMock()
        page.extract_text.return_value = "Remote PDF"
        mock_reader = MagicMock()
        mock_reader.pages = [page]
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"pdf-bytes"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with (
            patch("urllib.request.urlopen", return_value=mock_resp),
            patch("src.tools.file_reader.pypdf") as mock_pypdf,
        ):
            mock_pypdf.PdfReader.return_value = mock_reader
            result = _read_remote("https://example.com/report.pdf")
        assert "Remote PDF" in result

    def test_download_error_returns_message(self):
        with patch(
            "urllib.request.urlopen", side_effect=OSError("connection refused")
        ):
            result = _read_remote("https://example.com/file.pdf")
        assert "Download error" in result

    def test_no_text_extracted_from_html(self):
        with patch("src.tools.file_reader.trafilatura") as mock_traf:
            mock_traf.fetch_url.return_value = "<html></html>"
            mock_traf.extract.return_value = None
            result = _read_remote("https://example.com/empty.html")
        assert "No readable text" in result


# ---------------------------------------------------------------------------
# read_file — integration of local + remote paths
# ---------------------------------------------------------------------------


class TestReadFile:
    def test_routes_url_to_remote(self):
        with patch(
            "src.tools.file_reader._read_remote", return_value="Remote"
        ) as m:
            result = read_file("https://example.com/doc.txt")
        m.assert_called_once()
        assert "Remote" in result

    def test_routes_local_path(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Local content", encoding="utf-8")
        result = read_file(str(f))
        assert "Local content" in result

    def test_output_is_framed(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Body text", encoding="utf-8")
        result = read_file(str(f))
        assert "Content from" in result
        assert "(Source:" in result

    def test_output_truncated_to_max(self, tmp_path):
        f = tmp_path / "long.txt"
        f.write_text("x" * 10_000, encoding="utf-8")
        result = read_file(str(f))
        # Should not include all 10k chars
        assert len(result) < 6000

    def test_propagates_error_messages(self):
        result = read_file("/nonexistent/file.txt")
        assert "not found" in result.lower()


# ---------------------------------------------------------------------------
# Callable (JSON arg parsing)
# ---------------------------------------------------------------------------


class TestFileReaderCallable:
    def test_valid_args(self, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("Hello", encoding="utf-8")
        result = _file_reader_callable(json.dumps({"path_or_url": str(f)}))
        assert result is not None
        assert "Hello" in result

    def test_empty_path_returns_none(self):
        result = _file_reader_callable(json.dumps({"path_or_url": ""}))
        assert result is None

    def test_missing_key_returns_none(self):
        result = _file_reader_callable(json.dumps({}))
        assert result is None

    def test_invalid_json_returns_none(self):
        result = _file_reader_callable("not-json")
        assert result is None


# ---------------------------------------------------------------------------
# Registry registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_tool_is_registered(self):
        names = [t.name for t in REGISTRY.all()]
        assert "file_reader" in names

    def test_default_enabled(self):
        tool = next(t for t in REGISTRY.all() if t.name == "file_reader")
        assert tool.default_enabled is True

    def test_approach_b(self):
        tool = next(t for t in REGISTRY.all() if t.name == "file_reader")
        assert tool.approach == "B"

    def test_parameters_schema_has_required_key(self):
        tool = next(t for t in REGISTRY.all() if t.name == "file_reader")
        assert "path_or_url" in tool.parameters_schema["properties"]
        assert "path_or_url" in tool.parameters_schema["required"]

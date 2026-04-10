"""Data analysis tool — CSV/Excel summarisation and charting.

Approach B tool — the LLM decides when to call it.  Reads a CSV or Excel
file from a local path or HTTP(S) URL, then either:

  * ``summarise`` — returns shape, column types, descriptive statistics, and
    the first five rows as plain text.
  * ``plot`` — generates a bar, line, scatter, or histogram chart as a PNG
    image returned via the __IMAGE__: sentinel.

Uses Polars for fast data loading and matplotlib (Agg backend, no display)
for chart rendering.
"""

from __future__ import annotations

import io
import json
import logging
import tempfile
import urllib.request
from pathlib import Path

import matplotlib

# Non-interactive backend — must be set before pyplot import.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import polars as pl
from PIL import Image

from src.tools.image_utils import encode_image
from src.tools.registry import REGISTRY, ToolDefinition
from src.tools.url_reader import _validate_url

_MAX_SUMMARY_LEN = 3000
_CHART_TYPES = {"bar", "line", "scatter", "histogram"}

_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "path_or_url": {
            "type": "string",
            "description": (
                "Local filesystem path or HTTP(S) URL of a CSV or Excel file."
            ),
        },
        "action": {
            "type": "string",
            "enum": ["summarise", "plot"],
            "description": (
                "'summarise' returns statistics and a preview of the data. "
                "'plot' generates a chart image."
            ),
        },
        "chart_type": {
            "type": "string",
            "enum": ["bar", "line", "scatter", "histogram"],
            "description": "Chart style. Required when action='plot'.",
        },
        "x_col": {
            "type": "string",
            "description": (
                "Column name for the x-axis. Required when action='plot'."
            ),
        },
        "y_col": {
            "type": "string",
            "description": (
                "Column name for the y-axis. "
                "Required when action='plot' except for histogram."
            ),
        },
        "title": {
            "type": "string",
            "description": "Optional chart title.",
        },
    },
    "required": ["path_or_url", "action"],
    "additionalProperties": False,
}


def _load_dataframe(path_or_url: str) -> pl.DataFrame:
    """Load a CSV or Excel file into a Polars DataFrame.

    Downloads remote files to a temporary path before loading.

    Args:
        path_or_url: A local path or HTTP(S) URL to a CSV or Excel file.

    Returns:
        A Polars DataFrame.

    Raises:
        ValueError: If the file extension is unsupported.
        Exception: On download or parse failure.
    """
    validated_url = _validate_url(path_or_url)
    if validated_url:
        suffix = Path(path_or_url.split("?")[0]).suffix.lower()
        with urllib.request.urlopen(validated_url, timeout=20) as resp:  # noqa: S310
            data = resp.read()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        source = tmp_path
    else:
        source = path_or_url
        suffix = Path(source).suffix.lower()

    if suffix in (".xlsx", ".xls"):
        return pl.read_excel(source)
    if suffix == ".csv":
        return pl.read_csv(source)
    raise ValueError(
        f"Unsupported file type {suffix!r}. Use .csv, .xlsx, or .xls."
    )


def _summarise(df: pl.DataFrame, source: str) -> str:
    """Return a plain-text statistical summary of a DataFrame.

    Args:
        df: The loaded Polars DataFrame.
        source: The original path or URL, used in the header.

    Returns:
        A multi-line string summary truncated to ``_MAX_SUMMARY_LEN`` chars.
    """
    lines = [
        f"Data from: {source}",
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        "",
        "Column types:",
    ]
    for name, dtype in zip(df.columns, df.dtypes, strict=True):
        lines.append(f"  {name}: {dtype}")

    lines.append("")
    lines.append("Descriptive statistics:")
    lines.append(str(df.describe()))

    lines.append("")
    lines.append("First 5 rows:")
    lines.append(str(df.head(5)))

    text = "\n".join(lines)
    if len(text) > _MAX_SUMMARY_LEN:
        text = text[:_MAX_SUMMARY_LEN].rstrip() + "\u2026"
    return text


def _plot(
    df: pl.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str | None,
    title: str,
) -> bytes:
    """Render a chart from a DataFrame and return image sentinel bytes.

    Args:
        df: The loaded Polars DataFrame.
        chart_type: One of ``"bar"``, ``"line"``, ``"scatter"``,
          ``"histogram"``.
        x_col: Column name for the x-axis (or the data column for histogram).
        y_col: Column name for the y-axis (not used for histogram).
        title: Chart title.

    Returns:
        ``__IMAGE__:`` sentinel bytes wrapping a PNG.

    Raises:
        ValueError: If required columns are missing from the DataFrame.
        KeyError: If a requested column does not exist.
    """
    if x_col not in df.columns:
        raise ValueError(f"Column {x_col!r} not found. Available: {df.columns}")
    if chart_type != "histogram" and y_col and y_col not in df.columns:
        raise ValueError(f"Column {y_col!r} not found. Available: {df.columns}")

    fig, ax = plt.subplots(figsize=(8, 5))

    x_data = df[x_col].to_list()

    if chart_type == "histogram":
        ax.hist(x_data, bins="auto")
        ax.set_xlabel(x_col)
        ax.set_ylabel("Frequency")
    elif chart_type == "bar":
        y_data = df[y_col].to_list()
        ax.bar([str(v) for v in x_data], y_data)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
    elif chart_type == "line":
        y_data = df[y_col].to_list()
        ax.plot(x_data, y_data)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
    elif chart_type == "scatter":
        y_data = df[y_col].to_list()
        ax.scatter(x_data, y_data)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)

    ax.set_title(title or f"{chart_type.capitalize()} chart")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf)
    return encode_image(img)


def _data_analysis_callable(args_json: str) -> bytes | str:
    """Approach B callable — parses JSON args and runs summarise or plot.

    Args:
        args_json: JSON string with at least ``path_or_url`` and ``action``.

    Returns:
        A plain-text summary string, ``__IMAGE__:`` sentinel bytes for a
        plot, or an error string.
    """
    try:
        args = json.loads(args_json)
    except (json.JSONDecodeError, AttributeError):
        return "Error: invalid arguments for data_analysis tool."

    path_or_url = args.get("path_or_url", "").strip()
    action = args.get("action", "").strip()

    if not path_or_url:
        return "Error: path_or_url is required."
    if action not in ("summarise", "plot"):
        return "Error: action must be 'summarise' or 'plot'."

    try:
        df = _load_dataframe(path_or_url)
    except Exception as exc:
        logging.warning("Data load failed for %r: %s", path_or_url, exc)
        return f"Could not load data from {path_or_url!r}: {exc}"

    if action == "summarise":
        return _summarise(df, path_or_url)

    # action == "plot"
    chart_type = args.get("chart_type", "").strip()
    x_col = args.get("x_col", "").strip()
    y_col = args.get("y_col", "").strip() or None
    title = args.get("title", "").strip()

    if chart_type not in _CHART_TYPES:
        return (
            f"Error: chart_type must be one of "
            f"{sorted(_CHART_TYPES)}. Got {chart_type!r}."
        )
    if not x_col:
        return "Error: x_col is required for action='plot'."
    if chart_type != "histogram" and not y_col:
        return f"Error: y_col is required for chart_type={chart_type!r}."

    try:
        return _plot(df, chart_type, x_col, y_col, title)
    except Exception as exc:
        logging.warning("Plot failed: %s", exc)
        return f"Plot error: {exc}"


REGISTRY.register(
    ToolDefinition(
        name="data_analysis",
        router_tier="data_analysis",
        label="Tool: Data analysis",
        description=(
            "load a CSV or Excel file and either summarise its statistics "
            "or generate a chart (bar, line, scatter, histogram)"
        ),
        examples=[
            "summarise this CSV: /home/user/sales.csv",
            "plot a bar chart of revenue by region from data.xlsx",
            "show me the statistics for https://example.com/data.csv",
            "scatter plot of age vs income from survey.csv",
        ],
        default_enabled=True,
        min_tier="complex_sonnet",
        approach="B",
        callable=_data_analysis_callable,
        category="files",
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)

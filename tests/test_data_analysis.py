"""Unit tests for the data_analysis tool.

All file I/O and network calls are mocked; no real files or HTTP requests
are made.
"""

import json
from unittest.mock import patch

import polars as pl
import pytest

from src.tools.data_analysis import (
    _data_analysis_callable,
    _load_dataframe,
    _plot,
    _summarise,
)
from src.tools.image_utils import _IMAGE_PREFIX
from src.tools.registry import REGISTRY

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLE_CSV = b"name,age,score\nAlice,30,88\nBob,25,92\nCarol,35,78\n"


@pytest.fixture()
def sample_df():
    return pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Carol"],
            "age": [30, 25, 35],
            "score": [88, 92, 78],
        }
    )


@pytest.fixture()
def csv_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_bytes(_SAMPLE_CSV)
    return p


@pytest.fixture()
def excel_file(tmp_path):
    """Write a tiny Excel file using openpyxl directly."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["name", "age", "score"])
    ws.append(["Alice", 30, 88])
    p = tmp_path / "data.xlsx"
    wb.save(str(p))
    return p


# ---------------------------------------------------------------------------
# _load_dataframe
# ---------------------------------------------------------------------------


class TestLoadDataframe:
    def test_loads_csv(self, csv_file):
        df = _load_dataframe(str(csv_file))
        assert df.shape == (3, 3)
        assert "name" in df.columns

    def test_loads_excel(self, excel_file):
        df = _load_dataframe(str(excel_file))
        assert df.shape[1] == 3

    def test_unsupported_extension_raises(self, tmp_path):
        f = tmp_path / "data.parquet"
        f.write_bytes(b"fake")
        with pytest.raises(ValueError, match="Unsupported"):
            _load_dataframe(str(f))

    def test_loads_remote_csv(self):
        import io

        mock_resp = io.BytesIO(_SAMPLE_CSV)
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None
        mock_resp.read = lambda: _SAMPLE_CSV

        with patch("urllib.request.urlopen", return_value=mock_resp):
            df = _load_dataframe("https://example.com/data.csv")
        assert df.shape[1] == 3


# ---------------------------------------------------------------------------
# _summarise
# ---------------------------------------------------------------------------


class TestSummarise:
    def test_returns_string(self, sample_df):
        result = _summarise(sample_df, "test.csv")
        assert isinstance(result, str)

    def test_contains_shape(self, sample_df):
        result = _summarise(sample_df, "test.csv")
        assert "3" in result  # rows
        assert "3" in result  # columns

    def test_contains_column_names(self, sample_df):
        result = _summarise(sample_df, "test.csv")
        assert "name" in result
        assert "age" in result
        assert "score" in result

    def test_contains_source(self, sample_df):
        result = _summarise(sample_df, "myfile.csv")
        assert "myfile.csv" in result

    def test_truncates_long_output(self):
        big_df = pl.DataFrame({"col": list(range(10_000))})
        result = _summarise(big_df, "big.csv")
        assert len(result) <= 3100  # _MAX_SUMMARY_LEN + small overhead


# ---------------------------------------------------------------------------
# _plot
# ---------------------------------------------------------------------------


class TestPlot:
    def test_bar_chart_returns_sentinel(self, sample_df):
        result = _plot(sample_df, "bar", "name", "score", "Test")
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_line_chart_returns_sentinel(self, sample_df):
        result = _plot(sample_df, "line", "age", "score", "")
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_scatter_returns_sentinel(self, sample_df):
        result = _plot(sample_df, "scatter", "age", "score", "")
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_histogram_returns_sentinel(self, sample_df):
        result = _plot(sample_df, "histogram", "score", None, "")
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_missing_x_col_raises(self, sample_df):
        with pytest.raises(ValueError, match="not found"):
            _plot(sample_df, "bar", "nonexistent", "score", "")

    def test_missing_y_col_raises(self, sample_df):
        with pytest.raises(ValueError, match="not found"):
            _plot(sample_df, "bar", "name", "nonexistent", "")


# ---------------------------------------------------------------------------
# _data_analysis_callable
# ---------------------------------------------------------------------------


class TestCallable:
    def test_summarise_csv(self, csv_file):
        args = json.dumps({"path_or_url": str(csv_file), "action": "summarise"})
        result = _data_analysis_callable(args)
        assert isinstance(result, str)
        assert "name" in result

    def test_plot_bar_returns_sentinel(self, csv_file):
        args = json.dumps(
            {
                "path_or_url": str(csv_file),
                "action": "plot",
                "chart_type": "bar",
                "x_col": "name",
                "y_col": "score",
            }
        )
        result = _data_analysis_callable(args)
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_plot_histogram_no_y_col(self, csv_file):
        args = json.dumps(
            {
                "path_or_url": str(csv_file),
                "action": "plot",
                "chart_type": "histogram",
                "x_col": "age",
            }
        )
        result = _data_analysis_callable(args)
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_missing_path_returns_error(self):
        result = _data_analysis_callable(json.dumps({"action": "summarise"}))
        assert "path_or_url" in result.lower() or "error" in result.lower()

    def test_invalid_action_returns_error(self, csv_file):
        args = json.dumps({"path_or_url": str(csv_file), "action": "explode"})
        result = _data_analysis_callable(args)
        assert "error" in result.lower()

    def test_invalid_chart_type_returns_error(self, csv_file):
        args = json.dumps(
            {
                "path_or_url": str(csv_file),
                "action": "plot",
                "chart_type": "pie",
                "x_col": "name",
                "y_col": "score",
            }
        )
        result = _data_analysis_callable(args)
        assert "error" in result.lower()

    def test_missing_x_col_for_plot_returns_error(self, csv_file):
        args = json.dumps(
            {
                "path_or_url": str(csv_file),
                "action": "plot",
                "chart_type": "bar",
                "y_col": "score",
            }
        )
        result = _data_analysis_callable(args)
        assert "x_col" in result.lower() or "error" in result.lower()

    def test_missing_y_col_for_bar_returns_error(self, csv_file):
        args = json.dumps(
            {
                "path_or_url": str(csv_file),
                "action": "plot",
                "chart_type": "bar",
                "x_col": "name",
            }
        )
        result = _data_analysis_callable(args)
        assert "y_col" in result.lower() or "error" in result.lower()

    def test_invalid_json_returns_error(self):
        result = _data_analysis_callable("not-json")
        assert "error" in result.lower()

    def test_file_not_found_returns_error(self):
        args = json.dumps(
            {"path_or_url": "/nonexistent/data.csv", "action": "summarise"}
        )
        result = _data_analysis_callable(args)
        assert "error" in result.lower() or "could not load" in result.lower()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_registered(self):
        assert any(t.name == "data_analysis" for t in REGISTRY.all())

    def test_approach_b(self):
        tool = next(t for t in REGISTRY.all() if t.name == "data_analysis")
        assert tool.approach == "B"

    def test_default_enabled(self):
        tool = next(t for t in REGISTRY.all() if t.name == "data_analysis")
        assert tool.default_enabled is True

    def test_schema_required_fields(self):
        tool = next(t for t in REGISTRY.all() if t.name == "data_analysis")
        required = tool.parameters_schema["required"]
        assert "path_or_url" in required
        assert "action" in required

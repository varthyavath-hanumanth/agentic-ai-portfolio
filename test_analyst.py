import pytest
from analyst_agent.analyst import analyze_question, classify_question, run_read_only_query


def test_region_question_is_classified():
    assert classify_question("Show total sales by region")["key"] == "region"


def test_analysis_returns_rows(tmp_path):
    result = analyze_question("Show monthly sales", tmp_path / "sales.db")
    assert result["status"] == "completed"
    assert result["row_count"] > 0


def test_unsupported_question_is_rejected(tmp_path):
    result = analyze_question("Predict next year's stock price", tmp_path / "sales.db")
    assert result["status"] == "unsupported_question"


def test_write_query_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        run_read_only_query(tmp_path / "does-not-matter.db", "DELETE FROM sales")


import pandas as pd

from app.ai.parser import parse
from app.analysis.engine import execute
from app.analysis.profiling import profile_dataframe, quality_report


def df():
    return pd.DataFrame({
        "Product": ["Laptop", "Laptop", "Phone"],
        "Sales": [100, 200, 50],
        "Profit": [20, 40, 10],
        "Region": ["West", "East", "West"]
    })


def test_group():
    result = execute(df(), parse("top 2 products by profit", df()))
    assert result.iloc[0]["Product"] == "Laptop"
    assert result.iloc[0]["Profit"] == 60


def test_average():
    result = execute(df(), parse("average sales", df()))
    assert abs(result.iloc[0]["value"] - (350 / 3)) < 1e-9


def test_profile_counts():
    result = profile_dataframe(df())
    assert result["rows"] == 3
    assert result["columns"] == 4
    assert result["duplicates"] == 0


def test_quality_report_detects_missing_values():
    data = pd.DataFrame({"Sales": [100, None, 50]})
    issues = quality_report(data)
    assert any("Missing values in Sales" in issue for issue in issues)


def test_quality_report_detects_duplicate_rows():
    data = pd.DataFrame({
        "Product": ["Laptop", "Laptop"],
        "Sales": [100, 100]
    })
    issues = quality_report(data)
    assert any("duplicate rows" in issue for issue in issues)


def test_quality_report_detects_empty_dataset():
    data = pd.DataFrame(columns=["Product", "Sales"])
    issues = quality_report(data)
    assert any("Dataset is empty" in issue for issue in issues)


def test_quality_report_detects_blank_text():
    data = pd.DataFrame({"Product": ["Laptop", "   "]})
    issues = quality_report(data)
    assert any("Blank text values in Product" in issue for issue in issues)

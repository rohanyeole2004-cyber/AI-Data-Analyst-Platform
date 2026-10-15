
import pandas as pd


def profile_dataframe(df):
    details = []

    for column in df.columns:
        series = df[column]

        item = {
            "column": str(column),
            "dtype": str(series.dtype),
            "rows": len(series),
            "missing": int(series.isna().sum()),
            "missing_pct": round(
                float(series.isna().mean() * 100), 2
            ) if len(series) > 0 else 0.0,
            "unique": int(series.nunique(dropna=True)),
        }

        if pd.api.types.is_numeric_dtype(series):
            item.update({
                "min": series.min(),
                "max": series.max(),
                "mean": series.mean(),
                "median": series.median(),
            })

        details.append(item)

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicates": int(df.duplicated().sum()),
        "columns_detail": details,
        "numeric_columns": [
            str(column)
            for column in df.select_dtypes(include="number").columns
        ],
    }


def quality_report(df):
    issues = []

    if df.empty:
        issues.append("Dataset is empty.")

    if len(df.columns) == 0:
        issues.append("Dataset has no columns.")

    if df.columns.duplicated().any():
        duplicate_columns = df.columns[
            df.columns.duplicated()
        ].tolist()
        issues.append(
            f"Duplicate column names: {duplicate_columns}"
        )

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        issues.append(f"{duplicate_rows} duplicate rows")

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        if missing_count:
            issues.append(
                f"Missing values in {column}: {missing_count}"
            )

        if (
            pd.api.types.is_object_dtype(df[column])
            and df[column].dropna().astype(str).str.strip().eq("").any()
        ):
            issues.append(
                f"Blank text values in {column}"
            )

    if not issues:
        issues.append("No basic data quality issues detected.")

    return issues

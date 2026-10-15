
import re


def find_metric(columns, text):
    """Find the metric column mentioned in the question."""
    metric_aliases = {
        "profit": ["profit"],
        "sales": ["sales"],
        "revenue": ["revenue", "sales"],
        "amount": ["amount", "sales"],
        "quantity": ["quantity", "qty"],
        "orders": ["orders", "orderid"],
    }

    lower_map = {str(c).lower(): c for c in columns}

    # Prefer an actual column name explicitly mentioned.
    for name in sorted(lower_map, key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            if name in {
                "profit", "sales", "revenue", "amount",
                "quantity", "qty", "orders", "orderid"
            }:
                return lower_map[name]

    # Otherwise use a known metric synonym.
    for alias, names in metric_aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            for name in names:
                if name in lower_map:
                    return lower_map[name]

    return None


def find_group(columns, text, metric=None):
    """Find the grouping column, such as Product or Region."""
    group_aliases = {
        "product": ["product", "products"],
        "region": ["region", "regions"],
        "category": ["category", "categories"],
        "customer": ["customer", "customers"],
        "segment": ["segment", "segments"],
        "city": ["city", "cities"],
        "state": ["state", "states"],
    }

    lower_map = {str(c).lower(): c for c in columns}
    excluded = str(metric).lower() if metric is not None else None

    for column_name, actual in lower_map.items():
        if column_name == excluded:
            continue

        aliases = group_aliases.get(column_name, [column_name])

        for alias in aliases:
            if re.search(r"\b" + re.escape(alias) + r"\b", text):
                return actual

    return None


def parse(q, df):
    text = q.lower().strip()
    columns = list(df.columns)

    if not text:
        raise ValueError("Please enter a question about your dataset.")

    if any(word in text for word in ["summary", "describe", "statistics"]):
        return {"operation": "describe"}

    metric = find_metric(columns, text)
    group = find_group(columns, text, metric)

    # Average / mean questions
    if re.search(r"\b(average|mean)\b", text):
        if metric is None:
            raise ValueError(
                "Please mention a numeric column, e.g. average sales."
            )

        return {
            "operation": "aggregate",
            "metric_column": metric,
            "aggregation": "mean",
        }

    # Top / bottom / highest / lowest questions
    top_match = re.search(r"\b(top|bottom)\s+(\d+)\b", text)

    is_lowest = any(
        phrase in text
        for phrase in ["lowest", "least", "smallest", "bottom"]
    )
    is_highest = any(
        phrase in text
        for phrase in ["highest", "most", "largest", "top", "best-selling"]
    )

    if is_highest or is_lowest or top_match:
        if group is None:
            raise ValueError(
                "Please mention a group, e.g. products or regions."
            )

        if metric is None:
            raise ValueError(
                "Please mention a metric, e.g. sales, profit, or quantity."
            )

        if group == metric:
            raise ValueError(
                "Please choose different grouping and metric columns."
            )

        limit = int(top_match.group(2)) if top_match else 1
        limit = max(1, min(limit, 100))

        aggregation = "median" if "median" in text else "sum"

        return {
            "operation": "group_by",
            "group_column": group,
            "metric_column": metric,
            "aggregation": aggregation,
            "sort": "ascending" if is_lowest else "descending",
            "limit": limit,
        }

    # Questions such as "sales by region"
    if group and metric and re.search(r"\bby\b", text):
        aggregation = (
            "mean" if "average" in text
            else "median" if "median" in text
            else "sum"
        )

        return {
            "operation": "group_by",
            "group_column": group,
            "metric_column": metric,
            "aggregation": aggregation,
            "sort": "descending",
            "limit": 100,
        }

    raise ValueError(
        "Question not supported yet. Try: "
        "'What are the top 2 products by profit?', "
        "'Which region has the lowest profit?', "
        "or 'What is the average sales?'"
    )

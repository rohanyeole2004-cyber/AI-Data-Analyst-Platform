

import re


def generate_sql(question: str, table_name: str) -> str:
    """Generate safe SQL for supported natural-language questions."""

    q = question.lower().strip()

    # Only allow a simple SQL table identifier.
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
        raise ValueError("Invalid table name.")

    table = f'"{table_name}"'

    # Normalize common phrases to improve question understanding.
    replacements = {
        r"\bbest[- ]selling\b": "highest sales",
        r"\btop[- ]selling\b": "highest sales",
        r"\bperformed the best\b": "highest sales",
        r"\bmost popular\b": "highest sales",
        r"\bworst[- ]selling\b": "lowest sales",
        r"\bleast popular\b": "lowest sales",
        r"\baverage\b": "avg",
        r"\bmean\b": "avg",
        r"\bnumber of products\b": "count products",
        r"\bhow many different products\b": "count products",
        r"\btotal revenue\b": "total sales",
    }

    for pattern, replacement in replacements.items():
        q = re.sub(pattern, replacement, q)

    # Lowest-selling product
    if (
        any(word in q for word in ("lowest", "least", "smallest"))
        and any(word in q for word in ("sales", "selling"))
        and "product" in q
    ):
        return f"""
SELECT Product, SUM(Sales) AS Total_Sales
FROM {table}
GROUP BY Product
ORDER BY Total_Sales ASC
LIMIT 1;
""".strip()

    # Average sales
    if any(term in q for term in ("average sales", "avg sales", "avg of sales")):
        return f"""
SELECT AVG(Sales) AS Average_Sales
FROM {table};
""".strip()

    # Count distinct products
    if (
        "count products" in q
        or "how many products" in q
        or "number of products" in q
    ):
        return f"""
SELECT COUNT(DISTINCT Product) AS Product_Count
FROM {table};
""".strip()

    # Highest-selling product(s)
    if (
        any(word in q for word in ("highest", "top", "maximum", "best"))
        and any(word in q for word in ("product", "selling"))
        and any(word in q for word in ("sales", "selling"))
    ):
        return f"""
SELECT Product, SUM(Sales) AS Total_Sales
FROM {table}
GROUP BY Product
ORDER BY Total_Sales DESC;
""".strip()

    # Sales grouped by product
    if (
        "sales by product" in q
        or "product wise sales" in q
        or "sales for each product" in q
        or "sales per product" in q
    ):
        return f"""
SELECT Product, SUM(Sales) AS Total_Sales
FROM {table}
GROUP BY Product
ORDER BY Total_Sales DESC;
""".strip()

    # Total sales
    if "total sales" in q or "sum of sales" in q:
        return f"""
SELECT SUM(Sales) AS Total_Sales
FROM {table};
""".strip()

    raise ValueError(
        "I could not map this question to a supported analysis. "
        "Try asking about highest sales, lowest sales, average sales, "
        "total sales, product count, or sales by product."
    )

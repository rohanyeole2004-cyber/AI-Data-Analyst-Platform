
import json
import re

from app.ai.ollama_client import ask_ai


def smart_parse(question: str, df):
    """Convert a question into a validated analysis plan."""

    columns = [str(column) for column in df.columns]
    q = question.lower()

    is_average = any(word in q for word in ["average", "mean"])
    is_highest = any(
        word in q for word in ["highest", "best-selling", "top"]
    )
    is_lowest = any(word in q for word in ["lowest", "least", "bottom"])

    # Handle average questions deterministically.
    if is_average:
        for keyword, column in [
            ("profit", "Profit"),
            ("sales", "Sales"),
            ("quantity", "Quantity"),
        ]:
            if keyword in q and column in columns:
                return {
                    "operation": "aggregate",
                    "metric_column": column,
                    "aggregation": "mean",
                }

   
    # Handle highest/lowest questions deterministically.
    if is_highest or is_lowest:
        if "region" in q and "Region" in columns:
            group = "Region"
        elif "category" in q and "Category" in columns:
            group = "Category"
        elif "customer" in q and "Customer" in columns:
            group = "Customer"
        elif "product" in q and "Product" in columns:
            group = "Product"
        else:
            group = "Product" if "Product" in columns else None

        if "profit" in q and "Profit" in columns:
            metric = "Profit"
        elif "quantity" in q and "Quantity" in columns:
            metric = "Quantity"
        elif "sales" in q and "Sales" in columns:
            metric = "Sales"
        else:
            metric = None

        # Read the requested number from questions like "top 2 products".
        number_match = re.search(r"\b(?:top|bottom)\s+(\d+)\b", q)
        limit = int(number_match.group(1)) if number_match else 1
        limit = max(1, min(limit, 100))

        if group and metric:
            return {
                "operation": "group_by",
                "group_column": group,
                "metric_column": metric,
                "aggregation": "sum",
                "sort": "ascending" if is_lowest else "descending",
                "limit": limit,
            }

        if "region" in q and "Region" in columns:
            group = "Region"
        elif "category" in q and "Category" in columns:
            group = "Category"
        elif "customer" in q and "Customer" in columns:
            group = "Customer"
        elif "product" in q and "Product" in columns:
            group = "Product"
        elif "Product" in columns:
            group = "Product"
        else:
            group = None

        if "profit" in q and "Profit" in columns:
            metric = "Profit"
        elif "quantity" in q and "Quantity" in columns:
            metric = "Quantity"
        elif "sales" in q and "Sales" in columns:
            metric = "Sales"
        else:
            metric = None

        if group and metric:
            return {
                "operation": "group_by",
                "group_column": group,
                "metric_column": metric,
                "aggregation": "sum",
                "sort": "ascending" if is_lowest else "descending",
                "limit": 1,
            }

    prompt = f"""
Convert the user's question into one JSON analysis plan.

Available columns:
{json.dumps(columns)}

Allowed operations:
- aggregate: metric_column, aggregation
- group_by: group_column, metric_column, aggregation, sort, limit
- describe

Allowed aggregations: sum, mean, median, count, min, max
Allowed sort: ascending, descending
Allowed limit: integer from 1 to 100

Rules:
- Use exact column names.
- Return only one JSON object.
- Never invent results.
- For unsupported questions, return {{"operation": "unsupported"}}.

Question: {question}
"""

    response = ask_ai(prompt)
    match = re.search(r"\{.*\}", response, re.DOTALL)

    if not match:
        raise ValueError("AI did not return valid JSON.")

    try:
        plan = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError("AI returned malformed JSON.") from exc

    if not isinstance(plan, dict):
        raise ValueError("AI plan must be a JSON object.")

    operation = plan.get("operation")

    if operation == "describe":
        return {"operation": "describe"}

    if operation not in {"aggregate", "group_by"}:
        raise ValueError(
            "This question is not supported yet. Try asking about "
            "sales, profit, region, product, or averages."
        )

    aggregation = plan.get("aggregation")
    if aggregation not in {"sum", "mean", "median", "count", "min", "max"}:
        raise ValueError("AI selected an unsupported aggregation.")

    metric = plan.get("metric_column")
    if not isinstance(metric, str) or metric not in columns:
        raise ValueError(f"Invalid metric column: {metric!r}")

    if operation == "aggregate":
        return {
            "operation": "aggregate",
            "metric_column": metric,
            "aggregation": aggregation,
        }

    group = plan.get("group_column")
    if not isinstance(group, str) or group not in columns:
        raise ValueError(f"Invalid group column: {group!r}")

    if group == metric:
        raise ValueError("Group and metric columns cannot be the same.")

    sort = plan.get("sort")
    if sort not in {"ascending", "descending"}:
        sort = "ascending" if is_lowest else "descending"

    try:
        limit = int(plan.get("limit", 10))
    except (TypeError, ValueError):
        limit = 10

    limit = max(1, min(limit, 100))

    return {
        "operation": "group_by",
        "group_column": group,
        "metric_column": metric,
        "aggregation": aggregation,
        "sort": sort,
        "limit": limit,
    }

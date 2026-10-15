
def verified_insight(plan, result):
    """Create a concise insight using only verified calculation results."""

    if result.empty:
        return "The analysis returned no rows, so no conclusion can be drawn."

    operation = plan.get("operation")

    if operation == "group_by":
        group_column = plan.get("group_column")
        metric_column = plan.get("metric_column")
        aggregation = plan.get("aggregation", "sum")

        # The engine returns a column named "count" for count aggregation.
        value_column = (
            "count"
            if aggregation == "count" and "count" in result.columns
            else metric_column
        )

        if group_column not in result.columns:
            return "The result does not contain the expected grouping column."

        if value_column not in result.columns:
            return "The result does not contain the expected metric column."

        top_row = result.iloc[0]
        group_value = top_row[group_column]
        metric_value = top_row[value_column]

        sort_direction = plan.get("sort", "descending")
        rank_label = (
            "lowest"
            if sort_direction == "ascending"
            else "highest"
        )

        return (
            f"{group_value} has the {rank_label} "
            f"{aggregation} of {metric_column}: {metric_value}. "
            "This conclusion is based on the calculated dataset results."
        )

    if operation == "aggregate":
        if "metric" not in result.columns or "value" not in result.columns:
            return "The aggregate result is missing its expected fields."

        metric_name = result.iloc[0]["metric"]
        metric_value = result.iloc[0]["value"]

        return (
            f"The verified result for {metric_name} is {metric_value}. "
            "This value was calculated from the uploaded dataset."
        )

    if operation == "describe":
        return (
            "The table contains descriptive statistics calculated "
            "from numeric columns in the uploaded dataset."
        )

    return "No verified insight is available for this operation."


import pandas as pd

READ_ONLY_AGGS = {"sum", "mean", "median", "min", "max", "count"}


def col(df, c):
    if c not in df.columns:
        raise ValueError(
            f"Column '{c}' not found. Available: {list(df.columns)}"
        )


def execute(df, plan):
    op = plan["operation"]

    if op == "group_by":
        g = plan["group_column"]
        m = plan["metric_column"]
        a = plan["aggregation"]

        col(df, g)
        col(df, m)

        if a not in READ_ONLY_AGGS:
            raise ValueError("Unsupported aggregation")

        if g == m and a != "count":
            raise ValueError(
                "Group column and metric column must be different."
            )

        if a == "count":
            out = df.groupby(g, dropna=False).size().reset_index(name="count")
            metric = "count"
        else:
            out = (
                df.groupby(g, dropna=False)[m]
                .agg(a)
                .rename("result")
                .reset_index()
            )
            metric = "result"

        out = out.sort_values(
            metric,
            ascending=plan.get("sort") == "ascending"
        )

        if plan.get("limit"):
            out = out.head(int(plan["limit"]))

        if metric == "result":
            out = out.rename(columns={"result": m})

        return out.reset_index(drop=True)

    if op == "aggregate":
        m = plan["metric_column"]
        a = plan["aggregation"]

        col(df, m)

        if a not in READ_ONLY_AGGS:
            raise ValueError("Unsupported aggregation")

        return pd.DataFrame({
            "metric": [f"{a}({m})"],
            "value": [getattr(df[m], a)()]
        })

    if op == "describe":
        return df.select_dtypes(include="number").describe().T.reset_index(
            names="column"
        )

    raise ValueError("Unsupported operation")


def validate(result):
    if not isinstance(result, pd.DataFrame):
        raise TypeError("Result must be DataFrame")

    return {
        "valid": True,
        "rows": len(result),
        "warnings": [] if not result.empty else ["No rows returned"]
    }

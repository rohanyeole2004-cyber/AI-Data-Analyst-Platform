import re

import pandas as pd
from sqlalchemy import inspect, text

from app.database.connection import engine


def sanitize_table_name(filename: str) -> str:
    """
    Convert a filename into a safe SQLite table name.
    Example:
        sample_sales.csv -> sample_sales
    """

    name = filename.rsplit(".", 1)[0]

    name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)

    if not name:
        name = "dataset"

    if name[0].isdigit():
        name = f"dataset_{name}"

    return name.lower()


def load_dataframe_to_sql(
    df: pd.DataFrame,
    filename: str
) -> str:
    """
    Load a Pandas DataFrame into SQLite.
    Returns the generated table name.
    """

    table_name = sanitize_table_name(filename)

    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False
    )

    return table_name


def get_table_names() -> list[str]:
    """
    Return all tables currently available in SQLite.
    """

    inspector = inspect(engine)

    return inspector.get_table_names()


def read_table(table_name: str) -> pd.DataFrame:
    """
    Read a complete SQL table into a DataFrame.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        raise ValueError(
            f"Table '{table_name}' does not exist."
        )

    query = text(
        f'SELECT * FROM "{table_name}"'
    )

    return pd.read_sql(query, engine)
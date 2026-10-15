import re

import pandas as pd
from sqlalchemy import text

from app.database.connection import engine


ALLOWED_START = re.compile(
    r"^\s*(SELECT|WITH)\b",
    re.IGNORECASE
)

BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH)\b",
    re.IGNORECASE
)


def validate_sql(query: str) -> bool:
    """
    Allow only read-only SQL queries.
    """

    if not query or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    if not ALLOWED_START.match(query):
        raise ValueError(
            "Only SELECT or WITH queries are allowed."
        )

    if BLOCKED_KEYWORDS.search(query):
        raise ValueError(
            "Unsafe SQL detected. Only read-only queries are allowed."
        )

    return True


def execute_sql(query: str) -> pd.DataFrame:
    """
    Execute a validated read-only SQL query
    and return the result as a DataFrame.
    """

    validate_sql(query)

    with engine.connect() as connection:
        result = pd.read_sql(
            text(query),
            connection
        )

    return result
def analyze_question_with_sql(question: str, table_name: str) -> pd.DataFrame:
    """
    Convert a natural-language question into SQL
    and execute the generated read-only SQL query.
    """

    from app.ai.sql_generator import generate_sql

    sql_query = generate_sql(
        question,
        table_name
    )

    result = execute_sql(sql_query)

    return result

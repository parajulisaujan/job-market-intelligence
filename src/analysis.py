"""Parameter-bound filtering followed by SQL summaries, not pandas aggregations."""

import sqlite3

import pandas as pd

from src.database import DATABASE_PATH, ROOT


def read_queries():
    text = (ROOT / "sql/queries.sql").read_text(encoding="utf-8")
    queries = {}
    for section in text.split("-- name: ")[1:]:
        name, sql = section.split("\n", 1)
        queries[name.strip()] = sql.strip()
    return queries


def filter_options(path=DATABASE_PATH):
    with sqlite3.connect(path) as connection:
        options = {}
        for column in ["role", "location", "remote_status"]:
            options[column] = [row[0] for row in connection.execute(
                f"SELECT DISTINCT {column} FROM jobs ORDER BY {column}")]
        options["skill"] = [row[0] for row in connection.execute("SELECT DISTINCT skill FROM job_skills ORDER BY skill")]
    return options


def analyze(filters=None, path=DATABASE_PATH):
    filters = filters or {}
    clauses, parameters = [], []
    # Column names come from this fixed list, never from user input.
    for column in ["role", "location", "remote_status"]:
        values = filters.get(column, [])
        if values:
            clauses.append(f"j.{column} IN ({','.join('?' for _ in values)})")
            parameters.extend(values)
    if filters.get("skill"):
        values = filters["skill"]
        clauses.append(f"EXISTS (SELECT 1 FROM job_skills s WHERE s.job_id = j.job_id AND s.skill IN ({','.join('?' for _ in values)}))")
        parameters.extend(values)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with sqlite3.connect(path) as connection:
        # SQLite views cannot take bound parameters. Materialize matching IDs first.
        connection.execute("CREATE TEMP TABLE selected_jobs AS SELECT j.job_id FROM jobs j" + where, parameters)
        connection.execute("CREATE TEMP VIEW filtered_jobs AS SELECT j.* FROM jobs j JOIN selected_jobs s ON j.job_id = s.job_id")
        return {name: pd.read_sql_query(sql, connection) for name, sql in read_queries().items()}

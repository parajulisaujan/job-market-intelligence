import sqlite3

import pandas as pd

from src.analysis import analyze, filter_options
from src.pipeline import build_pipeline


def test_pipeline_database_and_sql_filters(tmp_path):
    raw = pd.DataFrame([
        {"title": "Data Analyst", "description": "SQL Python SQL", "location": "Chicago", "salary": "80k-100k", "currency": "USD", "salary_period": "annual"},
        {"title": "Data Engineer", "description": "SQL Spark", "location": "Austin"},
        {"title": "Data Scientist", "description": "Python R", "location": "Chicago"},
    ])
    source, database = tmp_path / "input.csv", tmp_path / "jobs.sqlite"
    raw.to_csv(source, index=False)
    summary = build_pipeline(source, database)
    assert summary["cleaned_rows"] == 3
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("SELECT COUNT(*) FROM job_skills").fetchone()[0] == 6
    result = analyze(path=database)
    assert result["kpis"].iloc[0].total_jobs == 3
    assert result["kpis"].iloc[0].mean_salary_midpoint == 90000
    assert result["skills"].set_index("skill").loc["SQL", "jobs"] == 2
    assert len(result["pairs"]) == 3
    selected = analyze({"role": ["Data Analyst"], "skill": ["SQL", "Python"]}, database)
    assert selected["kpis"].iloc[0].total_jobs == 1
    assert selected["pairs"].iloc[0].jobs == 1
    assert analyze({"location": ["' OR 1=1 --"]}, database)["postings"].empty
    assert filter_options(database)["skill"] == ["Python", "R", "SQL", "Spark"]


def test_empty_csv_creates_usable_database(tmp_path):
    source, database = tmp_path / "empty.csv", tmp_path / "jobs.sqlite"
    pd.DataFrame(columns=["title", "description"]).to_csv(source, index=False)
    build_pipeline(source, database)
    results = analyze(path=database)
    assert results["kpis"].iloc[0].total_jobs == 0
    assert results["postings"].empty

"""Store postings and their skills in two ordinary SQLite tables."""

from pathlib import Path
import sqlite3

from src.skill_extraction import extract_skills

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data/processed/jobs.sqlite"


def write_database(jobs, path=DATABASE_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["job_id", "title", "company", "location", "description", "role", "remote_status",
               "salary_min", "salary_max", "salary_mid", "experience", "role_label", "source", "is_demo"]
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("DROP TABLE IF EXISTS job_skills")
        connection.execute("DROP TABLE IF EXISTS jobs")
        connection.execute("""CREATE TABLE jobs (
            job_id INTEGER PRIMARY KEY, title TEXT, company TEXT, location TEXT,
            description TEXT, role TEXT, remote_status TEXT, salary_min REAL,
            salary_max REAL, salary_mid REAL, experience TEXT, role_label TEXT,
            source TEXT, is_demo INTEGER NOT NULL CHECK (is_demo IN (0, 1)))""")
        jobs[columns].to_sql("jobs", connection, if_exists="append", index=False)
        connection.execute("""CREATE TABLE job_skills (
            job_id INTEGER REFERENCES jobs(job_id), skill TEXT,
            PRIMARY KEY (job_id, skill))""")
        skill_rows = []
        for job in jobs.itertuples():
            for skill in extract_skills(job.description):
                skill_rows.append((job.job_id, skill))
        connection.executemany("INSERT INTO job_skills VALUES (?, ?)", skill_rows)
    return path

"""Run with python -m src.pipeline [--input path/to/jobs.csv]."""

import argparse
from pathlib import Path

import pandas as pd

from src.data_cleaning import clean_jobs
from src.database import DATABASE_PATH, ROOT, write_database


def default_input():
    custom = ROOT / "data/raw/jobs.csv"
    return custom if custom.exists() else ROOT / "data/raw/demo_jobs.csv"


def build_pipeline(input_path=None, database_path=DATABASE_PATH):
    input_path = Path(input_path) if input_path else default_input()
    raw = pd.read_csv(input_path)
    # The bundled demo remains marked even if its flag column was edited away.
    if input_path.name == "demo_jobs.csv":
        raw["is_demo"] = True
    cleaned = clean_jobs(raw)
    write_database(cleaned, database_path)
    output = Path(database_path).parent / "jobs_cleaned.csv"
    cleaned.to_csv(output, index=False)
    return {"input": str(input_path), "raw_rows": len(raw), "cleaned_rows": len(cleaned),
            "duplicates_removed": len(raw) - len(cleaned), "database": str(database_path)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean a CSV and create the SQLite database.")
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    print(build_pipeline(args.input))

import pandas as pd

from src.data_cleaning import clean_jobs
from src.demo_data import generate_demo
from src.model import train_model


def test_model_skips_demo_unless_explicitly_enabled(tmp_path):
    jobs = clean_jobs(pd.read_csv(generate_demo(tmp_path / "demo.csv")))
    model, report = train_model(jobs)
    assert model is None
    assert report["status"] == "skipped"
    model, report = train_model(jobs, allow_demo=True)
    assert report["demo_only"]
    assert report["train_rows"] + report["test_rows"] == len(jobs)
    assert 0 <= report["accuracy"] <= 1
    assert model.predict(["Data analyst building SQL reports"])[0] in jobs.role_label.values


def test_model_skips_unlabeled_or_tiny_data():
    jobs = clean_jobs(pd.DataFrame({"title": ["Data Analyst"], "description": ["SQL reports"]}))
    assert train_model(jobs)[1]["status"] == "skipped"

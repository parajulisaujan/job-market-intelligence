from pathlib import Path

from streamlit.testing.v1 import AppTest
import pandas as pd
import pytest

from src import database, pipeline
from src.demo_data import generate_demo

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_source(tmp_path, monkeypatch):
    source = tmp_path / "demo_jobs.csv"
    generate_demo(source)
    monkeypatch.setattr(pipeline, "default_input", lambda: source)
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "jobs.sqlite")
    return source


def test_dashboard_loads_and_filters(isolated_source):
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "Job Market Intelligence"
    assert app.warning
    assert app.metric[0].value == "80"
    app.sidebar.multiselect[0].select("Data Analyst").run()
    assert not app.exception
    assert app.metric[0].value == "16"
    app.sidebar.multiselect[3].select("TensorFlow").run()
    assert not app.exception
    assert app.metric[0].value == "0"


def test_dashboard_empty_data(isolated_source):
    pd.DataFrame(columns=["title", "description"]).to_csv(isolated_source, index=False)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "0"


def test_dashboard_missing_data(isolated_source):
    isolated_source.unlink()
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert "could not be loaded" in app.error[0].value

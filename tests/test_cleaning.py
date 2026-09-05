import pandas as pd
import pytest

from src.data_cleaning import clean_job_title, clean_jobs, clean_location, clean_remote_status, clean_salary, classify_role
from src.skill_extraction import extract_skills


def test_title_and_location_cleanup():
    assert clean_job_title(" <b>Senior   Data Analyst</b> ") == "Senior Data Analyst"
    assert clean_job_title(None) == "Unknown"
    assert clean_location(" Chicago ,IL ") == "Chicago, IL"
    assert clean_location(None) == "Unknown"
    assert classify_role("Senior ML Engineer") == "Machine Learning Engineer"
    assert classify_role("Database Administrator") == "Other"


@pytest.mark.parametrize("value,expected", [("on-site", "Onsite"), ("FULLY REMOTE", "Remote"), (None, "Unknown"), ("maybe remote", "Unknown")])
def test_remote_status(value, expected):
    assert clean_remote_status(value) == expected


@pytest.mark.parametrize("text,currency,period,expected", [
    ("$80k - $120k", "USD", "annual", (80000, 120000)),
    ("USD 100,000 per year", "", "", (100000, 100000)),
    ("$25-$30/hour", "USD", "", (52000, 62400)),
    (None, "USD", "annual", (None, None)),
    ("$80k", "", "annual", (None, None)),
    ("€80000", "EUR", "annual", (None, None)),
    ("$80k", "USD", "", (None, None)),
    ("120k-80k", "USD", "annual", (None, None)),
    ("from 80k", "USD", "annual", (None, None)),
    ("80k+", "USD", "annual", (None, None)),
    ("-50000", "USD", "annual", (None, None)),
    ("80-100k", "USD", "annual", (80000, 100000)),
])
def test_salary(text, currency, period, expected):
    assert clean_salary(text, currency, period) == expected


def test_skill_aliases_and_boundaries():
    assert extract_skills("Python, PYTHON; Postgres / PostgreSQL and sklearn; PowerBI; R.") == ["Power BI", "Python", "R", "SQL", "scikit-learn"]
    assert extract_skills("Bright guitarist uses an excelled mysqldriver") == []
    assert extract_skills(None) == []


def test_transformations_remove_normalized_duplicates_and_keep_missing():
    raw = pd.DataFrame({"title": [" Data Analyst ", "data analyst", None],
                        "description": ["<p>SQL</p>", "sql", None]})
    cleaned = clean_jobs(raw)
    assert len(cleaned) == 2
    assert cleaned.job_id.tolist() == [1, 2]
    assert cleaned.role.tolist() == ["Data Analyst", "Other"]
    assert cleaned.salary_mid.isna().all()
    assert not cleaned.is_demo.any()
    assert cleaned.remote_status.tolist() == ["Unknown", "Unknown"]


def test_missing_required_columns_and_empty_input():
    with pytest.raises(ValueError, match="title and description"):
        clean_jobs(pd.DataFrame({"title": []}))
    assert clean_jobs(pd.DataFrame(columns=["title", "description"])).empty

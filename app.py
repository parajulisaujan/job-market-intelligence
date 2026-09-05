"""Run from the repository with streamlit run app.py."""

from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import analyze, filter_options
from src.database import DATABASE_PATH
from src.pipeline import build_pipeline, default_input

st.set_page_config(page_title="Job Market Intelligence", page_icon=None, layout="wide")
st.title("Job Market Intelligence")
st.caption("Explore the skills, roles, work arrangements, and posted salaries in a job-postings dataset.")


@st.cache_data(show_spinner="Preparing the dataset…")
def prepare_data(source_path, modified_ns, size):
    # File metadata invalidates the cache after a CSV replacement.
    return build_pipeline(Path(source_path))


def bar_chart(frame, category, title, horizontal=False):
    st.subheader(title)
    if frame.empty:
        st.info("No matching data for this chart.")
        return
    if horizontal:
        figure = px.bar(frame, x="jobs", y=category, orientation="h", labels={"jobs": "Postings", category: ""})
        figure.update_yaxes(categoryorder="total ascending")
    else:
        figure = px.bar(frame, x=category, y="jobs", labels={"jobs": "Postings", category: ""})
    figure.update_traces(marker_color="#2563EB")
    figure.update_layout(margin=dict(l=0, r=10, t=10, b=0), height=360)
    st.plotly_chart(figure, use_container_width=True)


source = default_input()
try:
    stat = source.stat()
    pipeline_summary = prepare_data(str(source), stat.st_mtime_ns, stat.st_size)
    if not DATABASE_PATH.exists():
        pipeline_summary = build_pipeline(source)
    options = filter_options()
except (OSError, ValueError, pd.errors.ParserError, sqlite3.Error) as error:
    st.error("The dataset could not be loaded. Add a valid CSV with title and description columns to data/raw/jobs.csv, or restore the bundled demo CSV.")
    with st.expander("Data loading details"):
        st.code(str(error))
    st.stop()

with sqlite3.connect(DATABASE_PATH) as connection:
    demo_count = connection.execute("SELECT COUNT(*) FROM jobs WHERE is_demo = 1").fetchone()[0]
if demo_count or source.name == "demo_jobs.csv":
    st.warning("DEMO DATA — Fictional postings for a portfolio demonstration. These charts are not real labor-market findings.")
else:
    st.info("User-provided dataset. Coverage and accuracy depend on its source; these counts do not represent the whole job market.")

st.sidebar.header("Filter postings")
filters = {
    "role": st.sidebar.multiselect("Job role", options["role"]),
    "location": st.sidebar.multiselect("Location", options["location"]),
    "remote_status": st.sidebar.multiselect("Work arrangement", options["remote_status"]),
    "skill": st.sidebar.multiselect("Skill (matches any selected)", options["skill"]),
}
st.sidebar.caption("No selection includes all values. Filters across different fields are combined.")
results = analyze(filters)
stats = results["kpis"].iloc[0]
jobs = results["postings"]
columns = st.columns(4)
columns[0].metric("Matching postings", f"{int(stats.total_jobs):,}")
columns[1].metric("Named companies", f"{int(stats.companies):,}")
columns[2].metric("With comparable salary", f"{int(stats.salary_count):,}")
mean_salary = stats.mean_salary_midpoint
columns[3].metric("Mean salary midpoint · USD/year", "N/A" if pd.isna(mean_salary) else f"${mean_salary:,.0f}")
st.caption("Salary metrics use annual USD ranges only; hourly amounts assume 2,080 hours/year. A range midpoint is not an actual employee salary.")

overview, skills_tab, salary_tab, data_tab, about_tab = st.tabs(["Overview", "Skills", "Salaries", "Explore data", "About / Methodology"])
with overview:
    if jobs.empty:
        st.info("No postings match these filters. Clear a filter to explore more data.")
    left, right = st.columns(2)
    with left:
        bar_chart(results["roles"], "role", "Jobs by Role", True)
        bar_chart(results["remote"], "remote_status", "Remote vs Hybrid vs Onsite")
    with right:
        bar_chart(results["locations"], "location", "Jobs by Location", True)
        bar_chart(results["experience"], "experience", "Experience Levels")
with skills_tab:
    bar_chart(results["skills"], "skill", "Top Skills", True)
    st.caption("Each skill counts at most once per posting. Mentions are not necessarily requirements.")
    st.subheader("Skills by Role")
    skill_roles = results["skills_by_role"]
    if not skill_roles.empty:
        matrix = skill_roles.pivot(index="skill", columns="role", values="jobs").fillna(0)
        figure = px.imshow(matrix, labels={"color": "Postings", "x": "Role", "y": "Skill"}, color_continuous_scale="Blues", aspect="auto")
        st.plotly_chart(figure, use_container_width=True)
    else:
        st.info("No skill mentions in the selected postings.")
    st.subheader("Common Skill Combinations")
    st.dataframe(results["pairs"].rename(columns={"skill_a": "First skill", "skill_b": "Second skill", "jobs": "Postings mentioning both"}), hide_index=True, use_container_width=True)
with salary_tab:
    st.subheader("Salary Distribution")
    salary_jobs = jobs.dropna(subset=["salary_mid"])
    if salary_jobs.empty:
        st.info("No comparable annual USD salaries are available for this selection.")
    else:
        figure = px.histogram(salary_jobs, x="salary_mid", nbins=15, labels={"salary_mid": "Posted salary midpoint (USD/year)"})
        figure.update_yaxes(title="Postings")
        st.plotly_chart(figure, use_container_width=True)
        st.subheader("Posted Salaries by Role")
        st.dataframe(results["salary_by_role"], hide_index=True, use_container_width=True)
        st.caption("Counts show sample size. Small groups are unstable; unreported, ambiguous, and non-USD salaries are excluded.")
with data_tab:
    st.subheader("Filtered Postings")
    st.dataframe(jobs[["title", "company", "role", "location", "remote_status", "experience", "salary_min", "salary_max", "source"]], hide_index=True, use_container_width=True)
    st.download_button("Download filtered postings (CSV)", jobs.to_csv(index=False).encode("utf-8"), "filtered_jobs.csv", "text/csv")
with about_tab:
    st.subheader("About this project")
    st.write("An entry-level analytics portfolio project built with Python, pandas, SQLite, SQL, Streamlit, Plotly, and scikit-learn. All charts describe postings in this dataset, not people hired or vacancies verified to be open.")
    st.write(f"Loaded {pipeline_summary['raw_rows']} CSV rows; retained {pipeline_summary['cleaned_rows']} postings after removing {pipeline_summary['duplicates_removed']} duplicates.")
    st.markdown("""
**Methodology**

- pandas cleans whitespace and HTML, retains missing categories as Unknown, and removes duplicate title/company/location/description/work-arrangement combinations.
- Broad roles come from title keywords. Experience uses a supplied level or explicit title words; it does not infer years of experience.
- A small alias dictionary matches skill mentions with word boundaries. SQL joins a postings table to a unique posting/skill table.
- SQL supplies counts, role summaries, salary summaries, and skill pairs. Location strings are not geocoded. Work arrangements use explicit fields only.
- Salary summaries compare annual USD ranges. Hourly pay is multiplied by 2,080; no currency conversion or benefits adjustment is performed.

**Optional machine learning**

`python -m src.model` uses TF-IDF and Logistic Regression when independently labeled data is available. It skips the bundled synthetic data by default. The explicit `--allow-demo` exercise tests the workflow only; templates make its scores unrealistic. Model predictions do not determine dashboard role counts.

**Limitations**

Skill matching cannot understand negation, required versus preferred qualifications, or every alias. Duplicate detection is exact after basic normalization. This dataset is not representative of the job market. Do not draw career or salary conclusions from fictional examples.
""")

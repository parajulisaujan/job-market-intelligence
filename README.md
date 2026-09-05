# Job Market Intelligence Dashboard

A graduate-level analytics portfolio project combining pandas cleaning, SQLite storage, SQL analysis, and an interactive Streamlit dashboard.

**Live Demo:** [add deployed Streamlit URL]

**GitHub Repository:** [parajulisaujan/job-market-intelligence](https://github.com/parajulisaujan/job-market-intelligence)

> **DEMO DATA:** The bundled postings are fictional. Their counts, salaries, and model scores are educational examples, not real labor-market findings.

## Overview and problem

Job descriptions contain useful information in inconsistent formats. This project organizes that information to explore technical skill mentions, broad job categories, locations, work arrangements, experience levels, and posted salary ranges within a dataset.

## Features and dashboard

- Filters for role, location, work arrangement, and skills.
- KPI cards for posting count, named companies, salary coverage, and mean posted salary midpoint.
- Plotly charts for Top Skills, Jobs by Role, Jobs by Location, Remote vs Hybrid vs Onsite, Experience Levels, Salary Distribution, and Skills by Role.
- SQL salary summaries with sample sizes and common skill combinations.
- Filtered CSV download and an About / Methodology tab.
- Optional TF-IDF + Logistic Regression classification exercise.
- pytest tests for cleaning, SQL results, model eligibility, and dashboard interaction.

## Tools

Python, pandas, SQLite, SQL, Streamlit, Plotly, scikit-learn, pytest, and Git/GitHub. SQLite is included with Python. Transitive packages are installed by these libraries; there are no additional application services.

## Dataset

`data/raw/demo_jobs.csv` contains **81 fictional rows**, including one intentional duplicate. Cleaning retains **80 postings** in five categories. `python -m src.demo_data` reproduces the CSV with seed 42. No postings were scraped or copied from employers. See [data/DATASET.md](data/DATASET.md).

An initial public-dataset search did not establish an easily reusable source with verified provenance for this build, so the project uses the requested demo fallback. It makes no representative market claims.

### Replace the demo

Obtain a CSV you have permission to use and redistribute, map its columns to the contract below, and save it as `data/raw/jobs.csv`. Record its publisher, URL, license, download date, coverage, and mapping steps in `data/DATASET.md`. Mark genuine rows `is_demo=false` and preserve `true` for synthetic rows. Then run `python -m src.pipeline` and rerun the dashboard. The app prefers `jobs.csv`; remove your custom file to return to demo mode.

| Column | Required? | Meaning |
| --- | --- | --- |
| `title`, `description` | Yes | Posting title and description text |
| `company`, `location` | No | Missing values become Unknown |
| `remote_status` | No | remote, fully remote, hybrid, onsite, on-site, on site, in office |
| `salary` | No | A number or closed range, such as `$80k - $100k` |
| `currency` | For salary | USD, unless explicitly stated in salary text |
| `salary_period` | For salary | annual, yearly, hourly, unless explicitly stated in text |
| `experience` | No | entry, junior, intern, mid, senior, lead |
| `role_label` | For ML | Independently reviewed category: Data Analyst, Data Scientist, Data Engineer, Machine Learning Engineer, Other |
| `source` | Recommended | Dataset name or source URL |
| `is_demo` | Recommended | true for fictional records; false for genuine records |

Missing required columns produce a helpful error. Missing optional values remain unknown. A header-only CSV creates an empty dashboard; an empty or malformed file shows a loading message. A broken custom file is not silently replaced with demo data.

For one-off processing, use `python -m src.pipeline --input path/to/input.csv`. The dashboard always selects `data/raw/jobs.csv` or the bundled demo; this CLI option does not change its source selection.

## Project structure

```text
app.py                       Streamlit entry point
data/
  DATASET.md                 Dataset provenance
  raw/demo_jobs.csv          Fictional examples
  processed/                 Generated CSV, SQLite, model report (ignored)
src/
  data_cleaning.py            pandas transformations
  skill_extraction.py         Skill dictionary and alias matching
  demo_data.py                Reproducible demo generator
  database.py                 jobs and job_skills tables
  pipeline.py                 CSV → cleaning → database
  analysis.py                 Bound filters and SQL execution
  model.py                    TF-IDF classifier and evaluation
sql/queries.sql              SQL used by the dashboard
tests/                       pytest and Streamlit AppTest
README.md
INTERVIEW_NOTES.md
RESUME_BULLETS.md
requirements.txt
.streamlit/config.toml
```

## Installation

Use Python 3.12 or newer. This build was tested with Python 3.14. From the repository root:

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
python -m pip install -r requirements.txt
python -m src.pipeline
streamlit run app.py
```

The dashboard also builds SQLite automatically on first launch and refreshes when the selected CSV's metadata changes. All paths are relative to the repository's Python files. No credentials, external downloads, or prebuilt database are required at runtime.

If PowerShell activation is disabled, run `.\.venv\Scripts\python.exe -m streamlit run app.py` directly.

## Data cleaning

Small functions strip HTML, collapse whitespace, normalize location comma spacing, map explicit work arrangements, and preserve missing categories. Readable titles remain intact; a separate keyword rule assigns broad roles. Experience uses a provided level or explicit title words such as Junior or Senior.

Duplicate detection compares cleaned title, company, location, description, and work arrangement without case differences, retaining the first row. It may merge identical reposts or miss near-duplicates; it does not reconcile conflicting salary fields.

Salary comparisons require USD and a known period. Closed ranges and single amounts are supported. Hourly pay assumes 40 hours × 52 weeks. Open-ended, reversed, ambiguous, and non-USD salaries are excluded. The salary KPI averages range midpoints, not actual worker compensation. Missing salary rows remain in all other analyses.

## Skill extraction

A dictionary maps canonical names to literal aliases. Regex word boundaries prevent partial-word matches, and each posting counts once per skill. Postgres/PostgreSQL/MySQL count under SQL; sklearn maps to scikit-learn; PowerBI maps to Power BI.

Skills include Python, SQL, R, Excel, Tableau, Power BI, pandas, NumPy, scikit-learn, TensorFlow, PyTorch, AWS, Azure, GCP, Spark, Git, Docker, Snowflake, Databricks, Airflow, and dbt. Cloud and infrastructure names are extraction vocabulary, not technologies used to build the app.

Matches represent mentions, not necessarily requirements. The extractor cannot understand negation or preferred versus required qualifications. An isolated R can still be ambiguous.

## SQLite and SQL analysis

`jobs` stores one cleaned posting per row. `job_skills` stores unique `(job_id, skill)` pairs with primary and foreign keys. Dashboard summaries use [sql/queries.sql](sql/queries.sql), demonstrating SELECT, WHERE, GROUP BY, ORDER BY, JOIN, CASE, and a CTE.

```sql
SELECT s.skill, COUNT(*) AS postings
FROM jobs j JOIN job_skills s ON j.job_id = s.job_id
WHERE j.role = 'Data Analyst'
GROUP BY s.skill
ORDER BY postings DESC, s.skill;
```

Filters use bound parameters. Matching IDs populate a temporary table and a `filtered_jobs` view shared by all summaries. Skill selection matches ANY chosen skill; different fields combine with AND. For manual SQL execution, first run `CREATE TEMP VIEW filtered_jobs AS SELECT * FROM jobs;` in the same SQLite session.

## Machine-learning component

```bash
python -m src.model
python -m src.model --allow-demo
```

The default skips synthetic data. The second command explicitly runs a **synthetic learning exercise**, writing measured results to `data/processed/model_report.json`. Do not cite demo accuracy as real-world performance.

Genuine training requires at least two categories with ten distinct nonempty descriptions each and a supplied `role_label`. Model labels are not automatically derived from dashboard title rules. Exact normalized description duplicates are removed before splitting.

- **TF-IDF** converts words and two-word phrases into numbers, reducing the emphasis on words common across documents.
- **Logistic Regression** learns weights relating text features to broad job categories. It is an explainable baseline for text classification.
- **Train/test split** holds out 25% of labeled examples, using stratification and seed 42. TF-IDF is fitted only on training text inside an sklearn Pipeline.
- Evaluation computes accuracy, classification_report (precision, recall, F1, support), and a majority-class baseline. No results are hard-coded.

Template wording and titles make demo evaluation artificially easy. Random splits on real data can also share employer templates. Independently reviewed labels and employer/time-based holdouts would make evaluation more credible. Model predictions do not drive dashboard counts.

## Tests

```bash
python -m pytest -q
```

Without activating PowerShell: `.\.venv\Scripts\python.exe -m pytest -q`.

Tests cover salary boundaries, missing data, duplicates, aliases, known SQL counts, filtering, database integrity, model guards, and Streamlit rendering/filter interactions. Server startup and its health endpoint were also checked during the build.

## Streamlit Community Cloud deployment

1. Push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and connect GitHub.
3. Select **Create app**, repository `parajulisaujan/job-market-intelligence`, branch `main`, and entry point `app.py`.
4. Choose a supported Python version of 3.12 or newer in advanced settings. Dependencies install from `requirements.txt`.
5. Deploy and replace the Live Demo placeholder with the public URL.

See the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app). No secrets are required. Generated files are disposable and rebuilt from the committed CSV. The project is prepared for deployment; connecting the user's Streamlit account and publishing remain user actions.

## Limitations and future improvements

This is a small local-file application, not a live vacancy feed. Fictional data cannot answer actual market questions. Counts are postings, not hiring outcomes or confirmed openings. Locations are strings, not standardized metropolitan areas. Salary missingness and small role groups limit comparisons. Keyword roles and experience categories can miss unusual wording.

Future steps: obtain a permitted real dataset with provenance, manually check extraction precision/recall, add source-specific salary mappings and location aliases, and evaluate ML on employers or dates absent from training. Keep additions small and driven by observed errors.

## What I Learned

I learned how to turn a CSV into a repeatable analysis pipeline instead of manually editing spreadsheet cells. pandas helped me handle missing values consistently, while SQLite let me practice joins and grouped summaries. Building the dashboard showed me why every chart needs the same filtered population. I also learned that a model score only means something when the labels and test data are credible, and that explaining demo-data limitations is part of honest analysis.

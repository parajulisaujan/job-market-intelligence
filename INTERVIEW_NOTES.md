# Interview notes

## 30-second explanation

“I built a job-postings dashboard to practice the full analytics workflow. pandas cleans a CSV, SQLite stores postings and extracted skills, and SQL calculates summaries. Streamlit lets users filter the data and explore Plotly charts. The bundled records are fictional, so I present it as a working analytics demonstration rather than real market research.”

## Two-minute explanation

“I wanted to connect data cleaning, SQL, and a usable dashboard. Job descriptions have messy text, inconsistent categories, and missing salaries. I used clearly labeled synthetic examples so the project can run without accounts or restricted scraping.

“The pipeline removes HTML and extra whitespace, maps explicit work arrangements, and keeps unknown values visible. It parses salary ranges only when currency and period are clear. A small skill dictionary handles aliases such as sklearn and Postgres. SQLite stores postings in one table and unique posting/skill pairs in another.

“SQL drives the summaries, including joins, GROUP BY, CASE, and a CTE for skill pairs. Every chart shares the same filters, and users can inspect the underlying rows. I also added an optional TF-IDF and Logistic Regression classifier. It requires supplied labels and skips demo data by default because repeated templates make synthetic accuracy misleading.

“Tests check cleaning rules, SQL results, and dashboard interaction. My next step would be a permitted real dataset and manual extraction checks before making any market claims.”

## How the pipeline works

1. `pipeline.py` reads custom `data/raw/jobs.csv` if present, otherwise the bundled demo.
2. `data_cleaning.py` validates columns, normalizes text and categories, parses salary fields, removes duplicates, and assigns local IDs.
3. `database.py` writes `jobs`, extracts skills, and writes `job_skills` with a unique posting/skill key.
4. `analysis.py` binds filter values and runs queries from `sql/queries.sql` against one filtered view.
5. `app.py` presents SQL results. pandas only reshapes the grouped skill result for the heatmap.
6. `model.py` runs optional training separately; predictions do not determine dashboard role counts.

## Why these tools?

**pandas:** CSV loading and tabular cleaning are readable, and intermediate DataFrames are easy to inspect.

**SQLite:** A file database suits this small project. I can demonstrate relational tables and SQL without managing a server. It is not intended for a large concurrent write workload.

**Streamlit:** I could build an interface using Python and focus on analysis rather than a separate web framework.

**Plotly:** Basic interactive charts make categories and distributions easy to explore without much custom interface code.

## How skill extraction works

For each skill I loop over its aliases, search with word boundaries, and add the canonical name once. “Python, Postgres, and sklearn” becomes Python, SQL, and scikit-learn. R does not match inside “reports.” I match descriptions only.

This is interpretable but does not understand negation. “No Python required” still counts as a mention, and an isolated R may be ambiguous. I would hand-label a sample and measure precision and recall before trusting it on real data.

## SQL examples

Skills requested in analyst postings:

```sql
SELECT s.skill, COUNT(*) AS postings
FROM jobs j JOIN job_skills s ON j.job_id = s.job_id
WHERE j.role = 'Data Analyst'
GROUP BY s.skill
ORDER BY postings DESC, s.skill;
```

The join associates skills with roles. The unique posting/skill key means each posting counts once per skill.

Salary coverage using CASE:

```sql
SELECT CASE WHEN salary_mid IS NULL THEN 'Missing or unsupported'
            ELSE 'Comparable USD salary' END AS coverage,
       COUNT(*) AS postings
FROM jobs GROUP BY coverage ORDER BY postings DESC;
```

Skill combinations using a CTE:

```sql
WITH pairs AS (
    SELECT a.skill AS first_skill, b.skill AS second_skill
    FROM job_skills a JOIN job_skills b
    ON a.job_id = b.job_id AND a.skill < b.skill
)
SELECT first_skill, second_skill, COUNT(*) AS postings
FROM pairs GROUP BY first_skill, second_skill
ORDER BY postings DESC;
```

`a.skill < b.skill` avoids self-pairs and reversed duplicates. The CTE names an intermediate result. Co-occurrence is not causation or a normalized measure of association.

## How the model works

**TF-IDF** converts text into a sparse numerical matrix. Term frequency represents word occurrence in a document; inverse document frequency reduces the weight of words common across documents. Most matrix values are zero because each posting uses only a fraction of the vocabulary.

**Logistic Regression** learns weights connecting words and two-word phrases to categories. Despite its name, it performs classification. I chose it as a common, fast baseline for sparse text, not because I proved it was the best algorithm.

**Train/test split** reserves 25% of labeled rows for evaluation. Stratification preserves category proportions, and seed 42 makes the split repeatable. TF-IDF is inside an sklearn Pipeline so it is fitted only on training text.

**Labels:** The model uses supplied `role_label`, not the dashboard's title-derived `role`. Labels must be independently reviewed; the code cannot verify their quality. At least two categories need ten distinct nonempty descriptions each. Exact normalized descriptions are deduplicated before splitting.

**Evaluation:** Accuracy is the fraction correct. Precision measures how often a predicted category is right; recall measures how many examples of a category were found. F1 balances them, and support is the test count. A majority-class baseline shows what always choosing the most common training class achieves.

Demo training requires `--allow-demo` and only exercises the software. Template overlap and title wording make its scores optimistic. I would use employer/time-based holdouts for a more credible real-data evaluation.

## Limitations and improvements

The data is fictional. Location strings are not geocoded, salary formats are intentionally limited, and rule-based roles can miss unusual titles. Exact duplicate checks can miss near-duplicates. Salary missingness biases comparisons. A mention may not be a requirement.

I would obtain a permitted real dataset with clear coverage, manually validate extraction, add aliases based on errors, improve source-specific salary mappings, and independently label examples for ML. I would keep the code small until real usage justified more complexity.

## Ten interview questions and natural answers

**1. What did you build?**  
“The cleaning functions, extraction dictionary, SQLite schema, SQL queries, dashboard, optional model workflow, tests, and documentation. The libraries supply underlying data and chart operations, and the bundled records are generated.”

**2. Why not do all analysis in pandas?**  
“SQL makes joins and grouped summaries explicit. Keeping the queries in a file also lets someone review the analysis separately from the interface.”

**3. How do you prevent double-counting skills?**  
“Extraction returns each canonical skill once, and the database has a primary key on job ID and skill. Repeated mentions do not increase counts.”

**4. What happens to missing salaries?**  
“The posting stays in other analyses. Its salary is null and excluded from salary averages. The dashboard shows salary coverage so the denominator is visible.”

**5. What is a duplicate?**  
“A match on cleaned title, company, location, description, and work arrangement, ignoring case. I keep the first row. This is easy to explain but does not reconcile different salaries or catch near-duplicates.”

**6. Can this tell me what skills to learn?**  
“Not with demo data. A credible real sample could show skill mentions, but I would still need to consider time period, coverage, role, and required versus optional qualifications.”

**7. How are filters applied?**  
“I use bound SQLite parameters. Values within a field are alternatives; different fields combine with AND. Every summary uses the resulting filtered view.”

**8. What does the model's accuracy prove?**  
“It measures the held-out examples in that run. With synthetic templates it only demonstrates the workflow. I would need credible labels and a more independent test set to claim generalization.”

**9. How did you test the project?**  
“I used known inputs and expected outputs for cleaning and extraction. A tiny database checks SQL counts and filters. Streamlit AppTest checks rendering and count changes after filters.”

**10. What design choice matters most?**  
“I kept unknown values visible instead of guessing. A missing remote field is Unknown, not Onsite. That prevents missing information from becoming a misleading claim.”

"""Dictionary matching: a posting counts once for each skill it mentions."""

import re

SKILL_ALIASES = {
    "Python": ["python"], "SQL": ["sql", "postgresql", "postgres", "mysql", "t-sql"],
    "R": ["r"], "Excel": ["excel", "microsoft excel"], "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"], "Pandas": ["pandas"], "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "TensorFlow": ["tensorflow"], "PyTorch": ["pytorch"],
    "AWS": ["aws", "amazon web services"], "Azure": ["azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"], "Spark": ["spark", "pyspark"],
    "Git": ["git"], "Docker": ["docker"], "Snowflake": ["snowflake"],
    "Databricks": ["databricks"], "Airflow": ["airflow"], "dbt": ["dbt"],
}


def extract_skills(description):
    if not isinstance(description, str):
        return []
    found = []
    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
            if re.search(pattern, description, flags=re.IGNORECASE):
                found.append(skill)
                break
    return sorted(found)

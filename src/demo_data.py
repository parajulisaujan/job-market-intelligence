"""Create reproducible fictional examples. Never a labor-market sample."""

import csv
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def generate_demo(path=ROOT / "data/raw/demo_jobs.csv"):
    rng = random.Random(42)
    profiles = {
        "Data Analyst": (["SQL", "Excel", "Tableau", "Power BI", "Python"], "Build reports, validate metrics, and explain business trends."),
        "Data Scientist": (["Python", "R", "Pandas", "NumPy", "scikit-learn", "SQL"], "Design experiments and evaluate statistical prediction models."),
        "Data Engineer": (["SQL", "Python", "Spark", "Airflow", "dbt", "Snowflake", "Databricks"], "Build reliable data pipelines and maintain warehouse tables."),
        "Machine Learning Engineer": (["Python", "PyTorch", "TensorFlow", "Docker", "AWS", "Git"], "Train machine learning models and monitor prediction services."),
        "Other": (["Excel", "SQL", "Git", "Azure", "GCP"], "Support business systems and document operational requirements."),
    }
    rows = []
    for role, (skills, description) in profiles.items():
        for number in range(16):
            title = role if role != "Other" else "Business Systems Specialist"
            selected = rng.sample(skills, rng.randint(2, len(skills)))
            low = rng.randrange(55, 151, 5)
            rows.append({
                "title": ("Junior " if number % 4 == 0 else "Senior " if number % 4 == 1 else "") + title,
                "company": f"Demo Company {number + 1:02}",
                "location": rng.choice(["Chicago, IL", "Austin, TX", "New York, NY", "Seattle, WA", ""]),
                "remote_status": rng.choice(["remote", "hybrid", "on-site", ""]),
                "salary": f"${low}k - ${low + 25}k" if number % 5 else "",
                "currency": "USD", "salary_period": "annual",
                "description": f"<p>{description}</p> Skills: {', '.join(selected)}. Work with team {number + 1}.",
                "experience": rng.choice(["entry", "mid", "senior", ""]),
                "role_label": role, "source": "Fictional demo generated with seed 42", "is_demo": "true",
            })
    rows.append(rows[0].copy())  # Intentional duplicate to demonstrate cleaning.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


if __name__ == "__main__":
    print(generate_demo())

"""One optional classifier. Synthetic scores are only a software demonstration."""

import argparse
import json
import sqlite3

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import pandas as pd

from src.database import DATABASE_PATH
from src.pipeline import build_pipeline


def train_model(jobs, allow_demo=False):
    if jobs["is_demo"].any() and not allow_demo:
        return None, {"status": "skipped", "reason": "Demo data cannot support real-world model evaluation. Use --allow-demo only for a learning exercise."}
    labeled = jobs.loc[jobs.role_label.ne("") & jobs.description.str.strip().ne("")].copy()
    # Repeated descriptions must not land in both train and test sets.
    keys = labeled.description.str.casefold().str.replace(r"\s+", " ", regex=True).str.strip()
    labeled = labeled.loc[~keys.duplicated()]
    counts = labeled.role_label.value_counts()
    if len(counts) < 2 or counts.min() < 10:
        return None, {"status": "skipped", "reason": "Need at least two human-labeled categories with ten distinct descriptions each."}
    text = labeled.title + " " + labeled.description
    x_train, x_test, y_train, y_test = train_test_split(
        text, labeled.role_label, test_size=0.25, random_state=42, stratify=labeled.role_label
    )
    model = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    report = {
        "status": "trained", "demo_only": bool(jobs.is_demo.any()),
        "train_rows": len(x_train), "test_rows": len(x_test),
        "accuracy": accuracy_score(y_test, predictions),
        "majority_baseline_accuracy": float((y_test == y_train.mode().iloc[0]).mean()),
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        "limitations": "Random split; similar templates and title wording can make scores optimistic. Labels must be independently reviewed. Demo scores are not market evidence.",
    }
    return model, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-demo", action="store_true")
    args = parser.parse_args()
    if not DATABASE_PATH.exists():
        build_pipeline()
    with sqlite3.connect(DATABASE_PATH) as connection:
        jobs = pd.read_sql_query("SELECT * FROM jobs", connection)
    _, report = train_model(jobs, allow_demo=args.allow_demo)
    path = DATABASE_PATH.parent / "model_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

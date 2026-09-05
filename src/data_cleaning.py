"""Conservative cleaning; unknown values are never guessed into facts."""

import html
import re

import pandas as pd

ROLES = ["Data Analyst", "Data Scientist", "Data Engineer", "Machine Learning Engineer", "Other"]


def clean_text(value):
    if pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_job_title(value):
    text = clean_text(value)
    return text if text else "Unknown"


def classify_role(title):
    text = title.lower()
    for pattern, role in [
        (r"\b(machine learning|ml|ai) engineer\b", "Machine Learning Engineer"),
        (r"\bdata scientist\b", "Data Scientist"),
        (r"\bdata engineer\b", "Data Engineer"),
        (r"\b(data analyst|business intelligence analyst|bi analyst)\b", "Data Analyst"),
    ]:
        if re.search(pattern, text):
            return role
    return "Other"


def clean_location(value):
    text = clean_text(value)
    text = re.sub(r"\s*,\s*", ", ", text)
    return text or "Unknown"


def clean_remote_status(value):
    text = clean_text(value).lower()
    mapping = {"remote": "Remote", "fully remote": "Remote", "hybrid": "Hybrid",
               "onsite": "Onsite", "on-site": "Onsite", "on site": "Onsite",
               "in office": "Onsite"}
    return mapping.get(text, "Unknown")


def clean_salary(value, currency="", period=""):
    """Return an annual USD range or (None, None).

    Hourly pay assumes 40 hours/week and 52 weeks/year. No exchange rates.
    Bare dollar signs require an explicit USD currency column.
    """
    text = clean_text(value).lower().replace(",", "")
    currency = clean_text(currency).upper()
    period = clean_text(period).lower()
    if not text or re.search(r"[€£]|\b(eur|gbp|cad|aud)\b", text):
        return None, None
    if currency not in ("", "USD") or (currency != "USD" and "usd" not in text):
        return None, None
    if any(word in text for word in ["hour", "/hr"]):
        period = "hourly"
    elif any(word in text for word in ["annual", "/year", "per year", "yearly"]):
        period = "annual"
    if period not in ("annual", "yearly", "hourly"):
        return None, None
    # Reject open ranges and explanatory numbers rather than guessing endpoints.
    if re.search(r"\+|\b(from|up to|minimum|maximum|starting)\b", text):
        return None, None
    if re.match(r"^[^\d]*-\s*\d", text) or "--" in text:
        return None, None
    matches = re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(k)?", text)
    if not 1 <= len(matches) <= 2:
        return None, None
    numbers = [float(number) * (1000 if suffix else 1) for number, suffix in matches]
    # A shared trailing k in 80-100k applies to both endpoints.
    if len(matches) == 2 and matches[1][1] and not matches[0][1] and numbers[0] < 1000:
        numbers[0] *= 1000
    if len(numbers) == 1:
        numbers *= 2
    low, high = numbers
    if low <= 0 or high < low:
        return None, None
    multiplier = 2080 if period == "hourly" else 1
    return low * multiplier, high * multiplier


def experience_level(value, title):
    text = clean_text(value).lower()
    mapping = {"entry": "Entry", "entry level": "Entry", "junior": "Entry", "intern": "Intern",
               "mid": "Mid", "mid level": "Mid", "senior": "Senior", "lead": "Lead"}
    if text in mapping:
        return mapping[text]
    for pattern, level in [(r"\bintern\b", "Intern"), (r"\b(junior|jr\.?|entry)\b", "Entry"),
                           (r"\b(senior|sr\.?)\b", "Senior"), (r"\b(lead|principal)\b", "Lead")]:
        if re.search(pattern, title.lower()):
            return level
    return "Unknown"


def remove_duplicates(jobs):
    columns = ["title", "company", "location", "description", "remote_status"]
    keys = jobs[columns].apply(lambda column: column.str.casefold())
    return jobs.loc[~keys.duplicated()].copy()


def clean_jobs(raw):
    required = {"title", "description"}
    if not required.issubset(raw.columns):
        raise ValueError("CSV must contain title and description columns.")
    jobs = raw.copy()
    optional = ["company", "location", "remote_status", "salary", "currency", "salary_period",
                "experience", "role_label", "source", "is_demo"]
    for column in optional:
        if column not in jobs:
            jobs[column] = ""
    jobs["title"] = jobs["title"].map(clean_job_title)
    jobs["description"] = jobs["description"].map(clean_text)
    jobs["company"] = jobs["company"].map(lambda value: clean_text(value) or "Unknown")
    jobs["location"] = jobs["location"].map(clean_location)
    jobs["remote_status"] = jobs["remote_status"].map(clean_remote_status)
    jobs["role"] = jobs["title"].map(classify_role)
    jobs["experience"] = [experience_level(value, title) for value, title in zip(jobs.experience, jobs.title)]
    salaries = [clean_salary(s, c, p) for s, c, p in zip(jobs.salary, jobs.currency, jobs.salary_period)]
    jobs["salary_min"] = pd.Series([s[0] for s in salaries], index=jobs.index, dtype=float)
    jobs["salary_max"] = pd.Series([s[1] for s in salaries], index=jobs.index, dtype=float)
    jobs["salary_mid"] = (jobs.salary_min + jobs.salary_max) / 2
    jobs["role_label"] = jobs["role_label"].map(lambda value: clean_text(value) if clean_text(value) in ROLES else "")
    jobs["source"] = jobs["source"].map(lambda value: clean_text(value) or "User-provided CSV (unverified)")
    jobs["is_demo"] = jobs["is_demo"].map(lambda value: clean_text(value).lower() in ("true", "1", "yes"))
    jobs = remove_duplicates(jobs).reset_index(drop=True)
    jobs.insert(0, "job_id", range(1, len(jobs) + 1))
    return jobs

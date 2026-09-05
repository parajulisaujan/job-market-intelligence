-- Dashboard queries share a filtered_jobs temporary view.
-- In a SQLite client, first run: CREATE TEMP VIEW filtered_jobs AS SELECT * FROM jobs;
-- name: kpis
SELECT COUNT(*) AS total_jobs,
       COUNT(DISTINCT CASE WHEN company <> 'Unknown' THEN company END) AS companies,
       COUNT(salary_mid) AS salary_count,
       AVG(salary_mid) AS mean_salary_midpoint
FROM filtered_jobs;

-- name: roles
SELECT role, COUNT(*) AS jobs FROM filtered_jobs
GROUP BY role ORDER BY jobs DESC, role;

-- name: skills
SELECT s.skill, COUNT(*) AS jobs
FROM job_skills s JOIN filtered_jobs j ON j.job_id = s.job_id
GROUP BY s.skill ORDER BY jobs DESC, s.skill LIMIT 20;

-- name: locations
SELECT location, COUNT(*) AS jobs FROM filtered_jobs
GROUP BY location ORDER BY jobs DESC, location LIMIT 15;

-- name: remote
SELECT remote_status, COUNT(*) AS jobs FROM filtered_jobs
GROUP BY remote_status ORDER BY jobs DESC, remote_status;

-- name: experience
SELECT experience, COUNT(*) AS jobs FROM filtered_jobs
GROUP BY experience ORDER BY jobs DESC, experience;

-- name: skills_by_role
SELECT j.role, s.skill, COUNT(*) AS jobs
FROM filtered_jobs j JOIN job_skills s ON j.job_id = s.job_id
GROUP BY j.role, s.skill ORDER BY j.role, jobs DESC, s.skill;

-- name: salary_by_role
SELECT role, COUNT(*) AS salary_count, AVG(salary_mid) AS mean_salary_midpoint,
       MIN(salary_min) AS lowest_posted_salary, MAX(salary_max) AS highest_posted_salary
FROM filtered_jobs WHERE salary_mid IS NOT NULL
GROUP BY role ORDER BY mean_salary_midpoint DESC;

-- name: pairs
WITH skill_pairs AS (
    SELECT a.skill AS skill_a, b.skill AS skill_b, a.job_id
    FROM job_skills a JOIN job_skills b ON a.job_id = b.job_id AND a.skill < b.skill
    JOIN filtered_jobs j ON j.job_id = a.job_id
)
SELECT skill_a, skill_b, COUNT(*) AS jobs FROM skill_pairs
GROUP BY skill_a, skill_b ORDER BY jobs DESC, skill_a, skill_b LIMIT 15;

-- name: postings
SELECT * FROM filtered_jobs ORDER BY title, company, job_id;

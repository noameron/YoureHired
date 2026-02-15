DELETE FROM repositories
WHERE github_id NOT IN (
    SELECT DISTINCT github_id
    FROM analysis_results
)
AND last_seen_at < ?;

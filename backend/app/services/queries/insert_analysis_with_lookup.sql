INSERT INTO analysis_results
(run_id, github_id, fit_score, reason,
 contributions, reject, reject_reason,
 analyzed_at)
SELECT ?, github_id, ?, ?, ?, ?, ?, ?
FROM repositories WHERE owner = ? AND name = ?;
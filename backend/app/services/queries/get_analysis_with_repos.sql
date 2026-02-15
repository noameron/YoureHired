SELECT
    a.fit_score, a.reason, a.contributions,
    a.reject, a.reject_reason,
    r.github_id, r.owner, r.name, r.url,
    r.description, r.primary_language,
    r.languages, r.star_count, r.fork_count,
    r.open_issue_count, r.topics, r.license,
    r.pushed_at, r.created_at,
    r.good_first_issue_count,
    r.help_wanted_count
FROM analysis_results a
JOIN repositories r ON a.github_id = r.github_id
WHERE a.run_id = ?
ORDER BY a.fit_score DESC;

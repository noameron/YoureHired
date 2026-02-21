INSERT OR REPLACE INTO repositories
(github_id, owner, name, url, description,
 primary_language, languages, star_count,
 fork_count, open_issue_count, topics,
 license, pushed_at, created_at,
 good_first_issue_count, help_wanted_count,
 last_seen_at)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);

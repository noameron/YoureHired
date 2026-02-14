UPDATE search_runs
SET status=?, finished_at=?,
    total_discovered=?, total_filtered=?,
    total_analyzed=?
WHERE id=?;

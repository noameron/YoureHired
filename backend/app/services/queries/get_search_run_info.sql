SELECT id, status, total_discovered,
    total_filtered, total_analyzed
FROM search_runs WHERE id = ?;

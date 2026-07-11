SELECT
    id_stage,
    run_id,
    stage,
    layer,
    started_at,
    duration_ms,
    rows_in,
    rows_out,
    status,
    details
FROM ctl_pipeline_stages
ORDER BY started_at DESC

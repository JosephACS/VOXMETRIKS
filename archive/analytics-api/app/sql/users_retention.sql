SELECT
    cohort_week,
    users_cohort,
    week_1_pct,
    week_2_pct,
    week_4_pct
FROM agg_user_retention
ORDER BY cohort_week

SELECT
    id_track,
    nombre_track,
    recommendation_score,
    engagement_score,
    popularity
FROM agg_recommendation_scores
ORDER BY recommendation_score DESC, popularity DESC

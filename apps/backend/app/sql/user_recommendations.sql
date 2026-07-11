SELECT
    rs.id_track,
    rs.nombre_track,
    rs.recommendation_score,
    rs.engagement_score,
    rs.popularity,
    CASE
        WHEN uh.user_streams > 0 THEN 'genre_affinity'
        ELSE 'global_score'
    END AS reason,
    rs.recommendation_score
        + COALESCE(uh.user_streams, 0) * 0.05
        + CASE WHEN uh.user_streams > 0 THEN 5.0 ELSE 0.0 END AS blended_score
FROM agg_recommendation_scores rs
LEFT JOIN (
    SELECT
        fs.id_track,
        COUNT(*) AS user_streams
    FROM fact_streaming fs
    WHERE fs.id_usuario = ?
    GROUP BY fs.id_track
) uh ON uh.id_track = rs.id_track
WHERE rs.id_track NOT IN (
    SELECT DISTINCT id_track
    FROM fact_streaming
    WHERE id_usuario = ?
)
ORDER BY blended_score DESC, rs.recommendation_score DESC
LIMIT ?

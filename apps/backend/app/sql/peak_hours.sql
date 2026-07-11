SELECT
    CAST(EXTRACT(hour FROM fecha_evento) AS INTEGER) AS hour_of_day,
    COUNT(*) AS stream_count
FROM fact_streaming
WHERE CAST(fecha_evento AS DATE) BETWEEN ? AND ?
GROUP BY 1
ORDER BY stream_count DESC

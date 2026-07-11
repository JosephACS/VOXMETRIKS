SELECT
    id_carga,
    fecha_carga,
    modo,
    registros_nuevos,
    total_raw,
    estado
FROM ctl_carga_dataset
ORDER BY fecha_carga DESC

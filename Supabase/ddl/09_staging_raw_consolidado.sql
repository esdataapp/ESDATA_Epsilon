-- 09_staging_raw_consolidado.sql
-- Área de staging para cargas crudas antes de transformación.

CREATE TABLE IF NOT EXISTS staging_raw_consolidado (
    id_source        TEXT,
    pagina_web       TEXT,
    ciudad_raw       TEXT,
    fecha_scrap_raw  TEXT,
    tipo_prop_raw    TEXT,
    precio_raw       TEXT,
    area_raw         TEXT,
    recamaras_raw    TEXT,
    estacionamientos_raw TEXT,
    operacion_raw    TEXT,
    titulo_raw       TEXT,
    descripcion_raw  TEXT,
    ubicacion_url    TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

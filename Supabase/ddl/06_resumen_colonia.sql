-- 06_resumen_colonia.sql
-- Tablas resumen inicial y final (representatividad)

CREATE TABLE IF NOT EXISTS resumen_colonia_inicial (
    ciudad         TEXT,
    colonia        TEXT,
    operacion      TEXT,
    tipo_propiedad TEXT,
    periodo        TEXT NOT NULL,
    n              INTEGER,
    precio_mediana NUMERIC(14,2),
    area_m2_mediana NUMERIC(10,2),
    pxm2_mediana   NUMERIC(14,4),
    pxm2_iqr       NUMERIC(14,4),
    pxm2_cv        NUMERIC(14,6),
    metodo_precio  TEXT,
    metodo_area    TEXT,
    metodo_pxm2    TEXT,
    PRIMARY KEY (ciudad, colonia, operacion, tipo_propiedad, periodo)
);

CREATE TABLE IF NOT EXISTS resumen_colonia_final (LIKE resumen_colonia_inicial INCLUDING ALL);

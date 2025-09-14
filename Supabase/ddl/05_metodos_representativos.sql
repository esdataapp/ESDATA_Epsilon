-- 05_metodos_representativos.sql

CREATE TABLE IF NOT EXISTS metodos_representativos (
    ciudad           TEXT,
    colonia          TEXT,
    operacion        TEXT,
    tipo_propiedad   TEXT,
    periodo          TEXT NOT NULL,
    precio_metodo    TEXT,
    area_m2_metodo   TEXT,
    pxm2_metodo      TEXT,
    n                INTEGER,
    skew_pxm2        NUMERIC(12,6),
    cv_pxm2          NUMERIC(12,6),
    iqr_pxm2         NUMERIC(14,4),
    PRIMARY KEY (ciudad, colonia, operacion, tipo_propiedad, periodo)
);

CREATE INDEX IF NOT EXISTS idx_metodos_periodo ON metodos_representativos(periodo);

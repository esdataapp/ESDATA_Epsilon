-- 08_estadistico_normalidad.sql

CREATE TABLE IF NOT EXISTS estadistico_normalidad (
    ciudad         TEXT,
    colonia        TEXT,
    operacion      TEXT,
    tipo_propiedad TEXT,
    periodo        TEXT NOT NULL,
    variable       TEXT NOT NULL,
    test           TEXT NOT NULL, -- shapiro / kolmogorov / jarque_bera
    estadistico    NUMERIC(18,6),
    p_value        NUMERIC(12,8),
    n              INTEGER,
    PRIMARY KEY (ciudad, colonia, operacion, tipo_propiedad, variable, test, periodo)
);

CREATE INDEX IF NOT EXISTS idx_normalidad_periodo ON estadistico_normalidad(periodo);

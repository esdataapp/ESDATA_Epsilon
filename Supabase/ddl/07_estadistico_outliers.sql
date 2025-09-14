-- 07_estadistico_outliers.sql

CREATE TABLE IF NOT EXISTS estadistico_outliers (
    id          VARCHAR(40),
    periodo     TEXT NOT NULL,
    variable    TEXT NOT NULL,
    valor       NUMERIC(18,6),
    flag_iqr    SMALLINT,
    flag_zscore SMALLINT,
    low_iqr     NUMERIC(18,6),
    high_iqr    NUMERIC(18,6),
    PRIMARY KEY (id, variable, periodo)
);

CREATE INDEX IF NOT EXISTS idx_outliers_periodo ON estadistico_outliers(periodo);

-- 01_core_final_num.sql
-- Tabla principal final_num consolidando todos los periodos.
-- Recomendación: particionar por rango de periodo (si formato YYYYMM) o usar índice compuesto.

CREATE TABLE IF NOT EXISTS final_num (
    id                VARCHAR(40) PRIMARY KEY,
    periodo           TEXT NOT NULL,
    pagina_web        TEXT,
    ciudad            TEXT,
    colonia           TEXT,
    operacion         TEXT,
    tipo_propiedad    TEXT,
    fecha_scrap       DATE,
    precio            NUMERIC(14,2),
    area_m2           NUMERIC(10,2),
    pxm2              NUMERIC(14,4),
    recamaras         SMALLINT,
    banos             SMALLINT,
    medio_banos       SMALLINT,
    banos_totales     NUMERIC(5,2),
    estacionamientos  SMALLINT,
    antiguedad_icon   TEXT,
    mantenimiento     NUMERIC(12,2),
    latitud           DOUBLE PRECISION,
    longitud          DOUBLE PRECISION,
    geom              geometry(Point,4326),
    -- Metricas derivadas posibles (null si no aplica en periodo)
    clasificacion_mercado TEXT,
    precio_min        NUMERIC(14,2),
    precio_mediana    NUMERIC(14,2),
    precio_media      NUMERIC(14,2),
    precio_max        NUMERIC(14,2),
    area_m2_min       NUMERIC(10,2),
    area_m2_mediana   NUMERIC(10,2),
    area_m2_media     NUMERIC(10,2),
    area_m2_max       NUMERIC(10,2),
    pxm2_min          NUMERIC(14,4),
    pxm2_mediana      NUMERIC(14,4),
    pxm2_media        NUMERIC(14,4),
    pxm2_max          NUMERIC(14,4),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Índices auxiliares
CREATE INDEX IF NOT EXISTS idx_final_num_periodo ON final_num(periodo);
CREATE INDEX IF NOT EXISTS idx_final_num_ciudad ON final_num(ciudad);
CREATE INDEX IF NOT EXISTS idx_final_num_colonia ON final_num(colonia);
CREATE INDEX IF NOT EXISTS idx_final_num_operacion_tipo ON final_num(operacion, tipo_propiedad);
CREATE INDEX IF NOT EXISTS idx_final_num_geom ON final_num USING GIST (geom);

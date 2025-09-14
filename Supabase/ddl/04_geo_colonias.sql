-- 04_geo_colonias.sql
-- Capa geoespacial de colonias (polígonos). Fuente: GeoJSON colonias-<Ciudad>.geojson

CREATE TABLE IF NOT EXISTS geo_colonias (
    id_colonia     SERIAL PRIMARY KEY,
    ciudad         TEXT NOT NULL,
    colonia        TEXT NOT NULL,
    slug_colonia   TEXT,
    fuente         TEXT,
    periodo_carga  TEXT,
    geom           geometry(MultiPolygon,4326) NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_geo_colonias_ciudad ON geo_colonias(ciudad);
CREATE INDEX IF NOT EXISTS idx_geo_colonias_colonia ON geo_colonias(colonia);
CREATE INDEX IF NOT EXISTS idx_geo_colonias_geom ON geo_colonias USING GIST (geom);

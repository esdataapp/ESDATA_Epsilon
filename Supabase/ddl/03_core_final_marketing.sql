-- 03_core_final_marketing.sql
-- Variables derivadas de análisis de texto (marketing) por listing.

CREATE TABLE IF NOT EXISTS final_marketing (
    id             VARCHAR(40) PRIMARY KEY REFERENCES final_num(id) ON DELETE CASCADE,
    periodo        TEXT NOT NULL,
    ciudad         TEXT,
    colonia        TEXT,
    operacion      TEXT,
    tipo_propiedad TEXT,
    len_desc       INTEGER,
    len_desc_ratio NUMERIC(10,4),
    marketing_keyword_count INTEGER,
    marketing_intensity_idx NUMERIC(10,4),
    -- Prefijos dinámicos (desc_*, titulo_*). Se recomienda crear columnas a demanda.
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_final_marketing_periodo ON final_marketing(periodo);
CREATE INDEX IF NOT EXISTS idx_final_marketing_colonia ON final_marketing(colonia);

-- 02_core_final_amenidades.sql
-- Tabla de amenidades binarias/semi-binarias. Puede almacenarse wide (una columna por amenidad)
-- o normalizarse en formato long. Aquí ofrecemos modelo wide para velocidad de consulta.

CREATE TABLE IF NOT EXISTS final_amenidades (
    id             VARCHAR(40) PRIMARY KEY REFERENCES final_num(id) ON DELETE CASCADE,
    periodo        TEXT NOT NULL,
    ciudad         TEXT,
    colonia        TEXT,
    operacion      TEXT,
    tipo_propiedad TEXT,
    -- Ejemplos de columnas (añadir las reales al ejecutar):
    amen_alberca       SMALLINT,
    amen_gimnasio      SMALLINT,
    amen_elevador      SMALLINT,
    amen_seguridad     SMALLINT,
    amen_patio         SMALLINT,
    amen_balcon        SMALLINT,
    amen_jardin        SMALLINT,
    -- ... (completar con script de inspección)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_final_amenidades_periodo ON final_amenidades(periodo);
CREATE INDEX IF NOT EXISTS idx_final_amenidades_colonia ON final_amenidades(colonia);

# Estrategia de Índices, Particionado y Mantenimiento

## 1. Objetivos
- Optimizar consultas analíticas (agregaciones por ciudad/colonia/periodo, filtros por tipo/operación).
- Acelerar joins espaciales (final_num <-> geo_colonias) y métricas colonia.
- Facilitar purga / recarga incremental por periodo.

## 2. Índices Recomendados
```sql
-- Búsquedas frecuentes por geografía y tipo
CREATE INDEX IF NOT EXISTS idx_final_num_ciudad_colonia ON final_num(ciudad, colonia);
CREATE INDEX IF NOT EXISTS idx_final_num_oper_tipo ON final_num(operacion, tipo_propiedad);
CREATE INDEX IF NOT EXISTS idx_final_num_periodo ON final_num(periodo);
CREATE INDEX IF NOT EXISTS idx_final_num_pxm2 ON final_num(pxm2);
CREATE INDEX IF NOT EXISTS idx_final_num_created_at ON final_num(created_at);

-- Amenidades: si se consultan flags específicos
CREATE INDEX IF NOT EXISTS idx_final_amenidades_alberca ON final_amenidades(amen_alberca) WHERE amen_alberca=1;

-- Marketing (texto resumido)
CREATE INDEX IF NOT EXISTS idx_final_marketing_len_desc ON final_marketing(len_descripcion);

-- Estadísticos colonia
CREATE INDEX IF NOT EXISTS idx_resumen_colonia_ciudad_colonia ON resumen_colonia_final(ciudad,colonia,periodo);

-- Representatividad métodos
CREATE INDEX IF NOT EXISTS idx_metodos_rep_colonia ON metodos_representativos(ciudad,colonia,periodo);

-- Outliers y normalidad
CREATE INDEX IF NOT EXISTS idx_outliers_variable_periodo ON estadistico_outliers(variable,periodo);
CREATE INDEX IF NOT EXISTS idx_normalidad_variable_periodo ON estadistico_normalidad(variable,periodo);

-- Geoespacial
CREATE INDEX IF NOT EXISTS idx_final_num_geom ON final_num USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_geo_colonias_geom ON geo_colonias USING GIST(geom);
```

## 3. Particionado (Opcional Evolutivo)
Estrategía planteada: particionar tablas de alto volumen por periodo.

Ejemplo (PostgreSQL declarative partitioning):
```sql
-- Tabla padre
CREATE TABLE final_num_part (
  LIKE final_num INCLUDING ALL,
  periodo TEXT NOT NULL
) PARTITION BY LIST (periodo);

-- Partición para 'Sep25'
CREATE TABLE final_num_part_sep25 PARTITION OF final_num_part FOR VALUES IN ('Sep25');
```
Migrar gradualmente: insertar nuevos periodos en versión particionada y mantener vista de compatibilidad:
```sql
CREATE OR REPLACE VIEW final_num AS SELECT * FROM final_num_part;
```

Beneficios:
- Borrado rápido de un periodo: DROP PARTITION.
- ANALYZE/VACUUM más eficientes segmentando.

## 4. Mantenimiento
```sql
VACUUM (ANALYZE) final_num;
VACUUM (ANALYZE) final_amenidades;
ANALYZE;
```
Schedule sugerido: diario (bajo carga baja) + full semanal.

Reindex ocasional (si bloat >20%):
```sql
REINDEX TABLE CONCURRENTLY final_num;
```

## 5. Estadísticas y Planner
Aumentar target para columnas de alta cardinalidad:
```sql
ALTER TABLE final_num ALTER COLUMN colonia SET STATISTICS 500;
ALTER TABLE final_num ALTER COLUMN ciudad SET STATISTICS 500;
```

## 6. RLS / Seguridad (Resumen)
1. Crear rol applicacion con permisos CRUD controlados.
2. Rol readonly solo SELECT.
3. (Opcional) Activar RLS y políticas por ciudad si multi-cliente:
```sql
ALTER TABLE final_num ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_select_city ON final_num FOR SELECT USING (ciudad = current_setting('app.current_ciudad', true));
```
Aplicar set local `SET app.current_ciudad='Gdl';` antes de consultas.

## 7. Monitoreo
- pg_stat_statements: identificar queries pesadas.
- auto_explain (logging): plan de consultas > 1s.
- Extensions sugeridas: pg_stat_statements, hypopg (índices hipotéticos).

## 8. Checklist Post-Load
[ ] Conteo filas concuerda con CSV origen.
[ ] No duplicados en (id) y (periodo,id) si particionado.
[ ] Índices creados sin errores.
[ ] EXPLAIN sample queries < 50ms (filtros simples), < 200ms (agregaciones medianas).
[ ] Geometrías válidas (SELECT COUNT(*) FROM final_num WHERE NOT ST_IsValid(geom) = 0).

## 9. Futuras Mejoras
- BRIN index en columnas monotónicas (created_at) si muy grande.
- Partial indexes para flags frecuentes (flag_outlier_precio=1).
- Materialized views refrescadas incrementalmente por periodo.
- Automatizar particiones vía trigger (creación on-demand). 

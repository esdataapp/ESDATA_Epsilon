# Supabase / PostgreSQL Deployment (Core Pipeline Data)

Este directorio orquesta la carga de TODOS los CSV y GEOJSON del pipeline (sin incluir artefactos exclusivos del dashboard) hacia una instancia Supabase (PostgreSQL + PostGIS).

## Alcance
Incluye:
- Tablas finales (0.Final_Num_*, 0.Final_Ame_*, 0.Final_MKT_*)
- Tablas intermedias relevantes si decides historizarlas (1.Consolidado_Adecuado_*, 2.Consolidado_ConColonia_*, 5.Num_Corroborado_*, metodos_representativos_*, *_inicial.csv, *_final.csv)
- Estadística núcleo (descriptivos, outliers, normalidad) opcional
- GeoJSON de colonias a capa PostGIS

Excluye (por ahora):
- Archivos en Dashboard/CSV/<Periodo>/ (ya que los puedes reconstruir; se pueden crear vistas en su lugar)

## Estructura propuesta de carpetas
Supabase/
  README.md
  ddl/                # CREATE TABLE ...
  load/               # Scripts COPY o Python
  views/              # Definición de vistas materializadas
  indices/            # Índices adicionales y constraints
  docs/               # Guías (particionado, seguridad, checklist)
  geo/                # Scripts carga PostGIS
  config/             # Variables de entorno ejemplo

## Pasos de implementación
1. Provisionar base en Supabase con extensión PostGIS:
  ```sql
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- si se necesitan UUIDs
  -- (Opcional) Para performance diagnóstica
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
  ```
2. Crear tablas (ejecutar en orden los archivos de ddl/ numerados).
3. Subir CSVs usando interfaz o scripts COPY.
4. Ejecutar índices / constraints.
5. Cargar GeoJSON a tabla colonias.
6. Crear vistas derivadas (ej. v_colony_stats) para emular dashboard.
7. Validar conteos y checks de integridad.

## Nomenclatura sugerida de tablas
- raw_consolidado_adecuado (histórico multi-periodo)
- geo_colonias
- final_num
- final_amenidades
- final_marketing
- metodos_representativos
- resumen_colonia_inicial / resumen_colonia_final
- estadistico_outliers
- estadistico_normalidad

Agregar columna periodo (TEXT) en todas para permitir queries temporales.

## Tipos de datos clave
- IDs: VARCHAR(40) (hash) PRIMARY KEY
- Fechas scrap: DATE
- Números monetarios: NUMERIC(14,2)
- Área: NUMERIC(10,2)
- Coordenadas: DOUBLE PRECISION + geometry(Point, 4326)
- Amenidades: BOOLEAN o SMALLINT (0/1)
- Texto largo: TEXT

## Estrategia de carga
Para volumen moderado (<5M filas) usar COPY directa.
Para control incremental: staging -> merge (INSERT ... ON CONFLICT DO NOTHING/UPDATE).

### Variables de entorno (.env) recomendadas
Ubicar un `.env` en la raíz o en `Supabase/` (el script `ingestion_loader.py` los intenta cargar):
```
PG_HOST=aws-xyz.supabase.co
PG_PORT=5432
PG_DB=postgres
PG_USER=postgres
PG_PASSWORD=TU_PASSWORD
# Pooler (opcional si se usa en otros servicios tipo Prisma):
PGPOOL_URL=postgresql://postgres:TU_PASSWORD@aws-xyz.supabase.co:6543/postgres?sslmode=require
PGURL=postgresql://postgres:TU_PASSWORD@aws-xyz.supabase.co:5432/postgres?sslmode=require
```

### Script de ingesta Python
Archivo: `Supabase/scripts/ingestion_loader.py`
Funciones clave:
- Auto-descubre CSV en `N5_Resultados/Nivel_1/CSV/` que empiecen con prefijos: `0.Final_Num`, `0.Final_Ame`, `0.Final_MKT`, `metodos_representativos`.
- Parametrización por periodo y modo dry-run.

Ejemplos:
```powershell
python Supabase/scripts/ingestion_loader.py --dry-run
python Supabase/scripts/ingestion_loader.py --periodos Sep25
python Supabase/scripts/ingestion_loader.py --periodos Sep25 May25
```

Salida: imprime JSON por archivo con tiempo y total post-carga.

### Flujo incremental con staging (patrón sugerido)
1. COPY a `staging_raw_consolidado`.
2. Validar duplicados / nulos.
3. INSERT SELECT hacia tabla final con transformación y deduplicación (ON CONFLICT DO NOTHING).

### Validaciones Post-Carga (SQL)
```sql
-- 1. Conteo por periodo
SELECT periodo, COUNT(*) total FROM final_num GROUP BY 1 ORDER BY 1;

-- 2. Duplicados id
SELECT periodo, COUNT(*) total, COUNT(DISTINCT id) distinct_ids
FROM final_num GROUP BY periodo HAVING COUNT(*) <> COUNT(DISTINCT id);

-- 3. Campos críticos nulos
SELECT periodo, COUNT(*) null_area FROM final_num WHERE area_m2 IS NULL GROUP BY periodo;

-- 4. Geometrías faltantes
SELECT COUNT(*) sin_geom FROM final_num WHERE geom IS NULL;

-- 5. Validación estadística básica precio
SELECT periodo, MIN(precio) min_p, MAX(precio) max_p FROM final_num GROUP BY periodo;

-- 6. Amenidades prevalencia (ejemplo alberca)
SELECT periodo, AVG(amen_alberca::int) AS pct_alberca FROM final_amenidades GROUP BY periodo;
```

### Regenerar geom (si se añadieron luego coordenadas)
```sql
UPDATE final_num SET geom = ST_SetSRID(ST_MakePoint(longitud,latitud),4326)
WHERE geom IS NULL AND longitud IS NOT NULL AND latitud IS NOT NULL;
```

### Limpieza / rollback por periodo
```sql
DELETE FROM final_amenidades WHERE periodo='Sep25';
DELETE FROM final_marketing  WHERE periodo='Sep25';
DELETE FROM final_num        WHERE periodo='Sep25';
```

### Indicadores de Calidad recomendados
- ratio_outliers_pxm2 (ver tablas estadístico_outliers / resumen_colonia)
- confidence_score_colonia (v_colony_stats / resumen_colonia_final)
- n_colonia y iqr_ratio para priorizar visualizaciones.

## Operación continua
1. Ejecutar script de ingesta para nuevo periodo.
2. Validar queries de control.
3. REFRESH MATERIALIZED VIEW si existen MV dependientes.
4. Ejecutar checklist de índices (ver `docs/INDEXING_PARTITIONING.md`).
5. Actualizar `docs/schema/` si hay nuevas columnas.

## Mejoras Futuras
- Particionado declarativo por periodo (ver `docs/INDEXING_PARTITIONING.md`).
- Materialized views para KPIs de dashboard (evitar recalcular).
- Job programado (GitHub Actions) para validar integridad nocturna.
- Métrica de drift (comparar distribución pxm2 entre periodos). 

## Troubleshooting rápido
| Problema | Posible causa | Acción |
|----------|---------------|--------|
| COPY falla por encoding | CSV con caracteres Latin-1 | Guardar en UTF-8 / usar iconv |
| Geom nulas tras carga | Faltan columnas lat/long o nombres distintos | Confirmar cabeceras y reconstruir |
| Lento en SELECT colonia | Falta índice (ciudad,colonia) | Crear índice sugerido |
| Duplicados id | CSV sin dedupe previo | Aplicar DISTINCT ON o hash pre-carga |
| Amenidades todas 0 | Archivo 0.Final_Ame no coincide en ids | Verificar join y periodo |


## GeoJSON a PostGIS (ejemplo comando ogr2ogr)
ogr2ogr -f "PostgreSQL" PG:"host=<HOST> user=<USER> dbname=<DB> password=<PWD>" \
  N1_Tratamiento/Geolocalizacion/Colonias/colonias-Guadalajara.geojson \
  -nln geo_colonias -nlt MULTIPOLYGON -lco GEOMETRY_NAME=geom -append

## Seguridad básica
- Revocar permisos públicos sobre tablas base.
- Crear rol readonly para analytics.
- En Supabase aplicar RLS si se necesita filtrar por ciudad.

## Próximos archivos
Ver ddl/*.sql y docs/*.md para más detalle.

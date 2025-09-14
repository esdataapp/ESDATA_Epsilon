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
   CREATE EXTENSION IF NOT EXISTS postgis;
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

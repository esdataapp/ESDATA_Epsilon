# Guía de Ingestión a Supabase

## 1. Preparar entorno local
Instala psql u ogr2ogr (GDAL) según necesidades geoespaciales.

## 2. Cargar tablas núcleo (DDL)
Ejecutar en orden:
01_core_final_num.sql
02_core_final_amenidades.sql
03_core_final_marketing.sql
04_geo_colonias.sql
05_metodos_representativos.sql
06_resumen_colonia.sql
07_estadistico_outliers.sql
08_estadistico_normalidad.sql
09_staging_raw_consolidado.sql
10_views.sql

## 3. Carga de datos (ejemplos COPY)
```sql
\COPY final_num FROM 'N5_Resultados/Nivel_1/CSV/0.Final_Num_Sep25.csv' CSV HEADER ENCODING 'UTF8';
\COPY final_amenidades FROM 'N5_Resultados/Nivel_1/CSV/0.Final_Ame_Sep25.csv' CSV HEADER ENCODING 'UTF8';
\COPY final_marketing FROM 'N5_Resultados/Nivel_1/CSV/0.Final_MKT_Sep25.csv' CSV HEADER ENCODING 'UTF8';
\COPY metodos_representativos FROM 'N5_Resultados/Nivel_1/CSV/metodos_representativos_Sep25.csv' CSV HEADER ENCODING 'UTF8';
```

Asegúrate de añadir la columna periodo si el CSV original no la trae (puedes usar staging + INSERT SELECT anexando periodo constante).

## 4. Poblado de geom en final_num
Si tus CSV sólo traen latitud / longitud:
```sql
UPDATE final_num SET geom = ST_SetSRID(ST_MakePoint(longitud, latitud), 4326)
WHERE geom IS NULL AND longitud IS NOT NULL AND latitud IS NOT NULL;
```

## 5. Carga GeoJSON Colonias
Opción 1 ogr2ogr (recomendado para muchos polígonos):
```
ogr2ogr -f "PostgreSQL" PG:"host=<HOST> dbname=<DB> user=<USER> password=<PWD>" \
  N1_Tratamiento/Geolocalizacion/Colonias/colonias-Guadalajara.geojson \
  -nln geo_colonias -nlt MULTIPOLYGON -lco GEOMETRY_NAME=geom -append
```
Opción 2 SQL manual (para pocos registros):
```sql
INSERT INTO geo_colonias(ciudad,colonia,slug_colonia,fuente,periodo_carga,geom)
VALUES ('Guadalajara','Country Club','country_club','geojson','Sep25',
        ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[...]}'),4326));
```

## 6. Índices adicionales sugeridos
```sql
CREATE INDEX IF NOT EXISTS idx_final_num_pxm2 ON final_num(pxm2);
CREATE INDEX IF NOT EXISTS idx_final_num_ciudad_colonia ON final_num(ciudad,colonia);
```

## 7. Calidad / Checks
- Conteo filas final_num = filas 0.Final_Num_* (por periodo)
- DISTINCT(id) = COUNT(*): garantizar sin duplicados
- Amenidades: verificar proporciones plausibles (0 <= ratio <= 1)
- Geometrías: ST_IsValid(geom) = true

## 8. Rollback / Reprocesos
Mantener staging separado permite TRUNCATE staging y reimportar sin tocar final_num.
Para reprocesar un periodo: DELETE FROM final_num WHERE periodo='Sep25'; luego COPY del nuevo CSV.

## 9. Automatización
Se puede preparar script Python que lea todos los CSV de N5_Resultados/Nivel_1/CSV y ejecute COPY dinámico.

## 10. Seguridad y Roles
- Crear rol readonly: GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
- Revocar INSERT/UPDATE/DELETE a readonly.
- (Opcional) RLS por ciudad si multi-tenant.

## 11. Vistas Materializadas (ejemplo)
```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_pxm2_ciudad AS
SELECT ciudad, periodo, AVG(pxm2) avg_pxm2, COUNT(*) n
FROM final_num
GROUP BY 1,2;
REFRESH MATERIALIZED VIEW mv_pxm2_ciudad;
```

## 12. Futuras ampliaciones
- Particionado nativo declarativo por periodo
- Tabla long para amenidades (amenidad, presente) si quieres queries flexibles
- Almacén de tokens TF-IDF (tabla final_tfidf_terms)

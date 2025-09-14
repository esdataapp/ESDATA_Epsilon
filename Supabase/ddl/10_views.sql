-- 10_views.sql
-- Vistas derivadas que emulan algunas salidas del dashboard sin recrear lógica en cliente.

CREATE OR REPLACE VIEW v_colony_stats AS
SELECT ciudad, colonia, operacion, tipo_propiedad, periodo,
       COUNT(*) AS n_propiedades,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pxm2) AS pxm2_mediana,
       AVG(pxm2) AS pxm2_media,
       MIN(pxm2) AS pxm2_min,
       MAX(pxm2) AS pxm2_max
FROM final_num
GROUP BY 1,2,3,4,5;

CREATE OR REPLACE VIEW v_amenity_presence AS
SELECT colonia, periodo,
       COUNT(*) FILTER (WHERE amen_alberca=1) *1.0 / NULLIF(COUNT(*),0) AS ratio_alberca,
       COUNT(*) FILTER (WHERE amen_gimnasio=1) *1.0 / NULLIF(COUNT(*),0) AS ratio_gimnasio
FROM final_amenidades
GROUP BY 1,2;

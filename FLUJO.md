# FLUJO DETALLADO DEL PIPELINE (ESDATA_Epsilon)

Este documento expande el README y describe decisiones de diseño, entradas, salidas, y puntos de control por paso.

## Convenciones
- Periodo: MesAño en formato `Sep25` (`datetime.now().strftime('%b%y')`).
- ID: `Periodo_<sha1:8>` basado en combinación (Periodo, Ciudad, operacion, tipo_propiedad, titulo, precio).
- Eliminaciones sólo en pasos: 5 (inválidos), 6 (duplicados), 8/9 (colonias <5 -> Esperando).

## Paso 1 — Consolidar y Adecuar
Script: `esdata/pipeline/step1_consolidar_adecuar.py`
Entradas: `Base_de_Datos/**/*.csv` (+ futuro: `Datos_Filtrados/Esperando/<PeriodoAnterior>/*.csv`).
Acciones:
- Unión vertical.
- Normalización abreviaturas (`Ciudad`, `operacion`, `tipo_propiedad`).
- Parseo fechas `Fecha_Scrap`.
- Extracción coords desde `ubicacion_url` (regex `center=lat,lon`).
- Cálculo `Banos_totales`.
- Generación `id`.
Salida: `N1_Tratamiento/Consolidados/<Per>/1.Consolidado_Adecuado_<Per>.csv`.
No elimina registros.

## Paso 2 — Procesamiento Geoespacial
Script: `esdata/geo/step2_procesamiento_geoespacial.py`
Entradas: Paso 1 + GeoJSON colonias (`N1_Tratamiento/Geolocalizacion/Colonias/`).
Acciones:
- Generación GeoDataFrame puntos (EPSG:4326).
- Spatial join `within` contra polígonos.
- Asignación `Colonia` y corrección `Ciudad`.
- Registros sin colonia -> `Datos_Filtrados/Eliminados/<Per>/sin_colonia_<Per>.csv` (retenidos para auditoría).
Salida: `2.Consolidado_ConColonia_<Per>.csv` (completa).

## Paso 3 — Versiones Especiales
Script: `esdata/pipeline/step3_versiones_especiales.py`
Entradas: Paso 2.
Acciones: Subset Num / Tex sin eliminar.
Salidas: `3a.Consolidado_Num_<Per>.csv`, `3b.Consolidado_Tex_<Per>.csv`.

## Paso 4 — Análisis Variables Texto (Placeholder)
Script: `esdata/text/step4_analisis_variables_texto.py`
Entradas: `3b.Consolidado_Tex_<Per>.csv`.
Acciones actuales: Regex básico para `recamaras_texto`, `banos_texto` desde título+descripción y bloque de características.
Salidas: `4a.Tex_Titulo_Descripcion_<Per>.csv`, `4b.Tex_Car_Ame_Ser_Ext_<Per>.csv`.
Futuro: NLP avanzado, extracción de amenidades estructuradas.

## Paso 5 — Análisis Lógico y Corroboración
Script: `esdata/pipeline/step5_analisis_logico_corroboracion.py`
Entradas: 3a + 4a.
Acciones:
- Merge num + texto derivado.
- Completar `recamaras`, `Banos_totales` usando texto si faltan.
- Filtrado registros sin `precio` o `area_m2` válidos.
Salidas: `5.Num_Corroborado_<Per>.csv` + invalidos a `Datos_Filtrados/Eliminados/<Per>/paso5_invalidos_<Per>.csv`.

## Paso 6 — Remover Duplicados
Script: `esdata/pipeline/step6_remover_duplicados.py`
Entradas: Paso 5 + 4a + 4b.
Acciones:
- Dedupe por `id`, fallback hash compuesto.
- Cálculo `PxM2` (num y marketing/amenidades).
- Filtrar marketing/amenidades por IDs finales.
Salidas: `0.Final_Num_<Per>.csv`, `0.Final_MKT_<Per>.csv`, `0.Final_Ame_<Per>.csv` + duplicados en `Datos_Filtrados/Duplicados/<Per>/`.

## Paso 7 — Estadísticas Básicas
Script: `esdata/estadistica/step7_estadisticas_variables.py`
Entradas: `0.Final_Num_<Per>.csv`.
Acciones: Descriptivos + IQR outliers + normalidad (skew/kurtosis) para `precio`, `area_m2`, `PxM2`.
Salidas:
- `N2_Estadisticas/Estudios/<Per>/F1_Descriptivo_<Per>.csv`
- `N2_Estadisticas/Estudios/<Per>/F1_Outliers_<Per>.csv`
- `N2_Estadisticas/Estudios/<Per>/F1_Normalidad_<Per>.csv`
- Reporte consolidado `N2_Estadisticas/Reportes/<Per>/Estadisticas_Global_<Per>.csv`.

## Paso 8 — Resumen por Colonia (Inicial y Final)
Script: `esdata/estadistica/step8_resumen_colonias.py`
Entradas: `0.Final_Num_<Per>.csv`.
Acciones:
- Cálculo inicial min/mean/max por colonia (todas).
- Versión final sólo colonias con `n>=5` aplicando método representativo (media vs mediana) y almacenando colonias pequeñas en `Esperando`.
Salidas: `<Ciudad>_<Oper>_<Tipo>_<Per>_inicial.csv` y `_final.csv` en `N5_Resultados/Nivel_1/CSV/Tablas/<Per>/`.

## Paso 9 — Separar por Colonia
Script: `esdata/estadistica/step9_separar_colonias.py`
Acciones: Un CSV por colonia (n>=5) dentro de jerarquía:
`N1_Tratamiento/Consolidados/Colonias/<Ciudad>/<Venta|Renta>/<Tipo>/<Per>/`
Nombre: `Ciudad_Oper_Tipo_Per_ColXXXX.csv` (abreviatura 7 chars).
Colonias n<5 -> Esperando.

## Paso 10 — Métodos Representativos Consolidado
Script: `esdata/estadistica/step10_metodos_representativos.py`
Acciones: Árbol de decisión final para `precio`,`area_m2`,`PxM2`; genera tabla consolidada de métodos y valores representativos.
Salida: `metodos_representativos_<Per>.csv` en Tablas.

## Árbol de Decisión (Resumen)
```
n < 5           -> no_estadistica / Esperando
5 <= n < 10     -> mediana_rango
n >= 10 & |skew| > 1 -> mediana_IQR
n >= 30 & |skew| <= 0.5 -> media_desv
Else             -> mediana_IQR
```

## Manejo de Colonias con <5 Propiedades
- Pasos 8 y 9 consolidan colonias pequeñas en archivos `esperando_<Ciudad>_<Oper>_<Tipo>_<Per>.csv`.
- Futuro: Paso 1 debe incorporar `Esperando/<PeriodoAnterior>` para aumentar n y promover colonias.

## Consideraciones de Calidad de Datos
- Control de tipos numéricos al normalizar (limpieza regex + float coercion).
- Prevenir división por cero en PxM2.
- Logging en cada paso con conteos antes/después.

## Extensiones Recomendadas
1. Integrar `scipy` para pruebas t / ANOVA en colonias n>=30.
2. Añadir validaciones de rango (ej. area_m2 < 10000, precio > 1000, etc.) parametrizadas.
3. Pipeline orquestado con un único comando (futuro `run_pipeline.py`).
4. Export GEOJSON union con estadísticos para visualización.
5. NLP avanzado (detección amenities, marketing score, sentimiento).

## Invariantes Propuestos para Pruebas
- `count(id)` no disminuye entre 1 y 4.
- `id` únicos después del paso 6.
- `PxM2` nulo sólo si falta `precio` o `area_m2`.
- `n` de colonias final + colonias Esperando == colonias inicial (paso 8) por combo.

## Ejemplo de Validación Rápida (pseudo)
```python
import pandas as pd, os
per='Sep25'
base='N1_Tratamiento/Consolidados/'+per
num=pd.read_csv(os.path.join(base,f'3a.Consolidado_Num_{per}.csv'))
tex=pd.read_csv(os.path.join(base,f'3b.Consolidado_Tex_{per}.csv'))
assert len(num)==len(tex)  # Sin pérdidas antes del paso 5
```

## Registro de Cambios (Changelog Resumido)
- v0.1: Arquitectura modular, pasos 1–10 implementados, placeholder NLP.

---
Última actualización: 2025-09-13

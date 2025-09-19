# 🔄 Flujo de Trabajo ESDATA_Epsilon

## 📊 Resumen Ejecutivo

El pipeline ESDATA_Epsilon procesa datos inmobiliarios a través de **8 pasos secuenciales**, cada uno con objetivos específicos y validaciones automáticas. El proceso transforma datos crudos de múltiples fuentes en información estructurada y confiable para análisis de mercado.

## 🎯 Objetivo General

Procesar y analizar datos inmobiliarios de Guadalajara y Zapopan, México, generando reportes estadísticos confiables y geoespacialmente precisos para análisis de mercado inmobiliario.

---

## 📝 Pipeline Detallado

### 🔧 Step 1: Consolidación y Adecuación
**Archivo**: `esdata/pipeline/step1_consolidar_adecuar.py`

#### 🎯 **Objetivo**
Unificar múltiples archivos CSV fuente, normalizar nombres de columnas, estandarizar valores, y extraer precios con conversión de divisas.

#### 📥 **Entrada**
- Múltiples archivos CSV en `Base_de_Datos/{periodo}/`
- Archivo de configuración: `Lista de Variables Orquestacion.csv`

#### 🔄 **Proceso Principal**

1. **Lectura y Unificación**
   ```python
   # Lee todos los CSV del directorio base
   archivos_csv = glob.glob(f"{base_dir}/*.csv")
   df_consolidado = pd.concat([pd.read_csv(f) for f in archivos_csv])
   ```

2. **Mapeo de Columnas**
   ```python
   COLUMN_NAME_MAPPING = {
       'Precio': 'precio',
       'Superficie': 'area_m2', 
       'Operación': 'operacion',
       'Tipo de Propiedad': 'tipo_propiedad',
       # ... más mapeos
   }
   ```

3. **Extracción de Precios**
   ```python
   def _extract_precio(precio_str):
       # Formatos: "rentaUSD 1,650", "ventaMN 10,650,000"
       if 'USD' in precio_str:
           return float(precio_numerico) * 20  # USD → MN
       return float(precio_numerico)
   ```

4. **Estandarización de Valores**
   - Normalización usando CSV de configuración
   - Limpieza de caracteres especiales
   - Unificación de formatos

#### 📤 **Salida**
- `N1_Tratamiento/Consolidados/{periodo}/1.Consolidado_Adecuado_{periodo}.csv`
- **Métricas**: Total propiedades, columnas procesadas, precios extraídos

#### 🚨 **Validaciones**
- ✅ Verificación de columnas requeridas
- ✅ Validación de formatos de precio
- ✅ Control de duplicación de registros

---

### 🗺️ Step 2: Procesamiento Geoespacial
**Archivo**: `esdata/geo/step2_procesamiento_geoespacial.py`

#### 🎯 **Objetivo**
Asignar colonias y ciudades usando polígonos GeoJSON, validar coordenadas y mantener coherencia geoespacial.

#### 📥 **Entrada**
- `1.Consolidado_Adecuado_{periodo}.csv`
- GeoJSON de colonias: `N1_Tratamiento/Geolocalizacion/GEOJSON/`

#### 🔄 **Proceso Principal**

1. **Carga de Geometrías**
   ```python
   gdf_colonias = gpd.read_file("colonias.geojson")
   points = gpd.points_from_xy(df.longitud, df.latitud)
   ```

2. **Asignación Espacial**
   ```python
   # Spatial join para asignar colonia
   df_geo = gpd.sjoin(gdf_points, gdf_colonias, how='left', predicate='within')
   ```

3. **Validación de Coherencia**
   ```python
   # Coherencia: sin colonia → sin ciudad
   sin_colonia_mask = df['colonia'] == 'Desconocido'
   df.loc[sin_colonia_mask, 'Ciudad'] = 'Desconocido'
   ```

#### 📤 **Salida**
- `2.Consolidado_ConColonia_{periodo}.csv`
- **Métricas**: Propiedades con/sin colonia, cobertura por ciudad

#### 🚨 **Validaciones**
- ✅ Coordenadas válidas (lat/lon en rangos)
- ✅ Coherencia geoespacial
- ✅ Verificación de asignación de colonias

---

### 🔀 Step 3: Versiones Especiales
**Archivo**: `esdata/pipeline/step3_versiones_especiales.py`

#### 🎯 **Objetivo**
Generar versiones específicas de datos filtrados para diferentes análisis.

#### 📥 **Entrada**
- `2.Consolidado_ConColonia_{periodo}.csv`

#### 🔄 **Proceso Principal**
1. Filtrado por criterios específicos
2. Generación de subconjuntos especializados
3. Validación de consistencia

#### 📤 **Salida**
- Múltiples archivos CSV especializados
- Versiones para diferentes tipos de análisis

---

### 📝 Step 4: Análisis de Variables de Texto
**Archivo**: `esdata/text/step4_analisis_variables_texto.py`

#### 🎯 **Objetivo**
Procesar y analizar variables textuales, extraer características y patrones.

#### 📥 **Entrada**
- Archivos del Step 3

#### 🔄 **Proceso Principal**
1. Análisis de longitud de textos
2. Extracción de características
3. Clasificación de contenido
4. Detección de patrones

#### 📤 **Salida**
- Archivos con variables textuales procesadas
- Reportes de análisis de texto

---

### ✅ Step 5: Análisis Lógico y Corroboración
**Archivo**: `esdata/pipeline/step5_analisis_logico_corroboracion.py`

#### 🎯 **Objetivo**
Aplicar filtros de calidad específicos por tipo de propiedad y operación, eliminando propiedades que no cumplen criterios lógicos.

#### 📥 **Entrada**
- Archivos procesados del Step 4

#### 🔄 **Proceso Principal**

1. **Normalización de Operaciones**
   ```python
   def _normalize_operation(op):
       if op in ['venta', 'Venta', 'VENTA']:
           return 'Ven'
       elif op in ['renta', 'Renta', 'RENTA']:
           return 'Ren'
       return op
   ```

2. **Aplicación de Filtros por Tipo**
   ```python
   PROPERTY_CONDITIONS = {
       'Cas': {  # Casa
           'venta': {'precio': (500000, 50000000), 'area_m2': (50, 2000)},
           'renta': {'precio': (5000, 100000), 'area_m2': (50, 2000)}
       },
       'Dep': {  # Departamento
           'venta': {'precio': (400000, 30000000), 'area_m2': (25, 800)},
           'renta': {'precio': (4000, 80000), 'area_m2': (25, 800)}
       }
       # ... más tipos
   }
   ```

#### 📤 **Salida**
- `Final_Num_{periodo}.csv`
- **Métricas**: Propiedades filtradas, razones de exclusión

#### 🚨 **Validaciones**
- ✅ Rangos lógicos por tipo de propiedad
- ✅ Consistencia operación-precio
- ✅ Valores atípicos detectados

---

### 🔄 Step 6: Remoción de Duplicados
**Archivo**: `esdata/pipeline/step6_remover_duplicados.py`

#### 🎯 **Objetivo**
Eliminar propiedades duplicadas manteniendo consistencia entre archivos Final_Num, Final_AME y Final_MKT.

#### 📥 **Entrada**
- `Final_Num_{periodo}.csv`
- Archivos relacionados de amenidades y marketing

#### 🔄 **Proceso Principal**

1. **Detección de Duplicados**
   ```python
   # Criterios jerárquicos de duplicación
   duplicados = df.groupby(['latitud', 'longitud', 'precio', 'area_m2'])
   ```

2. **Preservación Consistente**
   ```python
   # LEFT JOIN para mantener consistencia
   final_ame = pd.merge(ids_finales, df_ame, on='id', how='left')
   final_mkt = pd.merge(ids_finales, df_mkt, on='id', how='left')
   ```

#### 📤 **Salida**
- `Final_Num_{periodo}.csv` (sin duplicados)
- `Final_AME_{periodo}.csv` 
- `Final_MKT_{periodo}.csv`
- **Garantía**: Misma cantidad de registros en los 3 archivos

#### 🚨 **Validaciones**
- ✅ Consistencia entre archivos finales
- ✅ Preservación de registros únicos
- ✅ Verificación de conteos

---

### 📊 Step 7: Estadísticas de Variables
**Archivo**: `esdata/estadistica/step7_estadisticas_variables.py`

#### 🎯 **Objetivo**
Calcular estadísticas descriptivas exhaustivas para todas las variables del dataset.

#### 📥 **Entrada**
- Archivos Final_{tipo}_{periodo}.csv

#### 🔄 **Proceso Principal**
1. **Análisis por Tipo de Variable**
   - Numéricas: media, mediana, std, percentiles
   - Categóricas: frecuencias, modos
   - Textuales: longitudes, patrones

2. **Detección Automática de Tipos**
   ```python
   def detectar_tipo_variable(serie):
       if serie.dtype in ['int64', 'float64']:
           return 'numerica'
       elif len(serie.unique()) / len(serie) < 0.1:
           return 'categorica'
       return 'textual'
   ```

#### 📤 **Salida**
- `N2_Estadisticas/Reportes/{periodo}/estadisticas_variables.csv`
- Reportes especializados por tipo de variable

---

### 🏘️ Step 8: Resumen por Colonias
**Archivo**: `esdata/estadistica/step8_resumen_colonias.py`

#### 🎯 **Objetivo**
Generar reportes especializados por colonia, tablero maestro de cobertura y archivo de puntos finales.

#### 📥 **Entrada**
- Archivos finales procesados
- GeoJSON completo de colonias

#### 🔄 **Proceso Principal**

1. **Generación Final_Puntos**
   ```python
   def generar_final_puntos():
       # Combina TODOS los datos finales SIN filtro de colonia
       df_final = pd.read_csv(final_num_path)
       df_final.to_csv(final_puntos_path)
   ```

2. **Tablero Maestro de Colonias**
   ```python
   def generar_tablero_maestro_colonias():
       # Incluye TODAS las 1,062 colonias del GeoJSON
       cobertura_completa = merge(todas_colonias, datos, how='left')
   ```

3. **Estadísticas por Colonia**
   - Cantidad de propiedades por colonia
   - Precio promedio/mediano por colonia
   - Tipos de propiedad más comunes
   - Métricas de mercado

#### 📤 **Salida**
- `N5_Resultados/Nivel_1/CSV/Final_Puntos_{periodo}.csv`
- `N2_Estadisticas/Reportes/{periodo}/tablero_maestro_colonias.csv`
- Reportes individuales por colonia

#### 🚨 **Validaciones**
- ✅ Cobertura completa de colonias (1,062)
- ✅ Métricas de calidad por colonia
- ✅ Análisis de gaps de información

---

## 🎯 Métricas de Calidad Global

### 📈 **Indicadores de Rendimiento** (Sep25)

| Paso | Entrada | Salida | Filtrado | Porcentaje |
|------|---------|--------|----------|------------|
| **Step 1** | ~30,000 | 25,851 | 4,149 | 86.2% |
| **Step 2** | 25,851 | 25,815 | 36 | 99.9% |
| **Step 5** | 25,815 | 24,853 | 962 | 96.3% |
| **Step 6** | 24,853 | 24,853 | 0 | 100% |

### 🗺️ **Cobertura Geoespacial**

- **Total Colonias**: 1,062 (GeoJSON)
- **Colonias con Datos**: 423 (39.8%)
- **Zapopan**: 770 colonias → 291 con datos (37.8%)
- **Guadalajara**: 292 colonias → 132 con datos (45.2%)

---

## 🚀 Ejecución del Pipeline

### ⚡ **Ejecución Secuencial**

```bash
#!/bin/bash
# Script de ejecución completa

PERIODO="Sep25"

echo "🚀 Iniciando Pipeline ESDATA_Epsilon para $PERIODO"

echo "📊 Step 1: Consolidación..."
python -m esdata.pipeline.step1_consolidar_adecuar $PERIODO

echo "🗺️ Step 2: Geoespacial..."
python -m esdata.geo.step2_procesamiento_geoespacial $PERIODO

echo "🔀 Step 3: Versiones Especiales..."
python -m esdata.pipeline.step3_versiones_especiales $PERIODO

echo "📝 Step 4: Variables Texto..."
python -m esdata.text.step4_analisis_variables_texto $PERIODO

echo "✅ Step 5: Validación Lógica..."
python -m esdata.pipeline.step5_analisis_logico_corroboracion $PERIODO

echo "🔄 Step 6: Duplicados..."
python -m esdata.pipeline.step6_remover_duplicados $PERIODO

echo "📊 Step 7: Estadísticas..."
python -m esdata.estadistica.step7_estadisticas_variables $PERIODO

echo "🏘️ Step 8: Colonias..."
python -m esdata.estadistica.step8_resumen_colonias $PERIODO

echo "✅ Pipeline completado para $PERIODO"
```

### 🔍 **Monitoreo de Progreso**

Cada paso genera logs detallados con:
- ✅ Emojis para identificación rápida
- 📊 Estadísticas de entrada/salida
- ⏱️ Tiempos de ejecución
- 🚨 Alertas de calidad
- 📈 Métricas de cobertura

### 🐛 **Manejo de Errores**

- **Archivos de Respaldo**: Se crean automáticamente antes de modificaciones
- **Logging Detallado**: Cada error incluye contexto completo
- **Validaciones Cruzadas**: Verificación en cada paso
- **Rollback Automático**: En caso de fallas críticas

---

## 🎯 Resultados Esperados

### 📊 **Archivos Finales**

1. **`Final_Puntos_{periodo}.csv`**: Todas las propiedades válidas con ubicación precisa
2. **`tablero_maestro_colonias.csv`**: Cobertura completa de 1,062 colonias
3. **Reportes Estadísticos**: Análisis detallados por variable y colonia

### 🏆 **Garantías de Calidad**

- ✅ **100% de precios válidos** (con conversión USD)
- ✅ **99.9% de coordenadas válidas**
- ✅ **96.1% de propiedades con colonia asignada**
- ✅ **Consistencia geoespacial completa**
- ✅ **Eliminación total de duplicados**

---

## 🔧 Convenciones Técnicas

### 📋 **Formato de Identificadores**
- **Periodo**: `MesAño` en formato `Sep25` 
- **ID**: `Periodo_<sha1:8>` basado en combinación (Periodo, Ciudad, operacion, tipo_propiedad, titulo, precio)

### 🗂️ **Manejo de Eliminaciones**
- **Paso 5**: Propiedades inválidas → `Datos_Filtrados/Eliminados/`
- **Paso 6**: Duplicados → `Datos_Filtrados/Duplicados/`
- **Paso 8**: Colonias <5 propiedades → `Datos_Filtrados/Esperando/`

### 📊 **Árbol de Decisión Estadístico**
```
n < 5           -> no_estadistica / Esperando
5 <= n < 10     -> mediana_rango
n >= 10 & |skew| > 1 -> mediana_IQR
n >= 30 & |skew| <= 0.5 -> media_desv
Else             -> mediana_IQR
```

---

## 🔄 Invariantes y Validaciones

### ✅ **Garantías del Sistema**
- `count(id)` no disminuye entre pasos 1-4
- `id` únicos después del paso 6
- `PxM2` nulo sólo si falta `precio` o `area_m2`
- Consistencia entre archivos Final_Num, Final_AME, Final_MKT

### 🧪 **Ejemplo de Validación**
```python
import pandas as pd, os
per='Sep25'
base='N1_Tratamiento/Consolidados/'+per
num=pd.read_csv(os.path.join(base,f'3a.Consolidado_Num_{per}.csv'))
tex=pd.read_csv(os.path.join(base,f'3b.Consolidado_Tex_{per}.csv'))
assert len(num)==len(tex)  # Sin pérdidas antes del paso 5
```

---

## 🚀 Extensiones Futuras

1. **Integrar `scipy`** para pruebas t / ANOVA en colonias n>=30
2. **Validaciones paramétricas** de rango (area_m2 < 10000, precio > 1000)
3. **Pipeline orquestado** con un único comando
4. **Export GEOJSON** union con estadísticos para visualización
5. **NLP avanzado** (detección amenities, marketing score, sentimiento)

---

*Este flujo ha sido optimizado y validado para maximizar la calidad y confiabilidad de los datos inmobiliarios procesados.*

---

**🔄 ESDATA_Epsilon Pipeline** - *Septiembre 2025* ✨

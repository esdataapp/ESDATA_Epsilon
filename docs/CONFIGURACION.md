# ⚙️ Guía de Configuración ESDATA_Epsilon

## 📋 Descripción General

Este documento detalla todas las opciones de configuración disponibles en el pipeline ESDATA_Epsilon, incluyendo parámetros por defecto, customización avanzada y mejores prácticas.

---

## 🔧 Configuración Principal

### 📂 **Estructura de Directorios**

El pipeline requiere la siguiente estructura de directorios (se crea automáticamente):

```
ESDATA_Epsilon/
├── Base_de_Datos/              # 📥 Datos fuente
│   └── {periodo}/              # Ej: Sep25/
├── N1_Tratamiento/             # 🔄 Datos procesados
│   ├── Consolidados/{periodo}/ # Archivos principales
│   └── Geolocalizacion/        # GeoJSON de colonias
├── N2_Estadisticas/            # 📊 Reportes estadísticos  
│   ├── Estudios/{periodo}/     # Análisis detallados
│   └── Reportes/{periodo}/     # Resúmenes ejecutivos
├── N5_Resultados/              # 🎯 Salidas finales
│   └── Nivel_1/CSV/           # Archivos principales
└── Datos_Filtrados/           # 🗑️ Propiedades eliminadas
    ├── Duplicados/{periodo}/   # Duplicados removidos
    ├── Eliminados/{periodo}/   # Inválidos filtrados
    └── Esperando/{periodo}/    # Colonias <5 propiedades
```

### 🔑 **Variables de Configuración**

#### **Configuración por Código**

```python
# esdata/utils/paths.py - Configuración de rutas
BASE_DIR = "C:\\Users\\criss\\Desktop\\ESDATA_Epsilon"
GEOJSON_PATH = f"{BASE_DIR}\\N1_Tratamiento\\Geolocalizacion\\GEOJSON"

# Estructura automática de directorios
REQUIRED_DIRS = [
    "Base_de_Datos",
    "N1_Tratamiento/Consolidados", 
    "N2_Estadisticas/Estudios",
    "N2_Estadisticas/Reportes",
    "N5_Resultados/Nivel_1/CSV",
    "Datos_Filtrados/Duplicados",
    "Datos_Filtrados/Eliminados", 
    "Datos_Filtrados/Esperando"
]
```

#### **Variables de Entorno (Opcional)**

```bash
# .env file
ESDATA_BASE_PATH=C:\Users\criss\Desktop\ESDATA_Epsilon
ESDATA_LOG_LEVEL=INFO
ESDATA_GEOJSON_PATH=custom/path/to/geojson
ESDATA_CHUNK_SIZE=5000
ESDATA_MAX_WORKERS=4
```

---

## 📊 Configuración por Paso

### 🔧 **Step 1: Consolidación y Adecuación**

#### **Mapeo de Columnas** (`step1_consolidar_adecuar.py`)

```python
COLUMN_NAME_MAPPING = {
    # Información básica
    'Precio': 'precio',
    'Superficie': 'area_m2',
    'Operación': 'operacion', 
    'Tipo de Propiedad': 'tipo_propiedad',
    'Ciudad': 'Ciudad',
    
    # Características de la propiedad
    'Recámaras': 'recamaras',
    'Baños': 'banos_completos',
    'Medio Baño': 'medio_banos',
    'Estacionamientos': 'estacionamientos',
    
    # Ubicación
    'Latitud': 'latitud',
    'Longitud': 'longitud',
    'Dirección': 'direccion',
    'Colonia': 'colonia',
    
    # Información adicional
    'Título': 'titulo',
    'Descripción': 'descripcion',
    'URL': 'url_inmueble',
    'Fecha Scraping': 'fecha_scrap'
}
```

#### **Conversión de Precios USD→MN**

```python
# Factor de conversión (configurable)
USD_TO_MN_RATE = 20.0

def _extract_precio(precio_str):
    """
    Formatos soportados:
    - rentaUSD 1,650
    - ventaMN 10,650,000  
    - $1,500,000 MN
    - $2,500 USD
    """
    if 'USD' in precio_str:
        return precio_numerico * USD_TO_MN_RATE
    return precio_numerico
```

#### **Estandarización de Valores**

```python
# Archivo: Lista de Variables Orquestacion.csv
# Formato: columna,valor_original,valor_estandarizado

# Ejemplo de contenido:
# Ciudad,guadalajara,Guadalajara
# Ciudad,zapopan,Zapopan  
# Ciudad,gdl,Guadalajara
# operacion,venta,Ven
# operacion,renta,Ren
# tipo_propiedad,casa,Cas
# tipo_propiedad,departamento,Dep
```

---

### 🗺️ **Step 2: Procesamiento Geoespacial**

#### **Configuración de Colonias**

```python
# Archivos GeoJSON requeridos
GEOJSON_FILES = {
    'guadalajara': 'Guadalajara_Colonias.geojson',
    'zapopan': 'Zapopan_Colonias.geojson'
}

# Proyección espacial
CRS_GEOGRAFICO = 'EPSG:4326'    # WGS84 para coordenadas lat/lon
CRS_PROYECTADO = 'EPSG:32613'   # UTM Zone 13N para cálculos de área
```

#### **Validación de Coordenadas**

```python
# Límites geográficos para Guadalajara/Zapopan
COORD_BOUNDS = {
    'lat_min': 20.500,    # Límite sur
    'lat_max': 20.800,    # Límite norte  
    'lon_min': -103.500,  # Límite oeste
    'lon_max': -103.200   # Límite este
}
```

#### **Coherencia Geoespacial**

```python
# Reglas de coherencia automática
COHERENCE_RULES = {
    # Si no hay colonia asignada → Ciudad = "Desconocido"
    'sin_colonia_sin_ciudad': True,
    
    # Validar que colonia pertenezca a ciudad declarada
    'validar_colonia_ciudad': True,
    
    # Corregir ciudad basada en colonia asignada
    'corregir_ciudad_por_colonia': True
}
```

---

### ✅ **Step 5: Validación Lógica**

#### **Rangos de Validación por Tipo**

```python
PROPERTY_CONDITIONS = {
    'Cas': {  # Casa
        'venta': {
            'precio': (500_000, 50_000_000),      # 500K - 50M MN
            'area_m2': (50, 2000)                 # 50 - 2000 m²
        },
        'renta': {
            'precio': (5_000, 100_000),           # 5K - 100K MN/mes
            'area_m2': (50, 2000)
        }
    },
    'Dep': {  # Departamento
        'venta': {
            'precio': (400_000, 30_000_000),      # 400K - 30M MN
            'area_m2': (25, 800)                  # 25 - 800 m²
        },
        'renta': {
            'precio': (4_000, 80_000),            # 4K - 80K MN/mes
            'area_m2': (25, 800)
        }
    },
    'CasC': {  # Casa en Condominio
        'venta': {
            'precio': (600_000, 40_000_000),
            'area_m2': (60, 1500)
        },
        'renta': {
            'precio': (6_000, 90_000), 
            'area_m2': (60, 1500)
        }
    },
    'Ter': {  # Terreno
        'venta': {
            'precio': (200_000, 100_000_000),
            'area_m2': (100, 10000)               # 100 - 10000 m²
        }
        # Terrenos generalmente no se rentan
    },
    'LocC': {  # Local Comercial
        'venta': {
            'precio': (300_000, 20_000_000),
            'area_m2': (20, 1000)                 # 20 - 1000 m²
        },
        'renta': {
            'precio': (3_000, 50_000),
            'area_m2': (20, 1000)
        }
    },
    'Ofc': {  # Oficina
        'venta': {
            'precio': (200_000, 15_000_000),
            'area_m2': (15, 500)                  # 15 - 500 m²
        },
        'renta': {
            'precio': (2_000, 30_000),
            'area_m2': (15, 500)
        }
    }
}
```

#### **Normalización de Operaciones**

```python
OPERATION_MAPPING = {
    # Variantes de venta
    'venta': 'Ven',
    'Venta': 'Ven', 
    'VENTA': 'Ven',
    'vende': 'Ven',
    'se_vende': 'Ven',
    
    # Variantes de renta  
    'renta': 'Ren',
    'Renta': 'Ren',
    'RENTA': 'Ren', 
    'rente': 'Ren',
    'se_renta': 'Ren',
    'alquiler': 'Ren'
}
```

---

### 🔄 **Step 6: Eliminación de Duplicados**

#### **Criterios de Duplicación**

```python
DUPLICATE_CRITERIA = [
    # Criterio primario: ID exacto
    ['id'],
    
    # Criterio secundario: ubicación + precio + área
    ['latitud', 'longitud', 'precio', 'area_m2'],
    
    # Criterio terciario: ubicación + características básicas
    ['latitud', 'longitud', 'recamaras', 'banos_completos'],
    
    # Criterio cuaternario: título similar + precio similar
    ['titulo_hash', 'precio_rango']
]
```

#### **Tolerancias para Duplicados**

```python
DUPLICATE_TOLERANCES = {
    'coordenadas': 0.0001,      # ~11 metros de diferencia
    'precio_pct': 0.05,         # 5% de diferencia en precio
    'area_pct': 0.10,           # 10% de diferencia en área
    'titulo_similarity': 0.85    # 85% similitud en título
}
```

---

### 📊 **Step 7: Análisis Estadístico**

#### **Configuración de Outliers**

```python
OUTLIER_CONFIG = {
    # Métodos de detección
    'iqr_multiplier': 1.5,        # Factor IQR estándar
    'z_score_threshold': 3.0,     # Z-score para outliers extremos
    'modified_z_threshold': 3.5,  # Z-score modificado (usando mediana)
    
    # Variables a analizar
    'numeric_vars': ['precio', 'area_m2', 'PxM2', 'recamaras', 'banos_completos'],
    
    # Percentiles de interés
    'percentiles': [1, 5, 10, 25, 50, 75, 90, 95, 99]
}
```

#### **Pruebas de Normalidad**

```python
NORMALITY_TESTS = {
    'skewness_threshold': 0.5,      # Umbral para considerar asimetría
    'kurtosis_threshold': 3.0,      # Umbral para considerar curtosis
    'shapiro_wilk_max_n': 5000,     # Max muestras para Shapiro-Wilk
    'anderson_darling': True,       # Habilitar test Anderson-Darling
    'kolmogorov_smirnov': True      # Habilitar test KS
}
```

---

### 🏘️ **Step 8: Resumen por Colonias**

#### **Métodos Representativos**

```python
# Árbol de decisión para método estadístico
REPRESENTATIVE_METHODS = {
    'rules': [
        # n < 5: No estadística
        {'condition': 'n < 5', 'method': 'no_estadistica'},
        
        # 5 ≤ n < 10: Mediana con rango
        {'condition': '5 <= n < 10', 'method': 'mediana_rango'},
        
        # n ≥ 10 y |skew| > 1: Mediana con IQR
        {'condition': 'n >= 10 and abs(skew) > 1', 'method': 'mediana_IQR'},
        
        # n ≥ 30 y |skew| ≤ 0.5: Media con desviación
        {'condition': 'n >= 30 and abs(skew) <= 0.5', 'method': 'media_desv'},
        
        # Otro caso: Mediana con IQR
        {'condition': 'else', 'method': 'mediana_IQR'}
    ]
}
```

#### **Umbrales de Colonias**

```python
COLONIA_THRESHOLDS = {
    'min_propiedades': 5,         # Mínimo para análisis estadístico
    'reportar_todas': True,       # Incluir colonias sin datos en tablero
    'separar_por_ciudad': True,   # Reportes separados por ciudad
    'incluir_sin_colonia': True   # Incluir propiedades sin colonia
}
```

---

## 🔐 Configuración Avanzada

### 📊 **Logging y Monitoreo**

```python
# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO',              # DEBUG, INFO, WARNING, ERROR
    'format': '[%(asctime)s] %(levelname)s: %(message)s',
    'use_emojis': True,           # Emojis en mensajes de log
    'detailed_stats': True,       # Estadísticas detalladas
    'progress_bars': True,        # Barras de progreso con tqdm
    'color_output': True          # Colores en terminal (colorama)
}

# Emojis por tipo de mensaje
LOG_EMOJIS = {
    'info': 'ℹ️',
    'success': '✅', 
    'warning': '⚠️',
    'error': '🚨',
    'processing': '🔄',
    'stats': '📊',
    'geo': '🗺️',
    'filter': '🔍'
}
```

### 🚀 **Configuración de Performance**

```python
PERFORMANCE_CONFIG = {
    # Procesamiento en chunks
    'chunk_size': 5000,           # Tamaño de chunks para datasets grandes
    'use_multiprocessing': False, # Multiprocesamiento (requiere más memoria)
    'max_workers': 4,             # Workers para procesamiento paralelo
    
    # Optimizaciones de memoria
    'low_memory_mode': False,     # Modo de baja memoria (más lento)
    'garbage_collect': True,      # Garbage collection frecuente
    
    # Formatos de archivo
    'prefer_parquet': False,      # Usar Parquet en lugar de CSV
    'compression': 'gzip'         # Compresión para archivos temporales
}
```

### 🔒 **Validaciones y Calidad**

```python
QUALITY_CHECKS = {
    # Validaciones automáticas
    'check_required_columns': True,     # Verificar columnas requeridas
    'validate_data_types': True,        # Validar tipos de datos
    'check_coordinate_bounds': True,    # Validar límites de coordenadas
    'verify_file_integrity': True,      # Verificar integridad de archivos
    
    # Umbrales de alerta
    'max_null_percentage': 0.10,        # Max 10% valores nulos
    'min_valid_coordinates': 0.95,      # Min 95% coordenadas válidas  
    'max_duplicate_percentage': 0.05,   # Max 5% duplicados
    
    # Backup automático
    'create_backups': True,             # Crear respaldos antes de modificar
    'backup_retention_days': 30         # Retener respaldos por 30 días
}
```

---

## 🛠️ Personalización y Extensiones

### 🔧 **Agregar Nuevos Tipos de Propiedad**

1. **Actualizar `PROPERTY_CONDITIONS`**:
```python
PROPERTY_CONDITIONS['NuevoTipo'] = {
    'venta': {'precio': (min_precio, max_precio), 'area_m2': (min_area, max_area)},
    'renta': {'precio': (min_precio, max_precio), 'area_m2': (min_area, max_area)}
}
```

2. **Agregar al mapeo de estandarización**:
```csv
# En Lista de Variables Orquestacion.csv
tipo_propiedad,nuevo_tipo,NuevoTipo
```

### 🗺️ **Agregar Nuevas Ciudades**

1. **Agregar GeoJSON de colonias** en `N1_Tratamiento/Geolocalizacion/GEOJSON/`

2. **Actualizar configuración geoespacial**:
```python
GEOJSON_FILES['nueva_ciudad'] = 'NuevaCiudad_Colonias.geojson'
```

3. **Actualizar límites de coordenadas**:
```python
COORD_BOUNDS_NUEVA_CIUDAD = {
    'lat_min': lat_min, 'lat_max': lat_max,
    'lon_min': lon_min, 'lon_max': lon_max
}
```

### 📊 **Configurar Nuevos Análisis Estadísticos**

```python
# Agregar nuevas variables numéricas
ADDITIONAL_NUMERIC_VARS = ['nueva_variable_numerica']

# Agregar nuevas pruebas estadísticas  
CUSTOM_STATISTICAL_TESTS = {
    'test_personalizado': {
        'function': custom_test_function,
        'params': {'param1': value1}
    }
}
```

---

## 🚨 Troubleshooting de Configuración

### ❌ **Problemas Comunes**

1. **Error: Directorio no encontrado**
   - **Causa**: Estructura de directorios incompleta
   - **Solución**: Ejecutar `verificar_estructura()` desde `esdata.utils.paths`

2. **Error: GeoJSON no encontrado**
   - **Causa**: Archivos GeoJSON faltantes o ruta incorrecta
   - **Solución**: Verificar existencia de archivos en `GEOJSON_PATH`

3. **Error: Columnas faltantes**
   - **Causa**: `COLUMN_NAME_MAPPING` incompleto
   - **Solución**: Actualizar mapeos para nuevos formatos de datos

4. **Warning: Muchos valores fuera de rango**
   - **Causa**: `PROPERTY_CONDITIONS` muy restrictivos
   - **Solución**: Ajustar rangos o revisar calidad de datos fuente

### 🔧 **Comandos de Diagnóstico**

```python
# Verificar configuración completa
from esdata.utils.paths import verificar_configuracion
verificar_configuracion()

# Validar estructura de datos
from esdata.utils.validation import validar_dataset
validar_dataset('ruta/al/archivo.csv')

# Probar conectividad geoespacial
from esdata.geo.validation import test_geojson_loading
test_geojson_loading()
```

---

## 📝 Best Practices

### ✅ **Recomendaciones**

1. **Backup de Configuración**: Mantener copias de archivos de configuración críticos
2. **Versionado**: Usar control de versiones para cambios en configuración
3. **Testing**: Probar configuraciones en datasets pequeños primero
4. **Documentación**: Documentar cambios personalizados para el equipo
5. **Monitoreo**: Revisar logs regularmente para detectar problemas

### 📊 **Optimización de Rendimiento**

1. **Datasets Grandes (>50K propiedades)**:
   - Habilitar `chunk_size` apropiado
   - Considerar `prefer_parquet = True`
   - Usar `low_memory_mode` si es necesario

2. **Análisis Geoespacial Intensivo**:
   - Optimizar tolerancias de duplicados
   - Usar índices espaciales cuando sea posible
   - Simplificar geometrías si no se requiere precisión extrema

3. **Procesamiento Frecuente**:
   - Implementar cache de resultados intermedios
   - Usar procesamiento incremental cuando sea posible
   - Automatizar limpieza de archivos temporales

---

**⚙️ Configuración ESDATA_Epsilon** - *Septiembre 2025* ✨

*Para soporte técnico o consultas sobre configuración, consultar la documentación adicional en `/docs/` o contactar al equipo de desarrollo.*
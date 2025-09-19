# 🛠️ Guía de Solución de Problemas - ESDATA_Epsilon

## 🎯 Descripción General

Esta guía proporciona soluciones paso a paso para los problemas más comunes encontrados al ejecutar el pipeline ESDATA_Epsilon. Incluye diagnósticos, soluciones rápidas y prevención de errores.

---

## 🚨 Problemas Críticos y Soluciones

### 🔥 **ERROR CRÍTICO: 'operacion' Column All "Desconocido"**

**Síntomas**:
```bash
# Todas las propiedades muestran operacion = "Desconocido"
df['operacion'].value_counts()
# Desconocido    25851
```

**Causa**: Variable `operacion` en `TEXT_COLUMNS_DESCONOCIDO` siendo sobrescrita

**Solución**:
```python
# En step1_consolidar_adecuar.py
# REMOVER 'operacion' de esta lista:
TEXT_COLUMNS_DESCONOCIDO = [
    'direccion', 'colonia', 'descripcion', 'titulo',
    'caracteristicas', 'amenidades', 'servicios', 'exteriores'
    # ❌ NO incluir 'operacion' aquí
]

# Verificar mapeo correcto
COLUMN_NAME_MAPPING = {
    'Operación': 'operacion',  # ✅ Correcto
    # ❌ NO duplicar: 'operacion': 'operacion'
}
```

**Verificación**:
```python
python -c "
import pandas as pd
df = pd.read_csv('N1_Tratamiento/Consolidados/Sep25/1.Consolidado_Adecuado_Sep25.csv')
print('Operacion values:', df['operacion'].value_counts())
print('Column position:', list(df.columns).index('operacion'))
"
```

---

### 🗺️ **ERROR GEOESPACIAL: Inconsistencia sin_colonia vs sin_ciudad**

**Síntomas**:
```bash
# Diferentes conteos para propiedades problemáticas
Sin colonia: 998 propiedades
Sin ciudad: 904 propiedades  # ❌ Inconsistente
```

**Causa**: Falta de coherencia geoespacial en asignación

**Solución**:
```python
# En step2_procesamiento_geoespacial.py - Agregar coherencia
def aplicar_coherencia_geoespacial(df):
    """Asegurar coherencia: sin colonia → sin ciudad"""
    sin_colonia_mask = df['colonia'] == 'Desconocido'
    
    # Forzar coherencia
    df.loc[sin_colonia_mask, 'Ciudad'] = 'Desconocido'
    
    # Validar resultado
    sin_colonia_count = sin_colonia_mask.sum()
    sin_ciudad_count = (df['Ciudad'] == 'Desconocido').sum()
    
    assert sin_colonia_count == sin_ciudad_count, f"Inconsistencia: {sin_colonia_count} != {sin_ciudad_count}"
    
    return df
```

---

### 💰 **ERROR PRECIOS: USD No Convertidos**

**Síntomas**:
```bash
# Precios USD sin convertir aparecen como valores bajos
precio: 1650.0  # Debería ser 33,000 (1650 * 20)
```

**Causa**: Función `_extract_precio` no detectando formato USD

**Solución**:
```python
def _extract_precio(precio_str):
    """Mejorada detección de USD"""
    if pd.isna(precio_str):
        return None
        
    precio_str = str(precio_str).strip()
    
    # Detectar USD en múltiples formatos
    is_usd = any(indicator in precio_str.upper() for indicator in [
        'USD', 'DOLLAR', '$USD', 'DOLARES', 'DOLAR'
    ])
    
    # Extraer número
    numeros = re.findall(r'[\d,]+\.?\d*', precio_str.replace(',', ''))
    if not numeros:
        return None
        
    precio_numerico = float(numeros[0])
    
    # Conversión USD → MN
    if is_usd and precio_numerico < 100000:  # Filtro adicional
        return precio_numerico * 20
    
    return precio_numerico
```

---

### 📊 **ERROR CONSISTENCIA: Final_Num ≠ Final_AME ≠ Final_MKT**

**Síntomas**:
```bash
Final_Num_Sep25.csv: 24,853 rows
Final_AME_Sep25.csv: 24,800 rows  # ❌ Diferente
Final_MKT_Sep25.csv: 24,790 rows  # ❌ Diferente
```

**Causa**: Uso de INNER JOIN en lugar de LEFT JOIN

**Solución**:
```python
# En step6_remover_duplicados.py - Usar LEFT JOIN
def mantener_consistencia_archivos(ids_finales, df_ame, df_mkt):
    """Asegurar misma cantidad de registros en todos los archivos"""
    
    # LEFT JOIN para preservar todos los IDs finales
    final_ame = pd.merge(ids_finales, df_ame, on='id', how='left')
    final_mkt = pd.merge(ids_finales, df_mkt, on='id', how='left')
    
    # Verificación de consistencia
    n_num = len(ids_finales)
    n_ame = len(final_ame)
    n_mkt = len(final_mkt)
    
    assert n_num == n_ame == n_mkt, f"Inconsistencia: {n_num} ≠ {n_ame} ≠ {n_mkt}"
    
    return final_ame, final_mkt
```

---

## ⚠️ Errores de Instalación

### 🔧 **ERROR: Microsoft Visual C++ Required (Windows)**

**Síntomas**:
```bash
error: Microsoft Visual C++ 14.0 is required
```

**Soluciones**:

1. **Opción A - Visual Studio Build Tools**:
```bash
# Descargar e instalar:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

2. **Opción B - Conda (Recomendado)**:
```bash
conda create -n esdata python=3.10
conda activate esdata
conda install geopandas pandas numpy scipy scikit-learn -c conda-forge
pip install -r requirements.txt
```

3. **Opción C - Binarios precompilados**:
```bash
pip install --only-binary=all geopandas shapely fiona
```

---

### 🗺️ **ERROR: GDAL/GEOS Not Found**

**Síntomas**:
```bash
ImportError: Could not find the GDAL/OGR C library
```

**Soluciones por Sistema Operativo**:

#### **Windows**:
```bash
# Opción 1: Conda (Más fácil)
conda install gdal geos -c conda-forge

# Opción 2: OSGeo4W
# Descargar desde: https://trac.osgeo.org/osgeo4w/

# Opción 3: Binarios precompilados
pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ GDAL
```

#### **macOS**:
```bash
# Con Homebrew
brew install gdal geos proj

# Variables de entorno
export GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib
export GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.dylib
```

#### **Linux (Ubuntu/Debian)**:
```bash
# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev libgeos-dev libproj-dev

# Instalar paquetes Python
pip install GDAL==$(gdal-config --version) geopandas
```

---

### 🐍 **ERROR: Python Version Compatibility**

**Síntomas**:
```bash
ERROR: No matching distribution found for package==version
```

**Diagnóstico**:
```python
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
```

**Soluciones**:

1. **Python 3.12 (Muy nuevo)**:
```bash
# Usar Python 3.10 o 3.11 (más compatible)
pyenv install 3.10.12
pyenv local 3.10.12
```

2. **Python < 3.9 (Muy viejo)**:
```bash
# Actualizar Python
python --version  # Verificar versión actual
# Instalar Python 3.10+ desde python.org
```

---

## 📁 Errores de Archivos y Directorios

### 🗂️ **ERROR: Directory Structure Missing**

**Síntomas**:
```bash
FileNotFoundError: [Errno 2] No such file or directory: 'Base_de_Datos/Sep25/'
```

**Diagnóstico**:
```python
from esdata.utils.paths import verificar_estructura
verificar_estructura()
```

**Solución**:
```python
from esdata.utils.paths import crear_estructura_directorios
crear_estructura_directorios()
```

---

### 📄 **ERROR: CSV Reading Issues**

**Síntomas**:
```bash
UnicodeDecodeError: 'utf-8' codec can't decode byte
ParserError: Error tokenizing data
```

**Soluciones**:

1. **Encoding Issues**:
```python
# Detectar encoding
import chardet
with open('archivo.csv', 'rb') as f:
    result = chardet.detect(f.read())
    print(f"Encoding detectado: {result['encoding']}")

# Leer con encoding correcto
df = pd.read_csv('archivo.csv', encoding='latin-1')
```

2. **Delimiters Incorrectos**:
```python
# Detectar delimitador
df = pd.read_csv('archivo.csv', sep=None, engine='python', nrows=5)

# Usar delimitador específico
df = pd.read_csv('archivo.csv', delimiter=';')
```

3. **Archivos Corruptos**:
```python
# Leer línea por línea para identificar problemas
with open('archivo.csv', 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f):
        try:
            # Procesar línea
            pass
        except Exception as e:
            print(f"Error en línea {i}: {e}")
```

---

### 🗺️ **ERROR: GeoJSON Loading Failed**

**Síntomas**:
```bash
fiona.errors.DriverError: unsupported driver: 'GeoJSON'
```

**Soluciones**:

1. **Verificar archivos GeoJSON**:
```python
import geopandas as gpd
import os

geojson_dir = "N1_Tratamiento/Geolocalizacion/GEOJSON"
for file in os.listdir(geojson_dir):
    if file.endswith('.geojson'):
        try:
            gdf = gpd.read_file(os.path.join(geojson_dir, file))
            print(f"✅ {file}: {len(gdf)} polígonos")
        except Exception as e:
            print(f"❌ {file}: {e}")
```

2. **Reparar GeoJSON corrupto**:
```python
import json

def reparar_geojson(archivo):
    try:
        with open(archivo, 'r') as f:
            data = json.load(f)
        
        # Verificar estructura básica
        assert 'type' in data
        assert 'features' in data
        
        print(f"✅ {archivo} válido")
        return True
    except Exception as e:
        print(f"❌ {archivo} corrupto: {e}")
        return False
```

---

## 🔍 Errores de Procesamiento

### 📊 **ERROR: Memory Issues with Large Datasets**

**Síntomas**:
```bash
MemoryError: Unable to allocate array
pandas.errors.OutOfMemoryError
```

**Soluciones**:

1. **Chunk Processing**:
```python
def procesar_en_chunks(archivo, chunk_size=5000):
    chunks = []
    for chunk in pd.read_csv(archivo, chunksize=chunk_size):
        # Procesar chunk
        chunk_procesado = procesar_chunk(chunk)
        chunks.append(chunk_procesado)
    
    return pd.concat(chunks, ignore_index=True)
```

2. **Optimización de Tipos**:
```python
def optimizar_tipos(df):
    """Reducir uso de memoria optimizando tipos de datos"""
    for col in df.columns:
        if df[col].dtype == 'int64':
            if df[col].min() > -2147483648 and df[col].max() < 2147483647:
                df[col] = df[col].astype('int32')
        elif df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
    
    return df
```

3. **Liberar memoria**:
```python
import gc

def limpiar_memoria():
    """Forzar garbage collection"""
    gc.collect()
    
# Usar después de operaciones pesadas
limpiar_memoria()
```

---

### 🔢 **ERROR: NaN Values in Critical Columns**

**Síntomas**:
```bash
# Muchos valores NaN en columnas críticas
precio: 1250 non-null, 500 null
area_m2: 1100 non-null, 650 null
```

**Diagnóstico**:
```python
def diagnosticar_nans(df):
    """Analizar valores NaN por columna"""
    nan_summary = df.isnull().sum().sort_values(ascending=False)
    nan_percentage = (nan_summary / len(df) * 100).round(2)
    
    diagnosis = pd.DataFrame({
        'Missing_Count': nan_summary,
        'Missing_Percentage': nan_percentage
    })
    
    return diagnosis[diagnosis['Missing_Count'] > 0]
```

**Soluciones**:

1. **Mejorar extracción de precios**:
```python
def extract_precio_robusto(precio_str):
    """Extracción más robusta de precios"""
    if pd.isna(precio_str):
        return None
    
    # Múltiples patrones de búsqueda
    patterns = [
        r'[\d,]+\.?\d*',  # Números con comas
        r'\$\s*[\d,]+',   # Con símbolo de peso
        r'precio[:\s]+[\d,]+',  # Con palabra precio
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, str(precio_str))
        if matches:
            return float(matches[0].replace(',', '').replace('$', ''))
    
    return None
```

2. **Imputación inteligente**:
```python
def imputar_valores_inteligente(df):
    """Imputación basada en características similares"""
    
    # Imputar área basada en tipo y recámaras
    for tipo in df['tipo_propiedad'].unique():
        mask = (df['tipo_propiedad'] == tipo) & df['area_m2'].isna()
        if mask.sum() > 0:
            area_promedio = df[df['tipo_propiedad'] == tipo]['area_m2'].median()
            df.loc[mask, 'area_m2'] = area_promedio
    
    return df
```

---

## 🛠️ Herramientas de Diagnóstico

### 🔍 **Script de Diagnóstico General**

```python
#!/usr/bin/env python3
"""
Script de diagnóstico completo para ESDATA_Epsilon
Ejecutar: python diagnostic.py
"""

import pandas as pd
import geopandas as gpd
import os
import sys
from pathlib import Path

def diagnostico_completo():
    """Ejecuta diagnóstico completo del sistema"""
    
    print("🔍 DIAGNÓSTICO ESDATA_EPSILON")
    print("=" * 50)
    
    # 1. Verificar Python y dependencias
    print(f"🐍 Python: {sys.version}")
    
    dependencias = [
        'pandas', 'numpy', 'geopandas', 'shapely', 
        'scipy', 'sklearn', 'matplotlib', 'seaborn'
    ]
    
    for dep in dependencias:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep}: {version}")
        except ImportError:
            print(f"❌ {dep}: NO INSTALADO")
    
    # 2. Verificar estructura de directorios
    print("\n📁 ESTRUCTURA DE DIRECTORIOS:")
    required_dirs = [
        "Base_de_Datos", "N1_Tratamiento", "N2_Estadisticas",
        "N5_Resultados", "Datos_Filtrados"
    ]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - FALTANTE")
    
    # 3. Verificar archivos GeoJSON
    print("\n🗺️ ARCHIVOS GEOJSON:")
    geojson_path = "N1_Tratamiento/Geolocalizacion/GEOJSON"
    if os.path.exists(geojson_path):
        for file in os.listdir(geojson_path):
            if file.endswith('.geojson'):
                try:
                    gdf = gpd.read_file(f"{geojson_path}/{file}")
                    print(f"✅ {file}: {len(gdf)} polígonos")
                except Exception as e:
                    print(f"❌ {file}: ERROR - {e}")
    else:
        print(f"❌ Directorio {geojson_path} no existe")
    
    # 4. Verificar archivos de datos más recientes
    print("\n📊 ARCHIVOS DE DATOS:")
    data_patterns = [
        ("N1_Tratamiento/Consolidados/*/1.Consolidado_Adecuado_*.csv", "Consolidado"),
        ("N1_Tratamiento/Consolidados/*/Final_Num_*.csv", "Final_Num"),
        ("N5_Resultados/Nivel_1/CSV/Final_Puntos_*.csv", "Final_Puntos")
    ]
    
    for pattern, name in data_patterns:
        files = list(Path(".").glob(pattern))
        if files:
            latest = max(files, key=os.path.getmtime)
            size_mb = os.path.getsize(latest) / 1024 / 1024
            print(f"✅ {name}: {latest} ({size_mb:.1f} MB)")
        else:
            print(f"❌ {name}: No encontrado")
    
    print("\n🎯 DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    diagnostico_completo()
```

### 🔧 **Script de Reparación Automática**

```python
#!/usr/bin/env python3
"""
Script de reparación automática para problemas comunes
Ejecutar: python fix_common_issues.py
"""

import os
import pandas as pd
from pathlib import Path

def crear_directorios_faltantes():
    """Crear estructura de directorios requerida"""
    dirs = [
        "Base_de_Datos", "N1_Tratamiento/Consolidados",
        "N2_Estadisticas/Estudios", "N2_Estadisticas/Reportes",
        "N5_Resultados/Nivel_1/CSV", "Datos_Filtrados/Duplicados",
        "Datos_Filtrados/Eliminados", "Datos_Filtrados/Esperando",
        "N1_Tratamiento/Geolocalizacion/GEOJSON"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado/verificado: {dir_path}")

def reparar_archivos_corruptos():
    """Intentar reparar archivos CSV corruptos"""
    import chardet
    
    csv_files = list(Path(".").glob("**/*.csv"))
    
    for csv_file in csv_files:
        try:
            # Intentar leer normalmente
            pd.read_csv(csv_file, nrows=5)
            print(f"✅ {csv_file}: OK")
        except Exception as e:
            print(f"⚠️ {csv_file}: Intentando reparar... {e}")
            
            # Detectar encoding
            with open(csv_file, 'rb') as f:
                encoding = chardet.detect(f.read())['encoding']
            
            try:
                # Intentar con encoding detectado
                df = pd.read_csv(csv_file, encoding=encoding, errors='replace')
                
                # Guardar corregido
                backup_file = str(csv_file) + '.backup'
                os.rename(csv_file, backup_file)
                df.to_csv(csv_file, index=False, encoding='utf-8')
                
                print(f"🔧 {csv_file}: Reparado (backup: {backup_file})")
            except Exception as e2:
                print(f"❌ {csv_file}: No se pudo reparar - {e2}")

def reparacion_completa():
    """Ejecutar todas las reparaciones"""
    print("🔧 INICIANDO REPARACIÓN AUTOMÁTICA")
    print("=" * 40)
    
    crear_directorios_faltantes()
    print()
    reparar_archivos_corruptos()
    
    print("\n✅ REPARACIÓN COMPLETADA")

if __name__ == "__main__":
    reparacion_completa()
```

---

## 📞 Soporte y Contacto

### 🆘 **Cuando Contactar Soporte**

1. **Errores no cubiertos en esta guía**
2. **Problemas de rendimiento persistentes**
3. **Bugs en funcionalidades core**
4. **Solicitudes de nuevas características**

### 📋 **Información a Incluir en Reportes de Bug**

```python
# Template de reporte de bug
print("🐛 REPORTE DE BUG ESDATA_EPSILON")
print("=" * 40)
print(f"Python version: {sys.version}")
print(f"OS: {os.name} {os.uname() if hasattr(os, 'uname') else 'Windows'}")
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Paso del pipeline: [ESPECIFICAR]")
print(f"Comando ejecutado: [ESPECIFICAR]")
print(f"Error completo:")
print("[PEGAR TRACEBACK COMPLETO]")
print(f"Archivos de entrada: [LISTAR ARCHIVOS Y TAMAÑOS]")
print(f"Configuración modificada: [SÍ/NO - DETALLAR]")
```

### 🔗 **Recursos Adicionales**

- **Documentación**: `/docs/` directory
- **Configuración**: `/docs/CONFIGURACION.md`
- **Flujo de trabajo**: `FLUJO.md`
- **Issues conocidos**: GitHub Issues
- **Actualizaciones**: Changelog en README.md

---

**🛠️ Troubleshooting ESDATA_Epsilon** - *Septiembre 2025* ✨

*Esta guía se actualiza regularmente. Para problemas no cubiertos, consultar documentación adicional o contactar soporte técnico.*
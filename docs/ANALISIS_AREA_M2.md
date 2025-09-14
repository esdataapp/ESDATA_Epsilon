# Análisis Exhaustivo de `area_m2`

Este documento detalla la lógica y uso del nuevo módulo de **Análisis Area** dentro del dashboard.

## Objetivos
1. Entender cómo se distribuye el tamaño (m²) a distintos niveles (global, colonia, estratos).
2. Identificar variables que covarían con `area_m2` (correlaciones globales y por colonia).
3. Medir impacto de amenidades sobre la superficie (medianas condicionadas).
4. Proveer insumos exportables para estudios posteriores (modelos, pricing avanzado, segmentaciones).

## Componentes del Módulo
| Componente | Función Backend | Descripción | Exportable |
|------------|-----------------|-------------|------------|
| Correlaciones Globales | `area_correlations` | Pearson (area_m2 vs otras numéricas) | No (se puede añadir) |
| Estratificación | `area_stratification` | Binning configurable (default 0→50→70→...→10000) | No directo |
| Correlaciones por Colonia | `colony_area_correlations` | Pearson por colonia con filtro `min_n` | Sí (CSV) |
| Efecto Amenidades | `amenity_area_effect` | Diferencia mediana area (present vs absent) | Sí (CSV) |
| Histogramas Área | (Plotly en vista) | Distribución y densidad básica | No |

## Detalles de Implementación
### 1. Estratificación
```python
bins = [0,50,70,90,120,160,220,300,450,600,1000,2000,10_000]
```
- Ajustar en `analytics_backend.area_stratification`.
- Columna generada: `estrato_area_m2` (Interval -> convertido a string en la vista para Plotly).

### 2. Correlaciones Globales
- Selección de columnas numéricas excluyendo (`latitud`, `longitud`).
- Método: `df[numeric].corr()["area_m2"]` (Pearson). Fácil extender a Spearman.

### 3. Correlaciones por Colonia
- Requiere `area_m2` y columna `Colonia`.
- Filtro configurable de `n` mín. (default 15, slider en UI). Se calcula sólo si ambos (`area_m2` y variable candidata) tienen `>= min_n` registros no nulos.
- Exportación: `area_correlaciones_colonia_<Periodo>.csv`.

### 4. Efecto de Amenidades
- Cruza `amenities_full` (0.Final_Ame) con `final_num` por `id`.
- Amenidad considerada si: columna numérica binaria y al menos 10 casos en present y absent.
- Métrica: `diff_mediana = mediana_present - mediana_absent` (orden desc). Top configurable (`top_n`).

### 5. Performance
- Sampling a 50k filas cuando el dataset supera ese umbral (`base_area.sample(50_000, random_state=42)`).
- Se puede promover a caché usando `@st.cache_data` si las combinaciones de filtros se estabilizan.

## Posibles Extensiones
1. Spearman / Kendall para robustez en colas.
2. Significancia estadística (Mann–Whitney U) para `amenity_area_effect` → añadir columnas `p_value` y `significativo` (alpha configurable).
3. Heatmap colonia × estrato (conteos, mediana PxM2) para detectar mix de inventario.
4. Segmentador dinámico de bins (slider + cuantiles automáticos / Freedman–Diaconis).
5. Modelos explicativos simples (Regresión lineal area_m2 ~ amenidades clave / recámaras / estacionamientos).

## Buenas Prácticas / Notas
- Evitar interpretar causalidad directa en diferencias de mediana de amenidades (correlación ≠ causalidad).
- Controlar outliers previos: Si hay distorsión severa, considerar winsorizar antes de correlaciones.
- Validar que `area_m2` > 0 para todos los registros usados.

## Hooks para Desarrolladores
- Ajustar lista de bins: editar variable `bins` en `area_stratification`.
- Cambiar umbral de sampling: variable local `large` en `app.py` (sección área).
- Añadir caching: envolver bloques largos con `@st.cache_data(show_spinner=False)`.
- Extender exportaciones: agregar botones para `correlaciones_globales` y `estratificación` si se necesitan.

---
Actualizado: Sep 2025.

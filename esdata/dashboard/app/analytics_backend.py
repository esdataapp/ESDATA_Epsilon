"""Backend analítico para Dashboard Inmobiliario (versión inicial)

Funciones actuales:
- load_base(periodo): carga datasets finales y derivados (colony_stats, quantiles, outliers).
- apply_filters(...): filtra por ciudad, operacion, tipo_propiedad, rango precio, rango area.
- descriptive_table(df): tabla resumen rápida.
- correlation_matrix(df): matriz de correlaciones numéricas.
- compute_outlier_rate(df): % outliers por colonia.
- variable_importance(df): RandomForestRegressor (PxM2 ~ features num).
- kmeans_colonies(df, k): clustering por centroides de coordenadas y mediana PxM2.
- prepare_property_level(df): normaliza dataset propiedad (crea PxM2 si falta, coerciona numéricos básicos).
- flag_outliers_iqr(df, variable, group_col): marca outliers por IQR intra-grupo.

Pendiente:
- Integrar análisis de texto y amenidades diferenciación.
- Sistema de recomendaciones.
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
from esdata.utils.io import read_csv
from esdata.utils.paths import path_base

BASE_DASH_DIR = lambda periodo: path_base('Dashboard','CSV', periodo)

def load_base(periodo: str):
    base_dir = BASE_DASH_DIR(periodo)
    # Localización robusta del archivo 0.Final_Num
    # path_base('N5_Resultados','Nivel_1','CSV') debería existir si pipeline corrió.
    try:
        n5_dir = path_base('N5_Resultados','Nivel_1','CSV')
    except Exception:
        n5_dir = os.path.join(os.path.dirname(base_dir), 'N5_Resultados','Nivel_1','CSV')
    final_num_name = f'0.Final_Num_{periodo}.csv'
    final_num_path = os.path.join(n5_dir, final_num_name)
    final_num = read_csv(final_num_path) if os.path.exists(final_num_path) else pd.DataFrame()
    # Cargar archivo de amenidades completo (para análisis detalle variable area_m2)
    ame_full_path = os.path.join(n5_dir, f'0.Final_Ame_{periodo}.csv')
    ame_full = read_csv(ame_full_path) if os.path.exists(ame_full_path) else pd.DataFrame()

    colony_stats = read_csv(os.path.join(base_dir,'colony_stats.csv'))
    quantiles = read_csv(os.path.join(base_dir,'colony_quantiles.csv'))
    outliers = read_csv(os.path.join(base_dir,'outliers_flagged.csv'))
    heat_long = read_csv(os.path.join(base_dir,'price_area_heatmap_long.csv'))
    # Archivos adicionales si existen
    distribution_long_path = os.path.join(base_dir,'colony_distribution_long.csv')
    heat_matrix_path = os.path.join(base_dir,'price_area_heatmap_matrix.csv')
    marketing_signals_path = os.path.join(base_dir,'marketing_signals.csv')
    evolution_stub_path = os.path.join(base_dir,'pxm2_evolution_stub.csv')
    distribution_long = read_csv(distribution_long_path) if os.path.exists(distribution_long_path) else pd.DataFrame()
    heat_matrix = read_csv(heat_matrix_path) if os.path.exists(heat_matrix_path) else pd.DataFrame()
    marketing_signals = read_csv(marketing_signals_path) if os.path.exists(marketing_signals_path) else pd.DataFrame()
    evolution_stub = read_csv(evolution_stub_path) if os.path.exists(evolution_stub_path) else pd.DataFrame()
    # Amenity prevalence (puede no existir en versiones anteriores)
    amenity_prev_path = os.path.join(base_dir,'amenity_prevalence.csv')
    persisted_fallback = False
    if os.path.exists(amenity_prev_path):
        amenity_prev = read_csv(amenity_prev_path)
    else:
        amenity_prev = pd.DataFrame()
        try:
            n5_dir = path_base('N5_Resultados','Nivel_1','CSV')
            ame_file = os.path.join(n5_dir, f'0.Final_Ame_{periodo}.csv')
            if os.path.exists(ame_file) and not final_num.empty:
                ame_df = read_csv(ame_file)
                meta = ['id','Ciudad','Colonia','operacion','tipo_propiedad']
                ids_final = set(final_num['id']) if 'id' in final_num.columns else set()
                if ids_final:
                    amen_cols = [c for c in ame_df.columns if c not in meta and c not in ('PaginaWeb','Fecha_Scrap','area_m2','precio','mantenimiento')]
                    sub = ame_df[ame_df['id'].isin(ids_final)].copy()
                    rows=[]
                    for col in amen_cols:
                        present = sub[col].fillna(0)
                        ratio = (present>0).mean()
                        rows.append({'amenidad':col,'n_propiedades':len(sub),'ratio_presencia':ratio,'conteo_presencia':int((present>0).sum())})
                    amenity_prev = pd.DataFrame(rows)
                    persisted_fallback = True
        except Exception:
            pass
    # Guardar fallback si se construyó
    if persisted_fallback and not amenity_prev.empty:
        try:
            amenity_prev.to_csv(amenity_prev_path, index=False)
        except Exception:
            pass
    return {
        'colony_stats': colony_stats,
        'quantiles': quantiles,
        'outliers': outliers,
        'heat_long': heat_long,
        'heat_matrix': heat_matrix,
        'distribution_long': distribution_long,
        'marketing_signals': marketing_signals,
        'evolution_stub': evolution_stub,
        'final_num': final_num,
        'amenity_prev': amenity_prev,
        'amenities_full': ame_full
    }

def apply_filters(df: pd.DataFrame, ciudad=None, operacion=None, tipo=None, precio_rango=None, area_rango=None):
    sub = df.copy()
    if ciudad and 'Ciudad' in sub.columns:
        sub = sub[sub['Ciudad'].isin(ciudad if isinstance(ciudad,list) else [ciudad])]
    if operacion and 'operacion' in sub.columns:
        sub = sub[sub['operacion'].isin(operacion if isinstance(operacion,list) else [operacion])]
    if tipo and 'tipo_propiedad' in sub.columns:
        sub = sub[sub['tipo_propiedad'].isin(tipo if isinstance(tipo,list) else [tipo])]
    if precio_rango and {'precio_min','precio_max'} & set(sub.columns):
        if 'precio_mediana' in sub.columns:
            sub = sub[(sub['precio_mediana']>=precio_rango[0]) & (sub['precio_mediana']<=precio_rango[1])]
    if area_rango and {'area_m2_min','area_m2_max'} & set(sub.columns):
        if 'area_m2_mediana' in sub.columns:
            sub = sub[(sub['area_m2_mediana']>=area_rango[0]) & (sub['area_m2_mediana']<=area_rango[1])]
    return sub

def descriptive_table(df: pd.DataFrame):
    cols = [c for c in df.columns if any(x in c for x in ['precio_','area_m2_','PxM2_'])]
    meta = [c for c in ['Ciudad','Colonia','operacion','tipo_propiedad','n_propiedades'] if c in df.columns]
    return df[meta + cols]

def correlation_matrix(df: pd.DataFrame):
    num_cols = [c for c in df.columns if df[c].dtype!=object and c not in ['longitud','latitud']]
    if not num_cols:
        return pd.DataFrame()
    return df[num_cols].corr(method='pearson')

def compute_outlier_rate(outliers_df: pd.DataFrame):
    if outliers_df.empty:
        return pd.DataFrame()
    pivot = outliers_df.groupby(['Ciudad','Colonia','variable']).size().reset_index(name='outliers') if 'Ciudad' in outliers_df.columns else outliers_df.groupby(['Colonia','variable']).size().reset_index(name='outliers')
    # Nota: necesitaríamos n por colonia (lo trae colony_stats)
    return pivot

def variable_importance(num_df: pd.DataFrame, target='PxM2'):
    if target not in num_df.columns:
        return pd.DataFrame()
    feature_candidates = [c for c in ['area_m2','recamaras','estacionamientos','banos_totales','antiguedad_icon'] if c in num_df.columns]
    if len(feature_candidates)<2:
        return pd.DataFrame()
    data = num_df[feature_candidates+[target]].dropna()
    if len(data)<50:
        return pd.DataFrame()
    X = data[feature_candidates]
    y = data[target]
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('model', RandomForestRegressor(n_estimators=150, random_state=42))
    ])
    pipe.fit(X,y)
    importances = pipe.named_steps['model'].feature_importances_
    return pd.DataFrame({'variable': feature_candidates, 'importancia': importances}).sort_values('importancia', ascending=False)

def kmeans_colonies(df: pd.DataFrame, k=5):
    needed = ['longitud','latitud','PxM2_mediana']
    if not all(c in df.columns for c in needed):
        return pd.DataFrame()
    sub = df.dropna(subset=needed).copy()
    if len(sub)<k:
        return pd.DataFrame()
    X = sub[['longitud','latitud','PxM2_mediana']]
    km = KMeans(n_clusters=k, random_state=42, n_init='auto')
    sub['cluster']= km.fit_predict(X)
    summary = sub.groupby('cluster').agg(
        n=('cluster','count'),
        PxM2_mediana=('PxM2_mediana','median'),
        lon_med=('longitud','median'),
        lat_med=('latitud','median')
    ).reset_index()
    return sub, summary

# ---------------------------
# Amenidades
# ---------------------------
def amenity_differentiation(amenity_prev: pd.DataFrame, top_n: int=30):
    """Calcula una métrica de diferenciación por colonia: lift = ratio_colonia / ratio_global.

    Espera formato long: ['Colonia','amenidad','ratio_presencia','conteo_presencia','n_propiedades']
    (si el archivo original no trae n_propiedades por amenidad, intentamos inferirlo; en generate_dashboard_data se guarda).
    Devuelve tablas:
        - heat (pivot: amenidad x Colonia con lift)
        - ranking (amenidad, Colonia, lift, ratio_colonia, ratio_global)
    """
    if amenity_prev is None or amenity_prev.empty:
        return pd.DataFrame(), pd.DataFrame()
    req = {'Colonia','amenidad','ratio_presencia'}
    if not req <= set(amenity_prev.columns):
        return pd.DataFrame(), pd.DataFrame()
    df = amenity_prev.copy()
    # Ratio global por amenidad
    global_ratio = df.groupby('amenidad')['ratio_presencia'].mean().rename('ratio_global')
    df = df.merge(global_ratio, on='amenidad', how='left')
    df['lift'] = np.where(df['ratio_global']>0, df['ratio_presencia']/df['ratio_global'], np.nan)
    # Limitar a top_n amenidades más frecuentes globalmente (ratio_global)
    top_amen = global_ratio.sort_values(ascending=False).head(top_n).index
    df_top = df[df['amenidad'].isin(top_amen)].copy()
    heat = df_top.pivot_table(index='amenidad', columns='Colonia', values='lift')
    # Ranking de diferenciación (ordenar por lift desc)
    ranking = df_top[['amenidad','Colonia','lift','ratio_presencia','ratio_global']].dropna().sort_values('lift', ascending=False)
    return heat, ranking

# ---------------------------
# Confianza de colonia
# ---------------------------
def compute_colony_confidence(final_num: pd.DataFrame, outliers: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas de confianza enriquecidas por Colonia.

    Dimensiones consideradas:
      - Volumen (n propiedades únicas)
      - Porcentaje de outliers (si dataset de outliers disponible)
      - Dispersión de PxM2 (IQR / mediana) y coeficiente de variación (std / media)

    Proceso:
      1. Asegura columna PxM2 (si falta y hay precio & area_m2, la crea al vuelo)
      2. Para cada colonia calcula: n, outliers, pct_outliers, mediana, p25, p75, media, std
      3. Deriva iqr_ratio = (p75 - p25)/mediana y cv = std / media
      4. Asigna un puntaje (0-100) sumando componentes y mapea a niveles de confianza.

    Retorna DataFrame con columnas claves (confianza_colonia, pct_outliers_colonia, confianza_score, métricas de dispersión).
    """
    if final_num is None or final_num.empty or 'Colonia' not in final_num.columns:
        return pd.DataFrame()

    work = final_num.copy()
    # Asegurar PxM2 para métricas homogéneas
    if 'PxM2' not in work.columns and {'precio','area_m2'} <= set(work.columns):
        with np.errstate(divide='ignore', invalid='ignore'):
            work['PxM2'] = np.where(work['area_m2']>0, work['precio']/work['area_m2'], np.nan)

    target_col = 'PxM2' if 'PxM2' in work.columns else ('precio' if 'precio' in work.columns else None)
    if target_col is None:
        return pd.DataFrame()

    # Outliers por colonia (conteo de ids únicos en dataset outliers)
    out_rate = None
    if outliers is not None and not outliers.empty and 'id' in outliers.columns and 'id' in work.columns:
        id_to_col = work[['id','Colonia']].dropna()
        out_sub = outliers.merge(id_to_col, on='id', how='left')
        out_rate = out_sub.groupby('Colonia')['id'].nunique().rename('outliers')

    rows = []
    for col, sub in work.groupby('Colonia', dropna=False):
        # Filtrar valores numéricos válidos del target
        vals = pd.to_numeric(sub[target_col], errors='coerce').dropna()
        n = sub['id'].nunique() if 'id' in sub.columns else len(sub)
        if n == 0:
            continue
        out_n = 0
        if out_rate is not None and col in out_rate.index:
            out_n = int(out_rate.loc[col])
        pct_out = (out_n / n * 100) if n > 0 else 0.0

        if len(vals) < 5:
            # Datos insuficientes para estadísticas robustas
            med = p25 = p75 = mean_v = std_v = np.nan
        else:
            med = vals.median()
            p25 = vals.quantile(0.25)
            p75 = vals.quantile(0.75)
            mean_v = vals.mean()
            std_v = vals.std(ddof=1)
        iqr = (p75 - p25) if pd.notna(p75) and pd.notna(p25) else np.nan
        iqr_ratio = (iqr / med) if (pd.notna(iqr) and med and med != 0) else np.nan
        cv = (std_v / mean_v) if (pd.notna(std_v) and mean_v and mean_v != 0) else np.nan

        # Scoring
        score = 50.0
        # Volumen
        if n >= 120: score += 30
        elif n >= 80: score += 22
        elif n >= 60: score += 16
        elif n >= 40: score += 10
        elif n >= 25: score += 5
        elif n < 12: score -= 25
        elif n < 20: score -= 12
        # Outliers (penaliza alto, premia bajo)
        if pct_out < 8: score += 12
        elif pct_out < 12: score += 6
        elif pct_out > 30: score -= 18
        elif pct_out > 22: score -= 10
        # Dispersión IQR/mediana (más bajo = mejor)
        if not np.isnan(iqr_ratio):
            if iqr_ratio <= 0.35: score += 8
            elif iqr_ratio <= 0.50: score += 4
            elif iqr_ratio > 0.80: score -= 10
        # Coeficiente de variación
        if not np.isnan(cv):
            if cv <= 0.30: score += 5
            elif cv <= 0.45: score += 2
            elif cv > 0.70: score -= 8

        score = max(0, min(100, score))
        if score >= 82:
            label = 'Muy Alta'
        elif score >= 68:
            label = 'Alta'
        elif score >= 50:
            label = 'Media'
        elif score >= 35:
            label = 'Baja'
        else:
            label = 'Muy Baja'

        rows.append({
            'Colonia': col,
            'n_prop_colonia': n,
            'outliers_colonia': out_n,
            'pct_outliers_colonia': round(pct_out,2),
            f'{target_col}_mediana': med,
            f'{target_col}_p25': p25,
            f'{target_col}_p75': p75,
            f'{target_col}_media': mean_v,
            f'{target_col}_std': std_v,
            f'{target_col}_iqr_ratio': iqr_ratio,
            f'{target_col}_cv': cv,
            'confianza_score': round(score,1),
            'confianza_colonia': label
        })

    return pd.DataFrame(rows)

# ---------------------------
# Propiedad a nivel detalle
# ---------------------------
def prepare_property_level(final_num: pd.DataFrame) -> pd.DataFrame:
    """Limpieza ligera para dataset a nivel propiedad destinado a visualizaciones.

    - Asegura existencia de columnas clave: precio, area_m2, PxM2.
    - Convierte a numérico silenciosamente (coerce) y elimina filas sin precio/area.
    - Calcula PxM2 si no existe o si tiene muchos NA.
    - Devuelve copia para no mutar el original.
    """
    if final_num is None or final_num.empty:
        return pd.DataFrame()
    df = final_num.copy()
    for c in ['precio','area_m2']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # Crear PxM2 si procede
    if 'PxM2' not in df.columns or df['PxM2'].isna().mean() > 0.5:
        if {'precio','area_m2'} <= set(df.columns):
            df['PxM2'] = np.where(df['area_m2']>0, df['precio']/df['area_m2'], np.nan)
    # Drop básicos
    df = df.dropna(subset=['precio','area_m2']) if {'precio','area_m2'} <= set(df.columns) else df
    return df

def flag_outliers_iqr(df: pd.DataFrame, variable: str, group_col: str='Colonia', k: float=1.5) -> pd.DataFrame:
    """Añade columnas <variable>_outlier bool y <variable>_lim_inf/sup por grupo.

    Si group_col no existe, aplica IQR global.
    Devuelve nuevo DataFrame (no in-place).
    """
    if df.empty or variable not in df.columns:
        return df
    work = df.copy()
    if group_col in work.columns:
        bounds = []
        for g, sub in work.groupby(group_col):
            series = pd.to_numeric(sub[variable], errors='coerce').dropna()
            if series.empty:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lim_inf = q1 - k * iqr
            lim_sup = q3 + k * iqr
            bounds.append((g, lim_inf, lim_sup))
        bdf = pd.DataFrame(bounds, columns=[group_col,f'{variable}_lim_inf',f'{variable}_lim_sup'])
        work = work.merge(bdf, on=group_col, how='left')
        work[f'{variable}_outlier'] = (work[variable]<work[f'{variable}_lim_inf']) | (work[variable]>work[f'{variable}_lim_sup'])
    else:
        series = pd.to_numeric(work[variable], errors='coerce').dropna()
        if series.empty:
            work[f'{variable}_outlier']=False
            return work
        q1 = series.quantile(0.25); q3 = series.quantile(0.75); iqr = q3-q1
        lim_inf = q1 - k*iqr; lim_sup = q3 + k*iqr
        work[f'{variable}_lim_inf']=lim_inf
        work[f'{variable}_lim_sup']=lim_sup
        work[f'{variable}_outlier']=(work[variable]<lim_inf)|(work[variable]>lim_sup)
    return work

# ---------------------------
# Análisis específico area_m2
# ---------------------------
def area_stratification(df: pd.DataFrame, bins: list[int]|None=None) -> pd.DataFrame:
    if df.empty or 'area_m2' not in df.columns:
        return pd.DataFrame()
    if bins is None:
        bins = [0,50,70,90,120,160,220,300,450,600,1000,2000,10_000]
    work = df.copy()
    work['estrato_area_m2'] = pd.cut(work['area_m2'], bins=bins, include_lowest=True, right=False)
    grp_cols = [c for c in ['Ciudad','Colonia','operacion','tipo_propiedad'] if c in work.columns]
    aggs = work.groupby(grp_cols + ['estrato_area_m2'], dropna=False).agg(
        n=('id','nunique'),
        precio_mediana=('precio','median') if 'precio' in work.columns else ('area_m2','median'),
        PxM2_mediana=('PxM2','median') if 'PxM2' in work.columns else ('area_m2','median'),
        area_m2_mediana=('area_m2','median')
    ).reset_index()
    return aggs

def area_correlations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or 'area_m2' not in df.columns:
        return pd.DataFrame()
    numeric_cols = [c for c in df.columns if df[c].dtype!=object and c not in ('latitud','longitud')]
    if 'area_m2' not in numeric_cols:
        return pd.DataFrame()
    corr = df[numeric_cols].corr(method='pearson')['area_m2'].sort_values(ascending=False).to_frame(name='corr_area_m2')
    return corr.reset_index().rename(columns={'index':'variable'})

def colony_area_correlations(df: pd.DataFrame, min_n: int=15) -> pd.DataFrame:
    if df.empty or 'area_m2' not in df.columns:
        return pd.DataFrame()
    grp_col = 'Colonia' if 'Colonia' in df.columns else None
    if not grp_col:
        return pd.DataFrame()
    numeric_cols = [c for c in df.columns if df[c].dtype!=object and c not in ('latitud','longitud')]
    rows=[]
    for col, sub in df.groupby(grp_col):
        if sub['area_m2'].notna().sum() < min_n:
            continue
        for var in numeric_cols:
            if var=='area_m2' or sub[var].notna().sum()<min_n:
                continue
            try:
                r = sub[['area_m2',var]].dropna()
                if len(r) < min_n:
                    continue
                corr = r.corr(method='pearson').iloc[0,1]
                rows.append({'Colonia': col, 'variable': var, 'corr': corr, 'n': len(r)})
            except Exception:
                continue
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def amenity_area_effect(amenities_df: pd.DataFrame, num_df: pd.DataFrame, top_n: int=30) -> pd.DataFrame:
    """Evalúa diferencia de área_m2 según presencia de amenidades binarias (amenidades_df y num_df comparten id)."""
    if amenities_df.empty or num_df.empty or 'id' not in amenities_df.columns or 'id' not in num_df.columns:
        return pd.DataFrame()
    # Detectar columnas de amenidades candidatas (excluir meta y no numéricas binarias)
    meta = {'id','Ciudad','Colonia','operacion','tipo_propiedad','precio','area_m2','PxM2','PaginaWeb','Fecha_Scrap','mantenimiento'}
    amen_cols = [c for c in amenities_df.columns if c not in meta and amenities_df[c].dtype!=object]
    if not amen_cols:
        return pd.DataFrame()
    merged = amenities_df[['id']+amen_cols].merge(num_df[['id','area_m2']], on='id', how='inner')
    rows=[]
    for col in amen_cols:
        s = merged[[col,'area_m2']].dropna()
        if s.empty: continue
        present = s[s[col]>0]['area_m2']
        absent = s[s[col]==0]['area_m2']
        if len(present)<10 or len(absent)<10:
            continue
        diff = present.median()-absent.median()
        rows.append({'amenidad': col, 'n_present': len(present), 'n_absent': len(absent), 'mediana_present': present.median(), 'mediana_absent': absent.median(), 'diff_mediana': diff})
    if not rows:
        return pd.DataFrame()
    df_eff = pd.DataFrame(rows).sort_values('diff_mediana', ascending=False)
    return df_eff.head(top_n)

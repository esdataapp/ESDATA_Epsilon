"""Aplicación Streamlit - Dashboard Inmobiliario

Ejecutar (desde raíz del proyecto):
    streamlit run esdata/dashboard/app/app.py -- --periodo Sep25

Si se ejecuta estando parado dentro de esdata/dashboard/app, el código añade la raíz al sys.path automáticamente.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import argparse, sys, os

# Asegurar que la raíz del proyecto (donde vive el paquete esdata) esté en sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from esdata.dashboard.app.analytics_backend import (
        load_base, apply_filters, descriptive_table, correlation_matrix,
        variable_importance, kmeans_colonies, prepare_property_level, flag_outliers_iqr,
        amenity_differentiation, compute_colony_confidence,
        area_stratification, area_correlations, colony_area_correlations, amenity_area_effect
    )
    from esdata.dashboard.app.analytics_kpi import compute_kpis
    from esdata.dashboard.app.analytics_text import load_marketing, word_frequencies, tfidf_top_terms, build_wordcloud
except ModuleNotFoundError:
    # Fallback a import relativo si el paquete no está instalado como paquete
    from analytics_backend import (
        load_base, apply_filters, descriptive_table, correlation_matrix,
        variable_importance, kmeans_colonies, prepare_property_level, flag_outliers_iqr,
        amenity_differentiation, compute_colony_confidence,
        area_stratification, area_correlations, colony_area_correlations, amenity_area_effect
    )
    from analytics_kpi import compute_kpis
    from analytics_text import load_marketing, word_frequencies, tfidf_top_terms, build_wordcloud

# --- Argumentos ---
@st.cache_resource(show_spinner=False)
def get_args():
    # Streamlit pasa args propios, tomamos después de '--'
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--periodo', default='Sep25')
    known, _ = parser.parse_known_args(sys.argv[1:])
    return known

args = get_args()
PERIODO = args.periodo

# --- Refrescar datasets (botón) ---
with st.sidebar.expander('⚙️ Actualizar Datos'):
    import sys as _sys, subprocess as _sub
    if st.button('♻️ Reprocesar periodo actual'):
        try:
            cmd = [_sys.executable, '-m', 'esdata.dashboard.generate_dashboard_data', '--periodo', PERIODO]
            res = _sub.run(cmd, capture_output=True, text=True, timeout=900)
            if res.returncode == 0:
                st.success('Datos regenerados correctamente. Refrescando vista...')
                st.cache_data.clear(); st.cache_resource.clear()
                st.rerun()
            else:
                st.error('Error al regenerar datos.')
                st.caption(res.stderr[:800])
        except Exception as _e:
            st.error(f'Fallo al ejecutar generador: {_e}')

# -------------------------------------------------------------
# Detección de ejecución incorrecta (python app.py en lugar de streamlit run)
# Si no hay un runtime de Streamlit activo relanzamos automáticamente.
# -------------------------------------------------------------
def _in_streamlit_runtime():
    try:
        from streamlit import runtime as _rt  # type: ignore
        try:
            return _rt.exists()
        except Exception:
            return False
    except Exception:
        # Heurística secundaria basada en variables de entorno que crea streamlit
        return any(k.startswith('STREAMLIT_SERVER') for k in os.environ.keys())

if __name__ == '__main__' and not _in_streamlit_runtime():
    periodo = PERIODO
    print('\n⚠️  Ejecutaste el script directamente con Python. Relanzando con Streamlit...')
    cmd = ["streamlit", "run", __file__, "--", "--periodo", periodo]
    try:
        os.execvp('streamlit', cmd)  # Reemplaza el proceso actual
    except FileNotFoundError:
        print("No se encontró el comando 'streamlit'. Instala con: pip install streamlit")
        sys.exit(1)

st.sidebar.title('Filtros')
st.sidebar.markdown('---')
st.sidebar.subheader('Variable Análisis')
var_sel = st.sidebar.selectbox('Variable principal', ['precio','area_m2','PxM2'], index=0)
log_scale = st.sidebar.checkbox('Escala log (boxplot)', value=False)
solo_out = st.sidebar.checkbox('Mostrar solo outliers en tabla', value=False)

# Sliders precio / área (se definen después de cargar datos, placeholder aquí)

# --- Carga datos ---
@st.cache_data(show_spinner=True)
def load_data(periodo):
    return load_base(periodo)

data = load_data(PERIODO)
colony_stats = data['colony_stats']
quantiles = data['quantiles']
outliers = data['outliers']
heat_long = data['heat_long']
heat_matrix = data.get('heat_matrix', pd.DataFrame())
distribution_long = data.get('distribution_long', pd.DataFrame())
marketing_signals = data.get('marketing_signals', pd.DataFrame())
evolution_stub = data.get('evolution_stub', pd.DataFrame())
final_num_raw = data.get('final_num', pd.DataFrame())
amenity_prev = data.get('amenity_prev', pd.DataFrame())
amenities_full = data.get('amenities_full', pd.DataFrame())

@st.cache_data(show_spinner=False)
def get_property_dataset(df, variable):
    prep = prepare_property_level(df)
    if prep.empty:
        return prep
    # Aplicar flag outliers para variable seleccionada
    flagged = flag_outliers_iqr(prep, variable)
    return flagged

final_num = get_property_dataset(final_num_raw, var_sel)

# Crear sliders dinámicos basados en final_num
precio_min, precio_max = (0,0)
area_min, area_max = (0,0)
if not final_num.empty:
    if 'precio' in final_num.columns:
        serie_p = final_num['precio'].dropna()
        if not serie_p.empty:
            precio_min, precio_max = float(serie_p.min()), float(serie_p.max())
    if 'area_m2' in final_num.columns:
        serie_a = final_num['area_m2'].dropna()
        if not serie_a.empty:
            area_min, area_max = float(serie_a.min()), float(serie_a.max())
if precio_max>0 and precio_min<precio_max:
    rango_precio = st.sidebar.slider('Rango Precio', min_value=precio_min, max_value=precio_max,
                                     value=(precio_min, precio_max))
else:
    rango_precio = None
if area_max>0 and area_min<area_max:
    rango_area = st.sidebar.slider('Rango Área (m2)', min_value=area_min, max_value=area_max,
                                   value=(area_min, area_max))
else:
    rango_area = None

def _apply_property_filters(df: pd.DataFrame, sel_ciudad, sel_oper, sel_tipo) -> pd.DataFrame:
    if df.empty:
        return df
    sub = df.copy()
    if sel_ciudad and 'Ciudad' in sub.columns:
        sub = sub[sub['Ciudad'].isin(sel_ciudad)]
    if sel_oper and 'operacion' in sub.columns:
        sub = sub[sub['operacion'].isin(sel_oper)]
    if sel_tipo and 'tipo_propiedad' in sub.columns:
        sub = sub[sub['tipo_propiedad'].isin(sel_tipo)]
    if rango_precio and 'precio' in sub.columns:
        sub = sub[(sub['precio']>=rango_precio[0]) & (sub['precio']<=rango_precio[1])]
    if rango_area and 'area_m2' in sub.columns:
        sub = sub[(sub['area_m2']>=rango_area[0]) & (sub['area_m2']<=rango_area[1])]
    return sub

"""Definir filtros dinámicos antes de aplicar a dataset propiedad."""
# --- Filtros dinámicos ---
ciudades = sorted(colony_stats['Ciudad'].dropna().unique()) if 'Ciudad' in colony_stats.columns else []
operaciones = sorted(colony_stats['operacion'].dropna().unique()) if 'operacion' in colony_stats.columns else []
tipos = sorted(colony_stats['tipo_propiedad'].dropna().unique()) if 'tipo_propiedad' in colony_stats.columns else []

sel_ciudad = st.sidebar.multiselect('Ciudad', ciudades)
sel_oper = st.sidebar.multiselect('Operación', operaciones)
sel_tipo = st.sidebar.multiselect('Tipo Propiedad', tipos)

filtered_stats = colony_stats.copy()
if sel_ciudad:
    filtered_stats = filtered_stats[filtered_stats['Ciudad'].isin(sel_ciudad)]
if sel_oper:
    filtered_stats = filtered_stats[filtered_stats['operacion'].isin(sel_oper)]
if sel_tipo:
    filtered_stats = filtered_stats[filtered_stats['tipo_propiedad'].isin(sel_tipo)]

# Aplicar filtros a dataset propiedad después de conocer selecciones
final_num_filtered = _apply_property_filters(final_num, sel_ciudad, sel_oper, sel_tipo)

st.title('Dashboard Inmobiliario - Versión Inicial')
st.caption(f'Periodo: {PERIODO}')

# Panel Diagnóstico
with st.expander('🔎 Diagnóstico de Carga de Datos'):
    def _ds_info(name, df):
        return f"{name}: filas={len(df)} | columnas={len(df.columns) if not df.empty else 0}"
    st.write(_ds_info('colony_stats', colony_stats))
    st.write(_ds_info('quantiles', quantiles))
    st.write(_ds_info('outliers_flagged', outliers))
    st.write(_ds_info('price_area_heatmap_long', heat_long))
    st.write(_ds_info('price_area_heatmap_matrix', heat_matrix))
    st.write(_ds_info('colony_distribution_long', distribution_long))
    st.write(_ds_info('marketing_signals', marketing_signals))
    st.write(_ds_info('pxm2_evolution_stub', evolution_stub))
    st.write(_ds_info('final_num', final_num_raw))
    st.write(_ds_info('amenity_prevalence', amenity_prev))
    if final_num_raw.empty:
        st.warning('final_num está vacío: verifica existencia de 0.Final_Num_<Periodo>.csv en N5_Resultados/Nivel_1/CSV.')
    missing_cols = [c for c in ['precio','area_m2','PxM2'] if c not in final_num_raw.columns]
    if missing_cols:
        st.info(f"Columnas faltantes en final_num: {missing_cols}")


# KPI Band
kpis = compute_kpis(final_num_filtered, filtered_stats, outliers, PERIODO)
show_amen_cov = 'amenidades_cobertura_pct' in kpis
col_kpi = st.columns(6 if show_amen_cov else 5)
def _fmt_num(v):
    if v is None: return '—'
    if isinstance(v, (int,float)):
        if abs(v)>=1_000_000: return f'{v/1_000_000:.2f}M'
        if abs(v)>=1000: return f'{v/1000:.1f}K'
        return f'{v:,.0f}'
    return str(v)

with col_kpi[0]:
    st.metric('Propiedades', _fmt_num(kpis.get('n_propiedades')))
with col_kpi[1]:
    st.metric('Mediana Precio', _fmt_num(kpis.get('precio_mediana')))
with col_kpi[2]:
    delta = kpis.get('PxM2_mediana_delta_pct')
    med_pxm2 = kpis.get('PxM2_mediana')
    st.metric('Mediana PxM2', _fmt_num(med_pxm2), (f"{delta:+.1f}%" if isinstance(delta,(int,float)) else None))
with col_kpi[3]:
    st.metric('% Outliers', f"{kpis.get('pct_outliers',0):.1f}%")
with col_kpi[4]:
    topc = kpis.get('top_colonia_pxm2','—')
    st.metric('Top Colonia PxM2', topc)
if show_amen_cov:
    with col_kpi[5]:
        cov = kpis.get('amenidades_cobertura_pct')
        st.metric('Cobertura Amenidades', f"{cov:.1f}%" if isinstance(cov,(int,float)) else '—')

# --- Sección 1: Tabla descriptiva ---
st.header('📊 Resumen Descriptivo')
# Enriquecer tabla descriptiva con confianza
try:
    conf_df = compute_colony_confidence(final_num_filtered, outliers)
    if not conf_df.empty:
        desc = descriptive_table(filtered_stats).merge(conf_df[['Colonia','confianza_colonia','pct_outliers_colonia']], on='Colonia', how='left')
    else:
        desc = descriptive_table(filtered_stats)
except Exception:
    desc = descriptive_table(filtered_stats)

conf_filter_opts = sorted(desc['confianza_colonia'].dropna().unique()) if 'confianza_colonia' in desc.columns else []
sel_conf = st.multiselect('Filtrar por confianza de colonia', conf_filter_opts) if conf_filter_opts else []
if sel_conf and 'confianza_colonia' in desc.columns:
    desc_show = desc[desc['confianza_colonia'].isin(sel_conf)]
else:
    desc_show = desc
def _format_money(v):
    return '' if pd.isna(v) else f"$ {v:,.2f}"
def _format_area(v):
    return '' if pd.isna(v) else f"{v:,.2f}"

desc_fmt = desc_show.copy()
for col in desc_fmt.columns:
    if col.startswith('precio_') and desc_fmt[col].dtype!=object:
        desc_fmt[col] = desc_fmt[col].apply(_format_money)
    if col.startswith('area_m2_') and desc_fmt[col].dtype!=object:
        desc_fmt[col] = desc_fmt[col].apply(_format_area)

# Badges de confianza (convertir a HTML si existe la columna)
def _badge_conf(v: str):
    palette = {
        'Muy Alta': '#1b7837',
        'Alta': '#5aae61',
        'Media': '#b2abd2',
        'Baja': '#fdae61',
        'Muy Baja': '#d7191c'
    }
    if pd.isna(v):
        return ''
    color = palette.get(v, '#888')
    return f"<span style='background:{color};color:white;padding:2px 6px;border-radius:12px;font-size:11px;font-weight:600'>{v}</span>"

if 'confianza_colonia' in desc_fmt.columns:
    desc_fmt['confianza_colonia'] = desc_fmt['confianza_colonia'].apply(_badge_conf)
    st.markdown("<div style='max-height:500px;overflow-y:auto'>" +
                desc_fmt.head(300).to_html(escape=False, index=False) + "</div>", unsafe_allow_html=True)
else:
    st.dataframe(desc_fmt.head(300))

# --- Sección 2: Boxplots (placeholder) ---
st.header('🧪 Boxplots por Colonia (Propiedad)')
import plotly.express as px
if not final_num_filtered.empty and var_sel in final_num_filtered.columns:
    fn = final_num_filtered.copy()
    if sel_ciudad: fn = fn[fn['Ciudad'].isin(sel_ciudad)]
    if sel_oper: fn = fn[fn['operacion'].isin(sel_oper)]
    if sel_tipo: fn = fn[fn['tipo_propiedad'].isin(sel_tipo)]
    if len(fn) > 20000:
        st.info(f"Muestreo (20k de {len(fn)} filas) para performance")
        fn = fn.sample(20000, random_state=42)
    y_data = fn[var_sel]
    if log_scale:
        # Evitar log de valores <=0
        y_min = y_data[y_data>0]
        if y_min.empty:
            st.warning('No hay valores positivos para escala log.')
        else:
            fn = fn[y_data>0].copy()
            fn[f'log_{var_sel}'] = np.log10(fn[var_sel])
            fig = px.box(fn, x='Colonia', y=f'log_{var_sel}', points='suspectedoutliers', title=f'Log10 {var_sel} por Colonia')
            st.plotly_chart(fig, use_container_width=True)
    else:
        fig = px.box(fn, x='Colonia', y=var_sel, points='suspectedoutliers', title=f'{var_sel} por Colonia')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning('Dataset propiedad vacío o variable no disponible.')

st.subheader('Tabla de Outliers (IQR)')
if not final_num_filtered.empty and f'{var_sel}_outlier' in final_num_filtered.columns:
    fn_tab = final_num_filtered.copy()
    if sel_ciudad: fn_tab = fn_tab[fn_tab['Ciudad'].isin(sel_ciudad)]
    if sel_oper: fn_tab = fn_tab[fn_tab['operacion'].isin(sel_oper)]
    if sel_tipo: fn_tab = fn_tab[fn_tab['tipo_propiedad'].isin(sel_tipo)]
    cols_show = ['Ciudad','Colonia','operacion','tipo_propiedad', var_sel]
    lim_inf_col = f'{var_sel}_lim_inf'; lim_sup_col = f'{var_sel}_lim_sup'
    for c in [lim_inf_col, lim_sup_col]:
        if c in fn_tab.columns: cols_show.append(c)
    cols_show.append(f'{var_sel}_outlier')
    fn_tab = fn_tab[cols_show]
    if solo_out:
        fn_tab = fn_tab[fn_tab[f'{var_sel}_outlier'] == True]
    # Formatear precio / area_m2 si presentes
    if 'precio' in fn_tab.columns and fn_tab['precio'].dtype!=object:
        fn_tab['precio'] = fn_tab['precio'].apply(_format_money)
    if 'area_m2' in fn_tab.columns and fn_tab['area_m2'].dtype!=object:
        fn_tab['area_m2'] = fn_tab['area_m2'].apply(_format_area)
    st.dataframe(fn_tab.head(1000))
    csv_out = fn_tab.to_csv(index=False).encode('utf-8')
    st.download_button('Descargar outliers filtrados', data=csv_out, file_name=f'outliers_{var_sel}_{PERIODO}.csv', mime='text/csv')
else:
    st.info('Outliers no calculados para la variable seleccionada.')

# --- Sección adicional: Distribución / Histograma ---
st.header('📦 Distribución & Densidad')
if not final_num_filtered.empty and var_sel in final_num_filtered.columns:
    import plotly.express as px
    import plotly.graph_objects as go
    bins = st.slider('Bins', min_value=10, max_value=200, value=50, step=10)
    use_kde = st.checkbox('KDE (gaussian) si n > 200', value=True)
    serie = final_num_filtered[var_sel].dropna()
    if len(serie)>0:
        hist_fig = px.histogram(final_num_filtered, x=var_sel, nbins=bins, opacity=0.70)
        if use_kde and len(serie) > 200:
            try:
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(serie)
                xs = np.linspace(serie.min(), serie.max(), 256)
                ys = kde(xs)
                # Escalar densidad para que la altura sea comparable (opcional): multiplicar por área total / bins
                scale = len(serie) * (serie.max()-serie.min()) / bins
                ys_scaled = ys * scale
                hist_fig.add_trace(go.Scatter(x=xs, y=ys_scaled, mode='lines', name='KDE', line=dict(color='#d62728', width=2)))
            except Exception as e:
                st.caption(f"KDE no disponible: {e}")
        st.plotly_chart(hist_fig, use_container_width=True)
    else:
        st.info('Sin datos numéricos para histograma.')
else:
    st.info('Variable no disponible para histograma.')

# --- Sección 3: Scatter con tendencia ---
st.header('📈 Scatter Precio vs Área (Propiedad)')
if not final_num_filtered.empty and {'area_m2','precio'} <= set(final_num_filtered.columns):
    color_candidate = f'{var_sel}_outlier'
    needed_cols = ['area_m2','precio','Colonia'] + ([color_candidate] if color_candidate in final_num_filtered.columns else [])
    fn_sc = final_num_filtered[needed_cols].dropna(subset=['area_m2','precio']).copy()
    if sel_ciudad: fn_sc = fn_sc[fn_sc['Colonia'].isin(filtered_stats['Colonia'])]
    if len(fn_sc) > 30000:
        fn_sc = fn_sc.sample(30000, random_state=42)
    use_color = color_candidate if color_candidate in fn_sc.columns else None
    fig2 = px.scatter(
        fn_sc, x='area_m2', y='precio', hover_data=['Colonia'], opacity=0.5,
        color=use_color,
        title='Precio vs Área (color = outlier)' if use_color else 'Precio vs Área'
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info('Dataset insuficiente para scatter (requiere area_m2 y precio).')

# --- Sección 3b: Mapa geoespacial ---
st.header('🗺️ Mapa Geoespacial (Propiedades)')
if not final_num_filtered.empty and {'latitud','longitud'} <= set(final_num_filtered.columns):
    try:
        import pydeck as pdk
        map_df = final_num_filtered.dropna(subset=['latitud','longitud']).copy()
        if sel_ciudad and 'Ciudad' in map_df.columns:
            map_df = map_df[map_df['Ciudad'].isin(sel_ciudad)]
        if sel_oper and 'operacion' in map_df.columns:
            map_df = map_df[map_df['operacion'].isin(sel_oper)]
        if sel_tipo and 'tipo_propiedad' in map_df.columns:
            map_df = map_df[map_df['tipo_propiedad'].isin(sel_tipo)]
        if len(map_df) > 20000:
            map_df = map_df.sample(20000, random_state=42)
        color_var = 'PxM2' if 'PxM2' in map_df.columns else ('precio' if 'precio' in map_df.columns else None)
        # Normalizar color
        if color_var:
            vals = map_df[color_var].astype(float).clip(lower=0)
            vmin, vmax = vals.quantile(0.02), vals.quantile(0.98)
            rng = vmax - vmin if vmax>vmin else 1
            map_df['_color_val'] = ((vals - vmin)/rng).clip(0,1)
            map_df['_r'] = (255*map_df['_color_val']).astype(int)
            map_df['_g'] = (255*(1-map_df['_color_val'])).astype(int)
            map_df['_b'] = 120
        else:
            map_df['_r'], map_df['_g'], map_df['_b'] = 30,144,255
        # Nota: Versión simplificada; pydeck en algunas versiones maneja tooltip desde layer pickable + frontend.
        # Se omite dict tooltip para evitar incompatibilidades tipadas.
        layer = pdk.Layer(
            'ScatterplotLayer',
            data=map_df,
            get_position='[longitud, latitud]',
            get_radius=40,
            get_fill_color='[_r,_g,_b,140]',
            pickable=True,
            radius_scale=2,
        )
        view_state = pdk.ViewState(
            longitude=float(map_df['longitud'].median()),
            latitude=float(map_df['latitud'].median()),
            zoom=11
        )
        r = pdk.Deck(layers=[layer], initial_view_state=view_state)
        st.pydeck_chart(r, use_container_width=True)
    except Exception as e:
        st.caption(f"Mapa no disponible: {e}")
else:
    st.info('No hay columnas latitud/longitud para mapa.')

# --- Sección 3c: Análisis de Texto (Descripciones) ---
st.header('📝 Análisis de Texto (Descripciones)')
with st.expander('Mostrar análisis de texto'):
    mkt_df = load_marketing(PERIODO)
    if mkt_df is None or mkt_df.empty:
        st.info('No se encontró dataset de marketing 0.Final_MKT para este periodo.')
    else:
        # Intentar detectar columna de descripción
        desc_col = None
        for cand in ['descripcion','descripcion_limpia','texto','detalle']:
            if cand in mkt_df.columns:
                desc_col = cand; break
        if desc_col is None:
            st.warning('No se encontró columna de descripción estándar. (descripcion / texto)')
        else:
            # Construir un segmento por terciles de PxM2 si posible
            if 'PxM2' in final_num_filtered.columns and 'id' in final_num_filtered.columns and 'id' in mkt_df.columns:
                mkt_merge = mkt_df.merge(final_num_filtered[['id','PxM2']], on='id', how='left')
                if mkt_merge['PxM2'].notna().sum() > 50:
                    try:
                        terciles = pd.qcut(mkt_merge['PxM2'], 3, labels=['Bajo','Medio','Alto'])
                        mkt_merge['segmento'] = terciles.astype(str)
                    except Exception:
                        mkt_merge['segmento'] = 'General'
                else:
                    mkt_merge['segmento'] = 'General'
            else:
                mkt_merge = mkt_df.copy()
                mkt_merge['segmento'] = 'General'

            top_freq = word_frequencies(mkt_merge, text_col=desc_col, top_n=80)
            if top_freq.empty:
                st.info('No se pudieron calcular frecuencias de palabras.')
            else:
                # Word Cloud
                wc, png_bytes = build_wordcloud(top_freq)
                if png_bytes:
                    st.image(png_bytes, caption='Word Cloud (Top términos)')
                st.subheader('Frecuencias de Palabras')
                st.dataframe(top_freq.head(100))
                csv_tf = top_freq.to_csv(index=False).encode('utf-8')
                st.download_button('Descargar frecuencias', data=csv_tf, file_name=f'word_freq_{PERIODO}.csv', mime='text/csv')

            # TF-IDF por segmento
            seg_tfidf = tfidf_top_terms(mkt_merge, text_col=desc_col, group_col='segmento', top_k=12)
            if not seg_tfidf.empty:
                st.subheader('Términos Diferenciadores (TF-IDF) por Segmento PxM2')
                st.dataframe(seg_tfidf)
                csv_tfidf = seg_tfidf.to_csv(index=False).encode('utf-8')
                st.download_button('Descargar TF-IDF', data=csv_tfidf, file_name=f'tfidf_segmentos_{PERIODO}.csv', mime='text/csv')
            else:
                st.caption('TF-IDF no disponible (quizá pocos textos por segmento).')

# --- Sección 4: Heatmap outliers (placeholder) ---
st.header('🔥 % Outliers por Colonia (Placeholder)')
if not outliers.empty and 'Colonia' in outliers.columns:
    rate = outliers.groupby('Colonia').size().reset_index(name='outliers')
    total = filtered_stats[['Colonia','n_propiedades']]
    merged = rate.merge(total, on='Colonia', how='left')
    merged['pct_outliers'] = merged['outliers']/merged['n_propiedades']
    fig3 = px.density_heatmap(merged, x='Colonia', y='pct_outliers', z='pct_outliers', nbinsx=len(merged), nbinsy=1, color_continuous_scale='Reds')
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info('Sin outliers disponibles.')

# --- Sección 5: Correlaciones ---
st.header('🧩 Correlaciones')
cor = correlation_matrix(filtered_stats)
if not cor.empty:
    fig_cor = px.imshow(cor, text_auto=True, aspect='auto', color_continuous_scale='Viridis')
    st.plotly_chart(fig_cor, use_container_width=True)
else:
    st.info('No hay suficientes columnas numéricas para correlación.')

# --- Sección 6: Importancia de variables ---
st.header('🌲 Importancia de Variables (Random Forest)')
# Requerimos datos a nivel propiedad para mejor modelo; placeholder usando colony_stats.
imp = variable_importance(filtered_stats.rename(columns={'PxM2_mediana':'PxM2'}))
if not imp.empty:
    fig_imp = px.bar(imp, x='variable', y='importancia')
    st.plotly_chart(fig_imp, use_container_width=True)
else:
    st.info('Insuficiente data para importancia de variables.')

# --- Sección 7: Clustering espacial (placeholder) ---
st.header('🗺️ Clustering Espacial (Placeholder)')
if {'longitud','latitud','PxM2_mediana'} <= set(filtered_stats.columns):
    from analytics_backend import kmeans_colonies
    res = kmeans_colonies(filtered_stats, k=min(5, max(2, len(filtered_stats)//15)))
    if isinstance(res, tuple):
        sub, summ = res
        st.subheader('Clusters Summary')
        st.dataframe(summ)
        fig_clu = px.scatter(sub, x='longitud', y='latitud', color='cluster', size='PxM2_mediana', hover_data=['Colonia'])
        st.plotly_chart(fig_clu, use_container_width=True)
    else:
        st.info('Clustering no disponible (pocos datos).')
else:
    st.info('Faltan columnas longitud/latitud/PxM2_mediana para clustering.')

# (Se eliminó la sección de Recomendaciones Automatizadas para dar paso a análisis de amenidades.)

# --- Sección 9: Descargas de datasets ---
st.header('💾 Exportar Datasets (CSV)')
export_sets = {
    'colony_stats.csv': colony_stats,
    'colony_quantiles.csv': quantiles,
    'outliers_flagged.csv': outliers,
    'price_area_heatmap_long.csv': heat_long,
    'price_area_heatmap_matrix.csv': heat_matrix,
    'colony_distribution_long.csv': distribution_long,
    'marketing_signals.csv': marketing_signals,
    'pxm2_evolution_stub.csv': evolution_stub,
    'amenity_prevalence.csv': amenity_prev,
}
col1, col2, col3, col4 = st.columns(4)
cols = [col1,col2,col3,col4]
for (name, df_exp), c in zip(export_sets.items(), cols):
    with c:
        if df_exp is not None and not df_exp.empty:
            csv_bytes = df_exp.to_csv(index=False).encode('utf-8')
            st.download_button(label=name, data=csv_bytes, file_name=name, mime='text/csv')
        else:
            st.write(f"{name}: vacío")

# Placeholder para futura exportación PDF/Reporte
st.info('Exportación PDF vendrá en una versión posterior (placeholder).')

# --- Sección Amenidades: Prevalencia y Diferenciación ---
st.header('🏗️ Amenidades: Prevalencia y Diferenciación')
if amenity_prev is not None and not amenity_prev.empty:
    amen_view = amenity_prev.copy()
    # Aplicar filtros de contexto
    if sel_ciudad and 'Ciudad' in amen_view.columns:
        amen_view = amen_view[amen_view['Ciudad'].isin(sel_ciudad)]
    if sel_oper and 'operacion' in amen_view.columns:
        amen_view = amen_view[amen_view['operacion'].isin(sel_oper)]
    if sel_tipo and 'tipo_propiedad' in amen_view.columns:
        amen_view = amen_view[amen_view['tipo_propiedad'].isin(sel_tipo)]
    top_n = st.slider('Top amenidades (por frecuencia global)', 5, 60, 30, 5)
    heat, ranking = amenity_differentiation(amen_view, top_n=top_n)
    import plotly.express as px
    if heat is not None and not heat.empty:
        fig_h = px.imshow(heat, aspect='auto', color_continuous_scale='Tealrose', origin='lower')
        st.plotly_chart(fig_h, use_container_width=True)
        st.caption('Lift = Ratio Colonia / Ratio Global. >1 indica diferenciación hacia arriba.')
    else:
        st.info('Sin datos suficientes para heatmap de amenidades filtrado.')
    if ranking is not None and not ranking.empty:
        st.subheader('Ranking Amenidad-Colonia (Lift)')
        st.dataframe(ranking.head(300))
        csv_rank = ranking.to_csv(index=False).encode('utf-8')
        st.download_button('Descargar ranking amenidades', data=csv_rank, file_name=f'amenity_lift_{PERIODO}.csv', mime='text/csv')
    else:
        st.info('Sin ranking disponible tras filtros.')
else:
    st.info('No se encontró amenity_prevalence.csv para este período. Ejecuta: python -m esdata.dashboard.generate_dashboard_data <Periodo> para generarlo (o asegúrate que exista 0.Final_Ame_<Periodo>.csv).')

# --- Sección Especial: Análisis Exhaustivo de area_m2 ---
st.header('📐 Análisis Exhaustivo: area_m2')
with st.expander('Mostrar análisis avanzado de área (area_m2)'):
    if final_num_filtered.empty or 'area_m2' not in final_num_filtered.columns:
        st.warning('No hay datos suficientes o falta la columna area_m2.')
    else:
        # Sampling para performance
        base_area = final_num_filtered.copy()
        large = len(base_area) > 50_000
        if large:
            st.caption(f'Muestreo aplicado (50k de {len(base_area)} filas) para cálculos intensivos.')
            base_area = base_area.sample(50_000, random_state=42)

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.subheader('Correlaciones Globales (area_m2 vs otras)')
            corr_area = area_correlations(base_area)
            if not corr_area.empty:
                st.dataframe(corr_area.head(40))
            else:
                st.info('No se pudieron calcular correlaciones globales.')
        with col_a2:
            st.subheader('Estratificación de Área')
            strata = area_stratification(base_area)
            if not strata.empty:
                # Mostrar tabla con estrato casteado a texto para evitar issues Interval JSON
                if 'estrato_area_m2' in strata.columns:
                    strata_display = strata.copy()
                    strata_display['estrato_area_m2'] = strata_display['estrato_area_m2'].astype(str)
                    st.dataframe(strata_display.head(40))
                    # Distribución simple (convertir Interval a string)
                    import plotly.express as px
                    freq = strata_display.groupby('estrato_area_m2')['n'].sum().reset_index()
                    fig_strata = px.bar(freq, x='estrato_area_m2', y='n', title='Distribución por Estratos de Área')
                    st.plotly_chart(fig_strata, use_container_width=True)
                else:
                    st.dataframe(strata.head(40))
            else:
                st.info('No se pudo generar estratificación.')

        st.subheader('Correlaciones por Colonia (area_m2 ~ variable)')
        col_corr_min, col_corr_var = st.columns(2)
        with col_corr_min:
            min_n = st.number_input('Mínimo n por colonia para correlación', min_value=5, max_value=200, value=15, step=1)
        with col_corr_var:
            st.caption('Se filtran sólo variables numéricas con suficiente n.')
        colony_corr = colony_area_correlations(base_area, min_n=min_n)
        if not colony_corr.empty:
            top_pos = colony_corr.sort_values('corr', ascending=False).head(30)
            top_neg = colony_corr.sort_values('corr', ascending=True).head(30)
            st.markdown('**Top Correlaciones Positivas**')
            st.dataframe(top_pos)
            st.markdown('**Top Correlaciones Negativas**')
            st.dataframe(top_neg)
            csv_col = colony_corr.to_csv(index=False).encode('utf-8')
            st.download_button('Descargar correlaciones colonia', data=csv_col, file_name=f'area_correlaciones_colonia_{PERIODO}.csv', mime='text/csv')
        else:
            st.info('Sin correlaciones por colonia (insuficiente n).')

        st.subheader('Efecto de Amenidades sobre Área (mediana)')
        if not amenities_full.empty and 'area_m2' in base_area.columns:
            amen_eff = amenity_area_effect(amenities_full, base_area, top_n=40)
            if not amen_eff.empty:
                st.dataframe(amen_eff)
                csv_ame = amen_eff.to_csv(index=False).encode('utf-8')
                st.download_button('Descargar efecto amenidades área', data=csv_ame, file_name=f'amenidades_area_effect_{PERIODO}.csv', mime='text/csv')
            else:
                st.caption('No se pudieron derivar efectos de amenidades (quizá pocas columnas binarias o bajo n).')
        else:
            st.caption('No hay dataset completo de amenidades cargado o sin area_m2.')

        st.subheader('Visualizaciones Área (Histogramas & KDE)')
        import plotly.express as px
        serie_area = base_area['area_m2'].dropna()
        if len(serie_area)>0:
            bins_area = st.slider('Bins Área', 10, 150, 50, 10)
            fig_area_hist = px.histogram(base_area, x='area_m2', nbins=bins_area, opacity=0.75)
            st.plotly_chart(fig_area_hist, use_container_width=True)
        else:
            st.info('Sin datos para histograma de área.')

# --- Sección Marketing Signals ---
st.header('📣 Marketing Signals')
if marketing_signals is not None and not marketing_signals.empty:
    ms_view = marketing_signals.head(300)
    st.dataframe(ms_view)
    csv_ms = marketing_signals.to_csv(index=False).encode('utf-8')
    st.download_button('Descargar marketing_signals.csv', data=csv_ms, file_name='marketing_signals.csv', mime='text/csv')
else:
    st.caption('marketing_signals.csv no cargado o vacío.')

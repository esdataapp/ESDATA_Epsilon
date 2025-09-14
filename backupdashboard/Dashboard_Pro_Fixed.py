#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Profesional Completo - Versión Corregida
Sistema Integral de Análisis Inmobiliario con 5 Secciones
"""

import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback, dash_table, State
import dash_bootstrap_components as dbc
from datetime import datetime
import glob
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURACIÓN INICIAL ====================

print("🚀 Iniciando Dashboard Profesional Completo - Versión Corregida...")

# Inicializar aplicación Dash con estilos futuristas
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True
)

# Agregar estilos CSS personalizados
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>ESDATA - Realty Analytics AI</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Inter', sans-serif !important;
                background: linear-gradient(135deg, #0F1419 0%, #1E293B 50%, #334155 100%) !important;
                color: #E2E8F0 !important;
                margin: 0;
                padding: 0;
            }
            
            /* Dropdown personalizado */
            .dash-dropdown .Select-control {
                background-color: rgba(15, 23, 42, 0.8) !important;
                border: 1px solid rgba(124, 58, 237, 0.3) !important;
                border-radius: 8px !important;
                color: #E2E8F0 !important;
            }
            
            .dash-dropdown .Select-value-label {
                color: #E2E8F0 !important;
            }
            
            .dash-dropdown .Select-placeholder {
                color: #64748B !important;
            }
            
            .dash-dropdown .Select-menu-outer {
                background-color: rgba(15, 23, 42, 0.95) !important;
                border: 1px solid rgba(124, 58, 237, 0.3) !important;
                border-radius: 8px !important;
            }
            
            .dash-dropdown .Select-option {
                background-color: transparent !important;
                color: #E2E8F0 !important;
            }
            
            .dash-dropdown .Select-option:hover {
                background-color: rgba(124, 58, 237, 0.2) !important;
            }
            
            /* Sliders personalizados */
            .rc-slider-track {
                background: linear-gradient(90deg, #7C3AED 0%, #A855F7 100%) !important;
            }
            
            .rc-slider-handle {
                border: 2px solid #7C3AED !important;
                background-color: #FFFFFF !important;
                box-shadow: 0 0 10px rgba(124, 58, 237, 0.5) !important;
            }
            
            .rc-slider-rail {
                background-color: rgba(71, 85, 105, 0.3) !important;
            }
            
            /* Gráficos */
            .plotly-graph-div {
                border-radius: 15px !important;
                overflow: hidden !important;
            }
            
            /* Animaciones */
            .card:hover {
                transform: translateY(-5px) !important;
                transition: all 0.3s ease !important;
            }
            
            /* Scroll personalizado */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(15, 23, 42, 0.5);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #A855F7 0%, #C084FC 100%);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.title = "ESDATA"

# Variables globales
current_data = pd.DataFrame()
reports_data = {}

# ==================== FUNCIONES DE CARGA DE DATOS ====================

def load_comprehensive_data():
    """Carga todos los datos disponibles del sistema"""
    global current_data, reports_data
    
    try:
        # Obtener ruta base del proyecto
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Cargar datos principales
        data_path = os.path.join(base_path, "Consolidados", "pretratadaCol_num", "Sep25", "pretratadaCol_num_Sep25_01.csv")
        
        if os.path.exists(data_path):
            current_data = pd.read_csv(data_path)
            print(f"✅ Datos principales cargados: {len(current_data)} registros")
            
            # Procesar datos
            current_data = preprocess_data(current_data)
        else:
            print(f"❌ No se encontró el archivo: {data_path}")
            current_data = generate_professional_sample_data()
            print("📊 Generando datos de muestra profesionales")
            
        # Cargar reportes
        load_reports(base_path)
        
        return current_data
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        current_data = generate_professional_sample_data()
        return current_data

def preprocess_data(df):
    """Procesa y limpia los datos para análisis"""
    # Limpiar nombres de columnas
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    # Convertir columnas numéricas
    numeric_cols = ['precio', 'area_m2', 'recamaras', 'banos', 'estacionamientos', 
                   'antiguedad', 'latitud', 'longitud']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].replace('Desconocido', np.nan)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calcular métricas derivadas
    if 'precio' in df.columns and 'area_m2' in df.columns:
        df['precio_m2'] = df['precio'] / df['area_m2']
    
    # Limpiar datos
    df = df.dropna(subset=['precio'])
    df = df[df['precio'] > 0]
    
    # Agregar columnas faltantes si no existen
    if 'tipo_propiedad' not in df.columns:
        df['tipo_propiedad'] = np.random.choice(['Casa', 'Departamento', 'Townhouse'], len(df))
    
    if 'colonia' not in df.columns:
        df['colonia'] = np.random.choice(['Centro', 'Providencia', 'Americana', 'Chapalita'], len(df))
    
    if 'descripcion' not in df.columns:
        df['descripcion'] = "Propiedad en excelente ubicación con amenidades modernas"
    
    return df

def generate_professional_sample_data():
    """Crear datos de muestra profesionales"""
    print("📊 Creando datos de muestra profesionales...")
    
    np.random.seed(42)
    n_records = 5000
    
    colonias = ['Centro Histórico', 'Providencia', 'Americana', 'Chapalita', 'Zapopan Centro',
                'Vallarta Norte', 'Puerta de Hierro', 'Lomas del Valle', 'Santa Tere', 'Lafayette']
    tipos = ['Casa', 'Departamento', 'Townhouse', 'Condominio']
    
    data = {
        'precio': np.random.lognormal(15, 0.5, n_records),
        'area_m2': np.random.normal(120, 40, n_records),
        'recamaras': np.random.choice([1, 2, 3, 4, 5], n_records, p=[0.1, 0.3, 0.4, 0.15, 0.05]),
        'banos': np.random.choice([1, 2, 3, 4], n_records, p=[0.2, 0.5, 0.25, 0.05]),
        'estacionamientos': np.random.choice([0, 1, 2, 3], n_records, p=[0.1, 0.4, 0.4, 0.1]),
        'antiguedad': np.random.choice(range(0, 30), n_records),
        'colonia': np.random.choice(colonias, n_records),
        'tipo_propiedad': np.random.choice(tipos, n_records),
        'latitud': np.random.normal(20.6597, 0.1, n_records),
        'longitud': np.random.normal(-103.3496, 0.1, n_records),
        'descripcion': np.random.choice([
            "Hermosa propiedad en zona residencial con jardín y alberca",
            "Moderno departamento con vista panorámica y amenidades",
            "Casa familiar en colonia tradicional con patio amplio",
            "Condominio de lujo con seguridad 24/7 y club house"
        ], n_records)
    }
    
    df = pd.DataFrame(data)
    df['precio'] = np.abs(df['precio'])
    df['area_m2'] = np.abs(df['area_m2'])
    df['precio_m2'] = df['precio'] / df['area_m2']
    
    return df

def load_reports(base_path):
    """Cargar reportes estadísticos"""
    global reports_data
    
    reports_paths = {
        'descriptivo': os.path.join(base_path, 'Estadisticas', 'Reportes', '1. Descriptivo', 'Sep25'),
        'outliers': os.path.join(base_path, 'Estadisticas', 'Reportes', '1. Outliers', 'Sep25'),
        'normalizacion': os.path.join(base_path, 'Estadisticas', 'Reportes', '1. Normalizacion', 'Sep25')
    }
    
    report_files = ['insights.csv', 'recommendations.csv', 'action_matrix.csv', 'alerts.csv']
    
    for section, path in reports_paths.items():
        if os.path.exists(path):
            print(f"🔍 Buscando reportes en: {path}")
            for file in report_files:
                pattern = os.path.join(path, f"*{file}")
                matching_files = glob.glob(pattern)
                if matching_files:
                    try:
                        reports_data[f"{section}_{file.replace('.csv', '')}"] = pd.read_csv(matching_files[0])
                        print(f"✅ Cargado: {os.path.basename(matching_files[0])}")
                    except Exception as e:
                        print(f"❌ Error cargando {file}: {e}")
                else:
                    print(f"⚠️  No encontrado: *{file} en {path}")
        else:
            print(f"❌ Directorio no encontrado: {path}")
    
    print(f"📊 Total de reportes cargados: {len(reports_data)}")

# ==================== FUNCIONES DE ANÁLISIS ====================

def analyze_outliers_contextual(df):
    """Análisis contextual de outliers por colonia"""
    outliers_analysis = {}
    
    try:
        for colonia in df['colonia'].unique():
            colonia_data = df[df['colonia'] == colonia]
            
            if len(colonia_data) < 10:
                continue
                
            # Calcular outliers usando IQR
            Q1 = colonia_data['precio'].quantile(0.25)
            Q3 = colonia_data['precio'].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = colonia_data[(colonia_data['precio'] < lower_bound) | 
                                  (colonia_data['precio'] > upper_bound)]
            
            outliers_analysis[colonia] = {
                'total_propiedades': len(colonia_data),
                'num_outliers': len(outliers),
                'porcentaje_outliers': (len(outliers) / len(colonia_data)) * 100,
                'outliers_detalle': outliers[['precio', 'area_m2', 'precio_m2']].to_dict('records')
            }
            
    except Exception as e:
        print(f"Error en análisis de outliers: {e}")
        
    return outliers_analysis

def analyze_price_dependencies(df):
    """Análisis de dependencias de precio"""
    dependencies = {}
    
    try:
        # Preparar datos numéricos
        numeric_cols = ['area_m2', 'recamaras', 'banos', 'estacionamientos', 'antiguedad']
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        if len(available_cols) > 0:
            df_numeric = df[available_cols + ['precio']].dropna()
            
            # Correlaciones
            correlations = df_numeric.corr()['precio'].drop('precio').to_dict()
            dependencies['correlations'] = correlations
            
            # Importancia de variables con Random Forest
            if len(df_numeric) > 100:
                X = df_numeric[available_cols]
                y = df_numeric['precio']
                
                rf = RandomForestRegressor(n_estimators=100, random_state=42)
                rf.fit(X, y)
                
                feature_importance = dict(zip(available_cols, rf.feature_importances_))
                dependencies['feature_importance'] = feature_importance
                
    except Exception as e:
        print(f"Error en análisis de dependencias: {e}")
        
    return dependencies

def perform_spatial_clustering(df):
    """Clustering espacial K-Means"""
    clustering_results = {}
    
    try:
        if 'latitud' in df.columns and 'longitud' in df.columns:
            coords_data = df[['latitud', 'longitud', 'precio']].dropna()
            
            if len(coords_data) > 50:
                # Clustering K-Means
                coords = coords_data[['latitud', 'longitud']]
                scaler = StandardScaler()
                coords_scaled = scaler.fit_transform(coords)
                
                kmeans = KMeans(n_clusters=5, random_state=42)
                clusters = kmeans.fit_predict(coords_scaled)
                
                coords_data['cluster'] = clusters
                clustering_results['data'] = coords_data
                
                # Análisis por cluster
                cluster_analysis = {}
                for cluster_id in range(5):
                    cluster_data = coords_data[coords_data['cluster'] == cluster_id]
                    cluster_analysis[f'Cluster_{cluster_id}'] = {
                        'num_propiedades': len(cluster_data),
                        'precio_promedio': cluster_data['precio'].mean(),
                        'centro_lat': cluster_data['latitud'].mean(),
                        'centro_lng': cluster_data['longitud'].mean()
                    }
                
                clustering_results['analysis'] = cluster_analysis
                
    except Exception as e:
        print(f"Error en clustering espacial: {e}")
        
    return clustering_results

def analyze_text_content(df):
    """Análisis de contenido textual"""
    text_analysis = {}
    
    try:
        if 'descripcion' in df.columns:
            # Segmentar por precio
            precio_mediana = df['precio'].median()
            premium_props = df[df['precio'] > precio_mediana]
            economic_props = df[df['precio'] <= precio_mediana]
            
            # Palabras frecuentes en cada segmento
            premium_text = ' '.join(premium_props['descripcion'].astype(str))
            economic_text = ' '.join(economic_props['descripcion'].astype(str))
            
            # Análisis simple de palabras
            premium_words = premium_text.lower().split()
            economic_words = economic_text.lower().split()
            
            # Contar palabras más frecuentes
            from collections import Counter
            premium_count = Counter(premium_words).most_common(20)
            economic_count = Counter(economic_words).most_common(20)
            
            text_analysis['palabras_premium'] = premium_count
            text_analysis['palabras_economico'] = economic_count
            
            # Amenidades frecuentes
            amenidades = ['alberca', 'jardín', 'seguridad', 'gym', 'terraza', 'balcón', 'cochera']
            amenidades_count = {}
            
            for amenidad in amenidades:
                count = df['descripcion'].str.contains(amenidad, case=False, na=False).sum()
                if count > 0:
                    amenidades_count[amenidad] = int(count)
            
            text_analysis['amenidades_frecuentes'] = amenidades_count
            
    except Exception as e:
        print(f"Error en análisis textual: {e}")
        
    return text_analysis

# ==================== UTILIDADES ====================

def format_currency_pro(value):
    """Formato de moneda profesional"""
    if value >= 1000000:
        return f"${value/1000000:.1f}M"
    elif value >= 1000:
        return f"${value/1000:.0f}K"
    else:
        return f"${value:.0f}"

def create_professional_kpi_card(title, value, icon, color="primary"):
    """Crear card de KPI con estilo futurista ESDATA"""
    
    # Colores corporativos ESDATA
    color_map = {
        "primary": "#7C3AED",
        "success": "#10B981", 
        "info": "#06B6D4",
        "warning": "#F59E0B"
    }
    
    main_color = color_map.get(color, "#7C3AED")
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                # Icono con efecto glow
                html.Div([
                    html.I(className=f"bi-{icon}", style={
                        'fontSize': '48px',
                        'color': main_color,
                        'filter': f'drop-shadow(0 0 10px {main_color}50)',
                        'marginBottom': '15px'
                    })
                ], className="text-center"),
                
                # Valor principal con efecto neon
                html.H2(value, style={
                    'color': main_color,
                    'fontWeight': '700',
                    'fontSize': '28px',
                    'textShadow': f'0 0 15px {main_color}50',
                    'marginBottom': '8px',
                    'fontFamily': 'monospace'
                }, className="text-center"),
                
                # Título con estilo tech
                html.P(title, style={
                    'color': '#94A3B8',
                    'fontSize': '12px',
                    'fontWeight': '500',
                    'textTransform': 'uppercase',
                    'letterSpacing': '1px',
                    'marginBottom': '0'
                }, className="text-center")
            ])
        ], style={'padding': '25px 15px'})
    ], style={
        'background': 'linear-gradient(145deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)',
        'border': f'1px solid {main_color}30',
        'borderRadius': '15px',
        'backdropFilter': 'blur(10px)',
        'boxShadow': f'0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)',
        'transition': 'all 0.3s ease',
        'position': 'relative'
    }, className="h-100")

def create_superficie_precio_m2_scatter(df):
    """Crear gráfico de dispersión superficie vs precio/m² con líneas de media"""
    if df.empty or 'area_m2' not in df.columns or 'precio_m2' not in df.columns:
        return go.Figure().add_annotation(text="No hay datos disponibles", x=0.5, y=0.5, showarrow=False)
    
    # Filtrar datos válidos
    df_clean = df.dropna(subset=['area_m2', 'precio_m2'])
    df_clean = df_clean[(df_clean['area_m2'] > 0) & (df_clean['precio_m2'] > 0)]
    
    if df_clean.empty:
        return go.Figure().add_annotation(text="No hay datos válidos", x=0.5, y=0.5, showarrow=False)
    
    # Calcular medias
    media_superficie = df_clean['area_m2'].mean()
    media_precio_m2 = df_clean['precio_m2'].mean()
    
    # Crear gráfico de dispersión
    fig = px.scatter(
        df_clean, 
        x='area_m2', 
        y='precio_m2', 
        color='colonia',
        title="Superficie vs Precio/m² con Líneas de Media",
        labels={'area_m2': 'Superficie (m²)', 'precio_m2': 'Precio/m² (MXN)'},
        hover_data=['precio', 'tipo_propiedad']
    )
    
    # Agregar línea vertical roja (media de superficie)
    fig.add_vline(
        x=media_superficie, 
        line_dash="dash", 
        line_color="red", 
        line_width=3,
        annotation_text=f"Media Superficie: {media_superficie:.0f}m²",
        annotation_position="top"
    )
    
    # Agregar línea horizontal roja (media de precio/m²)
    fig.add_hline(
        y=media_precio_m2, 
        line_dash="dash", 
        line_color="red", 
        line_width=3,
        annotation_text=f"Media Precio/m²: ${media_precio_m2:,.0f}",
        annotation_position="left"
    )
    
    # Personalizar layout
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=500,
        showlegend=True
    )
    
    return fig

# ==================== LAYOUT PRINCIPAL ====================

def create_main_layout():
    """Crear layout principal del dashboard"""
    
    return dbc.Container([
        
        # Header futurista con logo ESDATA
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Contenedor del logo y título
                    html.Div([
                        html.Div([
                            # Simulación del logo ESDATA (se puede reemplazar con imagen real)
                            html.Div([
                                html.Div("≡", style={
                                    'fontSize': '48px',
                                    'color': '#7C3AED',
                                    'fontWeight': 'bold',
                                    'transform': 'rotate(45deg)',
                                    'display': 'inline-block',
                                    'marginRight': '10px'
                                }),
                                html.Span("ESDATA", style={
                                    'fontSize': '42px',
                                    'fontWeight': '700',
                                    'color': '#7C3AED',
                                    'fontFamily': 'Arial, sans-serif'
                                })
                            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '10px'})
                        ]),
                        html.H1([
                            "REALTY ANALYTICS AI"
                        ], className="display-5 text-white mb-2", style={
                            'fontWeight': '300',
                            'letterSpacing': '2px',
                            'textShadow': '0 0 20px rgba(124, 58, 237, 0.5)'
                        }),
                        html.P("INTELLIGENCE FOR TOMORROW'S MARKET", 
                              className="text-white-50 mb-2", style={
                                  'fontSize': '14px',
                                  'letterSpacing': '3px',
                                  'fontWeight': '300',
                                  'textTransform': 'uppercase'
                              }),
                        html.P("Análisis de Venta de Departamentos • Guadalajara + Zapopan", 
                              className="text-white-50 mb-0", style={
                                  'fontSize': '16px',
                                  'fontWeight': '400'
                              })
                    ], className="text-center")
                ], className="py-5", 
                   style={
                       'background': 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 50%, rgba(51, 65, 85, 0.95) 100%)',
                       'backdropFilter': 'blur(20px)',
                       'borderRadius': '20px',
                       'border': '1px solid rgba(124, 58, 237, 0.3)',
                       'boxShadow': '0 25px 50px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)',
                       'position': 'relative',
                       'overflow': 'hidden'
                   })
            ])
        ], className="mb-4"),
        
        # KPIs Ejecutivos
        html.Div(id="kpis-executive", className="mb-4"),
        
        # Filtros Avanzados con estilo futurista
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi-funnel me-2", style={'color': '#7C3AED'}),
                        "ADVANCED ANALYTICS FILTERS"
                    ], style={
                        'background': 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.9) 100%)',
                        'border': 'none',
                        'color': '#E2E8F0',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'letterSpacing': '1px',
                        'textTransform': 'uppercase'
                    }),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("PRECIO RANGE", style={
                                    'color': '#7C3AED',
                                    'fontWeight': '600',
                                    'fontSize': '12px',
                                    'letterSpacing': '1px',
                                    'textTransform': 'uppercase'
                                }),
                                dcc.RangeSlider(
                                    id='precio-range-pro',
                                    min=0,
                                    max=10000000,
                                    step=100000,
                                    value=[0, 10000000],
                                    marks={
                                        0: {'label': '$0', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        2500000: {'label': '$2.5M', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        5000000: {'label': '$5M', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        7500000: {'label': '$7.5M', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        10000000: {'label': '$10M', 'style': {'color': '#64748B', 'fontSize': '11px'}}
                                    },
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("SUPERFICIE RANGE", style={
                                    'color': '#7C3AED',
                                    'fontWeight': '600',
                                    'fontSize': '12px',
                                    'letterSpacing': '1px',
                                    'textTransform': 'uppercase'
                                }),
                                dcc.RangeSlider(
                                    id='superficie-range-pro',
                                    min=0,
                                    max=500,
                                    step=10,
                                    value=[0, 500],
                                    marks={
                                        0: {'label': '0m²', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        100: {'label': '100m²', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        200: {'label': '200m²', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        300: {'label': '300m²', 'style': {'color': '#64748B', 'fontSize': '11px'}},
                                        500: {'label': '500m²', 'style': {'color': '#64748B', 'fontSize': '11px'}}
                                    },
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("COLONIAS", style={
                                    'color': '#7C3AED',
                                    'fontWeight': '600',
                                    'fontSize': '12px',
                                    'letterSpacing': '1px',
                                    'textTransform': 'uppercase'
                                }),
                                dcc.Dropdown(
                                    id='colonias-filter-pro',
                                    options=[],
                                    value=None,
                                    placeholder="Select locations...",
                                    multi=True,
                                    style={
                                        'backgroundColor': 'rgba(15, 23, 42, 0.8)',
                                        'color': '#E2E8F0'
                                    }
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("PROPERTY TYPE", style={
                                    'color': '#7C3AED',
                                    'fontWeight': '600',
                                    'fontSize': '12px',
                                    'letterSpacing': '1px',
                                    'textTransform': 'uppercase'
                                }),
                                dcc.Dropdown(
                                    id='tipo-filter-pro',
                                    options=[],
                                    value=None,
                                    placeholder="Select types...",
                                    multi=True,
                                    style={
                                        'backgroundColor': 'rgba(15, 23, 42, 0.8)',
                                        'color': '#E2E8F0'
                                    }
                                )
                            ], md=3)
                        ])
                    ], style={'padding': '30px'})
                ], style={
                    'background': 'linear-gradient(145deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)',
                    'border': '1px solid rgba(124, 58, 237, 0.3)',
                    'borderRadius': '15px',
                    'backdropFilter': 'blur(10px)',
                    'boxShadow': '0 8px 32px rgba(0,0,0,0.3)'
                })
            ])
        ], className="mb-4"),
        
        # Botones de Análisis futuristas
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button([
                        html.I(className="bi-play-circle me-2"),
                        "EXECUTE ANALYSIS"
                    ], id="btn-analyze-all", size="lg", style={
                        'background': 'linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)',
                        'border': '1px solid #7C3AED',
                        'borderRadius': '12px',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'letterSpacing': '1px',
                        'textTransform': 'uppercase',
                        'padding': '12px 30px',
                        'boxShadow': '0 8px 25px rgba(124, 58, 237, 0.4)',
                        'transition': 'all 0.3s ease'
                    }),
                    dbc.Button([
                        html.I(className="bi-download me-2"),
                        "EXPORT REPORTS"
                    ], id="btn-export", size="lg", style={
                        'background': 'linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)',
                        'border': '1px solid #06B6D4',
                        'borderRadius': '12px',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'letterSpacing': '1px',
                        'textTransform': 'uppercase',
                        'padding': '12px 30px',
                        'boxShadow': '0 8px 25px rgba(6, 182, 212, 0.4)',
                        'marginLeft': '15px',
                        'transition': 'all 0.3s ease'
                    }),
                    dbc.Button([
                        html.I(className="bi-arrow-clockwise me-2"),
                        "REFRESH DATA"
                    ], id="btn-refresh", size="lg", style={
                        'background': 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                        'border': '1px solid #10B981',
                        'borderRadius': '12px',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'letterSpacing': '1px',
                        'textTransform': 'uppercase',
                        'padding': '12px 30px',
                        'boxShadow': '0 8px 25px rgba(16, 185, 129, 0.4)',
                        'marginLeft': '15px',
                        'transition': 'all 0.3s ease'
                    })
                ], className="text-center")
            ])
        ], className="mb-4"),
        
        # Tabs Principales con estilo futurista
        html.Div([
            dbc.Tabs([
                dbc.Tab([
                    html.Div(id="descriptiva-content")
                ], label="📊 DESCRIPTIVE ANALYTICS", tab_id="descriptiva", 
                   tab_style={
                       'background': 'rgba(15, 23, 42, 0.8)',
                       'border': '1px solid rgba(124, 58, 237, 0.3)',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#94A3B8',
                       'fontWeight': '600',
                       'fontSize': '12px',
                       'letterSpacing': '1px'
                   },
                   active_tab_style={
                       'background': 'linear-gradient(135deg, rgba(124, 58, 237, 0.8) 0%, rgba(168, 85, 247, 0.8) 100%)',
                       'border': '1px solid #7C3AED',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#FFFFFF',
                       'fontWeight': '700',
                       'boxShadow': '0 4px 15px rgba(124, 58, 237, 0.4)'
                   }),
                
                dbc.Tab([
                    html.Div(id="outliers-content")
                ], label="🚨 OUTLIER DETECTION", tab_id="outliers",
                   tab_style={
                       'background': 'rgba(15, 23, 42, 0.8)',
                       'border': '1px solid rgba(124, 58, 237, 0.3)',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#94A3B8',
                       'fontWeight': '600',
                       'fontSize': '12px',
                       'letterSpacing': '1px'
                   },
                   active_tab_style={
                       'background': 'linear-gradient(135deg, rgba(124, 58, 237, 0.8) 0%, rgba(168, 85, 247, 0.8) 100%)',
                       'border': '1px solid #7C3AED',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#FFFFFF',
                       'fontWeight': '700',
                       'boxShadow': '0 4px 15px rgba(124, 58, 237, 0.4)'
                   }),
                
                dbc.Tab([
                    html.Div(id="dependencies-content")
                ], label="📈 DEPENDENCY ANALYSIS", tab_id="dependencies",
                   tab_style={
                       'background': 'rgba(15, 23, 42, 0.8)',
                       'border': '1px solid rgba(124, 58, 237, 0.3)',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#94A3B8',
                       'fontWeight': '600',
                       'fontSize': '12px',
                       'letterSpacing': '1px'
                   },
                   active_tab_style={
                       'background': 'linear-gradient(135deg, rgba(124, 58, 237, 0.8) 0%, rgba(168, 85, 247, 0.8) 100%)',
                       'border': '1px solid #7C3AED',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#FFFFFF',
                       'fontWeight': '700',
                       'boxShadow': '0 4px 15px rgba(124, 58, 237, 0.4)'
                   }),
                
                dbc.Tab([
                    html.Div(id="geospatial-content")
                ], label="🗺️ GEOSPATIAL INTELLIGENCE", tab_id="geospatial",
                   tab_style={
                       'background': 'rgba(15, 23, 42, 0.8)',
                       'border': '1px solid rgba(124, 58, 237, 0.3)',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#94A3B8',
                       'fontWeight': '600',
                       'fontSize': '12px',
                       'letterSpacing': '1px'
                   },
                   active_tab_style={
                       'background': 'linear-gradient(135deg, rgba(124, 58, 237, 0.8) 0%, rgba(168, 85, 247, 0.8) 100%)',
                       'border': '1px solid #7C3AED',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#FFFFFF',
                       'fontWeight': '700',
                       'boxShadow': '0 4px 15px rgba(124, 58, 237, 0.4)'
                   }),
                
                dbc.Tab([
                    html.Div(id="textual-content")
                ], label="📝 TEXT ANALYTICS", tab_id="textual",
                   tab_style={
                       'background': 'rgba(15, 23, 42, 0.8)',
                       'border': '1px solid rgba(124, 58, 237, 0.3)',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#94A3B8',
                       'fontWeight': '600',
                       'fontSize': '12px',
                       'letterSpacing': '1px'
                   },
                   active_tab_style={
                       'background': 'linear-gradient(135deg, rgba(124, 58, 237, 0.8) 0%, rgba(168, 85, 247, 0.8) 100%)',
                       'border': '1px solid #7C3AED',
                       'borderRadius': '10px 10px 0 0',
                       'color': '#FFFFFF',
                       'fontWeight': '700',
                       'boxShadow': '0 4px 15px rgba(124, 58, 237, 0.4)'
                   })
                
            ], id="main-tabs", active_tab="descriptiva")
        ], style={
            'background': 'rgba(15, 23, 42, 0.6)',
            'borderRadius': '15px',
            'padding': '0',
            'backdropFilter': 'blur(10px)',
            'border': '1px solid rgba(124, 58, 237, 0.2)'
        }),
        
        # Datos filtrados (storage)
        dcc.Store(id='filtered-data-store'),
        dcc.Store(id='outliers-analysis-store'),
        dcc.Store(id='dependencies-analysis-store'),
        dcc.Store(id='clusters-analysis-store'),
        dcc.Store(id='text-analysis-store')
        
        ], fluid=True, className="p-4", style={
            'background': 'linear-gradient(135deg, #0F1419 0%, #1E293B 50%, #334155 100%)',
            'minHeight': '100vh'
        })

# Asignar layout
app.layout = create_main_layout()

# ==================== CALLBACKS PRINCIPALES ====================

@app.callback(
    [Output('colonias-filter-pro', 'options'),
     Output('tipo-filter-pro', 'options'),
     Output('precio-range-pro', 'min'),
     Output('precio-range-pro', 'max'),
     Output('precio-range-pro', 'value'),
     Output('superficie-range-pro', 'min'),
     Output('superficie-range-pro', 'max'),
     Output('superficie-range-pro', 'value')],
    [Input('btn-refresh', 'n_clicks')]
)
def update_filter_options(n_clicks):
    """Actualizar opciones de filtros"""
    if current_data.empty:
        return [], [], 0, 10000000, [0, 10000000], 0, 500, [0, 500]
    
    # Opciones de colonias
    colonias = [{'label': col, 'value': col} for col in sorted(current_data['colonia'].unique()) if pd.notna(col)]
    
    # Opciones de tipos
    tipos = [{'label': tipo, 'value': tipo} for tipo in sorted(current_data['tipo_propiedad'].unique()) if pd.notna(tipo)]
    
    # Rango de precios
    min_precio = int(current_data['precio'].min())
    max_precio = int(current_data['precio'].max())
    
    # Rango de superficie
    min_superficie = int(current_data['area_m2'].min()) if 'area_m2' in current_data.columns else 0
    max_superficie = int(current_data['area_m2'].max()) if 'area_m2' in current_data.columns else 500
    
    return colonias, tipos, min_precio, max_precio, [min_precio, max_precio], min_superficie, max_superficie, [min_superficie, max_superficie]

@app.callback(
    Output('filtered-data-store', 'data'),
    [Input('precio-range-pro', 'value'),
     Input('superficie-range-pro', 'value'),
     Input('colonias-filter-pro', 'value'),
     Input('tipo-filter-pro', 'value')]
)
def filter_data(precio_range, superficie_range, colonias, tipos):
    """Filtrar datos según criterios seleccionados"""
    if current_data.empty:
        return None
    
    filtered_data = current_data.copy()
    
    # Filtrar por precio
    if precio_range:
        filtered_data = filtered_data[
            (filtered_data['precio'] >= precio_range[0]) & 
            (filtered_data['precio'] <= precio_range[1])
        ]
    
    # Filtrar por superficie
    if superficie_range and 'area_m2' in filtered_data.columns:
        filtered_data = filtered_data[
            (filtered_data['area_m2'] >= superficie_range[0]) & 
            (filtered_data['area_m2'] <= superficie_range[1])
        ]
    
    # Filtrar por colonias
    if colonias:
        filtered_data = filtered_data[filtered_data['colonia'].isin(colonias)]
    
    # Filtrar por tipos
    if tipos:
        filtered_data = filtered_data[filtered_data['tipo_propiedad'].isin(tipos)]
    
    return filtered_data.to_json(date_format='iso', orient='split')

@app.callback(
    Output('kpis-executive', 'children'),
    [Input('filtered-data-store', 'data')]
)
def update_executive_kpis(data_json):
    """Actualizar KPIs ejecutivos"""
    if not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    if df.empty:
        return dbc.Alert("No hay datos disponibles con los filtros seleccionados", color="warning")
    
    # Calcular KPIs
    total_props = len(df)
    precio_promedio = df['precio'].mean()
    area_promedio = df['area_m2'].mean() if 'area_m2' in df.columns else 0
    precio_m2_promedio = df['precio_m2'].mean() if 'precio_m2' in df.columns else 0
    
    # Crear cards de KPIs
    return dbc.Row([
        dbc.Col([
            create_professional_kpi_card("Total Propiedades", f"{total_props:,}", "house-door", "primary")
        ], md=3),
        dbc.Col([
            create_professional_kpi_card("Precio Promedio", format_currency_pro(precio_promedio), "currency-dollar", "success")
        ], md=3),
        dbc.Col([
            create_professional_kpi_card("Área Promedio", f"{area_promedio:.0f} m²", "rulers", "info")
        ], md=3),
        dbc.Col([
            create_professional_kpi_card("Precio/m² Promedio", format_currency_pro(precio_m2_promedio), "calculator", "warning")
        ], md=3)
    ])

@app.callback(
    [Output('outliers-analysis-store', 'data'),
     Output('dependencies-analysis-store', 'data'),
     Output('clusters-analysis-store', 'data'),
     Output('text-analysis-store', 'data')],
    [Input('filtered-data-store', 'data')]  # Cambiar a que se ejecute automáticamente
)
def execute_comprehensive_analysis(data_json):
    """Ejecutar análisis comprensivo automáticamente"""
    if not data_json:
        return None, None, None, None
    
    df = pd.read_json(data_json, orient='split')
    
    if df.empty:
        return None, None, None, None
    
    # Ejecutar todos los análisis automáticamente
    outliers_analysis = analyze_outliers_contextual(df)
    dependencies_analysis = analyze_price_dependencies(df)
    clusters_analysis = perform_spatial_clustering(df)
    text_analysis = analyze_text_content(df)
    
    return outliers_analysis, dependencies_analysis, clusters_analysis, text_analysis

@app.callback(
    Output('descriptiva-content', 'children'),
    [Input('main-tabs', 'active_tab'),
     Input('filtered-data-store', 'data')]
)
def update_descriptiva_content(active_tab, data_json):
    """Actualizar contenido de estadística descriptiva"""
    if active_tab != 'descriptiva' or not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    if df.empty:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    # Crear visualizaciones
    content = []
    
    # Header
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-graph-up me-3"),
                "Estadística Descriptiva Global y por Colonia"
            ], className="text-primary mb-3"),
            html.P("Análisis estadístico completo con distribuciones, tendencias y métricas por colonia.",
                  className="text-muted mb-4")
        ])
    )
    
    # Gráficos principales
    content.append(
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Distribución de Precios"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.histogram(
                                df, x='precio', nbins=30,
                                title="Histograma de Precios",
                                labels={'precio': 'Precio (MXN)', 'count': 'Frecuencia'}
                            ).update_layout(template="plotly_white")
                        )
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Precio vs Área"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.scatter(
                                df, x='area_m2', y='precio', color='colonia',
                                title="Relación Precio-Área por Colonia",
                                labels={'area_m2': 'Área (m²)', 'precio': 'Precio (MXN)'},
                                trendline="ols"
                            ).update_layout(template="plotly_white")
                        )
                    ])
                ])
            ], md=6)
        ], className="mb-4")
    )
    
    # Nuevo gráfico: Superficie vs Precio/m² con líneas de media
    content.append(
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi-graph-down me-2"),
                        "📊 Análisis Superficie vs Precio/m² con Referencias de Media"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_superficie_precio_m2_scatter(df)
                        )
                    ])
                ])
            ])
        ], className="mb-4")
    )
    
    # Boxplot por colonias
    content.append(
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏘️ Distribución de Precios por Colonia"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.box(
                                df, x='colonia', y='precio',
                                title="Boxplot de Precios por Colonia"
                            ).update_xaxes(tickangle=45).update_layout(template="plotly_white")
                        )
                    ])
                ])
            ])
        ], className="mb-4")
    )
    
    # Tabla resumen por colonia
    summary_by_colonia = df.groupby('colonia').agg({
        'precio': ['count', 'mean', 'median', 'std'],
        'area_m2': 'mean',
        'precio_m2': 'mean'
    }).round(2)
    
    summary_by_colonia.columns = ['Propiedades', 'Precio Prom', 'Precio Mediana', 'Desv Std', 'Área Prom', 'Precio/m² Prom']
    summary_by_colonia = summary_by_colonia.reset_index()
    
    content.append(
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Resumen Estadístico por Colonia"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=[{str(k): v for k, v in row.items()} for row in summary_by_colonia.to_dict('records')],
                            columns=[{'name': str(col), 'id': str(col)} for col in summary_by_colonia.columns],
                            style_cell={'textAlign': 'center'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                            page_size=10
                        )
                    ])
                ])
            ])
        ])
    )
    
    return html.Div(content)

@app.callback(
    Output('outliers-content', 'children'),
    [Input('main-tabs', 'active_tab'),
     Input('outliers-analysis-store', 'data')]
)
def update_outliers_content(active_tab, outliers_data):
    """Actualizar contenido de detección de outliers"""
    if active_tab != 'outliers':
        return html.Div()
    
    content = []
    
    # Header
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-exclamation-triangle me-3"),
                "Detección y Gestión de Outliers Contextual"
            ], className="text-primary mb-3"),
            html.P("Análisis contextual de outliers por colonia con clasificación inteligente.",
                  className="text-muted mb-4")
        ])
    )
    
    # Mostrar información de reportes cargados
    if reports_data:
        outliers_insights = reports_data.get('outliers_insights')
        outliers_alerts = reports_data.get('outliers_alerts')
        
        if outliers_insights is not None and not outliers_insights.empty:
            content.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("🔍 Insights de Outliers (Reportes)"),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    data=outliers_insights.head(10).to_dict('records'),
                                    columns=[{'name': col, 'id': col} for col in outliers_insights.columns],
                                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                                    page_size=5
                                )
                            ])
                        ])
                    ])
                ], className="mb-4")
            )
        
        if outliers_alerts is not None and not outliers_alerts.empty:
            content.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("⚠️ Alertas de Outliers"),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    data=outliers_alerts.head(10).to_dict('records'),
                                    columns=[{'name': col, 'id': col} for col in outliers_alerts.columns],
                                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                                    style_header={'backgroundColor': '#fff3cd', 'fontWeight': 'bold'},
                                    page_size=5
                                )
                            ])
                        ])
                    ])
                ], className="mb-4")
            )
    
    if outliers_data:
        # Crear gráfico de outliers por colonia
        colonias = list(outliers_data.keys())
        porcentajes = [outliers_data[col]['porcentaje_outliers'] for col in colonias]
        
        fig = px.bar(
            x=colonias, y=porcentajes,
            title="Porcentaje de Outliers por Colonia",
            labels={'x': 'Colonia', 'y': '% Outliers'},
            color=porcentajes,
            color_continuous_scale='Reds'
        )
        fig.update_xaxes(tickangle=45)
        fig.update_layout(template="plotly_white")
        
        content.append(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔍 Análisis de Outliers por Colonia"),
                        dbc.CardBody([
                            dcc.Graph(figure=fig)
                        ])
                    ])
                ])
            ], className="mb-4")
        )
        
        # Resumen de outliers
        total_props = sum(data['total_propiedades'] for data in outliers_data.values())
        total_outliers = sum(data['num_outliers'] for data in outliers_data.values())
        
        content.append(
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H4("📊 Resumen de Outliers", className="alert-heading"),
                        html.P(f"Total de outliers detectados: {total_outliers:,}"),
                        html.P(f"Porcentaje general: {(total_outliers/total_props*100):.1f}%"),
                        html.P(f"Colonias analizadas: {len(outliers_data)}")
                    ], color="info")
                ])
            ])
        )
    
    if not outliers_data and not reports_data:
        content.append(
            dbc.Alert("Los datos se están procesando automáticamente. Si persiste este mensaje, revise la carga de datos.", color="warning")
        )
    
    return html.Div(content)

# Continuar con los demás callbacks...
@app.callback(
    Output('dependencies-content', 'children'),
    [Input('main-tabs', 'active_tab'),
     Input('dependencies-analysis-store', 'data')]
)
def update_dependencies_content(active_tab, dependencies_data):
    """Actualizar contenido de análisis de dependencias"""
    if active_tab != 'dependencies':
        return html.Div()
    
    content = []
    
    # Header
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-graph-up me-3"),
                "Análisis de Dependencia e Influencia sobre Precio"
            ], className="text-primary mb-3"),
            html.P("Análisis de correlaciones e importancia de variables usando Machine Learning.",
                  className="text-muted mb-4")
        ])
    )
    
    if dependencies_data:
        # Gráfico de correlaciones
        if 'correlations' in dependencies_data:
            correlations = dependencies_data['correlations']
            variables = list(correlations.keys())
            values = list(correlations.values())
            
            fig_corr = px.bar(
                x=values, y=variables, orientation='h',
                title="Correlación con Precio",
                labels={'x': 'Correlación', 'y': 'Variables'},
                color=values,
                color_continuous_scale='RdBu'
            )
            fig_corr.update_layout(template="plotly_white")
            
            content.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("📊 Correlaciones con Precio"),
                            dbc.CardBody([
                                dcc.Graph(figure=fig_corr)
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        # Importancia de variables si está disponible
                        html.Div(id="feature-importance-placeholder")
                    ], md=6)
                ], className="mb-4")
            )
        
        # Importancia de variables
        if 'feature_importance' in dependencies_data:
            importance = dependencies_data['feature_importance']
            variables = list(importance.keys())
            values = list(importance.values())
            
            fig_imp = px.bar(
                x=values, y=variables, orientation='h',
                title="Importancia de Variables (Random Forest)",
                labels={'x': 'Importancia', 'y': 'Variables'},
                color=values,
                color_continuous_scale='Viridis'
            )
            fig_imp.update_layout(template="plotly_white")
            
            content.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("🤖 Importancia de Variables (ML)"),
                            dbc.CardBody([
                                dcc.Graph(figure=fig_imp)
                            ])
                        ])
                    ])
                ], className="mb-4")
            )
    else:
        content.append(
            dbc.Alert("Ejecuta el análisis para ver las dependencias", color="info")
        )
    
    return html.Div(content)

@app.callback(
    Output('geospatial-content', 'children'),
    [Input('main-tabs', 'active_tab'),
     Input('clusters-analysis-store', 'data'),
     Input('filtered-data-store', 'data')]
)
def update_geospatial_content(active_tab, clusters_data, data_json):
    """Actualizar contenido de análisis geoespacial"""
    if active_tab != 'geospatial':
        return html.Div()
    
    content = []
    
    # Header
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-map me-3"),
                "Análisis Geoespacial (Mapas + Clustering)"
            ], className="text-primary mb-3"),
            html.P("Mapas interactivos y clustering espacial K-Means para análisis de micro-mercados.",
                  className="text-muted mb-4")
        ])
    )
    
    if data_json:
        df = pd.read_json(data_json, orient='split')
        
        if 'latitud' in df.columns and 'longitud' in df.columns and not df.empty:
            # Mapa de propiedades
            fig_map = px.scatter_mapbox(
                df, lat='latitud', lon='longitud',
                color='precio', size='area_m2',
                hover_data=['colonia', 'tipo_propiedad', 'precio'],
                color_continuous_scale='Viridis',
                title="Mapa Interactivo de Propiedades",
                zoom=10
            )
            fig_map.update_layout(
                mapbox_style="open-street-map",
                height=500
            )
            
            content.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("🗺️ Mapa Interactivo de Propiedades"),
                            dbc.CardBody([
                                dcc.Graph(figure=fig_map)
                            ])
                        ])
                    ])
                ], className="mb-4")
            )
            
            # Información de clustering si está disponible
            if clusters_data and 'analysis' in clusters_data:
                cluster_info = []
                for cluster_id, data in clusters_data['analysis'].items():
                    cluster_info.append({
                        'Cluster': cluster_id,
                        'Propiedades': data['num_propiedades'],
                        'Precio Promedio': f"${data['precio_promedio']:,.0f}",
                        'Centro Lat': f"{data['centro_lat']:.4f}",
                        'Centro Lng': f"{data['centro_lng']:.4f}"
                    })
                
                content.append(
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("📊 Análisis de Clusters Espaciales"),
                                dbc.CardBody([
                                    dash_table.DataTable(
                                        data=[{str(k): str(v) for k, v in row.items()} for row in cluster_info],
                                        columns=[{'name': str(col), 'id': str(col)} for col in cluster_info[0].keys() if cluster_info],
                                        style_cell={'textAlign': 'center'},
                                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
                                    )
                                ])
                            ])
                        ])
                    ])
                )
        else:
            content.append(
                dbc.Alert("No hay datos de coordenadas disponibles para análisis geoespacial", color="warning")
            )
    else:
        content.append(
            dbc.Alert("Selecciona filtros para ver el análisis geoespacial", color="info")
        )
    
    return html.Div(content)

@app.callback(
    Output('textual-content', 'children'),
    [Input('main-tabs', 'active_tab'),
     Input('text-analysis-store', 'data')]
)
def update_textual_content(active_tab, text_data):
    """Actualizar contenido de análisis textual"""
    if active_tab != 'textual':
        return html.Div()
    
    content = []
    
    # Header
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-chat-text me-3"),
                "Análisis de Texto (Descripciones y Amenidades)"
            ], className="text-primary mb-3"),
            html.P("Análisis de contenido textual, palabras clave y amenidades frecuentes.",
                  className="text-muted mb-4")
        ])
    )
    
    if text_data:
        # Palabras clave por segmento
        if 'palabras_premium' in text_data and 'palabras_economico' in text_data:
            content.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("💎 Palabras Clave - Propiedades Premium"),
                            dbc.CardBody([
                                html.Ul([
                                    html.Li(f"{word} ({count})") 
                                    for word, count in text_data['palabras_premium'][:10]
                                ])
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("🏠 Palabras Clave - Propiedades Económicas"),
                            dbc.CardBody([
                                html.Ul([
                                    html.Li(f"{word} ({count})") 
                                    for word, count in text_data['palabras_economico'][:10]
                                ])
                            ])
                        ])
                    ], md=6)
                ], className="mb-4")
            )
        
        # Amenidades frecuentes
        if 'amenidades_frecuentes' in text_data:
            amenidades = text_data['amenidades_frecuentes']
            if amenidades:
                fig_amenidades = px.bar(
                    x=list(amenidades.values()),
                    y=list(amenidades.keys()),
                    orientation='h',
                    title="Frecuencia de Amenidades"
                )
                fig_amenidades.update_layout(template="plotly_white")
                
                content.append(
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("🏊‍♀️ Amenidades Más Frecuentes"),
                                dbc.CardBody([
                                    dcc.Graph(figure=fig_amenidades)
                                ])
                            ])
                        ])
                    ])
                )
    else:
        content.append(
            dbc.Alert("Ejecuta el análisis para ver el análisis textual", color="info")
        )
    
    return html.Div(content)

# ==================== EJECUCIÓN PRINCIPAL ====================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 DASHBOARD PROFESIONAL COMPLETO - VERSIÓN CORREGIDA")
    print("="*80)
    print("📊 Sistema Integral con 5 Secciones:")
    print("   1. 📊 Estadística Descriptiva Global y por Colonia")
    print("   2. 🚨 Detección y Gestión de Outliers Contextual") 
    print("   3. 📈 Análisis de Dependencia e Influencia sobre Precio")
    print("   4. 🗺️ Análisis Geoespacial (Mapas + Clustering)")
    print("   5. 📝 Análisis de Texto (Títulos y Amenidades)")
    print("\n🎯 Características:")
    print("   • Diseño glassmorphism profesional")
    print("   • Análisis contextual avanzado")
    print("   • Machine Learning integrado")
    print("   • Mapas interactivos")
    print("   • Sistema de reportes completo")
    print("\n🌐 Acceso:")
    print("   • URL: http://127.0.0.1:8053")
    print("   • Optimizado para presentaciones ejecutivas")
    print("="*80)
    
    try:
        # Cargar datos al inicio
        load_comprehensive_data()
        
        print("\n🏁 Iniciando servidor profesional...")
        print("💡 Presiona Ctrl+C para detener")
        print("="*80 + "\n")
        
        app.run(
            debug=True,
            host='127.0.0.1',
            port=8053
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard profesional detenido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        print("🔚 Finalizando Dashboard Profesional")

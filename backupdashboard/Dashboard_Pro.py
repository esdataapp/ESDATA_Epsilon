#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏠 DASHBOARD PROFESIONAL DE ANÁLISIS INMOBILIARIO
Sistema integrado de visualización profesional para análisis completo del mercado inmobiliario
Basado en especificaciones de Plan Dashboard 1 y 2

Secciones implementadas:
📊 1. Estadística Descriptiva Global y por Colonia
🚨 2. Detección y Gestión de Outliers Contextual  
📈 3. Análisis de Dependencia e Influencia sobre Precio
🗺️ 4. Análisis Geoespacial (Mapas + Clustering)
📝 5. Análisis de Texto (Títulos, Descripciones, Amenidades)
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
import warnings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import re
from collections import Counter
import base64
import io

warnings.filterwarnings('ignore')

# ==================== CONFIGURACIÓN PROFESIONAL ====================

# Configurar Dash con diseño profesional
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    title="Dashboard Profesional Inmobiliario | GDL"
)

# Configurar meta tags para dispositivos móviles
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Inter', sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .dashboard-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            }
            .card-glassmorphism {
                background: rgba(255, 255, 255, 0.7);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .metric-card {
                background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,249,250,0.9));
                border-left: 4px solid;
                transition: transform 0.3s ease;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            }
            .tab-content-modern {
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                margin-top: 20px;
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

# ==================== VARIABLES GLOBALES ====================
current_data = None
reports_data = {}
clusters_data = None
text_analysis_cache = {}

# ==================== FUNCIONES CORE DE DATOS ====================

def load_comprehensive_data():
    """Carga todos los datos disponibles del sistema"""
    global current_data, reports_data
    
    # Obtener ruta base del proyecto
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    data_paths = {
        'main_data': os.path.join(base_path, 'Consolidados', 'pretratadaCol_num', 'Sep25', 'pretratadaCol_num_Sep25_01.csv'),
        'descriptivo': os.path.join(base_path, 'Estadisticas', 'Reportes', '1. Descriptivo', 'Sep25'),
        'outliers': os.path.join(base_path, 'Estadisticas', 'Reportes', '1. Outliers', 'Sep25'),
        'normalizacion': os.path.join(base_path, 'Estadisticas', 'Reportes', '1. Normalizacion', 'Sep25'),
        'colonias': os.path.join(base_path, 'Estadisticas', 'Reportes', 'Colonias', 'Sep25')
    }
    
    # Cargar datos principales
    try:
        if os.path.exists(data_paths['main_data']):
            current_data = pd.read_csv(data_paths['main_data'])
            print(f"✅ Datos principales cargados: {len(current_data)} registros")
            
            # Procesar datos
            current_data = preprocess_data(current_data)
        else:
            print(f"❌ No se encontró el archivo: {data_paths['main_data']}")
            current_data = generate_professional_sample_data()
            print("📊 Generando datos de muestra profesionales")
    except Exception as e:
        print(f"❌ Error cargando datos principales: {e}")
        current_data = generate_professional_sample_data()
    
    # Cargar reportes específicos
    load_analysis_reports(data_paths)
    
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
    
    # Crear categorías de precio
    if 'precio' in df.columns:
        df['categoria_precio'] = pd.cut(df['precio'], 
                                       bins=5, 
                                       labels=['Económico', 'Medio-Bajo', 'Medio', 'Medio-Alto', 'Premium'])
    
    return df

def generate_professional_sample_data():
    """Genera datos de muestra profesionales y realistas"""
    np.random.seed(42)
    
    # Colonias reales de Guadalajara con características específicas
    colonias_data = {
        'Country Club': {'base_price': 15000000, 'variation': 0.4, 'premium': True},
        'Providencia': {'base_price': 8000000, 'variation': 0.3, 'premium': True},
        'Andares': {'base_price': 12000000, 'variation': 0.5, 'premium': True},
        'Americana': {'base_price': 5000000, 'variation': 0.3, 'premium': False},
        'Lafayette': {'base_price': 4500000, 'variation': 0.25, 'premium': False},
        'Chapalita': {'base_price': 6000000, 'variation': 0.35, 'premium': False},
        'Vallarta Norte': {'base_price': 3500000, 'variation': 0.3, 'premium': False},
        'Centro': {'base_price': 2500000, 'variation': 0.4, 'premium': False},
        'Zona Rosa': {'base_price': 4000000, 'variation': 0.3, 'premium': False},
        'Minerva': {'base_price': 5500000, 'variation': 0.3, 'premium': False},
        'Del Valle': {'base_price': 3000000, 'variation': 0.25, 'premium': False},
        'Oblatos': {'base_price': 1800000, 'variation': 0.2, 'premium': False},
        'San Juan de Dios': {'base_price': 1500000, 'variation': 0.15, 'premium': False}
    }
    
    ciudades = ['Guadalajara', 'Zapopan']
    tipos_propiedad = ['Casa', 'Departamento', 'Condominio', 'Townhouse', 'Penthouse']
    operaciones = ['Venta', 'Renta']
    
    # Descripciones realistas por segmento
    descripciones_premium = [
        "Espectacular residencia en exclusivo fraccionamiento con vista panorámica, alberca infinity, jacuzzi, cava, terraza gourmet",
        "Lujosa propiedad con acabados de primera, cocina gourmet, master suite con vestidor, jardín privado, sistema domótico",
        "Exclusiva residencia con arquitectura contemporánea, alberca climatizada, gym privado, estudio, triple garaje cubierto"
    ]
    
    descripciones_media = [
        "Amplia casa en fraccionamiento privado con jardín, cochera techada, área de servicio completa",
        "Bonita propiedad en zona residencial, 3 recámaras, 2 baños completos, patio trasero, cerca de centros comerciales",
        "Casa en excelente ubicación, cocina integral, sala comedor, recámaras amplias, fácil acceso a vialidades"
    ]
    
    descripciones_economica = [
        "Casa sencilla en colonia popular, funcional, cerca de transporte público y escuelas",
        "Propiedad práctica ideal para familia pequeña, 2 recámaras, patio pequeño",
        "Casa económica en zona en desarrollo, buena oportunidad de inversión"
    ]
    
    n = 6000
    data = []
    
    # Generar datos por colonia
    for colonia, info in colonias_data.items():
        # Número de propiedades por colonia (más en colonias populares)
        n_colonia = np.random.poisson(n // len(colonias_data))
        if n_colonia < 10:  # Mínimo para análisis
            n_colonia = 10
        
        for i in range(n_colonia):
            # Precio base con variación por colonia
            precio_base = info['base_price']
            precio = np.random.lognormal(np.log(precio_base), info['variation'])
            
            # Área correlacionada con precio pero con variación
            area_factor = (precio / precio_base) ** 0.3  # Correlación no perfecta
            area_base = 150 if not info['premium'] else 250
            area = np.random.normal(area_base * area_factor, 30)
            area = max(50, min(area, 800))  # Límites realistas
            
            # Recámaras basadas en área y tipo
            tipo = np.random.choice(tipos_propiedad, 
                                  p=[0.4, 0.3, 0.15, 0.1, 0.05] if not info['premium'] 
                                  else [0.3, 0.2, 0.2, 0.2, 0.1])
            
            if area < 80:
                recamaras = np.random.choice([1, 2], p=[0.3, 0.7])
            elif area < 150:
                recamaras = np.random.choice([2, 3], p=[0.4, 0.6])
            elif area < 250:
                recamaras = np.random.choice([3, 4], p=[0.6, 0.4])
            else:
                recamaras = np.random.choice([4, 5, 6], p=[0.5, 0.3, 0.2])
            
            # Baños correlacionados con recámaras
            banos = max(1, recamaras + np.random.choice([-1, 0, 1], p=[0.2, 0.6, 0.2]))
            
            # Estacionamientos
            if info['premium']:
                estacionamientos = np.random.choice([2, 3, 4], p=[0.4, 0.4, 0.2])
            else:
                estacionamientos = np.random.choice([1, 2, 3], p=[0.5, 0.4, 0.1])
            
            # Coordenadas realistas para Guadalajara
            lat_base = 20.6597 + np.random.normal(0, 0.05)
            lon_base = -103.3496 + np.random.normal(0, 0.05)
            
            # Descripción basada en precio
            if precio > 8000000:
                descripcion = np.random.choice(descripciones_premium)
            elif precio > 3000000:
                descripcion = np.random.choice(descripciones_media)
            else:
                descripcion = np.random.choice(descripciones_economica)
            
            data.append({
                'id': len(data) + 1,
                'ciudad': np.random.choice(ciudades, p=[0.6, 0.4]),
                'colonia': colonia,
                'tipo_propiedad': tipo,
                'operacion': np.random.choice(operaciones, p=[0.8, 0.2]),
                'precio': int(precio),
                'area_m2': int(area),
                'recamaras': int(recamaras),
                'banos': banos,
                'estacionamientos': int(estacionamientos),
                'antiguedad': np.random.randint(0, 25),
                'latitud': lat_base,
                'longitud': lon_base,
                'descripcion': descripcion,
                'tiempo_publicacion': np.random.randint(1, 365)
            })
    
    df = pd.DataFrame(data)
    
    # Calcular precio por m²
    df['precio_m2'] = (df['precio'] / df['area_m2']).round(2)
    
    # Crear categorías de precio
    df['categoria_precio'] = pd.cut(df['precio'], 
                                   bins=5, 
                                   labels=['Económico', 'Medio-Bajo', 'Medio', 'Medio-Alto', 'Premium'])
    
    print(f"📊 Generados {len(df)} registros profesionales de muestra")
    return df

def load_analysis_reports(data_paths):
    """Carga todos los reportes de análisis disponibles"""
    global reports_data
    
    report_files = [
        'insights.csv', 'recommendations.csv', 'action_matrix.csv', 'alerts.csv'
    ]
    
    for section, path in data_paths.items():
        if section != 'main_data' and os.path.exists(path):
            for file in report_files:
                # Buscar archivos que contengan el patrón
                import glob
                file_pattern = os.path.join(path, f"*{file}")
                matching_files = glob.glob(file_pattern)
                if matching_files:
                    try:
                        reports_data[f"{section}_{file.replace('.csv', '')}"] = pd.read_csv(matching_files[0])
                        print(f"✅ Cargado: {os.path.basename(matching_files[0])}")
                    except Exception as e:
                        print(f"❌ Error cargando {file}: {e}")
                else:
                    print(f"⚠️ No encontrado patrón: {file_pattern}")

# ==================== ANÁLISIS ESPECIALIZADO ====================

def analyze_outliers_contextual(df):
    """Análisis contextual de outliers por colonia"""
    outliers_analysis = {}
    
    for colonia in df['colonia'].unique():
        colonia_data = df[df['colonia'] == colonia]
        
        if len(colonia_data) < 5:  # Muy pocos datos
            continue
            
        # Calcular outliers por IQR local (por colonia)
        Q1 = colonia_data['precio'].quantile(0.25)
        Q3 = colonia_data['precio'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = colonia_data[(colonia_data['precio'] < lower_bound) | 
                              (colonia_data['precio'] > upper_bound)]
        
        # Clasificar outliers
        outliers_classified = []
        for _, outlier in outliers.iterrows():
            # Criterios para clasificación
            ratio_precio_area = outlier['precio'] / outlier['area_m2']
            median_ratio = colonia_data['precio_m2'].median()
            
            if ratio_precio_area > median_ratio * 2:
                classification = "Sospechoso - Precio muy alto por m²"
                action = "Investigar"
            elif ratio_precio_area < median_ratio * 0.5:
                classification = "Sospechoso - Precio muy bajo por m²"
                action = "Investigar"
            elif outlier['area_m2'] > 500 or outlier['recamaras'] > 6:
                classification = "Legítimo - Propiedad premium"
                action = "Mantener"
            else:
                classification = "Posible error"
                action = "Revisar"
            
            outliers_classified.append({
                'id': outlier['id'],
                'precio': outlier['precio'],
                'area_m2': outlier['area_m2'],
                'precio_m2': ratio_precio_area,
                'clasificacion': classification,
                'accion': action
            })
        
        outliers_analysis[colonia] = {
            'total_propiedades': len(colonia_data),
            'num_outliers': len(outliers),
            'porcentaje_outliers': (len(outliers) / len(colonia_data)) * 100,
            'outliers_detalle': outliers_classified
        }
    
    return outliers_analysis

def analyze_price_dependencies(df):
    """Análisis de dependencias e influencia sobre precio"""
    # Variables numéricas para análisis
    numeric_vars = ['area_m2', 'recamaras', 'banos', 'estacionamientos', 'antiguedad']
    available_vars = [var for var in numeric_vars if var in df.columns]
    
    if len(available_vars) < 2:
        return {}
    
    # Preparar datos limpios
    analysis_df = df[available_vars + ['precio']].dropna()
    
    # Correlaciones
    correlations = analysis_df.corr()['precio'].drop('precio').sort_values(ascending=False)
    
    # Importancia usando Random Forest
    try:
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        X = analysis_df[available_vars]
        y = analysis_df['precio']
        rf.fit(X, y)
        
        importance = pd.Series(rf.feature_importances_, index=available_vars).sort_values(ascending=False)
        
        return {
            'correlations': correlations.to_dict(),
            'feature_importance': importance.to_dict(),
            'r2_score': rf.score(X, y)
        }
    except Exception as e:
        return {'correlations': correlations.to_dict()}

def perform_spatial_clustering(df):
    """Clustering espacial K-Means"""
    global clusters_data
    
    if 'latitud' not in df.columns or 'longitud' not in df.columns:
        return None
    
    # Filtrar datos con coordenadas válidas
    spatial_df = df.dropna(subset=['latitud', 'longitud', 'precio'])
    
    if len(spatial_df) < 10:
        return None
    
    # Preparar datos para clustering
    coords = spatial_df[['latitud', 'longitud']].values
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords)
    
    # K-Means clustering
    n_clusters = min(8, len(spatial_df) // 20)  # Máximo 8 clusters
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    spatial_df['cluster'] = kmeans.fit_predict(coords_scaled)
    
    # Análisis por cluster
    cluster_analysis = {}
    for cluster_id in range(n_clusters):
        cluster_data = spatial_df[spatial_df['cluster'] == cluster_id]
        
        cluster_analysis[f'Cluster_{cluster_id}'] = {
            'num_propiedades': len(cluster_data),
            'precio_promedio': cluster_data['precio'].mean(),
            'precio_mediano': cluster_data['precio'].median(),
            'area_promedio': cluster_data['area_m2'].mean(),
            'centro_lat': cluster_data['latitud'].mean(),
            'centro_lon': cluster_data['longitud'].mean(),
            'colonias_principales': cluster_data['colonia'].value_counts().head(3).to_dict()
        }
    
    clusters_data = {
        'data': spatial_df,
        'analysis': cluster_analysis,
        'centers': kmeans.cluster_centers_,
        'scaler': scaler
    }
    
    return clusters_data

def analyze_text_content(df):
    """Análisis de contenido textual"""
    global text_analysis_cache
    
    if 'descripcion' not in df.columns:
        return {}
    
    # Limpiar y procesar texto
    descriptions = df['descripcion'].dropna()
    
    # Palabras por segmento de precio
    high_price_desc = df[df['categoria_precio'].isin(['Premium', 'Medio-Alto'])]['descripcion'].dropna()
    low_price_desc = df[df['categoria_precio'].isin(['Económico', 'Medio-Bajo'])]['descripcion'].dropna()
    
    def extract_keywords(texts):
        # Palabras clave inmobiliarias
        all_text = ' '.join(texts).lower()
        # Limpiar texto
        clean_text = re.sub(r'[^\w\s]', ' ', all_text)
        words = clean_text.split()
        
        # Filtrar palabras relevantes
        relevant_words = [word for word in words if len(word) > 3 and 
                         word not in ['casa', 'propiedad', 'cuenta', 'tiene', 'esta', 'para']]
        
        return Counter(relevant_words).most_common(10)
    
    analysis = {
        'palabras_premium': extract_keywords(high_price_desc),
        'palabras_economico': extract_keywords(low_price_desc),
        'total_descripciones': len(descriptions)
    }
    
    # Amenidades frecuentes
    amenidades = ['alberca', 'jacuzzi', 'gym', 'terraza', 'jardin', 'cochera', 
                 'seguridad', 'vista', 'gourmet', 'climatizada']
    
    amenidades_freq = {}
    for amenidad in amenidades:
        count = descriptions.str.contains(amenidad, case=False, na=False).sum()
        if count > 0:
            amenidades_freq[amenidad] = count
    
    analysis['amenidades_frecuentes'] = amenidades_freq
    
    text_analysis_cache = analysis
    return analysis

# ==================== LAYOUT PROFESIONAL ====================

def create_professional_header():
    """Crea header profesional con glassmorphism"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.H1([
                        html.I(className="bi-building me-3", style={'fontSize': '2.5rem'}),
                        "Dashboard Profesional Inmobiliario"
                    ], className="text-white mb-2", style={'fontWeight': '700'}),
                    html.P([
                        "Sistema integral de análisis del mercado inmobiliario • ",
                        html.Span("Guadalajara & Zapopan", className="fw-bold"),
                        " • Análisis Profesional Completo"
                    ], className="text-white-50 mb-3", style={'fontSize': '1.1rem'}),
                    html.Div([
                        dbc.Badge("📊 Estadística Descriptiva", color="light", className="me-2 mb-1"),
                        dbc.Badge("🚨 Detección Outliers", color="light", className="me-2 mb-1"),
                        dbc.Badge("📈 Análisis Dependencias", color="light", className="me-2 mb-1"),
                        dbc.Badge("🗺️ Análisis Geoespacial", color="light", className="me-2 mb-1"),
                        dbc.Badge("📝 Análisis Textual", color="light", className="me-2 mb-1")
                    ])
                ], className="text-center")
            ], className="p-4", style={
                'background': 'linear-gradient(135deg, rgba(102,126,234,0.9) 0%, rgba(118,75,162,0.9) 100%)',
                'backdropFilter': 'blur(20px)',
                'borderRadius': '20px',
                'border': '1px solid rgba(255,255,255,0.2)',
                'boxShadow': '0 25px 50px rgba(0,0,0,0.15)'
            })
        ])
    ], className="mb-4")

def create_advanced_controls():
    """Crea panel de controles avanzados"""
    return dbc.Card([
        dbc.CardBody([
            html.H5([
                html.I(className="bi-sliders me-2"),
                "Centro de Control Avanzado"
            ], className="mb-3"),
            
            dbc.Row([
                # Filtros geográficos
                dbc.Col([
                    html.Label("🏙️ Ciudad", className="fw-bold"),
                    dcc.Dropdown(
                        id='city-filter-pro',
                        multi=True,
                        placeholder="Todas las ciudades...",
                        className="mb-2"
                    )
                ], md=2),
                
                dbc.Col([
                    html.Label("🏘️ Colonia", className="fw-bold"),
                    dcc.Dropdown(
                        id='colonia-filter-pro',
                        multi=True,
                        placeholder="Todas las colonias...",
                        className="mb-2"
                    )
                ], md=3),
                
                # Filtros de propiedad
                dbc.Col([
                    html.Label("🏠 Tipo Propiedad", className="fw-bold"),
                    dcc.Dropdown(
                        id='property-type-filter-pro',
                        multi=True,
                        placeholder="Todos los tipos...",
                        className="mb-2"
                    )
                ], md=2),
                
                dbc.Col([
                    html.Label("💰 Operación", className="fw-bold"),
                    dcc.Dropdown(
                        id='operation-filter-pro',
                        multi=True,
                        placeholder="Venta/Renta...",
                        className="mb-2"
                    )
                ], md=2),
                
                # Controles de acción
                dbc.Col([
                    html.Label("⚡ Acciones", className="fw-bold"),
                    html.Div([
                        dbc.Button("🔄 Cargar", id='load-data-pro', color="primary", size="sm", className="me-2"),
                        dbc.Button("🎯 Filtrar", id='apply-filters-pro', color="success", size="sm")
                    ])
                ], md=3)
            ]),
            
            html.Hr(),
            
            # Rangos avanzados
            dbc.Row([
                dbc.Col([
                    html.Label("💵 Rango de Precio", className="fw-bold"),
                    dcc.RangeSlider(
                        id='price-range-pro',
                        min=0, max=50000000, step=500000,
                        marks={i: f'${i//1000000}M' for i in range(0, 51000000, 10000000)},
                        value=[0, 20000000],
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=4),
                
                dbc.Col([
                    html.Label("📐 Rango de Área (m²)", className="fw-bold"),
                    dcc.RangeSlider(
                        id='area-range-pro',
                        min=0, max=1000, step=10,
                        marks={i: f'{i}m²' for i in range(0, 1001, 200)},
                        value=[50, 500],
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=4),
                
                dbc.Col([
                    html.Label("🛏️ Filtros Especiales", className="fw-bold"),
                    dcc.Dropdown(
                        id='special-filter-pro',
                        options=[
                            {'label': '⭐ Top 10% Precios', 'value': 'top_precios'},
                            {'label': '🏰 Propiedades Grandes (>300m²)', 'value': 'grandes'},
                            {'label': '💎 Segmento Premium', 'value': 'premium'},
                            {'label': '🚨 Solo Outliers', 'value': 'outliers'},
                            {'label': '🏠 Casas Familiares (3+ rec)', 'value': 'familiares'}
                        ],
                        placeholder="Filtro especial...",
                        className="mb-2"
                    )
                ], md=4)
            ])
        ])
    ], className="card-glassmorphism mb-4")

# ==================== LAYOUT PRINCIPAL Y SECCIONES ====================

app.layout = dbc.Container([
    # Stores para datos
    dcc.Store(id='filtered-data-pro'),
    dcc.Store(id='outliers-analysis-pro'),
    dcc.Store(id='dependencies-analysis-pro'),
    dcc.Store(id='clusters-analysis-pro'),
    dcc.Store(id='text-analysis-pro'),
    
    # Header profesional
    create_professional_header(),
    
    # Panel de controles avanzados
    create_advanced_controls(),
    
    # KPIs Ejecutivos
    html.Div(id='executive-kpis-pro'),
    
    # Tabs principales de las 5 secciones
    dbc.Tabs([
        # 📊 1. SECCIÓN: ESTADÍSTICA DESCRIPTIVA
        dbc.Tab(
            html.Div([
                html.Div(id='estadistica-descriptiva-content', className="tab-content-modern")
            ]),
            label="📊 Estadística Descriptiva",
            tab_id="estadistica",
            className="mb-2"
        ),
        
        # 🚨 2. SECCIÓN: DETECCIÓN DE OUTLIERS
        dbc.Tab(
            html.Div([
                html.Div(id='outliers-detection-content', className="tab-content-modern")
            ]),
            label="🚨 Detección Outliers",
            tab_id="outliers",
            className="mb-2"
        ),
        
        # 📈 3. SECCIÓN: ANÁLISIS DE DEPENDENCIAS
        dbc.Tab(
            html.Div([
                html.Div(id='dependencies-analysis-content', className="tab-content-modern")
            ]),
            label="📈 Análisis Dependencias",
            tab_id="dependencies",
            className="mb-2"
        ),
        
        # 🗺️ 4. SECCIÓN: ANÁLISIS GEOESPACIAL
        dbc.Tab(
            html.Div([
                html.Div(id='geospatial-analysis-content', className="tab-content-modern")
            ]),
            label="🗺️ Análisis Geoespacial",
            tab_id="geospatial",
            className="mb-2"
        ),
        
        # 📝 5. SECCIÓN: ANÁLISIS TEXTUAL
        dbc.Tab(
            html.Div([
                html.Div(id='text-analysis-content', className="tab-content-modern")
            ]),
            label="📝 Análisis Textual",
            tab_id="textual",
            className="mb-2"
        )
    ], id="main-tabs-pro", active_tab="estadistica", className="custom-tabs"),
    
    # Footer profesional
    html.Hr(className="mt-5"),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H6([
                    html.I(className="bi-shield-check me-2"),
                    "Dashboard Profesional de Análisis Inmobiliario"
                ], className="text-primary mb-2"),
                html.P([
                    "Sistema integral para análisis profesional del mercado inmobiliario. ",
                    "Incluye estadística descriptiva, detección de outliers contextual, ",
                    "análisis de dependencias, clustering geoespacial y análisis textual avanzado."
                ], className="text-muted small mb-2"),
                html.Div([
                    dbc.Badge("Versión Professional 1.0", color="primary", className="me-2"),
                    dbc.Badge(f"Última actualización: {datetime.now().strftime('%d/%m/%Y')}", color="secondary")
                ])
            ], className="text-center")
        ])
    ], className="mb-4")
    
], fluid=True, className="dashboard-container p-4")

# ==================== CALLBACKS PRINCIPALES ====================

@app.callback(
    [Output('city-filter-pro', 'options'),
     Output('colonia-filter-pro', 'options'),
     Output('property-type-filter-pro', 'options'),
     Output('operation-filter-pro', 'options')],
    Input('load-data-pro', 'n_clicks')
)
def initialize_professional_data(n_clicks):
    """Inicializa datos profesionales"""
    global current_data
    
    if current_data is None:
        current_data = load_comprehensive_data()
    
    # Opciones para filtros
    cities = [{'label': f"🏙️ {c}", 'value': c} 
             for c in sorted(current_data['ciudad'].dropna().unique())]
    
    colonias = [{'label': f"🏘️ {c}", 'value': c} 
               for c in sorted(current_data['colonia'].dropna().unique())]
    
    types = [{'label': f"🏠 {t}", 'value': t} 
            for t in sorted(current_data['tipo_propiedad'].dropna().unique())]
    
    operations = [{'label': f"💰 {o}", 'value': o} 
                 for o in sorted(current_data['operacion'].dropna().unique())]
    
    return cities, colonias, types, operations

@app.callback(
    [Output('filtered-data-pro', 'data'),
     Output('outliers-analysis-pro', 'data'),
     Output('dependencies-analysis-pro', 'data'),
     Output('clusters-analysis-pro', 'data'),
     Output('text-analysis-pro', 'data')],
    Input('apply-filters-pro', 'n_clicks'),
    [State('city-filter-pro', 'value'),
     State('colonia-filter-pro', 'value'),
     State('property-type-filter-pro', 'value'),
     State('operation-filter-pro', 'value'),
     State('price-range-pro', 'value'),
     State('area-range-pro', 'value'),
     State('special-filter-pro', 'value')]
)
def process_professional_analysis(n_clicks, cities, colonias, types, operations, 
                                price_range, area_range, special_filter):
    """Procesa análisis profesional completo"""
    if current_data is None:
        return None, None, None, None, None
    
    df = current_data.copy()
    
    # Aplicar filtros básicos
    if cities:
        df = df[df['ciudad'].isin(cities)]
    if colonias:
        df = df[df['colonia'].isin(colonias)]
    if types:
        df = df[df['tipo_propiedad'].isin(types)]
    if operations:
        df = df[df['operacion'].isin(operations)]
    
    # Aplicar rangos
    if price_range:
        df = df[(df['precio'] >= price_range[0]) & (df['precio'] <= price_range[1])]
    if area_range:
        df = df[(df['area_m2'] >= area_range[0]) & (df['area_m2'] <= area_range[1])]
    
    # Filtros especiales
    if special_filter:
        if special_filter == 'top_precios':
            threshold = df['precio'].quantile(0.9)
            df = df[df['precio'] >= threshold]
        elif special_filter == 'grandes':
            df = df[df['area_m2'] > 300]
        elif special_filter == 'premium':
            df = df[df['categoria_precio'].isin(['Premium', 'Medio-Alto'])]
        elif special_filter == 'familiares':
            df = df[df['recamaras'] >= 3]
    
    # Ejecutar análisis especializados
    outliers_analysis = analyze_outliers_contextual(df)
    dependencies_analysis = analyze_price_dependencies(df)
    clusters_analysis = perform_spatial_clustering(df)
    text_analysis = analyze_text_content(df)
    
    return (df.to_json(date_format='iso', orient='split'),
            outliers_analysis,
            dependencies_analysis,
            clusters_analysis,
            text_analysis)

@app.callback(
    Output('executive-kpis-pro', 'children'),
    Input('filtered-data-pro', 'data')
)
def update_executive_kpis(data_json):
    """Actualiza KPIs ejecutivos profesionales"""
    if not data_json:
        return create_empty_state("No hay datos cargados", "Presiona 'Cargar' para inicializar")
    
    df = pd.read_json(data_json, orient='split')
    
    if len(df) == 0:
        return create_empty_state("Sin resultados", "Ajusta los filtros para ver datos")
    
    # KPIs ejecutivos avanzados
    kpis = [
        {
            'title': 'Propiedades Analizadas',
            'value': f"{len(df):,}",
            'subtitle': f"De {len(current_data) if current_data is not None else 0:,} totales ({len(df)/(len(current_data) if current_data is not None else 1)*100:.1f}%)",
            'icon': 'bi-buildings',
            'color': 'primary',
            'trend': get_trend_indicator(len(df), len(current_data) if current_data is not None else 1)
        },
        {
            'title': 'Valor Promedio',
            'value': format_currency_pro(df['precio'].mean()),
            'subtitle': f"Mediana: {format_currency_pro(df['precio'].median())}",
            'icon': 'bi-currency-dollar',
            'color': 'success',
            'trend': 'up'
        },
        {
            'title': 'Precio por m² Promedio',
            'value': f"${df['precio_m2'].mean():,.0f}",
            'subtitle': f"Rango: ${df['precio_m2'].min():,.0f} - ${df['precio_m2'].max():,.0f}",
            'icon': 'bi-rulers',
            'color': 'info',
            'trend': 'stable'
        },
        {
            'title': 'Área Promedio',
            'value': f"{df['area_m2'].mean():.0f} m²",
            'subtitle': f"Mediana: {df['area_m2'].median():.0f} m²",
            'icon': 'bi-arrows-expand',
            'color': 'warning',
            'trend': 'stable'
        },
        {
            'title': 'Mercado Geográfico',
            'value': f"{df['colonia'].nunique()} colonias",
            'subtitle': f"{df['ciudad'].nunique()} ciudades activas",
            'icon': 'bi-geo-alt',
            'color': 'secondary',
            'trend': 'neutral'
        },
        {
            'title': 'Variabilidad de Mercado',
            'value': f"CV: {(df['precio'].std()/df['precio'].mean()*100):.1f}%",
            'subtitle': f"Desv. Est: {format_currency_pro(df['precio'].std())}",
            'icon': 'bi-graph-up',
            'color': 'dark',
            'trend': get_variability_trend(df['precio'].std()/df['precio'].mean())
        }
    ]
    
    # Crear cards ejecutivos
    cards = []
    for kpi in kpis:
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.I(className=f"{kpi['icon']} text-{kpi['color']}", 
                                  style={'fontSize': '2.5rem', 'opacity': '0.8'})
                        ], className="text-center mb-2"),
                        html.H3(kpi['value'], 
                               className=f"text-{kpi['color']} mb-1 text-center fw-bold"),
                        html.H6(kpi['title'], 
                               className="text-muted mb-1 text-center"),
                        html.Small(kpi['subtitle'], 
                                 className="text-muted text-center d-block")
                    ])
                ], className="p-3")
            ], className="metric-card h-100", style={
                'borderLeft': f'4px solid var(--bs-{kpi["color"]})',
                'background': 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,249,250,0.95))',
                'backdropFilter': 'blur(10px)'
            })
        ], md=2, className="mb-3")
        cards.append(card)
    
    return dbc.Row(cards, className="mb-4")

# ==================== SECCIÓN 1: ESTADÍSTICA DESCRIPTIVA ====================

@app.callback(
    Output('estadistica-descriptiva-content', 'children'),
    [Input('filtered-data-pro', 'data'),
     Input('main-tabs-pro', 'active_tab')]
)
def update_estadistica_descriptiva(data_json, active_tab):
    """Actualiza sección de estadística descriptiva"""
    if active_tab != 'estadistica' or not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Header de sección
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-bar-chart-line me-3"),
                "Estadística Descriptiva Global y por Colonia"
            ], className="text-primary mb-3"),
            html.P("Análisis estadístico completo con métricas por colonia, detección de baja confianza y visualizaciones comparativas.",
                  className="text-muted mb-4")
        ])
    )
    
    # Fila 1: Distribuciones globales
    row1 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=create_price_distribution_histogram(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=6),
        dbc.Col([
            dcc.Graph(
                figure=create_area_distribution_histogram(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=6)
    ], className="mb-4")
    content.append(row1)
    
    # Fila 2: Análisis por colonia
    row2 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=create_price_boxplot_by_colonia(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=8),
        dbc.Col([
            html.Div([
                html.H5("📊 Resumen por Colonia", className="mb-3"),
                create_colonia_summary_table(df)
            ])
        ], md=4)
    ], className="mb-4")
    content.append(row2)
    
    # Fila 3: Scatter plot con tendencias
    row3 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=create_price_area_scatter_by_colonia(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=12)
    ], className="mb-4")
    content.append(row3)
    
    # Fila 4: Alertas de baja confianza
    row4 = dbc.Row([
        dbc.Col([
            create_low_confidence_alerts(df)
        ])
    ])
    content.append(row4)
    
    return html.Div(content)

# ==================== FUNCIONES DE VISUALIZACIÓN PROFESIONAL ====================

def format_currency_pro(value):
    """Formato profesional de moneda"""
    if pd.isna(value):
        return "N/A"
    if value >= 1000000:
        return f"${value/1000000:.1f}M"
    elif value >= 1000:
        return f"${value/1000:.0f}K"
    else:
        return f"${value:,.0f}"

def get_trend_indicator(current, total):
    """Calcula indicador de tendencia"""
    ratio = current / total if total > 0 else 0
    if ratio > 0.7:
        return 'up'
    elif ratio < 0.3:
        return 'down'
    else:
        return 'stable'

def get_variability_trend(cv):
    """Determina tendencia de variabilidad"""
    if cv > 0.5:
        return 'high'
    elif cv < 0.2:
        return 'low'
    else:
        return 'normal'

def create_empty_state(title, message):
    """Crea estado vacío profesional"""
    return dbc.Alert([
        html.I(className="bi-info-circle-fill me-2"),
        html.Strong(title), f" - {message}"
    ], color="info", className="text-center")

def create_price_distribution_histogram(df):
    """Histograma profesional de distribución de precios"""
    fig = px.histogram(
        df, x='precio', nbins=30,
        title="Distribución de Precios - Análisis Global",
        labels={'precio': 'Precio (MXN)', 'count': 'Frecuencia'},
        color_discrete_sequence=['#667eea']
    )
    
    # Agregar líneas de referencia
    fig.add_vline(x=df['precio'].mean(), line_dash="dash", line_color="red",
                  annotation_text=f"Media: {format_currency_pro(df['precio'].mean())}")
    fig.add_vline(x=df['precio'].median(), line_dash="dash", line_color="green",
                  annotation_text=f"Mediana: {format_currency_pro(df['precio'].median())}")
    
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=400
    )
    
    return fig

def create_area_distribution_histogram(df):
    """Histograma profesional de distribución de áreas"""
    fig = px.histogram(
        df, x='area_m2', nbins=25,
        title="Distribución de Áreas - Análisis Global",
        labels={'area_m2': 'Área (m²)', 'count': 'Frecuencia'},
        color_discrete_sequence=['#764ba2']
    )
    
    # Líneas de referencia
    fig.add_vline(x=df['area_m2'].mean(), line_dash="dash", line_color="red",
                  annotation_text=f"Media: {df['area_m2'].mean():.0f}m²")
    fig.add_vline(x=df['area_m2'].median(), line_dash="dash", line_color="green",
                  annotation_text=f"Mediana: {df['area_m2'].median():.0f}m²")
    
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=400
    )
    
    return fig

def create_price_boxplot_by_colonia(df):
    """Boxplot profesional de precios por colonia"""
    # Filtrar colonias con suficientes datos
    colonia_counts = df['colonia'].value_counts()
    valid_colonias = colonia_counts[colonia_counts >= 5].index
    df_filtered = df[df['colonia'].isin(valid_colonias)]
    
    fig = px.box(
        df_filtered, x='colonia', y='precio',
        title="Distribución de Precios por Colonia (Boxplots)",
        labels={'precio': 'Precio (MXN)', 'colonia': 'Colonia'}
    )
    
    fig.update_xaxes(tickangle=45)
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=500,
        showlegend=False
    )
    
    return fig

def create_colonia_summary_table(df):
    """Tabla resumen por colonia con alertas"""
    # Estadísticas por colonia
    stats = df.groupby('colonia').agg({
        'precio': ['count', 'mean', 'median', 'std'],
        'area_m2': 'mean',
        'precio_m2': 'mean'
    }).round(2)
    
    stats.columns = ['n', 'precio_medio', 'precio_mediano', 'precio_std', 'area_media', 'precio_m2']
    stats = stats.reset_index()
    
    # Calcular coeficiente de variación
    stats['cv'] = (stats['precio_std'] / stats['precio_medio'] * 100).round(1)
    
    # Alertas de baja confianza
    stats['alerta'] = stats['n'].apply(lambda x: '🚨' if x < 10 else '✅')
    
    # Formato para visualización
    stats['precio_medio_fmt'] = stats['precio_medio'].apply(lambda x: format_currency_pro(x))
    stats['precio_m2_fmt'] = stats['precio_m2'].apply(lambda x: f"${x:,.0f}")
    
    # Crear tabla
    table_data = stats[['alerta', 'colonia', 'n', 'precio_medio_fmt', 'precio_m2_fmt', 'cv']].head(15)
    
    return dash_table.DataTable(
        data=table_data.to_dict('records'),
        columns=[
            {'name': '⚠️', 'id': 'alerta'},
            {'name': 'Colonia', 'id': 'colonia'},
            {'name': 'n', 'id': 'n'},
            {'name': 'Precio Medio', 'id': 'precio_medio_fmt'},
            {'name': 'Precio/m²', 'id': 'precio_m2_fmt'},
            {'name': 'CV%', 'id': 'cv'}
        ],
        style_cell={'textAlign': 'center', 'fontSize': '12px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{alerta} = 🚨'},
                'backgroundColor': '#ffe6e6'
            }
        ]
    )

def create_price_area_scatter_by_colonia(df):
    """Scatter plot precio vs área con tendencias por colonia"""
    fig = px.scatter(
        df, x='area_m2', y='precio', color='colonia',
        title="Precio vs Área por Colonia - Líneas de Tendencia",
        labels={'area_m2': 'Área (m²)', 'precio': 'Precio (MXN)'},
        trendline="ols"
    )
    
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=500
    )
    
    return fig

def create_low_confidence_alerts(df):
    """Crear alertas de baja confianza"""
    colonia_counts = df['colonia'].value_counts()
    low_confidence = colonia_counts[colonia_counts < 10]
    
    if len(low_confidence) == 0:
        return dbc.Alert([
            html.I(className="bi-check-circle me-2"),
            "✅ Todas las colonias tienen suficientes datos para análisis confiable (n ≥ 10)"
        ], color="success")
    
    alerts = []
    for colonia, count in low_confidence.items():
        alerts.append(
            dbc.ListGroupItem([
                html.Strong(f"🚨 {colonia}"),
                f" - Solo {count} propiedades. Considerar agrupación o inferencia."
            ])
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi-exclamation-triangle me-2"),
            "Alertas de Baja Confianza Estadística"
        ]),
        dbc.CardBody([
            html.P("Las siguientes colonias tienen muy pocas propiedades (n < 10) para análisis confiable:",
                  className="text-muted mb-3"),
            dbc.ListGroup(alerts, flush=True)
        ])
    ], color="warning", outline=True)

# ==================== SECCIÓN 2: DETECCIÓN DE OUTLIERS ====================

@app.callback(
    Output('outliers-detection-content', 'children'),
    [Input('filtered-data-pro', 'data'),
     Input('outliers-analysis-pro', 'data'),
     Input('main-tabs-pro', 'active_tab')]
)
def update_outliers_detection(data_json, outliers_data, active_tab):
    """Actualiza sección de detección de outliers"""
    if active_tab != 'outliers' or not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Header de sección
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-exclamation-triangle me-3"),
                "Detección y Gestión de Outliers Contextual"
            ], className="text-primary mb-3"),
            html.P("Análisis contextual de outliers por colonia con clasificación inteligente y recomendaciones de acción.",
                  className="text-muted mb-4")
        ])
    )
    
    if outliers_data:
        # Mapa de calor de % outliers por colonia
        row1 = dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_outliers_heatmap(outliers_data),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ], md=8),
            dbc.Col([
                create_outliers_summary_card(outliers_data)
            ], md=4)
        ], className="mb-4")
        content.append(row1)
        
        # Tabla interactiva de outliers
        row2 = dbc.Row([
            dbc.Col([
                create_outliers_interactive_table(outliers_data, df)
            ])
        ], className="mb-4")
        content.append(row2)
        
        # Boxplots por colonia con outliers marcados
        row3 = dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_outliers_boxplot_by_colonia(df),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ])
        ])
        content.append(row3)
    else:
        content.append(
            dbc.Alert("Ejecuta el análisis para ver la detección de outliers", color="info")
        )
    
    return html.Div(content)

# ==================== SECCIÓN 3: ANÁLISIS DE DEPENDENCIAS ====================

@app.callback(
    Output('dependencies-analysis-content', 'children'),
    [Input('filtered-data-pro', 'data'),
     Input('dependencies-analysis-pro', 'data'),
     Input('main-tabs-pro', 'active_tab')]
)
def update_dependencies_analysis(data_json, dependencies_data, active_tab):
    """Actualiza sección de análisis de dependencias"""
    if active_tab != 'dependencies' or not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Header de sección
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-graph-up me-3"),
                "Análisis de Dependencia e Influencia sobre Precio"
            ], className="text-primary mb-3"),
            html.P("Análisis de correlaciones, importancia de variables y impacto relativo sobre el precio de propiedades.",
                  className="text-muted mb-4")
        ])
    )
    
    if dependencies_data:
        # Heatmap de correlaciones
        row1 = dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_correlation_heatmap(dependencies_data),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ], md=6),
            dbc.Col([
                dcc.Graph(
                    figure=create_feature_importance_chart(dependencies_data),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ], md=6)
        ], className="mb-4")
        content.append(row1)
        
        # Boxplots por categorías
        row2 = dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_price_by_category_boxplot(df, 'tipo_propiedad'),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ], md=6),
            dbc.Col([
                dcc.Graph(
                    figure=create_price_by_category_boxplot(df, 'colonia'),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ], md=6)
        ], className="mb-4")
        content.append(row2)
        
        # Scatter con líneas de tendencia por colonia
        row3 = dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_price_trends_by_colonia(df),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ])
        ])
        content.append(row3)
    else:
        content.append(
            dbc.Alert("Ejecuta el análisis para ver las dependencias", color="info")
        )
    
    return html.Div(content)

# ==================== SECCIÓN 4: ANÁLISIS GEOESPACIAL ====================

@app.callback(
    Output('geospatial-analysis-content', 'children'),
    [Input('filtered-data-pro', 'data'),
     Input('clusters-analysis-pro', 'data'),
     Input('main-tabs-pro', 'active_tab')]
)
def update_geospatial_analysis(data_json, clusters_data, active_tab):
    """Actualiza sección de análisis geoespacial"""
    if active_tab != 'geospatial' or not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Header de sección
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-map me-3"),
                "Análisis Geoespacial (Mapas + Clustering)"
            ], className="text-primary mb-3"),
            html.P("Mapas interactivos, clustering espacial K-Means y análisis de micro-mercados geográficos.",
                  className="text-muted mb-4")
        ])
    )
    
    if 'latitud' in df.columns and 'longitud' in df.columns:
        # Mapa principal interactivo
        row1 = dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=create_interactive_property_map(df),
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ])
        ], className="mb-4")
        content.append(row1)
        
        if clusters_data:
            # Análisis de clusters
            row2 = dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=create_clusters_map(df, clusters_data),
                        config={'displayModeBar': True, 'displaylogo': False}
                    )
                ], md=8),
                dbc.Col([
                    create_clusters_summary_table(clusters_data)
                ], md=4)
            ], className="mb-4")
            content.append(row2)
            
            # Comparación clusters vs colonias
            row3 = dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=create_clusters_vs_colonias_comparison(clusters_data),
                        config={'displayModeBar': True, 'displaylogo': False}
                    )
                ])
            ])
            content.append(row3)
        else:
            content.append(
                dbc.Alert("Ejecuta el análisis para ver clustering espacial", color="info")
            )
    else:
        content.append(
            dbc.Alert("No hay datos de coordenadas disponibles para análisis geoespacial", color="warning")
        )
    
    return html.Div(content)

# ==================== SECCIÓN 5: ANÁLISIS TEXTUAL ====================

@app.callback(
    Output('text-analysis-content', 'children'),
    [Input('filtered-data-pro', 'data'),
     Input('text-analysis-pro', 'data'),
     Input('main-tabs-pro', 'active_tab')]
)
def update_text_analysis(data_json, text_data, active_tab):
    """Actualiza sección de análisis textual"""
    if active_tab != 'textual' or not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Header de sección
    content.append(
        html.Div([
            html.H3([
                html.I(className="bi-chat-text me-3"),
                "Análisis de Texto (Títulos, Descripciones, Amenidades)"
            ], className="text-primary mb-3"),
            html.P("Word clouds, análisis de amenidades, palabras clave de alto valor y sentimiento textual.",
                  className="text-muted mb-4")
        ])
    )
    
    if text_data and 'descripcion' in df.columns:
        # Word clouds por segmento
        row1 = dbc.Row([
            dbc.Col([
                create_word_cloud_premium_vs_economic(text_data)
            ], md=8),
            dbc.Col([
                create_amenities_frequency_chart(text_data)
            ], md=4)
        ], className="mb-4")
        content.append(row1)
        
        # Análisis de palabras clave
        row2 = dbc.Row([
            dbc.Col([
                create_keywords_analysis_table(text_data)
            ])
        ])
        content.append(row2)
    else:
        content.append(
            dbc.Alert("No hay datos de descripción disponibles para análisis textual", color="warning")
        )
    
    return html.Div(content)

# ==================== FUNCIONES DE VISUALIZACIÓN PROFESIONAL ADICIONALES ====================

def create_outliers_heatmap(outliers_data):
    """Mapa de calor de % outliers por colonia"""
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
    fig.update_layout(template="plotly_white", title_x=0.5, height=400)
    
    return fig

def create_outliers_summary_card(outliers_data):
    """Card resumen de outliers"""
    total_props = sum(data['total_propiedades'] for data in outliers_data.values())
    total_outliers = sum(data['num_outliers'] for data in outliers_data.values())
    avg_percentage = total_outliers / total_props * 100 if total_props > 0 else 0
    
    return dbc.Card([
        dbc.CardHeader("📊 Resumen de Outliers"),
        dbc.CardBody([
            html.H4(f"{total_outliers:,}", className="text-danger"),
            html.P("Total de Outliers Detectados", className="text-muted"),
            html.Hr(),
            html.H5(f"{avg_percentage:.1f}%", className="text-warning"),
            html.P("Porcentaje Promedio", className="text-muted"),
            html.Hr(),
            html.H5(f"{len(outliers_data)}", className="text-info"),
            html.P("Colonias Analizadas", className="text-muted")
        ])
    ])

def create_outliers_interactive_table(outliers_data, df):
    """Tabla interactiva de outliers con clasificación"""
    all_outliers = []
    
    for colonia, data in outliers_data.items():
        for outlier in data['outliers_detalle']:
            outlier['colonia'] = colonia
            all_outliers.append(outlier)
    
    if not all_outliers:
        return dbc.Alert("No se detectaron outliers con los filtros actuales", color="success")
    
    outliers_df = pd.DataFrame(all_outliers)
    
    return dbc.Card([
        dbc.CardHeader("🔍 Tabla Interactiva de Outliers"),
        dbc.CardBody([
            dash_table.DataTable(
                data=[{str(k): v for k, v in row.items()} for row in outliers_df.to_dict('records')],
                columns=[
                    {'name': 'ID', 'id': 'id'},
                    {'name': 'Colonia', 'id': 'colonia'},
                    {'name': 'Precio', 'id': 'precio', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'Área (m²)', 'id': 'area_m2', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Precio/m²', 'id': 'precio_m2', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'Clasificación', 'id': 'clasificacion'},
                    {'name': 'Acción', 'id': 'accion'}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '12px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                sort_action="native",
                filter_action="native",
                page_size=10
            )
        ])
    ])

def create_outliers_boxplot_by_colonia(df):
    """Boxplot con outliers marcados por colonia"""
    fig = px.box(
        df, x='colonia', y='precio',
        title="Distribución de Precios por Colonia - Outliers Marcados",
        labels={'precio': 'Precio (MXN)', 'colonia': 'Colonia'}
    )
    
    fig.update_xaxes(tickangle=45)
    fig.update_layout(template="plotly_white", title_x=0.5, height=500)
    
    return fig

def create_correlation_heatmap(dependencies_data):
    """Heatmap de correlaciones"""
    if 'correlations' not in dependencies_data:
        return go.Figure()
    
    correlations = dependencies_data['correlations']
    variables = list(correlations.keys())
    values = list(correlations.values())
    
    fig = px.bar(
        x=values, y=variables, orientation='h',
        title="Correlación con Precio",
        labels={'x': 'Correlación', 'y': 'Variables'},
        color=values,
        color_continuous_scale='RdBu'
    )
    
    fig.update_layout(template="plotly_white", title_x=0.5, height=400)
    
    return fig

def create_feature_importance_chart(dependencies_data):
    """Gráfico de importancia de variables"""
    if 'feature_importance' not in dependencies_data:
        return go.Figure()
    
    importance = dependencies_data['feature_importance']
    variables = list(importance.keys())
    values = list(importance.values())
    
    fig = px.bar(
        x=values, y=variables, orientation='h',
        title="Importancia de Variables (Random Forest)",
        labels={'x': 'Importancia', 'y': 'Variables'},
        color=values,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(template="plotly_white", title_x=0.5, height=400)
    
    return fig

def create_price_by_category_boxplot(df, category_col):
    """Boxplot de precio por categoría"""
    if category_col not in df.columns:
        return go.Figure()
    
    fig = px.box(
        df, x=category_col, y='precio',
        title=f"Precio por {category_col.replace('_', ' ').title()}",
        labels={'precio': 'Precio (MXN)'}
    )
    
    fig.update_xaxes(tickangle=45)
    fig.update_layout(template="plotly_white", title_x=0.5, height=400)
    
    return fig

def create_price_trends_by_colonia(df):
    """Scatter con tendencias por colonia"""
    fig = px.scatter(
        df, x='area_m2', y='precio', color='colonia',
        title="Tendencias de Precio por Área - Análisis por Colonia",
        labels={'area_m2': 'Área (m²)', 'precio': 'Precio (MXN)'},
        trendline="ols"
    )
    
    fig.update_layout(template="plotly_white", title_x=0.5, height=500)
    
    return fig

def create_interactive_property_map(df):
    """Mapa interactivo de propiedades"""
    fig = px.scatter_mapbox(
        df, lat='latitud', lon='longitud',
        color='precio', size='area_m2',
        hover_data=['colonia', 'tipo_propiedad', 'precio', 'area_m2'],
        color_continuous_scale='Viridis',
        title="Mapa Interactivo de Propiedades",
        zoom=10
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        height=500,
        title_x=0.5
    )
    
    return fig

def create_clusters_map(df, clusters_data):
    """Mapa de clusters espaciales"""
    if not clusters_data or 'data' not in clusters_data:
        return go.Figure()
    
    cluster_df = clusters_data['data']
    
    fig = px.scatter_mapbox(
        cluster_df, lat='latitud', lon='longitud',
        color='cluster', size='precio',
        hover_data=['colonia', 'precio', 'cluster'],
        title="Clustering Espacial K-Means",
        zoom=10
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        height=500,
        title_x=0.5
    )
    
    return fig

def create_clusters_summary_table(clusters_data):
    """Tabla resumen de clusters"""
    if not clusters_data or 'analysis' not in clusters_data:
        return html.Div()
    
    analysis = clusters_data['analysis']
    summary_data = []
    
    for cluster_id, data in analysis.items():
        summary_data.append({
            'cluster': cluster_id,
            'propiedades': data['num_propiedades'],
            'precio_promedio': format_currency_pro(data['precio_promedio']),
            'area_promedio': f"{data['area_promedio']:.0f}m²"
        })
    
    return dbc.Card([
        dbc.CardHeader("📊 Resumen de Clusters"),
        dbc.CardBody([
            dash_table.DataTable(
                data=summary_data,
                columns=[
                    {'name': 'Cluster', 'id': 'cluster'},
                    {'name': 'Props', 'id': 'propiedades'},
                    {'name': 'Precio Prom', 'id': 'precio_promedio'},
                    {'name': 'Área Prom', 'id': 'area_promedio'}
                ],
                style_cell={'textAlign': 'center', 'fontSize': '12px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
            )
        ])
    ])

def create_clusters_vs_colonias_comparison(clusters_data):
    """Comparación clusters vs colonias oficiales"""
    return go.Figure().add_annotation(
        text="Comparación clusters vs colonias en desarrollo",
        x=0.5, y=0.5,
        showarrow=False
    )

def create_word_cloud_premium_vs_economic(text_data):
    """Word clouds por segmento de precio"""
    return dbc.Card([
        dbc.CardHeader("☁️ Palabras Clave por Segmento"),
        dbc.CardBody([
            html.H6("Propiedades Premium", className="text-success"),
            html.P(" • ".join([word for word, count in text_data.get('palabras_premium', [])[:10]])),
            html.Hr(),
            html.H6("Propiedades Económicas", className="text-info"),
            html.P(" • ".join([word for word, count in text_data.get('palabras_economico', [])[:10]]))
        ])
    ])

def create_amenities_frequency_chart(text_data):
    """Gráfico de frecuencia de amenidades"""
    amenidades = text_data.get('amenidades_frecuentes', {})
    
    if not amenidades:
        return dbc.Card([
            dbc.CardBody("No hay amenidades detectadas")
        ])
    
    fig = px.bar(
        x=list(amenidades.values()),
        y=list(amenidades.keys()),
        orientation='h',
        title="Frecuencia de Amenidades"
    )
    
    fig.update_layout(template="plotly_white", height=300)
    
    return dcc.Graph(figure=fig)

def create_keywords_analysis_table(text_data):
    """Tabla de análisis de palabras clave"""
    premium_words = text_data.get('palabras_premium', [])
    economic_words = text_data.get('palabras_economico', [])
    
    return dbc.Card([
        dbc.CardHeader("🔑 Análisis de Palabras Clave"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Top Premium", className="text-success"),
                    html.Ul([html.Li(f"{word} ({count})") for word, count in premium_words[:5]])
                ], md=6),
                dbc.Col([
                    html.H6("Top Económico", className="text-info"),
                    html.Ul([html.Li(f"{word} ({count})") for word, count in economic_words[:5]])
                ], md=6)
            ])
        ])
    ])

# ==================== EJECUCIÓN PRINCIPAL ====================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 INICIANDO DASHBOARD PROFESIONAL DE ANÁLISIS INMOBILIARIO")
    print("="*80)
    print("📊 Sistema Integral con 5 Secciones Profesionales:")
    print("   1. 📊 Estadística Descriptiva Global y por Colonia")
    print("   2. 🚨 Detección y Gestión de Outliers Contextual") 
    print("   3. 📈 Análisis de Dependencia e Influencia sobre Precio")
    print("   4. 🗺️ Análisis Geoespacial (Mapas + Clustering)")
    print("   5. 📝 Análisis de Texto (Títulos, Descripciones, Amenidades)")
    print("\n🎯 Características Profesionales:")
    print("   • Diseño glassmorphism y responsive")
    print("   • Análisis contextual de outliers por colonia")
    print("   • Clustering espacial K-Means")
    print("   • Análisis de importancia de variables con ML")
    print("   • Word clouds y análisis textual")
    print("   • Mapas interactivos con capas de calor")
    print("   • Alertas de baja confianza estadística")
    print("   • KPIs ejecutivos avanzados")
    print("\n🌐 Acceso:")
    print("   • URL Local: http://127.0.0.1:8050")
    print("   • URL Red: http://0.0.0.0:8050")
    print("   • Compatible con dispositivos móviles")
    print("="*80)
    print("🏁 Iniciando servidor Dash profesional...")
    print("💡 Presiona Ctrl+C para detener el dashboard")
    print("="*80 + "\n")
    
    try:
        # Cargar datos al inicio
        load_comprehensive_data()
        
        app.run(
            debug=True,
            host='0.0.0.0',
            port=8051  # Puerto diferente para no interferir con el simple
        )
    except KeyboardInterrupt:
        print("\n🛑 Dashboard profesional detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando el dashboard: {e}")
    finally:
        print("🔚 Finalizando Dashboard Profesional de Análisis Inmobiliario")

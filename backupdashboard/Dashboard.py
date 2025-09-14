"""
Dashboard Inmobiliario Interactivo para Zapopan y Guadalajara
Análisis Estadístico Profesional con Visualizaciones Dinámicas
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# Configuración inicial
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Inmobiliario - Zapopan & Guadalajara"

# Variables globales para almacenar datos
df_main = None
df_stats = None
df_insights = None

# Configuración de colores
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40'
}

# Función para cargar datos
def load_data(filepath):
    """Carga y preprocesa el dataset principal"""
    try:
        df = pd.read_csv(filepath, encoding='latin-1')
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Convertir columnas numéricas
        numeric_cols = ['precio', 'area_m2', 'recamaras', 'banos', 'estacionamientos']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convertir coordenadas
        if 'latitud' in df.columns and 'longitud' in df.columns:
            df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
            df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        
        # Calcular precio por m2
        if 'precio' in df.columns and 'area_m2' in df.columns:
            df['precio_m2'] = df['precio'] / df['area_m2']
        
        return df
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return None

# Función para calcular estadísticas
def calculate_statistics(df, group_by=None):
    """Calcula estadísticas descriptivas para el dataframe"""
    if group_by:
        stats = df.groupby(group_by).agg({
            'precio': ['count', 'mean', 'median', 'std', 'min', 'max'],
            'area_m2': ['mean', 'median', 'std'],
            'precio_m2': ['mean', 'median', 'std']
        }).round(2)
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        return stats.reset_index()
    else:
        return df.describe()

# Función para detectar outliers
def detect_outliers(df, column, method='IQR', group_by=None):
    """Detecta outliers usando IQR o Z-score"""
    outliers = pd.DataFrame()
    
    if group_by:
        for group in df[group_by].unique():
            group_data = df[df[group_by] == group]
            if method == 'IQR':
                Q1 = group_data[column].quantile(0.25)
                Q3 = group_data[column].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                group_outliers = group_data[(group_data[column] < lower) | (group_data[column] > upper)]
            else:  # Z-score
                mean = group_data[column].mean()
                std = group_data[column].std()
                group_outliers = group_data[np.abs((group_data[column] - mean) / std) > 3]
            outliers = pd.concat([outliers, group_outliers])
    else:
        if method == 'IQR':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers = df[(df[column] < lower) | (df[column] > upper)]
        else:  # Z-score
            mean = df[column].mean()
            std = df[column].std()
            outliers = df[np.abs((df[column] - mean) / std) > 3]
    
    return outliers

# Layout del Dashboard
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("🏠 Dashboard Inmobiliario Inteligente", 
                       className="text-center text-white mb-2"),
                html.P("Análisis Estadístico Profesional - Zapopan & Guadalajara",
                      className="text-center text-white-50")
            ], style={
                'background': f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%)',
                'padding': '30px',
                'borderRadius': '15px',
                'marginBottom': '30px'
            })
        ])
    ]),
    
    # Control Panel
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Nivel de Análisis
                dbc.Col([
                    html.Label("📊 Nivel de Análisis", className="fw-bold"),
                    dcc.Dropdown(
                        id='analysis-level',
                        options=[
                            {'label': '🏙️ Ciudad', 'value': 'ciudad'},
                            {'label': '🏘️ Colonia', 'value': 'colonia'},
                            {'label': '🏠 Propiedad Individual', 'value': 'propiedad'}
                        ],
                        value='ciudad',
                        clearable=False
                    )
                ], md=2),
                
                # Ciudad
                dbc.Col([
                    html.Label("🏙️ Ciudad", className="fw-bold"),
                    dcc.Dropdown(
                        id='city-filter',
                        multi=True,
                        placeholder="Seleccionar ciudades..."
                    )
                ], md=2),
                
                # Colonia
                dbc.Col([
                    html.Label("🏘️ Colonia", className="fw-bold"),
                    dcc.Dropdown(
                        id='colonia-filter',
                        multi=True,
                        placeholder="Seleccionar colonias..."
                    )
                ], md=2),
                
                # Tipo de Propiedad
                dbc.Col([
                    html.Label("🏠 Tipo de Propiedad", className="fw-bold"),
                    dcc.Dropdown(
                        id='property-type-filter',
                        multi=True,
                        placeholder="Todos los tipos..."
                    )
                ], md=2),
                
                # Operación
                dbc.Col([
                    html.Label("💰 Operación", className="fw-bold"),
                    dcc.Dropdown(
                        id='operation-filter',
                        options=[
                            {'label': 'Venta', 'value': 'venta'},
                            {'label': 'Renta', 'value': 'renta'},
                            {'label': 'Ambas', 'value': 'todas'}
                        ],
                        value='todas',
                        clearable=False
                    )
                ], md=2),
                
                # Botón de aplicar
                dbc.Col([
                    html.Br(),
                    dbc.Button("🔄 Aplicar Filtros", 
                              id="apply-filters", 
                              color="primary", 
                              className="w-100")
                ], md=2)
            ], className="mb-3"),
            
            # Filtros adicionales
            dbc.Row([
                dbc.Col([
                    html.Label("💵 Rango de Precio", className="fw-bold"),
                    dcc.RangeSlider(
                        id='price-range',
                        min=0,
                        max=50000000,
                        step=100000,
                        marks={i: f'${i/1000000:.0f}M' for i in range(0, 51000000, 10000000)},
                        value=[0, 50000000],
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], md=6),
                
                dbc.Col([
                    html.Label("📏 Rango de Área (m²)", className="fw-bold"),
                    dcc.RangeSlider(
                        id='area-range',
                        min=0,
                        max=1000,
                        step=10,
                        marks={i: f'{i}' for i in range(0, 1001, 200)},
                        value=[0, 1000],
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], md=6)
            ])
        ])
    ], className="mb-4", style={'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    
    # Métricas principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-properties", className="text-primary"),
                    html.P("Total Propiedades", className="text-muted mb-0"),
                    html.Small(id="properties-change", className="text-success")
                ])
            ], className="text-center")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="avg-price", className="text-primary"),
                    html.P("Precio Promedio", className="text-muted mb-0"),
                    html.Small(id="price-change", className="text-success")
                ])
            ], className="text-center")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="avg-area", className="text-primary"),
                    html.P("Área Promedio", className="text-muted mb-0"),
                    html.Small(id="area-change", className="text-success")
                ])
            ], className="text-center")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="avg-price-m2", className="text-primary"),
                    html.P("Precio/m²", className="text-muted mb-0"),
                    html.Small(id="price-m2-change", className="text-success")
                ])
            ], className="text-center")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="outliers-count", className="text-warning"),
                    html.P("Outliers Detectados", className="text-muted mb-0"),
                    html.Small("Requieren atención", className="text-warning")
                ])
            ], className="text-center")
        ], md=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="data-quality", className="text-info"),
                    html.P("Calidad de Datos", className="text-muted mb-0"),
                    html.Small(id="quality-score", className="text-info")
                ])
            ], className="text-center")
        ], md=2)
    ], className="mb-4"),
    
    # Tabs para diferentes vistas
    dbc.Tabs([
        # Tab 1: Análisis Estadístico
        dbc.Tab(label="📊 Análisis Estadístico", tab_id="stats-tab", children=[
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='price-distribution')
                ], md=6),
                dbc.Col([
                    dcc.Graph(id='area-distribution')
                ], md=6)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='boxplot-analysis')
                ], md=12)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("📈 Tabla de Estadísticas Detalladas", className="mt-3 mb-3"),
                    html.Div(id='stats-table')
                ], md=12)
            ])
        ]),
        
        # Tab 2: Análisis Comparativo
        dbc.Tab(label="🔍 Análisis Comparativo", tab_id="comparative-tab", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Seleccionar elementos a comparar:", className="fw-bold mt-3"),
                    dcc.Dropdown(
                        id='comparison-items',
                        multi=True,
                        placeholder="Seleccionar hasta 5 elementos para comparar..."
                    )
                ], md=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='comparison-chart')
                ], md=12)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='radar-comparison')
                ], md=6),
                dbc.Col([
                    dcc.Graph(id='heatmap-comparison')
                ], md=6)
            ], className="mt-3")
        ]),
        
        # Tab 3: Análisis Geoespacial
        dbc.Tab(label="🗺️ Análisis Geoespacial", tab_id="geo-tab", children=[
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='map-view', style={'height': '600px'})
                ], md=12)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='heatmap-geo')
                ], md=6),
                dbc.Col([
                    dcc.Graph(id='cluster-analysis')
                ], md=6)
            ], className="mt-3")
        ]),
        
        # Tab 4: Correlaciones y Tendencias
        dbc.Tab(label="📈 Correlaciones", tab_id="correlations-tab", children=[
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='correlation-matrix')
                ], md=6),
                dbc.Col([
                    dcc.Graph(id='scatter-matrix')
                ], md=6)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='price-vs-area-scatter')
                ], md=12)
            ], className="mt-3")
        ]),
        
        # Tab 5: Outliers y Anomalías
        dbc.Tab(label="⚠️ Outliers", tab_id="outliers-tab", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Método de detección:", className="fw-bold mt-3"),
                    dcc.RadioItems(
                        id='outlier-method',
                        options=[
                            {'label': 'IQR (Cuartiles)', 'value': 'IQR'},
                            {'label': 'Z-Score', 'value': 'zscore'}
                        ],
                        value='IQR',
                        inline=True
                    )
                ], md=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='outliers-chart')
                ], md=6),
                dbc.Col([
                    dcc.Graph(id='outliers-distribution')
                ], md=6)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("🎯 Propiedades Outliers Detectadas", className="mt-3 mb-3"),
                    html.Div(id='outliers-table')
                ], md=12)
            ])
        ]),
        
        # Tab 6: Insights y Recomendaciones
        dbc.Tab(label="💡 Insights", tab_id="insights-tab", children=[
            dbc.Row([
                dbc.Col([
                    html.Div(id='insights-cards', className="mt-3")
                ], md=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H5("📋 Recomendaciones Accionables", className="mt-4 mb-3"),
                    html.Div(id='recommendations-list')
                ], md=12)
            ])
        ])
    ], id="main-tabs", active_tab="stats-tab"),
    
    # Footer
    html.Hr(className="mt-5"),
    dbc.Row([
        dbc.Col([
            html.P("Dashboard Inmobiliario Profesional © 2024", 
                  className="text-center text-muted")
        ])
    ])
    
], fluid=True, style={'backgroundColor': '#f8f9fa'})

# Callbacks principales
@app.callback(
    [Output('city-filter', 'options'),
     Output('colonia-filter', 'options'),
     Output('property-type-filter', 'options')],
    Input('apply-filters', 'n_clicks')
)
def update_filter_options(n_clicks):
    """Actualiza las opciones de los filtros basado en los datos"""
    if df_main is None:
        return [], [], []
    
    cities = [{'label': c, 'value': c} for c in df_main['ciudad'].unique() if pd.notna(c)]
    colonias = [{'label': c, 'value': c} for c in df_main['colonia'].unique() if pd.notna(c)]
    types = [{'label': t, 'value': t} for t in df_main['tipo_propiedad'].unique() if pd.notna(t)]
    
    return cities, colonias, types

@app.callback(
    [Output('total-properties', 'children'),
     Output('avg-price', 'children'),
     Output('avg-area', 'children'),
     Output('avg-price-m2', 'children'),
     Output('outliers-count', 'children'),
     Output('data-quality', 'children')],
    [Input('apply-filters', 'n_clicks'),
     State('city-filter', 'value'),
     State('colonia-filter', 'value'),
     State('property-type-filter', 'value'),
     State('operation-filter', 'value'),
     State('price-range', 'value'),
     State('area-range', 'value')]
)
def update_metrics(n_clicks, cities, colonias, types, operation, price_range, area_range):
    """Actualiza las métricas principales del dashboard"""
    if df_main is None:
        return "---", "---", "---", "---", "---", "---"
    
    # Filtrar datos
    df_filtered = df_main.copy()
    
    if cities:
        df_filtered = df_filtered[df_filtered['ciudad'].isin(cities)]
    if colonias:
        df_filtered = df_filtered[df_filtered['colonia'].isin(colonias)]
    if types:
        df_filtered = df_filtered[df_filtered['tipo_propiedad'].isin(types)]
    if operation != 'todas':
        df_filtered = df_filtered[df_filtered['operacion'] == operation]
    if price_range:
        df_filtered = df_filtered[(df_filtered['precio'] >= price_range[0]) & 
                                  (df_filtered['precio'] <= price_range[1])]
    if area_range:
        df_filtered = df_filtered[(df_filtered['area_m2'] >= area_range[0]) & 
                                  (df_filtered['area_m2'] <= area_range[1])]
    
    # Calcular métricas
    total_props = len(df_filtered)
    avg_price = df_filtered['precio'].mean()
    avg_area = df_filtered['area_m2'].mean()
    avg_price_m2 = df_filtered['precio_m2'].mean()
    
    # Detectar outliers
    outliers = detect_outliers(df_filtered, 'precio')
    outliers_count = len(outliers)
    
    # Calidad de datos (porcentaje de campos completos)
    completeness = df_filtered.notna().mean().mean() * 100
    quality = "Excelente" if completeness > 90 else "Buena" if completeness > 70 else "Regular"
    
    return (
        f"{total_props:,}",
        f"${avg_price/1000000:.2f}M" if not pd.isna(avg_price) else "---",
        f"{avg_area:.0f} m²" if not pd.isna(avg_area) else "---",
        f"${avg_price_m2:,.0f}/m²" if not pd.isna(avg_price_m2) else "---",
        f"{outliers_count}",
        f"{quality} ({completeness:.0f}%)"
    )

# Función principal para cargar datos de ejemplo
def create_sample_data():
    """Crea datos de ejemplo para demostración"""
    np.random.seed(42)
    n_samples = 1000
    
    colonias = ['Providencia', 'Country Club', 'Chapalita', 'Ciudad del Sol', 
                'Zapopan Centro', 'Andares', 'Puerta de Hierro', 'Valle Real',
                'Santa Margarita', 'Jardines del Sol', 'Colinas de San Javier',
                'Bugambilias', 'El Palomar', 'Tesistán', 'La Estancia']
    
    ciudades = ['Zapopan', 'Guadalajara']
    tipos = ['Casa', 'Departamento', 'Oficina', 'Local Comercial', 'Terreno']
    operaciones = ['venta', 'renta']
    
    data = {
        'id': range(1, n_samples + 1),
        'ciudad': np.random.choice(ciudades, n_samples, p=[0.6, 0.4]),
        'colonia': np.random.choice(colonias, n_samples),
        'tipo_propiedad': np.random.choice(tipos, n_samples, p=[0.35, 0.30, 0.15, 0.10, 0.10]),
        'operacion': np.random.choice(operaciones, n_samples, p=[0.7, 0.3]),
        'precio': np.random.lognormal(14.5, 0.8, n_samples),
        'area_m2': np.random.gamma(4, 50, n_samples),
        'recamaras': np.random.poisson(3, n_samples),
        'banos': np.random.poisson(2.5, n_samples),
        'estacionamientos': np.random.poisson(2, n_samples),
        'antiguedad': np.random.exponential(10, n_samples),
        'latitud': 20.6597 + np.random.normal(0, 0.05, n_samples),
        'longitud': -103.3496 + np.random.normal(0, 0.05, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Ajustar precios por colonia (colonias premium más caras)
    premium_colonias = ['Providencia', 'Country Club', 'Andares', 'Puerta de Hierro', 'Valle Real']
    df.loc[df['colonia'].isin(premium_colonias), 'precio'] *= 2.5
    
    # Ajustar precios por tipo
    df.loc[df['tipo_propiedad'] == 'Terreno', 'precio'] *= 0.3
    df.loc[df['tipo_propiedad'] == 'Local Comercial', 'precio'] *= 1.5
    
    # Ajustar precios de renta
    df.loc[df['operacion'] == 'renta', 'precio'] *= 0.005
    
    # Calcular precio por m2
    df['precio_m2'] = df['precio'] / df['area_m2']
    
    # Agregar algunos outliers intencionales
    outlier_indices = np.random.choice(df.index, 20)
    df.loc[outlier_indices, 'precio'] *= np.random.uniform(3, 5, len(outlier_indices))
    
    return df

# Inicializar con datos de ejemplo
if __name__ == '__main__':
    # Cargar datos (cambiar esta ruta a tu archivo CSV real)
    # df_main = load_data('tu_archivo.csv')
    
    # Por ahora usar datos de ejemplo
    df_main = create_sample_data()
    
    print(f"Dashboard iniciado con {len(df_main)} propiedades")
    print(f"Ciudades: {df_main['ciudad'].unique()}")
    print(f"Colonias únicas: {df_main['colonia'].nunique()}")
    
    # Ejecutar servidor
    app.run_server(debug=True, port=8050)
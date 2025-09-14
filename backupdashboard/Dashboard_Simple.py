#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Simplificado de Análisis Inmobiliario
Sistema integrado de visualización y análisis de datos
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# ==================== CONFIGURACIÓN ====================

# Configurar Dash con Bootstrap
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css"
    ],
    suppress_callback_exceptions=True,
    title="Dashboard Análisis Inmobiliario"
)

# ==================== FUNCIONES DE DATOS ====================

def load_csv_data(filename):
    """Carga datos CSV con manejo de errores"""
    try:
        df = pd.read_csv(filename)
        return df
    except Exception as e:
        print(f"Error cargando {filename}: {e}")
        return None

def generate_sample_data():
    """Genera datos de muestra completos para pruebas"""
    np.random.seed(42)
    
    ciudades = ['Guadalajara', 'Zapopan', 'Tlaquepaque', 'Tonalá']
    colonias = [
        'Centro', 'Americana', 'Providencia', 'Chapalita', 'Zona Rosa',
        'Lafayette', 'Vallarta Norte', 'Monraz', 'Country Club', 'Del Valle',
        'Arcos Vallarta', 'Jardines del Bosque', 'Las Águilas', 'Lomas del Valle',
        'Santa Teresita', 'Minerva', 'Reforma', 'Oblatos', 'San Juan de Dios'
    ]
    tipos_propiedad = ['Casa', 'Departamento', 'Condominio', 'Townhouse']
    operaciones = ['Venta', 'Renta']
    
    n = 5000
    data = {
        'id': range(1, n+1),
        'ciudad': np.random.choice(ciudades, n),
        'colonia': np.random.choice(colonias, n),
        'tipo_propiedad': np.random.choice(tipos_propiedad, n),
        'operacion': np.random.choice(operaciones, n),
        'precio': np.random.lognormal(13, 0.8, n).astype(int),
        'area_m2': np.random.normal(150, 50, n).clip(30, 500).astype(int),
        'recamaras': np.random.choice([1, 2, 3, 4, 5, 6], n, p=[0.1, 0.25, 0.35, 0.2, 0.08, 0.02]),
        'banos': np.random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4], n, p=[0.15, 0.1, 0.3, 0.15, 0.2, 0.05, 0.05]),
        'estacionamientos': np.random.choice([0, 1, 2, 3, 4], n, p=[0.1, 0.3, 0.4, 0.15, 0.05]),
        'antiguedad': np.random.randint(0, 30, n)
    }
    
    df = pd.DataFrame(data)
    # Calcular precio por m²
    df['precio_m2'] = (df['precio'] / df['area_m2']).round(2)
    
    return df

def format_currency(value):
    """Formatea valores como moneda"""
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"

# Variable global para datos
current_data = None

# ==================== LAYOUT ====================

app.layout = dbc.Container([
    # Store para datos
    dcc.Store(id='filtered-data'),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1([
                    html.I(className="bi-house-fill me-3"),
                    "Dashboard Análisis Inmobiliario"
                ], className="text-white mb-2"),
                html.P("Sistema integrado de análisis del mercado inmobiliario", 
                      className="text-white-50 mb-0")
            ], className="p-4 text-center", style={
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'borderRadius': '10px'
            })
        ])
    ], className="mb-4"),
    
    # Controles
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🎛️ Controles", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Ciudad"),
                            dcc.Dropdown(
                                id='city-filter',
                                multi=True,
                                placeholder="Seleccionar ciudades..."
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Colonia"),
                            dcc.Dropdown(
                                id='colonia-filter',
                                multi=True,
                                placeholder="Seleccionar colonias..."
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Tipo de Propiedad"),
                            dcc.Dropdown(
                                id='property-type-filter',
                                multi=True,
                                placeholder="Seleccionar tipos..."
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Operación"),
                            dcc.Dropdown(
                                id='operation-filter',
                                multi=True,
                                placeholder="Venta/Renta..."
                            )
                        ], md=3)
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Cargar Datos", id='load-data', color="primary", size="sm"),
                            dbc.Button("🎯 Aplicar Filtros", id='apply-filters', color="success", size="sm", className="ms-2")
                        ])
                    ])
                ])
            ])
        ])
    ], className="mb-4"),
    
    # KPIs
    html.Div(id='kpi-container'),
    
    # Tabs principales
    dbc.Tabs([
        dbc.Tab(
            html.Div(id='overview-content', className="mt-4"),
            label="📊 Vista General",
            tab_id="overview"
        ),
        dbc.Tab(
            html.Div(id='descriptivo-content', className="mt-4"),
            label="📈 Análisis Descriptivo",
            tab_id="descriptivo"
        ),
        dbc.Tab(
            html.Div(id='colonias-content', className="mt-4"),
            label="🏘️ Análisis Colonias",
            tab_id="colonias"
        ),
        dbc.Tab(
            html.Div(id='correlaciones-content', className="mt-4"),
            label="🔗 Correlaciones",
            tab_id="correlaciones"
        ),
        dbc.Tab(
            html.Div(id='insights-content', className="mt-4"),
            label="💡 Insights",
            tab_id="insights"
        )
    ], id="main-tabs", active_tab="overview"),
    
    # Footer
    html.Hr(className="mt-5"),
    html.P("© 2025 Sistema de Análisis Inmobiliario", className="text-center text-muted")
    
], fluid=True)

# ==================== CALLBACKS ====================

@app.callback(
    [Output('city-filter', 'options'),
     Output('colonia-filter', 'options'),
     Output('property-type-filter', 'options'),
     Output('operation-filter', 'options')],
    Input('load-data', 'n_clicks')
)
def initialize_data(n_clicks):
    """Inicializa los datos y opciones de filtros"""
    global current_data
    
    if current_data is None:
        # Intentar cargar datos reales
        try:
            current_data = load_csv_data('../Consolidados/pretratadaCol/Sep25/pretratadaCol_Sep25_01.csv')
            if current_data is None:
                current_data = generate_sample_data()
        except:
            current_data = generate_sample_data()
    
    # Generar opciones
    cities = [{'label': f"🏙️ {c}", 'value': c} 
             for c in sorted(current_data['ciudad'].dropna().unique())] if 'ciudad' in current_data.columns else []
    
    colonias = [{'label': f"🏘️ {c}", 'value': c} 
               for c in sorted(current_data['colonia'].dropna().unique()[:100])] if 'colonia' in current_data.columns else []
    
    types = [{'label': f"🏠 {t}", 'value': t} 
            for t in sorted(current_data['tipo_propiedad'].dropna().unique())] if 'tipo_propiedad' in current_data.columns else []
    
    operations = [{'label': f"💰 {o}", 'value': o} 
                 for o in sorted(current_data['operacion'].dropna().unique())] if 'operacion' in current_data.columns else []
    
    return cities, colonias, types, operations

@app.callback(
    Output('filtered-data', 'data'),
    Input('apply-filters', 'n_clicks'),
    [State('city-filter', 'value'),
     State('colonia-filter', 'value'),
     State('property-type-filter', 'value'),
     State('operation-filter', 'value')]
)
def filter_data(n_clicks, cities, colonias, types, operations):
    """Aplica filtros a los datos"""
    if current_data is None:
        return None
    
    df = current_data.copy()
    
    # Aplicar filtros
    if cities and 'ciudad' in df.columns:
        df = df[df['ciudad'].isin(cities)]
    
    if colonias and 'colonia' in df.columns:
        df = df[df['colonia'].isin(colonias)]
    
    if types and 'tipo_propiedad' in df.columns:
        df = df[df['tipo_propiedad'].isin(types)]
    
    if operations and 'operacion' in df.columns:
        df = df[df['operacion'].isin(operations)]
    
    return df.to_json(date_format='iso', orient='split')

@app.callback(
    Output('kpi-container', 'children'),
    Input('filtered-data', 'data')
)
def update_kpis(data_json):
    """Actualiza los KPIs principales"""
    if not data_json:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    df = pd.read_json(data_json, orient='split')
    
    if len(df) == 0:
        return dbc.Alert("No hay datos con los filtros aplicados", color="info")
    
    # Calcular KPIs
    kpis = [
        {
            'title': 'Total Propiedades',
            'value': f"{len(df):,}",
            'subtitle': f"Analizadas",
            'color': 'primary'
        },
        {
            'title': 'Precio Promedio',
            'value': format_currency(df['precio'].mean()) if 'precio' in df.columns else "N/A",
            'subtitle': f"Mediana: {format_currency(df['precio'].median())}" if 'precio' in df.columns else "",
            'color': 'success'
        },
        {
            'title': 'Área Promedio',
            'value': f"{df['area_m2'].mean():.0f} m²" if 'area_m2' in df.columns else "N/A",
            'subtitle': f"Rango: {df['area_m2'].min():.0f}-{df['area_m2'].max():.0f} m²" if 'area_m2' in df.columns else "",
            'color': 'info'
        },
        {
            'title': 'Precio por m²',
            'value': f"${df['precio_m2'].mean():,.0f}" if 'precio_m2' in df.columns else "N/A",
            'subtitle': f"Mediana: ${df['precio_m2'].median():,.0f}" if 'precio_m2' in df.columns else "",
            'color': 'warning'
        },
        {
            'title': 'Colonias Únicas',
            'value': str(df['colonia'].nunique()) if 'colonia' in df.columns else "N/A",
            'subtitle': f"De {current_data['colonia'].nunique() if current_data is not None and 'colonia' in current_data.columns else 'N/A'} totales",
            'color': 'secondary'
        }
    ]
    
    # Crear cards KPI
    cards = []
    for kpi in kpis:
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(kpi['value'], className=f"text-{kpi['color']} mb-1"),
                    html.H6(kpi['title'], className="text-muted mb-1"),
                    html.Small(kpi['subtitle'], className="text-muted")
                ])
            ], className="h-100 text-center")
        ], md=2)
        cards.append(card)
    
    return dbc.Row(cards, className="mb-4")

@app.callback(
    Output('overview-content', 'children'),
    Input('filtered-data', 'data')
)
def update_overview_tab(data_json):
    """Actualiza el tab de vista general"""
    if not data_json:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Gráficos principales
    row1 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=px.histogram(df, x='precio', nbins=30, title="Distribución de Precios") if 'precio' in df.columns else go.Figure(),
                config={'displayModeBar': True}
            )
        ], md=6),
        dbc.Col([
            dcc.Graph(
                figure=px.bar(
                    df['colonia'].value_counts().head(10).reset_index(),
                    x='count', y='colonia', orientation='h',
                    title="Top 10 Colonias"
                ) if 'colonia' in df.columns else go.Figure(),
                config={'displayModeBar': True}
            )
        ], md=6)
    ])
    content.append(row1)
    
    # Segunda fila
    row2 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=px.pie(
                    df['tipo_propiedad'].value_counts().reset_index(),
                    values='count', names='tipo_propiedad',
                    title="Distribución por Tipo"
                ) if 'tipo_propiedad' in df.columns else go.Figure(),
                config={'displayModeBar': True}
            )
        ], md=6),
        dbc.Col([
            dcc.Graph(
                figure=px.scatter(
                    df, x='area_m2', y='precio',
                    color='tipo_propiedad' if 'tipo_propiedad' in df.columns else None,
                    title="Precio vs Área"
                ) if 'precio' in df.columns and 'area_m2' in df.columns else go.Figure(),
                config={'displayModeBar': True}
            )
        ], md=6)
    ], className="mt-3")
    content.append(row2)
    
    return html.Div(content)

@app.callback(
    Output('descriptivo-content', 'children'),
    Input('filtered-data', 'data')
)
def update_descriptivo_tab(data_json):
    """Actualiza el tab de análisis descriptivo"""
    if not data_json:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    df = pd.read_json(data_json, orient='split')
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        return dbc.Alert("No hay columnas numéricas para analizar", color="info")
    
    # Estadísticas descriptivas
    stats_data = []
    for col in numeric_cols:
        stats_data.append({
            'Variable': col,
            'Media': f"{df[col].mean():.2f}",
            'Mediana': f"{df[col].median():.2f}",
            'Desv. Est.': f"{df[col].std():.2f}",
            'Mín': f"{df[col].min():.2f}",
            'Máx': f"{df[col].max():.2f}"
        })
    
    table = dbc.Table.from_dataframe(
        pd.DataFrame(stats_data),
        striped=True, bordered=True, hover=True
    )
    
    # Distribuciones
    charts = []
    for col in numeric_cols[:4]:  # Limitar a 4 columnas
        fig = px.box(df, y=col, title=f"Distribución de {col}")
        charts.append(
            dbc.Col([
                dcc.Graph(figure=fig, config={'displayModeBar': False})
            ], md=6 if len(numeric_cols) <= 2 else 3)
        )
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader("Estadísticas Descriptivas"),
            dbc.CardBody(table)
        ], className="mb-3"),
        dbc.Card([
            dbc.CardHeader("Distribuciones por Variable"),
            dbc.CardBody([
                dbc.Row(charts)
            ])
        ])
    ])

@app.callback(
    Output('colonias-content', 'children'),
    Input('filtered-data', 'data')
)
def update_colonias_tab(data_json):
    """Actualiza el tab de análisis por colonias"""
    if not data_json:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    df = pd.read_json(data_json, orient='split')
    
    if 'colonia' not in df.columns:
        return dbc.Alert("No hay datos de colonias disponibles", color="info")
    
    # Análisis por colonias
    colonias_stats = df.groupby('colonia').agg({
        'precio': ['count', 'mean', 'median'] if 'precio' in df.columns else ['count'],
        'area_m2': ['mean'] if 'area_m2' in df.columns else []
    }).round(2)
    
    colonias_stats.columns = ['_'.join(col).strip() for col in colonias_stats.columns]
    colonias_stats = colonias_stats.reset_index()
    
    table = dbc.Table.from_dataframe(
        colonias_stats.head(20),
        striped=True, bordered=True, hover=True
    )
    
    return dbc.Card([
        dbc.CardHeader("Análisis por Colonias (Top 20)"),
        dbc.CardBody(table)
    ])

@app.callback(
    Output('correlaciones-content', 'children'),
    Input('filtered-data', 'data')
)
def update_correlaciones_tab(data_json):
    """Actualiza el tab de correlaciones"""
    if not data_json:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    df = pd.read_json(data_json, orient='split')
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return dbc.Alert("Se necesitan al menos 2 variables numéricas para correlaciones", color="info")
    
    corr_matrix = df[numeric_cols].corr()
    
    fig = px.imshow(
        corr_matrix,
        title="Matriz de Correlaciones",
        color_continuous_scale="RdBu",
        aspect="auto"
    )
    
    return dbc.Card([
        dbc.CardHeader("Análisis de Correlaciones"),
        dbc.CardBody([
            dcc.Graph(figure=fig, config={'displayModeBar': True})
        ])
    ])

@app.callback(
    Output('insights-content', 'children'),
    Input('filtered-data', 'data')
)
def update_insights_tab(data_json):
    """Actualiza el tab de insights"""
    if not data_json:
        return dbc.Alert("No hay datos disponibles", color="warning")
    
    df = pd.read_json(data_json, orient='split')
    
    insights = []
    
    # Insight de volumen
    insights.append(f"📊 Se analizaron {len(df):,} propiedades en total.")
    
    # Insight de precio
    if 'precio' in df.columns:
        avg_price = df['precio'].mean()
        insights.append(f"💰 El precio promedio es de {format_currency(avg_price)}.")
    
    # Insight de colonias
    if 'colonia' in df.columns:
        top_colonia = df['colonia'].mode()[0] if len(df['colonia'].mode()) > 0 else "N/A"
        insights.append(f"🏘️ La colonia con más propiedades es {top_colonia}.")
    
    # Insight de tipos
    if 'tipo_propiedad' in df.columns:
        top_type = df['tipo_propiedad'].mode()[0] if len(df['tipo_propiedad'].mode()) > 0 else "N/A"
        insights.append(f"🏠 El tipo de propiedad más común es {top_type}.")
    
    cards = []
    for insight in insights:
        cards.append(
            dbc.Card([
                dbc.CardBody(html.P(insight, className="mb-0"))
            ], className="mb-2")
        )
    
    return dbc.Card([
        dbc.CardHeader("Insights Automáticos"),
        dbc.CardBody(cards)
    ])

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 INICIANDO DASHBOARD SIMPLIFICADO DE ANÁLISIS INMOBILIARIO")
    print("="*80)
    print("📊 Características del Dashboard:")
    print("   • Vista general con gráficos principales")
    print("   • Análisis estadístico descriptivo")
    print("   • Análisis detallado por colonias")
    print("   • Matriz de correlaciones")
    print("   • Insights automáticos")
    print("   • Filtros interactivos")
    print("   • KPIs en tiempo real")
    print("\n🌐 Acceso:")
    print("   • URL Local: http://127.0.0.1:8050")
    print("   • URL Red: http://0.0.0.0:8050")
    print("="*80)
    print("🏁 Iniciando servidor Dash...")
    print("💡 Presiona Ctrl+C para detener el dashboard")
    print("="*80 + "\n")
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=8050
        )
    except KeyboardInterrupt:
        print("\n🛑 Dashboard detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando el dashboard: {e}")
    finally:
        print("🔚 Finalizando Dashboard Simplificado")

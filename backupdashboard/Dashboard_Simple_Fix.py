#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Simple y Robusto para Análisis Inmobiliario
Versión simplificada que garantiza funcionamiento
"""

import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime

# ==================== CONFIGURACIÓN INICIAL ====================

print("🚀 Iniciando Dashboard Simple y Robusto...")

# Inicializar la aplicación Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css"
    ],
    suppress_callback_exceptions=True
)

app.title = "Dashboard Inmobiliario - Análisis Estadístico"

# Variables globales
current_data = pd.DataFrame()
reports_data = {}

# ==================== FUNCIONES DE CARGA DE DATOS ====================

def load_main_data():
    """Carga el dataset principal"""
    global current_data
    
    try:
        # Buscar el archivo de datos
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_path, "Consolidados", "pretratadaCol_num", "Sep25", "pretratadaCol_num_Sep25_01.csv")
        
        if os.path.exists(data_path):
            current_data = pd.read_csv(data_path)
            print(f"✅ Datos cargados: {len(current_data)} registros")
            
            # Limpiar y procesar datos básicos
            current_data.columns = current_data.columns.str.lower().str.strip()
            
            # Convertir columnas numéricas principales
            numeric_cols = ['precio', 'area_m2', 'recamaras', 'banos']
            for col in numeric_cols:
                if col in current_data.columns:
                    current_data[col] = pd.to_numeric(current_data[col], errors='coerce')
            
            # Calcular precio por m2
            if 'precio' in current_data.columns and 'area_m2' in current_data.columns:
                current_data['precio_m2'] = current_data['precio'] / current_data['area_m2']
            
            # Filtrar datos válidos
            current_data = current_data.dropna(subset=['precio'])
            current_data = current_data[current_data['precio'] > 0]
            
            print(f"✅ Datos procesados: {len(current_data)} registros válidos")
            
        else:
            print(f"❌ No se encontró: {data_path}")
            current_data = create_sample_data()
            
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        current_data = create_sample_data()

def create_sample_data():
    """Crear datos de muestra para demostración"""
    print("📊 Creando datos de muestra...")
    
    np.random.seed(42)
    n_records = 1000
    
    colonias = ['Centro', 'Providencia', 'Americana', 'Chapalita', 'Zapopan Centro']
    tipos = ['Casa', 'Departamento', 'Townhouse']
    
    data = {
        'precio': np.random.normal(3500000, 1500000, n_records),
        'area_m2': np.random.normal(120, 40, n_records),
        'recamaras': np.random.choice([1, 2, 3, 4, 5], n_records, p=[0.1, 0.3, 0.4, 0.15, 0.05]),
        'banos': np.random.choice([1, 2, 3, 4], n_records, p=[0.2, 0.5, 0.25, 0.05]),
        'colonia': np.random.choice(colonias, n_records),
        'tipo_propiedad': np.random.choice(tipos, n_records)
    }
    
    df = pd.DataFrame(data)
    df['precio'] = np.abs(df['precio'])
    df['area_m2'] = np.abs(df['area_m2'])
    df['precio_m2'] = df['precio'] / df['area_m2']
    
    return df

# ==================== LAYOUT DEL DASHBOARD ====================

def create_layout():
    """Crear el layout principal del dashboard"""
    
    return dbc.Container([
        
        # Header
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1([
                        html.I(className="bi-house-door me-3"),
                        "Dashboard de Análisis Inmobiliario"
                    ], className="display-4 text-primary mb-0"),
                    html.P("Análisis estadístico robusto de propiedades inmobiliarias", 
                          className="lead text-muted")
                ], className="text-center py-4 mb-4", 
                   style={
                       'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                       'color': 'white',
                       'borderRadius': '15px',
                       'boxShadow': '0 10px 30px rgba(0,0,0,0.3)'
                   })
            ])
        ], className="mb-4"),
        
        # KPIs
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="total-propiedades", children="0", className="text-primary"),
                        html.P("Total Propiedades", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="precio-promedio", children="$0", className="text-success"),
                        html.P("Precio Promedio", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="area-promedio", children="0 m²", className="text-info"),
                        html.P("Área Promedio", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="precio-m2-promedio", children="$0/m²", className="text-warning"),
                        html.P("Precio/m² Promedio", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3)
        ], className="mb-4"),
        
        # Filtros
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔧 Filtros de Análisis"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Rango de Precio:", className="fw-bold"),
                                dcc.RangeSlider(
                                    id='precio-slider',
                                    min=0,
                                    max=10000000,
                                    step=100000,
                                    value=[0, 10000000],
                                    marks={
                                        0: '$0',
                                        2500000: '$2.5M',
                                        5000000: '$5M',
                                        7500000: '$7.5M',
                                        10000000: '$10M'
                                    },
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label("Colonia:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='colonia-dropdown',
                                    options=[],
                                    value=None,
                                    placeholder="Todas las colonias",
                                    multi=True
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Tipo de Propiedad:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='tipo-dropdown',
                                    options=[],
                                    value=None,
                                    placeholder="Todos los tipos",
                                    multi=True
                                )
                            ], md=3)
                        ])
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Gráficos principales
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Distribución de Precios"),
                    dbc.CardBody([
                        dcc.Graph(id='precio-histogram')
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Precio vs Área"),
                    dbc.CardBody([
                        dcc.Graph(id='precio-area-scatter')
                    ])
                ])
            ], md=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏘️ Precios por Colonia"),
                    dbc.CardBody([
                        dcc.Graph(id='precios-colonia-box')
                    ])
                ])
            ], md=12)
        ], className="mb-4"),
        
        # Tabla de datos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Tabla de Propiedades"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='propiedades-table',
                            columns=[],
                            data=[],
                            page_size=10,
                            sort_action="native",
                            filter_action="native",
                            style_cell={'textAlign': 'center'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
                        )
                    ])
                ])
            ])
        ])
        
    ], fluid=True, className="p-4")

# Asignar layout
app.layout = create_layout()

# ==================== CALLBACKS ====================

@app.callback(
    [Output('colonia-dropdown', 'options'),
     Output('tipo-dropdown', 'options'),
     Output('precio-slider', 'min'),
     Output('precio-slider', 'max'),
     Output('precio-slider', 'value')],
    [Input('precio-slider', 'id')]
)
def update_filter_options(_):
    """Actualizar opciones de filtros"""
    if current_data.empty:
        return [], [], 0, 10000000, [0, 10000000]
    
    # Opciones de colonia
    colonias = [{'label': col, 'value': col} for col in sorted(current_data['colonia'].unique()) if pd.notna(col)]
    
    # Opciones de tipo
    tipos = []
    if 'tipo_propiedad' in current_data.columns:
        tipos = [{'label': tipo, 'value': tipo} for tipo in sorted(current_data['tipo_propiedad'].unique()) if pd.notna(tipo)]
    
    # Rango de precios
    min_precio = int(current_data['precio'].min())
    max_precio = int(current_data['precio'].max())
    
    return colonias, tipos, min_precio, max_precio, [min_precio, max_precio]

@app.callback(
    [Output('total-propiedades', 'children'),
     Output('precio-promedio', 'children'),
     Output('area-promedio', 'children'),
     Output('precio-m2-promedio', 'children')],
    [Input('precio-slider', 'value'),
     Input('colonia-dropdown', 'value'),
     Input('tipo-dropdown', 'value')]
)
def update_kpis(precio_range, colonias, tipos):
    """Actualizar KPIs"""
    if current_data.empty:
        return "0", "$0", "0 m²", "$0/m²"
    
    # Filtrar datos
    filtered_data = current_data.copy()
    
    if precio_range:
        filtered_data = filtered_data[
            (filtered_data['precio'] >= precio_range[0]) & 
            (filtered_data['precio'] <= precio_range[1])
        ]
    
    if colonias:
        filtered_data = filtered_data[filtered_data['colonia'].isin(colonias)]
    
    if tipos and 'tipo_propiedad' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['tipo_propiedad'].isin(tipos)]
    
    if filtered_data.empty:
        return "0", "$0", "0 m²", "$0/m²"
    
    # Calcular KPIs
    total = len(filtered_data)
    precio_prom = filtered_data['precio'].mean()
    area_prom = filtered_data['area_m2'].mean() if 'area_m2' in filtered_data.columns else 0
    precio_m2_prom = filtered_data['precio_m2'].mean() if 'precio_m2' in filtered_data.columns else 0
    
    return (
        f"{total:,}",
        f"${precio_prom:,.0f}",
        f"{area_prom:.0f} m²",
        f"${precio_m2_prom:,.0f}/m²"
    )

@app.callback(
    Output('precio-histogram', 'figure'),
    [Input('precio-slider', 'value'),
     Input('colonia-dropdown', 'value'),
     Input('tipo-dropdown', 'value')]
)
def update_precio_histogram(precio_range, colonias, tipos):
    """Actualizar histograma de precios"""
    filtered_data = filter_data(precio_range, colonias, tipos)
    
    if filtered_data.empty:
        return go.Figure().add_annotation(text="No hay datos disponibles", x=0.5, y=0.5, showarrow=False)
    
    fig = px.histogram(
        filtered_data, 
        x='precio',
        title="Distribución de Precios",
        labels={'precio': 'Precio (MXN)', 'count': 'Cantidad'},
        nbins=30
    )
    
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('precio-area-scatter', 'figure'),
    [Input('precio-slider', 'value'),
     Input('colonia-dropdown', 'value'),
     Input('tipo-dropdown', 'value')]
)
def update_precio_area_scatter(precio_range, colonias, tipos):
    """Actualizar scatter precio vs área"""
    filtered_data = filter_data(precio_range, colonias, tipos)
    
    if filtered_data.empty or 'area_m2' not in filtered_data.columns:
        return go.Figure().add_annotation(text="No hay datos disponibles", x=0.5, y=0.5, showarrow=False)
    
    color_col = 'colonia' if 'colonia' in filtered_data.columns else None
    
    fig = px.scatter(
        filtered_data,
        x='area_m2',
        y='precio',
        color=color_col,
        title="Precio vs Área",
        labels={'area_m2': 'Área (m²)', 'precio': 'Precio (MXN)'},
        trendline="ols"
    )
    
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('precios-colonia-box', 'figure'),
    [Input('precio-slider', 'value'),
     Input('colonia-dropdown', 'value'),
     Input('tipo-dropdown', 'value')]
)
def update_precios_colonia_box(precio_range, colonias, tipos):
    """Actualizar boxplot de precios por colonia"""
    filtered_data = filter_data(precio_range, colonias, tipos)
    
    if filtered_data.empty:
        return go.Figure().add_annotation(text="No hay datos disponibles", x=0.5, y=0.5, showarrow=False)
    
    fig = px.box(
        filtered_data,
        x='colonia',
        y='precio',
        title="Distribución de Precios por Colonia",
        labels={'colonia': 'Colonia', 'precio': 'Precio (MXN)'}
    )
    
    fig.update_xaxes(tickangle=45)
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('propiedades-table', 'data'),
    Output('propiedades-table', 'columns'),
    [Input('precio-slider', 'value'),
     Input('colonia-dropdown', 'value'),
     Input('tipo-dropdown', 'value')]
)
def update_table(precio_range, colonias, tipos):
    """Actualizar tabla de propiedades"""
    filtered_data = filter_data(precio_range, colonias, tipos)
    
    if filtered_data.empty:
        return [], []
    
    # Seleccionar columnas para mostrar
    display_cols = ['precio', 'area_m2', 'precio_m2', 'colonia', 'recamaras', 'banos']
    available_cols = [col for col in display_cols if col in filtered_data.columns]
    
    # Preparar datos para tabla
    table_data = filtered_data[available_cols].head(100).copy()
    
    # Formatear números
    for col in ['precio', 'precio_m2']:
        if col in table_data.columns:
            table_data[col] = table_data[col].round(0).astype(int)
    
    if 'area_m2' in table_data.columns:
        table_data['area_m2'] = table_data['area_m2'].round(1)
    
    # Definir columnas
    columns = []
    col_names = {
        'precio': 'Precio',
        'area_m2': 'Área (m²)',
        'precio_m2': 'Precio/m²',
        'colonia': 'Colonia',
        'recamaras': 'Recámaras',
        'banos': 'Baños'
    }
    
    for col in available_cols:
        col_config = {'name': col_names.get(col, col), 'id': col}
        if col in ['precio', 'precio_m2']:
            col_config['type'] = 'numeric'
            col_config['format'] = dict(specifier=',.0f')
        columns.append(col_config)
    
    return table_data.to_dict('records'), columns

def filter_data(precio_range, colonias, tipos):
    """Función auxiliar para filtrar datos"""
    if current_data.empty:
        return pd.DataFrame()
    
    filtered_data = current_data.copy()
    
    if precio_range:
        filtered_data = filtered_data[
            (filtered_data['precio'] >= precio_range[0]) & 
            (filtered_data['precio'] <= precio_range[1])
        ]
    
    if colonias:
        filtered_data = filtered_data[filtered_data['colonia'].isin(colonias)]
    
    if tipos and 'tipo_propiedad' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['tipo_propiedad'].isin(tipos)]
    
    return filtered_data

# ==================== EJECUCIÓN PRINCIPAL ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DASHBOARD INMOBILIARIO - VERSIÓN ROBUSTA")
    print("="*60)
    print("📊 Funcionalidades:")
    print("   • Análisis estadístico de propiedades")
    print("   • KPIs ejecutivos en tiempo real")
    print("   • Filtros dinámicos interactivos")
    print("   • Visualizaciones profesionales")
    print("   • Tabla de datos filtrable")
    print("\n🌐 Acceso:")
    print("   • URL: http://127.0.0.1:8052")
    print("   • Compatible con dispositivos móviles")
    print("="*60)
    
    try:
        # Cargar datos
        load_main_data()
        
        print("\n🏁 Iniciando servidor...")
        print("💡 Presiona Ctrl+C para detener")
        print("="*60 + "\n")
        
        app.run(
            debug=True,
            host='127.0.0.1',
            port=8052
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("🔄 Intentando con datos de muestra...")
        current_data = create_sample_data()
        app.run(debug=True, host='127.0.0.1', port=8052)
    finally:
        print("🔚 Finalizando Dashboard")

"""
Dashboard Inmobiliario Completo - Sistema de Análisis Integral
Incluye todos los estudios realizados: Descriptivo, Normalización, Outliers, Colonias
Visualizaciones interactivas nivel Ciudad, Colonia y Propiedad individual
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import os
import glob
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURACIÓN INICIAL ====================

app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
                suppress_callback_exceptions=True)

app.title = "Dashboard Inmobiliario - Análisis Profesional Integral"

# Configuración de colores avanzada
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'gradient': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#43e97b', '#38f9d7'],
    'categorical': px.colors.qualitative.Set3,
    'sequential': px.colors.sequential.Viridis,
    'diverging': px.colors.diverging.RdBu,
    'geo': px.colors.sequential.Plasma
}

# Variables globales para datos
current_data = None
stats_data = None
reports_data = {}

# ==================== FUNCIONES DE CARGA DE DATOS ====================

def load_all_analysis_data():
    """Carga todos los archivos de análisis disponibles"""
    global stats_data, reports_data
    
    analysis_files = {
        'descriptivo': 'Estadisticas/Fase1/1.Descriptivo/sep25/num_F1Desc_Sep25_01.csv',
        'normalizacion': 'Estadisticas/Fase1/1.Normalizacion/sep25/num_F1Norm_Sep25_01.csv',
        'outliers': 'Estadisticas/Fase1/1.Outliers/sep25/num_F1Outl_Sep25_01.csv',
        'colonias_completo': 'Estadisticas/Reportes/Colonias/Sep25/ColoniasRep_Sep25_01_completo.csv',
        'colonias_top_precio': 'Estadisticas/Reportes/Colonias/Sep25/ColoniasRep_Sep25_01_top_precio.csv',
        'colonias_gdl': 'Estadisticas/Reportes/Colonias/Sep25/ColoniasRep_Sep25_01_gdl.csv',
        'colonias_zap': 'Estadisticas/Reportes/Colonias/Sep25/ColoniasRep_Sep25_01_zap.csv'
    }
    
    # Cargar archivos de reportes
    reports_files = {
        'descriptivo_insights': 'Estadisticas/Reportes/1. Descriptivo/Sep25/F1_DescriptivoRep_Sep25_01_insights.csv',
        'descriptivo_recommendations': 'Estadisticas/Reportes/1. Descriptivo/Sep25/F1_DescriptivoRep_Sep25_01_recommendations.csv',
        'descriptivo_alerts': 'Estadisticas/Reportes/1. Descriptivo/Sep25/F1_DescriptivoRep_Sep25_01_alerts.csv',
        'normalizacion_insights': 'Estadisticas/Reportes/1. Normalizacion/Sep25/F1_NormRep_Sep25_01_insights.csv',
        'normalizacion_recommendations': 'Estadisticas/Reportes/1. Normalizacion/Sep25/F1_NormRep_Sep25_01_recommendations.csv',
        'outliers_insights': 'Estadisticas/Reportes/1. Outliers/Sep25/F1_OutliersRep_Sep25_01_insights.csv',
        'outliers_recommendations': 'Estadisticas/Reportes/1. Outliers/Sep25/F1_OutliersRep_Sep25_01_recommendations.csv'
    }
    
    # Cargar datos principales
    try:
        # Cargar datos consolidados
        if os.path.exists('Consolidados/pretratadaCol/Sep25/pretratadaCol_Sep25_01.csv'):
            current_data = pd.read_csv('Consolidados/pretratadaCol/Sep25/pretratadaCol_Sep25_01.csv')
            print(f"✅ Datos principales cargados: {len(current_data)} registros")
        
        # Cargar análisis estadísticos
        for key, filepath in analysis_files.items():
            if os.path.exists(filepath):
                reports_data[key] = pd.read_csv(filepath)
                print(f"✅ {key} cargado: {len(reports_data[key])} registros")
        
        # Cargar reportes de insights
        for key, filepath in reports_files.items():
            if os.path.exists(filepath):
                reports_data[key] = pd.read_csv(filepath)
                print(f"✅ {key} cargado")
                
    except Exception as e:
        print(f"⚠️ Error cargando archivos: {e}")

def load_csv_data(filename):
    """Carga datos CSV con manejo de errores"""
    try:
        df = pd.read_csv(filename)
        return df
    except Exception as e:
        print(f"Error cargando {filename}: {e}")
        return None

def generate_comprehensive_sample_data():
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

def calculate_trend(df, column):
    """Calcula tendencia simple basada en quartiles"""
    if column == 'count':
        return 'up' if len(df) > 1000 else 'down' if len(df) < 500 else 'stable'
    
    if column not in df.columns or df[column].isna().all():
        return 'neutral'
    
    # Usar quartiles para determinar tendencia
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    median = df[column].median()
    
    if median > q3:
        return 'up'
    elif median < q1:
        return 'down'
    else:
        return 'stable'

def create_empty_kpis():
    """Crea KPIs vacíos cuando no hay datos"""
    return dbc.Alert("No hay datos disponibles para mostrar KPIs", color="warning")

def create_no_data_message():
    """Mensaje cuando no hay datos"""
    return dbc.Alert([
        html.I(className="bi-exclamation-triangle me-2"),
        "No hay datos disponibles con los filtros aplicados. Intenta ajustar los criterios de búsqueda."
    ], color="info", className="text-center")

def create_executive_summary(df):
    """Crea resumen ejecutivo"""
    if len(df) == 0:
        return create_no_data_message()
    
    summary_stats = {
        'Total Propiedades': len(df),
        'Precio Promedio': df['precio'].mean() if 'precio' in df.columns else 0,
        'Área Promedio': df['area_m2'].mean() if 'area_m2' in df.columns else 0,
        'Colonias Únicas': df['colonia'].nunique() if 'colonia' in df.columns else 0
    }
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi-clipboard-data me-2"),
            html.H5("Resumen Ejecutivo", className="mb-0")
        ]),
        dbc.CardBody([
            html.P(f"Análisis de {summary_stats['Total Propiedades']:,} propiedades con precio promedio de {format_currency(summary_stats['Precio Promedio'])} y área promedio de {summary_stats['Área Promedio']:.0f} m²."),
            html.P(f"Se identificaron {summary_stats['Colonias Únicas']} colonias diferentes en el conjunto de datos analizado.")
        ])
    ], className="mb-3")

def create_main_distribution(df, variable):
    """Crea gráfico de distribución principal"""
    if variable not in df.columns:
        variable = 'precio'
    
    fig = px.histogram(df, x=variable, nbins=30, 
                      title=f"Distribución de {variable.title()}")
    fig.update_layout(template="plotly_white")
    return fig

def create_top_colonias_chart(df):
    """Crea gráfico de top colonias"""
    if 'colonia' not in df.columns:
        return go.Figure().add_annotation(text="Datos de colonia no disponibles")
    
    top_colonias = df['colonia'].value_counts().head(10)
    
    fig = px.bar(x=top_colonias.values, y=top_colonias.index, 
                orientation='h', title="Top 10 Colonias por Propiedades")
    fig.update_layout(template="plotly_white", yaxis={'categoryorder':'total ascending'})
    return fig

def create_type_distribution_pie(df):
    """Crea gráfico circular de tipos de propiedad"""
    if 'tipo_propiedad' not in df.columns:
        return go.Figure().add_annotation(text="Datos de tipo de propiedad no disponibles")
    
    type_counts = df['tipo_propiedad'].value_counts()
    
    fig = px.pie(values=type_counts.values, names=type_counts.index,
                title="Distribución por Tipo de Propiedad")
    fig.update_layout(template="plotly_white")
    return fig

def create_price_vs_area_scatter(df):
    """Crea gráfico de dispersión precio vs área"""
    if 'precio' not in df.columns or 'area_m2' not in df.columns:
        return go.Figure().add_annotation(text="Datos de precio o área no disponibles")
    
    fig = px.scatter(df, x='area_m2', y='precio', 
                    color='tipo_propiedad' if 'tipo_propiedad' in df.columns else None,
                    title="Precio vs Área")
    fig.update_layout(template="plotly_white")
    return fig

def create_descriptive_stats_section(df):
    """Crea sección de estadísticas descriptivas"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        return create_no_data_message()
    
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
        striped=True, bordered=True, hover=True,
        className="mt-3"
    )
    
    return dbc.Card([
        dbc.CardHeader("Estadísticas Descriptivas"),
        dbc.CardBody(table)
    ], className="mb-3")

def create_distributions_section(df):
    """Crea sección de distribuciones"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns[:4]  # Limitar a 4 columnas
    
    if len(numeric_cols) == 0:
        return create_no_data_message()
    
    charts = []
    for col in numeric_cols:
        fig = px.box(df, y=col, title=f"Distribución de {col}")
        fig.update_layout(template="plotly_white", height=300)
        
        charts.append(
            dbc.Col([
                dcc.Graph(figure=fig, config={'displayModeBar': False})
            ], md=6 if len(numeric_cols) <= 2 else 3)
        )
    
    return dbc.Card([
        dbc.CardHeader("Distribuciones por Variable"),
        dbc.CardBody([
            dbc.Row(charts)
        ])
    ], className="mb-3")

def create_insights_from_reports(insights_data, report_type):
    """Crea insights desde reportes existentes"""
    return dbc.Alert(f"Insights de {report_type} estarán disponibles cuando se carguen los reportes.", 
                    color="info")

def create_normalization_analysis(df):
    """Crea análisis de normalización"""
    return dbc.Card([
        dbc.CardHeader("Análisis de Normalización"),
        dbc.CardBody([
            html.P("Análisis de normalización en desarrollo. Se mostrarán transformaciones aplicadas y su impacto."),
            # Aquí se puede agregar análisis específico de normalización
        ])
    ], className="mb-3")

def create_before_after_comparison(df, norm_data):
    """Crea comparación antes/después de normalización"""
    return dbc.Alert("Comparación antes/después disponible cuando se carguen datos de normalización.", 
                    color="info")

def create_outliers_analysis(df):
    """Crea análisis de outliers"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        return create_no_data_message()
    
    outliers_summary = []
    for col in numeric_cols:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower) | (df[col] > upper)]
            outliers_summary.append({
                'Variable': col,
                'Total Outliers': len(outliers),
                'Porcentaje': f"{len(outliers)/len(df)*100:.1f}%",
                'Límite Inferior': f"{lower:.2f}",
                'Límite Superior': f"{upper:.2f}"
            })
    
    table = dbc.Table.from_dataframe(
        pd.DataFrame(outliers_summary),
        striped=True, bordered=True, hover=True
    )
    
    return dbc.Card([
        dbc.CardHeader("Análisis de Outliers"),
        dbc.CardBody(table)
    ], className="mb-3")

def create_outliers_detection_section(df):
    """Crea sección de detección de outliers"""
    return dbc.Alert("Detección avanzada de outliers en desarrollo.", color="info")

def create_colonias_analysis(df):
    """Crea análisis por colonias"""
    if 'colonia' not in df.columns:
        return create_no_data_message()
    
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
    ], className="mb-3")

def create_colonias_rankings(df):
    """Crea rankings de colonias"""
    return dbc.Alert("Rankings detallados de colonias en desarrollo.", color="info")

def create_geo_analysis(df):
    """Crea análisis geoespacial"""
    return dbc.Card([
        dbc.CardHeader("Análisis Geoespacial"),
        dbc.CardBody([
            html.P("Mapas interactivos estarán disponibles cuando se integren datos geoespaciales."),
            html.P("Se mostrarán: mapas de calor, distribución por zonas, y análisis de proximidad.")
        ])
    ], className="mb-3")

def create_correlations_analysis(df):
    """Crea análisis de correlaciones"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return create_no_data_message()
    
    corr_matrix = df[numeric_cols].corr()
    
    fig = px.imshow(corr_matrix, 
                   title="Matriz de Correlaciones",
                   color_continuous_scale="RdBu",
                   aspect="auto")
    fig.update_layout(template="plotly_white")
    
    return dbc.Card([
        dbc.CardHeader("Análisis de Correlaciones"),
        dbc.CardBody([
            dcc.Graph(figure=fig, config={'displayModeBar': True})
        ])
    ], className="mb-3")

def create_comparison_selector(df, mode):
    """Crea selector para comparaciones"""
    return dbc.Alert(f"Selector de comparación para modo {mode} en desarrollo.", color="info")

def create_comparison_charts(df, mode):
    """Crea gráficos comparativos"""
    return dbc.Alert(f"Gráficos comparativos para modo {mode} en desarrollo.", color="info")

def create_automatic_insights(df):
    """Crea insights automáticos"""
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
    ], className="mb-3")

def create_recommendations_section():
    """Crea sección de recomendaciones"""
    return dbc.Card([
        dbc.CardHeader("Recomendaciones"),
        dbc.CardBody([
            html.P("Las recomendaciones se generarán automáticamente basadas en:"),
            html.Ul([
                html.Li("Análisis de mercado"),
                html.Li("Tendencias de precios"),
                html.Li("Oportunidades de inversión"),
                html.Li("Alertas de calidad de datos")
            ])
        ])
    ], className="mb-3")

# ==================== INICIALIZACIÓN DE DATOS ====================

# Cargar datos de reportes si están disponibles
reports_data = {}

def load_all_reports():
    """Carga todos los reportes disponibles"""
    global reports_data
    
    # Directorios de reportes
    base_path = "Estadisticas/Reportes"
    
    report_types = {
        'descriptivo_insights': f"{base_path}/1. Descriptivo/Sep25/F1_DescriptivoRep_Sep25_01_insights.csv",
        'normalizacion': f"{base_path}/1. Normalizacion/Sep25/F1_NormRep_Sep25_01_insights.csv",
        'outliers': f"{base_path}/1. Outliers/Sep25/F1_OutliersRep_Sep25_01_insights.csv",
        'colonias_completo': f"{base_path}/Colonias/Sep25/ColoniasRep_Sep25_01_completo.csv"
    }
    
    for report_name, file_path in report_types.items():
        try:
            if os.path.exists(file_path):
                reports_data[report_name] = pd.read_csv(file_path)
                print(f"✅ Cargado: {report_name}")
            else:
                print(f"❌ No encontrado: {file_path}")
        except Exception as e:
            print(f"❌ Error cargando {report_name}: {e}")

# Cargar reportes al inicializar
load_all_reports()

# ==================== EJECUCIÓN PRINCIPAL ====================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 INICIANDO DASHBOARD COMPLETO DE ANÁLISIS INMOBILIARIO")
    print("="*80)
    print("📊 Características del Dashboard:")
    print("   • Análisis multidimensional (Ciudad, Colonia, Propiedad)")
    print("   • 9 módulos de análisis especializados")
    print("   • Filtros avanzados e interactivos")
    print("   • Visualizaciones dinámicas con Plotly")
    print("   • KPIs en tiempo real")
    print("   • Integración con todos los estudios previos")
    print("   • Diseño responsivo con Bootstrap")
    print("   • Exportación de resultados")
    print("\n📋 Módulos Disponibles:")
    print("   1. 🏠 Overview - Vista general y resúmenes")
    print("   2. 📈 Descriptivo - Estadísticas y distribuciones")
    print("   3. 🔄 Normalización - Análisis de transformaciones")
    print("   4. ⚠️  Outliers - Detección de valores atípicos")
    print("   5. 🏘️  Colonias - Análisis territorial detallado")
    print("   6. ⚖️  Comparativo - Comparaciones multicritério")
    print("   7. 🗺️  Geoespacial - Mapas y análisis territorial")
    print("   8. 🔗 Correlaciones - Relaciones entre variables")
    print("   9. 💡 Insights - Recomendaciones inteligentes")
    print("\n🔧 Controles Avanzados:")
    print("   • Filtros por Ciudad, Colonia, Tipo, Operación")
    print("   • Rangos dinámicos de Precio, Área, Recámaras")
    print("   • Filtros especiales (Top precios, Propiedades grandes, etc.)")
    print("   • Modo de análisis configurable")
    print("   • Variable principal seleccionable")
    print("\n🎯 Datos Integrados:")
    print(f"   • Reportes de análisis descriptivo")
    print(f"   • Reportes de normalización")
    print(f"   • Reportes de detección de outliers")
    print(f"   • Análisis completo por colonias")
    print(f"   • {len(reports_data)} módulos de reportes cargados")
    print("\n🌐 Acceso:")
    print("   • URL Local: http://127.0.0.1:8050")
    print("   • URL Red: http://0.0.0.0:8050")
    print("   • Compatible con dispositivos móviles")
    print("="*80)
    print("🏁 Iniciando servidor Dash...")
    print("💡 Presiona Ctrl+C para detener el dashboard")
    print("="*80 + "\n")
    
    try:
        # Configuración del servidor
        app.run(
            debug=True,
            host='0.0.0.0',  # Permite acceso desde la red
            port=8050,
            dev_tools_ui=True,
            dev_tools_props_check=True,
            dev_tools_serve_dev_bundles=True
        )
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("🛑 Dashboard detenido por el usuario")
        print("="*80)
    except Exception as e:
        print(f"\n❌ Error ejecutando el dashboard: {e}")
        print("="*80)
    finally:
        print("🔚 Finalizando Dashboard de Análisis Inmobiliario")
        print("="*80)
def load_and_preprocess_csv(filepath):
    """Carga y preprocesa archivo CSV"""
    try:
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except:
                continue
        
        if df is None:
            raise ValueError("No se pudo cargar el archivo")
        
        # Preprocesamiento
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        
        # Convertir columnas numéricas
        numeric_cols = ['precio', 'area_m2', 'recamaras', 'banos', 'estacionamientos', 
                       'banos_icon', 'estacionamientos_icon', 'recamaras_icon', 
                       'tiempo_publicacion', 'latitud', 'longitud']
        
        for col in numeric_cols:
            if col in df.columns:
                # Manejar 'Desconocido' convirtiéndolo a NaN
                df[col] = df[col].replace('Desconocido', np.nan)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calcular precio_m2
        if 'precio' in df.columns and 'area_m2' in df.columns:
            df['precio_m2'] = df['precio'] / df['area_m2']
        
        print(f"Dataset procesado: {len(df)} registros, {len(df.columns)} columnas")
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# ==================== LAYOUT PRINCIPAL ====================

app.layout = dbc.Container([
    # Stores
    dcc.Store(id='filtered-data'),
    dcc.Store(id='comparison-data'),
    dcc.Store(id='selected-properties'),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1([
                    html.I(className="bi bi-house-fill me-3"),
                    "Dashboard Inmobiliario Integral"
                ], className="text-center text-white mb-2", style={'fontSize': '3rem', 'fontWeight': 'bold'}),
                html.H4("Análisis Estadístico Profesional - Zapopan & Guadalajara", 
                       className="text-center text-white-50 mb-3"),
                html.P([
                    html.I(className="bi bi-graph-up me-2"),
                    "Sistema completo de análisis: Descriptivo | Normalización | Outliers | Colonias | Comparativo"
                ], className="text-center text-white-50")
            ], style={
                'background': f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 50%, #43e97b 100%)',
                'padding': '50px',
                'borderRadius': '25px',
                'marginBottom': '30px',
                'boxShadow': '0 15px 35px rgba(0,0,0,0.2)',
                'border': '3px solid rgba(255,255,255,0.1)'
            })
        ])
    ]),
    
    # Panel de control principal
    dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-sliders me-2"),
                "Panel de Control Avanzado"
            ], className="mb-0 text-primary")
        ]),
        dbc.CardBody([
            # Configuración principal
            dbc.Row([
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-layers me-1"),
                        "Nivel de Análisis"
                    ], className="fw-bold text-primary"),
                    dcc.RadioItems(
                        id='analysis-level',
                        options=[
                            {'label': [html.I(className="bi bi-building me-1"), " Ciudad"], 'value': 'ciudad'},
                            {'label': [html.I(className="bi bi-geo-alt me-1"), " Colonia"], 'value': 'colonia'},
                            {'label': [html.I(className="bi bi-house me-1"), " Propiedad"], 'value': 'propiedad'}
                        ],
                        value='colonia',
                        inline=True,
                        className="mt-2",
                        labelStyle={'margin-right': '15px'}
                    )
                ], md=4),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-binoculars me-1"),
                        "Modo de Comparación"
                    ], className="fw-bold text-primary"),
                    dcc.RadioItems(
                        id='comparison-mode',
                        options=[
                            {'label': [html.I(className="bi bi-eye me-1"), " Individual"], 'value': 'single'},
                            {'label': [html.I(className="bi bi-arrows-angle-contract me-1"), " Comparativo"], 'value': 'compare'},
                            {'label': [html.I(className="bi bi-bar-chart me-1"), " Múltiple"], 'value': 'multiple'}
                        ],
                        value='single',
                        inline=True,
                        className="mt-2",
                        labelStyle={'margin-right': '15px'}
                    )
                ], md=4),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-graph-up me-1"),
                        "Variable Principal"
                    ], className="fw-bold text-primary"),
                    dcc.Dropdown(
                        id='main-variable',
                        options=[
                            {'label': '💰 Precio', 'value': 'precio'},
                            {'label': '📏 Área m²', 'value': 'area_m2'},
                            {'label': '📊 Precio/m²', 'value': 'precio_m2'},
                            {'label': '🛏️ Recámaras', 'value': 'recamaras'},
                            {'label': '🚗 Estacionamientos', 'value': 'estacionamientos'}
                        ],
                        value='precio',
                        clearable=False
                    )
                ], md=4)
            ], className="mb-4"),
            
            html.Hr(style={'borderColor': COLORS['primary'], 'borderWidth': '2px'}),
            
            # Filtros avanzados
            dbc.Row([
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-building me-1"),
                        "Ciudad"
                    ], className="fw-bold"),
                    dcc.Dropdown(
                        id='city-filter',
                        multi=True,
                        placeholder="Todas las ciudades..."
                    )
                ], md=2),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-geo-alt me-1"),
                        "Colonia"
                    ], className="fw-bold"),
                    dcc.Dropdown(
                        id='colonia-filter',
                        multi=True,
                        placeholder="Todas las colonias..."
                    )
                ], md=3),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-house me-1"),
                        "Tipo Propiedad"
                    ], className="fw-bold"),
                    dcc.Dropdown(
                        id='property-type-filter',
                        multi=True,
                        placeholder="Todos los tipos..."
                    )
                ], md=2),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-currency-dollar me-1"),
                        "Operación"
                    ], className="fw-bold"),
                    dcc.Dropdown(
                        id='operation-filter',
                        multi=True,
                        placeholder="Todas..."
                    )
                ], md=2),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-funnel me-1"),
                        "Filtro Especial"
                    ], className="fw-bold"),
                    dcc.Dropdown(
                        id='special-filter',
                        options=[
                            {'label': '🔥 Top 10 Precio', 'value': 'top_precio'},
                            {'label': '📏 Grandes (>200m²)', 'value': 'grandes'},
                            {'label': '💎 Premium', 'value': 'premium'},
                            {'label': '🏆 Más Recámaras', 'value': 'mas_recamaras'},
                            {'label': '⚠️ Con Outliers', 'value': 'outliers'}
                        ],
                        placeholder="Sin filtro especial"
                    )
                ], md=3)
            ], className="mb-3"),
            
            # Rangos avanzados
            dbc.Row([
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-currency-dollar me-1"),
                        "Rango de Precio (MXN)"
                    ], className="fw-bold"),
                    dcc.RangeSlider(
                        id='price-range',
                        min=0,
                        max=50000000,
                        step=100000,
                        marks={
                            0: '$0',
                            5000000: '$5M',
                            10000000: '$10M',
                            20000000: '$20M',
                            30000000: '$30M',
                            50000000: '$50M'
                        },
                        value=[0, 50000000],
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], md=4),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-rulers me-1"),
                        "Rango de Área (m²)"
                    ], className="fw-bold"),
                    dcc.RangeSlider(
                        id='area-range',
                        min=0,
                        max=1000,
                        step=10,
                        marks={
                            0: '0',
                            100: '100',
                            200: '200',
                            400: '400',
                            600: '600',
                            1000: '1000+'
                        },
                        value=[0, 1000],
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], md=4),
                dbc.Col([
                    html.Label([
                        html.I(className="bi bi-bed me-1"),
                        "Número de Recámaras"
                    ], className="fw-bold"),
                    dcc.RangeSlider(
                        id='bedrooms-range',
                        min=0,
                        max=6,
                        step=1,
                        marks={i: str(i) for i in range(0, 7)},
                        value=[0, 6],
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], md=4)
            ], className="mb-4"),
            
            # Botones de acción
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="bi bi-funnel me-1"),
                            "Aplicar Filtros"
                        ], id="apply-filters", color="primary", size="lg"),
                        dbc.Button([
                            html.I(className="bi bi-arrow-clockwise me-1"),
                            "Resetear"
                        ], id="reset-filters", color="secondary", size="lg"),
                        dbc.Button([
                            html.I(className="bi bi-download me-1"),
                            "Exportar"
                        ], id="export-data", color="success", size="lg")
                    ], className="w-100")
                ], md=8),
                dbc.Col([
                    dbc.Button([
                        html.I(className="bi bi-plus-circle me-1"),
                        "Cargar Datos Externos"
                    ], id="load-external", color="info", size="lg", className="w-100")
                ], md=4)
            ])
        ])
    ], className="mb-4", style={'boxShadow': '0 8px 25px rgba(0,0,0,0.15)'}),
    
    # Métricas principales (KPIs)
    html.Div(id='kpi-container'),
    
    # Tabs principales con diseño mejorado
    dbc.Tabs([
        # Tab 1: Vista General
        dbc.Tab(
            html.Div(id='overview-content', className="mt-4"),
            label=[html.I(className="bi bi-speedometer2 me-2"), "Vista General"],
            tab_id="overview"
        ),
        
        # Tab 2: Análisis Estadístico Descriptivo
        dbc.Tab([
            html.I(className="bi bi-bar-chart me-2"),
            "Análisis Descriptivo"
        ], tab_id="descriptivo", children=[
            html.Div(id='descriptivo-content', className="mt-4")
        ]),
        
        # Tab 3: Análisis de Normalización
        dbc.Tab([
            html.I(className="bi bi-arrow-through-heart me-2"),
            "Normalización"
        ], tab_id="normalizacion", children=[
            html.Div(id='normalizacion-content', className="mt-4")
        ]),
        
        # Tab 4: Análisis de Outliers
        dbc.Tab([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "Outliers"
        ], tab_id="outliers", children=[
            html.Div(id='outliers-content', className="mt-4")
        ]),
        
        # Tab 5: Análisis por Colonias
        dbc.Tab([
            html.I(className="bi bi-geo me-2"),
            "Análisis Colonias"
        ], tab_id="colonias", children=[
            html.Div(id='colonias-content', className="mt-4")
        ]),
        
        # Tab 6: Comparativo Avanzado
        dbc.Tab([
            html.I(className="bi bi-arrows-angle-contract me-2"),
            "Comparativo"
        ], tab_id="comparativo", children=[
            html.Div(id='comparativo-content', className="mt-4")
        ]),
        
        # Tab 7: Análisis Geoespacial
        dbc.Tab([
            html.I(className="bi bi-globe me-2"),
            "Geoespacial"
        ], tab_id="geo", children=[
            html.Div(id='geo-content', className="mt-4")
        ]),
        
        # Tab 8: Correlaciones
        dbc.Tab([
            html.I(className="bi bi-diagram-3 me-2"),
            "Correlaciones"
        ], tab_id="correlaciones", children=[
            html.Div(id='correlaciones-content', className="mt-4")
        ]),
        
        # Tab 9: Insights y Recomendaciones
        dbc.Tab([
            html.I(className="bi bi-lightbulb me-2"),
            "Insights & IA"
        ], tab_id="insights", children=[
            html.Div(id='insights-content', className="mt-4")
        ])
    ], id="main-tabs", active_tab="overview", className="mb-4"),
    
    # Footer mejorado
    html.Hr(className="mt-5"),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5([
                    html.I(className="bi bi-info-circle me-2"),
                    "Sistema de Análisis Inmobiliario Profesional"
                ], className="text-primary"),
                html.P([
                    "Desarrollado para análisis integral del mercado inmobiliario de ",
                    html.Strong("Zapopan y Guadalajara"), ". ",
                    "Incluye análisis descriptivo, normalización, detección de outliers, ",
                    "análisis por colonias y comparaciones avanzadas."
                ], className="text-muted"),
                html.Small([
                    html.I(className="bi bi-calendar me-1"),
                    f"© 2024 | Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                ], className="text-muted")
            ], className="text-center p-3", style={
                'background': 'linear-gradient(45deg, #f8f9fa, #e9ecef)',
                'borderRadius': '15px',
                'border': '1px solid #dee2e6'
            })
        ])
    ])
    
], fluid=True, style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

# ==================== CALLBACKS PRINCIPALES ====================

# Variable global para almacenar datos
current_data = None

@app.callback(
    [Output('city-filter', 'options'),
     Output('colonia-filter', 'options'),
     Output('property-type-filter', 'options'),
     Output('operation-filter', 'options')],
    Input('load-external', 'n_clicks')
)
def initialize_data(n_clicks):
    """Inicializa los datos y opciones de filtros"""
    global current_data
    
    # Cargar datos del sistema
    if current_data is None:
        # Intentar cargar datos existentes
        try:
            current_data = load_csv_data('Consolidados/pretratadaCol/Sep25/pretratadaCol_Sep25_01.csv')
            if current_data is None:
                # Generar datos de ejemplo
                current_data = generate_comprehensive_sample_data()
        except:
            current_data = generate_comprehensive_sample_data()
    
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
    [Input('apply-filters', 'n_clicks')],
    [State('city-filter', 'value'),
     State('colonia-filter', 'value'),
     State('property-type-filter', 'value'),
     State('operation-filter', 'value'),
     State('price-range', 'value'),
     State('area-range', 'value'),
     State('bedrooms-range', 'value'),
     State('special-filter', 'value')]
)
def filter_data(n_clicks, cities, colonias, types, operations, price_range, 
                area_range, bedrooms_range, special_filter):
    """Aplica filtros avanzados a los datos"""
    if current_data is None:
        return None
    
    df = current_data.copy()
    
    # Aplicar filtros básicos
    if cities and 'ciudad' in df.columns:
        df = df[df['ciudad'].isin(cities)]
    
    if colonias and 'colonia' in df.columns:
        df = df[df['colonia'].isin(colonias)]
    
    if types and 'tipo_propiedad' in df.columns:
        df = df[df['tipo_propiedad'].isin(types)]
    
    if operations and 'operacion' in df.columns:
        df = df[df['operacion'].isin(operations)]
    
    # Aplicar rangos numéricos
    if price_range and 'precio' in df.columns:
        df = df[(df['precio'] >= price_range[0]) & (df['precio'] <= price_range[1])]
    
    if area_range and 'area_m2' in df.columns:
        df = df[(df['area_m2'] >= area_range[0]) & (df['area_m2'] <= area_range[1])]
    
    if bedrooms_range and 'recamaras' in df.columns:
        df = df[(df['recamaras'] >= bedrooms_range[0]) & (df['recamaras'] <= bedrooms_range[1])]
    
    # Aplicar filtros especiales
    if special_filter:
        if special_filter == 'top_precio' and 'precio' in df.columns:
            df = df.nlargest(10, 'precio')
        elif special_filter == 'grandes' and 'area_m2' in df.columns:
            df = df[df['area_m2'] > 200]
        elif special_filter == 'premium' and 'precio_m2' in df.columns:
            threshold = df['precio_m2'].quantile(0.8)
            df = df[df['precio_m2'] > threshold]
        elif special_filter == 'mas_recamaras' and 'recamaras' in df.columns:
            max_bedrooms = df['recamaras'].max()
            df = df[df['recamaras'] == max_bedrooms]
        elif special_filter == 'outliers' and 'precio' in df.columns:
            # Detectar outliers usando IQR
            Q1 = df['precio'].quantile(0.25)
            Q3 = df['precio'].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            df = df[(df['precio'] < lower) | (df['precio'] > upper)]
    
    return df.to_json(date_format='iso', orient='split')

@app.callback(
    Output('kpi-container', 'children'),
    Input('filtered-data', 'data')
)
def update_kpis(data_json):
    """Actualiza los KPIs principales"""
    if not data_json:
        return create_empty_kpis()
    
    df = pd.read_json(data_json, orient='split')
    
    if len(df) == 0:
        return create_empty_kpis()
    
    # Calcular KPIs avanzados
    kpis = [
        {
            'title': 'Total Propiedades',
            'value': f"{len(df):,}",
            'subtitle': f"De {len(current_data):,} totales" if current_data is not None else "",
            'icon': 'bi-house-fill',
            'color': 'primary',
            'trend': calculate_trend(df, 'count')
        },
        {
            'title': 'Precio Promedio',
            'value': format_currency(df['precio'].mean()) if 'precio' in df.columns else "N/A",
            'subtitle': f"Mediana: {format_currency(df['precio'].median())}" if 'precio' in df.columns else "",
            'icon': 'bi-currency-dollar',
            'color': 'success',
            'trend': calculate_trend(df, 'precio')
        },
        {
            'title': 'Área Promedio',
            'value': f"{df['area_m2'].mean():.0f} m²" if 'area_m2' in df.columns else "N/A",
            'subtitle': f"Mediana: {df['area_m2'].median():.0f} m²" if 'area_m2' in df.columns else "",
            'icon': 'bi-rulers',
            'color': 'info',
            'trend': calculate_trend(df, 'area_m2')
        },
        {
            'title': 'Precio por m²',
            'value': f"${df['precio_m2'].mean():,.0f}" if 'precio_m2' in df.columns else "N/A",
            'subtitle': f"Mediana: ${df['precio_m2'].median():,.0f}" if 'precio_m2' in df.columns else "",
            'icon': 'bi-graph-up',
            'color': 'warning',
            'trend': calculate_trend(df, 'precio_m2')
        },
        {
            'title': 'Colonias Únicas',
            'value': str(df['colonia'].nunique()) if 'colonia' in df.columns else "N/A",
            'subtitle': f"Top: {df['colonia'].mode()[0] if 'colonia' in df.columns and len(df['colonia'].mode()) > 0 else 'N/A'}",
            'icon': 'bi-geo-alt-fill',
            'color': 'secondary',
            'trend': 'stable'
        },
        {
            'title': 'Variabilidad',
            'value': f"{(df['precio'].std() / df['precio'].mean() * 100):.1f}%" if 'precio' in df.columns else "N/A",
            'subtitle': "Coef. de Variación",
            'icon': 'bi-bar-chart',
            'color': 'dark',
            'trend': 'neutral'
        }
    ]
    
    # Crear cards KPI
    cards = []
    for kpi in kpis:
        # Determinar color del trend
        if kpi['trend'] == 'up':
            trend_color = 'success'
            trend_icon = 'bi-arrow-up'
        elif kpi['trend'] == 'down':
            trend_color = 'danger'
            trend_icon = 'bi-arrow-down'
        else:
            trend_color = 'secondary'
            trend_icon = 'bi-dash'
        
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f"{kpi['icon']} text-{kpi['color']}", 
                              style={'fontSize': '2rem'}),
                        html.I(className=f"{trend_icon} text-{trend_color} float-end", 
                              style={'fontSize': '1rem'})
                    ], className="d-flex justify-content-between mb-2"),
                    html.H3(kpi['value'], className=f"text-{kpi['color']} mb-1"),
                    html.H6(kpi['title'], className="text-muted mb-1"),
                    html.Small(kpi['subtitle'], className="text-muted")
                ])
            ], className="h-100 shadow-sm border-0", style={
                'background': f'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,249,250,0.9))',
                'borderLeft': f'4px solid var(--bs-{kpi["color"]})'
            })
        ], md=2)
        cards.append(card)
    
    return dbc.Row(cards, className="mb-4")

# Callbacks para cada tab
@app.callback(
    Output('overview-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('main-variable', 'value')]
)
def update_overview_tab(data_json, main_variable):
    """Actualiza el tab de vista general"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Resumen ejecutivo
    content.append(create_executive_summary(df))
    
    # Gráficos principales
    row1 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=create_main_distribution(df, main_variable),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=6),
        dbc.Col([
            dcc.Graph(
                figure=create_top_colonias_chart(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=6)
    ])
    content.append(row1)
    
    # Segunda fila de gráficos
    row2 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=create_type_distribution_pie(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=4),
        dbc.Col([
            dcc.Graph(
                figure=create_price_vs_area_scatter(df),
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ], md=8)
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
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Estadísticas descriptivas completas
    content.append(create_descriptive_stats_section(df))
    
    # Distribuciones
    content.append(create_distributions_section(df))
    
    # Cargar insights del análisis descriptivo si están disponibles
    if 'descriptivo_insights' in reports_data:
        content.append(create_insights_from_reports(reports_data['descriptivo_insights'], 'Descriptivo'))
    
    return html.Div(content)

@app.callback(
    Output('normalizacion-content', 'children'),
    Input('filtered-data', 'data')
)
def update_normalizacion_tab(data_json):
    """Actualiza el tab de normalización"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Análisis de normalización
    content.append(create_normalization_analysis(df))
    
    # Comparación antes/después si hay datos de normalización
    if 'normalizacion' in reports_data:
        content.append(create_before_after_comparison(df, reports_data['normalizacion']))
    
    return html.Div(content)

@app.callback(
    Output('outliers-content', 'children'),
    Input('filtered-data', 'data')
)
def update_outliers_tab(data_json):
    """Actualiza el tab de outliers"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Análisis de outliers
    content.append(create_outliers_analysis(df))
    
    # Detección de outliers por método
    content.append(create_outliers_detection_section(df))
    
    return html.Div(content)

@app.callback(
    Output('colonias-content', 'children'),
    Input('filtered-data', 'data')
)
def update_colonias_tab(data_json):
    """Actualiza el tab de análisis por colonias"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Cargar datos específicos de colonias si están disponibles
    colonias_data = reports_data.get('colonias_completo', df)
    
    # Análisis completo por colonias
    content.append(create_colonias_analysis(colonias_data))
    
    # Rankings de colonias
    content.append(create_colonias_rankings(colonias_data))
    
    return html.Div(content)

@app.callback(
    Output('geo-content', 'children'),
    Input('filtered-data', 'data')
)
def update_geo_tab(data_json):
    """Actualiza el tab geoespacial"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Mapa principal
    content.append(create_geo_analysis(df))
    
    return html.Div(content)

@app.callback(
    Output('correlaciones-content', 'children'),
    Input('filtered-data', 'data')
)
def update_correlaciones_tab(data_json):
    """Actualiza el tab de correlaciones"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Análisis de correlaciones
    content.append(create_correlations_analysis(df))
    
    return html.Div(content)

@app.callback(
    Output('comparativo-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('comparison-mode', 'value')]
)
def update_comparativo_tab(data_json, comparison_mode):
    """Actualiza el tab comparativo"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Selector de elementos a comparar
    content.append(create_comparison_selector(df, comparison_mode))
    
    # Gráficos comparativos
    content.append(create_comparison_charts(df, comparison_mode))
    
    return html.Div(content)

@app.callback(
    Output('insights-content', 'children'),
    Input('filtered-data', 'data')
)
def update_insights_tab(data_json):
    """Actualiza el tab de insights y recomendaciones"""
    if not data_json:
        return create_no_data_message()
    
    df = pd.read_json(data_json, orient='split')
    
    content = []
    
    # Insights automáticos
    content.append(create_automatic_insights(df))
    
    # Recomendaciones desde reportes
    content.append(create_recommendations_section())
    
    return html.Div(content)

# ==================== FUNCIONES DE VISUALIZACIÓN ====================

# Variable global para almacenar datos
current_data = None

@app.callback(
    [Output('upload-status', 'children'),
     Output('city-filter', 'options'),
     Output('colonia-filter', 'options'),
     Output('property-type-filter', 'options')],
    [Input('upload-data', 'contents'),
     Input('load-sample-data', 'n_clicks')],
    [State('upload-data', 'filename')]
)
def load_data(contents, n_clicks, filename):
    """Carga datos desde archivo o genera datos de ejemplo"""
    global current_data
    
    ctx = callback_context
    if not ctx.triggered:
        return "", [], [], []
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'load-sample-data':
        # Generar datos de ejemplo
        current_data = generate_sample_data()
        status = dbc.Alert("✅ Datos de ejemplo cargados correctamente", 
                          color="success", dismissable=True)
    
    elif trigger_id == 'upload-data' and contents:
        # Cargar desde archivo
        import base64
        import io
        
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            current_data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            # Preprocesar
            current_data.columns = current_data.columns.str.lower().str.replace(' ', '_')
            
            # Calcular precio_m2 si no existe
            if 'precio' in current_data.columns and 'area_m2' in current_data.columns:
                current_data['precio_m2'] = current_data['precio'] / current_data['area_m2']
            
            status = dbc.Alert(f"✅ Archivo '{filename}' cargado: {len(current_data)} registros", 
                              color="success", dismissable=True)
        except Exception as e:
            status = dbc.Alert(f"❌ Error cargando archivo: {str(e)}", 
                              color="danger", dismissable=True)
            return status, [], [], []
    else:
        return "", [], [], []
    
    # Actualizar opciones de filtros
    cities = [{'label': c, 'value': c} 
             for c in current_data['ciudad'].dropna().unique()] if 'ciudad' in current_data.columns else []
    
    colonias = [{'label': c, 'value': c} 
               for c in current_data['colonia'].dropna().unique()[:50]] if 'colonia' in current_data.columns else []
    
    types = [{'label': t, 'value': t} 
            for t in current_data['tipo_propiedad'].dropna().unique()] if 'tipo_propiedad' in current_data.columns else []
    
    return status, cities, colonias, types

@app.callback(
    Output('metrics-container', 'children'),
    Input('filtered-data', 'data')
)
def update_metrics(data_json):
    """Actualiza las métricas principales"""
    if not data_json:
        return html.Div()
    
    df = pd.read_json(data_json, orient='split')
    
    # Calcular métricas
    metrics = [
        {
            'title': 'Total Propiedades',
            'value': f"{len(df):,}",
            'subtitle': f"De {len(current_data):,} totales" if current_data is not None else "",
            'icon': '🏠',
            'color': 'primary'
        },
        {
            'title': 'Precio Promedio',
            'value': f"${df['precio'].mean()/1000000:.2f}M" if 'precio' in df.columns else "N/A",
            'subtitle': f"Mediana: ${df['precio'].median()/1000000:.2f}M" if 'precio' in df.columns else "",
            'icon': '💰',
            'color': 'success'
        },
        {
            'title': 'Área Promedio',
            'value': f"{df['area_m2'].mean():.0f} m²" if 'area_m2' in df.columns else "N/A",
            'subtitle': f"Mediana: {df['area_m2'].median():.0f} m²" if 'area_m2' in df.columns else "",
            'icon': '📏',
            'color': 'info'
        },
        {
            'title': 'Precio por m²',
            'value': f"${df['precio_m2'].mean():,.0f}" if 'precio_m2' in df.columns else "N/A",
            'subtitle': f"Mediana: ${df['precio_m2'].median():,.0f}" if 'precio_m2' in df.columns else "",
            'icon': '📊',
            'color': 'warning'
        }
    ]
    
    if 'colonia' in df.columns:
        metrics.append({
            'title': 'Colonias',
            'value': str(df['colonia'].nunique()),
            'subtitle': "En el filtro actual",
            'icon': '🏘️',
            'color': 'secondary'
        })
    
    if 'tipo_propiedad' in df.columns:
        most_common = df['tipo_propiedad'].mode()[0] if len(df['tipo_propiedad'].mode()) > 0 else "N/A"
        metrics.append({
            'title': 'Tipo Más Común',
            'value': most_common,
            'subtitle': f"{(df['tipo_propiedad'] == most_common).sum()} propiedades",
            'icon': '🏢',
            'color': 'dark'
        })
    
    # Crear cards de métricas
    cards = []
    for metric in metrics:
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(metric['icon'], className="text-center"),
                    html.H4(metric['value'], className=f"text-{metric['color']} text-center"),
                    html.P(metric['title'], className="text-muted text-center mb-0"),
                    html.Small(metric['subtitle'], className="text-muted")
                ])
            ], className="h-100", style={'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'})
        ], md=2)
        cards.append(card)
    
    return dbc.Row(cards, className="mb-4")

@app.callback(
    Output('stats-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('main-variable', 'value'),
     Input('analysis-level', 'value')]
)
def update_stats_tab(data_json, variable, level):
    """Actualiza el tab de estadísticas"""
    if not data_json:
        return html.Div("No hay datos para mostrar")
    
    df = pd.read_json(data_json, orient='split')
    
    # Crear visualizaciones
    content = []
    
    # Distribución principal
    row1 = dbc.Row([
        dbc.Col([
            dcc.Graph(
                figure=create_distribution_plot(df, variable, level),
                config={'displayModeBar': False}
            )
        ], md=6),
        dbc.Col([
            dcc.Graph(
                figure=create_boxplot(df, variable, level),
                config={'displayModeBar': False}
            )
        ], md=6)
    ])
    content.append(row1)
    
    # Tabla estadística
    if level in df.columns:
        stats_table = create_stats_table(df, variable, level)
        content.append(html.Hr())
        content.append(html.H5("📊 Estadísticas Detalladas", className="mb-3"))
        content.append(stats_table)
    
    return html.Div(content)

# ==================== FUNCIONES DE VISUALIZACIÓN ====================

def generate_sample_data():
    """Genera datos de ejemplo"""
    np.random.seed(42)
    n = 1000
    
    colonias = ['Providencia', 'Country Club', 'Chapalita', 'Ciudad Del Sol', 
                'Zapopan Centro', 'Andares', 'Puerta De Hierro', 'Valle Real',
                'Santa Margarita', 'Jardines Del Sol']
    
    data = {
        'id': range(1, n+1),
        'ciudad': np.random.choice(['Zapopan', 'Guadalajara'], n, p=[0.6, 0.4]),
        'colonia': np.random.choice(colonias, n),
        'tipo_propiedad': np.random.choice(['Casa', 'Departamento', 'Oficina', 'Local'], n, p=[0.4, 0.3, 0.2, 0.1]),
        'operacion': np.random.choice(['Venta', 'Renta'], n, p=[0.7, 0.3]),
        'precio': np.random.lognormal(14.5, 0.8, n),
        'area_m2': np.random.gamma(4, 50, n),
        'recamaras': np.random.poisson(3, n),
        'banos': np.random.poisson(2.5, n),
        'estacionamientos': np.random.poisson(2, n),
        'latitud': 20.6597 + np.random.normal(0, 0.05, n),
        'longitud': -103.3496 + np.random.normal(0, 0.05, n)
    }
    
    df = pd.DataFrame(data)
    
    # Ajustes por colonia
    premium = ['Providencia', 'Country Club', 'Andares', 'Puerta De Hierro']
    df.loc[df['colonia'].isin(premium), 'precio'] *= 2.5
    
    # Ajuste por operación
    df.loc[df['operacion'] == 'Renta', 'precio'] *= 0.005
    
    # Calcular precio_m2
    df['precio_m2'] = df['precio'] / df['area_m2']
    
    return df

def create_distribution_plot(df, variable, group_by):
    """Crea gráfico de distribución"""
    if variable not in df.columns:
        return go.Figure()
    
    if group_by in df.columns:
        fig = px.histogram(df, x=variable, color=group_by, 
                          title=f"Distribución de {variable.title()}",
                          nbins=30, marginal="box")
    else:
        fig = px.histogram(df, x=variable, 
                          title=f"Distribución de {variable.title()}",
                          nbins=30, marginal="box")
    
    fig.update_layout(height=400, template='plotly_white')
    return fig

def create_boxplot(df, variable, group_by):
    """Crea boxplot"""
    if variable not in df.columns:
        return go.Figure()
    
    if group_by in df.columns:
        # Limitar a top 15 para claridad
        top_groups = df[group_by].value_counts().head(15).index
        df_plot = df[df[group_by].isin(top_groups)]
        
        fig = px.box(df_plot, x=group_by, y=variable,
                    title=f"{variable.title()} por {group_by.title()}")
        fig.update_xaxis(tickangle=-45)
    else:
        fig = px.box(df, y=variable,
                    title=f"Boxplot de {variable.title()}")
    
    fig.update_layout(height=400, template='plotly_white')
    return fig

def create_stats_table(df, variable, group_by):
    """Crea tabla de estadísticas"""
    if group_by in df.columns and variable in df.columns:
        stats = df.groupby(group_by)[variable].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
        
        stats = stats.reset_index()
        stats.columns = [group_by.title(), 'N', 'Media', 'Mediana', 'Desv. Est.', 'Mínimo', 'Máximo']
        
        return dash_table.DataTable(
            data=stats.to_dict('records'),
            columns=[{"name": i, "id": i} for i in stats.columns],
            style_cell={'textAlign': 'center'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            style_header={
                'backgroundColor': COLORS['primary'],
                'color': 'white',
                'fontWeight': 'bold'
            }
        )
    
    return html.Div("No hay datos suficientes para la tabla")

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("DASHBOARD INMOBILIARIO - ZAPOPAN & GUADALAJARA")
    print("=" * 60)
    print("\n📊 Iniciando servidor...")
    print("\n💡 Instrucciones:")
    print("1. Abre tu navegador en: http://127.0.0.1:8050")
    print("2. Carga tu archivo CSV o usa datos de ejemplo")
    print("3. Aplica filtros y explora las visualizaciones")
    print("\n🔄 Para detener el servidor: Ctrl+C")
    print("=" * 60)
    
    app.run_server(debug=True, host='127.0.0.1', port=8050)
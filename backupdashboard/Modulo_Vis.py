"""
Módulo de Visualizaciones para Dashboard Inmobiliario
Contiene todas las funciones para generar gráficos interactivos
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats

# Configuración de colores consistente
COLORS = {
    'gradient': ['#667eea', '#764ba2', '#f093fb', '#f5576c'],
    'categorical': px.colors.qualitative.Set3,
    'sequential': px.colors.sequential.Viridis,
    'diverging': px.colors.diverging.RdBu
}

def create_price_distribution(df, group_by=None):
    """Crea histograma de distribución de precios"""
    if group_by:
        fig = px.histogram(
            df, 
            x='precio',
            color=group_by,
            nbins=30,
            title=f'📊 Distribución de Precios por {group_by.title()}',
            labels={'precio': 'Precio ($)', 'count': 'Cantidad'},
            color_discrete_sequence=COLORS['categorical']
        )
    else:
        fig = px.histogram(
            df, 
            x='precio',
            nbins=30,
            title='📊 Distribución de Precios',
            labels={'precio': 'Precio ($)', 'count': 'Cantidad'},
            color_discrete_sequence=[COLORS['gradient'][0]]
        )
    
    # Agregar línea de media y mediana
    mean_price = df['precio'].mean()
    median_price = df['precio'].median()
    
    fig.add_vline(x=mean_price, line_dash="dash", line_color="red", 
                  annotation_text=f"Media: ${mean_price/1000000:.1f}M")
    fig.add_vline(x=median_price, line_dash="dash", line_color="green",
                  annotation_text=f"Mediana: ${median_price/1000000:.1f}M")
    
    fig.update_layout(
        showlegend=True,
        hovermode='x unified',
        bargap=0.1,
        template='plotly_white'
    )
    
    return fig

def create_area_distribution(df, group_by=None):
    """Crea histograma de distribución de áreas"""
    fig = px.histogram(
        df, 
        x='area_m2',
        color=group_by if group_by else None,
        nbins=30,
        title='📏 Distribución de Áreas',
        labels={'area_m2': 'Área (m²)', 'count': 'Cantidad'},
        color_discrete_sequence=COLORS['categorical']
    )
    
    mean_area = df['area_m2'].mean()
    median_area = df['area_m2'].median()
    
    fig.add_vline(x=mean_area, line_dash="dash", line_color="red",
                  annotation_text=f"Media: {mean_area:.0f}m²")
    fig.add_vline(x=median_area, line_dash="dash", line_color="green",
                  annotation_text=f"Mediana: {median_area:.0f}m²")
    
    fig.update_layout(
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_boxplot_analysis(df, variable='precio', group_by='colonia'):
    """Crea boxplots comparativos"""
    # Ordenar por mediana
    if group_by in df.columns:
        order = df.groupby(group_by)[variable].median().sort_values(ascending=False).index[:15]
        df_plot = df[df[group_by].isin(order)]
        
        fig = px.box(
            df_plot,
            x=group_by,
            y=variable,
            color=group_by,
            title=f'📊 Análisis de {variable.title()} por {group_by.title()} (Top 15)',
            labels={variable: variable.title(), group_by: group_by.title()},
            color_discrete_sequence=COLORS['categorical']
        )
        
        fig.update_xaxis(tickangle=-45)
    else:
        fig = px.box(
            df,
            y=variable,
            title=f'📊 Análisis de {variable.title()}',
            color_discrete_sequence=[COLORS['gradient'][0]]
        )
    
    fig.update_layout(
        showlegend=False,
        height=500,
        template='plotly_white'
    )
    
    return fig

def create_scatter_price_area(df, color_by='colonia', trendline=True):
    """Crea scatter plot de precio vs área"""
    # Limitar colonias para mejor visualización
    if color_by == 'colonia':
        top_colonias = df['colonia'].value_counts().head(10).index
        df_plot = df[df['colonia'].isin(top_colonias)]
    else:
        df_plot = df
    
    fig = px.scatter(
        df_plot,
        x='area_m2',
        y='precio',
        color=color_by if color_by in df_plot.columns else None,
        size='precio',
        title='🏠 Relación Precio vs Área',
        labels={'area_m2': 'Área (m²)', 'precio': 'Precio ($)'},
        hover_data=['colonia', 'tipo_propiedad', 'recamaras', 'banos'],
        trendline='ols' if trendline else None,
        color_discrete_sequence=COLORS['categorical']
    )
    
    fig.update_layout(
        height=600,
        template='plotly_white',
        hovermode='closest'
    )
    
    return fig

def create_map_view(df):
    """Crea mapa interactivo con ubicaciones"""
    # Filtrar datos con coordenadas válidas
    df_map = df.dropna(subset=['latitud', 'longitud'])
    
    # Crear categorías de precio para colores
    df_map['precio_categoria'] = pd.qcut(df_map['precio'], 
                                          q=5, 
                                          labels=['Muy Bajo', 'Bajo', 'Medio', 'Alto', 'Muy Alto'])
    
    fig = px.scatter_mapbox(
        df_map,
        lat='latitud',
        lon='longitud',
        color='precio_categoria',
        size='area_m2',
        hover_name='colonia',
        hover_data={
            'precio': ':$,.0f',
            'area_m2': ':.0f',
            'tipo_propiedad': True,
            'recamaras': True,
            'precio_categoria': False,
            'latitud': False,
            'longitud': False
        },
        title='🗺️ Mapa de Propiedades',
        mapbox_style='open-street-map',
        color_discrete_map={
            'Muy Bajo': '#28a745',
            'Bajo': '#6c757d', 
            'Medio': '#ffc107',
            'Alto': '#fd7e14',
            'Muy Alto': '#dc3545'
        },
        zoom=11,
        center={"lat": 20.6597, "lon": -103.3496}
    )
    
    fig.update_layout(
        height=600,
        margin={"r": 0, "t": 30, "l": 0, "b": 0}
    )
    
    return fig

def create_heatmap_geo(df):
    """Crea heatmap de densidad de precios por zona"""
    # Agrupar por colonia
    heatmap_data = df.groupby('colonia').agg({
        'precio': 'mean',
        'precio_m2': 'mean',
        'area_m2': 'mean',
        'id': 'count'
    }).round(2)
    
    heatmap_data.columns = ['Precio Promedio', 'Precio/m²', 'Área Promedio', 'Cantidad']
    heatmap_data = heatmap_data.sort_values('Precio Promedio', ascending=False).head(20)
    
    fig = px.imshow(
        heatmap_data.T,
        labels=dict(x="Colonia", y="Métrica", color="Valor"),
        title='🔥 Heatmap de Métricas por Colonia',
        color_continuous_scale='RdYlGn_r',
        aspect='auto'
    )
    
    fig.update_xaxis(tickangle=-45)
    fig.update_layout(height=400)
    
    return fig

def create_correlation_matrix(df):
    """Crea matriz de correlación"""
    numeric_cols = ['precio', 'area_m2', 'recamaras', 'banos', 
                   'estacionamientos', 'antiguedad', 'precio_m2']
    
    # Filtrar columnas que existen
    cols_to_use = [col for col in numeric_cols if col in df.columns]
    
    corr_matrix = df[cols_to_use].corr()
    
    fig = px.imshow(
        corr_matrix,
        labels=dict(x="Variable", y="Variable", color="Correlación"),
        title='📈 Matriz de Correlación',
        color_continuous_scale='RdBu',
        zmin=-1,
        zmax=1,
        text_auto='.2f'
    )
    
    fig.update_layout(
        height=500,
        width=600
    )
    
    return fig

def create_comparison_chart(df, items, comparison_type='colonia'):
    """Crea gráfico comparativo entre elementos seleccionados"""
    if not items or len(items) == 0:
        return go.Figure().add_annotation(
            text="Selecciona elementos para comparar",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Filtrar datos
    df_comp = df[df[comparison_type].isin(items)]
    
    # Crear subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Precio Promedio', 'Área Promedio', 
                       'Distribución de Tipos', 'Precio por m²'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'pie'}, {'type': 'bar'}]]
    )
    
    # Precio promedio
    avg_price = df_comp.groupby(comparison_type)['precio'].mean()
    fig.add_trace(
        go.Bar(x=avg_price.index, y=avg_price.values, name='Precio',
              marker_color=COLORS['gradient'][0]),
        row=1, col=1
    )
    
    # Área promedio
    avg_area = df_comp.groupby(comparison_type)['area_m2'].mean()
    fig.add_trace(
        go.Bar(x=avg_area.index, y=avg_area.values, name='Área',
              marker_color=COLORS['gradient'][1]),
        row=1, col=2
    )
    
    # Distribución de tipos
    if len(items) == 1:
        type_dist = df_comp['tipo_propiedad'].value_counts()
        fig.add_trace(
            go.Pie(labels=type_dist.index, values=type_dist.values,
                  marker_colors=COLORS['categorical']),
            row=2, col=1
        )
    else:
        # Si hay múltiples items, mostrar barras agrupadas
        for item in items[:5]:  # Limitar a 5 para claridad
            item_data = df_comp[df_comp[comparison_type] == item]
            type_counts = item_data['tipo_propiedad'].value_counts()
            fig.add_trace(
                go.Bar(name=item, x=type_counts.index, y=type_counts.values),
                row=2, col=1
            )
    
    # Precio por m²
    avg_price_m2 = df_comp.groupby(comparison_type)['precio_m2'].mean()
    fig.add_trace(
        go.Bar(x=avg_price_m2.index, y=avg_price_m2.values, name='Precio/m²',
              marker_color=COLORS['gradient'][2]),
        row=2, col=2
    )
    
    fig.update_layout(
        height=700,
        showlegend=False,
        title_text=f"📊 Comparación de {comparison_type.title()}: {', '.join(items[:3])}{'...' if len(items) > 3 else ''}"
    )
    
    return fig

def create_radar_comparison(df, items, comparison_type='colonia'):
    """Crea gráfico de radar para comparación multidimensional"""
    if not items or len(items) == 0:
        return go.Figure()
    
    # Preparar datos para radar
    metrics = ['precio', 'area_m2', 'recamaras', 'banos', 'estacionamientos']
    
    fig = go.Figure()
    
    for item in items[:5]:  # Limitar a 5 para claridad
        item_data = df[df[comparison_type] == item]
        
        # Normalizar valores (0-100)
        values = []
        for metric in metrics:
            if metric in item_data.columns:
                val = item_data[metric].mean()
                max_val = df[metric].max()
                normalized = (val / max_val) * 100 if max_val > 0 else 0
                values.append(normalized)
            else:
                values.append(0)
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[m.title() for m in metrics],
            fill='toself',
            name=item
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="🎯 Comparación Multidimensional"
    )
    
    return fig

def create_outliers_visualization(df, column='precio', method='IQR'):
    """Visualiza outliers detectados"""
    # Calcular outliers
    if method == 'IQR':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = df[(df[column] < lower) | (df[column] > upper)]
    else:  # Z-score
        z_scores = np.abs(stats.zscore(df[column].dropna()))
        outliers = df[z_scores > 3]
    
    # Crear visualización
    fig = go.Figure()
    
    # Datos normales
    normal = df[~df.index.isin(outliers.index)]
    fig.add_trace(go.Scatter(
        x=normal.index,
        y=normal[column],
        mode='markers',
        name='Normal',
        marker=dict(color='blue', size=5, opacity=0.5)
    ))
    
    # Outliers
    fig.add_trace(go.Scatter(
        x=outliers.index,
        y=outliers[column],
        mode='markers',
        name='Outliers',
        marker=dict(color='red', size=10, symbol='diamond'),
        text=outliers['colonia'] if 'colonia' in outliers.columns else None,
        hovertemplate='<b>%{text}</b><br>' +
                     f'{column.title()}: %{{y:,.0f}}<br>' +
                     'Index: %{x}<extra></extra>'
    ))
    
    # Líneas de límites
    if method == 'IQR':
        fig.add_hline(y=upper, line_dash="dash", line_color="orange",
                     annotation_text=f"Upper: {upper:,.0f}")
        fig.add_hline(y=lower, line_dash="dash", line_color="orange",
                     annotation_text=f"Lower: {lower:,.0f}")
    
    fig.update_layout(
        title=f'⚠️ Detección de Outliers en {column.title()} (Método: {method})',
        xaxis_title='Índice',
        yaxis_title=column.title(),
        height=500,
        template='plotly_white'
    )
    
    return fig

def create_insights_cards(df):
    """Genera tarjetas de insights automáticos"""
    insights = []
    
    # Insight 1: Colonia más cara
    avg_by_colonia = df.groupby('colonia')['precio'].mean()
    most_expensive = avg_by_colonia.idxmax()
    most_expensive_price = avg_by_colonia.max()
    
    insights.append({
        'title': '💰 Colonia Más Premium',
        'value': most_expensive,
        'detail': f'Precio promedio: ${most_expensive_price/1000000:.1f}M',
        'color': 'success'
    })
    
    # Insight 2: Variabilidad de precios
    cv = (df['precio'].std() / df['precio'].mean()) * 100
    
    insights.append({
        'title': '📊 Variabilidad del Mercado',
        'value': f'{cv:.1f}%',
        'detail': 'Coeficiente de variación de precios',
        'color': 'warning' if cv > 50 else 'info'
    })
    
    # Insight 3: Tipo de propiedad más común
    most_common_type = df['tipo_propiedad'].mode()[0]
    type_percentage = (df['tipo_propiedad'] == most_common_type).mean() * 100
    
    insights.append({
        'title': '🏠 Tipo Predominante',
        'value': most_common_type,
        'detail': f'{type_percentage:.1f}% del inventario',
        'color': 'primary'
    })
    
    # Insight 4: Correlación precio-área
    if 'area_m2' in df.columns:
        correlation = df['precio'].corr(df['area_m2'])
        
        insights.append({
            'title': '📈 Correlación Precio-Área',
            'value': f'{correlation:.2f}',
            'detail': 'Relación lineal entre variables',
            'color': 'info'
        })
    
    # Insight 5: Oportunidades de inversión
    if 'precio_m2' in df.columns:
        low_price_m2 = df.nsmallest(10, 'precio_m2')['colonia'].value_counts().index[0]
        avg_price_m2_opp = df[df['colonia'] == low_price_m2]['precio_m2'].mean()
        
        insights.append({
            'title': '🎯 Oportunidad de Inversión',
            'value': low_price_m2,
            'detail': f'Precio/m²: ${avg_price_m2_opp:,.0f}',
            'color': 'success'
        })
    
    return insights

def create_time_series_analysis(df, date_column='fecha_publicacion'):
    """Crea análisis de series temporales si hay datos de fecha"""
    if date_column not in df.columns:
        return go.Figure().add_annotation(
            text="No hay datos temporales disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Convertir a datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Agrupar por mes
    monthly = df.groupby(pd.Grouper(key=date_column, freq='M')).agg({
        'precio': 'mean',
        'id': 'count'
    }).reset_index()
    
    # Crear figura con eje Y secundario
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Precio promedio
    fig.add_trace(
        go.Scatter(x=monthly[date_column], y=monthly['precio'],
                  name='Precio Promedio',
                  line=dict(color=COLORS['gradient'][0], width=3)),
        secondary_y=False
    )
    
    # Cantidad de propiedades
    fig.add_trace(
        go.Bar(x=monthly[date_column], y=monthly['id'],
               name='Cantidad',
               marker_color=COLORS['gradient'][1],
               opacity=0.5),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="Fecha")
    fig.update_yaxes(title_text="Precio Promedio", secondary_y=False)
    fig.update_yaxes(title_text="Cantidad de Propiedades", secondary_y=True)
    
    fig.update_layout(
        title='📅 Evolución Temporal del Mercado',
        hovermode='x unified',
        height=400
    )
    
    return fig
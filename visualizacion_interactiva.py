"""
VISUALIZADOR INTERACTIVO AVANZADO - ESDATA EPSILON
==================================================

Sistema completo de visualización interactiva con:
- Gráficas dinámicas con zoom y filtros
- Análisis inteligente automático
- Generación de conclusiones y recomendaciones
- Dashboard HTML interactivo

Características principales:
✓ Plotly para interactividad completa
✓ Detección automática de patrones
✓ Sistema de recomendaciones inteligente
✓ Exportación a HTML

Autor: Sistema ESDATA_Epsilon
Fecha: Septiembre 2025
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from scipy import stats
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

class AnalizadorInteligente:
    """Sistema de análisis inteligente y generación de insights"""
    
    def __init__(self, df):
        self.df = df
        self.insights = []
        self.recomendaciones = []
        self.alertas = []
        
    def detectar_patrones(self):
        """Detecta patrones automáticamente en los datos"""
        print("🔍 DETECTANDO PATRONES AUTOMÁTICAMENTE...")
        print("="*50)
        
        # Patrón 1: Concentración de outliers
        self._detectar_concentracion_outliers()
        
        # Patrón 2: Anomalías de precio por zona
        self._detectar_anomalias_geograficas()
        
        # Patrón 3: Inconsistencias área-precio
        self._detectar_inconsistencias_area_precio()
        
        # Patrón 4: Patrones estacionales (si hay fechas)
        self._detectar_patrones_temporales()
        
        # Patrón 5: Segmentación de mercado
        self._detectar_segmentacion_mercado()
        
    def _detectar_concentracion_outliers(self):
        """Detecta colonias con concentración anómala de outliers"""
        if 'Colonia' not in self.df.columns or 'precio' not in self.df.columns:
            return
            
        outliers_por_colonia = {}
        
        for colonia in self.df['Colonia'].unique():
            if pd.isna(colonia):
                continue
                
            data_colonia = self.df[self.df['Colonia'] == colonia]['precio'].dropna()
            if len(data_colonia) < 5:  # Muy pocos datos
                continue
                
            Q1 = data_colonia.quantile(0.25)
            Q3 = data_colonia.quantile(0.75)
            IQR = Q3 - Q1
            
            outliers = data_colonia[(data_colonia < Q1 - 1.5 * IQR) | 
                                   (data_colonia > Q3 + 1.5 * IQR)]
            
            pct_outliers = len(outliers) / len(data_colonia) * 100
            outliers_por_colonia[colonia] = {
                'total': len(data_colonia),
                'outliers': len(outliers),
                'porcentaje': pct_outliers
            }
        
        # Detectar colonias problemáticas
        colonias_problema = {k: v for k, v in outliers_por_colonia.items() 
                           if v['porcentaje'] > 25 and v['total'] >= 10}
        
        if colonias_problema:
            top_problema = sorted(colonias_problema.items(), 
                                key=lambda x: x[1]['porcentaje'], reverse=True)[:5]
            
            self.alertas.append({
                'tipo': 'CONCENTRACIÓN_OUTLIERS',
                'severidad': 'ALTA' if len(colonias_problema) > 10 else 'MEDIA',
                'mensaje': f"Detectadas {len(colonias_problema)} colonias con >25% outliers",
                'detalles': top_problema
            })
            
            self.insights.append(
                f"🚨 **PATRÓN CRÍTICO:** {len(colonias_problema)} colonias muestran concentración "
                f"anómala de outliers (>25%). Top problema: {top_problema[0][0]} "
                f"({top_problema[0][1]['porcentaje']:.1f}% outliers)"
            )
    
    def _detectar_anomalias_geograficas(self):
        """Detecta anomalías geográficas en precios"""
        if 'PxM2' not in self.df.columns:
            return
            
        df_clean = self.df[['Colonia', 'PxM2', 'operacion']].dropna()
        
        # Calcular PxM2 mediano por colonia
        pxm2_por_colonia = df_clean.groupby(['Colonia', 'operacion'])['PxM2'].agg([
            'median', 'count', 'std'
        ]).reset_index()
        
        # Detectar colonias con precios extremos
        for operacion in ['Ven', 'Ren']:
            data_op = pxm2_por_colonia[pxm2_por_colonia['operacion'] == operacion]
            if len(data_op) == 0:
                continue
                
            Q3 = data_op['median'].quantile(0.75)
            outliers_geograficos = data_op[data_op['median'] > Q3 * 3]  # 3x el Q3
            
            if len(outliers_geograficos) > 0:
                self.alertas.append({
                    'tipo': 'ANOMALÍA_GEOGRÁFICA',
                    'severidad': 'ALTA',
                    'operacion': operacion,
                    'colonias': outliers_geograficos['Colonia'].tolist()
                })
                
                self.insights.append(
                    f"🗺️ **ANOMALÍA GEOGRÁFICA ({operacion}):** "
                    f"{len(outliers_geograficos)} colonias con PxM2 extremo "
                    f"(>3x Q3): {', '.join(outliers_geograficos['Colonia'].head(3))}"
                )
    
    def _detectar_inconsistencias_area_precio(self):
        """Detecta inconsistencias entre área y precio"""
        if not all(col in self.df.columns for col in ['precio', 'area_m2', 'PxM2']):
            return
            
        df_clean = self.df[['precio', 'area_m2', 'PxM2']].dropna()
        
        # Calcular correlación
        correlacion = df_clean['precio'].corr(df_clean['area_m2'])
        
        # Detectar casos con área grande pero precio bajo (y viceversa)
        df_clean['precio_z'] = stats.zscore(df_clean['precio'])
        df_clean['area_z'] = stats.zscore(df_clean['area_m2'])
        df_clean['diferencia_z'] = df_clean['precio_z'] - df_clean['area_z']
        
        inconsistencias = df_clean[abs(df_clean['diferencia_z']) > 2]
        pct_inconsistencias = len(inconsistencias) / len(df_clean) * 100
        
        if pct_inconsistencias > 5:
            self.alertas.append({
                'tipo': 'INCONSISTENCIAS_ÁREA_PRECIO',
                'severidad': 'MEDIA',
                'porcentaje': pct_inconsistencias,
                'casos': len(inconsistencias)
            })
            
            self.insights.append(
                f"⚠️ **INCONSISTENCIAS:** {pct_inconsistencias:.1f}% de propiedades "
                f"({len(inconsistencias):,} casos) muestran desproporción área-precio. "
                f"Correlación general: {correlacion:.2f}"
            )
    
    def _detectar_patrones_temporales(self):
        """Detecta patrones temporales si hay información de fechas"""
        # Por ahora placeholder - se puede implementar si hay datos temporales
        self.insights.append(
            "📅 **ANÁLISIS TEMPORAL:** Datos disponibles para un período. "
            "Se recomienda análisis estacional para detectar tendencias."
        )
    
    def _detectar_segmentacion_mercado(self):
        """Detecta segmentación natural del mercado"""
        if 'PxM2' not in self.df.columns:
            return
            
        df_clean = self.df[['PxM2', 'operacion', 'tipo_propiedad']].dropna()
        
        # Análisis por tipo de propiedad
        segmentos = {}
        for tipo in df_clean['tipo_propiedad'].unique():
            if pd.isna(tipo):
                continue
                
            data_tipo = df_clean[df_clean['tipo_propiedad'] == tipo]['PxM2']
            if len(data_tipo) >= 10:
                segmentos[tipo] = {
                    'mediana': data_tipo.median(),
                    'std': data_tipo.std(),
                    'count': len(data_tipo)
                }
        
        # Detectar segmentos premium y económicos
        medianas = [v['mediana'] for v in segmentos.values()]
        if len(medianas) > 2:
            Q3_medianas = np.quantile(medianas, 0.75)
            Q1_medianas = np.quantile(medianas, 0.25)
            
            segmento_premium = [k for k, v in segmentos.items() 
                              if v['mediana'] > Q3_medianas]
            segmento_economico = [k for k, v in segmentos.items() 
                                if v['mediana'] < Q1_medianas]
            
            self.insights.append(
                f"🎯 **SEGMENTACIÓN:** Mercado naturalmente segmentado. "
                f"Premium: {', '.join(segmento_premium)}. "
                f"Económico: {', '.join(segmento_economico)}"
            )
    
    def generar_conclusiones(self):
        """Genera conclusiones automáticas basadas en los patrones"""
        conclusiones = []
        
        # Conclusión sobre calidad de datos
        total_registros = len(self.df)
        registros_completos = len(self.df[['precio', 'area_m2']].dropna())
        completitud = registros_completos / total_registros * 100
        
        if completitud >= 80:
            conclusiones.append(
                f"✅ **CALIDAD DE DATOS BUENA:** {completitud:.1f}% de completitud "
                f"permite análisis confiable con {registros_completos:,} registros válidos."
            )
        else:
            conclusiones.append(
                f"⚠️ **CALIDAD DE DATOS REGULAR:** {completitud:.1f}% de completitud "
                f"requiere limpieza adicional para análisis más precisos."
            )
        
        # Conclusión sobre outliers
        alertas_criticas = [a for a in self.alertas if a['severidad'] == 'ALTA']
        if len(alertas_criticas) > 0:
            conclusiones.append(
                f"🚨 **OUTLIERS CRÍTICOS:** {len(alertas_criticas)} problemas de alta "
                f"severidad requieren investigación inmediata."
            )
        
        # Conclusión sobre distribución de mercado
        if 'operacion' in self.df.columns:
            dist_operacion = self.df['operacion'].value_counts(normalize=True) * 100
            oper_principal = dist_operacion.index[0]
            pct_principal = dist_operacion.iloc[0]
            
            conclusiones.append(
                f"📊 **DISTRIBUCIÓN:** Mercado dominado por {oper_principal} "
                f"({pct_principal:.1f}%), sugiere especialización en este segmento."
            )
        
        return conclusiones
    
    def generar_recomendaciones(self):
        """Genera recomendaciones de acción y estudios adicionales"""
        recomendaciones = []
        
        # Recomendaciones basadas en alertas
        alertas_geograficas = [a for a in self.alertas if a['tipo'] == 'ANOMALÍA_GEOGRÁFICA']
        if alertas_geograficas:
            recomendaciones.append({
                'categoria': 'INVESTIGACIÓN INMEDIATA',
                'accion': 'Investigar colonias con precios extremos',
                'detalles': 'Verificar si son errores de captura o características únicas del mercado',
                'prioridad': 'ALTA'
            })
        
        # Recomendaciones de limpieza
        if any(a['severidad'] == 'ALTA' for a in self.alertas):
            recomendaciones.append({
                'categoria': 'LIMPIEZA DE DATOS',
                'accion': 'Implementar validaciones automáticas',
                'detalles': 'Crear reglas de negocio para detectar precios irreales',
                'prioridad': 'ALTA'
            })
        
        # Recomendaciones de análisis adicional
        recomendaciones.extend([
            {
                'categoria': 'ANÁLISIS TEMPORAL',
                'accion': 'Analizar tendencias por período',
                'detalles': 'Evaluar estacionalidad y evolución de precios',
                'prioridad': 'MEDIA'
            },
            {
                'categoria': 'SEGMENTACIÓN AVANZADA',
                'accion': 'Clustering de colonias similares',
                'detalles': 'Agrupar zonas con características de mercado similares',
                'prioridad': 'MEDIA'
            },
            {
                'categoria': 'MODELO PREDICTIVO',
                'accion': 'Desarrollar modelo de precio estimado',
                'detalles': 'Usar área, ubicación y tipo para predecir precios justos',
                'prioridad': 'BAJA'
            }
        ])
        
        return recomendaciones


class VisualizadorInteractivo:
    """Visualizador interactivo avanzado con Plotly"""
    
    def __init__(self, archivo_csv):
        self.archivo = archivo_csv
        self.df = None
        self.analizador = None
        self.figuras = []
        
    def cargar_datos(self):
        """Cargar y preparar datos"""
        try:
            self.df = pd.read_csv(self.archivo)
            
            # Convertir a numérico
            numeric_cols = ['area_m2', 'precio', 'PxM2']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            self.analizador = AnalizadorInteligente(self.df)
            print(f"✅ Datos cargados: {len(self.df):,} registros")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def crear_grafica_interactiva_precio(self):
        """Gráfica interactiva de distribución de precios"""
        if self.df is None or 'precio' not in self.df.columns:
            return None
            
        df_clean = self.df[['precio', 'operacion', 'Colonia', 'tipo_propiedad']].dropna()
        
        # Crear subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Distribución General', 'Por Operación', 
                          'Scatter por Colonia', 'Box Plot por Tipo'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Histograma general
        fig.add_trace(
            go.Histogram(x=df_clean['precio'], nbinsx=50, name='Distribución Precio',
                        hovertemplate='Precio: $%{x:,.0f}<br>Frecuencia: %{y}<extra></extra>'),
            row=1, col=1
        )
        
        # 2. Por operación
        for operacion in df_clean['operacion'].unique():
            data_op = df_clean[df_clean['operacion'] == operacion]['precio']
            fig.add_trace(
                go.Histogram(x=data_op, name=f'{operacion} ({len(data_op)})', 
                           opacity=0.7, nbinsx=30),
                row=1, col=2
            )
        
        # 3. Scatter por colonia (top 10)
        top_colonias = df_clean['Colonia'].value_counts().head(10).index
        df_top_colonias = df_clean[df_clean['Colonia'].isin(top_colonias)]
        
        fig.add_trace(
            go.Scatter(x=df_top_colonias.index, y=df_top_colonias['precio'],
                      mode='markers', text=df_top_colonias['Colonia'],
                      name='Precios por Colonia',
                      hovertemplate='Precio: $%{y:,.0f}<br>Colonia: %{text}<extra></extra>'),
            row=2, col=1
        )
        
        # 4. Box plot por tipo
        tipos_principales = df_clean['tipo_propiedad'].value_counts().head(6).index
        df_tipos = df_clean[df_clean['tipo_propiedad'].isin(tipos_principales)]
        
        for tipo in tipos_principales:
            data_tipo = df_tipos[df_tipos['tipo_propiedad'] == tipo]['precio']
            fig.add_trace(
                go.Box(y=data_tipo, name=tipo, 
                      hovertemplate=f'{tipo}<br>Precio: $%{{y:,.0f}}<extra></extra>'),
                row=2, col=2
            )
        
        # Actualizar layout
        fig.update_layout(
            title='📊 ANÁLISIS INTERACTIVO DE PRECIOS',
            height=800,
            showlegend=True,
            hovermode='closest'
        )
        
        # Personalizar ejes
        fig.update_xaxes(title_text="Precio ($)", row=1, col=1)
        fig.update_xaxes(title_text="Precio ($)", row=1, col=2)
        fig.update_xaxes(title_text="Índice", row=2, col=1)
        fig.update_xaxes(title_text="Tipo de Propiedad", row=2, col=2)
        
        fig.update_yaxes(title_text="Frecuencia", row=1, col=1)
        fig.update_yaxes(title_text="Frecuencia", row=1, col=2)
        fig.update_yaxes(title_text="Precio ($)", row=2, col=1)
        fig.update_yaxes(title_text="Precio ($)", row=2, col=2)
        
        self.figuras.append(('precio_interactivo', fig))
        return fig
    
    def crear_mapa_outliers(self):
        """Mapa de calor de outliers por colonia"""
        if self.df is None or 'Colonia' not in self.df.columns or 'precio' not in self.df.columns:
            return None
            
        # Calcular outliers por colonia
        outliers_data = []
        for colonia in self.df['Colonia'].unique():
            if pd.isna(colonia):
                continue
                
            data_colonia = self.df[self.df['Colonia'] == colonia]['precio'].dropna()
            if len(data_colonia) < 3:
                continue
                
            Q1 = data_colonia.quantile(0.25)
            Q3 = data_colonia.quantile(0.75)
            IQR = Q3 - Q1
            
            outliers = data_colonia[(data_colonia < Q1 - 1.5 * IQR) | 
                                   (data_colonia > Q3 + 1.5 * IQR)]
            
            pct_outliers = len(outliers) / len(data_colonia) * 100
            
            outliers_data.append({
                'Colonia': colonia,
                'Total_Propiedades': len(data_colonia),
                'Outliers': len(outliers),
                'Porcentaje_Outliers': pct_outliers,
                'Precio_Mediano': data_colonia.median(),
                'Precio_Promedio': data_colonia.mean()
            })
        
        df_outliers = pd.DataFrame(outliers_data)
        df_outliers = df_outliers.sort_values('Porcentaje_Outliers', ascending=False)
        
        # Crear gráfica de barras interactiva
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_outliers['Colonia'][:20],  # Top 20
            y=df_outliers['Porcentaje_Outliers'][:20],
            text=df_outliers['Outliers'][:20],
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>' +
                         'Outliers: %{text} (%{y:.1f}%)<br>' +
                         '<extra></extra>',
            marker_color=df_outliers['Porcentaje_Outliers'][:20],
            marker_colorscale='Reds'
        ))
        
        fig.update_layout(
            title='🗺️ MAPA DE OUTLIERS POR COLONIA (Top 20)',
            xaxis_title='Colonia',
            yaxis_title='Porcentaje de Outliers (%)',
            height=600,
            xaxis_tickangle=-45
        )
        
        self.figuras.append(('mapa_outliers', fig))
        return fig
    
    def crear_analisis_correlacion(self):
        """Análisis de correlación interactivo"""
        if self.df is None:
            return None
            
        vars_numericas = ['precio', 'area_m2', 'PxM2']
        df_clean = self.df[vars_numericas + ['operacion']].dropna()
        
        if len(df_clean) == 0:
            return None
        
        # Crear scatter plot matrix
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Precio vs Área', 'Precio vs PxM2', 
                          'Área vs PxM2', 'Correlaciones')
        )
        
        # Scatter plots por operación
        operaciones = df_clean['operacion'].unique()
        colors = ['blue', 'red', 'green']
        
        for i, op in enumerate(operaciones):
            data_op = df_clean[df_clean['operacion'] == op]
            color = colors[i % len(colors)]
            
            # Precio vs Área
            fig.add_trace(
                go.Scatter(x=data_op['area_m2'], y=data_op['precio'],
                          mode='markers', name=f'{op}',
                          marker_color=color, opacity=0.6,
                          hovertemplate=f'{op}<br>Área: %{{x}} m²<br>Precio: $%{{y:,.0f}}<extra></extra>'),
                row=1, col=1
            )
            
            # Precio vs PxM2
            fig.add_trace(
                go.Scatter(x=data_op['PxM2'], y=data_op['precio'],
                          mode='markers', name=f'{op}',
                          marker_color=color, opacity=0.6, showlegend=False,
                          hovertemplate=f'{op}<br>PxM2: $%{{x:,.0f}}<br>Precio: $%{{y:,.0f}}<extra></extra>'),
                row=1, col=2
            )
            
            # Área vs PxM2
            fig.add_trace(
                go.Scatter(x=data_op['area_m2'], y=data_op['PxM2'],
                          mode='markers', name=f'{op}',
                          marker_color=color, opacity=0.6, showlegend=False,
                          hovertemplate=f'{op}<br>Área: %{{x}} m²<br>PxM2: $%{{y:,.0f}}<extra></extra>'),
                row=2, col=1
            )
        
        # Matriz de correlación
        corr_matrix = df_clean[vars_numericas].corr()
        
        fig.add_trace(
            go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.index,
                      colorscale='RdBu', zmid=0, text=corr_matrix.round(2).values,
                      texttemplate='%{text}', textfont_size=12,
                      hovertemplate='%{x} vs %{y}<br>Correlación: %{z:.3f}<extra></extra>'),
            row=2, col=2
        )
        
        fig.update_layout(
            title='🔗 ANÁLISIS DE CORRELACIONES INTERACTIVO',
            height=800,
            showlegend=True
        )
        
        # Actualizar ejes
        fig.update_xaxes(title_text="Área (m²)", row=1, col=1)
        fig.update_xaxes(title_text="PxM2 ($)", row=1, col=2)
        fig.update_xaxes(title_text="Área (m²)", row=2, col=1)
        
        fig.update_yaxes(title_text="Precio ($)", row=1, col=1)
        fig.update_yaxes(title_text="Precio ($)", row=1, col=2)
        fig.update_yaxes(title_text="PxM2 ($)", row=2, col=1)
        
        self.figuras.append(('correlaciones', fig))
        return fig
    
    def generar_dashboard_html(self):
        """Genera dashboard HTML completo"""
        if not self.figuras:
            print("❌ No hay figuras para generar dashboard")
            return None
            
        print("🎨 Generando dashboard HTML interactivo...")
        
        # Verificar que los datos estén cargados
        if self.df is None:
            print("❌ No hay datos cargados para generar dashboard")
            return None
            
        # Verificar que el analizador esté inicializado
        if self.analizador is None:
            print("🔍 Inicializando analizador inteligente...")
            self.analizador = AnalizadorInteligente(self.df)
        
        # Configurar el HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ESDATA Epsilon - Dashboard Interactivo</title>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .header { background: linear-gradient(45deg, #1f77b4, #2ca02c); color: white; 
                         padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
                .section { background: white; padding: 20px; border-radius: 10px; 
                          margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                .insights { background: #e8f4fd; padding: 15px; border-left: 4px solid #1f77b4; 
                           border-radius: 5px; margin: 10px 0; }
                .alert { background: #ffe6e6; padding: 15px; border-left: 4px solid #ff4444; 
                        border-radius: 5px; margin: 10px 0; }
                .recomendacion { background: #e8f5e8; padding: 15px; border-left: 4px solid #28a745; 
                                border-radius: 5px; margin: 10px 0; }
                .chart-container { margin: 20px 0; }
                h2 { color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; }
                h3 { color: #2ca02c; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏠 ESDATA EPSILON - ANÁLISIS INMOBILIARIO INTERACTIVO</h1>
                <p>Dashboard inteligente con análisis automático y recomendaciones</p>
            </div>
        """
        
        # Añadir análisis inteligente
        self.analizador.detectar_patrones()
        conclusiones = self.analizador.generar_conclusiones()
        recomendaciones = self.analizador.generar_recomendaciones()
        
        # Sección de insights
        html_content += '<div class="section"><h2>🧠 INSIGHTS AUTOMÁTICOS</h2>'
        for insight in self.analizador.insights:
            html_content += f'<div class="insights">{insight}</div>'
        html_content += '</div>'
        
        # Sección de conclusiones
        html_content += '<div class="section"><h2>📋 CONCLUSIONES</h2>'
        for conclusion in conclusiones:
            html_content += f'<div class="insights">{conclusion}</div>'
        html_content += '</div>'
        
        # Sección de alertas
        if self.analizador.alertas:
            html_content += '<div class="section"><h2>🚨 ALERTAS</h2>'
            for alerta in self.analizador.alertas:
                html_content += f'<div class="alert"><strong>{alerta["tipo"]}:</strong> {alerta.get("mensaje", "Requiere atención")}</div>'
            html_content += '</div>'
        
        # Sección de recomendaciones
        html_content += '<div class="section"><h2>💡 RECOMENDACIONES</h2>'
        for rec in recomendaciones:
            prioridad_color = "red" if rec['prioridad'] == 'ALTA' else "orange" if rec['prioridad'] == 'MEDIA' else "green"
            html_content += f'''
            <div class="recomendacion">
                <h4 style="color: {prioridad_color};">🎯 {rec['categoria']} (Prioridad: {rec['prioridad']})</h4>
                <p><strong>Acción:</strong> {rec['accion']}</p>
                <p><strong>Detalles:</strong> {rec['detalles']}</p>
            </div>
            '''
        html_content += '</div>'
        
        # Añadir las gráficas
        html_content += '<div class="section"><h2>📊 VISUALIZACIONES INTERACTIVAS</h2>'
        
        chart_id = 0
        for nombre, fig in self.figuras:
            html_content += f'<div class="chart-container"><div id="chart{chart_id}"></div></div>'
            chart_id += 1
        
        html_content += '</div>'
        
        # Añadir scripts de Plotly
        html_content += '<script>'
        chart_id = 0
        for nombre, fig in self.figuras:
            # Usar método más confiable para HTML
            import json
            fig_dict = fig.to_dict()
            fig_json = json.dumps(fig_dict, default=str)
            html_content += f'''
            var plotData{chart_id} = {fig_json};
            Plotly.newPlot("chart{chart_id}", plotData{chart_id}.data, plotData{chart_id}.layout);
            '''
            chart_id += 1
        
        html_content += '''
        </script>
        </body>
        </html>
        '''
        
        # Guardar archivo
        with open('dashboard_interactivo.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print("✅ Dashboard guardado en: dashboard_interactivo.html")
        return 'dashboard_interactivo.html'
    
    def ejecutar_analisis_completo(self):
        """Ejecuta análisis completo con todas las visualizaciones"""
        print("🚀 INICIANDO ANÁLISIS INTERACTIVO COMPLETO")
        print("="*50)
        
        if not self.cargar_datos():
            return False
        
        print("\n📊 Creando visualizaciones interactivas...")
        
        # Crear todas las gráficas
        self.crear_grafica_interactiva_precio()
        self.crear_mapa_outliers()
        self.crear_analisis_correlacion()
        
        print(f"✅ {len(self.figuras)} visualizaciones creadas")
        
        # Generar dashboard HTML
        dashboard_file = self.generar_dashboard_html()
        
        print("\n🎉 ANÁLISIS INTERACTIVO COMPLETADO")
        print("📁 Archivos generados:")
        print(f"   - {dashboard_file}")
        print("\n💡 Instrucciones:")
        print("   1. Abrir dashboard_interactivo.html en tu navegador")
        print("   2. Usar zoom, hover y filtros en las gráficas")
        print("   3. Revisar insights automáticos y recomendaciones")
        
        return True


def main():
    """Función principal"""
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    
    print("🎨 VISUALIZADOR INTERACTIVO ESDATA EPSILON")
    print("="*50)
    print(f"📂 Archivo: {archivo}")
    
    visualizador = VisualizadorInteractivo(archivo)
    visualizador.ejecutar_analisis_completo()


if __name__ == "__main__":
    main()
"""
GENERADOR DE DASHBOARD HTML SIMPLE Y CONFIABLE
==============================================

Versión simplificada que garantiza que las gráficas se muestren correctamente
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo

class DashboardSimple:
    def __init__(self, archivo_csv):
        self.archivo = archivo_csv
        self.df = None
        
    def cargar_datos(self):
        """Cargar datos"""
        try:
            self.df = pd.read_csv(self.archivo)
            numeric_cols = ['area_m2', 'precio', 'PxM2']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            print(f"✅ Datos cargados: {len(self.df):,} registros")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def crear_grafica_precios(self):
        """Gráfica de distribución de precios"""
        if self.df is None:
            if not self.cargar_datos():
                return None
        
        # Double-check that df is not None after loading
        if self.df is None:
            print("❌ Error: No se pudieron cargar los datos")
            return None
            
        df_clean = self.df[['precio', 'operacion']].dropna()
        
        fig = px.histogram(
            df_clean, 
            x='precio', 
            color='operacion',
            title='🏠 Distribución de Precios por Operación',
            labels={'precio': 'Precio ($)', 'count': 'Frecuencia'},
            nbins=50
        )
        
        fig.update_layout(
            height=500,
            xaxis_title="Precio ($)",
            yaxis_title="Frecuencia"
        )
        
        return fig
    def crear_grafica_area(self):
        """Gráfica de área vs precio"""
        if self.df is None:
            if not self.cargar_datos():
                return None
        
        # Double-check that df is not None after loading
        if self.df is None:
            print("❌ Error: No se pudieron cargar los datos")
            return None
            
        df_clean = self.df[['precio', 'area_m2', 'operacion']].dropna()
        # Limitar área para mejor visualización
        df_clean = df_clean[df_clean['area_m2'] <= 1000]
        
        fig = px.scatter(
            df_clean,
            x='area_m2',
            y='precio',
            color='operacion',
            title='📐 Relación Área vs Precio',
            labels={'area_m2': 'Área (m²)', 'precio': 'Precio ($)'}
        )
        
        fig.update_layout(
            height=500,
            xaxis_title="Área (m²)",
            yaxis_title="Precio ($)"
        )
        
        return fig
    
    def crear_grafica_outliers(self):
        if self.df is None:
            if not self.cargar_datos():
                return None
        
        # Double-check that df is not None after loading
        if self.df is None:
            print("❌ Error: No se pudieron cargar los datos")
            return None
            
        # Calcular outliers por colonia
        outliers_data = []
        for colonia in self.df['Colonia'].unique():
            if pd.isna(colonia):
                continue
                
            data_col = self.df[self.df['Colonia'] == colonia]['precio'].dropna()
            if len(data_col) < 5:
                continue
                
            Q1 = data_col.quantile(0.25)
            Q3 = data_col.quantile(0.75)
            IQR = Q3 - Q1
            
            outliers = data_col[(data_col < Q1 - 1.5 * IQR) | 
                               (data_col > Q3 + 1.5 * IQR)]
            
            pct_outliers = len(outliers) / len(data_col) * 100
            
            outliers_data.append({
                'Colonia': colonia,
                'Total': len(data_col),
                'Outliers': len(outliers),
                'Porcentaje': pct_outliers
            })
        
        df_outliers = pd.DataFrame(outliers_data)
        df_outliers = df_outliers.sort_values('Porcentaje', ascending=False).head(15)
        
        fig = px.bar(
            df_outliers,
            x='Colonia',
            y='Porcentaje',
            title='🗺️ Top 15 Colonias con Más Outliers',
            labels={'Porcentaje': 'Porcentaje de Outliers (%)', 'Colonia': 'Colonia'}
        )
        
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def generar_dashboard(self):
        """Genera dashboard HTML funcional"""
        print("🎨 Generando dashboard HTML...")
        
        if not self.cargar_datos():
            return False
        
        # Explicit check to ensure self.df is not None
        if self.df is None:
            print("❌ Error: No hay datos para generar el dashboard")
            return False
            
        # Crear las 3 gráficas principales
        fig1 = self.crear_grafica_precios()
        fig2 = self.crear_grafica_area()
        fig3 = self.crear_grafica_outliers()
        
        # Generar HTML para cada gráfica por separado
        html1 = pyo.plot(fig1, output_type='div', include_plotlyjs=False)
        html2 = pyo.plot(fig2, output_type='div', include_plotlyjs=False)
        html3 = pyo.plot(fig3, output_type='div', include_plotlyjs=False) if fig3 else "<div>No hay datos suficientes para gráfica de outliers</div>"
        
        # Plantilla HTML completa
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🏠 ESDATA Epsilon - Dashboard Interactivo</title>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
        }}
        .header {{ 
            background: linear-gradient(45deg, #1f77b4, #2ca02c); 
            color: white; 
            padding: 30px; 
            border-radius: 10px; 
            text-align: center; 
            margin-bottom: 30px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .section {{ 
            background: white; 
            padding: 25px; 
            border-radius: 10px; 
            margin-bottom: 25px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        .chart-container {{ 
            margin: 30px 0; 
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .insights {{ 
            background: #e8f4fd; 
            padding: 20px; 
            border-left: 4px solid #1f77b4; 
            border-radius: 5px; 
            margin: 15px 0; 
        }}
        .stats {{ 
            display: flex; 
            justify-content: space-around; 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 20px 0;
        }}
        .stat-item {{ 
            text-align: center; 
        }}
        .stat-number {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #1f77b4; 
        }}
        h1 {{ font-size: 2.2em; margin-bottom: 10px; }}
        h2 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 ESDATA EPSILON - ANÁLISIS INMOBILIARIO</h1>
        <p style="font-size: 1.2em;">Dashboard Interactivo con Análisis de Outliers</p>
        <p style="opacity: 0.9;">📊 Explora las gráficas con zoom, hover y filtros interactivos</p>
    </div>
    
    <div class="section">
        <h2>📈 ESTADÍSTICAS GENERALES</h2>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(self.df):,}</div>
                <div>Total Propiedades</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(self.df.dropna(subset=['precio', 'area_m2'])):,}</div>
                <div>Registros Válidos</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{self.df['Colonia'].nunique():,}</div>
                <div>Colonias</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(self.df[self.df['operacion'] == 'Ven']):,}</div>
                <div>Ventas</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>💡 INSIGHTS PRINCIPALES</h2>
        <div class="insights">
            <strong>🎯 Distribución del Mercado:</strong><br>
            • {len(self.df[self.df['operacion'] == 'Ven']):,} propiedades en venta ({len(self.df[self.df['operacion'] == 'Ven'])/len(self.df)*100:.1f}%)<br>
            • {len(self.df[self.df['operacion'] == 'Ren']):,} propiedades en renta ({len(self.df[self.df['operacion'] == 'Ren'])/len(self.df)*100:.1f}%)<br>
            • Precio promedio: ${self.df['precio'].mean():,.0f}
        </div>
        <div class="insights">
            <strong>📊 Calidad de Datos:</strong><br>
            • Completitud precio: {self.df['precio'].notna().sum()/len(self.df)*100:.1f}%<br>
            • Completitud área: {self.df['area_m2'].notna().sum()/len(self.df)*100:.1f}%<br>
            • PxM2 calculado: {self.df['PxM2'].notna().sum():,} propiedades
        </div>
    </div>
    
    <div class="section">
        <h2>📊 GRÁFICAS INTERACTIVAS</h2>
        <p style="color: #666; margin-bottom: 20px;">
            💡 <strong>Instrucciones:</strong> Usa zoom (click y arrastra), hover (pasar mouse) y filtros (click en leyenda)
        </p>
        
        <div class="chart-container">
            <h3>📈 Distribución de Precios</h3>
            {html1}
        </div>
        
        <div class="chart-container">
            <h3>📐 Relación Área vs Precio</h3>
            {html2}
        </div>
        
        <div class="chart-container">
            <h3>🗺️ Outliers por Colonia</h3>
            {html3}
        </div>
    </div>
    
    <div class="section">
        <h2>🎯 PRÓXIMOS PASOS</h2>
        <div class="insights">
            <strong>🔍 Análisis Recomendados:</strong><br>
            • Investigar colonias con alta concentración de outliers<br>
            • Validar precios extremos vs características únicas<br>
            • Segmentar análisis por tipo de propiedad<br>
            • Implementar modelo predictivo de precios
        </div>
    </div>
    
    <footer style="text-align: center; color: #666; margin-top: 50px; padding: 20px;">
        <p>🏠 Sistema ESDATA Epsilon | Análisis generado automáticamente</p>
    </footer>
</body>
</html>
        """
        
        # Guardar archivo
        with open('dashboard_interactivo.html', 'w', encoding='utf-8') as f:
            f.write(html_template)
            
        print("✅ Dashboard HTML generado correctamente!")
        print("📁 Archivo: dashboard_interactivo.html")
        print("\n💡 Para ver el dashboard:")
        print("   1. Abre el archivo en tu navegador")
        print("   2. Las gráficas ahora se mostrarán correctamente")
        print("   3. Usa zoom, hover y filtros interactivos")
        
        return True

def main():
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    dashboard = DashboardSimple(archivo)
    dashboard.generar_dashboard()

if __name__ == "__main__":
    main()
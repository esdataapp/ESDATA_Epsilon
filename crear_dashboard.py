"""
GENERADOR DE DASHBOARD FUNCIONAL - VERSIÓN SIMPLE
================================================
"""

import pandas as pd
import plotly.express as px
import plotly.offline as pyo

def crear_dashboard_funcional():
    """Crea un dashboard HTML que funciona correctamente"""
    
    print("🎨 Creando dashboard HTML funcional...")
    
    # Cargar datos
    df = pd.read_csv(r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv")
    
    # Convertir a numérico
    numeric_cols = ['area_m2', 'precio', 'PxM2']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"✅ Datos cargados: {len(df):,} registros")
    
    # Crear gráficas
    df_clean = df[['precio', 'operacion']].dropna()
    
    # 1. Gráfica de precios
    fig1 = px.histogram(
        df_clean, 
        x='precio', 
        color='operacion',
        title='🏠 Distribución de Precios por Operación',
        labels={'precio': 'Precio ($)', 'count': 'Frecuencia'},
        nbins=50
    )
    fig1.update_layout(height=500)
    
    # 2. Gráfica área vs precio
    df_scatter = df[['precio', 'area_m2', 'operacion']].dropna()
    df_scatter = df_scatter[df_scatter['area_m2'] <= 1000]  # Limitar para visualizar mejor
    
    fig2 = px.scatter(
        df_scatter,
        x='area_m2',
        y='precio',
        color='operacion',
        title='📐 Relación Área vs Precio',
        labels={'area_m2': 'Área (m²)', 'precio': 'Precio ($)'},
        opacity=0.6
    )
    fig2.update_layout(height=500)
    
    # 3. PxM2 por operación
    df_pxm2 = df[['PxM2', 'operacion']].dropna()
    
    fig3 = px.box(
        df_pxm2,
        x='operacion',
        y='PxM2',
        title='💰 Precio por M² por Operación',
        labels={'PxM2': 'Precio por M² ($)', 'operacion': 'Operación'}
    )
    fig3.update_layout(height=500)
    
    # Generar HTML individual para cada gráfica
    html1 = pyo.plot(fig1, output_type='div', include_plotlyjs=False)
    html2 = pyo.plot(fig2, output_type='div', include_plotlyjs=False)
    html3 = pyo.plot(fig3, output_type='div', include_plotlyjs=False)
    
    # Calcular estadísticas
    total_props = len(df)
    props_validas = len(df.dropna(subset=['precio', 'area_m2']))
    total_colonias = df['Colonia'].nunique() if 'Colonia' in df.columns else 0
    ventas = len(df[df['operacion'] == 'Ven'])
    rentas = len(df[df['operacion'] == 'Ren'])
    precio_promedio = df['precio'].mean()
    
    # Plantilla HTML
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🏠 ESDATA Epsilon - Dashboard Interactivo</title>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 40px; 
            border-radius: 15px; 
            text-align: center; 
            margin-bottom: 30px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .stat-label {{
            color: #666;
            font-size: 1.1em;
        }}
        .chart-container {{ 
            background: white;
            margin: 30px 0; 
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .insights {{ 
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            font-size: 2.5em; 
            margin: 0 0 10px 0; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        h2 {{ 
            color: #667eea; 
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        h3 {{
            color: #555;
            font-size: 1.4em;
            margin-bottom: 15px;
        }}
        .subtitle {{
            font-size: 1.3em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .description {{
            opacity: 0.8;
            font-size: 1.1em;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 50px;
            padding: 30px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 ESDATA EPSILON</h1>
            <div class="subtitle">Análisis Inmobiliario Interactivo</div>
            <div class="description">Dashboard con gráficas dinámicas y análisis automático</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_props:,}</div>
                <div class="stat-label">Total Propiedades</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{props_validas:,}</div>
                <div class="stat-label">Registros Válidos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_colonias:,}</div>
                <div class="stat-label">Colonias</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${precio_promedio:,.0f}</div>
                <div class="stat-label">Precio Promedio</div>
            </div>
        </div>
        
        <div class="insights">
            <h3>💡 Resumen Ejecutivo</h3>
            <p><strong>📊 Distribución del Mercado:</strong></p>
            <ul>
                <li>{ventas:,} propiedades en venta ({ventas/total_props*100:.1f}%)</li>
                <li>{rentas:,} propiedades en renta ({rentas/total_props*100:.1f}%)</li>
                <li>Completitud de datos: {props_validas/total_props*100:.1f}%</li>
            </ul>
            <p><strong>🎯 Instrucciones de Uso:</strong></p>
            <p>Las gráficas son completamente interactivas. Puedes hacer zoom (click y arrastra), 
            ver detalles (hover con el mouse) y filtrar datos (click en la leyenda).</p>
        </div>
        
        <div class="chart-container">
            <h3>📊 Distribución de Precios por Operación</h3>
            <p>Explora la distribución de precios separada por ventas y rentas. Usa zoom para analizar rangos específicos.</p>
            {html1}
        </div>
        
        <div class="chart-container">
            <h3>📐 Relación entre Área y Precio</h3>
            <p>Analiza la correlación entre área de la propiedad y su precio. Los colores distinguen entre ventas y rentas.</p>
            {html2}
        </div>
        
        <div class="chart-container">
            <h3>💰 Precio por Metro Cuadrado</h3>
            <p>Compara el precio por m² entre ventas y rentas usando diagramas de caja para ver medianas y outliers.</p>
            {html3}
        </div>
        
        <div class="insights">
            <h3>🔍 Próximos Análisis Recomendados</h3>
            <ul>
                <li><strong>Análisis por Colonias:</strong> Identificar zonas con precios premium vs económicas</li>
                <li><strong>Detección de Outliers:</strong> Investigar propiedades con precios anómalos</li>
                <li><strong>Análisis Temporal:</strong> Evaluar tendencias de precios por período</li>
                <li><strong>Segmentación:</strong> Agrupar propiedades por características similares</li>
            </ul>
        </div>
        
        <div class="footer">
            <h3>🚀 Sistema ESDATA Epsilon</h3>
            <p>Dashboard generado automáticamente con análisis inteligente</p>
            <p>📅 Generado el: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    </div>
</body>
</html>
    """
    
    # Guardar archivo
    with open('dashboard_interactivo.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ Dashboard HTML generado exitosamente!")
    print("📁 Archivo: dashboard_interactivo.html")
    print("\n🎯 GRÁFICAS INCLUIDAS:")
    print("   1. 📊 Distribución de Precios (interactiva)")
    print("   2. 📐 Área vs Precio (scatter interactivo)")
    print("   3. 💰 PxM2 por Operación (box plots)")
    print("\n💡 Para usar:")
    print("   - Abre dashboard_interactivo.html en tu navegador")
    print("   - Usa zoom, hover y filtros en todas las gráficas")
    print("   - Las gráficas ahora se mostrarán correctamente")

if __name__ == "__main__":
    crear_dashboard_funcional()
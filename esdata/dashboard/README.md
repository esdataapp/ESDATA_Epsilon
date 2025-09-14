# Dashboard Estadísticas Inmobiliarias

Este módulo (independiente del pipeline core) provee visualizaciones interactivas sobre los artefactos ya generados en `N5_Resultados` y los CSV auxiliares creados por `generate_dashboard_data`.

## Instalación (entorno dedicado recomendado)
```powershell
python -m venv .venv_dashboard
.\.venv_dashboard\Scripts\Activate.ps1
pip install -r esdata/dashboard/requirements.txt
```
Si el entorno NO comparte el core y faltan pandas/numpy:
```powershell
pip install pandas numpy python-dotenv
```

## Ejecución
Generar primero los artefactos del periodo:
```powershell
python -m esdata.dashboard.generate_dashboard_data Sep25
```
Luego lanzar Streamlit:
```powershell
python -m streamlit run esdata/dashboard/app/app.py -- --periodo Sep25
```

## Estructura
```
esdata/dashboard/
  app/                  # Código Streamlit
  generate_dashboard_data.py
  requirements.txt
  README.md
```

## Dependencias Clave
- streamlit, plotly, pydeck: UI y mapas
- wordcloud: nubes de palabras
- seaborn/matplotlib: soporte adicional en algunas gráficas

## No incluido aquí
- Librerías de ingesta (psycopg2, SQLAlchemy)
- Librerías del pipeline geoespacial fuera de lo necesario para los CSV finales (se asume ya generados)

## Actualizaciones Futuras
- Materialized views integrables directo desde Supabase
- Cacheo selectivo (`st.cache_data`) para grandes periodos
- Modo multi-periodo comparativo

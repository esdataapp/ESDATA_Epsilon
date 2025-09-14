"""Utilidades centralizadas de rutas.
Contiene funciones únicas (sin duplicados) para evitar conflictos de análisis estático.
"""
from __future__ import annotations
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def periodo_actual() -> str:
    return datetime.now().strftime('%b%y')

def path_base(*parts: str) -> str:
    return os.path.join(BASE_DIR, *parts)

def ensure_dir(p: str) -> str:
    os.makedirs(p, exist_ok=True)
    return p

def path_input_base() -> str:
    return path_base('Base_de_Datos')

def path_consolidados() -> str:
    return path_base('N1_Tratamiento','Consolidados')

def path_geoloc() -> str:
    return path_base('N1_Tratamiento','Geolocalizacion')

def path_results_level(level: int) -> str:
    return path_base('N5_Resultados', f'Nivel_{level}','CSV')

def path_resultados_tablas_periodo(periodo: str) -> str:
    return ensure_dir(path_base('N5_Resultados','Nivel_1','CSV','Tablas', periodo))

def path_esperando(periodo: str) -> str:
    return ensure_dir(path_base('Datos_Filtrados','Esperando', periodo))

def path_eliminados(periodo: str) -> str:
    return ensure_dir(path_base('Datos_Filtrados','Eliminados', periodo))

def path_duplicados(periodo: str) -> str:
    return ensure_dir(path_base('Datos_Filtrados','Duplicados', periodo))

def path_estadistica_estudios(periodo: str) -> str:
    return ensure_dir(path_base('N2_Estadisticas','Estudios', periodo))

def path_estadistica_resultados(periodo: str) -> str:
    return ensure_dir(path_base('N2_Estadisticas','Resultados', periodo))

def path_estadistica_reportes(periodo: str) -> str:
    return ensure_dir(path_base('N2_Estadisticas','Reportes', periodo))

def path_colonias_branch(periodo: str, ciudad: str, oper: str, tipo: str) -> str:
    return ensure_dir(path_base('N1_Tratamiento','Consolidados','Colonias', ciudad, 'Venta' if oper=='Ven' else 'Renta', tipo, periodo))

def obtener_periodo_previo(periodo: str) -> str:
    try:
        dt = datetime.strptime(periodo, '%b%y')
    except ValueError:
        return periodo
    mes = dt.month - 1
    year = dt.year
    if mes == 0:
        mes = 12
        year -= 1
    prev = datetime(year, mes, 1)
    return prev.strftime('%b%y')

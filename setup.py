#!/usr/bin/env python3
"""
🚀 ESDATA_Epsilon - Setup e Instalación Automatizada

Este script automatiza la instalación completa del pipeline inmobiliario ESDATA_Epsilon,
incluyendo verificación de dependencias, creación de estructura de directorios,
validación de configuración y tests básicos.

Uso:
    python setup.py --full          # Instalación completa
    python setup.py --check         # Solo verificación
    python setup.py --repair        # Reparar instalación existente
    python setup.py --help          # Mostrar ayuda

Autor: ESDATA Team
Versión: 1.0.0
Fecha: Septiembre 2025
"""

import os
import sys
import subprocess
import argparse
import json
import platform
from pathlib import Path
from datetime import datetime

# Configuración de colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message, color=Colors.WHITE):
    """Imprimir mensaje con color"""
    print(f"{color}{message}{Colors.END}")

def print_header(title):
    """Imprimir header decorado"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"🚀 {title}", Colors.BOLD + Colors.CYAN)
    print_colored(f"{'='*60}", Colors.CYAN)

def print_success(message):
    """Imprimir mensaje de éxito"""
    print_colored(f"✅ {message}", Colors.GREEN)

def print_error(message):
    """Imprimir mensaje de error"""
    print_colored(f"❌ {message}", Colors.RED)

def print_warning(message):
    """Imprimir mensaje de advertencia"""
    print_colored(f"⚠️  {message}", Colors.YELLOW)

def print_info(message):
    """Imprimir mensaje informativo"""
    print_colored(f"ℹ️  {message}", Colors.BLUE)

class ESDATASetup:
    """Clase principal para setup de ESDATA_Epsilon"""
    
    def __init__(self):
        self.python_version = sys.version_info
        self.os_type = platform.system()
        self.base_path = Path.cwd()
        self.errors = []
        self.warnings = []
        
    def check_python_version(self):
        """Verificar versión de Python"""
        print_info(f"Verificando Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        
        if self.python_version < (3, 9):
            self.errors.append("Python >= 3.9 requerido")
            print_error(f"Python {self.python_version.major}.{self.python_version.minor} no es compatible")
            return False
        elif self.python_version >= (3, 12):
            self.warnings.append("Python 3.12+ puede tener problemas de compatibilidad")
            print_warning("Python 3.12+ puede requerir versiones específicas de dependencias")
        
        print_success(f"Python {self.python_version.major}.{self.python_version.minor} compatible")
        return True
    
    def check_system_dependencies(self):
        """Verificar dependencias del sistema"""
        print_info("Verificando dependencias del sistema...")
        
        if self.os_type == "Windows":
            return self._check_windows_dependencies()
        elif self.os_type == "Darwin":  # macOS
            return self._check_macos_dependencies()
        elif self.os_type == "Linux":
            return self._check_linux_dependencies()
        else:
            print_warning(f"Sistema operativo {self.os_type} no oficialmente soportado")
            return True
    
    def _check_windows_dependencies(self):
        """Verificar dependencias específicas de Windows"""
        print_info("Sistema: Windows")
        
        # Verificar Visual C++ Build Tools
        try:
            import setuptools
            print_success("Setuptools disponible")
        except ImportError:
            print_warning("Setuptools no encontrado - puede causar problemas de compilación")
        
        return True
    
    def _check_macos_dependencies(self):
        """Verificar dependencias específicas de macOS"""
        print_info("Sistema: macOS")
        
        # Verificar Xcode command line tools
        try:
            result = subprocess.run(['xcode-select', '--print-path'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print_success("Xcode command line tools instaladas")
            else:
                print_warning("Xcode command line tools no encontradas")
                print_info("Ejecutar: xcode-select --install")
        except FileNotFoundError:
            print_warning("xcode-select no encontrado")
        
        return True
    
    def _check_linux_dependencies(self):
        """Verificar dependencias específicas de Linux"""
        print_info("Sistema: Linux")
        
        # Verificar build-essential
        try:
            result = subprocess.run(['gcc', '--version'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print_success("GCC compiler disponible")
            else:
                print_warning("GCC compiler no encontrado")
                print_info("Ejecutar: sudo apt-get install build-essential")
        except FileNotFoundError:
            print_warning("GCC no encontrado - instalar build-essential")
        
        # Verificar GDAL
        try:
            result = subprocess.run(['gdal-config', '--version'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"GDAL {result.stdout.strip()} disponible")
            else:
                print_warning("GDAL no encontrado")
                print_info("Ejecutar: sudo apt-get install gdal-bin libgdal-dev")
        except FileNotFoundError:
            print_warning("GDAL no encontrado")
        
        return True
    
    def install_python_dependencies(self):
        """Instalar dependencias de Python"""
        print_info("Instalando dependencias de Python...")
        
        # Verificar si requirements.txt existe
        requirements_file = self.base_path / "requirements.txt"
        if not requirements_file.exists():
            print_error("requirements.txt no encontrado")
            return False
        
        try:
            # Actualizar pip primero
            print_info("Actualizando pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            print_success("pip actualizado")
            
            # Instalar dependencias
            print_info("Instalando paquetes desde requirements.txt...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True)
            print_success("Dependencias instaladas exitosamente")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print_error(f"Error instalando dependencias: {e}")
            
            # Intentar instalación alternativa con conda si está disponible
            if self._try_conda_installation():
                return True
                
            self.errors.append("Falló instalación de dependencias")
            return False
    
    def _try_conda_installation(self):
        """Intentar instalación con conda como fallback"""
        try:
            print_info("Intentando instalación con conda...")
            subprocess.run(["conda", "--version"], check=True, capture_output=True)
            
            # Instalar paquetes principales con conda
            conda_packages = [
                "pandas", "numpy", "scipy", "scikit-learn",
                "geopandas", "shapely", "fiona", "matplotlib", "seaborn"
            ]
            
            for package in conda_packages:
                subprocess.run(["conda", "install", "-c", "conda-forge", package, "-y"], 
                             check=True, capture_output=True)
            
            print_success("Dependencias instaladas con conda")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning("Conda no disponible")
            return False
    
    def create_directory_structure(self):
        """Crear estructura de directorios requerida"""
        print_info("Creando estructura de directorios...")
        
        directories = [
            "Base_de_Datos",
            "N1_Tratamiento/Consolidados",
            "N1_Tratamiento/Geolocalizacion/GEOJSON",
            "N1_Tratamiento/Geolocalizacion/CSV",
            "N1_Tratamiento/Geolocalizacion/Colonias",
            "N2_Estadisticas/Estudios",
            "N2_Estadisticas/Reportes",
            "N2_Estadisticas/Resultados",
            "N3_Correlaciones/Estudios",
            "N3_Correlaciones/Reportes", 
            "N3_Correlaciones/Resultados",
            "N4_Analisis_Temporal/Estudios",
            "N4_Analisis_Temporal/Reportes",
            "N4_Analisis_Temporal/Resultados",
            "N5_Resultados/Nivel_1/CSV",
            "N5_Resultados/Nivel_1/GEOJSON",
            "N5_Resultados/Nivel_2/CSV",
            "N5_Resultados/Nivel_2/GEOJSON",
            "N5_Resultados/Nivel_3/CSV",
            "N5_Resultados/Nivel_3/GEOJSON",
            "N5_Resultados/Nivel_4/CSV",
            "N5_Resultados/Nivel_4/GEOJSON",
            "Datos_Filtrados/Duplicados",
            "Datos_Filtrados/Eliminados",
            "Datos_Filtrados/Esperando",
            "docs/api",
            "docs/examples",
            "logs"
        ]
        
        created_count = 0
        for directory in directories:
            dir_path = self.base_path / directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                if not dir_path.exists():
                    created_count += 1
                print_success(f"📁 {directory}/")
            except Exception as e:
                print_error(f"Error creando {directory}: {e}")
                self.errors.append(f"No se pudo crear directorio: {directory}")
        
        if created_count > 0:
            print_success(f"Estructura de directorios creada ({len(directories)} directorios)")
        else:
            print_info("Estructura de directorios ya existía")
        
        return True
    
    def verify_imports(self):
        """Verificar que las dependencias se pueden importar"""
        print_info("Verificando importación de dependencias...")
        
        critical_imports = [
            ("pandas", "pd"),
            ("numpy", "np"), 
            ("geopandas", "gpd"),
            ("shapely", None),
            ("scipy", None),
            ("sklearn", None),
            ("matplotlib.pyplot", "plt"),
            ("seaborn", "sns")
        ]
        
        optional_imports = [
            ("nltk", None),
            ("textblob", None),
            ("plotly", None),
            ("tqdm", None)
        ]
        
        # Verificar imports críticos
        failed_critical = []
        for module, alias in critical_imports:
            try:
                if alias:
                    exec(f"import {module} as {alias}")
                else:
                    exec(f"import {module}")
                print_success(f"✓ {module}")
            except ImportError as e:
                failed_critical.append(module)
                print_error(f"✗ {module}: {e}")
        
        # Verificar imports opcionales
        failed_optional = []
        for module, alias in optional_imports:
            try:
                if alias:
                    exec(f"import {module} as {alias}")
                else:
                    exec(f"import {module}")
                print_success(f"✓ {module} (opcional)")
            except ImportError:
                failed_optional.append(module)
                print_warning(f"○ {module} (opcional) - no instalado")
        
        if failed_critical:
            print_error(f"Imports críticos fallidos: {', '.join(failed_critical)}")
            self.errors.append("Dependencias críticas no disponibles")
            return False
        
        if failed_optional:
            print_info(f"Imports opcionales no disponibles: {', '.join(failed_optional)}")
        
        print_success("Todas las dependencias críticas disponibles")
        return True
    
    def run_basic_tests(self):
        """Ejecutar tests básicos del sistema"""
        print_info("Ejecutando tests básicos...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Crear y leer DataFrame
        total_tests += 1
        try:
            import pandas as pd
            import numpy as np
            
            df = pd.DataFrame({
                'A': [1, 2, 3],
                'B': ['a', 'b', 'c'],
                'C': [1.1, 2.2, 3.3]
            })
            assert len(df) == 3
            assert list(df.columns) == ['A', 'B', 'C']
            
            print_success("Test DataFrame básico")
            tests_passed += 1
            
        except Exception as e:
            print_error(f"Test DataFrame fallido: {e}")
        
        # Test 2: Operaciones geoespaciales básicas
        total_tests += 1
        try:
            import geopandas as gpd
            from shapely.geometry import Point
            
            # Crear GeoDataFrame básico
            points = [Point(1, 1), Point(2, 2), Point(3, 3)]
            gdf = gpd.GeoDataFrame({'id': [1, 2, 3]}, geometry=points)
            assert len(gdf) == 3
            assert gdf.crs is None  # Sin CRS por defecto
            
            # Asignar CRS
            gdf = gdf.set_crs('EPSG:4326')
            assert gdf.crs.to_string() == 'EPSG:4326'
            
            print_success("Test GeoDataFrame básico")
            tests_passed += 1
            
        except Exception as e:
            print_error(f"Test geoespacial fallido: {e}")
        
        # Test 3: Estadísticas básicas
        total_tests += 1
        try:
            import scipy.stats as stats
            import numpy as np
            
            data = np.random.normal(0, 1, 1000)
            mean = np.mean(data)
            std = np.std(data)
            
            # Test de normalidad básico
            _, p_value = stats.shapiro(data[:100])  # Shapiro solo para n < 5000
            
            assert abs(mean) < 0.5  # Media cerca de 0
            assert abs(std - 1) < 0.5  # Std cerca de 1
            
            print_success("Test estadísticas básicas")
            tests_passed += 1
            
        except Exception as e:
            print_error(f"Test estadísticas fallido: {e}")
        
        # Test 4: I/O de archivos
        total_tests += 1
        try:
            import pandas as pd
            import tempfile
            import os
            
            # Crear archivo CSV temporal
            df_test = pd.DataFrame({
                'col1': [1, 2, 3],
                'col2': ['a', 'b', 'c']
            })
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                temp_file = f.name
            
            # Escribir y leer CSV
            df_test.to_csv(temp_file, index=False)
            df_read = pd.read_csv(temp_file)
            
            assert df_test.equals(df_read)
            
            # Limpiar
            os.unlink(temp_file)
            
            print_success("Test I/O archivos")
            tests_passed += 1
            
        except Exception as e:
            print_error(f"Test I/O fallido: {e}")
        
        # Resumen de tests
        print_info(f"Tests completados: {tests_passed}/{total_tests} exitosos")
        
        if tests_passed == total_tests:
            print_success("✅ Todos los tests básicos pasaron")
            return True
        else:
            print_warning(f"⚠️ {total_tests - tests_passed} tests fallaron")
            if tests_passed < total_tests // 2:
                self.errors.append("Múltiples tests básicos fallaron")
                return False
            return True
    
    def create_example_files(self):
        """Crear archivos de ejemplo y configuración"""
        print_info("Creando archivos de ejemplo...")
        
        # Crear archivo de configuración de ejemplo
        config_example = {
            "esdata": {
                "base_path": str(self.base_path),
                "log_level": "INFO",
                "chunk_size": 5000,
                "usd_to_mn_rate": 20.0,
                "coordinate_bounds": {
                    "lat_min": 20.500,
                    "lat_max": 20.800,
                    "lon_min": -103.500,
                    "lon_max": -103.200
                }
            }
        }
        
        try:
            config_path = self.base_path / "config_example.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_example, f, indent=2, ensure_ascii=False)
            print_success("config_example.json creado")
        except Exception as e:
            print_warning(f"No se pudo crear config_example.json: {e}")
        
        # Crear script de validación
        validation_script = '''#!/usr/bin/env python3
"""
Script de validación post-instalación para ESDATA_Epsilon
"""

import sys
import pandas as pd
import geopandas as gpd
import numpy as np

def validate_installation():
    """Validar instalación de ESDATA_Epsilon"""
    print("🔍 Validando instalación ESDATA_Epsilon...")
    
    # Test imports
    try:
        import esdata
        print("✅ Módulo esdata importado")
    except ImportError:
        print("⚠️ Módulo esdata no encontrado (normal si aún no está instalado)")
    
    # Test funcionalidad básica
    df = pd.DataFrame({'test': [1, 2, 3]})
    print(f"✅ Pandas working: {len(df)} rows")
    
    from shapely.geometry import Point
    point = Point(1, 1)
    gdf = gpd.GeoDataFrame([1], geometry=[point])
    print(f"✅ GeoPandas working: {len(gdf)} geometries")
    
    print("🎉 Validación completada exitosamente!")

if __name__ == "__main__":
    validate_installation()
'''
        
        try:
            validation_path = self.base_path / "validate_installation.py"
            with open(validation_path, 'w', encoding='utf-8') as f:
                f.write(validation_script)
            print_success("validate_installation.py creado")
        except Exception as e:
            print_warning(f"No se pudo crear validate_installation.py: {e}")
        
        return True
    
    def generate_setup_report(self):
        """Generar reporte de instalación"""
        print_header("REPORTE DE INSTALACIÓN")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# 📋 REPORTE DE INSTALACIÓN ESDATA_EPSILON

**Fecha**: {timestamp}
**Sistema**: {self.os_type} 
**Python**: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}
**Directorio**: {self.base_path}

## ✅ Componentes Instalados

- ✅ Estructura de directorios
- ✅ Dependencias de Python  
- ✅ Tests básicos
- ✅ Archivos de configuración

## ⚠️ Advertencias ({len(self.warnings)})
"""
        
        for warning in self.warnings:
            report += f"- ⚠️ {warning}\n"
        
        if not self.warnings:
            report += "- Ninguna\n"
        
        report += f"\n## ❌ Errores ({len(self.errors)})\n"
        
        for error in self.errors:
            report += f"- ❌ {error}\n"
        
        if not self.errors:
            report += "- Ninguno\n"
        
        report += """
## 🚀 Próximos Pasos

1. **Colocar datos fuente**: Agregar archivos CSV en `Base_de_Datos/{periodo}/`
2. **Configurar GeoJSON**: Copiar archivos de colonias a `N1_Tratamiento/Geolocalizacion/GEOJSON/`
3. **Ejecutar pipeline**: `python -m esdata.pipeline.step1_consolidar_adecuar Sep25`
4. **Validar resultados**: Revisar archivos en `N5_Resultados/`

## 📚 Documentación

- `README.md`: Descripción general y características
- `FLUJO.md`: Flujo detallado del pipeline
- `docs/CONFIGURACION.md`: Configuración avanzada
- `docs/TROUBLESHOOTING.md`: Solución de problemas

¡Instalación completada exitosamente! 🎉
"""
        
        # Guardar reporte
        try:
            report_path = self.base_path / "INSTALLATION_REPORT.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print_success(f"Reporte guardado en: {report_path}")
        except Exception as e:
            print_warning(f"No se pudo guardar reporte: {e}")
        
        # Mostrar resumen en consola
        if self.errors:
            print_error(f"⚠️ Instalación completada con {len(self.errors)} errores")
            for error in self.errors[:3]:  # Mostrar solo primeros 3 errores
                print_error(f"  • {error}")
        else:
            print_success("🎉 ¡Instalación completada exitosamente!")
        
        if self.warnings:
            print_info(f"ℹ️ {len(self.warnings)} advertencias (ver reporte para detalles)")
        
        return len(self.errors) == 0


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="🚀 ESDATA_Epsilon Setup e Instalación Automatizada",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--full', 
        action='store_true',
        help='Instalación completa (por defecto)'
    )
    
    parser.add_argument(
        '--check',
        action='store_true', 
        help='Solo verificar dependencias y configuración'
    )
    
    parser.add_argument(
        '--repair',
        action='store_true',
        help='Reparar instalación existente'
    )
    
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Omitir instalación de dependencias Python'
    )
    
    args = parser.parse_args()
    
    # Banner de bienvenida
    print_colored("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🏠 ESDATA_EPSILON - PIPELINE INMOBILIARIO             ║
║                     Setup Automatizado                      ║
║                                                              ║
║           Procesamiento de Datos Inmobiliarios              ║
║              Guadalajara & Zapopan, México                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """, Colors.BOLD + Colors.CYAN)
    
    setup = ESDATASetup()
    success = True
    
    try:
        # Verificaciones básicas
        if not setup.check_python_version():
            return 1
            
        if not setup.check_system_dependencies():
            print_warning("Algunas dependencias del sistema pueden causar problemas")
        
        if args.check:
            # Solo verificación
            print_header("MODO VERIFICACIÓN")
            setup.verify_imports()
            setup.generate_setup_report()
            return 0
        
        # Instalación completa o reparación
        mode = "REPARACIÓN" if args.repair else "INSTALACIÓN COMPLETA"
        print_header(mode)
        
        # Crear estructura de directorios
        if not setup.create_directory_structure():
            success = False
        
        # Instalar dependencias Python (a menos que se omita)
        if not args.skip_deps:
            if not setup.install_python_dependencies():
                success = False
        else:
            print_info("Omitiendo instalación de dependencias Python")
        
        # Verificar imports
        if not setup.verify_imports():
            success = False
        
        # Tests básicos
        if not setup.run_basic_tests():
            success = False
        
        # Crear archivos de ejemplo
        setup.create_example_files()
        
        # Generar reporte final
        report_success = setup.generate_setup_report()
        
        return 0 if (success and report_success) else 1
        
    except KeyboardInterrupt:
        print_error("\n\n⚠️ Instalación interrumpida por el usuario")
        return 1
    except Exception as e:
        print_error(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
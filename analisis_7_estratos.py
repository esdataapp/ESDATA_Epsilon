"""
ANÁLISIS ESTADÍSTICO ESTRATIFICADO POR VARIABLE
===============================================

Sistema especializado para análisis de estratificación con 7 niveles:
- Separación por operación (Venta/Renta)
- 7 estratos equitativos con promedio al centro
- Gráficas con cuadrantes y colores por estrato
- Distribución de frecuencias por estrato
- Box plots y outliers por estrato

Variables analizadas: precio, area_m2, PxM2

Autor: Sistema ESDATA_Epsilon
Fecha: Septiembre 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuración de matplotlib
plt.style.use('default')
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

class AnalizadorEstratos7Niveles:
    """Analizador con estratificación de 7 niveles por variable"""
    
    def __init__(self, archivo_csv):
        self.archivo = archivo_csv
        self.df = None
        self.df_venta = None
        self.df_renta = None
        self.colores_estratos = [
            '#FF0000',  # Rojo - Estrato 1 (Mínimo)
            '#FF8000',  # Naranja - Estrato 2  
            '#FFFF00',  # Amarillo - Estrato 3
            '#00FF00',  # Verde - Estrato 4 (PROMEDIO - CENTRO)
            '#00FFFF',  # Cian - Estrato 5
            '#0080FF',  # Azul - Estrato 6
            '#8000FF'   # Violeta - Estrato 7 (Máximo)
        ]
        
    def cargar_datos(self):
        """Cargar y preparar datos"""
        try:
            print("📂 Cargando datos para análisis de estratos...")
            self.df = pd.read_csv(self.archivo)
            
            # Convertir a numérico
            for col in ['area_m2', 'precio', 'PxM2']:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Separar por operación
            self.df_venta = self.df[self.df['operacion'] == 'Ven'].copy()
            self.df_renta = self.df[self.df['operacion'] == 'Ren'].copy()
            
            print(f"✅ Datos cargados:")
            print(f"   • Ventas: {len(self.df_venta):,}")
            print(f"   • Rentas: {len(self.df_renta):,}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def crear_estratos_7_niveles(self, serie, variable_nombre):
        """Crear 7 estratos equitativos con promedio al centro"""
        serie_limpia = serie.dropna()
        if len(serie_limpia) == 0:
            return None, None
        
        minimo = serie_limpia.min()
        maximo = serie_limpia.max()
        promedio = serie_limpia.mean()
        
        print(f"\n📊 ESTRATIFICACIÓN {variable_nombre.upper()}:")
        print(f"   • Mínimo: {float(minimo):,.2f}")
        print(f"   • Máximo: {float(maximo):,.2f}")
        print(f"   • Promedio: {float(promedio):,.2f}")
        
        # Crear 7 estratos con promedio al centro (estrato 4)
        # Estratos 1-3: desde mínimo hasta promedio
        # Estrato 4: centrado en el promedio
        # Estratos 5-7: desde promedio hasta máximo
        
        rango_inferior = promedio - minimo
        rango_superior = maximo - promedio
        
        # Definir límites de estratos
        limites = [
            minimo,
            minimo + (rango_inferior * 1/3),
            minimo + (rango_inferior * 2/3),
            promedio - (rango_inferior * 0.1),  # Inicio estrato central
            promedio + (rango_superior * 0.1),  # Fin estrato central
            promedio + (rango_superior * 1/3),
            promedio + (rango_superior * 2/3),
            maximo
        ]
        
        # Crear etiquetas de estratos
        estratos_info = []
        for i in range(7):
            nombre = f"Estrato {i+1}"
            if i == 3:  # Estrato central (4)
                nombre += " (PROMEDIO)"
            
            limite_inf = limites[i]
            limite_sup = limites[i+1]
            
            estratos_info.append({
                'numero': i+1,
                'nombre': nombre,
                'limite_inf': limite_inf,
                'limite_sup': limite_sup,
                'color': self.colores_estratos[i]
            })
            
            print(f"   • {nombre}: {limite_inf:,.0f} - {limite_sup:,.0f}")
        
        # Asignar estrato a cada valor
        estratos = pd.cut(serie_limpia, bins=limites, labels=[f"E{i+1}" for i in range(7)], include_lowest=True)
        
        return estratos, estratos_info
    
    def analizar_variable_completa(self, variable):
        """Análisis completo de una variable con 7 estratos"""
        print(f"\n🎯 ANÁLISIS COMPLETO: {variable.upper()}")
        print("="*60)
        
        # Analizar por operación
        for operacion, df_op in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df_op is None or len(df_op) == 0:
                continue
                
            print(f"\n📈 {operacion} - {variable.upper()}")
            print("-"*40)
            
            # Limpiar datos
            df_limpio = df_op[[variable, 'area_m2']].dropna()
            if len(df_limpio) == 0:
                continue
            
            # Crear estratos
            estratos, estratos_info = self.crear_estratos_7_niveles(df_limpio[variable], variable)
            if estratos is None:
                continue
            
            # Añadir estratos al dataframe
            df_limpio = df_limpio.copy()
            df_limpio['estrato'] = estratos
            df_limpio['estrato_numero'] = estratos.cat.codes + 1
            
            # Crear todas las gráficas
            self._crear_scatter_cuadrantes(df_limpio, variable, operacion, estratos_info)
            self._crear_distribucion_frecuencia(df_limpio, variable, operacion, estratos_info)
            self._crear_boxplot_outliers(df_limpio, variable, operacion, estratos_info)
    
    def _crear_scatter_cuadrantes(self, df_limpio, variable, operacion, estratos_info):
        """Crear scatter plot con cuadrantes y colores por estrato"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Calcular promedios para líneas rojas
        promedio_x = df_limpio['area_m2'].mean()
        promedio_y = df_limpio[variable].mean()
        
        # Crear scatter plot coloreado por estrato
        for i, estrato_info in enumerate(estratos_info):
            estrato_data = df_limpio[df_limpio['estrato_numero'] == i+1]
            if len(estrato_data) > 0:
                ax.scatter(estrato_data['area_m2'], estrato_data[variable], 
                         c=estrato_info['color'], alpha=0.6, s=20,
                         label=f"{estrato_info['nombre']} ({len(estrato_data)})")
        
        # Líneas rojas en los promedios (creando 4 cuadrantes)
        ax.axvline(x=promedio_x, color='red', linewidth=2, linestyle='--', 
                  label=f'Promedio Área: {promedio_x:.0f} m²')
        ax.axhline(y=promedio_y, color='red', linewidth=2, linestyle='--',
                  label=f'Promedio {variable}: {promedio_y:,.0f}')
        
        # Configurar ejes con 7 estratos
        area_min, area_max = df_limpio['area_m2'].min(), df_limpio['area_m2'].max()
        var_min, var_max = df_limpio[variable].min(), df_limpio[variable].max()
        
        # Crear ticks para 7 estratos en cada eje
        area_ticks = np.linspace(area_min, area_max, 8)  # 8 ticks para 7 estratos
        var_ticks = np.linspace(var_min, var_max, 8)
        
        ax.set_xticks(area_ticks)
        ax.set_yticks(var_ticks)
        ax.set_xticklabels([f'{tick:.0f}' for tick in area_ticks], rotation=45)
        ax.set_yticklabels([f'{tick:,.0f}' for tick in var_ticks])
        
        # Etiquetas y título
        ax.set_xlabel('Área m² (7 Estratos)', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{variable.upper()} (7 Estratos)', fontsize=12, fontweight='bold')
        ax.set_title(f'📊 SCATTER PLOT CON CUADRANTES - {variable.upper()} ({operacion})\n'
                    f'Líneas rojas: Promedio área={promedio_x:.0f}m², promedio {variable}={promedio_y:,.0f}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Leyenda
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'scatter_cuadrantes_{variable}_{operacion.lower()}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Análisis de cuadrantes
        self._analizar_cuadrantes(df_limpio, variable, operacion, promedio_x, promedio_y)
    
    def _crear_distribucion_frecuencia(self, df_limpio, variable, operacion, estratos_info):
        """Crear histograma de distribución de frecuencias por estrato"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Histograma general con colores por estrato
        for i, estrato_info in enumerate(estratos_info):
            estrato_data = df_limpio[df_limpio['estrato_numero'] == i+1][variable]
            if len(estrato_data) > 0:
                ax1.hist(estrato_data, bins=20, alpha=0.7, color=estrato_info['color'],
                        label=f"{estrato_info['nombre']} ({len(estrato_data)})")
        
        promedio = df_limpio[variable].mean()
        ax1.axvline(x=promedio, color='red', linewidth=3, linestyle='--',
                   label=f'Promedio: {promedio:,.0f}')
        
        ax1.set_xlabel(f'{variable.upper()}', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frecuencia', fontsize=12, fontweight='bold')
        ax1.set_title(f'📊 DISTRIBUCIÓN DE FRECUENCIAS\n{variable.upper()} - {operacion}', 
                     fontsize=14, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # Gráfico de barras por estrato
        estratos_nombres = [info['nombre'] for info in estratos_info]
        estratos_counts = [len(df_limpio[df_limpio['estrato_numero'] == i+1]) for i in range(7)]
        colores = [info['color'] for info in estratos_info]
        
        bars = ax2.bar(range(7), estratos_counts, color=colores, alpha=0.7)
        ax2.set_xlabel('Estratos', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Cantidad de Propiedades', fontsize=12, fontweight='bold')
        ax2.set_title(f'📊 CANTIDAD POR ESTRATO\n{variable.upper()} - {operacion}', 
                     fontsize=14, fontweight='bold')
        ax2.set_xticks(range(7))
        ax2.set_xticklabels([f'E{i+1}' for i in range(7)], rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Añadir valores en las barras
        for bar, count in zip(bars, estratos_counts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{count:,}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'distribucion_frecuencia_{variable}_{operacion.lower()}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def _crear_boxplot_outliers(self, df_limpio, variable, operacion, estratos_info):
        """Crear box plot y análisis de outliers por estrato"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Box plot por estrato
        datos_estratos = []
        labels_estratos = []
        colores_box = []
        
        outliers_por_estrato = []
        
        for i, estrato_info in enumerate(estratos_info):
            estrato_data = df_limpio[df_limpio['estrato_numero'] == i+1][variable]
            if len(estrato_data) > 0:
                datos_estratos.append(estrato_data.values)
                labels_estratos.append(f"E{i+1}")
                colores_box.append(estrato_info['color'])
                
                # Detectar outliers
                Q1 = estrato_data.quantile(0.25)
                Q3 = estrato_data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = estrato_data[(estrato_data < Q1 - 1.5 * IQR) | 
                                       (estrato_data > Q3 + 1.5 * IQR)]
                outliers_por_estrato.append(len(outliers))
        
        if datos_estratos:
            bp = ax1.boxplot(datos_estratos, labels=labels_estratos, patch_artist=True)
            
            # Colorear cajas
            for patch, color in zip(bp['boxes'], colores_box):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax1.set_xlabel('Estratos', fontsize=12, fontweight='bold')
            ax1.set_ylabel(f'{variable.upper()}', fontsize=12, fontweight='bold')
            ax1.set_title(f'📦 BOX PLOT POR ESTRATO - {variable.upper()} ({operacion})', 
                         fontsize=14, fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3)
        
        # Gráfico de outliers por estrato
        if outliers_por_estrato:
            bars = ax2.bar(range(len(labels_estratos)), outliers_por_estrato, 
                          color=colores_box[:len(labels_estratos)], alpha=0.7)
            
            ax2.set_xlabel('Estratos', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Cantidad de Outliers', fontsize=12, fontweight='bold')
            ax2.set_title(f'🚨 OUTLIERS POR ESTRATO - {variable.upper()} ({operacion})', 
                         fontsize=14, fontweight='bold', pad=20)
            ax2.set_xticks(range(len(labels_estratos)))
            ax2.set_xticklabels(labels_estratos)
            ax2.grid(True, alpha=0.3)
            
            # Añadir valores en las barras
            for bar, count in zip(bars, outliers_por_estrato):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{count}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'boxplot_outliers_{variable}_{operacion.lower()}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Imprimir estadísticas de outliers
        self._imprimir_estadisticas_outliers(variable, operacion, labels_estratos, outliers_por_estrato)
    
    def _analizar_cuadrantes(self, df_limpio, variable, operacion, promedio_x, promedio_y):
        """Analizar distribución en 4 cuadrantes"""
        print(f"\n🎯 ANÁLISIS DE CUADRANTES - {variable.upper()} ({operacion})")
        print("-"*50)
        
        # Definir cuadrantes
        cuadrante_1 = df_limpio[(df_limpio['area_m2'] >= promedio_x) & 
                                (df_limpio[variable] >= promedio_y)]  # Alta área, alto precio
        cuadrante_2 = df_limpio[(df_limpio['area_m2'] < promedio_x) & 
                                (df_limpio[variable] >= promedio_y)]   # Baja área, alto precio
        cuadrante_3 = df_limpio[(df_limpio['area_m2'] < promedio_x) & 
                                (df_limpio[variable] < promedio_y)]    # Baja área, bajo precio
        cuadrante_4 = df_limpio[(df_limpio['area_m2'] >= promedio_x) & 
                                (df_limpio[variable] < promedio_y)]   # Alta área, bajo precio
        
        total = len(df_limpio)
        
        print(f"📊 Cuadrante 1 (Alta área + Alto {variable}): {len(cuadrante_1):,} ({len(cuadrante_1)/total*100:.1f}%)")
        print(f"📊 Cuadrante 2 (Baja área + Alto {variable}): {len(cuadrante_2):,} ({len(cuadrante_2)/total*100:.1f}%)")
        print(f"📊 Cuadrante 3 (Baja área + Bajo {variable}): {len(cuadrante_3):,} ({len(cuadrante_3)/total*100:.1f}%)")
        print(f"📊 Cuadrante 4 (Alta área + Bajo {variable}): {len(cuadrante_4):,} ({len(cuadrante_4)/total*100:.1f}%)")
        
        # Identificar cuadrante dominante
        cuadrantes = [
            ("Alta área + Alto precio", len(cuadrante_1)),
            ("Baja área + Alto precio", len(cuadrante_2)),
            ("Baja área + Bajo precio", len(cuadrante_3)),
            ("Alta área + Bajo precio", len(cuadrante_4))
        ]
        
        cuadrante_dominante = max(cuadrantes, key=lambda x: x[1])
        print(f"\n🏆 Cuadrante dominante: {cuadrante_dominante[0]} ({cuadrante_dominante[1]:,} propiedades)")
    
    def _imprimir_estadisticas_outliers(self, variable, operacion, labels_estratos, outliers_por_estrato):
        """Imprimir estadísticas de outliers"""
        print(f"\n🚨 ESTADÍSTICAS DE OUTLIERS - {variable.upper()} ({operacion})")
        print("-"*60)
        
        total_outliers = sum(outliers_por_estrato)
        for i, (label, count) in enumerate(zip(labels_estratos, outliers_por_estrato)):
            pct = count / total_outliers * 100 if total_outliers > 0 else 0
            print(f"   • {label}: {count:,} outliers ({pct:.1f}% del total)")
        
        print(f"\n📈 Total de outliers: {total_outliers:,}")
        print("-"*60)
    
    def ejecutar_analisis_completo(self):
        """Ejecutar análisis completo para todas las variables"""
        print("🏠 ANÁLISIS DE ESTRATIFICACIÓN 7 NIVELES")
        print("="*60)
        
        if not self.cargar_datos():
            return False
        
        variables = ['precio', 'area_m2', 'PxM2']
        
        for variable in variables:
            self.analizar_variable_completa(variable)
        
        print("\n✅ ANÁLISIS COMPLETO TERMINADO")
        print("📁 Archivos generados por variable y operación:")
        print("   - scatter_cuadrantes_[variable]_[operacion].png")
        print("   - distribucion_frecuencia_[variable]_[operacion].png")
        print("   - boxplot_outliers_[variable]_[operacion].png")
        
        return True


def main():
    """Función principal"""
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    
    analizador = AnalizadorEstratos7Niveles(archivo)
    analizador.ejecutar_analisis_completo()


if __name__ == "__main__":
    main()
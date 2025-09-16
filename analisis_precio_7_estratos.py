"""
ANÁLISIS ESTADÍSTICO DE LA VARIABLE PRECIO CON 7 ESTRATOS
=========================================================

Análisis especializado para la variable PRECIO con:
- Separación por operación (Venta/Renta)
- 7 estratos equitativos con promedio al centro (estrato 4)
- Scatter plot con cuadrantes (líneas rojas en promedios)
- Distribución de frecuencias por estrato
- Box plots y outliers por estrato
- Análisis de cuadrantes detallado

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

class AnalizadorPrecio7Estratos:
    """Analizador especializado para PRECIO con 7 estratos"""
    
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
            print("📂 Cargando datos para análisis de PRECIO...")
            self.df = pd.read_csv(self.archivo)
            
            # Convertir a numérico
            for col in ['area_m2', 'precio', 'PxM2']:
                if col in self.df.columns:
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
    
    def crear_estratos_precio(self, df_operacion, operacion_nombre):
        """Crear 7 estratos equitativos para PRECIO con promedio al centro"""
        
        # Limpiar datos
        df_limpio = df_operacion[['precio', 'area_m2']].dropna()
        if len(df_limpio) == 0:
            return None, None, None
        
        precio_serie = df_limpio['precio']
        
        minimo = precio_serie.min()
        maximo = precio_serie.max()
        promedio = precio_serie.mean()
        
        print(f"\n📊 ESTRATIFICACIÓN PRECIO - {operacion_nombre}:")
        print(f"   • Mínimo: ${minimo:,.2f}")
        print(f"   • Máximo: ${maximo:,.2f}")
        print(f"   • Promedio: ${promedio:,.2f}")
        
        # Crear 7 estratos con promedio al centro (estrato 4)
        # Estratos 1-3: desde mínimo hasta promedio (3 estratos)
        # Estrato 4: centrado alrededor del promedio
        # Estratos 5-7: desde promedio hasta máximo (3 estratos)
        
        # Calcular rangos para cada lado del promedio
        rango_inferior = (promedio - minimo) / 3.5  # Para estratos 1-3 y parte del 4
        rango_superior = (maximo - promedio) / 3.5  # Para estratos 5-7 y parte del 4
        
        # Definir límites de estratos de forma monotónica
        limites = [
            minimo,
            minimo + rango_inferior,         # Fin E1
            minimo + 2 * rango_inferior,     # Fin E2
            minimo + 3 * rango_inferior,     # Fin E3
            promedio + rango_superior,       # Fin E4 (estrato central)
            promedio + 2 * rango_superior,   # Fin E5
            promedio + 3 * rango_superior,   # Fin E6
            maximo                           # Fin E7
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
            
            print(f"   • {nombre}: ${limite_inf:,.0f} - ${limite_sup:,.0f}")
        
        # Asignar estrato a cada valor
        estratos = pd.cut(precio_serie, bins=limites, labels=[f"E{i+1}" for i in range(7)], include_lowest=True)
        
        # Añadir estratos al dataframe
        df_limpio = df_limpio.copy()
        df_limpio['estrato'] = estratos
        df_limpio['estrato_numero'] = estratos.cat.codes + 1
        
        return df_limpio, estratos_info, promedio
    
    def crear_scatter_cuadrantes(self, df_limpio, operacion, estratos_info, promedio_precio):
        """Crear scatter plot con cuadrantes y colores por estrato"""
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # Calcular promedio de área
        promedio_area = df_limpio['area_m2'].mean()
        
        # Crear scatter plot coloreado por estrato
        for i, estrato_info in enumerate(estratos_info):
            estrato_data = df_limpio[df_limpio['estrato_numero'] == i+1]
            if len(estrato_data) > 0:
                ax.scatter(estrato_data['area_m2'], estrato_data['precio'], 
                         c=estrato_info['color'], alpha=0.6, s=25,
                         label=f"{estrato_info['nombre']} ({len(estrato_data):,})")
        
        # Líneas rojas en los promedios (creando 4 cuadrantes)
        ax.axvline(x=promedio_area, color='red', linewidth=3, linestyle='--', 
                  label=f'Promedio Área: {promedio_area:.0f} m²')
        ax.axhline(y=promedio_precio, color='red', linewidth=3, linestyle='--',
                  label=f'Promedio Precio: ${promedio_precio:,.0f}')
        
        # Configurar ejes
        area_min, area_max = df_limpio['area_m2'].min(), df_limpio['area_m2'].max()
        precio_min, precio_max = df_limpio['precio'].min(), df_limpio['precio'].max()
        
        # Crear ticks para 7 estratos en cada eje
        area_ticks = np.linspace(area_min, area_max, 8)
        precio_ticks = np.linspace(precio_min, precio_max, 8)
        
        ax.set_xticks(area_ticks)
        ax.set_yticks(precio_ticks)
        ax.set_xticklabels([f'{tick:.0f}' for tick in area_ticks])
        
        # Formatear etiquetas de precio
        precio_labels = []
        for tick in precio_ticks:
            if tick >= 1000000:
                precio_labels.append(f'${tick/1000000:.1f}M')
            else:
                precio_labels.append(f'${tick:,.0f}')
        ax.set_yticklabels(precio_labels)
        
        # Etiquetas y título
        ax.set_xlabel('Área m² (7 Estratos Equitativos)', fontsize=12, fontweight='bold')
        ax.set_ylabel('PRECIO (7 Estratos Equitativos)', fontsize=12, fontweight='bold')
        ax.set_title(f'📊 SCATTER PLOT CON CUADRANTES - PRECIO ({operacion})\n'
                    f'Líneas rojas crean 4 cuadrantes: Área promedio = {promedio_area:.0f}m², Precio promedio = ${promedio_precio:,.0f}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Leyenda
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'scatter_precio_cuadrantes_{operacion.lower()}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Análisis de cuadrantes
        self._analizar_cuadrantes_precio(df_limpio, operacion, promedio_area, promedio_precio)
    
    def crear_distribucion_frecuencia(self, df_limpio, operacion, estratos_info):
        """Crear histograma y distribución por estratos"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # Histograma general con colores por estrato
        for i, estrato_info in enumerate(estratos_info):
            estrato_data = df_limpio[df_limpio['estrato_numero'] == i+1]['precio']
            if len(estrato_data) > 0:
                ax1.hist(estrato_data, bins=25, alpha=0.7, color=estrato_info['color'],
                        label=f"{estrato_info['nombre']} ({len(estrato_data):,})")
        
        promedio = df_limpio['precio'].mean()
        ax1.axvline(x=promedio, color='red', linewidth=3, linestyle='--',
                   label=f'Promedio: ${promedio:,.0f}')
        
        ax1.set_xlabel('PRECIO', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frecuencia', fontsize=12, fontweight='bold')
        ax1.set_title(f'📊 DISTRIBUCIÓN DE FRECUENCIAS - PRECIO\n{operacion} ({len(df_limpio):,} propiedades)', 
                     fontsize=14, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # Formatear eje X de precios
        ax1.ticklabel_format(style='plain', axis='x')
        
        # Gráfico de barras por estrato
        estratos_nombres = [f"E{i+1}" for i in range(7)]
        estratos_counts = [len(df_limpio[df_limpio['estrato_numero'] == i+1]) for i in range(7)]
        colores = [info['color'] for info in estratos_info]
        
        bars = ax2.bar(range(7), estratos_counts, color=colores, alpha=0.8, edgecolor='black', linewidth=1)
        ax2.set_xlabel('Estratos de PRECIO', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Cantidad de Propiedades', fontsize=12, fontweight='bold')
        ax2.set_title(f'📊 PROPIEDADES POR ESTRATO - PRECIO\n{operacion}', 
                     fontsize=14, fontweight='bold')
        ax2.set_xticks(range(7))
        ax2.set_xticklabels(estratos_nombres)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Añadir valores en las barras
        for bar, count in zip(bars, estratos_counts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{count:,}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f'distribucion_precio_{operacion.lower()}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def crear_boxplot_outliers(self, df_limpio, operacion, estratos_info):
        """Crear box plot y análisis de outliers por estrato"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Box plot por estrato
        datos_estratos = []
        labels_estratos = []
        colores_box = []
        outliers_por_estrato = []
        
        for i, estrato_info in enumerate(estratos_info):
            estrato_data = df_limpio[df_limpio['estrato_numero'] == i+1]['precio']
            if len(estrato_data) > 0:
                datos_estratos.append(estrato_data.values)
                labels_estratos.append(f"E{i+1}")
                colores_box.append(estrato_info['color'])
                
                # Detectar outliers usando IQR
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
                patch.set_edgecolor('black')
                patch.set_linewidth(1)
            
            ax1.set_xlabel('Estratos de PRECIO', fontsize=12, fontweight='bold')
            ax1.set_ylabel('PRECIO', fontsize=12, fontweight='bold')
            ax1.set_title(f'📦 BOX PLOT POR ESTRATO - PRECIO ({operacion})\n'
                         f'Cada caja representa la distribución de precios en su estrato', 
                         fontsize=14, fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3)
            ax1.ticklabel_format(style='plain', axis='y')
        
        # Gráfico de outliers por estrato
        if outliers_por_estrato:
            bars = ax2.bar(range(len(labels_estratos)), outliers_por_estrato, 
                          color=colores_box[:len(labels_estratos)], alpha=0.8, 
                          edgecolor='black', linewidth=1)
            
            ax2.set_xlabel('Estratos de PRECIO', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Cantidad de Outliers', fontsize=12, fontweight='bold')
            ax2.set_title(f'🚨 OUTLIERS POR ESTRATO - PRECIO ({operacion})\n'
                         f'Total outliers: {sum(outliers_por_estrato):,}', 
                         fontsize=14, fontweight='bold', pad=20)
            ax2.set_xticks(range(len(labels_estratos)))
            ax2.set_xticklabels(labels_estratos)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Añadir valores en las barras
            for bar, count in zip(bars, outliers_por_estrato):
                height = bar.get_height()
                if height > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{count}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'boxplot_precio_{operacion.lower()}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Imprimir estadísticas
        self._imprimir_estadisticas_outliers(operacion, labels_estratos, outliers_por_estrato)
    
    def _analizar_cuadrantes_precio(self, df_limpio, operacion, promedio_area, promedio_precio):
        """Analizar distribución en 4 cuadrantes para PRECIO"""
        print(f"\n🎯 ANÁLISIS DE CUADRANTES - PRECIO ({operacion})")
        print("-"*55)
        
        # Definir cuadrantes
        cuadrante_1 = df_limpio[(df_limpio['area_m2'] >= promedio_area) & 
                                (df_limpio['precio'] >= promedio_precio)]  # Alta área, alto precio
        cuadrante_2 = df_limpio[(df_limpio['area_m2'] < promedio_area) & 
                                (df_limpio['precio'] >= promedio_precio)]   # Baja área, alto precio
        cuadrante_3 = df_limpio[(df_limpio['area_m2'] < promedio_area) & 
                                (df_limpio['precio'] < promedio_precio)]    # Baja área, bajo precio
        cuadrante_4 = df_limpio[(df_limpio['area_m2'] >= promedio_area) & 
                                (df_limpio['precio'] < promedio_precio)]   # Alta área, bajo precio
        
        total = len(df_limpio)
        
        print(f"📊 Cuadrante 1 (Alta área + Alto precio): {len(cuadrante_1):,} ({len(cuadrante_1)/total*100:.1f}%)")
        print(f"📊 Cuadrante 2 (Baja área + Alto precio): {len(cuadrante_2):,} ({len(cuadrante_2)/total*100:.1f}%)")
        print(f"📊 Cuadrante 3 (Baja área + Bajo precio): {len(cuadrante_3):,} ({len(cuadrante_3)/total*100:.1f}%)")
        print(f"📊 Cuadrante 4 (Alta área + Bajo precio): {len(cuadrante_4):,} ({len(cuadrante_4)/total*100:.1f}%)")
        
        # Identificar cuadrante dominante
        cuadrantes = [
            ("Alta área + Alto precio", len(cuadrante_1)),
            ("Baja área + Alto precio", len(cuadrante_2)),
            ("Baja área + Bajo precio", len(cuadrante_3)),
            ("Alta área + Bajo precio", len(cuadrante_4))
        ]
        
        cuadrante_dominante = max(cuadrantes, key=lambda x: x[1])
        print(f"\n🏆 Cuadrante dominante: {cuadrante_dominante[0]} ({cuadrante_dominante[1]:,} propiedades)")
        
        # Análisis adicional de precios promedio por cuadrante
        print(f"\n💰 PRECIOS PROMEDIO POR CUADRANTE:")
        if len(cuadrante_1) > 0:
            print(f"   • Cuadrante 1: ${cuadrante_1['precio'].mean():,.0f}")
        if len(cuadrante_2) > 0:
            print(f"   • Cuadrante 2: ${cuadrante_2['precio'].mean():,.0f}")
        if len(cuadrante_3) > 0:
            print(f"   • Cuadrante 3: ${cuadrante_3['precio'].mean():,.0f}")
        if len(cuadrante_4) > 0:
            print(f"   • Cuadrante 4: ${cuadrante_4['precio'].mean():,.0f}")
    
    def _imprimir_estadisticas_outliers(self, operacion, labels_estratos, outliers_por_estrato):
        """Imprimir estadísticas detalladas de outliers"""
        print(f"\n🚨 ESTADÍSTICAS DE OUTLIERS - PRECIO ({operacion})")
        print("-"*60)
        
        total_outliers = sum(outliers_por_estrato)
        for i, (label, count) in enumerate(zip(labels_estratos, outliers_por_estrato)):
            pct = count / total_outliers * 100 if total_outliers > 0 else 0
            print(f"   • {label}: {count:,} outliers ({pct:.1f}% del total)")
        
        print(f"\n📈 Total de outliers: {total_outliers:,}")
        print("-"*60)
    
    def analizar_precio_completo(self):
        """Análisis completo de la variable PRECIO"""
        print("🏠 ANÁLISIS COMPLETO: VARIABLE PRECIO")
        print("="*60)
        
        if not self.cargar_datos():
            return False
        
        # Analizar por operación
        for operacion, df_op in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df_op is None or len(df_op) == 0:
                continue
                
            print(f"\n🎯 ANÁLISIS DE {operacion}")
            print("="*40)
            
            # Crear estratos
            df_limpio, estratos_info, promedio_precio = self.crear_estratos_precio(df_op, operacion)
            if df_limpio is None:
                continue
            
            # Crear todas las gráficas
            self.crear_scatter_cuadrantes(df_limpio, operacion, estratos_info, promedio_precio)
            self.crear_distribucion_frecuencia(df_limpio, operacion, estratos_info)
            self.crear_boxplot_outliers(df_limpio, operacion, estratos_info)
        
        print("\n✅ ANÁLISIS DE PRECIO COMPLETADO")
        print("📁 Archivos generados:")
        print("   - scatter_precio_cuadrantes_venta.png")
        print("   - scatter_precio_cuadrantes_renta.png")
        print("   - distribucion_precio_venta.png")
        print("   - distribucion_precio_renta.png")
        print("   - boxplot_precio_venta.png")
        print("   - boxplot_precio_renta.png")
        
        return True


def main():
    """Función principal"""
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    
    analizador = AnalizadorPrecio7Estratos(archivo)
    analizador.analizar_precio_completo()


if __name__ == "__main__":
    main()
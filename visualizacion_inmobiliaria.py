"""
VISUALIZACIÓN AVANZADA DE DATOS INMOBILIARIOS
================================================

Script completo para análisis visual de propiedades inmobiliarias con:
- Análisis globales por operación (Venta/Renta)
- Estratificación por área, precio y PxM2
- Detección visual de outliers
- Gráficas interactivas y estáticas

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

# Configuración de estilo
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class VisualizadorInmobiliario:
    """
    Clase principal para visualización de datos inmobiliarios
    """
    
    def __init__(self, archivo_csv):
        """
        Inicializa el visualizador
        
        Args:
            archivo_csv: Ruta al archivo 3a.Consolidado_Num_Sep25.csv
        """
        self.archivo = archivo_csv
        self.df = None
        self.df_venta = None
        self.df_renta = None
        
        # Configuración de estratos
        self.estratos_config = {
            'area_m2': {
                'bins': [0, 50, 80, 120, 200, 500, np.inf],
                'labels': ['0-50m²', '50-80m²', '80-120m²', '120-200m²', '200-500m²', '500m²+']
            },
            'precio': {
                'venta': {
                    'bins': [0, 1000000, 2500000, 5000000, 10000000, 25000000, np.inf],
                    'labels': ['<1M', '1-2.5M', '2.5-5M', '5-10M', '10-25M', '25M+']
                },
                'renta': {
                    'bins': [0, 8000, 15000, 25000, 40000, 80000, np.inf],
                    'labels': ['<8K', '8-15K', '15-25K', '25-40K', '40-80K', '80K+']
                }
            },
            'PxM2': {
                'venta': {
                    'bins': [0, 15000, 25000, 35000, 50000, 80000, np.inf],
                    'labels': ['<15K', '15-25K', '25-35K', '35-50K', '50-80K', '80K+']
                },
                'renta': {
                    'bins': [0, 80, 120, 180, 250, 400, np.inf],
                    'labels': ['<80', '80-120', '120-180', '180-250', '250-400', '400+']
                }
            }
        }
    
    def cargar_datos(self):
        """Carga y prepara los datos"""
        print("🔄 Cargando datos...")
        
        try:
            self.df = pd.read_csv(self.archivo)
            print(f"✅ Datos cargados: {len(self.df):,} registros")
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
            
        # Convertir a numérico
        numeric_cols = ['area_m2', 'precio', 'PxM2']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Separar por operación
        self.df_venta = self.df[self.df['operacion'].isin(['Ven', 'venta', 'Venta'])].copy()
        self.df_renta = self.df[self.df['operacion'].isin(['Ren', 'renta', 'Renta'])].copy()
        
        print(f"📊 Venta: {len(self.df_venta):,} | Renta: {len(self.df_renta):,}")
        
        # Crear estratos
        self._crear_estratos()
        
        return True
    
    def _crear_estratos(self):
        """Crea las columnas de estratificación"""
        print("🔄 Creando estratos...")
        
        for df_name, df in [('venta', self.df_venta), ('renta', self.df_renta)]:
            if df is None or len(df) == 0:
                continue
                
            # Estratos de área (iguales para venta y renta)
            df['estrato_area'] = pd.cut(
                df['area_m2'], 
                bins=self.estratos_config['area_m2']['bins'],
                labels=self.estratos_config['area_m2']['labels'],
                include_lowest=True
            )
            
            # Estratos de precio (diferentes para venta/renta)
            config_precio = self.estratos_config['precio'][df_name]
            df['estrato_precio'] = pd.cut(
                df['precio'],
                bins=config_precio['bins'],
                labels=config_precio['labels'],
                include_lowest=True
            )
            
            # Estratos de PxM2 (diferentes para venta/renta)
            config_pxm2 = self.estratos_config['PxM2'][df_name]
            df['estrato_PxM2'] = pd.cut(
                df['PxM2'],
                bins=config_pxm2['bins'],
                labels=config_pxm2['labels'],
                include_lowest=True
            )
        
        print("✅ Estratos creados")
    
    def detectar_outliers_iqr(self, data, columna):
        """Detecta outliers usando método IQR"""
        Q1 = data[columna].quantile(0.25)
        Q3 = data[columna].quantile(0.75)
        IQR = Q3 - Q1
        
        limite_inferior = Q1 - 1.5 * IQR
        limite_superior = Q3 + 1.5 * IQR
        
        outliers = data[(data[columna] < limite_inferior) | (data[columna] > limite_superior)]
        return outliers, limite_inferior, limite_superior
    
    def graficas_globales(self):
        """Genera gráficas globales por operación"""
        print("📈 Generando gráficas globales...")
        
        variables = ['precio', 'area_m2', 'PxM2']
        
        for var in variables:
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'Análisis Global: {var.upper()}', fontsize=16, fontweight='bold')
            
            # VENTA
            if self.df_venta is not None and len(self.df_venta) > 0:
                # Histograma
                axes[0, 0].hist(self.df_venta[var].dropna(), bins=50, alpha=0.7, color='red', edgecolor='black')
                axes[0, 0].set_title(f'VENTA - Distribución {var}')
                axes[0, 0].set_xlabel(var)
                axes[0, 0].set_ylabel('Frecuencia')
                
                # Boxplot
                axes[0, 1].boxplot(self.df_venta[var].dropna())
                axes[0, 1].set_title(f'VENTA - Boxplot {var}')
                axes[0, 1].set_ylabel(var)
                
                # Outliers por tipo de propiedad
                if 'tipo_propiedad' in self.df_venta.columns:
                    sns.boxplot(data=self.df_venta, x='tipo_propiedad', y=var, ax=axes[0, 2])
                    axes[0, 2].set_title(f'VENTA - {var} por Tipo')
                    axes[0, 2].tick_params(axis='x', rotation=45)
            
            # RENTA
            if self.df_renta is not None and len(self.df_renta) > 0:
                # Histograma
                axes[1, 0].hist(self.df_renta[var].dropna(), bins=50, alpha=0.7, color='blue', edgecolor='black')
                axes[1, 0].set_title(f'RENTA - Distribución {var}')
                axes[1, 0].set_xlabel(var)
                axes[1, 0].set_ylabel('Frecuencia')
                
                # Boxplot
                axes[1, 1].boxplot(self.df_renta[var].dropna())
                axes[1, 1].set_title(f'RENTA - Boxplot {var}')
                axes[1, 1].set_ylabel(var)
                
                # Outliers por tipo de propiedad
                if 'tipo_propiedad' in self.df_renta.columns:
                    sns.boxplot(data=self.df_renta, x='tipo_propiedad', y=var, ax=axes[1, 2])
                    axes[1, 2].set_title(f'RENTA - {var} por Tipo')
                    axes[1, 2].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'grafica_global_{var}.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def graficas_por_estratos_area(self):
        """Gráficas estratificadas por área"""
        print("📊 Generando gráficas por estratos de área...")
        
        for operacion, df in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df is None or len(df) == 0:
                continue
                
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            fig.suptitle(f'{operacion} - Análisis por Estratos de Área', fontsize=16, fontweight='bold')
            
            # Distribución de estratos
            estrato_counts = df['estrato_area'].value_counts()
            axes[0, 0].bar(range(len(estrato_counts)), estrato_counts.values, 
                          color='skyblue', edgecolor='black')
            axes[0, 0].set_title('Distribución de Propiedades por Estrato')
            axes[0, 0].set_xticks(range(len(estrato_counts)))
            axes[0, 0].set_xticklabels(estrato_counts.index, rotation=45)
            axes[0, 0].set_ylabel('Cantidad')
            
            # Precio por estrato
            sns.boxplot(data=df, x='estrato_area', y='precio', ax=axes[0, 1])
            axes[0, 1].set_title('Precio por Estrato de Área')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # PxM2 por estrato
            sns.boxplot(data=df, x='estrato_area', y='PxM2', ax=axes[0, 2])
            axes[0, 2].set_title('PxM2 por Estrato de Área')
            axes[0, 2].tick_params(axis='x', rotation=45)
            
            # Outliers por estrato
            for idx, estrato in enumerate(estrato_counts.index[:3]):  # Solo primeros 3 estratos
                if idx >= 3:
                    break
                    
                datos_estrato = df[df['estrato_area'] == estrato]
                if len(datos_estrato) > 0:
                    outliers, _, _ = self.detectar_outliers_iqr(datos_estrato, 'precio')
                    
                    axes[1, idx].scatter(datos_estrato['area_m2'], datos_estrato['precio'], 
                                       alpha=0.6, label='Normal')
                    if len(outliers) > 0:
                        axes[1, idx].scatter(outliers['area_m2'], outliers['precio'], 
                                           color='red', alpha=0.8, label='Outliers')
                    axes[1, idx].set_title(f'Outliers - {estrato}')
                    axes[1, idx].set_xlabel('Área m²')
                    axes[1, idx].set_ylabel('Precio')
                    axes[1, idx].legend()
            
            plt.tight_layout()
            plt.savefig(f'estratos_area_{operacion.lower()}.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def graficas_por_estratos_precio(self):
        """Gráficas estratificadas por precio"""
        print("💰 Generando gráficas por estratos de precio...")
        
        for operacion, df in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df is None or len(df) == 0:
                continue
                
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            fig.suptitle(f'{operacion} - Análisis por Estratos de Precio', fontsize=16, fontweight='bold')
            
            # Distribución de estratos
            estrato_counts = df['estrato_precio'].value_counts()
            axes[0, 0].bar(range(len(estrato_counts)), estrato_counts.values, 
                          color='lightgreen', edgecolor='black')
            axes[0, 0].set_title('Distribución por Estrato de Precio')
            axes[0, 0].set_xticks(range(len(estrato_counts)))
            axes[0, 0].set_xticklabels(estrato_counts.index, rotation=45)
            
            # Área por estrato
            sns.boxplot(data=df, x='estrato_precio', y='area_m2', ax=axes[0, 1])
            axes[0, 1].set_title('Área por Estrato de Precio')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # PxM2 por estrato
            sns.boxplot(data=df, x='estrato_precio', y='PxM2', ax=axes[0, 2])
            axes[0, 2].set_title('PxM2 por Estrato de Precio')
            axes[0, 2].tick_params(axis='x', rotation=45)
            
            # Outliers por estrato (primeros 3)
            for idx, estrato in enumerate(estrato_counts.index[:3]):
                if idx >= 3:
                    break
                    
                datos_estrato = df[df['estrato_precio'] == estrato]
                if len(datos_estrato) > 0:
                    outliers, _, _ = self.detectar_outliers_iqr(datos_estrato, 'area_m2')
                    
                    axes[1, idx].scatter(datos_estrato['precio'], datos_estrato['area_m2'], 
                                       alpha=0.6, label='Normal')
                    if len(outliers) > 0:
                        axes[1, idx].scatter(outliers['precio'], outliers['area_m2'], 
                                           color='red', alpha=0.8, label='Outliers')
                    axes[1, idx].set_title(f'Outliers - {estrato}')
                    axes[1, idx].set_xlabel('Precio')
                    axes[1, idx].set_ylabel('Área m²')
                    axes[1, idx].legend()
            
            plt.tight_layout()
            plt.savefig(f'estratos_precio_{operacion.lower()}.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def graficas_por_estratos_pxm2(self):
        """Gráficas estratificadas por PxM2"""
        print("📐 Generando gráficas por estratos de PxM2...")
        
        for operacion, df in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df is None or len(df) == 0:
                continue
                
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            fig.suptitle(f'{operacion} - Análisis por Estratos de PxM2', fontsize=16, fontweight='bold')
            
            # Distribución de estratos
            estrato_counts = df['estrato_PxM2'].value_counts()
            axes[0, 0].bar(range(len(estrato_counts)), estrato_counts.values, 
                          color='orange', edgecolor='black')
            axes[0, 0].set_title('Distribución por Estrato de PxM2')
            axes[0, 0].set_xticks(range(len(estrato_counts)))
            axes[0, 0].set_xticklabels(estrato_counts.index, rotation=45)
            
            # Precio por estrato
            sns.boxplot(data=df, x='estrato_PxM2', y='precio', ax=axes[0, 1])
            axes[0, 1].set_title('Precio por Estrato de PxM2')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Área por estrato
            sns.boxplot(data=df, x='estrato_PxM2', y='area_m2', ax=axes[0, 2])
            axes[0, 2].set_title('Área por Estrato de PxM2')
            axes[0, 2].tick_params(axis='x', rotation=45)
            
            # Outliers por estrato (primeros 3)
            for idx, estrato in enumerate(estrato_counts.index[:3]):
                if idx >= 3:
                    break
                    
                datos_estrato = df[df['estrato_PxM2'] == estrato]
                if len(datos_estrato) > 0:
                    outliers, _, _ = self.detectar_outliers_iqr(datos_estrato, 'PxM2')
                    
                    axes[1, idx].scatter(datos_estrato['area_m2'], datos_estrato['PxM2'], 
                                       alpha=0.6, label='Normal')
                    if len(outliers) > 0:
                        axes[1, idx].scatter(outliers['area_m2'], outliers['PxM2'], 
                                           color='red', alpha=0.8, label='Outliers')
                    axes[1, idx].set_title(f'Outliers PxM2 - {estrato}')
                    axes[1, idx].set_xlabel('Área m²')
                    axes[1, idx].set_ylabel('PxM2')
                    axes[1, idx].legend()
            
            plt.tight_layout()
            plt.savefig(f'estratos_pxm2_{operacion.lower()}.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def resumen_outliers(self):
        """Genera resumen de outliers detectados"""
        print("🎯 Generando resumen de outliers...")
        
        variables = ['precio', 'area_m2', 'PxM2']
        
        fig, axes = plt.subplots(len(variables), 2, figsize=(15, 12))
        fig.suptitle('Resumen de Outliers por Variable y Operación', fontsize=16, fontweight='bold')
        
        for i, var in enumerate(variables):
            for j, (operacion, df) in enumerate([('VENTA', self.df_venta), ('RENTA', self.df_renta)]):
                if df is None or len(df) == 0:
                    continue
                    
                outliers, lim_inf, lim_sup = self.detectar_outliers_iqr(df, var)
                pct_outliers = len(outliers) / len(df) * 100
                
                # Scatter plot con outliers destacados
                normal_data = df[(df[var] >= lim_inf) & (df[var] <= lim_sup)]
                
                axes[i, j].scatter(normal_data.index, normal_data[var], 
                                 alpha=0.6, color='blue', s=10, label='Normal')
                
                if len(outliers) > 0:
                    axes[i, j].scatter(outliers.index, outliers[var], 
                                     alpha=0.8, color='red', s=15, label='Outliers')
                
                axes[i, j].axhline(y=lim_sup, color='red', linestyle='--', alpha=0.7)
                axes[i, j].axhline(y=lim_inf, color='red', linestyle='--', alpha=0.7)
                
                axes[i, j].set_title(f'{operacion} - {var}\n{len(outliers)} outliers ({pct_outliers:.1f}%)')
                axes[i, j].set_ylabel(var)
                axes[i, j].legend()
                
        plt.tight_layout()
        plt.savefig('resumen_outliers.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Tabla resumen
        print("\n" + "="*60)
        print("RESUMEN ESTADÍSTICO DE OUTLIERS")
        print("="*60)
        
        for operacion, df in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df is None or len(df) == 0:
                continue
                
            print(f"\n{operacion}:")
            print("-" * 40)
            
            for var in variables:
                outliers, _, _ = self.detectar_outliers_iqr(df, var)
                pct = len(outliers) / len(df) * 100
                print(f"{var:10}: {len(outliers):4d} outliers ({pct:5.1f}%)")
    
    def ejecutar_analisis_completo(self):
        """Ejecuta todo el análisis visual"""
        print("🚀 INICIANDO ANÁLISIS COMPLETO DE VISUALIZACIÓN")
        print("=" * 60)
        
        if not self.cargar_datos():
            return
            
        print("\n📊 GENERANDO VISUALIZACIONES...")
        
        # Gráficas globales
        self.graficas_globales()
        
        # Estratos por área
        self.graficas_por_estratos_area()
        
        # Estratos por precio
        self.graficas_por_estratos_precio()
        
        # Estratos por PxM2
        self.graficas_por_estratos_pxm2()
        
        # Resumen de outliers
        self.resumen_outliers()
        
        print("\n✅ ANÁLISIS COMPLETADO")
        print("📁 Archivos generados:")
        print("   - grafica_global_*.png")
        print("   - estratos_*.png")
        print("   - resumen_outliers.png")


def main():
    """Función principal"""
    # Configurar ruta al archivo
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    
    print("🏠 VISUALIZADOR INMOBILIARIO ESDATA_EPSILON")
    print("=" * 50)
    print(f"📂 Archivo: {archivo}")
    
    # Crear y ejecutar el visualizador
    viz = VisualizadorInmobiliario(archivo)
    viz.ejecutar_analisis_completo()


if __name__ == "__main__":
    main()
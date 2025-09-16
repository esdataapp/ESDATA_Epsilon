"""
ANÁLISIS AVANZADO DE OUTLIERS INMOBILIARIOS
============================================

Script complementario para análisis profundo de outliers con:
- Identificación de outliers extremos
- Análisis por colonias
- Comparaciones entre tipos de propiedad
- Métricas de calidad de datos

Autor: Sistema ESDATA_Epsilon
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from collections import Counter

class AnalizadorOutliers:
    """Análisis profundo de outliers"""
    
    def __init__(self, archivo_csv):
        self.archivo = archivo_csv
        self.df = None
        
    def cargar_datos(self):
        """Cargar datos con validaciones"""
        try:
            self.df = pd.read_csv(self.archivo)
            
            # Convertir a numérico
            numeric_cols = ['area_m2', 'precio', 'PxM2']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            print(f"✅ Datos cargados: {len(self.df):,} registros")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def outliers_multivariados(self):
        """Detecta outliers usando múltiples variables"""
        if self.df is None:
            print("❌ No hay datos cargados")
            return
            
        print("🔍 Analizando outliers multivariados...")
        
        # Preparar datos limpios
        vars_analisis = ['precio', 'area_m2', 'PxM2']
        df_clean = self.df[vars_analisis + ['operacion', 'tipo_propiedad', 'Colonia']].dropna()
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Análisis Multivariado de Outliers', fontsize=16, fontweight='bold')
        
        # Scatter precio vs área coloreado por operación
        for i, operacion in enumerate(['Ven', 'Ren']):
            data_op = df_clean[df_clean['operacion'] == operacion]
            if len(data_op) > 0:
                axes[0, 0].scatter(data_op['area_m2'], data_op['precio'], 
                                 alpha=0.6, label=f'{operacion} ({len(data_op)})', s=10)
        
        axes[0, 0].set_xlabel('Área m²')
        axes[0, 0].set_ylabel('Precio')
        axes[0, 0].set_title('Precio vs Área por Operación')
        axes[0, 0].legend()
        axes[0, 0].set_xlim(0, 500)  # Limitar para ver mejor
        
        # PxM2 vs Área por operación
        for operacion in ['Ven', 'Ren']:
            data_op = df_clean[df_clean['operacion'] == operacion]
            if len(data_op) > 0:
                axes[0, 1].scatter(data_op['area_m2'], data_op['PxM2'], 
                                 alpha=0.6, label=f'{operacion}', s=10)
        
        axes[0, 1].set_xlabel('Área m²')
        axes[0, 1].set_ylabel('PxM2')
        axes[0, 1].set_title('PxM2 vs Área por Operación')
        axes[0, 1].legend()
        
        # Top 5 colonias con más outliers de precio
        outliers_precio = []
        for _, row in df_clean.iterrows():
            Q1 = df_clean['precio'].quantile(0.25)
            Q3 = df_clean['precio'].quantile(0.75)
            IQR = Q3 - Q1
            if row['precio'] > Q3 + 1.5 * IQR or row['precio'] < Q1 - 1.5 * IQR:
                outliers_precio.append(row['Colonia'])
        
        colonia_counts = Counter(outliers_precio)
        top_colonias = colonia_counts.most_common(10)
        
        if top_colonias:
            colonias, counts = zip(*top_colonias)
            axes[1, 0].bar(range(len(colonias)), counts, color='coral')
            axes[1, 0].set_title('Top Colonias con Más Outliers de Precio')
            axes[1, 0].set_xlabel('Colonias')
            axes[1, 0].set_ylabel('Cantidad de Outliers')
            axes[1, 0].set_xticks(range(len(colonias)))
            axes[1, 0].set_xticklabels(colonias, rotation=45, ha='right')
        
        # Distribución de outliers por tipo de propiedad
        outliers_por_tipo = df_clean.groupby('tipo_propiedad').apply(
            lambda x: len(x[(x['precio'] > x['precio'].quantile(0.75) + 1.5 * 
                           (x['precio'].quantile(0.75) - x['precio'].quantile(0.25))) |
                          (x['precio'] < x['precio'].quantile(0.25) - 1.5 * 
                           (x['precio'].quantile(0.75) - x['precio'].quantile(0.25)))])
        )
        
        axes[1, 1].bar(range(len(outliers_por_tipo)), outliers_por_tipo.values, color='lightblue')
        axes[1, 1].set_title('Outliers de Precio por Tipo de Propiedad')
        axes[1, 1].set_xticks(range(len(outliers_por_tipo)))
        axes[1, 1].set_xticklabels(outliers_por_tipo.index, rotation=45)
        axes[1, 1].set_ylabel('Cantidad de Outliers')
        
        plt.tight_layout()
        plt.savefig('analisis_outliers_multivariado.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Reporte de colonias problemáticas
        print("\n🏘️ TOP 10 COLONIAS CON MÁS OUTLIERS DE PRECIO:")
        print("-" * 50)
        for i, (colonia, count) in enumerate(top_colonias[:10], 1):
            pct_colonia = count / len(df_clean[df_clean['Colonia'] == colonia]) * 100
            print(f"{i:2d}. {colonia:<25}: {count:3d} outliers ({pct_colonia:.1f}% de la colonia)")
    
    def metricas_calidad(self):
        """Genera métricas de calidad de datos"""
        if self.df is None:
            print("❌ No hay datos cargados")
            return
            
        print("\n📊 MÉTRICAS DE CALIDAD DE DATOS")
        print("=" * 50)
        
        # Completitud de datos
        total_registros = len(self.df)
        
        print(f"📈 COMPLETITUD DE DATOS:")
        print(f"   • Total de registros: {total_registros:,}")
        
        campos_criticos = ['precio', 'area_m2', 'tipo_propiedad', 'operacion']
        for campo in campos_criticos:
            if campo in self.df.columns:
                completos = self.df[campo].notna().sum()
                pct = completos / total_registros * 100
                print(f"   • {campo:15}: {completos:6,} ({pct:5.1f}%)")
        
        # PxM2 calculable
        if 'PxM2' in self.df.columns:
            pxm2_validos = self.df['PxM2'].notna().sum()
            pct_pxm2 = pxm2_validos / total_registros * 100
            print(f"   • PxM2 calculado  : {pxm2_validos:6,} ({pct_pxm2:5.1f}%)")
        
        # Distribución por operación
        if 'operacion' in self.df.columns:
            print(f"\n🔄 DISTRIBUCIÓN POR OPERACIÓN:")
            op_counts = self.df['operacion'].value_counts()
            for op, count in op_counts.items():
                pct = count / total_registros * 100
                print(f"   • {op:10}: {count:6,} ({pct:5.1f}%)")
        
        # Distribución por tipo
        if 'tipo_propiedad' in self.df.columns:
            print(f"\n🏠 DISTRIBUCIÓN POR TIPO DE PROPIEDAD:")
            tipo_counts = self.df['tipo_propiedad'].value_counts()
            for tipo, count in tipo_counts.items():
                pct = count / total_registros * 100
                print(f"   • {tipo:15}: {count:6,} ({pct:5.1f}%)")
        
        # Rangos de valores
        print(f"\n📏 RANGOS DE VALORES:")
        vars_numericas = ['precio', 'area_m2', 'PxM2']
        for var in vars_numericas:
            if var in self.df.columns:
                data = self.df[var].dropna()
                if len(data) > 0:
                    print(f"   • {var:10}: Min={data.min():>12,.0f} | Max={data.max():>15,.0f} | Media={data.mean():>12,.0f}")
    
    def reporte_outliers_detallado(self):
        """Genera reporte detallado de outliers"""
        if self.df is None:
            print("❌ No hay datos cargados")
            return None
            
        print("\n🎯 REPORTE DETALLADO DE OUTLIERS")
        print("=" * 60)
        
        variables = ['precio', 'area_m2', 'PxM2']
        operaciones = ['Ven', 'Ren']
        
        # Crear DataFrame resumen
        resumen_data = []
        
        for var in variables:
            if var not in self.df.columns:
                continue
                
            for op in operaciones:
                data_op = self.df[self.df['operacion'] == op][var].dropna()
                
                if len(data_op) > 0:
                    Q1 = data_op.quantile(0.25)
                    Q3 = data_op.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lim_inf = Q1 - 1.5 * IQR
                    lim_sup = Q3 + 1.5 * IQR
                    
                    outliers = data_op[(data_op < lim_inf) | (data_op > lim_sup)]
                    pct_outliers = len(outliers) / len(data_op) * 100
                    
                    resumen_data.append({
                        'Variable': var,
                        'Operacion': op,
                        'Total': len(data_op),
                        'Outliers': len(outliers),
                        'Porcentaje': pct_outliers,
                        'Q1': Q1,
                        'Q3': Q3,
                        'IQR': IQR,
                        'Lim_Inf': lim_inf,
                        'Lim_Sup': lim_sup
                    })
        
        if not resumen_data:
            print("❌ No se pudo generar el reporte")
            return None
            
        df_resumen = pd.DataFrame(resumen_data)
        
        # Mostrar tabla resumen
        print(df_resumen[['Variable', 'Operacion', 'Total', 'Outliers', 'Porcentaje']].to_string(index=False))
        
        # Guardar resumen detallado
        df_resumen.to_csv('resumen_outliers_detallado.csv', index=False)
        print(f"\n💾 Resumen guardado en: resumen_outliers_detallado.csv")
        
        return df_resumen
    
    def ejecutar_analisis_completo(self):
        """Ejecuta análisis completo de outliers"""
        print("🔍 ANÁLISIS AVANZADO DE OUTLIERS")
        print("=" * 50)
        
        if not self.cargar_datos():
            return
        
        # Análisis multivariado
        self.outliers_multivariados()
        
        # Métricas de calidad
        self.metricas_calidad()
        
        # Reporte detallado
        df_resumen = self.reporte_outliers_detallado()
        
        print("\n✅ ANÁLISIS DE OUTLIERS COMPLETADO")
        print("📁 Archivos generados:")
        print("   - analisis_outliers_multivariado.png")
        print("   - resumen_outliers_detallado.csv")


def main():
    """Función principal"""
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    
    print("🔍 ANALIZADOR AVANZADO DE OUTLIERS")
    print("=" * 40)
    print(f"📂 Archivo: {archivo}")
    
    analyzer = AnalizadorOutliers(archivo)
    analyzer.ejecutar_analisis_completo()


if __name__ == "__main__":
    main()
# 13. F1_Norm_Rep.py
"""
Generador de reportes para análisis de normalización
Crea insights, recomendaciones y reportes de transformación de variables

Versión: 1.0
Última actualización: Enero 2025
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class NormalizationReportGenerator:
    """
    Generador de reportes de normalización
    """
    
    def __init__(self, normalization_analysis_path, original_data_path):
        self.normalization_analysis_path = normalization_analysis_path
        self.original_data_path = original_data_path
        self.norm_df = pd.DataFrame()
        self.original_df = pd.DataFrame()
        
    def load_data(self):
        """Carga los datos necesarios"""
        try:
            # Cargar análisis de normalización
            self.norm_df = pd.read_csv(self.normalization_analysis_path, encoding='utf-8')
            print(f"✅ Análisis de normalización cargado: {len(self.norm_df)} variables")
            
            # Cargar datos originales
            self.original_df = pd.read_csv(self.original_data_path, encoding='utf-8')
            print(f"✅ Datos originales cargados: {self.original_df.shape}")
            
            return True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def create_insights_report(self):
        """Crea reporte de insights de normalización"""
        if self.norm_df.empty:
            return pd.DataFrame()
            
        insights_data = []
        
        for _, row in self.norm_df.iterrows():
            variable = row['variable']
            metodo_recomendado = row['metodo_recomendado']
            prioridad = row['prioridad_normalizacion']
            asimetria = row['asimetria']
            tipo_distribucion = row['tipo_distribucion']
            
            # Generar insights según características
            if prioridad == 'ALTA':
                if metodo_recomendado == 'LogTransform':
                    tipo_insight = 'TRANSFORMACION_CRITICA'
                    descripcion = f'Variable {variable} necesita transformación logarítmica urgente - distribución muy sesgada (asimetría: {asimetria:.2f})'
                elif metodo_recomendado == 'RobustScaler':
                    tipo_insight = 'OUTLIERS_CRITICOS'
                    descripcion = f'Variable {variable} tiene muchos outliers - usar RobustScaler para mayor estabilidad'
                else:
                    tipo_insight = 'NORMALIZACION_PRIORITARIA'
                    descripcion = f'Variable {variable} necesita {metodo_recomendado} con alta prioridad'
            elif prioridad == 'MEDIA':
                tipo_insight = 'MEJORA_RECOMENDADA'
                descripcion = f'Variable {variable} se beneficiaría de {metodo_recomendado} para mejor comportamiento'
            else:
                if metodo_recomendado != 'NINGUNO':
                    tipo_insight = 'OPTIMIZACION_OPCIONAL'
                    descripcion = f'Variable {variable} funciona bien sin normalizar, pero {metodo_recomendado} podría optimizar'
                else:
                    continue  # No incluir variables que no necesitan normalización
            
            # Determinar impacto esperado
            if 'mejora_normalidad' in row['razon_recomendacion']:
                impacto_principal = 'MEJORA_NORMALIDAD'
            elif 'reduce_asimetria' in row['razon_recomendacion']:
                impacto_principal = 'REDUCE_ASIMETRIA'
            elif 'resistente_outliers' in row['razon_recomendacion']:
                impacto_principal = 'RESISTENTE_OUTLIERS'
            else:
                impacto_principal = 'MEJORA_GENERAL'
            
            insights_data.append({
                'variable': variable,
                'tipo_insight': tipo_insight,
                'descripcion': descripcion,
                'metodo_recomendado': metodo_recomendado,
                'prioridad': prioridad,
                'impacto_principal': impacto_principal,
                'tipo_distribucion_original': tipo_distribucion,
                'asimetria_original': asimetria,
                'razon_tecnica': row['razon_recomendacion'],
                'puntuacion': row['puntuacion_recomendacion']
            })
        
        return pd.DataFrame(insights_data)
    
    def create_recommendations_report(self):
        """Crea reporte de recomendaciones detalladas"""
        if self.norm_df.empty:
            return pd.DataFrame()
            
        recommendations_data = []
        
        for _, row in self.norm_df.iterrows():
            variable = row['variable']
            metodo = row['metodo_recomendado']
            prioridad = row['prioridad_normalizacion']
            
            if metodo == 'NINGUNO':
                continue
            
            # Generar recomendación específica
            if metodo == 'StandardScaler':
                recomendacion = f'Aplicar StandardScaler a {variable}: (x - media) / desv_std'
                implementacion = 'from sklearn.preprocessing import StandardScaler; scaler = StandardScaler().fit_transform(data)'
                cuando_usar = 'Distribución aproximadamente normal, pocos outliers'
                ventajas = 'Centra en 0, escala unitaria, preserva forma de distribución'
                limitaciones = 'Sensible a outliers, asume normalidad'
            
            elif metodo == 'MinMaxScaler':
                recomendacion = f'Aplicar MinMaxScaler a {variable}: (x - min) / (max - min)'
                implementacion = 'from sklearn.preprocessing import MinMaxScaler; scaler = MinMaxScaler().fit_transform(data)'
                cuando_usar = 'Necesitas valores entre 0-1, distribución uniforme deseada'
                ventajas = 'Rango fijo [0,1], interpretable, preserva relaciones'
                limitaciones = 'Muy sensible a outliers extremos'
            
            elif metodo == 'RobustScaler':
                recomendacion = f'Aplicar RobustScaler a {variable}: (x - mediana) / IQR'
                implementacion = 'from sklearn.preprocessing import RobustScaler; scaler = RobustScaler().fit_transform(data)'
                cuando_usar = 'Muchos outliers, distribución no normal'
                ventajas = 'Resistente a outliers, usa mediana e IQR'
                limitaciones = 'No garantiza rango específico'
            
            elif metodo == 'LogTransform':
                recomendacion = f'Aplicar transformación logarítmica a {variable}: log(x + 1)'
                implementacion = 'import numpy as np; transformed = np.log1p(data)'
                cuando_usar = 'Distribución muy sesgada a la derecha, valores positivos'
                ventajas = 'Reduce asimetría, estabiliza varianza'
                limitaciones = 'Solo para valores positivos, cambia interpretación'
            
            else:
                recomendacion = f'Aplicar {metodo} a {variable}'
                implementacion = 'Consultar documentación específica'
                cuando_usar = 'Según características de la variable'
                ventajas = 'Método específico recomendado'
                limitaciones = 'Ver documentación del método'
            
            # Determinar orden de implementación
            if prioridad == 'ALTA':
                orden_implementacion = 1
            elif prioridad == 'MEDIA':
                orden_implementacion = 2
            else:
                orden_implementacion = 3
            
            recommendations_data.append({
                'variable': variable,
                'metodo_recomendado': metodo,
                'recomendacion_detallada': recomendacion,
                'implementacion_codigo': implementacion,
                'cuando_usar': cuando_usar,
                'ventajas': ventajas,
                'limitaciones': limitaciones,
                'prioridad': prioridad,
                'orden_implementacion': orden_implementacion,
                'impacto_esperado_asimetria': row.get('std_asimetria_final', np.nan),
                'mejora_normalidad_esperada': row.get('std_mejora_normalidad', False)
            })
        
        return pd.DataFrame(recommendations_data).sort_values('orden_implementacion')
    
    def create_transformation_matrix(self):
        """Crea matriz de transformación por variable"""
        if self.norm_df.empty:
            return pd.DataFrame()
            
        matrix_data = []
        
        for _, row in self.norm_df.iterrows():
            variable = row['variable']
            
            # Estado de transformación
            if row['metodo_recomendado'] == 'NINGUNO':
                estado = 'NO_REQUIERE'
                accion = 'USAR_SIN_CAMBIOS'
            elif row['prioridad_normalizacion'] == 'ALTA':
                estado = 'TRANSFORMACION_CRITICA'
                accion = 'APLICAR_INMEDIATAMENTE'
            elif row['prioridad_normalizacion'] == 'MEDIA':
                estado = 'TRANSFORMACION_BENEFICIOSA'
                accion = 'APLICAR_SI_POSIBLE'
            else:
                estado = 'TRANSFORMACION_OPCIONAL'
                accion = 'CONSIDERAR_APLICAR'
            
            # Métricas de mejora esperada
            mejora_std = row.get('std_mejora_normalidad', False)
            mejora_minmax = row.get('minmax_mejora_normalidad', False)
            mejora_robust = row.get('robust_mejora_normalidad', False)
            mejora_log = row.get('log_mejora_normalidad', False)
            
            total_mejoras = sum([mejora_std, mejora_minmax, mejora_robust, mejora_log])
            
            matrix_data.append({
                'variable': variable,
                'estado_transformacion': estado,
                'accion_recomendada': accion,
                'metodo_primario': row['metodo_recomendado'],
                'codigo_metodo': row.get('codigo_metodo', ''),
                'puntuacion_metodo': row['puntuacion_recomendacion'],
                'prioridad': row['prioridad_normalizacion'],
                
                # Características originales
                'asimetria_original': row['asimetria'],
                'curtosis_original': row['curtosis'],
                'tipo_distribucion': row['tipo_distribucion'],
                'coef_variacion': row['coef_variacion'],
                'pct_outliers': row['pct_outliers'],
                
                # Evaluación de métodos
                'standard_viable': mejora_std,
                'minmax_viable': mejora_minmax,
                'robust_viable': mejora_robust,
                'log_viable': mejora_log,
                'total_metodos_viables': total_mejoras,
                
                # Métricas finales esperadas
                'asimetria_final_esperada': row.get('std_asimetria_final', np.nan),
                'mejora_normalidad_esperada': mejora_std,
                'justificacion': row['razon_recomendacion']
            })
        
        return pd.DataFrame(matrix_data)
    
    def create_alerts_report(self):
        """Crea reporte de alertas y consideraciones especiales"""
        if self.norm_df.empty:
            return pd.DataFrame()
            
        alerts_data = []
        
        for _, row in self.norm_df.iterrows():
            variable = row['variable']
            asimetria = abs(row['asimetria'])
            tipo_dist = row['tipo_distribucion']
            pct_outliers = row['pct_outliers']
            
            # Alertas por asimetría extrema
            if asimetria > 3:
                alerts_data.append({
                    'severidad': 'CRITICA',
                    'variable': variable,
                    'tipo_alerta': 'ASIMETRIA_EXTREMA',
                    'mensaje': f'Asimetría muy alta ({asimetria:.2f}) - transformación urgente necesaria',
                    'accion_requerida': 'APLICAR_LOG_TRANSFORM_INMEDIATAMENTE',
                    'impacto_si_no_se_corrige': 'Algoritmos pueden fallar o dar resultados sesgados'
                })
            elif asimetria > 2:
                alerts_data.append({
                    'severidad': 'ALTA',
                    'variable': variable,
                    'tipo_alerta': 'ASIMETRIA_ALTA',
                    'mensaje': f'Asimetría considerable ({asimetria:.2f}) - recomendada transformación',
                    'accion_requerida': 'CONSIDERAR_TRANSFORMACION_DISTRIBUCIONAL',
                    'impacto_si_no_se_corrige': 'Pérdida de eficiencia en modelos estadísticos'
                })
            
            # Alertas por outliers excesivos
            if pct_outliers > 15:
                alerts_data.append({
                    'severidad': 'ALTA',
                    'variable': variable,
                    'tipo_alerta': 'OUTLIERS_EXCESIVOS',
                    'mensaje': f'Muchos outliers ({pct_outliers:.1f}%) - usar método robusto',
                    'accion_requerida': 'USAR_ROBUST_SCALER_OBLIGATORIO',
                    'impacto_si_no_se_corrige': 'Normalización estándar será inestable'
                })
            elif pct_outliers > 10:
                alerts_data.append({
                    'severidad': 'MEDIA',
                    'variable': variable,
                    'tipo_alerta': 'OUTLIERS_MODERADOS',
                    'mensaje': f'Outliers presentes ({pct_outliers:.1f}%) - considerar método robusto',
                    'accion_requerida': 'EVALUAR_ROBUST_SCALER',
                    'impacto_si_no_se_corrige': 'Posible inestabilidad en normalización'
                })
            
            # Alertas por distribución problemática
            if tipo_dist == 'KURTOSIS_ALTA':
                alerts_data.append({
                    'severidad': 'MEDIA',
                    'variable': variable,
                    'tipo_alerta': 'DISTRIBUCION_LEPTOCURTICA',
                    'mensaje': 'Distribución muy picuda - cuidado con métodos sensibles',
                    'accion_requerida': 'PREFERIR_METODOS_ROBUSTOS',
                    'impacto_si_no_se_corrige': 'Normalización puede no ser efectiva'
                })
            
            # Alertas por coeficiente de variación extremo
            coef_var = row.get('coef_variacion', 0)
            if coef_var > 2:
                alerts_data.append({
                    'severidad': 'ALTA',
                    'variable': variable,
                    'tipo_alerta': 'VARIABILIDAD_EXTREMA',
                    'mensaje': f'Coeficiente de variación muy alto ({coef_var:.2f}) - normalización crítica',
                    'accion_requerida': 'NORMALIZACION_OBLIGATORIA',
                    'impacto_si_no_se_corrige': 'Variable dominará análisis por su escala'
                })
        
        return pd.DataFrame(alerts_data)
    
    def create_implementation_guide(self):
        """Crea guía de implementación paso a paso"""
        if self.norm_df.empty:
            return pd.DataFrame()
        
        # Agrupar por método y prioridad
        high_priority = self.norm_df[self.norm_df['prioridad_normalizacion'] == 'ALTA']
        medium_priority = self.norm_df[self.norm_df['prioridad_normalizacion'] == 'MEDIA']
        
        guide_data = []
        step = 1
        
        # Paso 1: Variables críticas
        for _, row in high_priority.iterrows():
            if row['metodo_recomendado'] != 'NINGUNO':
                guide_data.append({
                    'paso': step,
                    'fase': 'CRITICA',
                    'variable': row['variable'],
                    'metodo': row['metodo_recomendado'],
                    'justificacion': f"Prioridad alta: {row['razon_recomendacion']}",
                    'codigo_ejemplo': f"# Transformar {row['variable']}\n# Método: {row['metodo_recomendado']}",
                    'verificacion': f"Comprobar asimetría < 1.0 después de transformación"
                })
                step += 1
        
        # Paso 2: Variables de mejora
        for _, row in medium_priority.iterrows():
            if row['metodo_recomendado'] != 'NINGUNO':
                guide_data.append({
                    'paso': step,
                    'fase': 'MEJORA',
                    'variable': row['variable'],
                    'metodo': row['metodo_recomendado'],
                    'justificacion': f"Mejora recomendada: {row['razon_recomendacion']}",
                    'codigo_ejemplo': f"# Optimizar {row['variable']}\n# Método: {row['metodo_recomendado']}",
                    'verificacion': f"Evaluar mejora en métricas de distribución"
                })
                step += 1
        
        return pd.DataFrame(guide_data)
    
    def create_summary_dashboard(self):
        """Crea dashboard de resumen ejecutivo"""
        if self.norm_df.empty:
            return {}
            
        total_variables = len(self.norm_df)
        variables_requieren_norm = len(self.norm_df[self.norm_df['metodo_recomendado'] != 'NINGUNO'])
        variables_alta_prioridad = len(self.norm_df[self.norm_df['prioridad_normalizacion'] == 'ALTA'])
        
        # Variables más problemáticas
        problematicas = self.norm_df[
            (self.norm_df['prioridad_normalizacion'] == 'ALTA') |
            (abs(self.norm_df['asimetria']) > 2)
        ].nlargest(5, 'puntuacion_recomendacion')[['variable', 'metodo_recomendado', 'asimetria', 'prioridad_normalizacion']]
        
        # Distribución de métodos
        metodos_count = self.norm_df[self.norm_df['metodo_recomendado'] != 'NINGUNO']['metodo_recomendado'].value_counts()
        
        dashboard = {
            'resumen_general': {
                'total_variables': total_variables,
                'variables_requieren_normalizacion': variables_requieren_norm,
                'variables_alta_prioridad': variables_alta_prioridad,
                'porcentaje_necesita_normalizacion': (variables_requieren_norm / total_variables) * 100,
                'variables_criticas_asimetria': len(self.norm_df[abs(self.norm_df['asimetria']) > 2])
            },
            'distribucion_metodos': metodos_count.to_dict(),
            'variables_problematicas': problematicas.to_dict('records')
        }
        
        return dashboard
    
    def generate_all_reports(self, output_dir):
        """Genera todos los reportes"""
        print("📊 Generando reportes de normalización...")
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar reportes
        insights_df = self.create_insights_report()
        recommendations_df = self.create_recommendations_report()
        transformation_matrix_df = self.create_transformation_matrix()
        alerts_df = self.create_alerts_report()
        implementation_df = self.create_implementation_guide()
        dashboard = self.create_summary_dashboard()
        
        # Guardar archivos
        insights_df.to_csv(f'{output_dir}/F1_NormRep_Sep25_01_insights.csv', index=False, encoding='utf-8-sig')
        recommendations_df.to_csv(f'{output_dir}/F1_NormRep_Sep25_01_recommendations.csv', index=False, encoding='utf-8-sig')
        transformation_matrix_df.to_csv(f'{output_dir}/F1_NormRep_Sep25_01_transformation_matrix.csv', index=False, encoding='utf-8-sig')
        alerts_df.to_csv(f'{output_dir}/F1_NormRep_Sep25_01_alerts.csv', index=False, encoding='utf-8-sig')
        implementation_df.to_csv(f'{output_dir}/F1_NormRep_Sep25_01_implementation_guide.csv', index=False, encoding='utf-8-sig')
        
        # Guardar dashboard como CSV
        dashboard_df = pd.DataFrame([dashboard['resumen_general']])
        dashboard_df.to_csv(f'{output_dir}/F1_NormRep_Sep25_01_dashboard.csv', index=False, encoding='utf-8-sig')
        
        return {
            'insights': insights_df,
            'recommendations': recommendations_df,
            'transformation_matrix': transformation_matrix_df,
            'alerts': alerts_df,
            'implementation_guide': implementation_df,
            'dashboard': dashboard
        }

def main():
    """Función principal"""
    print("🚀 GENERADOR DE REPORTES DE NORMALIZACIÓN")
    print("=" * 50)
    
    # Configurar rutas
    normalization_analysis_path = 'Estadisticas/Fase1/1.Normalizacion/sep25/num_F1Norm_Sep25_01.csv'
    original_data_path = 'Consolidados/pretratadaCol_num/Sep25/pretratadaCol_num_Sep25_01.csv'
    output_dir = 'Estadisticas/Reportes/1. Normalizacion/Sep25'
    
    # Crear generador
    generator = NormalizationReportGenerator(normalization_analysis_path, original_data_path)
    
    # Cargar datos
    if not generator.load_data():
        return None
    
    # Generar reportes
    results = generator.generate_all_reports(output_dir)
    
    # Mostrar resumen
    dashboard = results['dashboard']
    print("\n" + "=" * 50)
    print("RESUMEN EJECUTIVO - NORMALIZACIÓN")
    print("=" * 50)
    
    resumen = dashboard['resumen_general']
    print(f"📊 Variables analizadas: {resumen['total_variables']}")
    print(f"🔄 Variables requieren normalización: {resumen['variables_requieren_normalizacion']} ({resumen['porcentaje_necesita_normalizacion']:.1f}%)")
    print(f"🚨 Variables alta prioridad: {resumen['variables_alta_prioridad']}")
    print(f"📐 Variables con asimetría crítica: {resumen['variables_criticas_asimetria']}")
    
    print(f"\n🎯 MÉTODOS MÁS RECOMENDADOS:")
    for metodo, count in dashboard['distribucion_metodos'].items():
        print(f"  • {metodo}: {count} variables")
    
    print(f"\n🔍 TOP VARIABLES PROBLEMÁTICAS:")
    for problema in dashboard['variables_problematicas']:
        print(f"  • {problema['variable']}: {problema['metodo_recomendado']} (asimetría: {problema['asimetria']:.2f}) - {problema['prioridad_normalizacion']}")
    
    print(f"\n✅ Reportes generados en: {output_dir}")
    print(f"   📋 F1_NormRep_Sep25_01_insights.csv")
    print(f"   💡 F1_NormRep_Sep25_01_recommendations.csv")
    print(f"   📊 F1_NormRep_Sep25_01_transformation_matrix.csv")
    print(f"   🚨 F1_NormRep_Sep25_01_alerts.csv")
    print(f"   📝 F1_NormRep_Sep25_01_implementation_guide.csv")
    print(f"   📈 F1_NormRep_Sep25_01_dashboard.csv")
    
    return results

if __name__ == "__main__":
    results = main()
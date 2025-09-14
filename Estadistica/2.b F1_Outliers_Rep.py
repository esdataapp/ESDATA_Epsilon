# 11. F1_Outliers_Rep_Simple.py
"""
Generador de reportes simplificado para análisis de outliers
Versión simplificada que funciona con el output del script 10. F1_Outliers.py

Versión: 1.0
Última actualización: Enero 2025
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OutliersReportGenerator:
    """
    Generador simplificado de reportes de outliers
    """
    
    def __init__(self, outliers_analysis_path, original_data_path):
        self.outliers_analysis_path = outliers_analysis_path
        self.original_data_path = original_data_path
        self.outliers_df = pd.DataFrame()
        self.original_df = pd.DataFrame()
        
    def load_data(self):
        """Carga los datos necesarios"""
        try:
            # Cargar análisis de outliers
            self.outliers_df = pd.read_csv(self.outliers_analysis_path, encoding='utf-8')
            print(f"✅ Análisis de outliers cargado: {len(self.outliers_df)} variables")
            
            # Cargar datos originales
            self.original_df = pd.read_csv(self.original_data_path, encoding='utf-8')
            print(f"✅ Datos originales cargados: {self.original_df.shape}")
            
            return True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def create_insights_report(self):
        """Crea reporte de insights"""
        if self.outliers_df.empty:
            return pd.DataFrame()
            
        insights_data = []
        
        for _, row in self.outliers_df.iterrows():
            variable = row['variable']
            outliers_count = row['outliers_iqr']
            pct_outliers = row['pct_outliers_iqr']
            severidad = row['severidad_outliers']
            
            if outliers_count > 0:
                # Determinar tipo de insight
                if pct_outliers > 10:
                    tipo_insight = 'CRITICO'
                    descripcion = f'Variable {variable} tiene {outliers_count} outliers ({pct_outliers:.1f}%) - Requiere atención inmediata'
                elif pct_outliers > 5:
                    tipo_insight = 'IMPORTANTE'
                    descripcion = f'Variable {variable} tiene {outliers_count} outliers ({pct_outliers:.1f}%) - Revisar detalladamente'
                else:
                    tipo_insight = 'MONITOREO'
                    descripcion = f'Variable {variable} tiene {outliers_count} outliers ({pct_outliers:.1f}%) - Monitorear evolución'
                
                insights_data.append({
                    'variable': variable,
                    'tipo_insight': tipo_insight,
                    'descripcion': descripcion,
                    'outliers_detectados': outliers_count,
                    'porcentaje_outliers': pct_outliers,
                    'severidad': severidad,
                    'accion_recomendada': row['accion_recomendada'],
                    'justificacion': row['justificacion']
                })
        
        return pd.DataFrame(insights_data)
    
    def create_recommendations_report(self):
        """Crea reporte de recomendaciones"""
        if self.outliers_df.empty:
            return pd.DataFrame()
            
        recommendations_data = []
        
        for _, row in self.outliers_df.iterrows():
            variable = row['variable']
            accion = row['accion_recomendada']
            outliers_count = row['outliers_iqr']
            pct_outliers = row['pct_outliers_iqr']
            
            if outliers_count > 0:
                # Generar recomendación detallada
                if accion == 'ELIMINAR_VALORES_IMPOSIBLES':
                    recomendacion = f'Eliminar {outliers_count} registros con valores imposibles'
                    prioridad = 'ALTA'
                    impacto = 'Mejora significativa en calidad de datos'
                elif accion == 'INVESTIGAR_Y_LIMPIAR':
                    recomendacion = f'Investigar manualmente {outliers_count} registros sospechosos'
                    prioridad = 'ALTA'
                    impacto = 'Previene errores en análisis posteriores'
                elif accion == 'REVISAR_DETALLADAMENTE':
                    recomendacion = f'Revisar {outliers_count} registros con valores extremos'
                    prioridad = 'MEDIA'
                    impacto = 'Mejora robustez de modelos'
                else:
                    recomendacion = f'Monitorear {outliers_count} registros atípicos'
                    prioridad = 'BAJA'
                    impacto = 'Mantiene calidad del dataset'
                
                recommendations_data.append({
                    'variable': variable,
                    'accion_principal': accion,
                    'recomendacion_detallada': recomendacion,
                    'prioridad': prioridad,
                    'impacto_esperado': impacto,
                    'registros_afectados': outliers_count,
                    'porcentaje_datos': pct_outliers,
                    'justificacion_tecnica': row['justificacion']
                })
        
        return pd.DataFrame(recommendations_data)
    
    def create_action_matrix(self):
        """Crea matriz de acción por variable"""
        if self.outliers_df.empty:
            return pd.DataFrame()
            
        action_data = []
        
        for _, row in self.outliers_df.iterrows():
            variable = row['variable']
            outliers_count = row['outliers_iqr']
            pct_outliers = row['pct_outliers_iqr']
            severidad = row['severidad_outliers']
            
            # Determinar estado y acción
            if outliers_count == 0:
                status = 'LIMPIA'
                accion_principal = 'USAR_DIRECTAMENTE'
            elif severidad == 'CRITICA':
                status = 'CRITICA'
                accion_principal = 'LIMPIAR_URGENTE'
            elif severidad == 'ALTA':
                status = 'ATENCION'
                accion_principal = 'REVISAR_DETALLADAMENTE'
            else:
                status = 'MONITOREO'
                accion_principal = 'VIGILAR_EVOLUCION'
            
            action_data.append({
                'variable': variable,
                'status': status,
                'accion_principal': accion_principal,
                'outliers_iqr': outliers_count,
                'outliers_zscore': row['outliers_zscore'],
                'outliers_logicos': row['outliers_logicos'],
                'pct_outliers_iqr': pct_outliers,
                'severidad': severidad,
                'valor_min': row['valor_min'],
                'valor_max': row['valor_max'],
                'q1': row['q1'],
                'mediana': row['mediana'],
                'q3': row['q3'],
                'limite_inf_iqr': row['limite_inf_iqr'],
                'limite_sup_iqr': row['limite_sup_iqr'],
                'accion_recomendada': row['accion_recomendada']
            })
        
        return pd.DataFrame(action_data)
    
    def create_alerts_report(self):
        """Crea reporte de alertas críticas"""
        if self.outliers_df.empty:
            return pd.DataFrame()
            
        alerts_data = []
        
        for _, row in self.outliers_df.iterrows():
            variable = row['variable']
            outliers_logicos = row['outliers_logicos']
            outliers_iqr = row['outliers_iqr']
            pct_outliers = row['pct_outliers_iqr']
            
            # Generar alertas según criterios
            if outliers_logicos > 0:
                alerts_data.append({
                    'severidad': 'CRITICA',
                    'mensaje': f'{variable} tiene {outliers_logicos} valores fuera de rango lógico',
                    'accion_requerida': 'CORREGIR_DATOS_INMEDIATAMENTE'
                })
            
            if pct_outliers > 15:
                alerts_data.append({
                    'severidad': 'ALTA',
                    'mensaje': f'{variable} tiene {pct_outliers:.1f}% de outliers - Muy alta variabilidad',
                    'accion_requerida': 'REVISAR_PROCESO_CAPTURA'
                })
            elif pct_outliers > 5:
                alerts_data.append({
                    'severidad': 'MEDIA',
                    'mensaje': f'{variable} tiene {pct_outliers:.1f}% de outliers - Variabilidad moderada',
                    'accion_requerida': 'MONITOREAR_TENDENCIA'
                })
        
        return pd.DataFrame(alerts_data)
    
    def create_summary_dashboard(self):
        """Crea dashboard de resumen ejecutivo"""
        if self.outliers_df.empty:
            return {}
            
        total_variables = len(self.outliers_df)
        variables_con_outliers = len(self.outliers_df[self.outliers_df['outliers_iqr'] > 0])
        variables_criticas = len(self.outliers_df[self.outliers_df['severidad_outliers'] == 'CRITICA'])
        total_outliers = self.outliers_df['outliers_iqr'].sum()
        
        # Variables más problemáticas
        top_problemas = self.outliers_df.nlargest(5, 'outliers_iqr')[['variable', 'outliers_iqr', 'pct_outliers_iqr', 'accion_recomendada']]
        
        dashboard = {
            'resumen_general': {
                'total_variables': total_variables,
                'variables_con_outliers': variables_con_outliers,
                'variables_criticas': variables_criticas,
                'total_outliers_detectados': total_outliers,
                'porcentaje_variables_problemáticas': (variables_con_outliers / total_variables) * 100
            },
            'top_problemas': top_problemas.to_dict('records')
        }
        
        return dashboard
    
    def generate_all_reports(self, output_dir):
        """Genera todos los reportes"""
        print("📊 Generando reportes de outliers...")
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar reportes
        insights_df = self.create_insights_report()
        recommendations_df = self.create_recommendations_report()
        action_matrix_df = self.create_action_matrix()
        alerts_df = self.create_alerts_report()
        dashboard = self.create_summary_dashboard()
        
        # Guardar archivos
        insights_df.to_csv(f'{output_dir}/F1_OutliersRep_Sep25_01_insights.csv', index=False, encoding='utf-8-sig')
        recommendations_df.to_csv(f'{output_dir}/F1_OutliersRep_Sep25_01_recommendations.csv', index=False, encoding='utf-8-sig')
        action_matrix_df.to_csv(f'{output_dir}/F1_OutliersRep_Sep25_01_action_matrix.csv', index=False, encoding='utf-8-sig')
        alerts_df.to_csv(f'{output_dir}/F1_OutliersRep_Sep25_01_alerts.csv', index=False, encoding='utf-8-sig')
        
        # Guardar dashboard como CSV
        dashboard_df = pd.DataFrame([dashboard['resumen_general']])
        dashboard_df.to_csv(f'{output_dir}/F1_OutliersRep_Sep25_01_dashboard.csv', index=False, encoding='utf-8-sig')
        
        return {
            'insights': insights_df,
            'recommendations': recommendations_df,
            'action_matrix': action_matrix_df,
            'alerts': alerts_df,
            'dashboard': dashboard
        }

def main():
    """Función principal"""
    print("🚀 GENERADOR DE REPORTES DE OUTLIERS")
    print("=" * 50)
    
    # Configurar rutas
    outliers_analysis_path = 'Estadisticas/Fase1/1.Outliers/sep25/num_F1Outl_Sep25_01.csv'
    original_data_path = 'Consolidados/pretratadaCol_num/Sep25/pretratadaCol_num_Sep25_01.csv'
    output_dir = 'Estadisticas/Reportes/1. Outliers/Sep25'
    
    # Crear generador
    generator = OutliersReportGenerator(outliers_analysis_path, original_data_path)
    
    # Cargar datos
    if not generator.load_data():
        return None
    
    # Generar reportes
    results = generator.generate_all_reports(output_dir)
    
    # Mostrar resumen
    dashboard = results['dashboard']
    print("\n" + "=" * 50)
    print("RESUMEN EJECUTIVO")
    print("=" * 50)
    
    resumen = dashboard['resumen_general']
    print(f"📊 Variables analizadas: {resumen['total_variables']}")
    print(f"⚠️  Variables con outliers: {resumen['variables_con_outliers']} ({resumen['porcentaje_variables_problemáticas']:.1f}%)")
    print(f"🚨 Variables críticas: {resumen['variables_criticas']}")
    print(f"📍 Total outliers detectados: {resumen['total_outliers_detectados']}")
    
    print(f"\n🔍 TOP 5 VARIABLES MÁS PROBLEMÁTICAS:")
    for problema in dashboard['top_problemas']:
        print(f"  • {problema['variable']}: {problema['outliers_iqr']} outliers ({problema['pct_outliers_iqr']:.1f}%) - {problema['accion_recomendada']}")
    
    print(f"\n✅ Reportes generados en: {output_dir}")
    print(f"   📋 F1_OutliersRep_Sep25_01_insights.csv")
    print(f"   💡 F1_OutliersRep_Sep25_01_recommendations.csv")
    print(f"   📊 F1_OutliersRep_Sep25_01_action_matrix.csv")
    print(f"   🚨 F1_OutliersRep_Sep25_01_alerts.csv")
    print(f"   📈 F1_OutliersRep_Sep25_01_dashboard.csv")
    
    return results

if __name__ == "__main__":
    results = main()

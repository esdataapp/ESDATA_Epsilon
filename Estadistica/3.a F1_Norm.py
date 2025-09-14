# 12. F1_Norm.py
"""
Análisis de Normalización de Variables Numéricas
Evalúa múltiples métodos de normalización y recomienda el mejor para cada variable

Métodos incluidos:
- StandardScaler (Z-Score normalization)
- MinMaxScaler (0-1 normalization) 
- RobustScaler (Median and IQR)
- Análisis de distribuciones (Normal, Log-normal, etc.)

Versión: 1.0
Última actualización: Enero 2025
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from scipy import stats
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

class NormalizationAnalyzer:
    """
    Analizador de métodos de normalización para variables numéricas
    """
    
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = pd.DataFrame()
        self.numeric_columns = []
        self.excluded_columns = [
            'id', 'PaginaWeb', 'Ciudad', 'Fecha_Scrap', 
            'tipo_propiedad', 'operacion', 'Colonia', 'latitud', 'longitud'
        ]
        
    def load_data(self):
        """Carga los datos y identifica columnas numéricas"""
        try:
            self.df = pd.read_csv(self.data_path, encoding='utf-8')
            print(f"✅ Datos cargados: {self.df.shape}")
            
            # Identificar columnas numéricas (excluyendo las especificadas)
            all_numeric = self.df.select_dtypes(include=[np.number]).columns.tolist()
            self.numeric_columns = [col for col in all_numeric if col not in self.excluded_columns]
            
            print(f"📊 Variables numéricas para normalizar: {len(self.numeric_columns)}")
            print(f"   Variables: {', '.join(self.numeric_columns[:5])}{'...' if len(self.numeric_columns) > 5 else ''}")
            
            return True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def analyze_distribution(self, column):
        """Analiza la distribución de una variable"""
        if self.df.empty:
            return {
                'distribution_type': 'NO_DATA',
                'normality_test': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'outlier_sensitivity': 'ALTA'
            }
            
        data = self.df[column].dropna()
        
        if len(data) == 0:
            return {
                'distribution_type': 'NO_DATA',
                'normality_test': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'outlier_sensitivity': 'ALTA'
            }
        
        # Test de normalidad (Shapiro-Wilk para muestras pequeñas, D'Agostino para grandes)
        if len(data) <= 5000:
            try:
                _, p_value = stats.shapiro(data)
            except:
                p_value = 0.0
        else:
            try:
                _, p_value = stats.normaltest(data)
            except:
                p_value = 0.0
        
        # Calcular métricas de distribución
        skewness = stats.skew(data)
        kurt = stats.kurtosis(data)
        
        # Determinar tipo de distribución
        if p_value > 0.05:
            dist_type = 'NORMAL'
        elif abs(skewness) > 2:
            if skewness > 0:
                dist_type = 'SESGO_DERECHA'
            else:
                dist_type = 'SESGO_IZQUIERDA'
        elif abs(kurt) > 2:
            dist_type = 'KURTOSIS_ALTA'
        else:
            dist_type = 'NO_NORMAL'
        
        # Evaluar sensibilidad a outliers
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        outliers = len(data[(data < q1 - 1.5*iqr) | (data > q3 + 1.5*iqr)])
        outlier_pct = (outliers / len(data)) * 100
        
        if outlier_pct > 10:
            outlier_sensitivity = 'ALTA'
        elif outlier_pct > 5:
            outlier_sensitivity = 'MEDIA'
        else:
            outlier_sensitivity = 'BAJA'
        
        return {
            'distribution_type': dist_type,
            'normality_test': p_value,
            'skewness': skewness,
            'kurtosis': kurt,
            'outlier_sensitivity': outlier_sensitivity,
            'outlier_percentage': outlier_pct
        }
    
    def apply_normalization_methods(self, column):
        """Aplica diferentes métodos de normalización a una columna"""
        if self.df.empty:
            return {}
            
        data = self.df[column].dropna().values.reshape(-1, 1)
        original_data = self.df[column].dropna()
        
        if len(data) == 0:
            return {}
        
        results = {}
        
        # 1. StandardScaler (Z-Score)
        try:
            scaler_std = StandardScaler()
            data_std = scaler_std.fit_transform(data).flatten()
            
            results['standard'] = {
                'method': 'StandardScaler',
                'mean': np.mean(data_std),
                'std': np.std(data_std),
                'min': np.min(data_std),
                'max': np.max(data_std),
                'range': np.max(data_std) - np.min(data_std),
                'skewness': stats.skew(data_std),
                'normality_improved': abs(stats.skew(data_std)) < abs(stats.skew(original_data))
            }
        except:
            results['standard'] = {'method': 'StandardScaler', 'error': 'FAILED'}
        
        # 2. MinMaxScaler (0-1)
        try:
            scaler_minmax = MinMaxScaler()
            data_minmax = scaler_minmax.fit_transform(data).flatten()
            
            results['minmax'] = {
                'method': 'MinMaxScaler',
                'mean': np.mean(data_minmax),
                'std': np.std(data_minmax),
                'min': np.min(data_minmax),
                'max': np.max(data_minmax),
                'range': np.max(data_minmax) - np.min(data_minmax),
                'skewness': stats.skew(data_minmax),
                'normality_improved': abs(stats.skew(data_minmax)) < abs(stats.skew(original_data))
            }
        except:
            results['minmax'] = {'method': 'MinMaxScaler', 'error': 'FAILED'}
        
        # 3. RobustScaler (Mediana e IQR)
        try:
            scaler_robust = RobustScaler()
            data_robust = scaler_robust.fit_transform(data).flatten()
            
            results['robust'] = {
                'method': 'RobustScaler',
                'mean': np.mean(data_robust),
                'std': np.std(data_robust),
                'min': np.min(data_robust),
                'max': np.max(data_robust),
                'range': np.max(data_robust) - np.min(data_robust),
                'skewness': stats.skew(data_robust),
                'normality_improved': abs(stats.skew(data_robust)) < abs(stats.skew(original_data))
            }
        except:
            results['robust'] = {'method': 'RobustScaler', 'error': 'FAILED'}
        
        # 4. Log Transform (si todos los valores son positivos)
        if np.all(original_data > 0):
            try:
                data_log = np.log1p(original_data)  # log(1+x) para evitar log(0)
                
                results['log'] = {
                    'method': 'LogTransform',
                    'mean': np.mean(data_log),
                    'std': np.std(data_log),
                    'min': np.min(data_log),
                    'max': np.max(data_log),
                    'range': np.max(data_log) - np.min(data_log),
                    'skewness': stats.skew(data_log),
                    'normality_improved': abs(stats.skew(data_log)) < abs(stats.skew(original_data))
                }
            except:
                results['log'] = {'method': 'LogTransform', 'error': 'FAILED'}
        
        return results
    
    def recommend_best_method(self, distribution_info, normalization_results):
        """Recomienda el mejor método de normalización"""
        
        if not normalization_results:
            return {
                'recommended_method': 'NINGUNO',
                'reason': 'No se pudieron aplicar métodos de normalización',
                'priority': 'BAJA'
            }
        
        # Criterios de selección
        dist_type = distribution_info['distribution_type']
        outlier_sens = distribution_info['outlier_sensitivity']
        skewness = abs(distribution_info['skewness'])
        
        recommendations = []
        
        # Evaluar cada método disponible
        for method_name, method_data in normalization_results.items():
            if 'error' in method_data:
                continue
                
            score = 0
            reasons = []
            
            # Criterio 1: Mejora en normalidad
            if method_data.get('normality_improved', False):
                score += 3
                reasons.append('mejora_normalidad')
            
            # Criterio 2: Reducción de asimetría
            if abs(method_data.get('skewness', 999)) < skewness:
                score += 2
                reasons.append('reduce_asimetria')
            
            # Criterio 3: Compatibilidad con distribución
            if dist_type == 'NORMAL' and method_name == 'standard':
                score += 3
                reasons.append('compatible_distribucion')
            elif dist_type in ['SESGO_DERECHA', 'SESGO_IZQUIERDA'] and method_name == 'log':
                score += 3
                reasons.append('corrige_sesgo')
            elif outlier_sens == 'ALTA' and method_name == 'robust':
                score += 3
                reasons.append('resistente_outliers')
            elif method_name == 'minmax':
                score += 1
                reasons.append('interpretabilidad_simple')
            
            # Criterio 4: Estabilidad (rango razonable)
            method_range = method_data.get('range', 999)
            if 0.1 <= method_range <= 10:
                score += 1
                reasons.append('rango_estable')
            
            recommendations.append({
                'method': method_name,
                'method_name': method_data['method'],
                'score': score,
                'reasons': reasons,
                'metrics': method_data
            })
        
        # Seleccionar el mejor
        if not recommendations:
            return {
                'recommended_method': 'NINGUNO',
                'reason': 'Ningún método aplicable',
                'priority': 'BAJA'
            }
        
        best = max(recommendations, key=lambda x: x['score'])
        
        # Determinar prioridad
        if best['score'] >= 5:
            priority = 'ALTA'
        elif best['score'] >= 3:
            priority = 'MEDIA'
        else:
            priority = 'BAJA'
        
        return {
            'recommended_method': best['method_name'],
            'method_code': best['method'],
            'score': best['score'],
            'reasons': ', '.join(best['reasons']),
            'priority': priority,
            'all_options': recommendations
        }
    
    def analyze_all_variables(self):
        """Analiza todas las variables numéricas"""
        print("\n🔄 Analizando métodos de normalización...")
        
        results = []
        
        for i, column in enumerate(self.numeric_columns, 1):
            print(f"  Procesando {i}/{len(self.numeric_columns)}: {column}")
            
            # Obtener estadísticas básicas
            if self.df.empty:
                continue
                
            col_data = self.df[column].dropna()
            
            if len(col_data) == 0:
                continue
            
            # Analizar distribución
            dist_info = self.analyze_distribution(column)
            
            # Aplicar métodos de normalización
            norm_results = self.apply_normalization_methods(column)
            
            # Obtener recomendación
            recommendation = self.recommend_best_method(dist_info, norm_results)
            
            # Compilar resultados
            result = {
                'variable': column,
                'n_valores': len(col_data),
                'n_valores_unicos': col_data.nunique(),
                'valor_min': col_data.min(),
                'valor_max': col_data.max(),
                'media': col_data.mean(),
                'mediana': col_data.median(),
                'desv_std': col_data.std(),
                'coef_variacion': col_data.std() / col_data.mean() if col_data.mean() != 0 else 0,
                
                # Información de distribución
                'tipo_distribucion': dist_info['distribution_type'],
                'p_value_normalidad': dist_info['normality_test'],
                'asimetria': dist_info['skewness'],
                'curtosis': dist_info['kurtosis'],
                'sensibilidad_outliers': dist_info['outlier_sensitivity'],
                'pct_outliers': dist_info.get('outlier_percentage', 0),
                
                # Recomendación
                'metodo_recomendado': recommendation['recommended_method'],
                'codigo_metodo': recommendation.get('method_code', ''),
                'puntuacion_recomendacion': recommendation.get('score', 0),
                'razon_recomendacion': recommendation.get('reasons', ''),
                'prioridad_normalizacion': recommendation['priority'],
                
                # Métricas de métodos específicos
                'std_mejora_normalidad': norm_results.get('standard', {}).get('normality_improved', False),
                'minmax_mejora_normalidad': norm_results.get('minmax', {}).get('normality_improved', False),
                'robust_mejora_normalidad': norm_results.get('robust', {}).get('normality_improved', False),
                'log_mejora_normalidad': norm_results.get('log', {}).get('normality_improved', False),
                
                'std_asimetria_final': norm_results.get('standard', {}).get('skewness', np.nan),
                'minmax_asimetria_final': norm_results.get('minmax', {}).get('skewness', np.nan),
                'robust_asimetria_final': norm_results.get('robust', {}).get('skewness', np.nan),
                'log_asimetria_final': norm_results.get('log', {}).get('skewness', np.nan),
            }
            
            results.append(result)
        
        return pd.DataFrame(results)
    
    def save_results(self, results_df, output_path):
        """Guarda los resultados del análisis"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Guardar CSV
            results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"✅ Análisis de normalización guardado en: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error guardando resultados: {e}")
            return False

def main():
    """Función principal"""
    print("🚀 ANÁLISIS DE MÉTODOS DE NORMALIZACIÓN")
    print("=" * 50)
    
    # Configurar rutas
    data_path = 'Consolidados/pretratadaCol_num/Sep25/pretratadaCol_num_Sep25_01.csv'
    output_path = 'Estadisticas/Fase1/1.Normalizacion/sep25/num_F1Norm_Sep25_01.csv'
    
    # Crear analizador
    analyzer = NormalizationAnalyzer(data_path)
    
    # Cargar datos
    if not analyzer.load_data():
        return None
    
    # Realizar análisis
    results_df = analyzer.analyze_all_variables()
    
    # Guardar resultados
    if analyzer.save_results(results_df, output_path):
        print("\n" + "=" * 50)
        print("RESUMEN DEL ANÁLISIS")
        print("=" * 50)
        
        total_vars = len(results_df)
        vars_necesitan_norm = len(results_df[results_df['prioridad_normalizacion'].isin(['ALTA', 'MEDIA'])])
        
        print(f"📊 Variables analizadas: {total_vars}")
        print(f"🔄 Variables que necesitan normalización: {vars_necesitan_norm}")
        print(f"📈 Porcentaje recomendado para normalizar: {(vars_necesitan_norm/total_vars)*100:.1f}%")
        
        # Mostrar métodos recomendados
        metodos_count = results_df['metodo_recomendado'].value_counts()
        print(f"\n🎯 MÉTODOS MÁS RECOMENDADOS:")
        for metodo, count in metodos_count.head(5).items():
            print(f"  • {metodo}: {count} variables")
        
        # Variables prioritarias
        vars_alta_prioridad = results_df[results_df['prioridad_normalizacion'] == 'ALTA']
        if len(vars_alta_prioridad) > 0:
            print(f"\n🚨 VARIABLES DE ALTA PRIORIDAD:")
            for _, row in vars_alta_prioridad.head(5).iterrows():
                print(f"  • {row['variable']}: {row['metodo_recomendado']} - {row['razon_recomendacion']}")
    
    return results_df

if __name__ == "__main__":
    results = main()

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class OutliersDetectorInmuebles:
    """
    Detector y evaluador de outliers para dataset de inmuebles con criterios
    estadísticos múltiples y recomendaciones contextuales.
    """
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None
        self.outliers_results = {}
        self.recommendations = {}
        
        # Rangos lógicos específicos para inmuebles (contexto Guadalajara/Zapopan)
        self.logical_ranges = {
            'precio': {'min': 100000, 'max': 100000000},  # 100K - 100M pesos
            'area_m2': {'min': 20, 'max': 2000},         # 20 - 2000 m²
            'area_total': {'min': 20, 'max': 5000},      # 20 - 5000 m²
            'area_cubierta': {'min': 15, 'max': 2000},   # 15 - 2000 m²
            'recamaras': {'min': 0, 'max': 10},          # 0 - 10 recámaras
            'banos_icon': {'min': 0.5, 'max': 15},       # 0.5 - 15 baños
            'estacionamientos': {'min': 0, 'max': 10},   # 0 - 10 estacionamientos
            'mantenimiento': {'min': 0, 'max': 50000},   # 0 - 50K pesos
            'tiempo_publicacion': {'min': 0, 'max': 730}, # 0 - 2 años
            'antiguedad_icon': {'min': 0, 'max': 200},   # 0 - 200 años
            'longitud': {'min': -104.5, 'max': -102.5},  # Zona metropolitana GDL
            'latitud': {'min': 20.3, 'max': 21.0}        # Zona metropolitana GDL
        }
    
    def load_data(self):
        """Carga el dataset"""
        try:
            self.df = pd.read_csv(self.filepath, encoding='utf-8')
            print(f"✅ Dataset cargado: {self.df.shape[0]} filas, {self.df.shape[1]} columnas")
        except UnicodeDecodeError:
            self.df = pd.read_csv(self.filepath, encoding='latin-1')
            print(f"✅ Dataset cargado con encoding latin-1")
        
        # Convertir columnas numéricas
        numeric_cols = ['area_m2', 'precio', 'mantenimiento', 'longitud', 'latitud', 
                       'tiempo_publicacion', 'area_total', 'area_cubierta', 'banos_icon',
                       'antiguedad_icon']
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
    
    def detect_iqr_outliers(self, series, variable_name):
        """Detecta outliers usando método IQR"""
        valid_data = series.dropna()
        if len(valid_data) < 4:
            return {'method': 'IQR', 'outliers_idx': [], 'bounds': None, 'count': 0}
        
        Q1 = valid_data.quantile(0.25)
        Q3 = valid_data.quantile(0.75)
        IQR = Q3 - Q1
        
        # Límites IQR estándar
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Límites IQR extremos (3 * IQR)
        extreme_lower = Q1 - 3 * IQR
        extreme_upper = Q3 + 3 * IQR
        
        # Identificar outliers
        outliers_mask = (series < lower_bound) | (series > upper_bound)
        extreme_outliers_mask = (series < extreme_lower) | (series > extreme_upper)
        
        outliers_idx = series[outliers_mask].index.tolist()
        extreme_outliers_idx = series[extreme_outliers_mask].index.tolist()
        
        return {
            'method': 'IQR',
            'outliers_idx': outliers_idx,
            'extreme_outliers_idx': extreme_outliers_idx,
            'bounds': {'lower': lower_bound, 'upper': upper_bound},
            'extreme_bounds': {'lower': extreme_lower, 'upper': extreme_upper},
            'count': len(outliers_idx),
            'extreme_count': len(extreme_outliers_idx),
            'percentage': (len(outliers_idx) / len(valid_data)) * 100,
            'Q1': Q1, 'Q3': Q3, 'IQR': IQR
        }
    
    def detect_zscore_outliers(self, series, threshold=3):
        """Detecta outliers usando Z-Score"""
        valid_data = series.dropna()
        if len(valid_data) < 3:
            return {'method': 'Z-Score', 'outliers_idx': [], 'count': 0}
        
        z_scores = np.abs(stats.zscore(valid_data))
        outliers_mask = z_scores > threshold
        moderate_outliers_mask = z_scores > 2  # Outliers moderados
        
        outliers_idx = valid_data[outliers_mask].index.tolist()
        moderate_outliers_idx = valid_data[moderate_outliers_mask].index.tolist()
        
        return {
            'method': 'Z-Score',
            'outliers_idx': outliers_idx,
            'moderate_outliers_idx': moderate_outliers_idx,
            'count': len(outliers_idx),
            'moderate_count': len(moderate_outliers_idx),
            'percentage': (len(outliers_idx) / len(valid_data)) * 100,
            'threshold': threshold,
            'max_zscore': z_scores.max(),
            'mean_zscore': z_scores.mean()
        }
    
    def detect_logical_outliers(self, series, variable_name):
        """Detecta outliers usando rangos lógicos específicos del dominio"""
        if variable_name not in self.logical_ranges:
            return {'method': 'Logical', 'outliers_idx': [], 'count': 0}
        
        ranges = self.logical_ranges[variable_name]
        valid_data = series.dropna()
        
        # Outliers por rango lógico
        logical_outliers_mask = (series < ranges['min']) | (series > ranges['max'])
        outliers_idx = series[logical_outliers_mask].index.tolist()
        
        # Valores imposibles (ej: área negativa)
        impossible_mask = series < 0
        impossible_idx = series[impossible_mask].index.tolist()
        
        return {
            'method': 'Logical',
            'outliers_idx': outliers_idx,
            'impossible_idx': impossible_idx,
            'count': len(outliers_idx),
            'impossible_count': len(impossible_idx),
            'percentage': (len(outliers_idx) / len(valid_data)) * 100 if len(valid_data) > 0 else 0,
            'ranges': ranges,
            'min_value': series.min(),
            'max_value': series.max()
        }
    
    def detect_frequency_outliers(self, series, threshold_pct=1):
        """Detecta valores raros por frecuencia baja"""
        valid_data = series.dropna()
        if len(valid_data) < 10:
            return {'method': 'Frequency', 'outliers_idx': [], 'count': 0}
        
        # Calcular frecuencias
        value_counts = valid_data.value_counts()
        total_count = len(valid_data)
        
        # Valores que aparecen menos del threshold_pct%
        rare_threshold = (threshold_pct / 100) * total_count
        rare_values = value_counts[value_counts <= rare_threshold].index
        
        # Encontrar índices de valores raros
        outliers_idx = []
        for rare_val in rare_values:
            outliers_idx.extend(series[series == rare_val].index.tolist())
        
        return {
            'method': 'Frequency',
            'outliers_idx': outliers_idx,
            'count': len(outliers_idx),
            'percentage': (len(outliers_idx) / len(valid_data)) * 100,
            'rare_values': rare_values.tolist(),
            'threshold_pct': threshold_pct,
            'unique_values': len(value_counts)
        }
    
    def evaluate_outlier_context(self, variable_name, outlier_info, series):
        """Evalúa el contexto del outlier para determinar si es error o valor legítimo"""
        recommendations = []
        
        # Reglas específicas por variable
        if variable_name == 'precio':
            # Precios muy altos pueden ser legítimos (propiedades de lujo)
            # Precios muy bajos probablemente son errores
            outlier_values = series.iloc[outlier_info.get('outliers_idx', [])]
            
            if len(outlier_values) > 0:
                if outlier_values.min() < 500000:  # Menos de 500K
                    recommendations.append({
                        'action': 'INVESTIGAR',
                        'reason': 'Precios muy bajos pueden ser errores de captura',
                        'severity': 'HIGH'
                    })
                
                if outlier_values.max() > 50000000:  # Más de 50M
                    recommendations.append({
                        'action': 'MANTENER',
                        'reason': 'Precios altos pueden ser propiedades de lujo legítimas',
                        'severity': 'LOW'
                    })
        
        elif variable_name in ['area_m2', 'area_total', 'area_cubierta']:
            outlier_values = series.iloc[outlier_info.get('outliers_idx', [])]
            
            if len(outlier_values) > 0:
                if outlier_values.min() < 30:
                    recommendations.append({
                        'action': 'ELIMINAR',
                        'reason': 'Áreas muy pequeñas probablemente son errores',
                        'severity': 'HIGH'
                    })
                
                if outlier_values.max() > 1000:
                    recommendations.append({
                        'action': 'INVESTIGAR',
                        'reason': 'Áreas muy grandes pueden ser desarrollos especiales',
                        'severity': 'MEDIUM'
                    })
        
        elif variable_name in ['longitud', 'latitud']:
            recommendations.append({
                'action': 'ELIMINAR',
                'reason': 'Coordenadas fuera de la zona metropolitana son errores',
                'severity': 'HIGH'
            })
        
        elif variable_name in ['recamaras', 'banos_icon', 'estacionamientos']:
            outlier_values = series.iloc[outlier_info.get('outliers_idx', [])]
            
            if len(outlier_values) > 0:
                if outlier_values.max() > 8:
                    recommendations.append({
                        'action': 'INVESTIGAR',
                        'reason': 'Valores muy altos pueden ser desarrollos comerciales o errores',
                        'severity': 'MEDIUM'
                    })
        
        elif variable_name == 'antiguedad_icon':
            outlier_values = series.iloc[outlier_info.get('impossible_idx', [])]
            
            if len(outlier_values) > 0:
                recommendations.append({
                    'action': 'ELIMINAR',
                    'reason': 'Antigüedad negativa es imposible',
                    'severity': 'HIGH'
                })
        
        # Recomendaciones generales
        if not recommendations:
            if outlier_info.get('percentage', 0) > 10:
                recommendations.append({
                    'action': 'INVESTIGAR',
                    'reason': 'Alto porcentaje de outliers sugiere problema sistemático',
                    'severity': 'MEDIUM'
                })
            else:
                recommendations.append({
                    'action': 'MANTENER',
                    'reason': 'Outliers normales para este tipo de variable',
                    'severity': 'LOW'
                })
        
        return recommendations
    
    def analyze_variable(self, variable_name):
        """Analiza una variable específica con todos los métodos"""
        if variable_name not in self.df.columns:
            return None
        
        series = self.df[variable_name]
        
        # Aplicar todos los métodos de detección
        results = {
            'variable': variable_name,
            'total_observations': len(series),
            'missing_values': series.isnull().sum(),
            'valid_observations': len(series.dropna())
        }
        
        # Método IQR
        iqr_result = self.detect_iqr_outliers(series, variable_name)
        results['iqr'] = iqr_result
        
        # Método Z-Score
        zscore_result = self.detect_zscore_outliers(series)
        results['zscore'] = zscore_result
        
        # Método de rangos lógicos
        logical_result = self.detect_logical_outliers(series, variable_name)
        results['logical'] = logical_result
        
        # Método de frecuencia (solo para variables con pocos valores únicos)
        if series.nunique() < len(series) * 0.1:  # Menos del 10% de valores únicos
            freq_result = self.detect_frequency_outliers(series)
            results['frequency'] = freq_result
        
        # Combinar todos los outliers únicos
        all_outliers = set()
        methods_detecting = []
        
        if iqr_result['count'] > 0:
            all_outliers.update(iqr_result['outliers_idx'])
            methods_detecting.append('IQR')
        
        if zscore_result['count'] > 0:
            all_outliers.update(zscore_result['outliers_idx'])
            methods_detecting.append('Z-Score')
        
        if logical_result['count'] > 0:
            all_outliers.update(logical_result['outliers_idx'])
            methods_detecting.append('Logical')
        
        results['summary'] = {
            'total_unique_outliers': len(all_outliers),
            'outlier_indices': list(all_outliers),
            'percentage_outliers': (len(all_outliers) / len(series.dropna())) * 100 if len(series.dropna()) > 0 else 0,
            'methods_detecting': methods_detecting,
            'consensus_outliers': []  # Outliers detectados por múltiples métodos
        }
        
        # Encontrar outliers detectados por múltiples métodos
        method_sets = []
        if iqr_result['count'] > 0:
            method_sets.append(set(iqr_result['outliers_idx']))
        if zscore_result['count'] > 0:
            method_sets.append(set(zscore_result['outliers_idx']))
        if logical_result['count'] > 0:
            method_sets.append(set(logical_result['outliers_idx']))
        
        if len(method_sets) >= 2:
            consensus = method_sets[0]
            for method_set in method_sets[1:]:
                consensus = consensus.intersection(method_set)
            results['summary']['consensus_outliers'] = list(consensus)
        
        # Evaluar contexto y generar recomendaciones
        recommendations = self.evaluate_outlier_context(variable_name, results['summary'], series)
        results['recommendations'] = recommendations
        
        return results
    
    def analyze_all_numeric_variables(self):
        """Analiza todas las variables numéricas"""
        # Variables a excluir del análisis de outliers
        variables_excluir = {
            'id', 'PaginaWeb', 'Ciudad', 'Fecha_Scrap', 
            'tipo_propiedad', 'operacion', 'Colonia', 
            'latitud', 'longitud'  # Excluimos lat/long porque ya están filtradas geográficamente
        }
        
        numeric_vars = [col for col in self.df.select_dtypes(include=[np.number]).columns.tolist() 
                       if col not in variables_excluir]
        
        print(f"🔍 Analizando outliers en {len(numeric_vars)} variables numéricas...")
        print(f"📋 Variables a analizar: {', '.join(numeric_vars)}")
        
        for var in numeric_vars:
            print(f"   Procesando: {var}")
            self.outliers_results[var] = self.analyze_variable(var)
    
    def create_outliers_summary(self):
        """Crea un resumen consolidado de todos los outliers"""
        summary_data = []
        
        for var_name, results in self.outliers_results.items():
            if results is None:
                continue
            
            # Información básica
            row = {
                'variable': var_name,
                'total_obs': results['total_observations'],
                'missing_values': results['missing_values'],
                'valid_obs': results['valid_observations']
            }
            
            # Resultados por método
            row['iqr_outliers'] = results['iqr']['count']
            row['iqr_percentage'] = results['iqr']['percentage']
            row['iqr_lower_bound'] = results['iqr']['bounds']['lower'] if results['iqr']['bounds'] else None
            row['iqr_upper_bound'] = results['iqr']['bounds']['upper'] if results['iqr']['bounds'] else None
            
            row['zscore_outliers'] = results['zscore']['count']
            row['zscore_percentage'] = results['zscore']['percentage']
            row['max_zscore'] = results['zscore']['max_zscore']
            
            row['logical_outliers'] = results['logical']['count']
            row['logical_percentage'] = results['logical']['percentage']
            row['impossible_values'] = results['logical']['impossible_count']
            
            # Resumen general
            row['total_unique_outliers'] = results['summary']['total_unique_outliers']
            row['consensus_outliers'] = len(results['summary']['consensus_outliers'])
            row['methods_agreeing'] = len(results['summary']['methods_detecting'])
            row['outlier_percentage_total'] = results['summary']['percentage_outliers']
            
            # Recomendaciones
            high_severity = sum(1 for r in results['recommendations'] if r['severity'] == 'HIGH')
            medium_severity = sum(1 for r in results['recommendations'] if r['severity'] == 'MEDIUM')
            low_severity = sum(1 for r in results['recommendations'] if r['severity'] == 'LOW')
            
            row['high_severity_issues'] = high_severity
            row['medium_severity_issues'] = medium_severity
            row['low_severity_issues'] = low_severity
            
            # Acción recomendada principal
            if high_severity > 0:
                row['main_recommendation'] = 'CRITICAL_REVIEW'
            elif medium_severity > 0:
                row['main_recommendation'] = 'INVESTIGATE'
            else:
                row['main_recommendation'] = 'MONITOR'
            
            summary_data.append(row)
        
        return pd.DataFrame(summary_data)
    
    def create_detailed_outliers_report(self):
        """Crea un reporte detallado de cada outlier identificado"""
        detailed_data = []
        
        for var_name, results in self.outliers_results.items():
            if results is None or results['summary']['total_unique_outliers'] == 0:
                continue
            
            outlier_indices = results['summary']['outlier_indices']
            
            for idx in outlier_indices:
                row = {
                    'variable': var_name,
                    'index': idx,
                    'value': self.df.loc[idx, var_name],
                    'detected_by_iqr': idx in results['iqr']['outliers_idx'],
                    'detected_by_zscore': idx in results['zscore']['outliers_idx'],
                    'detected_by_logical': idx in results['logical']['outliers_idx'],
                    'methods_count': sum([
                        idx in results['iqr']['outliers_idx'],
                        idx in results['zscore']['outliers_idx'],
                        idx in results['logical']['outliers_idx']
                    ]),
                    'is_consensus': idx in results['summary']['consensus_outliers'],
                    'is_impossible': idx in results['logical'].get('impossible_idx', [])
                }
                
                # Añadir información contextual del registro
                if 'precio' in self.df.columns:
                    row['precio'] = self.df.loc[idx, 'precio']
                if 'area_m2' in self.df.columns:
                    row['area_m2'] = self.df.loc[idx, 'area_m2']
                if 'Ciudad' in self.df.columns:
                    row['ciudad'] = self.df.loc[idx, 'Ciudad']
                if 'Colonia' in self.df.columns:
                    row['colonia'] = self.df.loc[idx, 'Colonia']
                
                detailed_data.append(row)
        
        return pd.DataFrame(detailed_data)
    
    def generate_recommendations_report(self):
        """Genera un reporte de recomendaciones por variable"""
        recommendations_data = []
        
        for var_name, results in self.outliers_results.items():
            if results is None:
                continue
            
            for rec in results['recommendations']:
                recommendations_data.append({
                    'variable': var_name,
                    'action': rec['action'],
                    'reason': rec['reason'],
                    'severity': rec['severity'],
                    'outliers_count': results['summary']['total_unique_outliers'],
                    'outliers_percentage': results['summary']['percentage_outliers']
                })
        
        return pd.DataFrame(recommendations_data)
    
    def run_complete_analysis(self, output_file='num_F1Outl_Sep25_01.csv'):
        """Ejecuta el análisis completo de outliers"""
        print("🔍 ANÁLISIS DE OUTLIERS - DATASET INMUEBLES")
        print("=" * 60)
        
        # Cargar datos
        self.load_data()
        
        # Variables a excluir del análisis
        variables_excluir = {
            'id', 'PaginaWeb', 'Ciudad', 'Fecha_Scrap', 
            'tipo_propiedad', 'operacion', 'Colonia', 
            'latitud', 'longitud'
        }
        
        # Analizar solo variables numéricas que no estén excluidas
        numeric_columns = self.df.select_dtypes(include=[np.number]).columns
        variables_analizar = [col for col in numeric_columns if col not in variables_excluir]
        
        print(f"📊 Variables a analizar: {len(variables_analizar)}")
        print(f"   Variables: {list(variables_analizar)}")
        
        # Analizar variables
        for col in variables_analizar:
            if col in self.df.columns:
                print(f"   Analizando outliers en: {col}")
                self.detect_outliers_variable(col)
        
        # Crear reporte consolidado
        print("\n📊 Generando reporte consolidado...")
        
        # Combinar todos los resultados en un DataFrame similar al F1_Descriptivo
        outliers_data = []
        
        for variable, results in self.outliers_results.items():
            if variable in variables_excluir:
                continue
                
            row_data = {
                'variable': variable,
                'total_registros': len(self.df),
                'valores_validos': self.df[variable].count(),
                'valores_nulos': self.df[variable].isnull().sum(),
                'pct_nulos': (self.df[variable].isnull().sum() / len(self.df)) * 100,
                
                # Outliers por método
                'outliers_iqr': len(results.get('iqr_outliers', [])),
                'outliers_zscore': len(results.get('zscore_outliers', [])),
                'outliers_logicos': len(results.get('logical_outliers', [])),
                'outliers_modificados_zscore': len(results.get('modified_zscore_outliers', [])),
                
                # Percentiles de outliers
                'pct_outliers_iqr': (len(results.get('iqr_outliers', [])) / self.df[variable].count()) * 100 if self.df[variable].count() > 0 else 0,
                'pct_outliers_zscore': (len(results.get('zscore_outliers', [])) / self.df[variable].count()) * 100 if self.df[variable].count() > 0 else 0,
                'pct_outliers_logicos': (len(results.get('logical_outliers', [])) / self.df[variable].count()) * 100 if self.df[variable].count() > 0 else 0,
                
                # Estadísticas básicas
                'valor_min': self.df[variable].min(),
                'valor_max': self.df[variable].max(),
                'q1': self.df[variable].quantile(0.25),
                'mediana': self.df[variable].median(),
                'q3': self.df[variable].quantile(0.75),
                'iqr': self.df[variable].quantile(0.75) - self.df[variable].quantile(0.25),
                
                # Límites de outliers
                'limite_inf_iqr': self.df[variable].quantile(0.25) - 1.5 * (self.df[variable].quantile(0.75) - self.df[variable].quantile(0.25)),
                'limite_sup_iqr': self.df[variable].quantile(0.75) + 1.5 * (self.df[variable].quantile(0.75) - self.df[variable].quantile(0.25)),
                
                # Rangos lógicos si aplican
                'rango_logico_min': self.logical_ranges.get(variable, {}).get('min', np.nan),
                'rango_logico_max': self.logical_ranges.get(variable, {}).get('max', np.nan),
                
                # Evaluación y recomendación
                'severidad_outliers': self._evaluar_severidad(variable, results),
                'accion_recomendada': self._generar_recomendacion(variable, results),
                'justificacion': self._generar_justificacion(variable, results)
            }
            
            outliers_data.append(row_data)
        
        # Crear DataFrame y guardar
        outliers_df = pd.DataFrame(outliers_data)
        outliers_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        # Mostrar resumen ejecutivo
        print("\n" + "="*60)
        print("RESUMEN EJECUTIVO DE OUTLIERS")
        print("="*60)
        
        total_outliers_iqr = outliers_df['outliers_iqr'].sum()
        variables_con_outliers = len(outliers_df[outliers_df['outliers_iqr'] > 0])
        variables_criticas = len(outliers_df[outliers_df['severidad_outliers'] == 'CRITICA'])
        
        print(f"📊 Variables analizadas: {len(outliers_df)}")
        print(f"⚠️  Variables con outliers (IQR): {variables_con_outliers}")
        print(f"🚨 Variables críticas: {variables_criticas}")
        print(f"📍 Total de outliers (IQR): {total_outliers_iqr}")
        
        if len(outliers_df) > 0:
            print(f"\n🔍 TOP 5 VARIABLES CON MÁS OUTLIERS:")
            top_outliers = outliers_df.nlargest(5, 'outliers_iqr')[['variable', 'outliers_iqr', 'pct_outliers_iqr', 'accion_recomendada']]
            for _, row in top_outliers.iterrows():
                print(f"  • {row['variable']}: {row['outliers_iqr']} outliers ({row['pct_outliers_iqr']:.1f}%) - {row['accion_recomendada']}")
        
        print(f"\n✅ Análisis completado")
        print(f"📁 Archivo generado: {output_file}")
        
        return outliers_df
    
    def detect_outliers_variable(self, column):
        """Detecta outliers en una variable específica usando múltiples métodos"""
        if column not in self.df.columns or self.df[column].isnull().all():
            return
        
        outliers_info = {}
        series_clean = self.df[column].dropna()
        
        if len(series_clean) == 0:
            return
        
        # 1. Método IQR
        Q1 = series_clean.quantile(0.25)
        Q3 = series_clean.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        iqr_outliers = self.df[(self.df[column] < lower_bound) | (self.df[column] > upper_bound)].index.tolist()
        outliers_info['iqr_outliers'] = iqr_outliers
        
        # 2. Método Z-Score
        if len(series_clean) > 1:
            z_scores = np.abs(stats.zscore(series_clean))
            zscore_outliers = series_clean[z_scores > 3].index.tolist()
            outliers_info['zscore_outliers'] = zscore_outliers
        else:
            outliers_info['zscore_outliers'] = []
        
        # 3. Z-Score Modificado (más robusto)
        if len(series_clean) > 1:
            median = series_clean.median()
            mad = np.median(np.abs(series_clean - median))
            modified_z_scores = 0.6745 * (series_clean - median) / mad if mad != 0 else np.zeros(len(series_clean))
            modified_zscore_outliers = series_clean[np.abs(modified_z_scores) > 3.5].index.tolist()
            outliers_info['modified_zscore_outliers'] = modified_zscore_outliers
        else:
            outliers_info['modified_zscore_outliers'] = []
        
        # 4. Rangos lógicos
        logical_outliers = []
        if column in self.logical_ranges:
            min_val = self.logical_ranges[column]['min']
            max_val = self.logical_ranges[column]['max']
            logical_outliers = self.df[(self.df[column] < min_val) | (self.df[column] > max_val)].index.tolist()
        outliers_info['logical_outliers'] = logical_outliers
        
        self.outliers_results[column] = outliers_info
    
    def _evaluar_severidad(self, variable, results):
        """Evalúa la severidad de los outliers en una variable"""
        total_records = len(self.df)
        iqr_outliers = len(results.get('iqr_outliers', []))
        logical_outliers = len(results.get('logical_outliers', []))
        
        iqr_pct = (iqr_outliers / total_records) * 100 if total_records > 0 else 0
        logical_pct = (logical_outliers / total_records) * 100 if total_records > 0 else 0
        
        if logical_pct > 5 or iqr_pct > 15:
            return 'CRITICA'
        elif logical_pct > 1 or iqr_pct > 5:
            return 'ALTA'
        elif iqr_pct > 1:
            return 'MEDIA'
        else:
            return 'BAJA'
    
    def _generar_recomendacion(self, variable, results):
        """Genera recomendación de acción para los outliers"""
        severidad = self._evaluar_severidad(variable, results)
        logical_outliers = len(results.get('logical_outliers', []))
        iqr_outliers = len(results.get('iqr_outliers', []))
        
        if logical_outliers > 0:
            return 'ELIMINAR_VALORES_IMPOSIBLES'
        elif severidad == 'CRITICA':
            return 'INVESTIGAR_Y_LIMPIAR'
        elif severidad == 'ALTA':
            return 'REVISAR_DETALLADAMENTE'
        elif severidad == 'MEDIA':
            return 'MONITOREAR'
        else:
            return 'MANTENER'
    
    def _generar_justificacion(self, variable, results):
        """Genera justificación para la recomendación"""
        iqr_outliers = len(results.get('iqr_outliers', []))
        logical_outliers = len(results.get('logical_outliers', []))
        zscore_outliers = len(results.get('zscore_outliers', []))
        
        justificaciones = []
        
        if logical_outliers > 0:
            justificaciones.append(f"{logical_outliers} valores fuera de rango lógico")
        
        if iqr_outliers > 0:
            pct_iqr = (iqr_outliers / len(self.df)) * 100
            justificaciones.append(f"{iqr_outliers} outliers IQR ({pct_iqr:.1f}%)")
        
        if zscore_outliers > 0:
            justificaciones.append(f"{zscore_outliers} outliers Z-Score")
        
        if not justificaciones:
            return "No se detectaron outliers significativos"
        
        return "; ".join(justificaciones)
        print(f"   📋 {output_prefix}_summary.csv - Resumen por variable")
        print(f"   📝 {output_prefix}_detailed.csv - Detalle de cada outlier")
        print(f"   💡 {output_prefix}_recommendations.csv - Recomendaciones de acción")
        
        return {
            'summary': summary_df,
            'detailed': detailed_df,
            'recommendations': recommendations_df
        }

# Función principal
def main():
    """Ejecuta el análisis de outliers"""
    # Ruta corregida para el archivo de datos
    input_file = 'Consolidados/pretratadaCol_num/Sep25/pretratadaCol_num_Sep25_01.csv'
    output_dir = 'Estadisticas/Fase1/1.Outliers/sep25'
    output_file = f'{output_dir}/num_F1Outl_Sep25_01.csv'
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    detector = OutliersDetectorInmuebles(input_file)
    results = detector.run_complete_analysis(output_file)
    
    return results

if __name__ == "__main__":
    analysis_results = main()
    


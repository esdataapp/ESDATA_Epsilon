import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class InmueblesStatsAnalyzer:
    """
    Analizador estadístico para dataset de inmuebles con clasificación automática 
    de variables y estadísticas descriptivas exhaustivas.
    """
    
    def __init__(self, filepath):
        """Inicializa el analizador con el archivo CSV"""
        self.filepath = filepath
        self.df = None
        self.variable_types = {}
        self.stats_results = {}
        
    def load_data(self):
        """Carga el dataset y maneja encoding"""
        try:
            self.df = pd.read_csv(self.filepath, encoding='utf-8')
            print(f"✅ Dataset cargado: {self.df.shape[0]} filas, {self.df.shape[1]} columnas")
        except UnicodeDecodeError:
            self.df = pd.read_csv(self.filepath, encoding='latin-1')
            print(f"✅ Dataset cargado con encoding latin-1: {self.df.shape[0]} filas, {self.df.shape[1]} columnas")
    
    def classify_variables(self):
        """Clasifica automáticamente los tipos de variables"""
        
        # Variables a excluir del análisis estadístico
        variables_excluir = {
            'id', 'PaginaWeb', 'Ciudad', 'Fecha_Scrap', 
            'tipo_propiedad', 'operacion', 'Colonia', 
            'latitud', 'longitud'
        }
        
        # Definición manual basada en la documentación
        manual_classification = {
            # Numéricas continuas
            'area_m2': 'numerica_continua',
            'precio': 'numerica_continua', 
            'mantenimiento': 'numerica_continua',
            'tiempo_publicacion': 'numerica_continua',
            'area_total': 'numerica_continua',
            'area_cubierta': 'numerica_continua',
            'banos_icon': 'numerica_continua',
            
            # Numéricas discretas
            'recamaras': 'numerica_discreta',
            'estacionamientos': 'numerica_discreta', 
            'estacionamientos_icon': 'numerica_discreta',
            'recamaras_icon': 'numerica_discreta',
            'medio_banos_icon': 'numerica_discreta',
            'antiguedad_icon': 'numerica_discreta',
        }
        
        # Aplicar clasificación manual y verificar con datos reales
        for col in self.df.columns:
            # Excluir variables no relevantes para análisis estadístico
            if col in variables_excluir:
                continue
                
            if col in manual_classification:
                self.variable_types[col] = manual_classification[col]
            else:
                # Clasificación automática para variables no especificadas
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    unique_ratio = self.df[col].nunique() / len(self.df[col])
                    if unique_ratio > 0.05:  # Más del 5% de valores únicos
                        self.variable_types[col] = 'numerica_continua'
                    else:
                        self.variable_types[col] = 'numerica_discreta'
                else:
                    # Intentar convertir a fecha
                    try:
                        pd.to_datetime(self.df[col].dropna().iloc[0])
                        self.variable_types[col] = 'fecha'
                    except:
                        self.variable_types[col] = 'categorica'
    
    def calculate_numeric_stats(self, series, var_type):
        """Calcula estadísticas para variables numéricas"""
        stats_dict = {}
        
        # Información básica
        stats_dict['tipo_variable'] = var_type
        stats_dict['total_observaciones'] = len(series)
        stats_dict['valores_faltantes'] = series.isnull().sum()
        stats_dict['valores_faltantes_pct'] = (series.isnull().sum() / len(series)) * 100
        stats_dict['valores_unicos'] = series.nunique()
        stats_dict['valores_duplicados'] = len(series) - series.nunique()
        
        # Solo calcular si hay datos válidos
        valid_data = series.dropna()
        if len(valid_data) == 0:
            return stats_dict
            
        # Medidas de tendencia central
        stats_dict['media'] = valid_data.mean()
        stats_dict['mediana'] = valid_data.median()
        try:
            stats_dict['moda'] = valid_data.mode().iloc[0] if len(valid_data.mode()) > 0 else np.nan
        except:
            stats_dict['moda'] = np.nan
            
        # Medidas de dispersión
        stats_dict['desviacion_estandar'] = valid_data.std()
        stats_dict['varianza'] = valid_data.var()
        stats_dict['rango'] = valid_data.max() - valid_data.min()
        stats_dict['rango_intercuartil'] = valid_data.quantile(0.75) - valid_data.quantile(0.25)
        stats_dict['coeficiente_variacion'] = (valid_data.std() / valid_data.mean()) * 100 if valid_data.mean() != 0 else np.nan
        
        # Medidas de forma
        stats_dict['asimetria'] = valid_data.skew()
        stats_dict['curtosis'] = valid_data.kurtosis()
        
        # Valores extremos
        stats_dict['valor_minimo'] = valid_data.min()
        stats_dict['valor_maximo'] = valid_data.max()
        
        # Percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            stats_dict[f'percentil_{p}'] = valid_data.quantile(p/100)
        
        # Detección de outliers (método IQR)
        Q1 = valid_data.quantile(0.25)
        Q3 = valid_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = valid_data[(valid_data < lower_bound) | (valid_data > upper_bound)]
        stats_dict['outliers_count'] = len(outliers)
        stats_dict['outliers_pct'] = (len(outliers) / len(valid_data)) * 100
        
        # Test de normalidad (Shapiro-Wilk para muestras pequeñas)
        if len(valid_data) >= 3 and len(valid_data) <= 5000:
            try:
                shapiro_stat, shapiro_p = stats.shapiro(valid_data.sample(min(5000, len(valid_data))))
                stats_dict['normalidad_shapiro_stat'] = shapiro_stat
                stats_dict['normalidad_shapiro_pvalue'] = shapiro_p
                stats_dict['es_normal_alpha_005'] = shapiro_p > 0.05
            except:
                stats_dict['normalidad_shapiro_stat'] = np.nan
                stats_dict['normalidad_shapiro_pvalue'] = np.nan
                stats_dict['es_normal_alpha_005'] = np.nan
        
        return stats_dict
    
    def calculate_categorical_stats(self, series):
        """Calcula estadísticas para variables categóricas"""
        stats_dict = {}
        
        # Información básica
        stats_dict['tipo_variable'] = 'categorica'
        stats_dict['total_observaciones'] = len(series)
        stats_dict['valores_faltantes'] = series.isnull().sum()
        stats_dict['valores_faltantes_pct'] = (series.isnull().sum() / len(series)) * 100
        stats_dict['categorias_unicas'] = series.nunique()
        
        # Solo calcular si hay datos válidos
        valid_data = series.dropna()
        if len(valid_data) == 0:
            return stats_dict
        
        # Frecuencias
        freq_table = valid_data.value_counts()
        stats_dict['categoria_mas_frecuente'] = freq_table.index[0] if len(freq_table) > 0 else np.nan
        stats_dict['frecuencia_maxima'] = freq_table.iloc[0] if len(freq_table) > 0 else 0
        stats_dict['frecuencia_maxima_pct'] = (freq_table.iloc[0] / len(valid_data)) * 100 if len(freq_table) > 0 else 0
        
        # Categoría menos frecuente
        stats_dict['categoria_menos_frecuente'] = freq_table.index[-1] if len(freq_table) > 0 else np.nan
        stats_dict['frecuencia_minima'] = freq_table.iloc[-1] if len(freq_table) > 0 else 0
        stats_dict['frecuencia_minima_pct'] = (freq_table.iloc[-1] / len(valid_data)) * 100 if len(freq_table) > 0 else 0
        
        # Entropía (medida de diversidad)
        proportions = freq_table / len(valid_data)
        entropy = -np.sum(proportions * np.log2(proportions + 1e-10))  # +1e-10 para evitar log(0)
        stats_dict['entropia'] = entropy
        stats_dict['entropia_normalizada'] = entropy / np.log2(len(freq_table)) if len(freq_table) > 1 else 0
        
        # Concentración (índice de Herfindahl)
        herfindahl = np.sum(proportions ** 2)
        stats_dict['indice_concentracion'] = herfindahl
        
        # Top 5 categorías más frecuentes
        top_5 = freq_table.head(5)
        for i, (cat, freq) in enumerate(top_5.items(), 1):
            stats_dict[f'top_{i}_categoria'] = cat
            stats_dict[f'top_{i}_frecuencia'] = freq
            stats_dict[f'top_{i}_porcentaje'] = (freq / len(valid_data)) * 100
            
        return stats_dict
    
    def calculate_date_stats(self, series):
        """Calcula estadísticas para variables de fecha"""
        stats_dict = {}
        
        # Información básica
        stats_dict['tipo_variable'] = 'fecha'
        stats_dict['total_observaciones'] = len(series)
        stats_dict['valores_faltantes'] = series.isnull().sum()
        stats_dict['valores_faltantes_pct'] = (series.isnull().sum() / len(series)) * 100
        
        # Convertir a datetime
        try:
            # Intentar diferentes formatos de fecha
            date_series = pd.to_datetime(series, dayfirst=True, errors='coerce')
            if date_series.isnull().all():
                date_series = pd.to_datetime(series, format='%d/%m/%Y', errors='coerce')
            
            valid_dates = date_series.dropna()
            
            if len(valid_dates) == 0:
                stats_dict['error_conversion'] = 'No se pudieron convertir fechas'
                return stats_dict
            
            # Rango de fechas
            stats_dict['fecha_minima'] = valid_dates.min()
            stats_dict['fecha_maxima'] = valid_dates.max()
            stats_dict['rango_dias'] = (valid_dates.max() - valid_dates.min()).days
            
            # Fecha más común
            freq_table = valid_dates.value_counts()
            stats_dict['fecha_mas_frecuente'] = freq_table.index[0] if len(freq_table) > 0 else np.nan
            stats_dict['frecuencia_maxima'] = freq_table.iloc[0] if len(freq_table) > 0 else 0
            
            # Análisis por componentes
            stats_dict['anos_unicos'] = valid_dates.dt.year.nunique()
            stats_dict['meses_unicos'] = valid_dates.dt.month.nunique() 
            stats_dict['dias_unicos'] = valid_dates.dt.day.nunique()
            
            # Año más frecuente
            year_freq = valid_dates.dt.year.value_counts()
            stats_dict['ano_mas_frecuente'] = year_freq.index[0] if len(year_freq) > 0 else np.nan
            
            # Mes más frecuente  
            month_freq = valid_dates.dt.month.value_counts()
            stats_dict['mes_mas_frecuente'] = month_freq.index[0] if len(month_freq) > 0 else np.nan
            
        except Exception as e:
            stats_dict['error_conversion'] = str(e)
            
        return stats_dict
    
    def analyze_all_variables(self):
        """Analiza todas las variables del dataset"""
        print("🔍 Iniciando análisis estadístico exhaustivo...")
        
        for col in self.df.columns:
            # Solo analizar variables que están en variable_types (no excluidas)
            if col not in self.variable_types:
                continue
                
            print(f"   Analizando: {col} ({self.variable_types[col]})")
            
            if self.variable_types[col] in ['numerica_continua', 'numerica_discreta']:
                # Convertir a numérico si es necesario
                if not pd.api.types.is_numeric_dtype(self.df[col]):
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                self.stats_results[col] = self.calculate_numeric_stats(self.df[col], self.variable_types[col])
                
            elif self.variable_types[col] == 'categorica':
                self.stats_results[col] = self.calculate_categorical_stats(self.df[col])
                
            elif self.variable_types[col] == 'fecha':
                self.stats_results[col] = self.calculate_date_stats(self.df[col])
    
    def create_summary_dataframe(self):
        """Crea un DataFrame resumen con todas las estadísticas"""
        # Convertir diccionario de resultados a DataFrame
        df_stats = pd.DataFrame.from_dict(self.stats_results, orient='index')
        
        # Añadir columna con nombre de variable
        df_stats.insert(0, 'nombre_variable', df_stats.index)
        
        # Reordenar columnas para mejor presentación
        priority_cols = ['nombre_variable', 'tipo_variable', 'total_observaciones', 
                        'valores_faltantes', 'valores_faltantes_pct', 'valores_unicos']
        
        remaining_cols = [col for col in df_stats.columns if col not in priority_cols]
        final_cols = priority_cols + remaining_cols
        
        df_stats = df_stats[final_cols]
        
        return df_stats
    
    def run_complete_analysis(self, output_path='estadisticas_descriptivas_inmuebles.csv'):
        """Ejecuta el análisis completo y guarda resultados"""
        print("🏠 ANÁLISIS ESTADÍSTICO DESCRIPTIVO - DATASET INMUEBLES")
        print("=" * 60)
        
        # Cargar datos
        self.load_data()
        
        # Clasificar variables
        print("\n📊 Clasificando tipos de variables...")
        self.classify_variables()
        
        # Mostrar clasificación
        print("\nClasificación de variables:")
        for var_type in ['numerica_continua', 'numerica_discreta', 'categorica', 'fecha']:
            vars_of_type = [k for k, v in self.variable_types.items() if v == var_type]
            if vars_of_type:
                print(f"  {var_type.upper()}: {vars_of_type}")
        
        # Realizar análisis
        print(f"\n📈 Calculando estadísticas descriptivas...")
        self.analyze_all_variables()
        
        # Crear DataFrame resumen
        df_summary = self.create_summary_dataframe()
        
        # Guardar resultados
        df_summary.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ Análisis completado. Resultados guardados en: {output_path}")
        print(f"📋 Variables analizadas: {len(self.stats_results)}")
        print(f"📊 Estadísticas calculadas: {len(df_summary.columns)} métricas por variable")
        
        return df_summary

# Función principal para usar el analizador
def main():
    """Función principal para ejecutar el análisis"""
    
    # Rutas de archivos
    input_file = "Consolidados/pretratadaCol_num/Sep25/pretratadaCol_num_Sep25_01.csv"
    output_dir = "Estadisticas/Fase1/1.Descriptivo/sep25"
    output_file = f"{output_dir}/num_F1Desc_Sep25_01.csv"
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Verificar que existe el archivo de entrada
    if not os.path.exists(input_file):
        print(f"❌ ERROR: No se encuentra el archivo {input_file}")
        return None
    
    print(f"📂 Archivo de entrada: {input_file}")
    print(f"📂 Archivo de salida: {output_file}")
    
    # Inicializar analizador
    analyzer = InmueblesStatsAnalyzer(input_file)
    
    # Ejecutar análisis completo
    results_df = analyzer.run_complete_analysis(output_file)
    
    # Mostrar muestra de resultados
    print("\n" + "="*60)
    print("MUESTRA DE RESULTADOS:")
    print("="*60)
    
    # Mostrar estadísticas por tipo de variable
    variable_types = results_df['tipo_variable'].value_counts()
    print(f"\nDISTRIBUCIÓN DE TIPOS DE VARIABLES:")
    for var_type, count in variable_types.items():
        print(f"  {str(var_type).upper()}: {count} variables")
    
    # Mostrar variables con más valores faltantes
    print(f"\nVARIABLES CON MÁS VALORES FALTANTES:")
    missing_vars = results_df[results_df['valores_faltantes'] > 0].sort_values('valores_faltantes_pct', ascending=False)
    if len(missing_vars) > 0:
        print(missing_vars[['nombre_variable', 'valores_faltantes', 'valores_faltantes_pct']].head(5).to_string(index=False))
    else:
        print("  ✅ No hay variables con valores faltantes")
    
    # Mostrar resumen general
    print(f"\n📊 RESUMEN GENERAL:")
    print(f"  Variables numéricas continuas: {len(results_df[results_df['tipo_variable'] == 'numerica_continua'])}")
    print(f"  Variables numéricas discretas: {len(results_df[results_df['tipo_variable'] == 'numerica_discreta'])}")
    print(f"  Variables categóricas: {len(results_df[results_df['tipo_variable'] == 'categorica'])}")
    print(f"  Variables de fecha: {len(results_df[results_df['tipo_variable'] == 'fecha'])}")
    print(f"  Total de observaciones: {results_df['total_observaciones'].iloc[0] if len(results_df) > 0 else 0}")
    
    print(f"\n✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print(f"📁 Resultados guardados en: {output_file}")
    
    return results_df

# Ejecutar si es script principal
if __name__ == "__main__":
    results = main()
    
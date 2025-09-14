import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class StatsInsightsProcessor:
    """
    Procesador inteligente que convierte estadísticas descriptivas en insights 
    accionables y recomendaciones específicas para análisis inmobiliario.
    """
    
    def __init__(self, stats_file_path, original_data_path=None):
        self.stats_file_path = stats_file_path
        self.original_data_path = original_data_path
        self.stats_df = None
        self.original_df = None
        self.insights = {}
        self.recommendations = {}
        self.alerts = []
        self.executive_summary = {}
        
        # Umbrales de interpretación específicos para inmuebles
        self.thresholds = {
            'high_missing_pct': 15,      # >15% de nulos es problemático
            'low_missing_pct': 1,        # <1% de nulos es manejable
            'high_cv': 1.0,              # CV >100% indica alta variabilidad
            'moderate_cv': 0.5,          # CV 50-100% es moderado
            'high_skewness': 1,          # |skew| >1 indica sesgo fuerte
            'moderate_skewness': 0.5,    # |skew| 0.5-1 es moderado
            'high_kurtosis': 4,          # Kurtosis >4 indica outliers/picos
            'low_entropy': 0.5,          # Entropía <0.5 indica baja diversidad
            'high_entropy': 2.0,         # Entropía >2 indica alta diversidad
            'extreme_outlier_pct': 10,   # >10% outliers es problemático
            'low_cardinality': 5,        # <5 categorías únicas
            'high_cardinality': 50       # >50 categorías únicas
        }
    
    def load_data(self):
        """Carga los archivos de estadísticas y datos originales"""
        try:
            self.stats_df = pd.read_csv(self.stats_file_path, encoding='utf-8')
            print(f"✅ Estadísticas cargadas: {len(self.stats_df)} variables")
            
            if self.original_data_path:
                self.original_df = pd.read_csv(self.original_data_path, encoding='utf-8')
                print(f"✅ Datos originales cargados: {self.original_df.shape}")
            
            return True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def analyze_central_tendency(self, row):
        """Analiza medidas de tendencia central y detecta sesgo"""
        var_name = row['nombre_variable']
        insights = []
        recommendations = []
        alerts = []
        
        if row['tipo_variable'] in ['numerica_continua', 'numerica_discreta']:
            media = row.get('media', np.nan)
            mediana = row.get('mediana', np.nan)
            
            if pd.notna(media) and pd.notna(mediana):
                # Detectar sesgo comparando media vs mediana
                ratio = media / mediana if mediana != 0 else np.inf
                
                if ratio > 1.2:  # Media 20% mayor que mediana
                    insights.append({
                        'tipo': 'SESGO_POSITIVO',
                        'descripcion': f'Media (${media:,.0f}) >> Mediana (${mediana:,.0f})' if 'precio' in var_name else f'Media ({media:.1f}) >> Mediana ({mediana:.1f})',
                        'interpretacion': 'Distribución sesgada hacia la derecha - valores altos extremos jalan la media',
                        'impacto': 'La media no es representativa del valor típico'
                    })
                    
                    if 'precio' in var_name.lower():
                        recommendations.append({
                            'accion': 'USAR_MEDIANA',
                            'justificacion': 'Para reportar precio típico usar mediana, no media',
                            'prioridad': 'ALTA'
                        })
                        recommendations.append({
                            'accion': 'SEGMENTAR_ANALISIS',
                            'justificacion': 'Hay propiedades de lujo que distorsionan - analizar por segmentos',
                            'prioridad': 'ALTA'
                        })
                    
                    recommendations.append({
                        'accion': 'TRANSFORMACION_LOG',
                        'justificacion': 'Considerar log-transformación para modelos predictivos',
                        'prioridad': 'MEDIA'
                    })
                
                elif ratio < 0.8:  # Media 20% menor que mediana
                    insights.append({
                        'tipo': 'SESGO_NEGATIVO',
                        'descripcion': f'Media (${media:,.0f}) << Mediana (${mediana:,.0f})' if 'precio' in var_name else f'Media ({media:.1f}) << Mediana ({mediana:.1f})',
                        'interpretacion': 'Distribución sesgada hacia la izquierda - valores bajos extremos',
                        'impacto': 'Posibles errores de captura o casos especiales'
                    })
                    
                    alerts.append({
                        'severidad': 'MEDIA',
                        'mensaje': f'Sesgo negativo inusual en {var_name} - revisar valores mínimos',
                        'accion_requerida': 'INVESTIGAR'
                    })
                
                else:
                    insights.append({
                        'tipo': 'DISTRIBUCION_SIMETRICA',
                        'descripcion': f'Media ≈ Mediana (ratio: {ratio:.2f})',
                        'interpretacion': 'Distribución aproximadamente simétrica',
                        'impacto': 'Ideal para modelos paramétricos'
                    })
                    
                    recommendations.append({
                        'accion': 'USAR_PARAMETRICOS',
                        'justificacion': 'Distribución simétrica permite usar regresión lineal, ANOVA',
                        'prioridad': 'BAJA'
                    })
        
        return insights, recommendations, alerts
    
    def analyze_dispersion(self, row):
        """Analiza medidas de dispersión y variabilidad"""
        var_name = row['nombre_variable']
        insights = []
        recommendations = []
        alerts = []
        
        if row['tipo_variable'] in ['numerica_continua', 'numerica_discreta']:
            cv = row.get('coeficiente_variacion', np.nan)
            desv_est = row.get('desviacion_estandar', np.nan)
            iqr = row.get('rango_intercuartil', np.nan)
            rango = row.get('rango', np.nan)
            
            # Analizar Coeficiente de Variación
            if pd.notna(cv):
                if cv > self.thresholds['high_cv'] * 100:  # CV en porcentaje
                    insights.append({
                        'tipo': 'ALTA_VARIABILIDAD',
                        'descripcion': f'CV = {cv:.1f}% (>100%)',
                        'interpretacion': 'Extrema variabilidad - la media no es representativa',
                        'impacto': 'Necesita segmentación urgente'
                    })
                    
                    recommendations.append({
                        'accion': 'SEGMENTAR_OBLIGATORIO',
                        'justificacion': f'CV de {cv:.1f}% indica que {var_name} debe analizarse por segmentos',
                        'prioridad': 'ALTA'
                    })
                    
                    if 'precio' in var_name.lower():
                        recommendations.append({
                            'accion': 'SEGMENTAR_POR_ZONA',
                            'justificacion': 'Segmentar precios por Colonia/Ciudad para reducir variabilidad',
                            'prioridad': 'ALTA'
                        })
                
                elif cv > self.thresholds['moderate_cv'] * 100:
                    insights.append({
                        'tipo': 'VARIABILIDAD_MODERADA',
                        'descripcion': f'CV = {cv:.1f}% (50-100%)',
                        'interpretacion': 'Moderada variabilidad - considerar factores explicativos',
                        'impacto': 'Puede beneficiarse de segmentación'
                    })
                
                else:
                    insights.append({
                        'tipo': 'BAJA_VARIABILIDAD',
                        'descripcion': f'CV = {cv:.1f}% (<50%)',
                        'interpretacion': 'Variable homogénea - buena para modelos',
                        'impacto': 'Ideal para análisis sin segmentación'
                    })
            
            # Analizar relación Rango vs IQR
            if pd.notna(rango) and pd.notna(iqr) and iqr > 0:
                ratio_rango_iqr = rango / iqr
                
                if ratio_rango_iqr > 5:
                    insights.append({
                        'tipo': 'OUTLIERS_EXTREMOS',
                        'descripcion': f'Rango/IQR = {ratio_rango_iqr:.1f}',
                        'interpretacion': 'El 50% central es compacto pero hay outliers extremos',
                        'impacto': 'Outliers distorsionan análisis'
                    })
                    
                    alerts.append({
                        'severidad': 'ALTA',
                        'mensaje': f'Outliers extremos en {var_name} - ratio Rango/IQR = {ratio_rango_iqr:.1f}',
                        'accion_requerida': 'LIMPIAR_OUTLIERS'
                    })
        
        return insights, recommendations, alerts
    
    def analyze_shape(self, row):
        """Analiza medidas de forma (asimetría y curtosis)"""
        var_name = row['nombre_variable']
        insights = []
        recommendations = []
        alerts = []
        
        if row['tipo_variable'] in ['numerica_continua', 'numerica_discreta']:
            skewness = row.get('asimetria', np.nan)
            kurtosis = row.get('curtosis', np.nan)
            
            # Analizar asimetría
            if pd.notna(skewness):
                if abs(skewness) > self.thresholds['high_skewness']:
                    direction = 'positiva' if skewness > 0 else 'negativa'
                    insights.append({
                        'tipo': 'ALTA_ASIMETRIA',
                        'descripcion': f'Asimetría {direction} = {skewness:.2f}',
                        'interpretacion': f'Distribución muy sesgada - cola hacia {"derecha" if skewness > 0 else "izquierda"}',
                        'impacto': 'No es normal - usar métodos no paramétricos'
                    })
                    
                    recommendations.append({
                        'accion': 'USAR_NO_PARAMETRICOS',
                        'justificacion': 'Alta asimetría - usar Spearman en lugar de Pearson',
                        'prioridad': 'ALTA'
                    })
                    
                    if skewness > 0:  # Sesgo positivo es común en inmuebles
                        recommendations.append({
                            'accion': 'TRANSFORMACION_LOG',
                            'justificacion': 'Sesgo positivo típico en precios/áreas - transformar con log',
                            'prioridad': 'MEDIA'
                        })
                
                elif abs(skewness) < 0.5:
                    insights.append({
                        'tipo': 'DISTRIBUCION_NORMAL',
                        'descripcion': f'Asimetría = {skewness:.2f} (aproximadamente simétrica)',
                        'interpretacion': 'Distribución cercana a normal',
                        'impacto': 'Ideal para modelos paramétricos'
                    })
            
            # Analizar curtosis
            if pd.notna(kurtosis):
                if kurtosis > self.thresholds['high_kurtosis']:
                    insights.append({
                        'tipo': 'ALTA_CURTOSIS',
                        'descripcion': f'Curtosis = {kurtosis:.2f} (>4)',
                        'interpretacion': 'Distribución muy picuda con colas pesadas',
                        'impacto': 'Muchos outliers o valores extremos'
                    })
                    
                    alerts.append({
                        'severidad': 'MEDIA',
                        'mensaje': f'Alta curtosis en {var_name} indica muchos outliers',
                        'accion_requerida': 'REVISAR_OUTLIERS'
                    })
                    
                    recommendations.append({
                        'accion': 'METODOS_ROBUSTOS',
                        'justificacion': 'Alta curtosis - usar medianas, IQR, métodos robustos',
                        'prioridad': 'ALTA'
                    })
        
        return insights, recommendations, alerts
    
    def analyze_data_quality(self, row):
        """Analiza calidad de datos"""
        var_name = row['nombre_variable']
        insights = []
        recommendations = []
        alerts = []
        
        missing_pct = row.get('valores_faltantes_pct', 0)
        unique_count = row.get('valores_unicos', 0) or row.get('categorias_unicas', 0)
        total_obs = row.get('total_observaciones', 1)
        
        # Analizar valores faltantes
        if missing_pct > self.thresholds['high_missing_pct']:
            insights.append({
                'tipo': 'ALTA_FALTANTE',
                'descripcion': f'{missing_pct:.1f}% valores faltantes',
                'interpretacion': 'Problema serio de calidad de datos',
                'impacto': 'Sesgo si se eliminan - requiere imputación'
            })
            
            alerts.append({
                'severidad': 'ALTA',
                'mensaje': f'{var_name} tiene {missing_pct:.1f}% de valores faltantes',
                'accion_requerida': 'IMPUTAR_O_ELIMINAR'
            })
            
            recommendations.append({
                'accion': 'ESTRATEGIA_IMPUTACION',
                'justificacion': f'Demasiados nulos para eliminar - imputar con mediana/moda o crear flag',
                'prioridad': 'ALTA'
            })
        
        elif missing_pct > self.thresholds['low_missing_pct']:
            recommendations.append({
                'accion': 'IMPUTACION_SIMPLE',
                'justificacion': f'{missing_pct:.1f}% nulos - imputar con mediana',
                'prioridad': 'MEDIA'
            })
        
        elif missing_pct > 0:
            recommendations.append({
                'accion': 'ELIMINAR_NULOS',
                'justificacion': f'Solo {missing_pct:.1f}% nulos - seguro eliminar',
                'prioridad': 'BAJA'
            })
        
        # Analizar cardinalidad
        if row['tipo_variable'] == 'categorica':
            cardinality_ratio = unique_count / total_obs
            
            if unique_count > self.thresholds['high_cardinality']:
                insights.append({
                    'tipo': 'ALTA_CARDINALIDAD',
                    'descripcion': f'{unique_count} categorías únicas',
                    'interpretacion': 'Demasiadas categorías - poco útil para modelos',
                    'impacto': 'Dificulta análisis y modelado'
                })
                
                recommendations.append({
                    'accion': 'AGRUPAR_CATEGORIAS',
                    'justificacion': 'Agrupar en categorías principales + "Otros"',
                    'prioridad': 'ALTA'
                })
            
            elif unique_count < self.thresholds['low_cardinality']:
                insights.append({
                    'tipo': 'BAJA_CARDINALIDAD',
                    'descripcion': f'Solo {unique_count} categorías',
                    'interpretacion': 'Poca variabilidad - limitada utilidad',
                    'impacto': 'Variable poco informativa'
                })
                
                if unique_count == 1:
                    recommendations.append({
                        'accion': 'ELIMINAR_VARIABLE',
                        'justificacion': 'Variable constante - no aporta información',
                        'prioridad': 'ALTA'
                    })
        
        # Detectar valores imposibles específicos de inmuebles
        if 'precio' in var_name.lower():
            min_val = row.get('valor_minimo', 0)
            if min_val <= 0:
                alerts.append({
                    'severidad': 'ALTA',
                    'mensaje': f'Precio mínimo = {min_val} - valores imposibles',
                    'accion_requerida': 'CORREGIR_DATOS'
                })
        
        elif 'area' in var_name.lower():
            min_val = row.get('valor_minimo', 0)
            if min_val <= 0:
                alerts.append({
                    'severidad': 'ALTA',
                    'mensaje': f'Área mínima = {min_val} - valores imposibles',
                    'accion_requerida': 'CORREGIR_DATOS'
                })
        
        return insights, recommendations, alerts
    
    def analyze_categorical_diversity(self, row):
        """Analiza diversidad en variables categóricas"""
        var_name = row['nombre_variable']
        insights = []
        recommendations = []
        
        if row['tipo_variable'] == 'categorica':
            entropy = row.get('entropia', np.nan)
            top_freq_pct = row.get('frecuencia_maxima_pct', np.nan)
            
            if pd.notna(entropy):
                if entropy < self.thresholds['low_entropy']:
                    insights.append({
                        'tipo': 'BAJA_DIVERSIDAD',
                        'descripcion': f'Entropía = {entropy:.2f}',
                        'interpretacion': 'Una categoría domina - poca diversidad',
                        'impacto': 'Variable poco informativa'
                    })
                    
                    if pd.notna(top_freq_pct) and top_freq_pct > 90:
                        recommendations.append({
                            'accion': 'CONSIDERAR_ELIMINAR',
                            'justificacion': f'Una categoría representa {top_freq_pct:.1f}% - considerar eliminar',
                            'prioridad': 'MEDIA'
                        })
                
                elif entropy > self.thresholds['high_entropy']:
                    insights.append({
                        'tipo': 'ALTA_DIVERSIDAD',
                        'descripcion': f'Entropía = {entropy:.2f}',
                        'interpretacion': 'Categorías muy balanceadas - alta diversidad',
                        'impacto': 'Excelente para segmentación'
                    })
                    
                    recommendations.append({
                        'accion': 'USAR_EN_MODELOS',
                        'justificacion': 'Alta entropía - variable rica en información',
                        'prioridad': 'ALTA'
                    })
                
                else:
                    insights.append({
                        'tipo': 'DIVERSIDAD_MODERADA',
                        'descripcion': f'Entropía = {entropy:.2f}',
                        'interpretacion': 'Diversidad balanceada',
                        'impacto': 'Buena para análisis'
                    })
        
        return insights, recommendations
    
    def generate_variable_insights(self):
        """Genera insights para cada variable"""
        print("🔍 Generando insights por variable...")
        
        # Variables a excluir del análisis de insights
        variables_excluir = {
            'id', 'PaginaWeb', 'Ciudad', 'Fecha_Scrap', 
            'tipo_propiedad', 'operacion', 'Colonia', 
            'latitud', 'longitud'
        }
        
        for idx, row in self.stats_df.iterrows():
            var_name = row['nombre_variable']
            
            # Saltar variables excluidas
            if var_name in variables_excluir:
                continue
            
            # Analizar cada aspecto
            central_insights, central_recs, central_alerts = self.analyze_central_tendency(row)
            disp_insights, disp_recs, disp_alerts = self.analyze_dispersion(row)
            shape_insights, shape_recs, shape_alerts = self.analyze_shape(row)
            quality_insights, quality_recs, quality_alerts = self.analyze_data_quality(row)
            
            # Para categóricas, analizar diversidad
            if row['tipo_variable'] == 'categorica':
                cat_insights, cat_recs = self.analyze_categorical_diversity(row)
                central_insights.extend(cat_insights)
                central_recs.extend(cat_recs)
            
            # Consolidar resultados
            self.insights[var_name] = {
                'tendencia_central': central_insights,
                'dispersion': disp_insights,
                'forma': shape_insights,
                'calidad': quality_insights
            }
            
            self.recommendations[var_name] = central_recs + disp_recs + shape_recs + quality_recs
            self.alerts.extend(central_alerts + disp_alerts + shape_alerts + quality_alerts)
    
    def create_executive_summary(self):
        """Crea resumen ejecutivo del análisis"""
        total_vars = len(self.stats_df)
        numeric_vars = len(self.stats_df[self.stats_df['tipo_variable'].isin(['numerica_continua', 'numerica_discreta'])])
        categorical_vars = len(self.stats_df[self.stats_df['tipo_variable'] == 'categorica'])
        
        # Contar problemas por severidad
        high_alerts = len([a for a in self.alerts if a['severidad'] == 'ALTA'])
        medium_alerts = len([a for a in self.alerts if a['severidad'] == 'MEDIA'])
        
        # Variables con problemas críticos
        critical_vars = []
        for var_name, recs in self.recommendations.items():
            high_priority_recs = [r for r in recs if r['prioridad'] == 'ALTA']
            if len(high_priority_recs) > 2:  # Más de 2 recomendaciones de alta prioridad
                critical_vars.append(var_name)
        
        # Variables listas para usar
        ready_vars = []
        for var_name, recs in self.recommendations.items():
            high_priority_recs = [r for r in recs if r['prioridad'] == 'ALTA']
            if len(high_priority_recs) == 0:
                ready_vars.append(var_name)
        
        self.executive_summary = {
            'total_variables': total_vars,
            'variables_numericas': numeric_vars,
            'variables_categoricas': categorical_vars,
            'alertas_criticas': high_alerts,
            'alertas_moderadas': medium_alerts,
            'variables_criticas': critical_vars,
            'variables_listas': ready_vars,
            'porcentaje_listas': (len(ready_vars) / total_vars) * 100,
            'porcentaje_criticas': (len(critical_vars) / total_vars) * 100
        }
    
    def generate_insights_report(self):
        """Genera reporte detallado de insights"""
        insights_data = []
        
        for var_name, var_insights in self.insights.items():
            for category, insights_list in var_insights.items():
                for insight in insights_list:
                    insights_data.append({
                        'variable': var_name,
                        'categoria': category,
                        'tipo_insight': insight['tipo'],
                        'descripcion': insight['descripcion'],
                        'interpretacion': insight['interpretacion'],
                        'impacto': insight['impacto']
                    })
        
        return pd.DataFrame(insights_data)
    
    def generate_recommendations_report(self):
        """Genera reporte de recomendaciones"""
        recs_data = []
        
        for var_name, recs_list in self.recommendations.items():
            for rec in recs_list:
                recs_data.append({
                    'variable': var_name,
                    'accion': rec['accion'],
                    'justificacion': rec['justificacion'],
                    'prioridad': rec['prioridad']
                })
        
        return pd.DataFrame(recs_data)
    
    def generate_alerts_report(self):
        """Genera reporte de alertas"""
        return pd.DataFrame(self.alerts)
    
    def create_action_matrix(self):
        """Crea matriz de acción por variable"""
        action_data = []
        
        for var_name in self.stats_df['nombre_variable']:
            row_data = {'variable': var_name}
            
            # Obtener estadísticas clave
            var_stats = self.stats_df[self.stats_df['nombre_variable'] == var_name].iloc[0]
            row_data['tipo'] = var_stats['tipo_variable']
            
            # Obtener recomendaciones
            var_recs = self.recommendations.get(var_name, [])
            high_recs = [r for r in var_recs if r['prioridad'] == 'ALTA']
            medium_recs = [r for r in var_recs if r['prioridad'] == 'MEDIA']
            
            # Determinar status
            if len(high_recs) > 2:
                row_data['status'] = 'CRITICA'
                row_data['accion_principal'] = 'REVISAR_URGENTE'
            elif len(high_recs) > 0:
                row_data['status'] = 'ATENCION'
                row_data['accion_principal'] = high_recs[0]['accion']
            elif len(medium_recs) > 0:
                row_data['status'] = 'MONITOREAR'
                row_data['accion_principal'] = medium_recs[0]['accion']
            else:
                row_data['status'] = 'OK'
                row_data['accion_principal'] = 'USAR_DIRECTAMENTE'
            
            # Estadísticas clave
            if var_stats['tipo_variable'] in ['numerica_continua', 'numerica_discreta']:
                row_data['media'] = var_stats.get('media', np.nan)
                row_data['mediana'] = var_stats.get('mediana', np.nan)
                row_data['cv_pct'] = var_stats.get('coeficiente_variacion', np.nan)
                row_data['asimetria'] = var_stats.get('asimetria', np.nan)
                row_data['outliers_pct'] = var_stats.get('outliers_pct', np.nan)
            else:
                row_data['categoria_principal'] = var_stats.get('categoria_mas_frecuente', 'N/A')
                row_data['freq_principal_pct'] = var_stats.get('frecuencia_maxima_pct', np.nan)
                row_data['entropia'] = var_stats.get('entropia', np.nan)
            
            row_data['nulos_pct'] = var_stats.get('valores_faltantes_pct', 0)
            row_data['recomendaciones_count'] = len(var_recs)
            
            action_data.append(row_data)
        
        return pd.DataFrame(action_data)
    
    def run_complete_analysis(self, output_prefix='stats_insights'):
        """Ejecuta análisis completo de insights"""
        print("🧠 ANÁLISIS INTELIGENTE DE ESTADÍSTICA DESCRIPTIVA")
        print("=" * 65)
        
        if not self.load_data():
            return None
        
        # Generar insights
        self.generate_variable_insights()
        
        # Crear resumen ejecutivo
        self.create_executive_summary()
        
        # Generar reportes
        print("\n📊 Generando reportes de insights...")
        
        insights_df = self.generate_insights_report()
        recommendations_df = self.generate_recommendations_report()
        alerts_df = self.generate_alerts_report()
        action_matrix_df = self.create_action_matrix()
        
        # Guardar archivos
        insights_df.to_csv(f'{output_prefix}_insights.csv', index=False, encoding='utf-8-sig')
        recommendations_df.to_csv(f'{output_prefix}_recommendations.csv', index=False, encoding='utf-8-sig')
        action_matrix_df.to_csv(f'{output_prefix}_action_matrix.csv', index=False, encoding='utf-8-sig')
        
        if not alerts_df.empty:
            alerts_df.to_csv(f'{output_prefix}_alerts.csv', index=False, encoding='utf-8-sig')
        
        # Mostrar resumen ejecutivo
        print("\n" + "="*65)
        print("RESUMEN EJECUTIVO")
        print("="*65)
        
        print(f"📊 Variables analizadas: {self.executive_summary['total_variables']}")
        print(f"   • Numéricas: {self.executive_summary['variables_numericas']}")
        print(f"   • Categóricas: {self.executive_summary['variables_categoricas']}")
        
        print(f"\n🚨 Alertas detectadas:")
        print(f"   • Críticas: {self.executive_summary['alertas_criticas']}")
        print(f"   • Moderadas: {self.executive_summary['alertas_moderadas']}")
        
        print(f"\n📈 Estado de variables:")
        print(f"   • Listas para usar: {len(self.executive_summary['variables_listas'])} ({self.executive_summary['porcentaje_listas']:.1f}%)")
        print(f"   • Requieren atención: {len(self.executive_summary['variables_criticas'])} ({self.executive_summary['porcentaje_criticas']:.1f}%)")
        
        # Top insights
        if not insights_df.empty:
            print(f"\n🔍 TOP INSIGHTS CRÍTICOS:")
            critical_insights = insights_df[insights_df['tipo_insight'].isin(['ALTA_VARIABILIDAD', 'OUTLIERS_EXTREMOS', 'ALTA_FALTANTE'])]
            for _, insight in critical_insights.head(5).iterrows():
                print(f"   • {insight['variable']}: {insight['descripcion']}")
        
        # Top recomendaciones
        if not recommendations_df.empty:
            print(f"\n💡 TOP RECOMENDACIONES URGENTES:")
            urgent_recs = recommendations_df[recommendations_df['prioridad'] == 'ALTA']
            for _, rec in urgent_recs.head(5).iterrows():
                print(f"   • {rec['variable']}: {rec['accion']}")
        
        print(f"\n✅ Análisis completado. Archivos generados:")
        print(f"   📋 {output_prefix}_insights.csv - Insights detallados")
        print(f"   💡 {output_prefix}_recommendations.csv - Recomendaciones de acción")
        print(f"   📊 {output_prefix}_action_matrix.csv - Matriz de acción por variable")
        if not alerts_df.empty:
            print(f"   🚨 {output_prefix}_alerts.csv - Alertas críticas")
        
        return {
            'insights': insights_df,
            'recommendations': recommendations_df,
            'action_matrix': action_matrix_df,
            'alerts': alerts_df,
            'executive_summary': self.executive_summary
        }

def main():
    """Función principal para ejecutar el análisis"""
    
    # Rutas de archivos según la estructura del proyecto
    stats_file = "Estadisticas/Fase1/1.Descriptivo/sep25/num_F1Desc_Sep25_01.csv"
    original_data_file = "Consolidados/pretratadaCol_num/Sep25/pretratadaCol_num_Sep25_01.csv"
    output_dir = "Estadisticas/Reportes/1. Descriptivo/Sep25"
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Verificar que existen los archivos de entrada
    if not os.path.exists(stats_file):
        print(f"❌ ERROR: No se encuentra el archivo de estadísticas {stats_file}")
        print("   Asegúrate de haber ejecutado primero '7. F1_Descriptivo.py'")
        return None
    
    if not os.path.exists(original_data_file):
        print(f"❌ ERROR: No se encuentra el archivo de datos originales {original_data_file}")
        return None
    
    print(f"📂 Archivo de estadísticas: {stats_file}")
    print(f"📂 Archivo de datos originales: {original_data_file}")
    print(f"📂 Directorio de reportes: {output_dir}")
    
    # Ejecutar análisis con rutas del proyecto
    processor = StatsInsightsProcessor(
        stats_file_path=stats_file,
        original_data_path=original_data_file
    )
    
    # Generar reportes con prefijo específico del proyecto
    output_prefix = f"{output_dir}/F1_DescriptivoRep_Sep25_01"
    
    results = processor.run_complete_analysis(output_prefix)
    
    if results:
        print(f"\n🎯 REPORTES GENERADOS EN: {output_dir}/")
        print(f"   📋 F1_DescriptivoRep_Sep25_01_insights.csv")
        print(f"   💡 F1_DescriptivoRep_Sep25_01_recommendations.csv") 
        print(f"   📊 F1_DescriptivoRep_Sep25_01_action_matrix.csv")
        if not results['alerts'].empty:
            print(f"   🚨 F1_DescriptivoRep_Sep25_01_alerts.csv")
        
        # Mostrar resumen de variables críticas
        action_matrix = results['action_matrix']
        critical_vars = action_matrix[action_matrix['status'] == 'CRITICA']
        attention_vars = action_matrix[action_matrix['status'] == 'ATENCION']
        ok_vars = action_matrix[action_matrix['status'] == 'OK']
        
        print(f"\n📊 CLASIFICACIÓN FINAL DE VARIABLES:")
        print(f"   🔴 CRÍTICAS (requieren intervención urgente): {len(critical_vars)}")
        if len(critical_vars) > 0:
            for var in critical_vars['variable'].tolist():
                print(f"      • {var}")
        
        print(f"   🟡 ATENCIÓN (requieren revisión): {len(attention_vars)}")
        if len(attention_vars) > 0:
            for var in attention_vars['variable'].tolist()[:5]:  # Mostrar solo primeras 5
                print(f"      • {var}")
            if len(attention_vars) > 5:
                print(f"      • ... y {len(attention_vars) - 5} más")
        
        print(f"   🟢 LISTAS PARA USAR: {len(ok_vars)}")
        
        # Identificar principales problemas
        if results['recommendations'] is not None and not results['recommendations'].empty:
            recs_df = results['recommendations']
            top_actions = recs_df[recs_df['prioridad'] == 'ALTA']['accion'].value_counts().head(3)
            
            print(f"\n💡 PRINCIPALES ACCIONES REQUERIDAS:")
            for action, count in top_actions.items():
                print(f"   • {action}: {count} variables")
    
    return results

if __name__ == "__main__":
    insights_results = main()
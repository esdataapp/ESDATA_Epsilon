"""
UTILIDADES PARA PAPELERA DE RECICLAJE INMOBILIARIO
Herramientas para consultar, analizar y recuperar propiedades eliminadas
"""

import pandas as pd
import numpy as np
from Sistema_Papelera_Reciclaje import PapeleraReciclaje
import matplotlib.pyplot as plt
import seaborn as sns

class UtilPapelera:
    """
    Utilidades para trabajar con la papelera de reciclaje
    """
    
    def __init__(self, directorio_papelera="Papelera_Reciclaje"):
        self.papelera = PapeleraReciclaje(directorio_papelera)
    
    def ver_resumen_completo(self):
        """Muestra un resumen completo de todas las eliminaciones"""
        
        print("🗑️ RESUMEN COMPLETO DE PAPELERA DE RECICLAJE")
        print("=" * 60)
        
        try:
            df_master = pd.read_csv(self.papelera.archivo_master)
            df_resumen = pd.read_csv(self.papelera.archivo_resumen)
            
            # Estadísticas generales
            total_eliminados = len(df_master)
            procesos_unicos = df_master['proceso_origen'].nunique()
            fechas_unicas = df_master['fecha_eliminacion'].nunique()
            
            print(f"📊 ESTADÍSTICAS GENERALES:")
            print(f"   • Total de propiedades eliminadas: {total_eliminados:,}")
            print(f"   • Procesos diferentes: {procesos_unicos}")
            print(f"   • Días con eliminaciones: {fechas_unicas}")
            
            # Por proceso
            print(f"\n📋 ELIMINACIONES POR PROCESO:")
            por_proceso = df_master['proceso_origen'].value_counts()
            for proceso, cantidad in por_proceso.items():
                porcentaje = (cantidad / total_eliminados) * 100
                print(f"   • {proceso}: {cantidad:,} ({porcentaje:.1f}%)")
            
            # Por categoría de error
            print(f"\n🔍 ELIMINACIONES POR CATEGORÍA DE ERROR:")
            por_categoria = df_master['categoria_error'].value_counts()
            for categoria, cantidad in por_categoria.items():
                porcentaje = (cantidad / total_eliminados) * 100
                print(f"   • {categoria}: {cantidad:,} ({porcentaje:.1f}%)")
            
            # Por fecha
            print(f"\n📅 ELIMINACIONES POR FECHA:")
            por_fecha = df_master['fecha_eliminacion'].value_counts().sort_index()
            for fecha, cantidad in por_fecha.items():
                print(f"   • {fecha}: {cantidad:,} propiedades")
            
            # Top colonias eliminadas
            if 'Colonia' in df_master.columns:
                print(f"\n🏘️ TOP 10 COLONIAS CON MÁS ELIMINACIONES:")
                top_colonias = df_master['Colonia'].value_counts().head(10)
                for i, (colonia, cantidad) in enumerate(top_colonias.items(), 1):
                    print(f"   {i:2d}. {colonia}: {cantidad} propiedades")
            
            return df_master, df_resumen
            
        except Exception as e:
            print(f"❌ Error al generar resumen: {e}")
            return None, None
    
    def buscar_propiedades(self, filtros):
        """
        Busca propiedades eliminadas según filtros específicos
        
        Args:
            filtros: Diccionario con criterios de búsqueda
        """
        
        try:
            df_master = pd.read_csv(self.papelera.archivo_master)
            df_resultado = df_master.copy()
            
            print(f"🔍 BÚSQUEDA EN PAPELERA DE RECICLAJE")
            print("=" * 45)
            
            # Aplicar filtros
            filtros_aplicados = []
            
            for campo, valor in filtros.items():
                if campo in df_resultado.columns:
                    if isinstance(valor, list):
                        df_resultado = df_resultado[df_resultado[campo].isin(valor)]
                        filtros_aplicados.append(f"{campo} en {valor}")
                    elif isinstance(valor, dict) and 'min' in valor:
                        # Filtro por rango
                        if 'min' in valor:
                            df_resultado = df_resultado[df_resultado[campo] >= valor['min']]
                        if 'max' in valor:
                            df_resultado = df_resultado[df_resultado[campo] <= valor['max']]
                        filtros_aplicados.append(f"{campo}: {valor}")
                    else:
                        df_resultado = df_resultado[df_resultado[campo] == valor]
                        filtros_aplicados.append(f"{campo} = {valor}")
            
            print(f"📋 Filtros aplicados:")
            for filtro in filtros_aplicados:
                print(f"   • {filtro}")
            
            print(f"\n📊 Resultados: {len(df_resultado):,} propiedades encontradas")
            
            if len(df_resultado) > 0:
                # Mostrar muestra
                print(f"\n📄 MUESTRA DE RESULTADOS:")
                columnas_mostrar = ['fecha_eliminacion', 'proceso_origen', 'categoria_error', 
                                  'tipo_propiedad', 'area_m2', 'recamaras', 'precio', 'Colonia']
                columnas_disponibles = [col for col in columnas_mostrar if col in df_resultado.columns]
                
                muestra = df_resultado[columnas_disponibles].head(10)
                print(muestra.to_string(index=False))
                
                if len(df_resultado) > 10:
                    print(f"\n   ... y {len(df_resultado) - 10} registros más")
            
            return df_resultado
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return None
    
    def recuperar_propiedades_selectivas(self, filtros, archivo_recuperacion):
        """
        Recupera propiedades que cumplen ciertos criterios
        """
        
        df_encontradas = self.buscar_propiedades(filtros)
        
        if df_encontradas is not None and len(df_encontradas) > 0:
            # Preparar para recuperación (eliminar metadatos)
            columnas_originales = [col for col in df_encontradas.columns 
                                 if not col.startswith(('id_eliminacion', 'fecha_eliminacion', 
                                                      'hora_eliminacion', 'proceso_origen',
                                                      'razon_eliminacion', 'categoria_error',
                                                      'detalles_error', 'valores_analizados',
                                                      'observaciones'))]
            
            df_recuperado = df_encontradas[columnas_originales]
            
            # Guardar
            df_recuperado.to_csv(archivo_recuperacion, index=False)
            
            print(f"\n💾 RECUPERACIÓN EXITOSA:")
            print(f"   • {len(df_recuperado):,} propiedades recuperadas")
            print(f"   • Guardadas en: {archivo_recuperacion}")
            
            return df_recuperado
        else:
            print(f"❌ No se encontraron propiedades para recuperar")
            return None
    
    def analizar_patrones_eliminacion(self):
        """Analiza patrones en las eliminaciones para mejorar el proceso"""
        
        try:
            df_master = pd.read_csv(self.papelera.archivo_master)
            
            print("🔬 ANÁLISIS DE PATRONES DE ELIMINACIÓN")
            print("=" * 50)
            
            # Análisis por precio
            if 'precio' in df_master.columns:
                df_master['precio'] = pd.to_numeric(df_master['precio'], errors='coerce')
                
                print(f"\n💰 ANÁLISIS POR PRECIO:")
                stats_precio = df_master['precio'].describe()
                print(f"   • Precio promedio eliminado: ${stats_precio['mean']:,.0f}")
                print(f"   • Precio mediano eliminado: ${stats_precio['50%']:,.0f}")
                print(f"   • Rango: ${stats_precio['min']:,.0f} - ${stats_precio['max']:,.0f}")
                
                # Distribución por categoría
                print(f"\n   Por categoría de error:")
                por_categoria_precio = df_master.groupby('categoria_error')['precio'].agg(['mean', 'count'])
                for categoria in por_categoria_precio.index:
                    precio_promedio = por_categoria_precio.loc[categoria, 'mean']
                    cantidad = por_categoria_precio.loc[categoria, 'count']
                    print(f"      • {categoria}: ${precio_promedio:,.0f} promedio ({cantidad} casos)")
            
            # Análisis por área
            if 'area_m2' in df_master.columns:
                df_master['area_m2'] = pd.to_numeric(df_master['area_m2'], errors='coerce')
                
                print(f"\n🏠 ANÁLISIS POR ÁREA:")
                stats_area = df_master['area_m2'].describe()
                print(f"   • Área promedio eliminada: {stats_area['mean']:.1f}m²")
                print(f"   • Área mediana eliminada: {stats_area['50%']:.1f}m²")
                print(f"   • Rango: {stats_area['min']:.1f}m² - {stats_area['max']:.1f}m²")
            
            # Análisis por tipo de propiedad
            if 'tipo_propiedad' in df_master.columns:
                print(f"\n🏢 ANÁLISIS POR TIPO DE PROPIEDAD:")
                por_tipo = df_master['tipo_propiedad'].value_counts()
                total_eliminados = len(df_master)
                
                for tipo, cantidad in por_tipo.items():
                    porcentaje = (cantidad / total_eliminados) * 100
                    print(f"   • {tipo}: {cantidad:,} ({porcentaje:.1f}%)")
            
            # Tendencias temporales
            print(f"\n📈 TENDENCIAS TEMPORALES:")
            df_master['fecha_eliminacion'] = pd.to_datetime(df_master['fecha_eliminacion'])
            por_fecha = df_master.groupby('fecha_eliminacion').size()
            
            print(f"   • Promedio diario: {por_fecha.mean():.1f} eliminaciones")
            print(f"   • Máximo en un día: {por_fecha.max()} eliminaciones")
            print(f"   • Días con actividad: {len(por_fecha)}")
            
            return df_master
            
        except Exception as e:
            print(f"❌ Error en análisis de patrones: {e}")
            return None
    
    def sugerir_recuperaciones(self):
        """Sugiere propiedades que podrían recuperarse"""
        
        try:
            df_master = pd.read_csv(self.papelera.archivo_master)
            
            print("💡 SUGERENCIAS DE RECUPERACIÓN")
            print("=" * 40)
            
            sugerencias = []
            
            # Buscar propiedades con precios razonables eliminadas por otros motivos
            if 'precio' in df_master.columns and 'categoria_error' in df_master.columns:
                df_master['precio'] = pd.to_numeric(df_master['precio'], errors='coerce')
                
                # Propiedades con precio entre 500k-50M eliminadas por coherencia dimensional
                candidatos_dimensionales = df_master[
                    (df_master['categoria_error'] == 'Incoherencia Dimensional') &
                    (df_master['precio'] >= 500000) &
                    (df_master['precio'] <= 50000000)
                ]
                
                if len(candidatos_dimensionales) > 0:
                    sugerencias.append({
                        'categoria': 'Revisar Dimensionales con Precio Razonable',
                        'cantidad': len(candidatos_dimensionales),
                        'descripcion': 'Propiedades eliminadas por área pero con precios del mercado',
                        'filtros': {
                            'categoria_error': 'Incoherencia Dimensional',
                            'precio': {'min': 500000, 'max': 50000000}
                        }
                    })
            
            # Buscar propiedades únicas en colonias premium
            if 'Colonia' in df_master.columns:
                colonias_premium = ['Providencia', 'Chapalita', 'Americana', 'Del Valle']
                for colonia in colonias_premium:
                    en_colonia = df_master[df_master['Colonia'].str.contains(colonia, na=False, case=False)]
                    if len(en_colonia) > 0:
                        sugerencias.append({
                            'categoria': f'Propiedades en {colonia}',
                            'cantidad': len(en_colonia),
                            'descripcion': f'Revisar eliminaciones en zona premium {colonia}',
                            'filtros': {'Colonia': colonia}
                        })
            
            # Mostrar sugerencias
            if sugerencias:
                print(f"📋 Se encontraron {len(sugerencias)} oportunidades de recuperación:\n")
                
                for i, sugerencia in enumerate(sugerencias, 1):
                    print(f"{i}. {sugerencia['categoria']}")
                    print(f"   • Cantidad: {sugerencia['cantidad']} propiedades")
                    print(f"   • Descripción: {sugerencia['descripcion']}")
                    print(f"   • Para buscar: util.buscar_propiedades({sugerencia['filtros']})")
                    print()
            else:
                print("No se encontraron oportunidades claras de recuperación")
            
            return sugerencias
            
        except Exception as e:
            print(f"❌ Error en sugerencias: {e}")
            return []

def main():
    """Función principal con menú interactivo"""
    
    util = UtilPapelera()
    
    print("🗑️ UTILIDADES DE PAPELERA DE RECICLAJE INMOBILIARIO")
    print("=" * 60)
    
    while True:
        print("\n📋 OPCIONES DISPONIBLES:")
        print("1. Ver resumen completo")
        print("2. Buscar propiedades específicas")
        print("3. Analizar patrones de eliminación")
        print("4. Sugerencias de recuperación")
        print("5. Salir")
        
        opcion = input("\nSelecciona una opción (1-5): ").strip()
        
        if opcion == "1":
            util.ver_resumen_completo()
        
        elif opcion == "2":
            print("\n🔍 BÚSQUEDA PERSONALIZADA")
            print("Ejemplos de filtros:")
            print("• Por colonia: {'Colonia': 'Providencia'}")
            print("• Por precio: {'precio': {'min': 1000000, 'max': 5000000}}")
            print("• Por categoría: {'categoria_error': 'Datos Faltantes'}")
            
        elif opcion == "3":
            util.analizar_patrones_eliminacion()
        
        elif opcion == "4":
            util.sugerir_recuperaciones()
        
        elif opcion == "5":
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()

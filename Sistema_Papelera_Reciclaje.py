"""
SISTEMA DE PAPELERA DE RECICLAJE INMOBILIARIO
Registra todas las propiedades eliminadas en cada proceso de análisis
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import json

class PapeleraReciclaje:
    """
    Sistema centralizado para registrar propiedades eliminadas
    """
    
    def __init__(self, directorio_papelera="Papelera_Reciclaje"):
        """
        Args:
            directorio_papelera: Directorio donde guardar los registros eliminados
        """
        self.directorio_papelera = directorio_papelera
        self.archivo_master = os.path.join(directorio_papelera, "papelera_master.csv")
        self.archivo_resumen = os.path.join(directorio_papelera, "resumen_eliminaciones.csv")
        
        # Crear directorio si no existe
        os.makedirs(directorio_papelera, exist_ok=True)
        
        # Inicializar archivos si no existen
        self._inicializar_archivos()
    
    def _inicializar_archivos(self):
        """Inicializa los archivos de papelera si no existen"""
        
        # Archivo master - contiene todos los registros eliminados
        if not os.path.exists(self.archivo_master):
            columnas_master = [
                'id_eliminacion', 'fecha_eliminacion', 'hora_eliminacion',
                'proceso_origen', 'razon_eliminacion', 'categoria_error',
                'id_original', 'PaginaWeb', 'Ciudad', 'Fecha_Scrap',
                'tipo_propiedad', 'area_m2', 'recamaras', 'estacionamientos',
                'operacion', 'precio', 'mantenimiento', 'Colonia',
                'longitud', 'latitud', 'tiempo_publicacion', 'area_total',
                'area_cubierta', 'banos_icon', 'estacionamientos_icon',
                'recamaras_icon', 'medio_banos_icon', 'antiguedad_icon',
                'detalles_error', 'valores_analizados', 'observaciones'
            ]
            
            df_master = pd.DataFrame(columns=columnas_master)
            df_master.to_csv(self.archivo_master, index=False)
            print(f"📁 Creado archivo master: {self.archivo_master}")
        
        # Archivo resumen - estadísticas por proceso
        if not os.path.exists(self.archivo_resumen):
            columnas_resumen = [
                'fecha', 'proceso', 'total_procesados', 'total_eliminados',
                'porcentaje_eliminado', 'categoria_error_principal',
                'archivo_origen', 'archivo_destino'
            ]
            
            df_resumen = pd.DataFrame(columns=columnas_resumen)
            df_resumen.to_csv(self.archivo_resumen, index=False)
            print(f"📁 Creado archivo resumen: {self.archivo_resumen}")
    
    def registrar_eliminados(self, df_eliminados, proceso_origen, razones_eliminacion, 
                           archivo_origen=None, archivo_destino=None, detalles_adicionales=None):
        """
        Registra propiedades eliminadas en la papelera
        
        Args:
            df_eliminados: DataFrame con registros eliminados
            proceso_origen: Nombre del proceso que eliminó los registros
            razones_eliminacion: Lista de razones por cada registro eliminado
            archivo_origen: Archivo de origen del proceso
            archivo_destino: Archivo de destino del proceso
            detalles_adicionales: Información adicional sobre las eliminaciones
        """
        
        if len(df_eliminados) == 0:
            print(f"📝 No hay registros eliminados en {proceso_origen}")
            return
        
        timestamp = datetime.now()
        fecha_str = timestamp.strftime("%Y-%m-%d")
        hora_str = timestamp.strftime("%H:%M:%S")
        
        print(f"🗑️ Registrando {len(df_eliminados)} eliminaciones de {proceso_origen}")
        
        # Preparar datos para papelera master
        df_papelera = df_eliminados.copy()
        
        # Agregar metadatos de eliminación
        df_papelera['id_eliminacion'] = [f"{proceso_origen}_{i:04d}_{timestamp.strftime('%Y%m%d_%H%M%S')}" 
                                        for i in range(len(df_eliminados))]
        df_papelera['fecha_eliminacion'] = fecha_str
        df_papelera['hora_eliminacion'] = hora_str
        df_papelera['proceso_origen'] = proceso_origen
        
        # PRESERVAR ID ORIGINAL - CRÍTICO PARA RECUPERACIÓN
        ids_originales = []
        for idx, row in df_eliminados.iterrows():
            id_original = None
            
            # Buscar ID en diferentes columnas posibles
            for col_id in ['id', 'ID_Unico', 'Id', 'ID', 'codigo_inmueble', 'codigo_inmuebles24']:
                if col_id in row and pd.notna(row[col_id]) and str(row[col_id]).strip() != '':
                    id_original = str(row[col_id]).strip()
                    break
            
            # Si no se encuentra ID válido, usar índice con prefijo
            if id_original is None:
                id_original = f"sin_id_idx_{idx}"
            
            ids_originales.append(id_original)
        
        df_papelera['id_original_preservado'] = ids_originales
        
        # Procesar razones de eliminación
        if isinstance(razones_eliminacion, list) and len(razones_eliminacion) == len(df_eliminados):
            df_papelera['razon_eliminacion'] = razones_eliminacion
        else:
            df_papelera['razon_eliminacion'] = str(razones_eliminacion)
        
        # Categorizar errores
        df_papelera['categoria_error'] = df_papelera['razon_eliminacion'].apply(self._categorizar_error)
        
        # Agregar detalles si están disponibles
        if detalles_adicionales:
            df_papelera['detalles_error'] = json.dumps(detalles_adicionales, ensure_ascii=False)
        else:
            df_papelera['detalles_error'] = ""
        
        # Valores analizados (para debugging)
        df_papelera['valores_analizados'] = df_papelera.apply(
            lambda row: self._extraer_valores_clave(row), axis=1
        )
        
        df_papelera['observaciones'] = ""
        
        # Guardar en archivo master
        try:
            # Leer archivo existente
            df_master_existente = pd.read_csv(self.archivo_master)
            
            # Concatenar nuevos registros
            df_master_nuevo = pd.concat([df_master_existente, df_papelera], ignore_index=True)
            
            # Guardar
            df_master_nuevo.to_csv(self.archivo_master, index=False)
            
            print(f"✅ Guardados {len(df_eliminados)} registros en papelera master")
            
        except Exception as e:
            print(f"❌ Error al guardar en papelera master: {e}")
        
        # Actualizar resumen
        self._actualizar_resumen(proceso_origen, len(df_eliminados), 
                               archivo_origen, archivo_destino, df_papelera)
    
    def _categorizar_error(self, razon):
        """Categoriza el tipo de error"""
        razon_lower = str(razon).lower()
        
        if any(palabra in razon_lower for palabra in ['datos básicos', 'faltante', 'vacío', 'nulo']):
            return "Datos Faltantes"
        elif any(palabra in razon_lower for palabra in ['dimensional', 'área', 'espacio']):
            return "Incoherencia Dimensional"
        elif any(palabra in razon_lower for palabra in ['relación', 'ratio', 'baños', 'recámara']):
            return "Relación Ilógica"
        elif any(palabra in razon_lower for palabra in ['colonia', 'precio', 'ubicación']):
            return "Incoherencia Geográfica"
        elif any(palabra in razon_lower for palabra in ['tipo', 'propiedad', 'departamento', 'casa']):
            return "Reglas de Tipo"
        elif any(palabra in razon_lower for palabra in ['outlier', 'atípico', 'estadístico']):
            return "Outlier Estadístico"
        elif any(palabra in razon_lower for palabra in ['duplicado', 'repetido']):
            return "Duplicado"
        else:
            return "Otro"
    
    def _extraer_valores_clave(self, row):
        """Extrae valores clave para análisis"""
        valores = {}
        
        if 'precio' in row and pd.notna(row['precio']):
            valores['precio'] = row['precio']
        if 'area_m2' in row and pd.notna(row['area_m2']):
            valores['area_m2'] = row['area_m2']
        if 'recamaras' in row and pd.notna(row['recamaras']):
            valores['recamaras'] = row['recamaras']
        if 'banos_icon' in row and pd.notna(row['banos_icon']):
            valores['banos'] = row['banos_icon']
        if 'tipo_propiedad' in row and pd.notna(row['tipo_propiedad']):
            valores['tipo'] = row['tipo_propiedad']
        
        return json.dumps(valores, ensure_ascii=False)
    
    def _actualizar_resumen(self, proceso, total_eliminados, archivo_origen, archivo_destino, df_papelera):
        """Actualiza el archivo resumen"""
        
        try:
            # Leer resumen existente
            df_resumen = pd.read_csv(self.archivo_resumen)
            
            # Calcular estadísticas
            categoria_principal = df_papelera['categoria_error'].value_counts().index[0] if len(df_papelera) > 0 else "N/A"
            
            # Nuevo registro
            nuevo_registro = {
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'proceso': proceso,
                'total_procesados': "N/A",  # Se actualizará externamente
                'total_eliminados': total_eliminados,
                'porcentaje_eliminado': "N/A",  # Se calculará externamente
                'categoria_error_principal': categoria_principal,
                'archivo_origen': archivo_origen or "N/A",
                'archivo_destino': archivo_destino or "N/A"
            }
            
            # Agregar al resumen
            df_resumen = pd.concat([df_resumen, pd.DataFrame([nuevo_registro])], ignore_index=True)
            
            # Guardar
            df_resumen.to_csv(self.archivo_resumen, index=False)
            
            print(f"📊 Actualizado resumen de eliminaciones")
            
        except Exception as e:
            print(f"❌ Error al actualizar resumen: {e}")
    
    def generar_reporte_completo(self):
        """Genera un reporte completo de todas las eliminaciones"""
        
        try:
            df_master = pd.read_csv(self.archivo_master)
            df_resumen = pd.read_csv(self.archivo_resumen)
            
            print("\n" + "="*60)
            print("📋 REPORTE COMPLETO DE PAPELERA DE RECICLAJE")
            print("="*60)
            
            # Estadísticas generales
            total_eliminados = len(df_master)
            procesos_unicos = df_master['proceso_origen'].nunique()
            
            print(f"📊 Total de propiedades eliminadas: {total_eliminados:,}")
            print(f"🔄 Procesos que han eliminado datos: {procesos_unicos}")
            
            # Por proceso
            print(f"\n📋 ELIMINACIONES POR PROCESO:")
            eliminaciones_por_proceso = df_master.groupby('proceso_origen').agg({
                'id_eliminacion': 'count',
                'categoria_error': lambda x: x.value_counts().index[0]
            }).rename(columns={
                'id_eliminacion': 'total_eliminados',
                'categoria_error': 'error_principal'
            })
            
            for proceso, stats in eliminaciones_por_proceso.iterrows():
                print(f"   • {proceso}: {stats['total_eliminados']} eliminados (Principal: {stats['error_principal']})")
            
            # Por categoría de error
            print(f"\n📋 ELIMINACIONES POR CATEGORÍA:")
            por_categoria = df_master['categoria_error'].value_counts()
            for categoria, cantidad in por_categoria.items():
                porcentaje = (cantidad / total_eliminados) * 100
                print(f"   • {categoria}: {cantidad} ({porcentaje:.1f}%)")
            
            # Por fecha
            print(f"\n📋 ELIMINACIONES POR FECHA:")
            por_fecha = df_master['fecha_eliminacion'].value_counts().sort_index()
            for fecha, cantidad in por_fecha.items():
                print(f"   • {fecha}: {cantidad} eliminados")
            
            return df_master, df_resumen
            
        except Exception as e:
            print(f"❌ Error al generar reporte: {e}")
            return None, None
    
    def ver_estado_papelera(self):
        """Muestra el estado actual de la papelera con estadísticas detalladas"""
        
        print("=" * 60)
        print("📊 ESTADO ACTUAL DE LA PAPELERA DE RECICLAJE")
        print("=" * 60)
        
        if not os.path.exists(self.archivo_master):
            print("🗑️ La papelera está vacía (sin archivo master)")
            return
        
        try:
            df_master = pd.read_csv(self.archivo_master, low_memory=False)
            
            print(f"📁 Total registros en papelera: {len(df_master):,}")
            print(f"📄 Archivo master: {self.archivo_master}")
            print("")
            
            # Estadísticas por proceso
            print("📋 REGISTROS POR PROCESO:")
            procesos = df_master['proceso_origen'].value_counts()
            for proceso, cantidad in procesos.items():
                print(f"   • {proceso}: {cantidad:,} registros")
            print("")
            
            # Estadísticas por categoría de error
            if 'categoria_error' in df_master.columns:
                print("🔍 REGISTROS POR CATEGORÍA DE ERROR:")
                categorias = df_master['categoria_error'].value_counts()
                for categoria, cantidad in categorias.items():
                    print(f"   • {categoria}: {cantidad:,} registros")
                print("")
            
            # Verificar IDs preservados
            if 'id_original_preservado' in df_master.columns:
                ids_validos = df_master['id_original_preservado'].notna().sum()
                ids_sin_id = df_master['id_original_preservado'].str.startswith('sin_id', na=False).sum()
                ids_recuperables = ids_validos - ids_sin_id
                
                print("🔗 ESTADO DE IDs ORIGINALES:")
                print(f"   • IDs preservados y recuperables: {ids_recuperables:,}")
                print(f"   • Sin ID original (usando índice): {ids_sin_id:,}")
                print(f"   • Total con información: {ids_validos:,}")
                print("")
            
            # Últimas eliminaciones
            if 'fecha_eliminacion' in df_master.columns:
                df_master['fecha_eliminacion'] = pd.to_datetime(df_master['fecha_eliminacion'], errors='coerce')
                ultima_fecha = df_master['fecha_eliminacion'].max()
                print(f"📅 Última eliminación registrada: {ultima_fecha}")
            
            # Mostrar muestra de registros
            print("\n🔍 MUESTRA DE REGISTROS EN PAPELERA (últimos 5):")
            columnas_muestra = ['id_eliminacion', 'proceso_origen', 'razon_eliminacion', 'id_original_preservado']
            columnas_disponibles = [col for col in columnas_muestra if col in df_master.columns]
            
            if columnas_disponibles:
                muestra = df_master[columnas_disponibles].tail(5)
                for _, row in muestra.iterrows():
                    print(f"   • {row['id_eliminacion']} | {row.get('proceso_origen', 'N/A')} | ID: {row.get('id_original_preservado', 'N/A')}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error al leer estado de papelera: {e}")
    
    def buscar_propiedad_eliminada(self, id_buscar):
        """
        Busca una propiedad específica en la papelera por su ID original
        
        Args:
            id_buscar: ID original de la propiedad a buscar
            
        Returns:
            DataFrame con los registros encontrados o None si no se encuentra
        """
        
        if not os.path.exists(self.archivo_master):
            print("🗑️ No hay archivo de papelera para buscar")
            return None
        
        try:
            df_master = pd.read_csv(self.archivo_master, low_memory=False)
            
            # Buscar por ID original preservado
            if 'id_original_preservado' in df_master.columns:
                # Convertir id_buscar a int si es posible, sino mantenerlo como string
                try:
                    id_buscar_num = int(id_buscar)
                    resultados = df_master[df_master['id_original_preservado'] == id_buscar_num]
                except (ValueError, TypeError):
                    resultados = df_master[df_master['id_original_preservado'] == str(id_buscar)]
                
                if len(resultados) > 0:
                    print(f"🔍 Encontradas {len(resultados)} eliminaciones para ID: {id_buscar}")
                    for _, row in resultados.iterrows():
                        print(f"   • Proceso: {row.get('proceso_origen', 'N/A')}")
                        print(f"   • Razón: {row.get('razon_eliminacion', 'N/A')}")
                        print(f"   • Fecha: {row.get('fecha_eliminacion', 'N/A')}")
                        print("   " + "-" * 50)
                    return resultados
                else:
                    print(f"❌ No se encontró la propiedad con ID: {id_buscar}")
                    return None
            else:
                print("⚠️ No hay información de IDs originales en la papelera")
                return None
                
        except Exception as e:
            print(f"❌ Error al buscar en papelera: {e}")
            return None
        """
        Permite recuperar propiedades eliminadas según filtros
        
        Args:
            filtros: Diccionario con filtros a aplicar
            guardar_como: Archivo donde guardar las propiedades recuperadas
        """
        
        try:
            df_master = pd.read_csv(self.archivo_master)
            
            if filtros:
                df_filtrado = df_master.copy()
                
                for campo, valor in filtros.items():
                    if campo in df_filtrado.columns:
                        if isinstance(valor, list):
                            df_filtrado = df_filtrado[df_filtrado[campo].isin(valor)]
                        else:
                            df_filtrado = df_filtrado[df_filtrado[campo] == valor]
                
                print(f"🔍 Encontrados {len(df_filtrado)} registros con los filtros aplicados")
                
                if guardar_como and len(df_filtrado) > 0:
                    # Eliminar columnas de metadatos para recuperación
                    columnas_recuperacion = [col for col in df_filtrado.columns 
                                           if not col.startswith(('id_eliminacion', 'fecha_eliminacion', 
                                                                'hora_eliminacion', 'proceso_origen',
                                                                'razon_eliminacion', 'categoria_error',
                                                                'detalles_error', 'valores_analizados',
                                                                'observaciones'))]
                    
                    df_recuperado = df_filtrado[columnas_recuperacion]
                    df_recuperado.to_csv(guardar_como, index=False)
                    print(f"💾 Propiedades recuperadas guardadas en: {guardar_como}")
                
                return df_filtrado
            else:
                return df_master
                
        except Exception as e:
            print(f"❌ Error al recuperar propiedades: {e}")
            return None

# Función para integrar con el análisis lógico existente
def integrar_papelera_analisis_logico():
    """
    Modifica el script de análisis lógico para usar la papelera
    """
    
    print("🔧 Integrando papelera con análisis lógico...")
    
    # Esta función se llamará desde el script modificado
    return PapeleraReciclaje()

if __name__ == "__main__":
    # Ejemplo de uso
    papelera = PapeleraReciclaje()
    
    print("🗑️ SISTEMA DE PAPELERA DE RECICLAJE INMOBILIARIO")
    print("=" * 55)
    print("Sistema inicializado correctamente")
    print(f"📁 Directorio: {papelera.directorio_papelera}")
    print(f"📄 Archivo master: {papelera.archivo_master}")
    print(f"📊 Archivo resumen: {papelera.archivo_resumen}")

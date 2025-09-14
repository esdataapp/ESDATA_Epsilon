"""
ANÁLISIS AVANZADO DE MARKETING INMOBILIARIO
Extrae variables de marketing y promoción de las descripciones de propiedades

Este script analiza las descripciones inmobiliarias para extraer:
1. ADJETIVOS PROMOCIONALES (binario 1/0): moderno, cómodo, espectacular, único, etc.
2. CARACTERÍSTICAS FÍSICAS (numéricas): m2, recámaras, baños, niveles, etc.
3. AMENIDADES Y SERVICIOS (binario 1/0): gimnasio, alberca, seguridad, etc.
4. TÉRMINOS DE UBICACIÓN (binario 1/0): céntrico, exclusivo, cerca de, etc.
5. ELEMENTOS ARQUITECTÓNICOS (binario 1/0): balcones, terraza, jardín, etc.

Autor: Asistente IA
Fecha: Septiembre 2025
"""

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
import unicodedata
import warnings
from collections import Counter

warnings.filterwarnings('ignore')

class AnalizadorMarketingInmobiliario:
    """
    Analizador especializado para extraer variables de marketing inmobiliario
    """
    
    def __init__(self):
        # DICCIONARIO DE ADJETIVOS PROMOCIONALES (1/0)
        self.adjetivos_promocionales = {
            # Calidad y Estado
            'moderno': [r'\bmodern[ao]s?\b'],
            'contemporaneo': [r'\bcontemporáne[ao]s?\b', r'\bcontemporane[ao]s?\b'],
            'nuevo': [r'\bnuev[ao]s?\b', r'\ba estrenar\b'],
            'espectacular': [r'\bespectacular(es)?\b'],
            'increible': [r'\bincre[ií]ble(s)?\b'],
            'hermoso': [r'\bhermos[ao]s?\b', r'\bbell[ao]s?\b'],
            'elegante': [r'\belegante(s)?\b'],
            'lujoso': [r'\blujós[ao]s?\b'],
            'exclusivo': [r'\bexclusiv[ao]s?\b'],
            'premium': [r'\bpremium\b'],
            'impecable': [r'\bimpecable(s)?\b'],
            
            # Comodidad y Confort
            'comodo': [r'\bcómod[ao]s?\b', r'\bcomod[ao]s?\b'],
            'confortable': [r'\bconfortable(s)?\b'],
            'acogedor': [r'\bacoged[o]r(es|a|as)?\b'],
            'funcional': [r'\bfuncional(es)?\b'],
            'practico': [r'\bpráctico\b', r'\bpractico\b'],
            'espacioso': [r'\bespacios[ao]s?\b', r'\bampli[ao]s?\b'],
            
            # Unicidad y Exclusividad
            'unico': [r'\b[uú]nic[ao]s?\b'],
            'especial': [r'\bespecial(es)?\b'],
            'extraordinario': [r'\bextraordinari[ao]s?\b'],
            'excepcional': [r'\bexcepcional(es)?\b'],
            'ideal': [r'\bideal(es)?\b'],
            'perfecto': [r'\bperfect[ao]s?\b'],
            
            # Ubicación
            'centrico': [r'\bcéntric[ao]s?\b', r'\bcentr[ao]l(es)?\b'],
            'privilegiado': [r'\bprivilegia[wd]o(s|a|as)?\b'],
            'estrategico': [r'\bestratégic[ao]s?\b'],
            'conveniente': [r'\bconveniente(s)?\b'],
            
            # Experiencia
            'encantador': [r'\bencanatd[o]r(es|a|as)?\b'],
            'sorprendente': [r'\bsorprendente(s)?\b'],
            'fascinante': [r'\bfascinante(s)?\b'],
            'maravilloso': [r'\bmaravillos[ao]s?\b'],
            
            # Estado físico
            'remodelado': [r'\bremodelad[ao]s?\b', r'\brenova[wd]o(s|a|as)?\b'],
            'restaurado': [r'\brestaurad[ao]s?\b'],
            'bien_conservado': [r'\bbien conservad[ao]s?\b'],
            'impecable': [r'\bimpecable(s)?\b'],
            
            # Iluminación
            'iluminado': [r'\biluminad[ao]s?\b', r'\bbien iluminad[ao]s?\b'],
            'luminoso': [r'\bluminos[ao]s?\b'],
            'soleado': [r'\bsolead[ao]s?\b'],
            
            # Diseño
            'minimalista': [r'\bminimalista(s)?\b'],
            'vanguardista': [r'\bvanguardista(s)?\b'],
            'tradicional': [r'\btradicional(es)?\b'],
            'clasico': [r'\bclásic[ao]s?\b', r'\bclasic[ao]s?\b']
        }
        
        # DICCIONARIO DE CONVERSIÓN DE NÚMEROS EN PALABRAS
        self.numeros_palabras = {
            # Números básicos
            'un': 1, 'una': 1, 'uno': 1,
            'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
            'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
            'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
            'dieciseis': 16, 'diecisiete': 17, 'dieciocho': 18, 'diecinueve': 19, 'veinte': 20,
            # Variaciones con acentos
            'dieciséis': 16, 'diecisiéis': 16,
            # Números compuestos comunes
            'veintiun': 21, 'veintiuno': 21, 'veintidos': 22, 'veintitres': 23, 'veinticuatro': 24, 'veinticinco': 25,
            'treinta': 30, 'cuarenta': 40, 'cincuenta': 50
        }
        
        # DICCIONARIO DE CARACTERÍSTICAS NUMÉRICAS - VERSIÓN AVANZADA
        self.caracteristicas_numericas = {
            # Superficies - patrones más específicos
            'area_m2_desc': [
                r'(\d+(?:\.\d+)?)\s*m2?\b',
                r'(\d+(?:\.\d+)?)\s*metros?\s*cuadrados?\b',
                r'(\d+(?:\.\d+)?)\s*m²\b',
                r'con\s+(\d+(?:\.\d+)?)\s*m2?\s+de\b',
                r'\((\d+(?:\.\d+)?)\)\s*m2?\b',
                r'superficie\s*de\s*(\d+(?:\.\d+)?)\s*m2?\b'
            ],
            
            # Habitaciones - PATRONES EXTENDIDOS
            'recamaras_desc': [
                # Números directos
                r'(\d+)\s*rec[áa]maras?\b',
                r'(\d+)\s*habitacion(es)?\b',
                r'(\d+)\s*dormitorios?\b',
                r'(\d+)\s*cuartos?\b',
                # Números entre paréntesis
                r'\((\d+)\)\s*rec[áa]maras?\b',
                r'\((\d+)\)\s*habitacion(es)?\b',
                r'\((\d+)\)\s*cuartos?\b',
                # Números en palabras - casos específicos
                r'\b(una)\s+rec[áa]mara\b',
                r'\b(dos|tres|cuatro|cinco|seis)\s+rec[áa]maras?\b',
                r'\b(dos|tres|cuatro|cinco|seis)\s+habitacion(es)?\b',
                r'\b(dos|tres|cuatro|cinco|seis)\s+cuartos?\b',
                # Descripciones específicas
                r'cuenta\s+con\s+(\d+)\s+rec[áa]maras?\b',
                r'dispone\s+de\s+(\d+)\s+rec[áa]maras?\b',
                r'tiene\s+(\d+)\s+rec[áa]maras?\b'
            ],
            
            # Baños - PATRONES EXTENDIDOS
            'banos_totales_desc': [
                r'(\d+)\s*baños?\b',
                r'(\d+)\s*ba[ñn]os?\b',
                r'\((\d+)\)\s*baños?\b',
                r'\b(dos|tres|cuatro|cinco)\s+baños?\b',
                r'cuenta\s+con\s+(\d+)\s+baños?\b',
                r'dispone\s+de\s+(\d+)\s+baños?\b',
                r'(\d+)\s+baños?\s+completos?\b'
            ],
            
            # Medios baños - PATRONES EXTENDIDOS
            'medios_banos_desc': [
                r'(\d+)\s*medios?\s*baños?\b',
                r'(\d+)\s*1/2\s*baños?\b',
                r'(\d+)\.5\s*baños?\b',
                r'\((\d+)\)\s*medios?\s*baños?\b',
                r'\b(un|dos|tres)\s+medio\s+baño\b'
            ],
            
            # Estacionamientos - PATRONES EXTENDIDOS
            'estacionamientos_desc': [
                r'(\d+)\s*estacionamientos?\b',
                r'(\d+)\s*cajones?\b',
                r'(\d+)\s*cocheras?\b',
                r'(\d+)\s*garages?\b',
                r'(\d+)\s*lugares?\s*de\s*estacionamiento\b',
                r'\((\d+)\)\s*estacionamientos?\b',
                r'\((\d+)\)\s*cajones?\b',
                r'\b(un|dos|tres|cuatro|cinco)\s+estacionamientos?\b',
                r'\b(un|dos|tres|cuatro|cinco)\s+cajones?\b',
                r'cuenta\s+con\s+(\d+)\s+estacionamientos?\b',
                r'incluye\s+(\d+)\s+estacionamientos?\b'
            ],
            
            # Niveles/Pisos - PATRONES EXTENDIDOS
            'niveles_desc': [
                r'(\d+)\s*niveles?\b',
                r'(\d+)\s*pisos?\b',
                r'(\d+)\s*plantas?\b',
                r'\((\d+)\)\s*niveles?\b',
                r'\b(dos|tres|cuatro|cinco)\s+niveles?\b',
                r'\b(dos|tres|cuatro|cinco)\s+pisos?\b',
                r'de\s+(\d+)\s+niveles?\b',
                r'casa\s+de\s+(\d+)\s+plantas?\b'
            ],
            
            # Balcones/Terrazas (cantidad) - PATRONES EXTENDIDOS
            'balcones_desc': [
                r'(\d+)\s*balcon(es)?\b',
                r'(\d+)\s*balcón(es)?\b',
                r'\((\d+)\)\s*balcon(es)?\b',
                r'\b(un|dos|tres)\s+balc[óo]n(es)?\b'
            ],
            
            'terrazas_desc': [
                r'(\d+)\s*terraza(s)?\b',
                r'\((\d+)\)\s*terraza(s)?\b',
                r'\b(una|dos|tres)\s+terraza(s)?\b'
            ],
            
            # Antigüedad - PATRONES EXTENDIDOS
            'antiguedad_anos_desc': [
                r'(\d+)\s*años?\s*de\s*antigüedad\b',
                r'construid[ao]\s*hace\s*(\d+)\s*años?\b',
                r'(\d+)\s*años?\s*de\s*construcci[óo]n\b',
                r'\((\d+)\)\s*años?\s*de\s*antigüedad\b',
                r'antigüedad\s*de\s*(\d+)\s*años?\b'
            ]
        }
        
        # DICCIONARIO DE AMENIDADES Y SERVICIOS (1/0)  
        self.amenidades_servicios = {
            # Seguridad
            'seguridad_24h': [r'\bseguridad\s*24\s*h(oras)?\b', r'\bvigilancia\s*24\s*h(oras)?\b'],
            'circuito_cerrado': [r'\bcircuito\s*cerrado\b', r'\bcctv\b', r'\bcámaras\s*de\s*vigilancia\b'],
            'caseta_vigilancia': [r'\bcaseta\s*de\s*(vigilancia|seguridad)\b'],
            'acceso_controlado': [r'\bacceso\s*controlad[ao]\b'],
            
            # Instalaciones deportivas
            'gimnasio': [r'\bgimnasio\b', r'\bgym\b'],
            'alberca': [r'\balberca\b', r'\bpiscina\b'],
            'cancha_tenis': [r'\bcancha\s*de\s*tenis\b'],
            'cancha_padel': [r'\bcancha\s*de\s*padel\b'],
            'area_juegos': [r'\b[aá]rea\s*de\s*juegos\b'],
            
            # Espacios comunes
            'salon_eventos': [r'\bsal[oó]n\s*de\s*eventos\b'],
            'salon_fiestas': [r'\bsal[oó]n\s*de\s*fiestas\b'],
            'salon_usos_multiples': [r'\bsal[oó]n\s*de\s*usos\s*m[úu]ltiples\b'],
            'roof_garden': [r'\broof\s*garden\b', r'\bazotea\b'],
            'terraza_comun': [r'\bterraza\s*com[uú]n\b'],
            
            # Comodidades
            'elevador': [r'\belevador(es)?\b', r'\basensor(es)?\b'],
            'aire_acondicionado': [r'\baire\s*acondicionad[ao]\b', r'\bclima\b', r'\ba/?c\b'],
            'calefaccion': [r'\bcalefacci[óo]n\b'],
            'calentador_agua': [r'\bcalentador\s*de\s*agua\b'],
            
            # Cocina y electrodomésticos  
            'cocina_integral': [r'\bcocina\s*integral\b'],
            'cocina_equipada': [r'\bcocina\s*equipada\b'],
            'linea_blanca': [r'\bl[ií]nea\s*blanca\b'],
            'electrodomesticos': [r'\belectrodom[ée]sticos\b'],
            
            # Servicios incluidos
            'internet_incluido': [r'\binternet\s*incluid[ao]\b', r'\bwifi\s*incluid[ao]\b'],
            'gas_incluido': [r'\bgas\s*incluid[ao]\b'],
            'agua_incluida': [r'\bagua\s*incluida\b'],
            'luz_incluida': [r'\bluz\s*incluida\b'],
            'mantenimiento_incluido': [r'\bmantenimiento\s*incluid[ao]\b'],
            
            # Características especiales
            'mascotas_permitidas': [r'\bmascotas\s*permitidas\b', r'\bpet\s*friendly\b', r'\bmascotas\s*bienvenidas\b'],
            'amueblado': [r'\bamueblad[ao]\b', r'\bcon\s*muebles\b'],
            'semi_amueblado': [r'\bsemi\s*amueblad[ao]\b'],
            'vista_panoramica': [r'\bvista\s*panor[áa]mica\b'],
            'frente_al_mar': [r'\bfrente\s*al\s*mar\b', r'\bvista\s*al\s*mar\b']
        }
        
        # Compilar todos los patrones regex
        self._compilar_patrones()
        
        # Contadores para estadísticas
        self.estadisticas = {
            'propiedades_procesadas': 0,
            'adjetivos_encontrados': Counter(),
            'caracteristicas_extraidas': Counter(),
            'amenidades_detectadas': Counter()
        }
    
    def _compilar_patrones(self):
        """Compila todos los patrones regex para mejor rendimiento"""
        
        # Compilar adjetivos promocionales
        self.adjetivos_compilados = {}
        for adjetivo, patrones in self.adjetivos_promocionales.items():
            self.adjetivos_compilados[adjetivo] = [re.compile(p, re.IGNORECASE) for p in patrones]
        
        # Compilar características numéricas
        self.numericas_compiladas = {}
        for caracteristica, patrones in self.caracteristicas_numericas.items():
            self.numericas_compiladas[caracteristica] = [re.compile(p, re.IGNORECASE) for p in patrones]
        
        # Compilar amenidades y servicios
        self.amenidades_compiladas = {}
        for amenidad, patrones in self.amenidades_servicios.items():
            self.amenidades_compiladas[amenidad] = [re.compile(p, re.IGNORECASE) for p in patrones]
    
    def normalizar_texto(self, texto):
        """Normaliza y limpia el texto para análisis MANTENIENDO acentos correctamente"""
        if pd.isna(texto) or texto == '':
            return ''
        
        # Convertir a string y limpiar
        texto = str(texto).lower().strip()
        
        # NO usar NFKD que desarma los acentos, usar NFC que los preserva
        texto = unicodedata.normalize('NFC', texto)
        
        # Limpiar caracteres especiales pero MANTENER acentos y eñes
        # Solo eliminar caracteres raros, no los acentos normales
        texto = re.sub(r'[^\w\sáéíóúñüç.,!¿?()²³-]', ' ', texto)
        
        # Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def extraer_adjetivos_promocionales(self, texto):
        """Extrae adjetivos promocionales del texto (1/0)"""
        texto_norm = self.normalizar_texto(texto)
        resultados = {}
        
        for adjetivo, patrones_compilados in self.adjetivos_compilados.items():
            encontrado = False
            
            for patron in patrones_compilados:
                if patron.search(texto_norm):
                    encontrado = True
                    self.estadisticas['adjetivos_encontrados'][adjetivo] += 1
                    break
            
            resultados[f'adj_{adjetivo}'] = 1 if encontrado else 0
        
        return resultados
    
    def extraer_caracteristicas_numericas(self, texto):
        """Extrae características numéricas del texto incluyendo números en palabras"""
        texto_norm = self.normalizar_texto(texto)
        resultados = {}
        
        for caracteristica, patrones_compilados in self.numericas_compiladas.items():
            valor_encontrado = None
            
            for patron in patrones_compilados:
                matches = patron.findall(texto_norm)
                if matches:
                    for match in matches:
                        try:
                            # Si el match es una tupla (grupos múltiples), tomar el primer grupo no vacío
                            if isinstance(match, tuple):
                                match = next((m for m in match if m), None)
                            
                            if not match:
                                continue
                            
                            # Convertir números en palabras a dígitos
                            if match.lower() in self.numeros_palabras:
                                valor = self.numeros_palabras[match.lower()]
                            else:
                                # Intentar conversión directa a float
                                valor = float(match)
                            
                            # Aplicar filtros de valores razonables según el tipo
                            if self._es_valor_razonable(caracteristica, valor):
                                valor_encontrado = valor
                                self.estadisticas['caracteristicas_extraidas'][caracteristica] += 1
                                break
                        except (ValueError, TypeError):
                            continue
                
                if valor_encontrado is not None:
                    break
            
            # Casos especiales para descripciones complejas (ej: "una recámara matrimonial y tres para hijos")
            if valor_encontrado is None and caracteristica == 'recamaras_desc':
                valor_encontrado = self._extraer_recamaras_complejas(texto_norm)
                if valor_encontrado:
                    self.estadisticas['caracteristicas_extraidas'][caracteristica] += 1
            
            resultados[caracteristica] = valor_encontrado
        
        return resultados
    
    def _es_valor_razonable(self, caracteristica, valor):
        """Valida si el valor extraído es razonable para el tipo de característica"""
        rangos_razonables = {
            'area_m2_desc': (15, 2000),  # 15 a 2000 m²
            'recamaras_desc': (1, 10),    # 1 a 10 recámaras
            'banos_totales_desc': (1, 8), # 1 a 8 baños
            'medios_banos_desc': (1, 4),  # 1 a 4 medios baños
            'estacionamientos_desc': (1, 10), # 1 a 10 estacionamientos
            'niveles_desc': (1, 5),       # 1 a 5 niveles
            'balcones_desc': (1, 6),      # 1 a 6 balcones
            'terrazas_desc': (1, 4),      # 1 a 4 terrazas
            'antiguedad_anos_desc': (0, 100) # 0 a 100 años
        }
        
        if caracteristica in rangos_razonables:
            min_val, max_val = rangos_razonables[caracteristica]
            return min_val <= valor <= max_val
        
        return valor > 0
    
    def _extraer_recamaras_complejas(self, texto):
        """Extrae recámaras de descripciones complejas como 'una recámara matrimonial y tres para hijos'"""
        
        # Patrón para "una recámara + número adicionales"
        patron_complejo1 = re.compile(r'una\s+rec[áa]mara\s+.*?\s+y\s+(dos|tres|cuatro|cinco)\s+(?:para\s+)?(?:hijos|adicionales|más)?', re.IGNORECASE)
        match = patron_complejo1.search(texto)
        if match:
            numero_adicional = self.numeros_palabras.get(match.group(1).lower(), 0)
            return 1 + numero_adicional  # una + las adicionales
        
        # Patrón para "X recámaras principales y Y adicionales"
        patron_complejo2 = re.compile(r'(\d+)\s+rec[áa]maras?\s+.*?\s+y\s+(\d+)', re.IGNORECASE)
        match = patron_complejo2.search(texto)
        if match:
            principal = int(match.group(1))
            adicional = int(match.group(2))
            return principal + adicional
        
        # Patrón para "recámara principal y X adicionales"
        patron_complejo3 = re.compile(r'rec[áa]mara\s+principal\s+y\s+(dos|tres|cuatro|cinco)\s+adicionales?', re.IGNORECASE)
        match = patron_complejo3.search(texto)
        if match:
            numero_adicional = self.numeros_palabras.get(match.group(1).lower(), 0)
            return 1 + numero_adicional
        
        # Patrón para "master bedroom y X recámaras"
        patron_complejo4 = re.compile(r'master\s+bedroom\s+y\s+(dos|tres|cuatro|cinco)\s+rec[áa]maras?', re.IGNORECASE)
        match = patron_complejo4.search(texto)
        if match:
            numero_adicional = self.numeros_palabras.get(match.group(1).lower(), 0)
            return 1 + numero_adicional
        
        return None
    
    def extraer_amenidades_servicios(self, texto):
        """Extrae amenidades y servicios del texto (1/0)"""
        texto_norm = self.normalizar_texto(texto)
        resultados = {}
        
        for amenidad, patrones_compilados in self.amenidades_compiladas.items():
            encontrado = False
            
            for patron in patrones_compilados:
                if patron.search(texto_norm):
                    encontrado = True
                    self.estadisticas['amenidades_detectadas'][amenidad] += 1
                    break
            
            resultados[f'serv_{amenidad}'] = 1 if encontrado else 0
        
        return resultados
    
    def analizar_descripcion_y_titulo_separados(self, descripcion, titulo):
        """Analiza descripción y título por separado para comparar estrategias de marketing"""
        
        # Analizar DESCRIPCIÓN
        resultado_desc = {}
        if descripcion and pd.notna(descripcion):
            texto_desc = self.normalizar_texto(str(descripcion))
            
            # 1. Adjetivos promocionales en descripción
            adjetivos_desc = self.extraer_adjetivos_promocionales(texto_desc)
            for key, value in adjetivos_desc.items():
                resultado_desc[f'desc_{key.replace("adj_", "")}'] = value
            
            # 2. Características numéricas en descripción
            numericas_desc = self.extraer_caracteristicas_numericas(texto_desc)
            for key, value in numericas_desc.items():
                resultado_desc[f'desc_{key}'] = value
            
            # 3. Amenidades en descripción
            amenidades_desc = self.extraer_amenidades_servicios(texto_desc)
            for key, value in amenidades_desc.items():
                resultado_desc[f'desc_{key.replace("serv_", "")}'] = value
        
        # Analizar TÍTULO
        resultado_titulo = {}
        if titulo and pd.notna(titulo):
            texto_titulo = self.normalizar_texto(str(titulo))
            
            # 1. Adjetivos promocionales en título
            adjetivos_titulo = self.extraer_adjetivos_promocionales(texto_titulo)
            for key, value in adjetivos_titulo.items():
                resultado_titulo[f'titulo_{key.replace("adj_", "")}'] = value
            
            # 2. Características numéricas en título
            numericas_titulo = self.extraer_caracteristicas_numericas(texto_titulo)
            for key, value in numericas_titulo.items():
                resultado_titulo[f'titulo_{key}'] = value
            
            # 3. Amenidades en título
            amenidades_titulo = self.extraer_amenidades_servicios(texto_titulo)
            for key, value in amenidades_titulo.items():
                resultado_titulo[f'titulo_{key.replace("serv_", "")}'] = value
        
        # Combinar resultados
        resultado_combinado = {}
        resultado_combinado.update(resultado_desc)
        resultado_combinado.update(resultado_titulo)
        
        self.estadisticas['propiedades_procesadas'] += 1
        
        # Actualizar contadores separados
        if not hasattr(self.estadisticas, 'desc_adjetivos'):
            self.estadisticas['desc_adjetivos'] = Counter()
            self.estadisticas['titulo_adjetivos'] = Counter()
            self.estadisticas['desc_numericas'] = Counter()
            self.estadisticas['titulo_numericas'] = Counter()
            self.estadisticas['desc_amenidades'] = Counter()
            self.estadisticas['titulo_amenidades'] = Counter()
        
        # Contar estadísticas por separado
        for key, value in resultado_desc.items():
            if key.startswith('desc_') and not key.endswith('_desc'):
                if value == 1:  # Solo contar binarios activados
                    self.estadisticas['desc_adjetivos'][key] += 1
            elif key.startswith('desc_') and key.endswith('_desc'):
                if value is not None:  # Solo contar numéricas encontradas
                    self.estadisticas['desc_numericas'][key] += 1
        
        for key, value in resultado_titulo.items():
            if key.startswith('titulo_') and not key.endswith('_desc'):
                if value == 1:  # Solo contar binarios activados
                    self.estadisticas['titulo_adjetivos'][key] += 1
            elif key.startswith('titulo_') and key.endswith('_desc'):
                if value is not None:  # Solo contar numéricas encontradas
                    self.estadisticas['titulo_numericas'][key] += 1
        
        return resultado_combinado
    
    def procesar_archivo_completo(self, archivo_entrada):
        """Procesa archivo completo y genera CSV con variables de marketing"""
        
        print(f"🏠 ANALIZADOR DE MARKETING INMOBILIARIO")
        print(f"=" * 50)
        print(f"📂 Cargando archivo: {archivo_entrada}")
        
        # Cargar datos
        try:
            df = pd.read_csv(archivo_entrada, encoding='utf-8-sig', low_memory=False)
            print(f"   ✅ Cargadas {len(df):,} propiedades")
        except Exception as e:
            print(f"   ❌ Error al cargar archivo: {e}")
            return None
        
        # Verificar columnas necesarias
        columnas_necesarias = ['id', 'descripcion']
        columnas_faltantes = [col for col in columnas_necesarias if col not in df.columns]
        if columnas_faltantes:
            print(f"   ❌ Faltan columnas: {columnas_faltantes}")
            return None
        
        print(f"📊 Iniciando análisis de descripciones...")
        
        # Procesar cada propiedad
        resultados = []
        contador = 0
        
        for idx, row in df.iterrows():
            
            # Analizar descripción y título por separado
            descripcion = row.get('descripcion', '')
            titulo = row.get('titulo', '')
            
            # Analizar con método separado
            variables_extraidas = self.analizar_descripcion_y_titulo_separados(descripcion, titulo)
            
            # Agregar TODAS las variables del archivo original
            resultado_fila = {
                # Variables básicas de identificación
                'id': row['id'],
                'PaginaWeb': row.get('PaginaWeb', ''),
                'Ciudad': row.get('Ciudad', ''),
                'Fecha_Scrap': row.get('Fecha_Scrap', ''),
                'tipo_propiedad': row.get('tipo_propiedad', ''),
                
                # Variables numéricas de la propiedad
                'area_m2': row.get('area_m2', ''),
                'recamaras': row.get('recamaras', ''),
                'estacionamientos': row.get('estacionamientos', ''),
                
                # Variables comerciales
                'operacion': row.get('operacion', ''),
                'precio': row.get('precio', ''),
                'mantenimiento': row.get('mantenimiento', ''),
                
                # Variables de ubicación
                'Colonia': row.get('Colonia', ''),
                'longitud': row.get('longitud', ''),
                'latitud': row.get('latitud', ''),
                'direccion': row.get('direccion', ''),
                
                # Variables de texto completas
                'titulo': row.get('titulo', ''),
                'descripcion': row.get('descripcion', ''),
                
                # Variables del anunciante
                'anunciante': row.get('anunciante', ''),
                'codigo_anunciante': row.get('codigo_anunciante', ''),
                'codigo_inmuebles24': row.get('codigo_inmuebles24', ''),
                
                # Variables adicionales que puedan existir
                'tiempo_publicacion': row.get('tiempo_publicacion', ''),
                'area_total': row.get('area_total', ''),
                'area_cubierta': row.get('area_cubierta', ''),
                'banos_icon': row.get('banos_icon', ''),
                'estacionamientos_icon': row.get('estacionamientos_icon', ''),
                'recamaras_icon': row.get('recamaras_icon', ''),
                'medio_banos_icon': row.get('medio_banos_icon', ''),
                'antiguedad_icon': row.get('antiguedad_icon', ''),
                'Caracteristicas_generales': row.get('Caracteristicas_generales', ''),
                'Servicios': row.get('Servicios', ''),
                'Amenidades': row.get('Amenidades', ''),
                'Exteriores': row.get('Exteriores', ''),
                'archivo_origen': row.get('archivo_origen', ''),
                'carpeta_origen': row.get('carpeta_origen', '')
            }
            
            # Agregar variables extraídas de marketing
            resultado_fila.update(variables_extraidas)
            
            resultados.append(resultado_fila)
            
            contador += 1
            if contador % 1000 == 0:
                print(f"   • Procesadas: {contador:,}/{len(df):,} propiedades")
        
        # Convertir resultados a DataFrame
        df_marketing = pd.DataFrame(resultados)
        
        print(f"✅ Análisis completado:")
        print(f"   • Propiedades analizadas: {len(df_marketing):,}")
        print(f"   • Variables generadas: {len(df_marketing.columns):,}")
        
        return df_marketing
    
    def generar_reporte_estadisticas(self):
        """Genera reporte de estadísticas del análisis de marketing separando descripción y título"""
        
        print(f"\n" + "=" * 80)
        print(f"📈 ESTADÍSTICAS DEL ANÁLISIS DE MARKETING - DESCRIPCIÓN vs TÍTULO")
        print(f"=" * 80)
        
        print(f"📊 Propiedades procesadas: {self.estadisticas['propiedades_procesadas']:,}")
        print(f"")
        
        # Estadísticas de DESCRIPCIÓN
        if hasattr(self.estadisticas, 'desc_adjetivos') and self.estadisticas['desc_adjetivos']:
            print(f"📝 TOP 10 ADJETIVOS EN DESCRIPCIONES:")
            top_desc_adj = self.estadisticas['desc_adjetivos'].most_common(10)
            for i, (adjetivo, count) in enumerate(top_desc_adj, 1):
                porcentaje = (count / self.estadisticas['propiedades_procesadas']) * 100
                adjetivo_clean = adjetivo.replace('desc_', '').replace('_', ' ').title()
                print(f"   {i:2d}. {adjetivo_clean}: {count:,} ({porcentaje:.1f}%)")
            print("")
        
        # Estadísticas de TÍTULO
        if hasattr(self.estadisticas, 'titulo_adjetivos') and self.estadisticas['titulo_adjetivos']:
            print(f"🏷️ TOP 10 ADJETIVOS EN TÍTULOS:")
            top_titulo_adj = self.estadisticas['titulo_adjetivos'].most_common(10)
            for i, (adjetivo, count) in enumerate(top_titulo_adj, 1):
                porcentaje = (count / self.estadisticas['propiedades_procesadas']) * 100
                adjetivo_clean = adjetivo.replace('titulo_', '').replace('_', ' ').title()
                print(f"   {i:2d}. {adjetivo_clean}: {count:,} ({porcentaje:.1f}%)")
            print("")
        
        # Estadísticas numéricas DESCRIPCIÓN
        if hasattr(self.estadisticas, 'desc_numericas') and self.estadisticas['desc_numericas']:
            print(f"🔢 CARACTERÍSTICAS NUMÉRICAS EN DESCRIPCIONES:")
            top_desc_num = self.estadisticas['desc_numericas'].most_common(5)
            for i, (caracteristica, count) in enumerate(top_desc_num, 1):
                porcentaje = (count / self.estadisticas['propiedades_procesadas']) * 100
                caract_clean = caracteristica.replace('desc_', '').replace('_', ' ').title()
                print(f"   {i:2d}. {caract_clean}: {count:,} ({porcentaje:.1f}%)")
            print("")
        
        # Estadísticas numéricas TÍTULO
        if hasattr(self.estadisticas, 'titulo_numericas') and self.estadisticas['titulo_numericas']:
            print(f"� CARACTERÍSTICAS NUMÉRICAS EN TÍTULOS:")
            top_titulo_num = self.estadisticas['titulo_numericas'].most_common(5)
            for i, (caracteristica, count) in enumerate(top_titulo_num, 1):
                porcentaje = (count / self.estadisticas['propiedades_procesadas']) * 100
                caract_clean = caracteristica.replace('titulo_', '').replace('_', ' ').title()
                print(f"   {i:2d}. {caract_clean}: {count:,} ({porcentaje:.1f}%)")
            print("")
        
        print(f"=" * 80)
        
        # Retornar datos estructurados para CSV
        return {
            'desc_adjetivos': dict(self.estadisticas.get('desc_adjetivos', {})),
            'titulo_adjetivos': dict(self.estadisticas.get('titulo_adjetivos', {})),
            'desc_numericas': dict(self.estadisticas.get('desc_numericas', {})),
            'titulo_numericas': dict(self.estadisticas.get('titulo_numericas', {}))
        }


def main():
    """Función principal"""
    
    # Archivos de entrada y salida
    ARCHIVO_ENTRADA = "Consolidados/pretratadaCol_tex/Sep25/pretratadaCol_tex_Sep25_01.csv"
    ARCHIVO_SALIDA = "Consolidados/Bases Finales/Sep25/Base_final_Textos_Sep25_01.csv"
    ARCHIVO_REPORTE = "Consolidados/pretratadaCol_tex/Sep25/Marketing_Estadisticas_Completo_Sep25_01.csv"
    
    # Crear directorios si no existen
    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)
    
    try:
        # Inicializar analizador
        analizador = AnalizadorMarketingInmobiliario()
        
        # Verificar si existe archivo de entrada
        if not os.path.exists(ARCHIVO_ENTRADA):
            print(f"❌ No se encontró el archivo: {ARCHIVO_ENTRADA}")
            print(f"   Por favor ejecuta primero los scripts 1-7 para generar los datos necesarios")
            return
        
        # Procesar archivo completo
        df_marketing = analizador.procesar_archivo_completo(ARCHIVO_ENTRADA)
        
        if df_marketing is not None:
            # Guardar resultado
            df_marketing.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8-sig')
            print(f"💾 Archivo guardado: {ARCHIVO_SALIDA}")
            
            # Generar y guardar estadísticas
            estadisticas = analizador.generar_reporte_estadisticas()
            
            # Crear DataFrame de estadísticas para CSV
            reporte_data = []
            
            # Agregar estadísticas de descripción
            for categoria in ['desc_adjetivos', 'desc_numericas']:
                if categoria in estadisticas:
                    for variable, count in estadisticas[categoria].items():
                        porcentaje = (count / analizador.estadisticas['propiedades_procesadas']) * 100
                        reporte_data.append({
                            'fuente': 'descripcion',
                            'categoria': categoria.replace('desc_', ''),
                            'variable': variable.replace('desc_', ''),
                            'cantidad': count,
                            'porcentaje': round(porcentaje, 2),
                            'descripcion': f'Propiedades con {variable.replace("desc_", "").replace("_", " ")} en descripción'
                        })
            
            # Agregar estadísticas de título
            for categoria in ['titulo_adjetivos', 'titulo_numericas']:
                if categoria in estadisticas:
                    for variable, count in estadisticas[categoria].items():
                        porcentaje = (count / analizador.estadisticas['propiedades_procesadas']) * 100
                        reporte_data.append({
                            'fuente': 'titulo',
                            'categoria': categoria.replace('titulo_', ''),
                            'variable': variable.replace('titulo_', ''),
                            'cantidad': count,
                            'porcentaje': round(porcentaje, 2),
                            'descripcion': f'Propiedades con {variable.replace("titulo_", "").replace("_", " ")} en título'
                        })
            
            df_reporte = pd.DataFrame(reporte_data)
            df_reporte = df_reporte.sort_values(['fuente', 'categoria', 'cantidad'], ascending=[True, True, False])
            df_reporte.to_csv(ARCHIVO_REPORTE, index=False, encoding='utf-8-sig')
            
            print(f"📊 Reporte de estadísticas guardado: {ARCHIVO_REPORTE}")
            print(f"\n🎉 ¡Análisis de marketing completado exitosamente!")
            
            # Mostrar resumen final
            print(f"\n📋 RESUMEN FINAL:")
            print(f"   • Archivo principal: {ARCHIVO_SALIDA}")
            print(f"   • Propiedades: {len(df_marketing):,}")
            print(f"   • Variables originales: {len([col for col in df_marketing.columns if not col.startswith(('desc_', 'titulo_'))])} variables")
            print(f"   • Variables de descripción: {len([col for col in df_marketing.columns if col.startswith('desc_')])} variables")
            print(f"   • Variables de título: {len([col for col in df_marketing.columns if col.startswith('titulo_')])} variables")
            print(f"   • Total columnas: {len(df_marketing.columns)} (dataset completo)")
            print(f"   • Reporte estadísticas: {ARCHIVO_REPORTE}")
            print(f"\n🎯 ANÁLISIS DISPONIBLES:")
            print(f"   • Correlación precio-marketing")
            print(f"   • Segmentación por ciudad (Gdl/Zap)")
            print(f"   • Análisis por tipo de propiedad")
            print(f"   • Clustering de estrategias")
            print(f"   • Análisis temporal por fecha")
            print(f"   • Análisis geográfico (lat/lon)")
            print(f"   • Comparación por anunciante")
            
        else:
            print(f"❌ No se pudo procesar el archivo")
    
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        raise


if __name__ == "__main__":
    main()
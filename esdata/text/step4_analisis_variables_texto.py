"""Paso 4: Analisis Variables Texto
Genera 4a (titulo+descripcion) y 4b (caracteristicas/amenidades/servicios/exteriores) a partir de 3b.
"""
from __future__ import annotations
import os, re, unicodedata
import pandas as pd
from esdata.utils.io import read_csv, write_csv
from esdata.utils.paths import path_consolidados
from esdata.utils.logging_setup import get_logger

log = get_logger('step4')

BASIC_REGEXES = {
    'recamaras_txt': re.compile(r'(\d+)\s*rec'),
    'banos_txt': re.compile(r'(\d+)\s*bañ'),
}

META_COLS = ["id","PaginaWeb","Ciudad","Fecha_Scrap","tipo_propiedad","area_m2","precio","mantenimiento","Colonia"]
TEXT_BLOCK_1 = ['titulo','descripcion']
TEXT_BLOCK_2 = ['Caracteristicas_generales','Servicios','Amenidades','Exteriores']

# Lista canónica de 98 variables
CANONICAL_FEATURES = [
 'balcon','terraza','roof_garden','jardin','patio','bodega','sotano','despensa','closet','estudio','vestidor','cuarto_tv',
 'biblioteca','bar','desayunador','cuarto_servicio','cuarto_lavado','doble_altura','loft','penthouse','duplex','alberca',
 'jacuzzi','sauna','vapor','gimnasio','spa','home_theater','cava','cancha_tenis','cancha_squash','cancha_padel','cancha_futbol',
 'cancha_basquet','area_juegos','ping_pong','billar','jardin_privado','asador','area_parrillas','fogata','kiosco','seguridad',
 'caseta','portero','circuito_cerrado','alarma','intercomunicador','elevador','montacargas','escaleras_electricas','aire_acondicionado',
 'calefaccion','chimenea','ventilacion','cocina_integral','linea_blanca','lavavajillas','horno','microondas','refrigerador','estufa',
 'campana','internet','cable','telefono','gas_natural','cisterna','planta_emergencia','ups','salon_eventos','salon_usos_multiples',
 'salon_fiestas','co_working','business_center','sala_juntas','auditorio','vista_panoramica','frente_al_mar','pet_friendly','acceso_discapacitados',
 'smart_home','paneles_solares','amueblado','semi_amueblado','sin_muebles','obra_nueva','remodelado','obra_gris','a_estrenar','esquina',
 'planta_baja','ultimo_piso','frente','servicio_limpieza','mantenimiento','administracion','conserje'
]
CANONICAL_SET = set(CANONICAL_FEATURES)

# === Listas marketing===
DESC_TERMS = [
 'moderno','contemporaneo','nuevo','espectacular','increible','hermoso','elegante','lujoso','exclusivo','premium','impecable','comodo',
 'confortable','acogedor','funcional','practico','espacioso','unico','especial','extraordinario','excepcional','ideal','perfecto','centrico',
 'privilegiado','estrategico','conveniente','encantador','sorprendente','fascinante','maravilloso','remodelado','restaurado','bien_conservado',
 'iluminado','luminoso','soleado','minimalista','vanguardista','tradicional','clasico','seguridad_24h','circuito_cerrado','caseta_vigilancia',
 'acceso_controlado','gimnasio','alberca','cancha_tenis','cancha_padel','area_juegos','salon_eventos','salon_fiestas','salon_usos_multiples',
 'roof_garden','terraza_comun','elevador','aire_acondicionado','calefaccion','calentador_agua','cocina_integral','cocina_equipada','linea_blanca',
 'electrodomesticos','internet_incluido','gas_incluido','agua_incluida','luz_incluida','mantenimiento_incluido','mascotas_permitidas','amueblado',
 'semi_amueblado','vista_panoramica','frente_al_mar'
]
TIT_TERMS = [t for t in DESC_TERMS]  # misma lista para titulo_* (según documento)

# Precompilar patrones de búsqueda (acentos ignorados, underscores -> espacios flexibles)
_ACCENT_MAP = str.maketrans('áéíóúÁÉÍÓÚñÑ','aeiouAEIOUnN')

def _norm_text_base(s: str) -> str:
    return re.sub(r'\s+',' ', s.lower().translate(_ACCENT_MAP))

def _term_to_regex(term: str) -> re.Pattern:
    base = term.replace('_',' ').lower()
    # casos especiales
    if term == 'seguridad_24h':
        base = 'seguridad 24h'
    pat = re.escape(base)
    # permitir uno o más espacios donde había espacios
    pat = pat.replace('\\ ', r'\s+')
    return re.compile(r'(?<![a-z0-9])' + pat + r'(?![a-z0-9])')

DESC_PATTERNS = {term: _term_to_regex(term) for term in DESC_TERMS}
TIT_PATTERNS = {term: _term_to_regex(term) for term in TIT_TERMS}

# Normalización básica
_def_space = re.compile(r'\s+')
_sep_split = re.compile(r'[;,\/\n]|\|')
_qty_pattern = re.compile(r'^([^:]+?)\s*[:=-]\s*(\d+(?:[.,]\d+)?)$')
_number_suffix = re.compile(r'(.+?)\s+(\d+)$')
_clean_symbols = re.compile(r'[^a-z0-9ñ_#\s]')

# Mapa de normalización (sin acentos -> canónico)
NORMALIZATION_MAP = {**{c:c for c in CANONICAL_FEATURES},
 'balcones':'balcon','balcon(es)':'balcon',
 'roof garden':'roof_garden','roof-garden':'roof_garden','roofgarden':'roof_garden',
 'garden':'jardin','jardin comun':'jardin','jardin comunal':'jardin',
 'cuarto de servicio':'cuarto_servicio','hab servicio':'cuarto_servicio','habitacion de servicio':'cuarto_servicio','servicio':'cuarto_servicio',
 'cuarto de lavado':'cuarto_lavado','area de lavado':'cuarto_lavado','lavanderia':'cuarto_lavado','area de lavanderia':'cuarto_lavado',
 'closets':'closet','clóset':'closet','walk in closet':'vestidor','walk-in closet':'vestidor','walkin closet':'vestidor','closet vestidor':'vestidor',
 'sala tv':'cuarto_tv','sala de tv':'cuarto_tv','family room':'cuarto_tv',
 'home theater':'home_theater','home-theater':'home_theater','cine':'home_theater',
 'cancha de tenis':'cancha_tenis','cancha tenis':'cancha_tenis',
 'cancha paddle':'cancha_padel','cancha de paddle':'cancha_padel','cancha padel':'cancha_padel',
 'cancha futbol':'cancha_futbol','cancha de futbol':'cancha_futbol','futbol rapido':'cancha_futbol',
 'cancha basquet':'cancha_basquet','cancha de basquet':'cancha_basquet','basquetbol':'cancha_basquet',
 'area de juegos infantiles':'area_juegos','juegos infantiles':'area_juegos','area juegos':'area_juegos',
 'ping pong':'ping_pong','mesa de ping pong':'ping_pong','mesa de ping-pong':'ping_pong',
 'mesa de billar':'billar','billar americano':'billar',
 'jardin privado':'jardin_privado','patio jardin':'jardin_privado',
 'parrilla':'asador','parrillero':'asador','area de parrillas':'area_parrillas','area parrillas':'area_parrillas',
 'fogatero':'fogata','fire pit':'fogata',
 'cctv':'circuito_cerrado','circuito cerrado':'circuito_cerrado','camaras':'circuito_cerrado','camaras de seguridad':'circuito_cerrado',
 'aire acondicionado':'aire_acondicionado','a/a':'aire_acondicionado',
 'linea blanca':'linea_blanca','linea-blanca':'linea_blanca',
 'lava vajillas':'lavavajillas','lava-vajillas':'lavavajillas',
 'micro ondas':'microondas','micro-ondas':'microondas',
 'refrig':'refrigerador','frigo':'refrigerador','refri':'refrigerador',
 'gas natural':'gas_natural','gas naturalizado':'gas_natural',
 'planta de emergencia':'planta_emergencia','plantas de emergencia':'planta_emergencia',
 'salon de eventos':'salon_eventos','salon eventos':'salon_eventos',
 'salon de usos multiples':'salon_usos_multiples','salon usos multiples':'salon_usos_multiples','sum':'salon_usos_multiples',
 'salon de fiestas':'salon_fiestas','salon fiestas':'salon_fiestas','salon social':'salon_fiestas',
 'coworking':'co_working','co working':'co_working','co-working':'co_working',
 'business center':'business_center','centro de negocios':'business_center',
 'sala de juntas':'sala_juntas','sala juntas':'sala_juntas',
 'vista panoramica':'vista_panoramica','vista  panoramica':'vista_panoramica',
 'frente al mar':'frente_al_mar','vista al mar':'frente_al_mar',
 'pet friendly':'pet_friendly','mascotas':'pet_friendly','acepta mascotas':'pet_friendly',
 'acceso discapacitados':'acceso_discapacitados','rampa discapacitados':'acceso_discapacitados',
 'smart home':'smart_home','domotica':'smart_home',
 'paneles solares':'paneles_solares','panel solar':'paneles_solares',
 'semi amueblado':'semi_amueblado','semi-amueblado':'semi_amueblado','semiamueblado':'semi_amueblado',
 'sin muebles':'sin_muebles','no amueblado':'sin_muebles','no-amueblado':'sin_muebles',
 'obra nueva':'obra_nueva','nueva':'obra_nueva','nuevo':'obra_nueva',
 'a estrenar':'a_estrenar','estrenar':'a_estrenar','brand new':'a_estrenar',
 'planta baja':'planta_baja','pb':'planta_baja',
 'ultimo piso':'ultimo_piso','ultimo nivel':'ultimo_piso','piso superior':'ultimo_piso','pent house':'penthouse',
 'servicio limpieza':'servicio_limpieza','limpieza':'servicio_limpieza',
 'administración':'administracion','conserjería':'conserje','conserjeria':'conserje',
 'doble altura':'doble_altura','cuarto de tv':'cuarto_tv','tv room':'cuarto_tv'
}

ALIAS_VALUE = 1
META_DEFAULTS = {c: None for c in META_COLS}


def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _normalize_token(tok: str) -> str:
    t = tok.lower().strip()
    t = _strip_accents(t)
    t = t.replace('-', ' ')
    t = _def_space.sub(' ', t)
    t = _clean_symbols.sub('', t)
    t = t.strip()
    if not t:
        return ''
    if t in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[t]
    t = t.replace(' ', '_')
    if t in CANONICAL_SET:
        return t
    return ''


def _split_items(text: str):
    if not text or str(text).strip().lower() in ('desconocido','nan'):
        return []
    parts = _sep_split.split(str(text))
    out=[]
    for p in parts:
        p=p.strip()
        if p:
            out.append(p)
    return out


def _parse_items(cells: dict[str,str]):
    accum={}
    for raw in cells.values():
        for item in _split_items(raw):
            m = _qty_pattern.match(item)
            if m:
                label = _normalize_token(m.group(1))
                if label:
                    try: qty=float(m.group(2).replace(',','.'))
                    except: qty=ALIAS_VALUE
                    accum[label]=accum.get(label,0)+qty
                continue
            m2 = _number_suffix.match(item)
            if m2:
                label = _normalize_token(m2.group(1))
                if label:
                    qty=float(m2.group(2))
                    accum[label]=accum.get(label,0)+qty
                continue
            label=_normalize_token(item)
            if label:
                accum[label]=max(accum.get(label,0),ALIAS_VALUE)
    return accum


def extract_block_titulo_desc(df, block_cols, outfile):
    rows=[]
    for _,r in df.iterrows():
        titulo_txt = str(r.get('titulo','') or '')
        desc_txt = str(r.get('descripcion','') or '')
        concat = (titulo_txt + ' ' + desc_txt).lower()
        norm_titulo = _norm_text_base(titulo_txt)
        norm_desc = _norm_text_base(desc_txt)
        data={c:r.get(c) for c in META_COLS if c in df.columns}
        # Extraer numéricos básicos desde el texto combinado
        m1=BASIC_REGEXES['recamaras_txt'].search(concat)
        if m1: data['recamaras_texto']=int(m1.group(1))
        m2=BASIC_REGEXES['banos_txt'].search(concat)
        if m2: data['banos_texto']=int(m2.group(1))
        # Indicadores descripcion
        for term, pat in DESC_PATTERNS.items():
            col = f'desc_{term}'
            data[col] = 1 if pat.search(norm_desc) else 0
        # Indicadores titulo
        for term, pat in TIT_PATTERNS.items():
            col = f'titulo_{term}'
            data[col] = 1 if pat.search(norm_titulo) else 0
        rows.append(data)
    out=pd.DataFrame(rows)
    write_csv(out, outfile)


def extract_block_amenidades(df, block_cols, outfile):
    rows=[]
    for _,r in df.iterrows():
        parsed=_parse_items({c:r.get(c,'') for c in block_cols})
        base={c:r.get(c) for c in META_COLS if c in df.columns}
        row={**META_DEFAULTS, **base}
        for lab in CANONICAL_FEATURES:
            val=parsed.get(lab,0)
            if isinstance(val,float) and val.is_integer(): val=int(val)
            row[lab]=val
        rows.append(row)
    out=pd.DataFrame(rows)
    write_csv(out, outfile)
    log.info(f'4b generado con {len(out)} filas y {len(CANONICAL_FEATURES)} variables amenidades canónicas')


def run(periodo):
    base_dir = os.path.join(path_consolidados(), periodo)
    inp = os.path.join(base_dir, f'3b.Consolidado_Tex_{periodo}.csv')
    if not os.path.exists(inp):
        raise FileNotFoundError(inp)
    df=read_csv(inp)
    extract_block_titulo_desc(df, TEXT_BLOCK_1, os.path.join(base_dir, f'4a.Tex_Titulo_Descripcion_{periodo}.csv'))
    extract_block_amenidades(df, TEXT_BLOCK_2, os.path.join(base_dir, f'4b.Tex_Car_Ame_Ser_Ext_{periodo}.csv'))
    log.info('Paso 4 completado')


if __name__=='__main__':
    from datetime import datetime
    per=datetime.now().strftime('%b%y')
    run(per)

"""Módulo de análisis de texto para descripciones inmobiliarias.

Funciones:
- load_marketing(periodo): intenta cargar 0.Final_MKT_<periodo>.csv
- basic_clean(text): limpieza ligera
- word_frequencies(df, text_col, top_n): frecuencias simples
- tfidf_top_terms(df, text_col, group_col, top_k): términos diferenciadores por grupo
- build_wordcloud(freq_dict): devuelve objeto WordCloud (si lib disponible) y bytes PNG
"""
from __future__ import annotations
import os, io, re
import pandas as pd
from typing import Dict, Tuple, Optional
from esdata.utils.paths import path_base
from esdata.utils.io import read_csv

STOPWORDS = set([
    'de','la','el','en','y','a','con','para','por','los','las','un','una','del','se','al','que','su','sus','es','esta','este','o','u','tu','mis','muy','ya','si','no'
])

_def_token_pattern = re.compile(r"[A-Za-zÁÉÍÓÚÜáéíóúñÑ]{3,}")

def load_marketing(periodo: str) -> pd.DataFrame:
    try:
        base = path_base('N5_Resultados','Nivel_1','CSV')
    except Exception:
        return pd.DataFrame()
    fname = os.path.join(base, f'0.Final_MKT_{periodo}.csv')
    if os.path.exists(fname):
        try:
            return read_csv(fname)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def basic_clean(text: str) -> str:
    if not isinstance(text,str):
        return ''
    t = text.lower()
    t = re.sub(r"\s+"," ", t)
    return t.strip()

def tokenize(text: str):
    tokens = _def_token_pattern.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS]

def word_frequencies(df: pd.DataFrame, text_col: str='descripcion', top_n: int=100) -> pd.DataFrame:
    if text_col not in df.columns:
        return pd.DataFrame()
    from collections import Counter
    cnt = Counter()
    for t in df[text_col].dropna():
        for tok in tokenize(t):
            cnt[tok]+=1
    if not cnt:
        return pd.DataFrame()
    most = cnt.most_common(top_n)
    return pd.DataFrame(most, columns=['token','frecuencia'])

def tfidf_top_terms(df: pd.DataFrame, text_col: str='descripcion', group_col: str='segmento', top_k: int=15) -> pd.DataFrame:
    if text_col not in df.columns or group_col not in df.columns:
        return pd.DataFrame()
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        return pd.DataFrame()
    sub = df.dropna(subset=[text_col, group_col]).copy()
    if sub.empty:
        return pd.DataFrame()
    docs = sub[text_col].astype(str).tolist()
    groups = sub[group_col].astype(str).tolist()
    vectorizer = TfidfVectorizer(token_pattern=r"[A-Za-zÁÉÍÓÚÜáéíóúñÑ]{3,}", lowercase=True, stop_words=list(STOPWORDS))
    try:
        X = vectorizer.fit_transform(docs)
    except ValueError:
        return pd.DataFrame()
    terms = vectorizer.get_feature_names_out()
    import numpy as np
    import itertools
    rows=[]
    # Agrupar índices por grupo
    from collections import defaultdict
    idx_by_group = defaultdict(list)
    for i,g in enumerate(groups):
        idx_by_group[g].append(i)
    import numpy as _np
    for g, idxs in idx_by_group.items():
        if not idxs:
            continue
        from scipy.sparse import vstack
        subm = vstack([X.getrow(i) for i in idxs])
        # Media tfidf por término dentro del grupo
        mean_vec = subm.mean(axis=0)
        import numpy as _npx
        mean_tfidf = _npx.asarray(mean_vec).ravel()
        top_idx = mean_tfidf.argsort()[::-1][:top_k]
        for ti in top_idx:
            rows.append({'grupo':g,'token':terms[ti],'tfidf':float(mean_tfidf[ti])})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(['grupo','tfidf'], ascending=[True, False])

def build_wordcloud(freq_df: pd.DataFrame, token_col: str='token', freq_col: str='frecuencia') -> Tuple[Optional[object], Optional[bytes]]:
    if freq_df is None or freq_df.empty:
        return None, None
    try:
        from wordcloud import WordCloud
    except ImportError:
        return None, None
    freq_dict = dict(zip(freq_df[token_col], freq_df[freq_col]))
    wc = WordCloud(width=800, height=400, background_color='white')
    img = wc.generate_from_frequencies(freq_dict).to_image()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return wc, buf.getvalue()

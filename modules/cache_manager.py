"""
Cache Manager - Gerencia todas as operações de cache do Streamlit
Extraído de app.py para melhor organização e manutenção.
"""

import streamlit as st
import csv
from io import StringIO
import pandas as pd
from typing import Optional, Union, List, Tuple


# ════════════════════════════════════════════════════════════
# LAZY LOADING — Abas 6-9 (Gráficos, Filtros, Semântica, Frequência)
# ════════════════════════════════════════════════════════════

def initialize_tab_state():
    """Inicializa estado de carregamento das abas"""
    tabs = ['tab6_loaded', 'tab7_loaded', 'tab8_loaded', 'tab9_loaded']
    for tab in tabs:
        if tab not in st.session_state:
            st.session_state[tab] = False


def mark_tab_loaded(tab_number: int):
    """Marca uma aba como carregada"""
    st.session_state[f'tab{tab_number}_loaded'] = True


def is_tab_loaded(tab_number: int) -> bool:
    """Verifica se uma aba foi carregada"""
    return st.session_state.get(f'tab{tab_number}_loaded', False)


def show_lazy_loading_placeholder(tab_number: int):
    """Mostra placeholder durante carregamento lazy de aba"""
    st.write(f"⏳ Carregando aba {tab_number}...")
    st.info("Clique novamente para carregar ou aguarde...")


# ════════════════════════════════════════════════════════════
# SEARCH CACHE — Histórico e resultados frequentes
# ════════════════════════════════════════════════════════════

def initialize_search_cache():
    """Inicializa cache de busca e histórico"""
    if 'search_cache' not in st.session_state:
        st.session_state.search_cache = {}
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []


def get_cached_search(query_key: str) -> Optional[Union[dict, List[Tuple[str, float]]]]:
    """Recupera resultado de busca do cache (dict para busca avançada, list para semântica)"""
    return st.session_state.search_cache.get(query_key)


def cache_search_result(query_key: str, results):
    """Armazena resultado de busca em cache (suporta dict e list)"""
    st.session_state.search_cache[query_key] = results

    # Adicionar ao histórico
    if query_key not in [h.get('query') for h in st.session_state.search_history]:
        # Calcular count: dict['ids'] para busca avançada, len(list) para semântica
        if isinstance(results, dict):
            count = len(results.get('ids', []))
        else:  # list of tuples from semantic search
            count = len(results)

        st.session_state.search_history.append({
            'query': query_key,
            'count': count,
            'timestamp': st.session_state.get('current_time')
        })
        # Manter apenas últimas 20 buscas
        if len(st.session_state.search_history) > 20:
            st.session_state.search_history = st.session_state.search_history[-20:]


def build_df_fast(card_ids: tuple, _todas_cartas: dict) -> pd.DataFrame:
    """
    Constrói DataFrame rápido a partir de IDs (sem cache por tamanho de dados).
    Usada quando cache por ID não é viável.
    """
    cartas = {k: _todas_cartas[k] for k in card_ids if k in _todas_cartas}
    df = pd.DataFrame(cartas.values())
    df.replace("nan", None, inplace=True)
    df.replace("None", None, inplace=True)
    df.fillna("Não informado", inplace=True)
    return df


@st.cache_data
def build_df_cached(db_name: str, card_ids: tuple, all_cartas: dict) -> pd.DataFrame:
    """
    Constrói DataFrame a partir das cartas filtradas, com cache por db e conjunto de IDs.

    Args:
        db_name: Nome do banco de dados
        card_ids: Tupla com IDs das cartas
        all_cartas: Dicionário com todas as cartas

    Returns:
        DataFrame com os dados das cartas
    """
    cartas = {k: all_cartas[k] for k in card_ids if k in all_cartas}
    df = pd.DataFrame(cartas.values())
    df.replace("nan", None, inplace=True)
    df.replace("None", None, inplace=True)
    df.fillna("Não informado", inplace=True)
    return df


@st.cache_data(ttl=3600)
def compute_chart_data_cached(db_name: str, card_ids: tuple, _todas_cartas_size: int) -> dict:
    """
    Pré-computa todos os value_counts para geração de gráficos. Usa tamanho como proxy de cache key.
    Cache compartilhado entre Tabs 6 e 8. TTL de 1 hora para evitar desincronização de bases.

    Args:
        db_name: Nome do banco de dados
        card_ids: Tupla com IDs das cartas
        _todas_cartas_size: Tamanho do dicionário de cartas (usado como cache key)

    Returns:
        Dicionário com dados pré-computados para gráficos
    """
    df = build_df_fast(card_ids, st.session_state.data_manager.get_todas_cartas())
    cols = set(df.columns)
    result: dict = {'_columns': list(cols)}

    campos_analise = [
        'sexo', 'estado_civil', 'faixa_etaria', 'morador', 'instrucao',
        'faixa_renda', 'uf', 'municipio', 'atividade', 'origem', 'catalogo', 'indexacao'
    ]

    for campo in campos_analise:
        if campo in cols:
            vc = df[campo].value_counts()
            result[campo] = {'names': vc.index.tolist(), 'values': vc.values.tolist()}

    return result


@st.cache_data
def build_semantic_csv_cached(card_ids: tuple, scores: tuple, db_name: str, _all_cartas: dict, _series: dict = None) -> bytes:
    """
    Gera CSV dos resultados da busca semântica com suporte a séries temáticas.
    Cache evita reconstrução a cada render.

    Args:
        card_ids: Tupla com IDs das cartas ordenadas por relevância
        scores: Tupla com scores de similaridade
        db_name: Nome do banco de dados
        _all_cartas: Dicionário com todas as cartas
        _series: Dicionário opcional com séries temáticas

    Returns:
        Bytes contendo o CSV formatado com delimiter ';' e BOM UTF-8
    """
    carta_series_idx: dict = {}
    if _series:
        for ns, si in _series.items():
            for cid in si['cartas']:
                carta_series_idx.setdefault(cid, []).append(ns)
        for cid in carta_series_idx:
            carta_series_idx[cid] = sorted(carta_series_idx[cid])

    buf = StringIO()
    writer = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow(['SERIES_TEMATICAS', 'RANK', 'LINHA_BASE_SAIC', 'NOME', 'DESTINATARIO',
                     'CATALOGO', 'INDEXACAO', 'ORIGEM', 'DATA',
                     'FORMUL', 'DV', 'DATA2', 'MUNICIPIO', 'UF', 'CEP', 'SEXO', 'MORADOR', 'INSTRUCAO',
                     'ESTADO CIVIL', 'FAIXA ETÁRIA', 'FAIXA RENDA', 'ATIVIDADE', 'SCORE', 'TEXTO'])
    scores_dict = dict(zip(card_ids, scores))
    for rank, carta_id in enumerate(card_ids, 1):
        carta = _all_cartas.get(carta_id)
        if carta:
            series_str = ' | '.join(carta_series_idx.get(carta_id, []))
            writer.writerow([
                series_str, rank, carta_id,
                carta.get('nome', ''), carta.get('destinatario', ''),
                carta.get('catalogo', ''), carta.get('indexacao', ''),
                carta.get('origem', ''), carta.get('data', ''),
                carta.get('formul', ''), carta.get('dv', ''),
                carta.get('data2', ''), carta.get('municipio', ''),
                carta.get('uf', ''), carta.get('cep', ''),
                carta.get('sexo', ''), carta.get('morador', ''),
                carta.get('instrucao', ''), carta.get('estado_civil', ''),
                carta.get('faixa_etaria', ''), carta.get('faixa_renda', ''),
                carta.get('atividade', ''),
                f"{scores_dict.get(carta_id, 0):.4f}",
                (carta.get('texto', '') or '').replace('\n', ' ')
            ])
    return buf.getvalue().encode('utf-8-sig')

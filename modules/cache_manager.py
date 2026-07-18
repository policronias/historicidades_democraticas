"""
Cache Manager - Gerencia todas as operações de cache do Streamlit
Extraído de app.py para melhor organização e manutenção.
"""

import streamlit as st
import csv
from io import StringIO
import pandas as pd


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

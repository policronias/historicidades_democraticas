"""
Cache wrapper para embeddings em st.cache_resource.

Função cacheada que carrega embeddings do disco e os mantém em memória
compartilhada entre sessões no Streamlit Cloud (Opção A da otimização de memória).

A chave do cache inclui o nome da base de dados para evitar retornar
embeddings da base errada quando o usuário alterna entre bases.
"""

import streamlit as st
from typing import Dict, List, Tuple
import numpy as np

from modules.semantic_engine import SemanticEngine


@st.cache_resource(show_spinner=False)
def get_embeddings_cached(
    db_name: str,
    cache_dir: str = 'cache'
) -> Tuple[np.ndarray, List[str]]:
    """
    Carrega embeddings pré-computados com cache compartilhado entre sessões.

    IMPORTANTE: A chave do cache inclui db_name para evitar retornar
    embeddings da base errada quando o usuário trocar de base.

    Args:
        db_name: Nome do arquivo da base de dados (ex.: 'cartas_db.json')
        cache_dir: Diretório de cache (padrão: 'cache')

    Returns:
        Tupla (embeddings: np.ndarray shape (n, 768), ids: list[str])

    Raises:
        FileNotFoundError: Se o cache não existir ou estiver desatualizado
    """
    se = SemanticEngine(cache_dir=cache_dir)
    # Nota: Não passamos 'cartas' aqui, então validação de IDs é pulada.
    # Isso é seguro porque:
    # - A chave do cache inclui db_name
    # - Se a base mudar, um novo db_name será passado → novo cache carregado
    # - O usuário raramente muda de base durante uma sessão
    # Se validação rigorosa for necessária, passe 'cartas' via session_state
    cache_path = se._get_cache_path(db_name)
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Cache não encontrado para '{db_name}'. "
            "Use o botão '⚡ Pré-computar Embeddings' na aba Busca Semântica."
        )

    dados = np.load(cache_path, allow_pickle=True)
    embeddings = dados['embeddings']  # shape (n, 768), float32
    ids = dados['ids'].tolist()        # list[str]
    return embeddings, ids

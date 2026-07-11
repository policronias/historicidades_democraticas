"""
Config Manager - Gerencia configurações da aplicação
Centraliza constantes, caminhos e parâmetros de configuração.
"""

import os
from pathlib import Path
from typing import Dict, List

# ============================================================================
# PATHS E CONFIGURAÇÕES DE DADOS
# ============================================================================

# Diretório base do projeto
PROJECT_DIR = Path(__file__).parent.parent

# Caminhos de dados
DATA_DIR = PROJECT_DIR / 'dados'
DATABASE_PATH = PROJECT_DIR / 'cartas_db.json'
EMBEDDINGS_PATH = PROJECT_DIR / 'cache' / 'embeddings_cartas_db.npz'
ANNOTATIONS_PATH = PROJECT_DIR / 'anotacoes.json'
SERIES_PATH = PROJECT_DIR / 'series_tematicas.json'

# Caminhos de bases auxiliares
BASES_DIR = PROJECT_DIR / 'bases'
DATASETS_DIR = BASES_DIR / 'Datasets'
EXPORTS_DIR = PROJECT_DIR / 'exports'

# ============================================================================
# CONFIGURAÇÕES DE APLICAÇÃO
# ============================================================================

# Streamlit page config
PAGE_CONFIG = {
    'page_title': 'Historicidades Democráticas',
    'page_icon': '📚',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
}

# ============================================================================
# CAMPOS DE ANÁLISE
# ============================================================================

# Campos de metadados disponíveis nas cartas
METADATA_FIELDS = [
    'linha', 'nome', 'destinatario', 'catalogo', 'indexacao',
    'origem', 'data', 'data2', 'formul', 'dv', 'municipio', 'uf', 'cep',
    'sexo', 'morador', 'instrucao', 'estado_civil', 'faixa_etaria',
    'faixa_renda', 'atividade', 'anotacoes', 'series'
]

# Campos disponíveis para análise estatística
ANALYSIS_FIELDS = [
    'sexo', 'estado_civil', 'faixa_etaria', 'morador', 'instrucao',
    'faixa_renda', 'uf', 'municipio', 'atividade', 'origem', 'catalogo', 'indexacao'
]

# ============================================================================
# CONFIGURAÇÕES DE BUSCA E ANÁLISE
# ============================================================================

# Embeddings
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
EMBEDDING_BATCH_SIZE = 32
EMBEDDING_DEVICE = 'cpu'  # Mude para 'cuda' se tiver GPU

# Busca semântica
SEMANTIC_SEARCH_TOP_K = 100
SEMANTIC_SEARCH_THRESHOLD = 0.0  # Sem threshold mínimo

# Paginação
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50

# ============================================================================
# CONFIGURAÇÕES DE UI
# ============================================================================

# Temas e estilos
COLORS = {
    'primary': '#1e3a8a',
    'secondary': '#3b82f6',
    'accent': '#fbbf24',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#0ea5e9',
    'text_primary': '#1f2937',
    'text_secondary': '#6b7280',
    'bg_light': '#f9fafb',
    'border': '#e5e7eb',
}

# Mensagens padrão
MESSAGES = {
    'loading_database': '⏳ Carregando banco de dados...',
    'loading_embeddings': '⏳ Carregando embeddings...',
    'searching': '🔍 Realizando busca semântica...',
    'exporting': '📥 Gerando exportação...',
    'no_results': '❌ Nenhum resultado encontrado.',
    'success': '✅ Operação realizada com sucesso!',
    'error': '⚠️ Ocorreu um erro. Por favor, tente novamente.',
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ensure_paths_exist():
    """
    Cria os diretórios necessários se não existirem.
    Deve ser chamado na inicialização da aplicação.
    """
    dirs_to_create = [DATA_DIR, BASES_DIR, DATASETS_DIR, EXPORTS_DIR, PROJECT_DIR / 'cache']
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_path(path_key: str) -> Path:
    """
    Retorna o caminho para um recurso específico.
    
    Args:
        path_key: Chave do caminho ('database', 'embeddings', 'annotations', etc.)
    
    Returns:
        Objeto Path do caminho solicitado
    """
    paths = {
        'database': DATABASE_PATH,
        'embeddings': EMBEDDINGS_PATH,
        'annotations': ANNOTATIONS_PATH,
        'series': SERIES_PATH,
        'bases': BASES_DIR,
        'exports': EXPORTS_DIR,
        'data': DATA_DIR,
    }
    return paths.get(path_key, None)


def get_field_groups() -> Dict[str, List[str]]:
    """
    Retorna campos agrupados por categoria para apresentação na UI.
    
    Returns:
        Dicionário com grupos de campos
    """
    return {
        'Identificação': ['linha', 'nome', 'destinatario', 'data'],
        'Localização': ['municipio', 'uf', 'cep'],
        'Catalogação': ['catalogo', 'indexacao', 'origem'],
        'Características': ['sexo', 'faixa_etaria', 'instrucao', 'estado_civil'],
        'Sociodemografia': ['morador', 'faixa_renda', 'atividade'],
        'Metadados': ['formul', 'dv', 'data2', 'anotacoes', 'series'],
    }

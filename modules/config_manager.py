"""
Config Manager - Gerencia configurações da aplicação
Centraliza constantes, caminhos e parâmetros de configuração.
"""

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

# Paleta de destaque (highlight) de termos em texto — usada em Explorar e
# como default do SearchEngine. Tintas de papel Policronias, fixas
# (independentes do tema claro/escuro): cada <mark> recebe texto tinta
# (#1b1815) sobre estas cores claras, legível nos dois modos.
HIGHLIGHT_PALETTE = [
    '#e8c9a0',  # âmbar-papel
    '#e6b8a6',  # selo dessaturado claro
    '#c3ccb2',  # musgo claro
    '#d9cdb4',  # areia / linha
    '#cbb9c6',  # violeta acinzentado
]

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


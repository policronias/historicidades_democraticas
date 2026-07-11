"""Módulos da plataforma Historicidades Democráticas."""

# Módulos principais
from .data_manager import DataManager
from .search_engine import SearchEngine
from .annotation_manager import AnnotationManager
from .series_manager import SeriesManager
from .export_manager import ExportManager
from .semantic_engine import SemanticEngine
from .stemming_engine import StemmingEngine
from .frequency_analyzer import FrequencyAnalyzer

# Novos módulos de gerenciamento
from .cache_manager import (
    build_df_cached,
    compute_chart_data_cached,
    build_semantic_csv_cached,
)
from .ui_manager import (
    configure_page_style,
    show_academic_header,
    show_footer,
    get_color_scheme,
)
from .config_manager import (
    ensure_paths_exist,
    get_path,
    get_field_groups,
    PAGE_CONFIG,
    METADATA_FIELDS,
    ANALYSIS_FIELDS,
    COLORS,
    MESSAGES,
    PROJECT_DIR,
    DATABASE_PATH,
    EMBEDDINGS_PATH,
    EXPORTS_DIR,
)

__all__ = [
    # Módulos principais
    'DataManager',
    'SearchEngine',
    'AnnotationManager',
    'SeriesManager',
    'ExportManager',
    'SemanticEngine',
    'StemmingEngine',
    'FrequencyAnalyzer',
    # Cache functions
    'build_df_cached',
    'compute_chart_data_cached',
    'build_semantic_csv_cached',
    # UI functions
    'configure_page_style',
    'show_academic_header',
    'show_footer',
    'get_color_scheme',
    # Config
    'ensure_paths_exist',
    'get_path',
    'get_field_groups',
    'PAGE_CONFIG',
    'METADATA_FIELDS',
    'ANALYSIS_FIELDS',
    'COLORS',
    'MESSAGES',
    'PROJECT_DIR',
    'DATABASE_PATH',
    'EMBEDDINGS_PATH',
    'EXPORTS_DIR',
]

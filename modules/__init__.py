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
    build_df_fast,
    build_df_cached,
    compute_chart_data_cached,
    build_semantic_csv_cached,
    initialize_tab_state,
    mark_tab_loaded,
    is_tab_loaded,
    initialize_search_cache,
    get_cached_search,
    cache_search_result,
    get_search_engine_cache_key,
    get_cached_engine_search,
    cache_engine_search_result,
)
from .feedback_manager import FeedbackManager
from .search_suggestions import SearchSuggestions
from .ui_manager import (
    configure_page_style,
    render_letter_text,
    get_plotly_color_palette,
    get_plotly_sequential_scale,
    breadcrumb_nav,
    apply_plotly_theme,
    format_pie_labels,
)
from .config_manager import (
    PAGE_CONFIG,
    METADATA_FIELDS,
    ANALYSIS_FIELDS,
    HIGHLIGHT_PALETTE,
    MESSAGES,
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
    'build_df_fast',
    'build_df_cached',
    'compute_chart_data_cached',
    'build_semantic_csv_cached',
    'initialize_tab_state',
    'mark_tab_loaded',
    'is_tab_loaded',
    'initialize_search_cache',
    'get_cached_search',
    'cache_search_result',
    'get_search_engine_cache_key',
    'get_cached_engine_search',
    'cache_engine_search_result',
    # Feedback
    'FeedbackManager',
    'SearchSuggestions',
    # UI functions
    'configure_page_style',
    'render_letter_text',
    'get_plotly_color_palette',
    'get_plotly_sequential_scale',
    'breadcrumb_nav',
    'apply_plotly_theme',
    'format_pie_labels',
    # Config
    'PAGE_CONFIG',
    'METADATA_FIELDS',
    'ANALYSIS_FIELDS',
    'HIGHLIGHT_PALETTE',
    'MESSAGES',
]

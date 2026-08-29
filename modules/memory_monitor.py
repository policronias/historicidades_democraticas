"""
Monitor de memória para debug (ativável via query string debug=true).
Exibe consumo de memória do processo em tempo real no sidebar.
"""

import os
import sys
from typing import Optional


def get_memory_usage_mb() -> float:
    """Retorna consumo de memória do processo em MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback para resource (Unix only)
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            return None


def get_available_system_memory_mb() -> Optional[float]:
    """
    Retorna memória disponível no sistema (não apenas do processo) em MB.

    Usado para alertar antes de operações pesadas (carregar modelo RoBERTa
    ~420MB + embeddings ~200MB) que podem falhar com segmentation fault
    quando o sistema está com pouca memória livre — esse crash acontece em
    código nativo (torch/safetensors) e não pode ser capturado como exceção
    Python, então o único jeito de evitar é avisar antes.

    Returns:
        Memória disponível em MB, ou None se psutil não estiver disponível.
    """
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 * 1024)
    except ImportError:
        return None


def display_memory_monitor(debug_mode: bool = False) -> Optional[str]:
    """
    Exibe monitor de memória no sidebar se debug_mode=True.

    Args:
        debug_mode: Se True, mostra o monitor

    Returns:
        String formatada com memória ou None
    """
    if not debug_mode:
        return None

    import streamlit as st

    mem_mb = get_memory_usage_mb()
    if mem_mb is None:
        return None

    with st.sidebar:
        st.divider()
        st.markdown("### 🔍 Debug: Memória")
        st.metric("Processo (MB)", f"{mem_mb:.1f}")

    return f"{mem_mb:.1f}"

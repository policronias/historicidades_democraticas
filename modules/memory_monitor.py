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

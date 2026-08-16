"""
Feedback Manager - Gerencia feedback visual do usuário
Centraliza spinners, status, progress bars, notifications
"""

import streamlit as st
from contextlib import contextmanager
from typing import Generator


class FeedbackManager:
    """Gerencia feedback visual consistente na aplicação"""

    @staticmethod
    @contextmanager
    def operation_status(title: str, expanded: bool = False) -> Generator:
        """
        Contexto manager para operações com status visual melhorado.

        Uso:
            with FeedbackManager.operation_status("Gerando PDF..."):
                pdf_bytes = generate_pdf(...)

        Args:
            title: Título da operação
            expanded: Se expande automaticamente
        """
        with st.status(title, expanded=expanded) as status:
            try:
                yield status
                status.update(label=f"✅ {title.replace('...', '')} concluído!", state="complete")
            except Exception as e:
                status.update(label=f"❌ Erro em {title}", state="error")
                st.error(f"Erro: {str(e)}")
                raise

    @staticmethod
    @contextmanager
    def operation_progress(title: str, steps: int = 0) -> Generator:
        """
        Contexto manager com progress bar.

        Uso:
            with FeedbackManager.operation_progress("Processando cartas", steps=100) as (status, progress):
                for i in range(100):
                    process_item(i)
                    progress.progress((i+1)/100)

        Args:
            title: Título da operação
            steps: Número total de passos (0 = indeterminado)
        """
        placeholder = st.empty()
        progress_bar = st.progress(0)

        with placeholder.container():
            with st.status(title, expanded=False) as status:
                try:
                    yield status, progress_bar
                    status.update(label=f"✅ {title.split()[0]} concluído!", state="complete")
                    progress_bar.progress(100)
                except Exception as e:
                    status.update(label=f"❌ Erro", state="error")
                    st.error(f"Erro: {str(e)}")
                    raise

    @staticmethod
    def success(message: str, icon: str = "✅") -> None:
        """Mostra mensagem de sucesso"""
        st.success(f"{icon} {message}")

    @staticmethod
    def error(message: str, icon: str = "❌") -> None:
        """Mostra mensagem de erro"""
        st.error(f"{icon} {message}")

    @staticmethod
    def warning(message: str, icon: str = "⚠️") -> None:
        """Mostra mensagem de aviso"""
        st.warning(f"{icon} {message}")

    @staticmethod
    def info(message: str, icon: str = "ℹ️") -> None:
        """Mostra mensagem de informação"""
        st.info(f"{icon} {message}")

    @staticmethod
    def update_progress(progress_bar, current: int, total: int, label: str = "") -> None:
        """
        Atualiza progress bar com valor e label opcional

        Args:
            progress_bar: Objeto de progress bar do Streamlit
            current: Valor atual
            total: Valor total
            label: Label opcional para mostrar
        """
        value = min(max(current / total, 0), 1)
        progress_bar.progress(value, text=label or f"{current}/{total}")


def create_spinner(message: str):
    """Legacy support - usar FeedbackManager.operation_status() em vez disso"""
    return st.spinner(message)

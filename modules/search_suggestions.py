"""
Search Suggestions - Gerencia autocomplete e sugestões de termos
Extrai termos frequentes, mantém histórico, oferece sugestões inteligentes
"""

import streamlit as st
from collections import Counter
from typing import List, Dict, Set


class SearchSuggestions:
    """Gerencia sugestões de busca e termos frequentes"""

    def __init__(self):
        self.default_suggestions = [
            "brasil",
            "constituição",
            "senado",
            "deputado",
            "cidadão",
            "direito",
            "lei",
            "governo",
            "voto",
            "democracia",
        ]

    def initialize_suggestions(self):
        """Inicializa cache de sugestões no session state"""
        if "search_suggestions" not in st.session_state:
            st.session_state.search_suggestions = self.default_suggestions.copy()
        if "search_term_frequency" not in st.session_state:
            st.session_state.search_term_frequency = {}

    def extract_terms_from_history(self) -> List[str]:
        """Extrai termos do histórico de buscas"""
        terms = []
        if st.session_state.get("search_history"):
            for h in st.session_state.search_history:
                # Extrair termo da chave de busca (formato: "advanced_termo_tipo_escopo_case")
                query_key = h.get("query", "")
                if query_key.startswith("advanced_"):
                    parts = query_key.split("_")
                    if len(parts) > 1:
                        termo = parts[1]
                        if termo and len(termo) > 2:  # Ignorar termos muito curtos
                            terms.append(termo.lower())
                elif query_key.startswith("semantic_"):
                    parts = query_key.split("_")
                    if len(parts) > 1:
                        termo = parts[1]
                        if termo and len(termo) > 2:
                            terms.append(termo.lower())
        return terms

    def get_suggested_terms(self, max_suggestions: int = 15) -> List[str]:
        """
        Retorna lista de termos sugeridos (combinação de histórico + frequentes)

        Args:
            max_suggestions: Número máximo de sugestões a retornar

        Returns:
            Lista de termos sugeridos, ordenados por frequência
        """
        self.initialize_suggestions()

        # Extrair termos do histórico
        history_terms = self.extract_terms_from_history()

        # Contar frequência
        if history_terms:
            freq = Counter(history_terms)
            # Combinar com sugestões padrão
            all_terms = list(freq.keys()) + [
                t for t in self.default_suggestions if t not in freq
            ]
        else:
            all_terms = self.default_suggestions

        # Remover duplicatas mantendo ordem
        seen = set()
        unique_terms = []
        for term in all_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms[:max_suggestions]

    def update_frequency(self, termo: str):
        """Atualiza frequência de um termo"""
        if "search_term_frequency" not in st.session_state:
            st.session_state.search_term_frequency = {}

        termo_lower = termo.lower()
        freq_dict = st.session_state.search_term_frequency
        freq_dict[termo_lower] = freq_dict.get(termo_lower, 0) + 1
        st.session_state.search_term_frequency = freq_dict

    def get_trending_terms(self, limit: int = 5) -> List[str]:
        """Retorna termos mais buscados"""
        if not st.session_state.get("search_term_frequency"):
            return self.default_suggestions[:limit]

        freq_dict = st.session_state.search_term_frequency
        sorted_terms = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_terms[:limit]]

    def filter_results_by_quick_filters(
        self, results: List[str], _todas_cartas: Dict
    ) -> List[str]:
        """
        Aplica quick filters aos resultados de busca

        Args:
            results: Lista de IDs de cartas
            _todas_cartas: Dicionário com todas as cartas

        Returns:
            IDs filtrados
        """
        if "quick_filters" not in st.session_state:
            st.session_state.quick_filters = {
                "century_xx": False,
                "only_with_data": False,
                "only_with_location": False,
            }

        filters = st.session_state.quick_filters
        filtered_results = results.copy()

        # Filtro: Século XX (1900-2000)
        if filters.get("century_xx"):
            filtered_results = [
                id for id in filtered_results
                if _todas_cartas.get(id, {}).get("data", "").startswith(("19", "20"))
            ]

        # Filtro: Apenas com data preenchida
        if filters.get("only_with_data"):
            filtered_results = [
                id for id in filtered_results
                if _todas_cartas.get(id, {}).get("data")
            ]

        # Filtro: Apenas com localização (município/UF)
        if filters.get("only_with_location"):
            filtered_results = [
                id
                for id in filtered_results
                if _todas_cartas.get(id, {}).get("municipio")
                or _todas_cartas.get(id, {}).get("uf")
            ]

        return filtered_results

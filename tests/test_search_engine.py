"""
Testes unitários para SearchEngine.
Cobertura: busca simples, operadores, variações lexicais, escopo.
"""

import pytest
from modules.search_engine import SearchEngine, StemIndexUnavailable


class TestSearchSimples:
    """Testes para busca simples por substring."""

    def test_busca_simples_case_insensitive(self, test_cartas):
        """Busca simples (case-insensitive)."""
        search = SearchEngine()
        ids, resultados = search.search_simples(test_cartas, "democracia", case_sensitive=False)

        # Verificar que encontrou as cartas esperadas (1, 2, 3, 8 têm "democracia")
        assert '1' in ids
        assert '2' in ids
        assert '3' in ids
        assert '8' in ids
        # Verificar contagens
        assert resultados['1'] >= 1

    def test_busca_simples_case_sensitive(self, test_cartas):
        """Busca simples (case-sensitive)."""
        search = SearchEngine()
        ids, resultados = search.search_simples(test_cartas, "Democracia", case_sensitive=True)

        # Case-sensitive, deve encontrar menos resultados
        assert len(ids) == 0  # nenhuma carta com "Democracia" maiúscula

    def test_busca_simples_accents_removed(self, test_cartas):
        """Busca sem acentos deve encontrar palavras acentuadas."""
        search = SearchEngine()
        # Buscar "historia" sem acento, mas o texto tem "história"
        ids, resultados = search.search_simples(test_cartas, "historia", case_sensitive=False)

        assert len(ids) >= 1  # deve encontrar mesmo sem acento
        assert '1' in ids

    def test_busca_simples_nao_encontrada(self, test_cartas):
        """Busca por termo não encontrado."""
        search = SearchEngine()
        ids, resultados = search.search_simples(test_cartas, "xyzabc", case_sensitive=False)

        assert len(ids) == 0
        assert len(resultados) == 0

    def test_busca_simples_nome_e_texto(self, test_cartas):
        """Busca simples busca em nome e texto."""
        search = SearchEngine()
        ids, resultados = search.search_simples(test_cartas, "silva", case_sensitive=False)

        # Encontra "Silva" em nome (cartas 1 e 5)
        assert '1' in ids  # João da Silva
        assert '5' in ids  # Pedro Silva

    def test_busca_simples_nome_maiuscula_case_insensitive(self, test_cartas):
        """REGRESSÃO: Busca case-insensitive em nome com maiúscula.

        Bug encontrado: search_simples não normalizava campo 'nome' para lowercase
        quando case_sensitive=False, fazendo buscas case-insensitive falharem em
        nomes com maiúsculas. Teste garante que a correção permanece.
        """
        search = SearchEngine()

        # Buscar por "silva" em minúsculas, deve encontrar nome="João da Silva"
        ids, resultados = search.search_simples(test_cartas, "silva", case_sensitive=False)
        assert '1' in ids, "Deve encontrar 'silva' minúscula em nome='João da Silva'"
        assert '5' in ids, "Deve encontrar 'silva' minúscula em nome='Pedro Silva'"

        # Buscar por "SILVA" em maiúsculas, deve encontrar os mesmos
        ids2, resultados2 = search.search_simples(test_cartas, "SILVA", case_sensitive=False)
        assert '1' in ids2, "Deve encontrar 'SILVA' maiúscula em nome='João da Silva'"
        assert '5' in ids2, "Deve encontrar 'SILVA' maiúscula em nome='Pedro Silva'"

        # Buscar case-sensitive deve ser diferente
        ids3, resultados3 = search.search_simples(test_cartas, "silva", case_sensitive=True)
        assert '1' not in ids3, "Case-sensitive deve NOT encontrar 'silva' em 'João da Silva'"


class TestSearchRegex:
    """Testes para busca com regex."""

    def test_search_regex_simples(self, test_cartas):
        """Busca regex com padrão simples."""
        search = SearchEngine()
        ids, resultados = search.search_regex(test_cartas, r"democr\w+", case_sensitive=False)

        assert len(ids) > 0
        assert '1' in ids  # tem "democracia"

    def test_search_regex_case_insensitive(self, test_cartas):
        """Busca regex case-insensitive."""
        search = SearchEngine()
        ids, resultados = search.search_regex(test_cartas, r"[Dd]ireit", case_sensitive=False)

        assert len(ids) > 0
        assert '3' in ids  # "direitos" em texto
        assert '6' in ids  # "direitos" em texto

    def test_search_regex_invalid(self, test_cartas):
        """Busca regex com padrão inválido."""
        search = SearchEngine()
        ids, resultados = search.search_regex(test_cartas, r"[", case_sensitive=False)

        assert len(ids) == 0
        assert 'erro' in resultados


class TestSearchLexicalVariations:
    """Testes para variações lexicais (stemming)."""

    def test_search_lexical_variations_no_index(self, test_cartas):
        """Busca de variações sem índice lança exceção."""
        search = SearchEngine()
        with pytest.raises(StemIndexUnavailable):
            search.search_lexical_variations(test_cartas, "democracia", None)

    def test_search_lexical_variations_requires_index(self, test_cartas):
        """Busca de variações requer índice de stems pré-computado."""
        # Este teste verifica que a API espera um índice
        search = SearchEngine()

        # Sem índice, deve lançar exceção
        with pytest.raises(StemIndexUnavailable):
            search.search_lexical_variations(test_cartas, "qualquer_termo", None)


class TestSearchAdvanced:
    """Testes para busca avançada com operadores."""

    def test_advanced_search_frase_exata(self, test_cartas):
        """Operador de frase exata ("frase")."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            '"direitos políticos"',
            use_variations=False
        )

        assert '3' in ids  # Tem "direitos políticos"

    def test_advanced_search_frase_exata_nao_encontrada(self, test_cartas):
        """Frase exata não encontrada."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            '"xyz abc def"',
            use_variations=False
        )

        assert len(ids) == 0

    def test_advanced_search_obrigatorio(self, test_cartas):
        """Operador obrigatório (+termo)."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            "+democracia",
            use_variations=False
        )

        # Deve encontrar apenas cartas com "democracia"
        assert '1' in ids
        assert '2' in ids
        assert '8' in ids
        assert '7' not in ids  # não tem democracia

    def test_advanced_search_exclusao(self, test_cartas):
        """Operador de exclusão (-termo)."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            "+direitos -trabalho",
            use_variations=False
        )

        # Deve encontrar cartas com "direitos" mas sem "trabalho"
        assert '3' in ids  # tem direitos, sem trabalho
        assert '4' in ids  # tem direitos, sem trabalho
        assert '6' not in ids  # tem ambos

    def test_advanced_search_wildcard(self, test_cartas):
        """Wildcard de prefixo (termo*)."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            "direito*",
            use_variations=False
        )

        # Deve encontrar "direitos", "direito", etc
        assert '3' in ids
        assert '4' in ids
        assert '6' in ids

    def test_advanced_search_multiplos_termos(self, test_cartas):
        """Múltiplos termos (OR - pelo menos um)."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            "justiça educação",
            use_variations=False
        )

        # Deve encontrar cartas com educação ou justiça
        assert '1' in ids  # tem educação
        assert '4' in ids  # tem justiça
        assert '8' in ids  # tem educação

    def test_advanced_search_obrigatorio_e_exclusao(self, test_cartas):
        """Combinação de obrigatório e exclusão."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            "+educação -trabalho",
            use_variations=False
        )

        # Tem educação, sem trabalho
        assert '1' in ids
        assert '8' in ids
        assert '6' not in ids  # tem trabalho

    def test_advanced_search_with_variations_requires_index(self, test_cartas):
        """Busca avançada com variações requer índice."""
        search = SearchEngine()
        # Sem índice, deve lançar exceção
        with pytest.raises(StemIndexUnavailable):
            search.search_advanced(
                test_cartas,
                "democracia",
                use_variations=True,
                stem_index=None
            )

    def test_advanced_search_variations_no_index(self, test_cartas):
        """Busca avançada com variações sem índice lança exceção."""
        search = SearchEngine()
        with pytest.raises(StemIndexUnavailable):
            search.search_advanced(
                test_cartas,
                "democracia",
                use_variations=True,
                stem_index=None
            )

    def test_advanced_search_search_fields(self, test_cartas):
        """Busca avançada com campos específicos."""
        search = SearchEngine()
        ids, resultados = search.search_advanced(
            test_cartas,
            "educação",
            use_variations=False,
            search_fields={'texto'}
        )

        # Busca apenas no campo 'texto'
        assert len(ids) > 0


class TestHighlight:
    """Testes para highlight de termos."""

    def test_highlight_term_simples(self, test_cartas):
        """Highlight de termo simples."""
        search = SearchEngine()
        texto = test_cartas['1']['texto']
        resultado = search.highlight_term(texto, "democracia", cor="yellow", case_sensitive=False)

        # Deve conter marca HTML
        assert '<mark' in resultado
        assert 'democracia' in resultado.lower()

    def test_highlight_term_case_insensitive(self, test_cartas):
        """Highlight case-insensitive."""
        search = SearchEngine()
        texto = test_cartas['1']['texto']
        resultado = search.highlight_term(texto, "DEMOCRACIA", cor="yellow", case_sensitive=False)

        assert '<mark' in resultado

    def test_highlight_term_not_found(self, test_cartas):
        """Highlight de termo não encontrado."""
        search = SearchEngine()
        texto = test_cartas['1']['texto']
        resultado = search.highlight_term(texto, "xyzabc", cor="yellow")

        # Deve retornar texto sem marcas
        assert '<mark' not in resultado
        assert resultado == texto

    def test_highlight_multiple_terms(self, test_cartas):
        """Highlight de múltiplos termos com cores diferentes."""
        search = SearchEngine()
        texto = test_cartas['1']['texto']
        resultado = search.highlight_multiple_terms(
            texto,
            ["democracia", "história"],
            ["yellow", "green"],
            case_sensitive=False
        )

        # Ambos os termos devem estar destacados
        assert '<mark' in resultado
        assert 'yellow' in resultado or 'green' in resultado


class TestParseQuery:
    """Testes para parse de query."""

    def test_parse_query_frase_exata(self):
        """Parse de frase exata."""
        search = SearchEngine()
        tokens = search._parse_query('"frase exata"')

        assert 'frase exata' in tokens['phrases']

    def test_parse_query_obrigatorio(self):
        """Parse de termo obrigatório."""
        search = SearchEngine()
        tokens = search._parse_query('+obrigatorio')

        assert 'obrigatorio' in tokens['required']

    def test_parse_query_exclusao(self):
        """Parse de termo exclusão."""
        search = SearchEngine()
        tokens = search._parse_query('-excluir')

        assert 'excluir' in tokens['excluded']

    def test_parse_query_wildcard(self):
        """Parse de wildcard."""
        search = SearchEngine()
        tokens = search._parse_query('term*')

        assert 'term*' in tokens['optional']

    def test_parse_query_complexa(self):
        """Parse de query complexa."""
        search = SearchEngine()
        tokens = search._parse_query('+obrigatorio "frase exata" opcional -excluir term*')

        assert 'obrigatorio' in tokens['required']
        assert 'frase exata' in tokens['phrases']
        assert 'opcional' in tokens['optional'] or 'term*' in tokens['optional']
        assert 'excluir' in tokens['excluded']


class TestGetResumo:
    """Testes para resumo de busca."""

    def test_get_resumo_busca(self, test_cartas):
        """Get resumo da última busca."""
        search = SearchEngine()
        search.search_simples(test_cartas, "democracia")
        resumo = search.get_resumo_busca()

        assert resumo["termo"] == "democracia"
        assert resumo["total_encontrado"] > 0
        assert len(resumo["ocorrencias"]) > 0

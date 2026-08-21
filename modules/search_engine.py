"""
Engine de busca avançada com suporte a regex, case-insensitive e variações lexicais.

O modo "Variações" delega a variações lexicais reais para StemmingEngine
(radical RSLP via NLTK) em vez de um dicionário fixo de termos
pré-selecionados -- funciona para qualquer palavra da base, não apenas para
uma lista escolhida manualmente. Ver modules/stemming_engine.py.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Set

from .stemming_engine import StemmingEngine


class StemIndexUnavailable(Exception):
    """Busca em modo 'Variações' foi solicitada sem um índice de stems carregado."""
    pass


class SearchEngine:
    """Executa buscas avançadas nas cartas."""

    def __init__(self):
        """Inicializa o search engine."""
        self.last_search_term = ""
        self.last_results: Dict[str, int] = {}
        # Usado apenas para stem(word)/tokenize() (leve, sem I/O de disco).
        # O índice invertido em si (stem -> carta_id -> contagem) é carregado
        # pelo chamador via StemmingEngine.load_index() e passado como
        # `stem_index` aos métodos de busca abaixo.
        self.stemming = StemmingEngine()

    @staticmethod
    def _strip_accents(text: str) -> str:
        """Remove acentos de um texto usando normalização Unicode NFD."""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    def search_simples(
        self,
        cartas: Dict,
        termo: str,
        case_sensitive: bool = False
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Busca simples por palavra exata.

        Args:
            cartas: Dicionário de cartas
            termo: Termo a buscar
            case_sensitive: Se True, considera maiúsculas/minúsculas

        Returns:
            Tupla (lista de IDs encontrados, dict com contagem de ocorrências)
        """
        resultados = {}

        for carta_id, carta in cartas.items():
            texto = carta.get('texto', '')
            nome = carta.get('nome', '')

            if not case_sensitive:
                texto = texto.lower()
                nome = nome.lower()
                termo_lower = termo.lower()
            else:
                termo_lower = termo

            # Contagem com normalização de acentos
            texto_norm = SearchEngine._strip_accents(texto)
            nome_norm = SearchEngine._strip_accents(nome)
            termo_norm = SearchEngine._strip_accents(termo_lower)
            ocorrencias = texto_norm.count(termo_norm)
            ocorrencias += nome_norm.count(termo_norm)

            if ocorrencias > 0:
                resultados[carta_id] = ocorrencias

        self.last_search_term = termo
        self.last_results = resultados
        return list(resultados.keys()), resultados

    def search_regex(
        self,
        cartas: Dict,
        pattern: str,
        case_sensitive: bool = False
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Busca usando expressões regulares.

        Args:
            cartas: Dicionário de cartas
            pattern: Padrão regex
            case_sensitive: Se True, considera maiúsculas/minúsculas

        Returns:
            Tupla (lista de IDs encontrados, dict com contagem de ocorrências)
        """
        resultados = {}

        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)

            for carta_id, carta in cartas.items():
                texto = carta.get('texto', '')
                nome = carta.get('nome', '')

                matches_texto = regex.findall(texto)
                matches_nome = regex.findall(nome)
                total_matches = len(matches_texto) + len(matches_nome)

                if total_matches > 0:
                    resultados[carta_id] = total_matches

        except re.error as e:
            return [], {"erro": str(e)}

        self.last_search_term = pattern
        self.last_results = resultados
        return list(resultados.keys()), resultados

    def _require_stem_index(self, stem_index: Optional[Dict]) -> Dict:
        if stem_index is None:
            raise StemIndexUnavailable(
                "Busca em modo 'Variações' requer o índice de stems pré-computado. "
                "Use o botão '⚡ Pré-computar Índice de Stems' na aba Configurações."
            )
        return stem_index

    def get_variacoes_matches(
        self,
        termo: str,
        stem_index: Dict,
        search_fields: Optional[Set[str]] = None,
        cartas: Optional[Dict] = None
    ) -> Dict[str, int]:
        """
        Retorna carta_id -> contagem de ocorrências do radical (stem RSLP) de
        `termo` nos campos indicados, a partir do índice pré-computado.

        Substitui o antigo get_variacoes_pattern(): variações lexicais deixam
        de ser um padrão regex fixo e passam a ser resolvidas por igualdade de
        radical via StemmingEngine. Radicais curtos demais (< MIN_STEM_LENGTH)
        caem para substring exata -- ver StemmingEngine.get_stem_matches().
        """
        self._require_stem_index(stem_index)
        return self.stemming.get_stem_matches(stem_index, termo, search_fields, cartas)

    def search_lexical_variations(
        self,
        cartas: Dict,
        termo: str,
        stem_index: Dict,
        search_fields: Optional[Set[str]] = None
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Busca por variações lexicais (mesmo radical RSLP) do termo.

        Args:
            cartas: Dicionário de cartas
            termo: Termo a buscar
            stem_index: Índice de stems pré-computado (StemmingEngine.load_index())
            search_fields: Campos a considerar (None = todos os campos indexados)

        Returns:
            Tupla (lista de IDs encontrados, dict com contagem de ocorrências)
        """
        contagens = self.get_variacoes_matches(termo, stem_index, search_fields, cartas)
        resultados = {cid: n for cid, n in contagens.items() if cid in cartas}

        self.last_search_term = termo
        self.last_results = resultados
        return list(resultados.keys()), resultados

    def search_advanced(
        self,
        cartas: Dict,
        query: str,
        case_sensitive: bool = False,
        use_variations: bool = True,
        search_fields: Set[str] = None,
        stem_index: Optional[Dict] = None
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Busca avançada com suporte a operadores: aspas (frase), + (obrigatório), - (excluído), * (wildcard).

        Args:
            cartas: Dicionário de cartas
            query: String de busca com operadores
            case_sensitive: Considerar maiúsculas
            use_variations: Usar variações lexicais (radical RSLP -- requer stem_index)
            search_fields: Campos a buscar (None = todos, ["texto"] = apenas texto)
            stem_index: Índice de stems pré-computado, obrigatório quando use_variations=True
                        (StemmingEngine.load_index()). Ignorado se use_variations=False.

        Returns:
            Tupla (lista de IDs encontrados, dict com contagem de ocorrências)

        Raises:
            StemIndexUnavailable: use_variations=True e stem_index=None.
        """
        if search_fields is None:
            search_fields = {'texto', 'nome', 'destinatario', 'catalogo', 'indexacao', 'origem'}

        resultados = {}
        tokens = self._parse_query(query)

        # Resolve os termos de variação via índice de stems UMA VEZ (lookup O(1)
        # por termo), em vez de tokenizar/radicalizar o texto de cada carta
        # dentro do loop principal -- é o que torna a busca em modo "Variações"
        # rápida mesmo sobre a base inteira.
        stem_matches: Dict[str, Dict[str, int]] = {}
        if use_variations:
            self._require_stem_index(stem_index)
            termos_variacao = set(
                t for t in tokens['required'] + tokens['excluded'] + tokens['optional']
                if '*' not in t
            )
            for term in termos_variacao:
                stem_matches[term] = self.stemming.get_stem_matches(stem_index, term, search_fields, cartas)

        for carta_id, carta in cartas.items():
            carta_text = self._extract_carta_text(carta, search_fields, case_sensitive)

            if self._matches_query(carta_id, carta_text, tokens, case_sensitive, use_variations, stem_matches):
                ocorrencias = self._count_occurrences(carta_id, carta_text, tokens, case_sensitive, use_variations, stem_matches)
                resultados[carta_id] = ocorrencias

        self.last_search_term = query
        self.last_results = resultados
        return list(resultados.keys()), resultados

    def _parse_query(self, query: str) -> Dict[str, list]:
        """Analisa a query e retorna dicionário com operadores."""
        tokens = {
            'required': [],
            'excluded': [],
            'phrases': [],
            'optional': []
        }

        i = 0
        current_token = ''
        in_quotes = False

        while i < len(query):
            char = query[i]

            if char == '"':
                in_quotes = not in_quotes
                if not in_quotes and current_token:
                    tokens['phrases'].append(current_token.strip())
                    current_token = ''
                i += 1
                continue

            if in_quotes:
                current_token += char
                i += 1
                continue

            if char == '+' and current_token == '':
                # Termo obrigatório
                i += 1
                j = i
                while j < len(query) and query[j] not in ' \t\n':
                    j += 1
                tokens['required'].append(query[i:j])
                i = j
                continue

            if char == '-' and current_token == '':
                # Termo a excluir
                i += 1
                j = i
                while j < len(query) and query[j] not in ' \t\n':
                    j += 1
                tokens['excluded'].append(query[i:j])
                i = j
                continue

            if char in ' \t\n':
                if current_token:
                    tokens['optional'].append(current_token)
                    current_token = ''
                i += 1
                continue

            current_token += char
            i += 1

        if current_token:
            tokens['optional'].append(current_token)

        return tokens

    def _extract_carta_text(self, carta: Dict, search_fields: Set[str], case_sensitive: bool) -> str:
        """Extrai texto da carta dos campos especificados."""
        texts = []
        for field in search_fields:
            if field in carta:
                text = str(carta[field])
                if not case_sensitive:
                    text = text.lower()
                texts.append(text)
        return ' '.join(texts)

    def _matches_query(
        self,
        carta_id: str,
        text: str,
        tokens: Dict,
        case_sensitive: bool,
        use_variations: bool,
        stem_matches: Optional[Dict[str, Dict[str, int]]] = None
    ) -> bool:
        """Verifica se o texto corresponde à query."""
        # Termos obrigatórios
        for term in tokens['required']:
            if not self._term_in_text(carta_id, text, term, case_sensitive, use_variations, stem_matches):
                return False

        # Termos a excluir
        for term in tokens['excluded']:
            if self._term_in_text(carta_id, text, term, case_sensitive, use_variations, stem_matches):
                return False

        # Frases exatas
        for phrase in tokens['phrases']:
            search_phrase = phrase if case_sensitive else phrase.lower()
            if search_phrase not in text:
                return False

        # Termos opcionais (pelo menos um deve estar presente)
        if tokens['optional']:
            found_any = False
            for term in tokens['optional']:
                if self._term_in_text(carta_id, text, term, case_sensitive, use_variations, stem_matches):
                    found_any = True
                    break
            if not found_any:
                return False

        return True

    def _term_in_text(
        self,
        carta_id: str,
        text: str,
        term: str,
        case_sensitive: bool,
        use_variations: bool,
        stem_matches: Optional[Dict[str, Dict[str, int]]] = None
    ) -> bool:
        """Verifica se um termo está no texto."""
        search_term = term if case_sensitive else term.lower()

        # Suporte a wildcard (*)
        if '*' in search_term:
            pattern = search_term.replace('*', r'\w*')
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                return bool(re.search(rf'\b{pattern}\b', text, flags))
            except:
                return False

        # Variações lexicais -- lookup O(1) no índice de stems pré-resolvido
        # em search_advanced (evita tokenizar/radicalizar o texto da carta aqui).
        if use_variations:
            if stem_matches is None or term not in stem_matches:
                raise StemIndexUnavailable(
                    "Busca em modo 'Variações' requer o índice de stems pré-computado. "
                    "Use o botão '⚡ Pré-computar Índice de Stems' na aba Configurações."
                )
            return carta_id in stem_matches[term]

        # Modo "Exato": substring com normalização de acentos (insensível a acentuação)
        norm_text = SearchEngine._strip_accents(text)
        norm_term = SearchEngine._strip_accents(search_term)
        return norm_term in norm_text

    def _count_occurrences(
        self,
        carta_id: str,
        text: str,
        tokens: Dict,
        case_sensitive: bool,
        use_variations: bool = False,
        stem_matches: Optional[Dict[str, Dict[str, int]]] = None
    ) -> int:
        """Conta ocorrências dos termos no texto."""
        count = 0
        flags = 0 if case_sensitive else re.IGNORECASE

        for term in tokens['required'] + tokens['optional']:
            search_term = term if case_sensitive else term.lower()

            # Wildcard (*) -- mesma lógica de padrão usada em _term_in_text
            if '*' in search_term:
                pattern = search_term.replace('*', r'\w*')
                try:
                    count += len(re.findall(rf'\b{pattern}\b', text, flags))
                except re.error:
                    pass
                continue

            # Variações lexicais -- soma as contagens (por campo já agregadas)
            # do índice de stems pré-resolvido, não apenas a substring literal.
            if use_variations:
                if stem_matches is None or term not in stem_matches:
                    raise StemIndexUnavailable(
                        "Busca em modo 'Variações' requer o índice de stems pré-computado. "
                        "Use o botão '⚡ Pré-computar Índice de Stems' na aba Configurações."
                    )
                count += stem_matches[term].get(carta_id, 0)
                continue

            count += text.count(search_term)

        for phrase in tokens['phrases']:
            search_phrase = phrase if case_sensitive else phrase.lower()
            count += text.count(search_phrase)

        return max(count, 1) if count > 0 else 0

    def get_matches_positions(
        self,
        texto: str,
        termo: str,
        case_sensitive: bool = False,
        use_regex: bool = False,
        use_stemming: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Encontra posições exatas do termo no texto.

        Args:
            texto: Texto a buscar
            termo: Termo ou padrão
            case_sensitive: Considerar maiúsculas
            use_regex: Usar regex
            use_stemming: Destacar palavras do texto que compartilham o
                          radical RSLP de `termo` (modo "Variações"), em vez
                          de casar `termo` literalmente ou via regex.

        Returns:
            Lista de tuplas (início, fim) das posições
        """
        posicoes = []

        try:
            if use_stemming:
                return self.stemming.get_stem_word_positions(texto, termo)

            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                for match in re.finditer(termo, texto, flags):
                    posicoes.append((match.start(), match.end()))
            else:
                search_text = texto if case_sensitive else texto.lower()
                search_termo = termo if case_sensitive else termo.lower()

                start = 0
                while True:
                    pos = search_text.find(search_termo, start)
                    if pos == -1:
                        break
                    posicoes.append((pos, pos + len(termo)))
                    start = pos + 1

                # Se não encontrou, tenta com normalização de acentos
                if not posicoes and not case_sensitive:
                    norm_text = SearchEngine._strip_accents(search_text)
                    norm_termo = SearchEngine._strip_accents(search_termo)
                    start = 0
                    while True:
                        pos = norm_text.find(norm_termo, start)
                        if pos == -1:
                            break
                        posicoes.append((pos, pos + len(termo)))
                        start = pos + 1

        except Exception:
            pass

        return posicoes

    def highlight_term(
        self,
        texto: str,
        termo: str,
        cor: str = "yellow",
        case_sensitive: bool = False,
        use_regex: bool = False,
        use_stemming: bool = False
    ) -> str:
        """
        Destaca o termo no texto com tags HTML.
        Usa StringBuilder pattern para evitar O(n²) complexity.

        Args:
            texto: Texto original
            termo: Termo a destacar
            cor: Cor do destaque
            case_sensitive: Considerar maiúsculas
            use_regex: Usar regex
            use_stemming: Destacar variações lexicais (mesmo radical RSLP)

        Returns:
            Texto com destaques em HTML
        """
        posicoes = self.get_matches_positions(texto, termo, case_sensitive, use_regex, use_stemming)

        if not posicoes:
            return texto

        # StringBuilder pattern: ordena por posição e reconstrói uma única vez
        resultado_parts = []
        idx_atual = 0

        for start, end in sorted(posicoes):
            match_text = texto[start:end]
            resultado_parts.append(texto[idx_atual:start])
            resultado_parts.append(f'<mark style="background-color: {cor}; color: #0a0e1f; padding: 2px 4px;">{match_text}</mark>')
            idx_atual = end

        resultado_parts.append(texto[idx_atual:])
        return ''.join(resultado_parts)

    def highlight_multiple_terms(
        self,
        texto: str,
        termos: List[str],
        cores: List[str],
        case_sensitive: bool = False,
        use_regex: bool = False,
        use_stemming: bool = False
    ) -> str:
        """
        Destaca múltiplos termos com cores diferentes.
        Usa StringBuilder pattern para evitar O(n²) string concatenation.

        Args:
            texto: Texto original
            termos: Lista de termos
            cores: Lista de cores
            case_sensitive: Considerar maiúsculas
            use_regex: Usar regex
            use_stemming: Destacar variações lexicais (mesmo radical RSLP)

        Returns:
            Texto com múltiplos destaques
        """
        # Cria lista de (posição, cor, texto_original) para todas as ocorrências
        todas_posicoes = []

        for termo, cor in zip(termos, cores):
            posicoes = self.get_matches_positions(texto, termo, case_sensitive, use_regex, use_stemming)
            for start, end in posicoes:
                todas_posicoes.append((start, end, cor, texto[start:end]))

        if not todas_posicoes:
            return texto

        # Remove duplicatas mantendo a cor da primeira ocorrência
        todas_posicoes = sorted(set((p[0], p[1], p[2], p[3]) for p in todas_posicoes))

        # StringBuilder pattern: ordena por posição inicial e reconstrói uma única vez
        resultado_parts = []
        idx_atual = 0

        for start, end, cor, original_text in todas_posicoes:
            # Adiciona texto antes do match
            resultado_parts.append(texto[idx_atual:start])
            # Adiciona texto destacado
            resultado_parts.append(f'<mark style="background-color: {cor}; color: #0a0e1f; padding: 2px 4px;">{original_text}</mark>')
            idx_atual = end

        # Adiciona texto restante
        resultado_parts.append(texto[idx_atual:])

        return ''.join(resultado_parts)

    def get_resumo_busca(self) -> Dict:
        """Retorna resumo da última busca realizada."""
        return {
            "termo": self.last_search_term,
            "total_encontrado": len(self.last_results),
            "ocorrencias": self.last_results
        }

    def get_variacoes_info(self, termo: str, stem_index: Dict) -> List[str]:
        """
        Retorna as formas de superfície (palavras reais da base) que
        compartilham o radical RSLP de `termo`, conforme observado no
        índice pré-computado -- ou seja, as variações efetivamente
        encontradas, não uma lista teórica pré-definida.
        """
        formas = self.stemming.get_forms(stem_index, termo)
        return list(formas) if formas else [termo]

    def get_wildcard_matches(self, cartas: Dict, query: str, case_sensitive: bool = False) -> Dict[str, int]:
        """Retorna contagem de palavras que corresponderam a termos com wildcard (*)."""
        from collections import Counter
        counter = Counter()
        tokens = self._parse_query(query)
        wildcard_terms = [t for t in tokens['required'] + tokens['optional'] if '*' in t]
        if not wildcard_terms:
            return {}
        patterns = []
        for term in wildcard_terms:
            pat = term.replace('*', r'\w*')
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                patterns.append(re.compile(rf'\b{pat}\b', flags))
            except re.error:
                continue
        for carta in cartas.values():
            texto = carta.get('texto', '')
            for pat in patterns:
                for m in pat.findall(texto):
                    key = m.lower() if not case_sensitive else m
                    counter[key] += 1
        return dict(counter)

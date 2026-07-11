"""
Engine de busca avançada com suporte a regex, case-insensitive e variações lexicais.
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Set


class SearchEngine:
    """Executa buscas avançadas nas cartas."""

    # Dicionário de variações lexicais comuns em português
    LEXICAL_VARIATIONS = {
        'historia': r'\b(?:história|histórica|histórico|históricos|históricas|historia)\b',
        'democracia': r'\b(?:democracia|democrático|democráticos|democrática|democráticas)\b',
        'constituicao': r'\b(?:constituição|constitucional|constitucionais)\b',
        'governo': r'\b(?:governo|governante|governantes|governamental)\b',
        'povo': r'\b(?:povo|popular|populares|pública|público|pública)\b',
        'direito': r'\b(?:direito|direitos|direitista)\b',
        'liberdade': r'\b(?:liberdade|liberdades|libertário|livre|livremente)\b',
        'justica': r'\b(?:justiça|justamente|justo|justos)\b',
        'igualdade': r'\b(?:igualdade|igual|iguais|igualmente)\b',
        'educacao': r'\b(?:educação|educacional|educativos|educados|educador)\b',
        'saude': r'\b(?:saúde|saudável|saúdável)\b',
    }

    def __init__(self):
        """Inicializa o search engine."""
        self.last_search_term = ""
        self.last_results: Dict[str, int] = {}

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
                termo_lower = termo.lower()
            else:
                termo_lower = termo

            # Contagem com normalização de acentos
            texto_norm = SearchEngine._strip_accents(texto)
            termo_norm = SearchEngine._strip_accents(termo_lower)
            ocorrencias = texto_norm.count(termo_norm)
            ocorrencias += SearchEngine._strip_accents(nome).count(termo_norm)

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

    def get_variacoes_pattern(self, termo: str) -> str:
        """
        Retorna o padrão regex final usado para buscar/destacar variações
        lexicais de um termo em modo "Variações" (dicionário pré-definido
        em LEXICAL_VARIATIONS ou padrão automático \\b{termo}\\w*\\b).

        Args:
            termo: Termo buscado

        Returns:
            Padrão regex (string) equivalente ao usado em search_lexical_variations
        """
        # Normalização completa de acentos (NFD) para bater com as chaves
        # (sem acento) de LEXICAL_VARIATIONS -- um replace() parcial de
        # ã/á/é deixava passar í/ó/ú/ê/ç etc. e nunca encontrava a entrada
        # do dicionário para termos como "história".
        termo_normalized = self._strip_accents(termo.lower())

        # Tenta encontrar variação pré-definida
        if termo_normalized in self.LEXICAL_VARIATIONS:
            return self.LEXICAL_VARIATIONS[termo_normalized]

        # Cria padrão automaticamente a partir do termo original
        return rf'\b{re.escape(termo)}\w*\b'

    def search_lexical_variations(
        self,
        cartas: Dict,
        termo: str,
        case_sensitive: bool = False
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Busca por variações lexicais do termo.

        Args:
            cartas: Dicionário de cartas
            termo: Termo a buscar
            case_sensitive: Se True, considera maiúsculas/minúsculas

        Returns:
            Tupla (lista de IDs encontrados, dict com contagem de ocorrências)
        """
        pattern = self.get_variacoes_pattern(termo)
        return self.search_regex(cartas, pattern, case_sensitive)

    def search_advanced(
        self,
        cartas: Dict,
        query: str,
        case_sensitive: bool = False,
        use_variations: bool = True,
        search_fields: Set[str] = None
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Busca avançada com suporte a operadores: aspas (frase), + (obrigatório), - (excluído), * (wildcard).

        Args:
            cartas: Dicionário de cartas
            query: String de busca com operadores
            case_sensitive: Considerar maiúsculas
            use_variations: Usar variações lexicais
            search_fields: Campos a buscar (None = todos, ["texto"] = apenas texto)

        Returns:
            Tupla (lista de IDs encontrados, dict com contagem de ocorrências)
        """
        if search_fields is None:
            search_fields = {'texto', 'nome', 'destinatario', 'catalogo', 'indexacao', 'origem'}

        resultados = {}
        tokens = self._parse_query(query)

        for carta_id, carta in cartas.items():
            carta_text = self._extract_carta_text(carta, search_fields, case_sensitive)

            if self._matches_query(carta_text, tokens, case_sensitive, use_variations):
                ocorrencias = self._count_occurrences(carta_text, tokens, case_sensitive, use_variations)
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

    def _matches_query(self, text: str, tokens: Dict, case_sensitive: bool, use_variations: bool) -> bool:
        """Verifica se o texto corresponde à query."""
        # Termos obrigatórios
        for term in tokens['required']:
            if not self._term_in_text(text, term, case_sensitive, use_variations):
                return False

        # Termos a excluir
        for term in tokens['excluded']:
            if self._term_in_text(text, term, case_sensitive, use_variations):
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
                if self._term_in_text(text, term, case_sensitive, use_variations):
                    found_any = True
                    break
            if not found_any:
                return False

        return True

    def _term_in_text(self, text: str, term: str, case_sensitive: bool, use_variations: bool) -> bool:
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

        # Variações lexicais -- usa o mesmo padrão do highlight (get_variacoes_pattern)
        # para garantir que matching e destaque nunca divirjam.
        if use_variations:
            pattern = self.get_variacoes_pattern(term)
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                if re.search(pattern, text, flags):
                    return True
            except re.error:
                pass

        # Busca com normalização de acentos (insensível a acentuação)
        norm_text = SearchEngine._strip_accents(text)
        norm_term = SearchEngine._strip_accents(search_term)
        return norm_term in norm_text

    def _count_occurrences(self, text: str, tokens: Dict, case_sensitive: bool, use_variations: bool = False) -> int:
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

            # Variações lexicais -- conta todas as formas que casaram,
            # não apenas a substring literal do termo buscado.
            if use_variations:
                pattern = self.get_variacoes_pattern(term)
                try:
                    count += len(re.findall(pattern, text, flags))
                    continue
                except re.error:
                    pass

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
        use_regex: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Encontra posições exatas do termo no texto.

        Args:
            texto: Texto a buscar
            termo: Termo ou padrão
            case_sensitive: Considerar maiúsculas
            use_regex: Usar regex

        Returns:
            Lista de tuplas (início, fim) das posições
        """
        posicoes = []

        try:
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
        use_regex: bool = False
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

        Returns:
            Texto com destaques em HTML
        """
        posicoes = self.get_matches_positions(texto, termo, case_sensitive, use_regex)

        if not posicoes:
            return texto

        # StringBuilder pattern: ordena por posição e reconstrói uma única vez
        resultado_parts = []
        idx_atual = 0

        for start, end in sorted(posicoes):
            match_text = texto[start:end]
            resultado_parts.append(texto[idx_atual:start])
            resultado_parts.append(f'<mark style="background-color: {cor}; padding: 2px 4px;">{match_text}</mark>')
            idx_atual = end

        resultado_parts.append(texto[idx_atual:])
        return ''.join(resultado_parts)

    def highlight_multiple_terms(
        self,
        texto: str,
        termos: List[str],
        cores: List[str],
        case_sensitive: bool = False,
        use_regex: bool = False
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

        Returns:
            Texto com múltiplos destaques
        """
        # Cria lista de (posição, cor, texto_original) para todas as ocorrências
        todas_posicoes = []

        for termo, cor in zip(termos, cores):
            posicoes = self.get_matches_positions(texto, termo, case_sensitive, use_regex)
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
            resultado_parts.append(f'<mark style="background-color: {cor}; padding: 2px 4px;">{original_text}</mark>')
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

    def get_variacoes_info(self, termo: str) -> List[str]:
        """Retorna lista de variações lexicais que serão pesquisadas."""
        pattern = self.get_variacoes_pattern(termo)
        match = re.search(r'\(\?:(.*?)\)', pattern)
        if match:
            return match.group(1).split('|')
        return [termo]

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

"""
Motor de variações lexicais por radical (stemming), via RSLP (NLTK).

Substitui o antigo dicionário fixo LEXICAL_VARIATIONS por um mecanismo
generalizável: duas palavras são consideradas variações uma da outra quando
compartilham o mesmo radical RSLP (Removedor de Sufixos da Língua
Portuguesa), sem depender de uma lista pré-selecionada de termos.

Antes de radicalizar, as palavras são despojadas de acentos (NFD). O RSLP é
sensível a acentuação -- "historia" (sem acento, como o usuário costuma
digitar na busca) e "história" (como aparece no texto real) produzem
radicais DIFERENTES se alimentados ao stemmer sem essa normalização
("hist" vs "histór"). Como indexação e consulta passam pelo mesmo
_normalize(), esse descasamento nunca ocorre.

Fluxo de uso:
    1. ensure_rslp_available() -- garante o recurso 'rslp' do NLTK (idempotente)
    2. compute_stem_index()    -- pré-computa e salva o índice invertido em cache
    3. load_index()            -- carrega o índice pré-computado (levanta
                                   FileNotFoundError com orientação se ausente/desatualizado)
    4. get_stem_matches()      -- dado um termo, retorna carta_id -> contagem
    5. get_stem_word_positions() -- usado pelo highlight, palavra a palavra, por carta
"""

import pickle
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

DEFAULT_FIELDS = ('texto', 'nome', 'destinatario', 'catalogo', 'indexacao', 'origem')

# Radicais mais curtos que isso são descartados demais pelas regras do RSLP e
# passam a colidir com palavras não-relacionadas por coincidência ortográfica
# (ex.: "justiça" -> radical "jus", que também casa com "jusante"). Abaixo
# desse comprimento, a expansão por família de radical é considerada pouco
# confiável e a busca cai para substring exata (accent-insensível) -- regra
# estrutural, não uma lista de exceções por palavra.
MIN_STEM_LENGTH = 5

# Memoização em nível de módulo: nltk.data.find() é chamado uma única vez
# por processo, evitando checar/baixar o recurso a cada instância criada.
_rslp_ready = False
_rslp_error: Optional[str] = None


def ensure_rslp_available() -> Tuple[bool, str]:
    """
    Garante que o recurso 'rslp' do NLTK está disponível, baixando-o se
    necessário. Não tenta baixar de novo em chamadas subsequentes -- nem
    quando já está presente em disco, nem quando uma tentativa anterior já
    falhou nesta mesma execução do processo.

    Trata falha de rede (ex.: deploy em ambiente sem acesso à internet) de
    forma explícita, retornando uma mensagem clara em vez de propagar a
    exceção do nltk.

    Returns:
        Tupla (disponível: bool, mensagem_erro: str). mensagem_erro é ''
        quando disponível é True.
    """
    global _rslp_ready, _rslp_error

    if _rslp_ready:
        return True, ""
    if _rslp_error:
        return False, _rslp_error

    import nltk

    try:
        nltk.data.find('stemmers/rslp')
        _rslp_ready = True
        return True, ""
    except LookupError:
        pass

    try:
        nltk.download('rslp', quiet=True)
        nltk.data.find('stemmers/rslp')
        _rslp_ready = True
        return True, ""
    except Exception as e:
        _rslp_error = (
            "Não foi possível baixar o recurso 'rslp' do NLTK, necessário para "
            "a busca por variações lexicais (stemming). Verifique a conexão "
            f"com a internet e tente novamente. Detalhe técnico: {e}"
        )
        return False, _rslp_error


class StemmingEngine:
    """
    Índice invertido de radicais RSLP para busca por variações lexicais,
    mais utilitários de tokenização/radicalização usados no highlight.
    """

    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = Path(cache_dir)
        self._stemmer = None
        self._stem_cache: Dict[str, str] = {}  # palavra normalizada -> radical

    # ------------------------------------------------------------------ #
    # Radicalização                                                       #
    # ------------------------------------------------------------------ #

    def _get_stemmer(self):
        if self._stemmer is None:
            ok, msg = ensure_rslp_available()
            if not ok:
                raise RuntimeError(msg)
            from nltk.stem import RSLPStemmer
            self._stemmer = RSLPStemmer()
        return self._stemmer

    @staticmethod
    def _strip_accents(text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    @classmethod
    def _normalize(cls, word: str) -> str:
        return cls._strip_accents(word.lower())

    @staticmethod
    def tokenize(text: str) -> List[Tuple[str, int, int]]:
        """Tokeniza em palavras (letras Unicode, ignora dígitos/pontuação).

        Returns:
            Lista de (palavra, inicio, fim) na ordem em que aparecem no texto.
        """
        return [(m.group(), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]

    def stem(self, word: str) -> str:
        """Radical RSLP de uma palavra, com acentos removidos e memoização."""
        normalizada = self._normalize(word)
        if not normalizada:
            return normalizada
        radical = self._stem_cache.get(normalizada)
        if radical is not None:
            return radical
        stemmer = self._get_stemmer()
        try:
            radical = stemmer.stem(normalizada)
        except Exception:
            radical = normalizada
        self._stem_cache[normalizada] = radical
        return radical

    def is_stem_reliable(self, termo: str) -> bool:
        """
        False quando o radical de `termo` é curto demais (< MIN_STEM_LENGTH)
        para expandir com segurança por família de radical -- nesse caso a
        busca/destaque devem cair para substring exata em vez de radical.
        """
        return len(self.stem(termo)) >= MIN_STEM_LENGTH

    @staticmethod
    def _word_boundary_pattern(termo_norm: str) -> "re.Pattern":
        """
        Regex do termo normalizado com fronteira de palavra dos dois lados e
        tolerância apenas a um 's' final (plural simples) -- NÃO um \\w*
        aberto. \\w* casaria "historia" dentro de "historiador"/"historiadores"
        (que começam com as mesmas 8 letras), reintroduzindo a colisão com
        palavras de família diferente que a busca por substring solto (e o
        \\b...\\w*\\b ingênuo) permitem. \\bhistorias?\\b não acha boundary
        entre "historia" e o "d" de "historiador", então não casa.
        """
        return re.compile(rf'\b{re.escape(termo_norm)}s?\b')

    def _exact_substring_positions(self, texto: str, termo: str) -> List[Tuple[int, int]]:
        """
        Posições de `termo` em `texto` por correspondência de palavra inteira
        (accent-insensível, tolerando um 's' final de plural) -- não substring
        solto, para não casar `termo` colado no meio de outra palavra.
        """
        texto_norm = self._normalize(texto)
        termo_norm = self._normalize(termo)
        if not termo_norm:
            return []
        pattern = self._word_boundary_pattern(termo_norm)
        return [(m.start(), m.end()) for m in pattern.finditer(texto_norm)]

    def get_stem_word_positions(self, texto: str, termo: str) -> List[Tuple[int, int]]:
        """
        Posições (início, fim) de todas as palavras em `texto` cujo radical
        RSLP é igual ao radical de `termo` -- usado para destacar variações
        lexicais reais do termo buscado, palavra a palavra, numa carta.

        Quando o radical de `termo` é curto demais (< MIN_STEM_LENGTH),
        recai em substring exata em vez de família de radical -- ver
        MIN_STEM_LENGTH.
        """
        if not texto or not termo:
            return []
        if not self.is_stem_reliable(termo):
            return self._exact_substring_positions(texto, termo)
        radical_alvo = self.stem(termo)
        if not radical_alvo:
            return []
        posicoes = []
        for palavra, start, end in self.tokenize(texto):
            if self.stem(palavra) == radical_alvo:
                posicoes.append((start, end))
        return posicoes

    # ------------------------------------------------------------------ #
    # Cache em disco (índice invertido)                                   #
    # ------------------------------------------------------------------ #

    def _get_cache_path(self, db_name: str) -> Path:
        nome_sem_extensao = db_name.rsplit('.', 1)[0] if '.' in db_name else db_name
        nome_seguro = re.sub(r'[^\w\-]', '_', nome_sem_extensao)
        return self.cache_dir / f"stems_{nome_seguro}.pkl"

    def _is_cache_valid(self, cache_path: Path, carta_ids: List[str]) -> bool:
        if not cache_path.exists():
            return False
        try:
            with open(cache_path, 'rb') as f:
                dados = pickle.load(f)
            return set(dados.get('ids', [])) == set(carta_ids)
        except Exception:
            return False

    def compute_stem_index(
        self,
        cartas: Dict,
        db_name: str,
        fields: Tuple[str, ...] = DEFAULT_FIELDS,
        progress_callback=None
    ) -> Tuple[bool, str]:
        """
        Pré-computa o índice invertido radical -> campo -> carta_id -> contagem
        para toda a base, e salva em cache/stems_{db}.pkl.

        Também salva, por radical, o conjunto de formas de superfície
        (palavras reais observadas no texto) -- usado para exibir ao usuário
        quais variações foram efetivamente encontradas.

        Args:
            cartas:  Dicionário {id: dados} com todas as cartas da base.
            db_name: Nome do arquivo da base (define o nome do cache).
            fields:  Campos a indexar.
            progress_callback: Função opcional (atual: int, total: int).

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        try:
            self._get_stemmer()  # garante RSLP disponível antes de processar a base toda
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            index: Dict[str, Dict[str, Dict[str, int]]] = {field: {} for field in fields}
            forms: Dict[str, Set[str]] = {}

            ids = list(cartas.keys())
            total = len(ids)

            for i, (carta_id, carta) in enumerate(cartas.items()):
                for field in fields:
                    valor = carta.get(field)
                    if not valor:
                        continue
                    for palavra, _, _ in self.tokenize(str(valor)):
                        radical = self.stem(palavra)
                        if not radical:
                            continue
                        campo_idx = index[field].setdefault(radical, {})
                        campo_idx[carta_id] = campo_idx.get(carta_id, 0) + 1
                        forms.setdefault(radical, set()).add(palavra.lower())

                if progress_callback is not None and ((i + 1) % 500 == 0 or i + 1 == total):
                    progress_callback(i + 1, total)

            cache_path = self._get_cache_path(db_name)
            payload = {
                'ids': ids,
                'fields': list(fields),
                'index': index,
                'forms': {radical: sorted(palavras) for radical, palavras in forms.items()},
            }
            with open(cache_path, 'wb') as f:
                pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

            tamanho_mb = cache_path.stat().st_size / (1024 * 1024)
            total_radicais = len(forms)
            return (
                True,
                f"{total:,} cartas indexadas · {total_radicais:,} radicais distintos · "
                f"{tamanho_mb:.1f} MB salvo em {cache_path.name}"
            )
        except Exception as e:
            return False, f"Erro durante a computação: {str(e)}"

    def load_index(self, cartas: Dict, db_name: str) -> Dict:
        """
        Carrega o índice de stems pré-computado do cache.

        Nunca dispara computação automaticamente -- se o cache não existir ou
        estiver desatualizado, lança FileNotFoundError com orientação clara.

        Raises:
            FileNotFoundError: cache ausente ou desatualizado em relação à base atual.
        """
        cache_path = self._get_cache_path(db_name)
        carta_ids = list(cartas.keys())

        if not cache_path.exists():
            raise FileNotFoundError(
                f"Índice de stems não encontrado para '{db_name}'. "
                "Use o botão '⚡ Pré-computar Índice de Stems' na aba Configurações "
                "antes de buscar em modo 'Variações'."
            )

        if not self._is_cache_valid(cache_path, carta_ids):
            raise FileNotFoundError(
                f"Índice de stems desatualizado para '{db_name}' "
                "(a base foi alterada desde a última indexação). "
                "Use o botão '⚡ Pré-computar Índice de Stems' para reindexar."
            )

        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    def get_status(self, db_name: str, cartas: Dict) -> Dict:
        """Status do índice de stems para a base atual, sem disparar computação."""
        cache_path = self._get_cache_path(db_name)
        carta_ids = list(cartas.keys())

        cache_existe = cache_path.exists()
        cache_valido = False
        total_indexado = 0
        total_radicais = 0
        tamanho_mb = 0.0

        if cache_existe:
            try:
                with open(cache_path, 'rb') as f:
                    dados = pickle.load(f)
                ids_cache = dados.get('ids', [])
                total_indexado = len(ids_cache)
                cache_valido = set(ids_cache) == set(carta_ids)
                total_radicais = len(dados.get('forms', {}))
                tamanho_mb = cache_path.stat().st_size / (1024 * 1024)
            except Exception:
                cache_existe = False

        return {
            'cache_existe': cache_existe,
            'cache_valido': cache_valido,
            'total_indexado': total_indexado,
            'total_radicais': total_radicais,
            'tamanho_mb': tamanho_mb,
        }

    # ------------------------------------------------------------------ #
    # Consulta ao índice                                                   #
    # ------------------------------------------------------------------ #

    def _exact_substring_matches(
        self,
        cartas: Optional[Dict],
        termo: str,
        campos: Tuple[str, ...]
    ) -> Dict[str, int]:
        """
        Contagem por correspondência de palavra inteira (accent-insensível,
        tolerando um 's' final de plural) nos campos indicados de cada carta
        -- não substring solto, para não casar `termo` colado no meio de
        outra palavra (ex.: "historia" dentro de "historiador").
        """
        contagens: Dict[str, int] = {}
        termo_norm = self._normalize(termo)
        if not cartas or not termo_norm:
            return contagens
        pattern = self._word_boundary_pattern(termo_norm)
        for carta_id, carta in cartas.items():
            total = 0
            for field in campos:
                valor = carta.get(field)
                if not valor:
                    continue
                total += len(pattern.findall(self._normalize(str(valor))))
            if total > 0:
                contagens[carta_id] = total
        return contagens

    def get_stem_matches(
        self,
        stem_index: Dict,
        termo: str,
        search_fields: Optional[Set[str]] = None,
        cartas: Optional[Dict] = None
    ) -> Dict[str, int]:
        """
        Consulta o índice pré-computado para um termo, somando as contagens
        dos campos em `search_fields` (None = todos os campos indexados).

        Quando o radical de `termo` é curto demais (< MIN_STEM_LENGTH) para
        expandir com segurança por família de radical, ignora o índice e
        conta por substring exata (accent-insensível) sobre `cartas` --
        requer que `cartas` seja informado; sem ele, a salvaguarda não tem
        como escanear o texto e a consulta segue pelo índice normalmente.

        Returns:
            Dicionário carta_id -> número de ocorrências do termo/radical.
        """
        campos = tuple(search_fields) if search_fields is not None else tuple(stem_index.get('fields', DEFAULT_FIELDS))

        if not self.is_stem_reliable(termo) and cartas is not None:
            return self._exact_substring_matches(cartas, termo, campos)

        radical = self.stem(termo)
        index = stem_index.get('index', {})

        contagens: Dict[str, int] = {}
        for field in campos:
            por_carta = index.get(field, {}).get(radical)
            if not por_carta:
                continue
            for carta_id, n in por_carta.items():
                contagens[carta_id] = contagens.get(carta_id, 0) + n
        return contagens

    def get_forms(self, stem_index: Dict, termo: str) -> List[str]:
        """
        Formas de superfície (palavras reais da base) que compartilham o
        radical de `termo`. Para radicais curtos demais (< MIN_STEM_LENGTH),
        restringe às formas que de fato contêm `termo` como substring --
        evita listar palavras não-relacionadas que só colidem no radical
        (ex.: "jusante" para a busca "justiça").
        """
        radical = self.stem(termo)
        formas = stem_index.get('forms', {}).get(radical, [])

        if not self.is_stem_reliable(termo):
            termo_norm = self._normalize(termo)
            pattern = self._word_boundary_pattern(termo_norm)
            formas = [f for f in formas if pattern.fullmatch(self._normalize(f))]

        return formas

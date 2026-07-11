"""
Motor de busca semântica por embeddings.

Utiliza o modelo RoBERTa multilíngue (sentence-transformers/paraphrase-multilingual-mpnet-base-v2)
para encontrar cartas semanticamente relacionadas a uma consulta em linguagem
natural, mesmo sem compartilhar palavras exatas com os textos.

Fluxo de uso:
    1. compute_embeddings() — pré-computa e salva embeddings em cache .npz
    2. search() — codifica a query e retorna cartas por similaridade cosseno

O modelo RoBERTa produz vetores de 768 dimensões com janela de 512 tokens,
cobrindo 99% das cartas da base SAIC sem truncagem silenciosa.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


class SemanticEngine:
    """
    Motor de busca semântica usando embeddings RoBERTa.

    O carregamento do modelo é feito de forma lazy (somente quando necessário).
    Os embeddings pré-computados são armazenados em cache .npz para reutilização
    entre sessões, evitando recalcular ~70 mil vetores a cada inicialização.
    """

    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2', cache_dir: str = 'cache'):
        """
        Configura o motor semântico sem carregar o modelo.

        Args:
            model_name: Nome do modelo SentenceTransformer. Padrão: 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2' (RoBERTa).
                        O download (~420 MB) ocorre automaticamente na primeira
                        chamada a load_model().
            cache_dir:  Diretório onde os arquivos .npz de cache serão salvos.
                        Padrão: 'cache/' na raiz do projeto.
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self._model = None  # carregado sob demanda

    # ------------------------------------------------------------------ #
    # Métodos internos                                                     #
    # ------------------------------------------------------------------ #

    def _get_cache_path(self, db_name: str) -> Path:
        """
        Retorna o caminho do arquivo .npz de cache para uma base de dados.

        O nome é sanitizado removendo a extensão e substituindo caracteres
        especiais por underscores, garantindo nomes de arquivo válidos.

        Args:
            db_name: Nome do arquivo da base de dados (ex.: 'cartas_db.json').

        Returns:
            Objeto Path apontando para 'cache/embeddings_{nome}.npz'.
        """
        nome_sem_extensao = db_name.rsplit('.', 1)[0] if '.' in db_name else db_name
        # Substitui caracteres não alfanuméricos (exceto hífen) por underscore
        nome_seguro = re.sub(r'[^\w\-]', '_', nome_sem_extensao)
        return self.cache_dir / f"embeddings_{nome_seguro}.npz"

    def _is_cache_valid(self, cache_path: Path, carta_ids: List[str]) -> bool:
        """
        Verifica se o cache .npz está atualizado com a base de dados atual.

        A validação é feita comparando o conjunto de IDs armazenados no arquivo
        com os IDs das cartas atualmente carregadas. Se a base foi substituída
        ou complementada, o cache é considerado inválido.

        Args:
            cache_path: Caminho para o arquivo .npz.
            carta_ids:  Lista de IDs das cartas na base atual.

        Returns:
            True se o arquivo existir e os IDs coincidirem; False caso contrário.
        """
        if not cache_path.exists():
            return False
        try:
            dados = np.load(cache_path, allow_pickle=True)
            ids_cache = set(dados['ids'].tolist())
            return ids_cache == set(carta_ids)
        except Exception:
            return False

    def _build_text(self, carta: Dict) -> str:
        """
        Constrói o texto a ser codificado para uma carta.

        Concatena texto principal, catálogo temático e palavras de indexação
        com separador ' | ', ignorando campos vazios, None ou 'nan'.
        Limita o resultado a 1800 caracteres (~450 tokens estimados), garantindo
        margem segura dentro da janela de 512 tokens do RoBERTa.

        Args:
            carta: Dicionário com os dados de uma carta da base.

        Returns:
            Texto concatenado, limitado a 1800 caracteres.
        """
        partes = []
        _invalidos = {'', 'none', 'nan', 'n/a'}

        for campo in ('texto', 'catalogo', 'indexacao'):
            bruto = carta.get(campo)
            # Descartar None e float NaN antes de converter para string
            if bruto is None:
                continue
            try:
                if isinstance(bruto, float) and np.isnan(bruto):
                    continue
            except Exception:
                pass
            valor = str(bruto).strip()
            if valor.lower() not in _invalidos:
                partes.append(valor)

        return ' | '.join(partes)[:1800]

    # ------------------------------------------------------------------ #
    # Carregamento do modelo                                               #
    # ------------------------------------------------------------------ #

    def load_model(self):
        """
        Carrega o modelo SentenceTransformer na primeira chamada (lazy loading).

        O modelo é mantido em memória no atributo _model após o primeiro
        carregamento. Chamadas subsequentes retornam a instância existente.

        O download do RoBERTa (~420 MB) ocorre automaticamente via Hugging Face
        Hub e é armazenado em ~/.cache/huggingface/ no sistema local.

        Returns:
            Instância de SentenceTransformer pronta para codificação.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    # ------------------------------------------------------------------ #
    # Pré-computação de embeddings                                        #
    # ------------------------------------------------------------------ #

    def compute_embeddings(
        self,
        cartas: Dict,
        db_name: str,
        progress_callback=None,
        batch_size: int = 32
    ) -> Tuple[bool, str]:
        """
        Computa os embeddings de todas as cartas e salva em cache .npz.

        Processa as cartas em batches para evitar estouro de memória em
        execução local com CPU. O arquivo .npz resultante contém dois arrays:
        - 'embeddings': matriz float32 de shape (n, 768), normalizada L2.
        - 'ids':        array de strings com os IDs das cartas, na mesma ordem.

        Os embeddings são normalizados (norma L2 = 1) para que a similaridade
        cosseno seja computada via produto escalar simples na busca.

        Args:
            cartas:            Dicionário {id: dados} com todas as cartas da base.
            db_name:           Nome do arquivo da base (define o nome do cache).
            progress_callback: Função opcional chamada com (atual: int, total: int)
                               ao final de cada batch. Útil para barras de progresso.
            batch_size:        Número de cartas por batch de codificação. Padrão: 32.
                               Reduza para 16 em máquinas com pouca memória RAM.

        Returns:
            Tupla (sucesso: bool, mensagem: str).
            - Sucesso: (True, "N cartas indexadas · X.X MB salvo em arquivo.npz")
            - Falha:   (False, "Erro durante a computação: <descrição do erro>")
        """
        try:
            modelo = self.load_model()
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            ids = list(cartas.keys())
            textos = [self._build_text(carta) for carta in cartas.values()]
            total = len(ids)

            todos_embeddings = []

            for inicio in range(0, total, batch_size):
                fim = min(inicio + batch_size, total)
                batch_textos = textos[inicio:fim]

                batch_emb = modelo.encode(
                    batch_textos,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True  # norma L2 = 1 → produto escalar = cosseno
                )
                todos_embeddings.append(batch_emb.astype(np.float32))

                if progress_callback is not None:
                    progress_callback(fim, total)

            matriz = np.vstack(todos_embeddings)  # shape (n, 768)

            cache_path = self._get_cache_path(db_name)
            np.savez_compressed(
                cache_path,
                embeddings=matriz,
                ids=np.array(ids, dtype=object)
            )

            tamanho_mb = cache_path.stat().st_size / (1024 * 1024)
            return (
                True,
                f"{total:,} cartas indexadas · {tamanho_mb:.1f} MB salvo em {cache_path.name}"
            )

        except Exception as e:
            return False, f"Erro durante a computação: {str(e)}"

    # ------------------------------------------------------------------ #
    # Carregamento do cache                                                #
    # ------------------------------------------------------------------ #

    def get_embeddings(
        self,
        cartas: Dict,
        db_name: str
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Carrega os embeddings pré-computados do cache .npz.

        Nunca dispara computação automaticamente — se o cache não existir
        ou estiver desatualizado, lança FileNotFoundError com orientação clara.
        A computação deve ser iniciada exclusivamente pelo botão na interface.

        Args:
            cartas:  Dicionário {id: dados} com as cartas atuais (para validação).
            db_name: Nome do arquivo da base de dados.

        Returns:
            Tupla (matriz_embeddings: np.ndarray, lista_ids: list[str]).
            A matriz tem shape (n, 768) com vetores normalizados L2.

        Raises:
            FileNotFoundError: Se o cache não existir ou os IDs divergirem
                               da base atual. A mensagem inclui orientação de uso.
        """
        cache_path = self._get_cache_path(db_name)
        carta_ids = list(cartas.keys())

        if not cache_path.exists():
            raise FileNotFoundError(
                f"Cache não encontrado para '{db_name}'. "
                "Use o botão '⚡ Pré-computar Embeddings' na aba Busca Semântica."
            )

        if not self._is_cache_valid(cache_path, carta_ids):
            raise FileNotFoundError(
                f"Cache desatualizado para '{db_name}' "
                "(a base foi alterada desde a última indexação). "
                "Use o botão '⚡ Pré-computar Embeddings' para reindexar."
            )

        dados = np.load(cache_path, allow_pickle=True)
        embeddings = dados['embeddings']      # shape (n, 768), float32
        ids = dados['ids'].tolist()           # list[str]
        return embeddings, ids

    # ------------------------------------------------------------------ #
    # Busca semântica                                                      #
    # ------------------------------------------------------------------ #

    def search(
        self,
        query: str,
        cartas: Dict,
        db_name: str,
        top_k: int = 99999,
        threshold: float = 0.35
    ) -> List[Tuple[str, float]]:
        """
        Executa busca semântica por similaridade cosseno.

        Codifica a query com o modelo RoBERTa, carrega os embeddings do cache
        e calcula a similaridade cosseno de forma vetorizada com numpy
        (produto escalar de vetores normalizados — sem loops Python).

        Args:
            query:     Consulta em linguagem natural (ex.: "medo da ditadura voltar").
            cartas:    Dicionário {id: dados} com as cartas da base.
            db_name:   Nome do arquivo da base de dados.
            top_k:     Número máximo de resultados a retornar. Padrão: 99999 (sem limite prático).
                       O filtro visual é aplicado via threshold na interface do usuário.
            threshold: Score mínimo de similaridade cosseno (0.0 a 1.0).
                       Padrão: 0.35 (equilibra precisão e cobertura para o RoBERTa).
                       Na interface, o threshold é aplicado dinamicamente via slider.

        Returns:
            Lista de tuplas (carta_id: str, score: float) ordenada por score
            decrescente, filtrada pelo threshold e limitada a top_k resultados.

        Raises:
            FileNotFoundError: Propagado de get_embeddings() se o cache não existir.
        """
        modelo = self.load_model()
        embeddings, ids = self.get_embeddings(cartas, db_name)

        # Codifica e normaliza a query (norma L2 = 1)
        query_emb = modelo.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]  # shape (768,)

        # Similaridade cosseno vetorizada: produto escalar com embeddings normalizados
        scores = embeddings @ query_emb  # shape (n,), float32

        # Filtrar por threshold
        indices_validos = np.where(scores >= threshold)[0]

        # Ordenar por score decrescente
        ordem = np.argsort(scores[indices_validos])[::-1]
        indices_ordenados = indices_validos[ordem]

        # Limitar a top_k
        indices_top = indices_ordenados[:top_k]

        return [(ids[i], float(scores[i])) for i in indices_top]

    # ------------------------------------------------------------------ #
    # Status do motor                                                      #
    # ------------------------------------------------------------------ #

    def get_status(self, db_name: str, cartas: Dict) -> Dict:
        """
        Retorna o status atual do motor semântico para uma base de dados.

        Informa se o modelo está em memória, se o cache existe e se está
        atualizado com a base atual — sem disparar nenhuma computação.

        Args:
            db_name: Nome do arquivo da base de dados.
            cartas:  Dicionário {id: dados} para validação do cache.

        Returns:
            Dicionário com as chaves:
                - modelo_carregado (bool):  Se o modelo RoBERTa está em memória.
                - cache_existe (bool):      Se o arquivo .npz existe em disco.
                - cache_valido (bool):      Se o cache está atualizado com a base.
                - total_indexado (int):     Número de cartas indexadas no cache.
                - tamanho_mb (float):       Tamanho do arquivo .npz em megabytes.
        """
        cache_path = self._get_cache_path(db_name)
        carta_ids = list(cartas.keys())

        cache_existe = cache_path.exists()
        cache_valido = False
        total_indexado = 0
        tamanho_mb = 0.0

        if cache_existe:
            try:
                dados = np.load(cache_path, allow_pickle=True)
                ids_cache = dados['ids'].tolist()
                total_indexado = len(ids_cache)
                cache_valido = set(ids_cache) == set(carta_ids)
                tamanho_mb = cache_path.stat().st_size / (1024 * 1024)
            except Exception:
                cache_existe = False

        return {
            'modelo_carregado': self._model is not None,
            'cache_existe': cache_existe,
            'cache_valido': cache_valido,
            'total_indexado': total_indexado,
            'tamanho_mb': tamanho_mb,
        }

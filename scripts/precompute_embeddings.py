#!/usr/bin/env python3
"""
Script CLI para pré-computar embeddings semânticos das cartas históricas.

Carrega a base de dados JSON, computa os embeddings de cada carta usando
o modelo RoBERTa e salva o resultado em cache .npz no diretório cache/.

Este script deve ser executado uma única vez por base de dados. O app
Streamlit carregará o cache automaticamente nas execuções seguintes.

Uso:
    # Base padrão (cartas_db.json)
    python scripts/precompute_embeddings.py

    # Base alternativa
    python scripts/precompute_embeddings.py --db bases/cartas_db_hist_claude.json

    # Ajuste de batch para máquinas com pouca memória RAM
    python scripts/precompute_embeddings.py --batch 16

    # Modelo alternativo (para testes)
    python scripts/precompute_embeddings.py --model paraphrase-multilingual-MiniLM-L12-v2

Estimativas para a base completa (~72 mil cartas) com RoBERTa em CPU:
    - 1ª execução: download do modelo (~420 MB) + codificação (~15–35 min)
    - Execuções seguintes: somente codificação (~15–35 min)
    - Arquivo de cache gerado: ~212 MB (72k cartas × 768 dims × float32)
"""

import argparse
import sys
import time
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path para importar os módulos
_RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(_RAIZ))

try:
    from tqdm import tqdm
except ImportError:
    print("❌ tqdm não encontrado. Instale com: pip install tqdm")
    sys.exit(1)

from modules.data_manager import DataManager
from modules.semantic_engine import SemanticEngine


def main() -> None:
    """Ponto de entrada do script de pré-computação."""

    parser = argparse.ArgumentParser(
        description='Pré-computa embeddings semânticos para a base de cartas históricas.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--db',
        default='cartas_db.json',
        metavar='ARQUIVO',
        help='Caminho do arquivo JSON da base de dados (padrão: cartas_db.json)'
    )
    parser.add_argument(
        '--model',
        default='sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        metavar='MODELO',
        help='Nome do modelo SentenceTransformer (padrão: sentence-transformers/paraphrase-multilingual-mpnet-base-v2 - RoBERTa)'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=32,
        metavar='N',
        help='Tamanho do batch para codificação (padrão: 32; reduza para 16 se faltar RAM)'
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------ #
    # Verifica o arquivo da base de dados                                 #
    # ------------------------------------------------------------------ #
    db_path = Path(args.db)
    if not db_path.is_absolute():
        # Resolve relativo à raiz do projeto
        db_path = _RAIZ / db_path

    if not db_path.exists():
        print(f"\n❌ Arquivo não encontrado: {db_path}")
        print(f"   Certifique-se de executar o script a partir da raiz do projeto.")
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # Carrega a base de dados                                             #
    # ------------------------------------------------------------------ #
    print(f"\n{'='*60}")
    print(f"  Historicidades Democráticas — Pré-computação de Embeddings")
    print(f"{'='*60}\n")

    print(f"📂 Carregando base de dados: {db_path.name}")
    dm = DataManager(data_dir=str(db_path.parent))
    sucesso, msg = dm.load_database(db_path.name)

    if not sucesso:
        print(f"❌ Erro ao carregar base: {msg}")
        sys.exit(1)

    cartas = dm.get_todas_cartas()
    total = len(cartas)
    print(f"✅ {total:,} cartas carregadas.\n")

    # ------------------------------------------------------------------ #
    # Instancia o motor e carrega o modelo                                #
    # ------------------------------------------------------------------ #
    engine = SemanticEngine(model_name=args.model)

    print(f"🤖 Carregando modelo: {args.model}")
    print(f"   (O download ocorre apenas na primeira execução.)")
    print(f"   RoBERTa: ~420 MB · armazenado em ~/.cache/huggingface/\n")

    t_inicio_modelo = time.time()
    engine.load_model()
    t_modelo = time.time() - t_inicio_modelo
    print(f"✅ Modelo carregado em {t_modelo:.1f}s.\n")

    # ------------------------------------------------------------------ #
    # Verifica se já existe cache válido                                  #
    # ------------------------------------------------------------------ #
    cache_path = engine._get_cache_path(db_path.name)
    if engine._is_cache_valid(cache_path, list(cartas.keys())):
        tamanho_mb = cache_path.stat().st_size / (1024 * 1024)
        print(f"ℹ️  Cache já existe e está atualizado: {cache_path.name} ({tamanho_mb:.1f} MB)")
        print(f"   Para reindexar, delete o arquivo e execute o script novamente.\n")
        resp = input("Deseja reindexar mesmo assim? [s/N] ").strip().lower()
        if resp != 's':
            print("Operação cancelada.")
            sys.exit(0)
        print()

    # ------------------------------------------------------------------ #
    # Pré-computação com barra de progresso                               #
    # ------------------------------------------------------------------ #
    print(f"⚡ Iniciando computação (batch={args.batch})...")
    print(f"   Isso pode levar entre 15 e 40 minutos em CPU.\n")

    pbar = tqdm(
        total=total,
        desc="Embeddings",
        unit="carta",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
    )

    # Acumula progresso entre batches (callback recebe total acumulado)
    _anterior = [0]

    def callback_progresso(atual: int, total_c: int) -> None:
        incremento = atual - _anterior[0]
        pbar.update(incremento)
        _anterior[0] = atual

    t_inicio = time.time()
    ok, msg_resultado = engine.compute_embeddings(
        cartas=cartas,
        db_name=db_path.name,
        progress_callback=callback_progresso,
        batch_size=args.batch
    )
    pbar.close()

    tempo_total = time.time() - t_inicio

    # ------------------------------------------------------------------ #
    # Relatório final                                                      #
    # ------------------------------------------------------------------ #
    print()
    if ok:
        cache_gerado = engine._get_cache_path(db_path.name)
        tamanho_mb = cache_gerado.stat().st_size / (1024 * 1024)

        print(f"{'='*60}")
        print(f"✅ Embeddings computados com sucesso!")
        print(f"   Total de cartas indexadas : {total:,}")
        print(f"   Modelo utilizado          : {args.model}")
        print(f"   Tamanho do batch          : {args.batch}")
        print(f"   Tempo total               : {tempo_total:.1f}s ({tempo_total / 60:.1f} min)")
        print(f"   Arquivo de cache          : {cache_gerado}")
        print(f"   Tamanho do arquivo        : {tamanho_mb:.1f} MB")
        print(f"{'='*60}\n")
        print("O app Streamlit carregará este cache automaticamente.")
        print("Execute: streamlit run app.py\n")
    else:
        print(f"{'='*60}")
        print(f"❌ Falha na computação: {msg_resultado}")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()

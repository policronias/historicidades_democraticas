#!/usr/bin/env python3
"""
Consolida multiplos CSVs exportados pela busca semantica em uma unica tabela.

Cada arquivo .csv em --pasta e tratado como uma query diferente, usando o
nome do arquivo (sem extensao) como identificador da query.

Formato esperado dos CSVs de entrada (delimitador ';'):
    rank;id;nome;uf;catalogo;score;texto

Saida (em exports/ por padrao):
    consolidado_completo.csv  -- todas as cartas encontradas, com metricas
    consolidado_tier1.csv     -- apenas Tier 1 (n_queries >= 4)

Tiers:
    Tier 1: n_queries >= 4  -> leitura prioritaria
    Tier 2: n_queries 2-3   -> leitura secundaria
    Tier 3: n_queries == 1  -> contexto quantitativo

Uso:
    python scripts/consolidar_buscas.py
    python scripts/consolidar_buscas.py --pasta exports/rodada_01
    python scripts/consolidar_buscas.py --pasta exports/ --saida exports/

Dependencias: apenas pandas e pathlib (stdlib).
"""

import argparse
import sys
from pathlib import Path

# Força UTF-8 no stdout para exibir acentos corretamente no Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import pandas as pd
except ImportError:
    print("ERRO: pandas nao encontrado. Instale com: pip install pandas")
    sys.exit(1)


# ─────────────────────────────────────────────
# Classificacao por tier (baseada em n_queries)
# ─────────────────────────────────────────────
# Tier 1: n_queries == 7  -> nucleo duro (todas as queries)
# Tier 2: n_queries == 6  -> alta cobertura
# Tier 3: n_queries == 5  -> cobertura intermediaria
# Tier 4: n_queries <= 4  -> cobertura parcial


def _classificar_tier(n: int) -> str:
    if n == 7:
        return "Tier 1"
    if n == 6:
        return "Tier 2"
    if n == 5:
        return "Tier 3"
    return "Tier 4"


def carregar_csvs(pasta: Path) -> pd.DataFrame:
    """Le todos os .csv da pasta e retorna um DataFrame com coluna 'query'."""
    arquivos = sorted(pasta.glob("*.csv"))
    # Ignora arquivos de saida anteriores desta ferramenta
    arquivos = [
        f for f in arquivos
        if f.stem not in ("consolidado_completo", "consolidado_tier1", "consolidado_nucleo")
    ]

    if not arquivos:
        print(f"ERRO: Nenhum arquivo .csv encontrado em: {pasta.resolve()}")
        sys.exit(1)

    partes = []
    sep = "-" * 60
    print(f"\n{sep}")
    print(f"  Arquivos encontrados em '{pasta}':")
    print(sep)

    for arq in arquivos:
        query_nome = arq.stem
        try:
            df = pd.read_csv(
                arq,
                delimiter=';',
                dtype=str,
                encoding='utf-8-sig',    # aceita BOM (exportacao Windows)
            )
            # Normaliza nomes de colunas (strip de espacos, lower)
            df.columns = [c.strip().lower() for c in df.columns]

            # Valida colunas minimas obrigatorias
            colunas_req = {'id', 'score'}
            faltando = colunas_req - set(df.columns)
            if faltando:
                print(f"  AVISO: {arq.name}: colunas ausentes {faltando} - ignorado")
                continue

            df['query'] = query_nome
            partes.append(df)
            print(f"  OK  {arq.name:45s} -> {len(df):>5} linhas  (query: '{query_nome}')")

        except Exception as exc:
            print(f"  AVISO: {arq.name}: erro ao ler - {exc} - ignorado")

    print(sep)

    if not partes:
        print("ERRO: Nenhum CSV pode ser lido com sucesso.")
        sys.exit(1)

    df_total = pd.concat(partes, ignore_index=True)
    print(f"\n  Total de linhas brutas carregadas: {len(df_total):,}")
    return df_total


def consolidar(df_total: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa por ID de carta e calcula as metricas de consolidacao.

    Retorna um DataFrame com uma linha por carta, ordenado por
    n_queries desc -> score_medio desc.
    """
    # Garante que 'score' seja numerico; linhas invalidas viram NaN e sao dropadas
    df_total['score'] = pd.to_numeric(df_total['score'], errors='coerce')
    df_total = df_total.dropna(subset=['score'])
    df_total['id'] = df_total['id'].astype(str).str.strip()

    # Normaliza catalogo: remove ponto final para unificar "NOME." com "NOME"
    # Ex.: "ORGANIZACAO SOCIAL." -> "ORGANIZACAO SOCIAL"
    if 'catalogo' in df_total.columns:
        df_total['catalogo'] = (
            df_total['catalogo']
            .astype(str)
            .str.strip()
            .str.rstrip('.')
            .str.strip()
        )

    # ── Metricas por carta ──────────────────────────────────────────────
    def agregar(grupo: pd.DataFrame) -> pd.Series:
        # Linha com maior score (fonte de nome, uf, catalogo, texto)
        melhor = grupo.loc[grupo['score'].idxmax()]

        queries_unicas = sorted(grupo['query'].unique().tolist())

        return pd.Series({
            'n_queries':    len(queries_unicas),
            'queries':      ' | '.join(queries_unicas),
            'score_max':    round(grupo['score'].max(), 4),
            'score_medio':  round(grupo['score'].mean(), 4),
            'nome':         melhor.get('nome', ''),
            'uf':           melhor.get('uf', ''),
            'catalogo':     melhor.get('catalogo', ''),
            'texto':        melhor.get('texto', ''),
        })

    print("\n  Consolidando por ID de carta...", end=' ', flush=True)
    df_cons = df_total.groupby('id', sort=False).apply(agregar).reset_index()
    print(f"-> {len(df_cons):,} cartas unicas")

    # ── Ordenacao ──────────────────────────────────────────────────────
    df_cons = df_cons.sort_values(
        ['n_queries', 'score_medio'],
        ascending=[False, False]
    ).reset_index(drop=True)

    # ── Tier ──────────────────────────────────────────────────────────
    df_cons['tier'] = df_cons['n_queries'].apply(_classificar_tier)

    # ── Reordenar colunas de forma legivel ────────────────────────────
    colunas_saida = [
        'id', 'tier', 'n_queries', 'score_max', 'score_medio',
        'queries', 'nome', 'uf', 'catalogo', 'texto',
    ]
    # Mantém apenas colunas que existem (robustez)
    colunas_saida = [c for c in colunas_saida if c in df_cons.columns]
    df_cons = df_cons[colunas_saida]

    return df_cons


def exportar(df_cons: pd.DataFrame, pasta_saida: Path) -> None:
    """Salva consolidado_completo.csv, consolidado_tier1.csv e consolidado_nucleo.csv."""
    pasta_saida.mkdir(parents=True, exist_ok=True)

    path_completo = pasta_saida / "consolidado_completo.csv"
    path_tier1    = pasta_saida / "consolidado_tier1.csv"
    path_nucleo   = pasta_saida / "consolidado_nucleo.csv"

    df_tier1 = df_cons[df_cons['tier'] == 'Tier 1'].copy()

    # Nucleo: apenas cartas presentes em todas as 7 queries, por score_medio desc
    df_nucleo = (
        df_cons[df_cons['n_queries'] == 7]
        .sort_values('score_medio', ascending=False)
        .copy()
    )

    df_cons.to_csv(path_completo, index=False, encoding='utf-8-sig', sep=';')
    df_tier1.to_csv(path_tier1,   index=False, encoding='utf-8-sig', sep=';')
    df_nucleo.to_csv(path_nucleo, index=False, encoding='utf-8-sig', sep=';')

    print(f"\n  Exportado: {path_completo.resolve()}")
    print(f"  Exportado: {path_tier1.resolve()}")
    print(f"  Exportado: {path_nucleo.resolve()}  ({len(df_nucleo):,} cartas nucleo)")


def imprimir_resumo(df_cons: pd.DataFrame) -> None:
    """Imprime o resumo analitico final."""
    tier_counts = df_cons['tier'].value_counts().sort_index()

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  RESUMO DA CONSOLIDACAO")
    print(f"{sep}")

    print(f"\n  Total de cartas unicas encontradas: {len(df_cons):,}")

    print(f"\n  Quantidade por tier:")
    for tier, label in [
        ('Tier 1', '(n_queries == 7, nucleo duro — todas as queries)'),
        ('Tier 2', '(n_queries == 6, alta cobertura)'),
        ('Tier 3', '(n_queries == 5, cobertura intermediaria)'),
        ('Tier 4', '(n_queries <= 4, cobertura parcial)'),
    ]:
        n = tier_counts.get(tier, 0)
        print(f"    {tier}: {n:>5,}  {label}")

    print(f"\n  Distribuicao por numero de queries:")
    max_queries = int(df_cons['n_queries'].max())
    for n_q in range(1, max_queries + 1):
        n_cartas = int((df_cons['n_queries'] == n_q).sum())
        if n_cartas == 0:
            continue
        barra = '#' * min(n_cartas, 40)
        label_q = 'query  ' if n_q == 1 else 'queries'
        print(f"    {n_q:>2} {label_q}: {n_cartas:>5,}  {barra}")

    # Top 10 catalogos no Tier 1
    df_tier1 = df_cons[df_cons['tier'] == 'Tier 1']

    if not df_tier1.empty and 'catalogo' in df_tier1.columns:
        # Catalogo pode ter multiplos valores separados por virgula ou ponto e virgula
        catalogos_raw = df_tier1['catalogo'].dropna().astype(str)
        catalogos_expandidos = (
            catalogos_raw
            .str.replace(';', ',', regex=False)
            .str.split(',')
            .explode()
            .str.strip()
        )
        catalogos_expandidos = catalogos_expandidos[catalogos_expandidos != '']
        top_catalogos = catalogos_expandidos.value_counts().head(10)

        if not top_catalogos.empty:
            print(f"\n  Top 10 catalogos tematicos no Tier 1:")
            for i, (cat, cnt) in enumerate(top_catalogos.items(), 1):
                print(f"    {i:>2}. {cat:<45} {cnt:>4} cartas")
        else:
            print("\n  (Nenhum catalogo disponivel para as cartas Tier 1.)")
    else:
        print("\n  (Sem cartas Tier 1 ou coluna 'catalogo' ausente.)")

    print(f"\n{sep}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Consolida CSVs de busca semantica em tabela unificada com tiers.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--pasta',
        default='exports',
        metavar='PASTA',
        help='Pasta com os arquivos .csv a consolidar (padrao: exports/)'
    )
    parser.add_argument(
        '--saida',
        default=None,
        metavar='PASTA_SAIDA',
        help=(
            'Pasta onde salvar os CSVs consolidados '
            '(padrao: mesma que --pasta)'
        )
    )
    args = parser.parse_args()

    # ── Resolve caminhos relativos a raiz do projeto ─────────────────────
    raiz = Path(__file__).parent.parent
    pasta = Path(args.pasta)
    if not pasta.is_absolute():
        pasta = raiz / pasta

    if not pasta.exists() or not pasta.is_dir():
        print(f"ERRO: Pasta nao encontrada: {pasta.resolve()}")
        sys.exit(1)

    pasta_saida = Path(args.saida) if args.saida else pasta
    if not pasta_saida.is_absolute():
        pasta_saida = raiz / pasta_saida

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  Historicidades Democraticas -- Consolidacao de Buscas")
    print(f"{sep}")
    print(f"\n  Pasta de entrada : {pasta.resolve()}")
    print(f"  Pasta de saida   : {pasta_saida.resolve()}")

    # ── Pipeline ──────────────────────────────────────────────────────────
    df_total = carregar_csvs(pasta)
    df_cons  = consolidar(df_total)
    exportar(df_cons, pasta_saida)
    imprimir_resumo(df_cons)


if __name__ == '__main__':
    main()

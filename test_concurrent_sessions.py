"""
Teste manual de concorrência — simula duas escritas simultâneas em sessions/current_session.json
"""

import os
import json
import threading
import time
import shutil
from pathlib import Path

# Usa diretório temporário para teste
test_session_dir = Path('sessions_test')
test_session_dir.mkdir(exist_ok=True)
session_file = test_session_dir / 'current_session.json'

# Limpa antes de começar
if session_file.exists():
    session_file.unlink()

# Importa os managers
from modules.annotation_manager import AnnotationManager
from modules.series_manager import SeriesManager


def thread_annotations():
    """Thread 1: adiciona anotações para 5 cartas diferentes"""
    am = AnnotationManager(str(session_file))

    for i in range(5):
        am.set_anotacao(f"carta_{i}", f"Anotação da carta {i} (thread 1)")
        time.sleep(0.1)  # Pequeno delay para aumentar chance de concorrência

    print("✓ Thread 1 (anotações) concluída: 5 anotações salvas")


def thread_series():
    """Thread 2: cria séries e adiciona cartas"""
    sm = SeriesManager(str(session_file))

    # Cria 3 séries
    series_names = ["Série A", "Série B", "Série C"]
    for serie in series_names:
        sm.criar_serie(serie, f"Descrição de {serie}")
        time.sleep(0.1)

    # Adiciona cartas às séries
    for i, serie in enumerate(series_names):
        for j in range(3):
            sm.adicionar_carta_serie(serie, f"carta_{i}_{j}")

    print("✓ Thread 2 (séries) concluída: 3 séries criadas, 9 cartas adicionadas")


def verify_result():
    """Verifica que todas as mudanças foram preservadas"""
    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    anotacoes = data.get('anotacoes', {})
    series = data.get('series', {})

    print(f"\n📊 Resultado final:")
    print(f"  Anotações salvas: {len(anotacoes)}")
    print(f"  Séries criadas: {len(series)}")

    # Verifica anotações
    expected_annotations = 5
    if len(anotacoes) == expected_annotations:
        print(f"  ✓ Todas as {expected_annotations} anotações foram preservadas")
    else:
        print(f"  ✗ PERDEU ANOTAÇÕES! Esperava {expected_annotations}, tem {len(anotacoes)}")
        print(f"    Anotações: {anotacoes}")
        return False

    # Verifica séries
    expected_series = 3
    if len(series) == expected_series:
        print(f"  ✓ Todas as {expected_series} séries foram preservadas")
    else:
        print(f"  ✗ PERDEU SÉRIES! Esperava {expected_series}, tem {len(series)}")
        return False

    # Verifica cartas nas séries
    total_cartas_em_series = sum(len(s['cartas']) for s in series.values())
    expected_cartas = 9
    if total_cartas_em_series == expected_cartas:
        print(f"  ✓ Todas as {expected_cartas} cartas foram preservadas nas séries")
    else:
        print(f"  ✗ PERDEU CARTAS! Esperava {expected_cartas}, tem {total_cartas_em_series}")
        return False

    print(f"\n✅ SUCESSO: Nenhuma perda de dados com concorrência!")
    return True


if __name__ == '__main__':
    print("🧪 Teste de concorrência — 2 threads escrevendo simultaneamente\n")

    # Cria threads
    t1 = threading.Thread(target=thread_annotations, daemon=False)
    t2 = threading.Thread(target=thread_series, daemon=False)

    # Inicia simultaneamente
    start = time.time()
    t1.start()
    t2.start()

    # Aguarda conclusão
    t1.join()
    t2.join()
    elapsed = time.time() - start

    print(f"\n⏱️  Tempo total: {elapsed:.2f}s")

    # Verifica resultado
    success = verify_result()

    # Limpa
    shutil.rmtree(test_session_dir)

    exit(0 if success else 1)

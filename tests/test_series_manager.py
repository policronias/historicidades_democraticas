"""
Testes unitários para SeriesManager.
Cobertura: CRUD de séries, índice invertido, persistência.
"""

import pytest
import os
import json
from modules.series_manager import SeriesManager


class TestCriarSerie:
    """Testes para criação de série."""

    def test_criar_serie_simples(self, session_file):
        """Criar uma série simples."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.criar_serie("Série A", "Descrição de teste")

        assert sucesso is True
        assert "Série A" in manager.series
        assert manager.series["Série A"]["descricao"] == "Descrição de teste"

    def test_criar_serie_sem_descricao(self, session_file):
        """Criar série sem descrição."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.criar_serie("Série B")

        assert sucesso is True
        assert "Série B" in manager.series
        assert manager.series["Série B"]["descricao"] == ""

    def test_criar_serie_duplicada(self, session_file):
        """Criar série com nome duplicado deve falhar."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série C")
        sucesso, mensagem = manager.criar_serie("Série C")

        assert sucesso is False
        assert "já existe" in mensagem.lower()

    def test_criar_serie_nome_vazio(self, session_file):
        """Criar série com nome vazio deve falhar."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.criar_serie("")

        assert sucesso is False
        assert "vazio" in mensagem.lower()

    def test_criar_serie_salva_em_arquivo(self, session_file):
        """Criar série persiste em arquivo."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série D")

        # Recarregar manager
        manager2 = SeriesManager(session_file)
        assert "Série D" in manager2.series


class TestDeletarSerie:
    """Testes para deleção de série."""

    def test_deletar_serie(self, session_file):
        """Deletar uma série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série E")
        sucesso, mensagem = manager.deletar_serie("Série E")

        assert sucesso is True
        assert "Série E" not in manager.series

    def test_deletar_serie_inexistente(self, session_file):
        """Deletar série inexistente deve falhar."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.deletar_serie("Série Inexistente")

        assert sucesso is False
        assert "não encontrada" in mensagem.lower()

    def test_deletar_serie_com_cartas(self, session_file):
        """Deletar série com cartas vinculadas."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série F")
        manager.adicionar_carta_serie("Série F", "1")
        manager.adicionar_carta_serie("Série F", "2")

        sucesso, mensagem = manager.deletar_serie("Série F")

        assert sucesso is True
        assert "Série F" not in manager.series
        # Verificar que o índice foi atualizado
        assert "1" not in manager._carta_index or "Série F" not in manager._carta_index["1"]


class TestRenomearSerie:
    """Testes para renomeação de série."""

    def test_renomear_serie(self, session_file):
        """Renomear uma série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série G")
        sucesso, mensagem = manager.renomear_serie("Série G", "Série G Renomeada")

        assert sucesso is True
        assert "Série G" not in manager.series
        assert "Série G Renomeada" in manager.series

    def test_renomear_serie_inexistente(self, session_file):
        """Renomear série inexistente deve falhar."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.renomear_serie("Série Inexistente", "Nova")

        assert sucesso is False
        assert "não encontrada" in mensagem.lower()

    def test_renomear_serie_para_nome_existente(self, session_file):
        """Renomear série para nome que já existe deve falhar."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série H1")
        manager.criar_serie("Série H2")
        sucesso, mensagem = manager.renomear_serie("Série H1", "Série H2")

        assert sucesso is False
        assert "já existe" in mensagem.lower()

    def test_renomear_serie_com_cartas(self, session_file):
        """Renomear série com cartas vinculadas."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série I")
        manager.adicionar_carta_serie("Série I", "1")

        sucesso, mensagem = manager.renomear_serie("Série I", "Série I Renomeada")

        assert sucesso is True
        # Verificar que as cartas foram movidas
        assert "1" in manager._carta_index
        assert "Série I" not in manager._carta_index["1"]
        assert "Série I Renomeada" in manager._carta_index["1"]


class TestAdicionarCartaSerie:
    """Testes para adicionar carta a série."""

    def test_adicionar_carta_serie(self, session_file):
        """Adicionar carta a série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série J")
        sucesso, mensagem = manager.adicionar_carta_serie("Série J", "1")

        assert sucesso is True
        assert "1" in manager.series["Série J"]["cartas"]

    def test_adicionar_carta_serie_inexistente(self, session_file):
        """Adicionar carta a série inexistente deve falhar."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.adicionar_carta_serie("Série Inexistente", "1")

        assert sucesso is False
        assert "não encontrada" in mensagem.lower()

    def test_adicionar_carta_indice_invertido(self, session_file):
        """Adicionar carta atualiza índice invertido."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série K")
        manager.adicionar_carta_serie("Série K", "5")

        # Verificar índice invertido
        assert "5" in manager._carta_index
        assert "Série K" in manager._carta_index["5"]

    def test_adicionar_multiplas_cartas(self, session_file):
        """Adicionar múltiplas cartas a série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série L")
        manager.adicionar_carta_serie("Série L", "1")
        manager.adicionar_carta_serie("Série L", "2")
        manager.adicionar_carta_serie("Série L", "3")

        cartas = manager.get_cartas_serie("Série L")
        assert len(cartas) == 3
        assert "1" in cartas
        assert "2" in cartas
        assert "3" in cartas

    def test_adicionar_carta_duplicate(self, session_file):
        """Adicionar mesma carta duas vezes (deve ser idempotente via set)."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série M")
        manager.adicionar_carta_serie("Série M", "1")
        manager.adicionar_carta_serie("Série M", "1")  # Adicionar novamente

        cartas = manager.get_cartas_serie("Série M")
        assert len(cartas) == 1  # Set evita duplicatas


class TestRemoverCartaSerie:
    """Testes para remover carta de série."""

    def test_remover_carta_serie(self, session_file):
        """Remover carta de série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série N")
        manager.adicionar_carta_serie("Série N", "1")
        sucesso, mensagem = manager.remover_carta_serie("Série N", "1")

        assert sucesso is True
        assert "1" not in manager.series["Série N"]["cartas"]

    def test_remover_carta_serie_inexistente(self, session_file):
        """Remover carta de série inexistente deve falhar."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.remover_carta_serie("Série Inexistente", "1")

        assert sucesso is False
        assert "não encontrada" in mensagem.lower()

    def test_remover_carta_indice_invertido(self, session_file):
        """Remover carta atualiza índice invertido."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série O")
        manager.adicionar_carta_serie("Série O", "1")
        manager.remover_carta_serie("Série O", "1")

        # Verificar índice invertido
        assert "1" not in manager._carta_index or "Série O" not in manager._carta_index.get("1", set())

    def test_remover_carta_inexistente_de_serie(self, session_file):
        """Remover carta que não está na série (deve ser seguro via discard)."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série P")
        manager.adicionar_carta_serie("Série P", "1")
        sucesso, mensagem = manager.remover_carta_serie("Série P", "99")  # Não existe

        assert sucesso is True  # discard não lança erro


class TestAtualizarSeriesCarta:
    """Testes para reconciliação de séries de uma carta."""

    def test_atualizar_series_carta_adicionar(self, session_file):
        """Atualizar séries: adicionar série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série Q")
        manager.atualizar_series_carta("1", ["Série Q"])

        assert "1" in manager._carta_index
        assert "Série Q" in manager._carta_index["1"]

    def test_atualizar_series_carta_remover(self, session_file):
        """Atualizar séries: remover série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série R")
        manager.adicionar_carta_serie("Série R", "1")
        manager.atualizar_series_carta("1", [])

        assert "1" not in manager._carta_index or "Série R" not in manager._carta_index.get("1", set())

    def test_atualizar_series_carta_multiplas(self, session_file):
        """Atualizar séries: múltiplas séries."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série S1")
        manager.criar_serie("Série S2")
        manager.criar_serie("Série S3")
        manager.atualizar_series_carta("1", ["Série S1", "Série S2"])

        series = manager.get_series_carta("1")
        assert len(series) == 2
        assert "Série S1" in series
        assert "Série S2" in series
        assert "Série S3" not in series

    def test_atualizar_series_carta_reconcialiacao(self, session_file):
        """Atualizar séries: reconciliação completa."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série T1")
        manager.criar_serie("Série T2")
        manager.criar_serie("Série T3")

        # Adicionar a T1 e T2
        manager.atualizar_series_carta("1", ["Série T1", "Série T2"])

        # Atualizar para T2 e T3 (T1 removida, T3 adicionada)
        sucesso, mensagem = manager.atualizar_series_carta("1", ["Série T2", "Série T3"])

        assert sucesso is True
        series = manager.get_series_carta("1")
        assert len(series) == 2
        assert "Série T1" not in series
        assert "Série T2" in series
        assert "Série T3" in series

    def test_atualizar_series_carta_save_uma_vez(self, session_file):
        """Atualizar séries: salva uma única vez independente de mudanças."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série U")

        # Múltiplas mudanças
        sucesso, mensagem = manager.atualizar_series_carta("1", ["Série U"])

        # Verificar que arquivo foi salvo (recarregar)
        manager2 = SeriesManager(session_file)
        series = manager2.get_series_carta("1")
        assert "Série U" in series


class TestGetSeries:
    """Testes para obter séries."""

    def test_get_series_carta(self, session_file):
        """Get séries de uma carta."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série V1")
        manager.criar_serie("Série V2")
        manager.adicionar_carta_serie("Série V1", "1")
        manager.adicionar_carta_serie("Série V2", "1")

        series = manager.get_series_carta("1")
        assert len(series) == 2
        assert "Série V1" in series
        assert "Série V2" in series

    def test_get_series_carta_ordenado(self, session_file):
        """Get séries retorna lista ordenada."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Zebra")
        manager.criar_serie("Alpha")
        manager.adicionar_carta_serie("Zebra", "1")
        manager.adicionar_carta_serie("Alpha", "1")

        series = manager.get_series_carta("1")
        assert series == sorted(series)

    def test_get_cartas_serie(self, session_file):
        """Get cartas de uma série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série W")
        manager.adicionar_carta_serie("Série W", "5")
        manager.adicionar_carta_serie("Série W", "3")
        manager.adicionar_carta_serie("Série W", "1")

        cartas = manager.get_cartas_serie("Série W")
        assert len(cartas) == 3
        assert "1" in cartas
        assert "3" in cartas
        assert "5" in cartas

    def test_get_todas_series(self, session_file):
        """Get todas as séries."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série X1")
        manager.criar_serie("Série X2")

        series = manager.get_todas_series()
        assert len(series) == 2
        assert "Série X1" in series
        assert "Série X2" in series

    def test_get_info_serie(self, session_file):
        """Get informações detalhadas de série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série Y", "Descrição Y")
        manager.adicionar_carta_serie("Série Y", "1")
        manager.adicionar_carta_serie("Série Y", "2")

        info = manager.get_info_serie("Série Y")
        assert info is not None
        assert info["descricao"] == "Descrição Y"
        assert len(info["cartas"]) == 2
        assert info["total_cartas"] == 2

    def test_get_info_serie_inexistente(self, session_file):
        """Get informações de série inexistente."""
        manager = SeriesManager(session_file)
        info = manager.get_info_serie("Série Inexistente")

        assert info is None


class TestEditarDescricao:
    """Testes para editar descrição de série."""

    def test_editar_descricao_serie(self, session_file):
        """Editar descrição de série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série Z", "Descrição original")
        sucesso, mensagem = manager.editar_descricao_serie("Série Z", "Nova descrição")

        assert sucesso is True
        assert manager.series["Série Z"]["descricao"] == "Nova descrição"

    def test_editar_descricao_serie_inexistente(self, session_file):
        """Editar descrição de série inexistente deve falhar."""
        manager = SeriesManager(session_file)
        sucesso, mensagem = manager.editar_descricao_serie("Série Inexistente", "Descrição")

        assert sucesso is False


class TestStats:
    """Testes para estatísticas."""

    def test_total_cartas_series(self, session_file):
        """Total de cartas em séries (com deduplicação)."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série AA")
        manager.criar_serie("Série AB")
        manager.adicionar_carta_serie("Série AA", "1")
        manager.adicionar_carta_serie("Série AB", "1")  # mesma carta
        manager.adicionar_carta_serie("Série AA", "2")

        total = manager.total_cartas_series()
        assert total == 2  # 1 e 2, não 3

    def test_total_series(self, session_file):
        """Total de séries."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série AC")
        manager.criar_serie("Série AD")
        manager.criar_serie("Série AE")

        total = manager.total_series()
        assert total == 3


class TestRebuildCartaIndex:
    """Testes para reconstrução do índice invertido."""

    def test_rebuild_carta_index_apos_deletar_serie(self, session_file):
        """Índice é reconstruído após deletar série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série AF")
        manager.criar_serie("Série AG")
        manager.adicionar_carta_serie("Série AF", "1")
        manager.adicionar_carta_serie("Série AG", "1")

        manager.deletar_serie("Série AF")

        # Verificar que índice foi atualizado
        assert manager._carta_index["1"] == {"Série AG"}

    def test_rebuild_carta_index_apos_renomear(self, session_file):
        """Índice é reconstruído após renomear série."""
        manager = SeriesManager(session_file)
        manager.criar_serie("Série AH")
        manager.adicionar_carta_serie("Série AH", "1")

        manager.renomear_serie("Série AH", "Série AH Novo")

        # Verificar que índice foi atualizado
        assert manager._carta_index["1"] == {"Série AH Novo"}

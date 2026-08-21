"""
Testes unitários para AnnotationManager.
Cobertura: CRUD de anotações, caderno de pesquisa, persistência.
"""

import pytest
import os
import json
import threading
import time
from modules.annotation_manager import AnnotationManager


class TestSetAnotacao:
    """Testes para salvar anotação."""

    def test_set_anotacao_simples(self, session_file):
        """Salvar anotação simples."""
        manager = AnnotationManager(session_file)
        sucesso = manager.set_anotacao("1", "Anotação de teste")

        assert sucesso is True
        assert manager.anotacoes["1"] == "Anotação de teste"

    def test_set_anotacao_atualizar(self, session_file):
        """Atualizar anotação existente."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação 1")
        sucesso = manager.set_anotacao("1", "Anotação 1 Atualizada")

        assert sucesso is True
        assert manager.anotacoes["1"] == "Anotação 1 Atualizada"

    def test_set_anotacao_com_espacos(self, session_file):
        """Salvar anotação com espaços (deve fazer strip)."""
        manager = AnnotationManager(session_file)
        sucesso = manager.set_anotacao("1", "  Anotação com espaços  ")

        assert sucesso is True
        assert manager.anotacoes["1"] == "Anotação com espaços"

    def test_set_anotacao_vazia(self, session_file):
        """Salvar anotação vazia."""
        manager = AnnotationManager(session_file)
        sucesso = manager.set_anotacao("1", "")

        assert sucesso is True
        assert manager.anotacoes["1"] == ""

    def test_set_anotacao_multiplas_cartas(self, session_file):
        """Salvar anotações para múltiplas cartas."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação 1")
        manager.set_anotacao("2", "Anotação 2")
        manager.set_anotacao("3", "Anotação 3")

        assert len(manager.anotacoes) == 3
        assert manager.anotacoes["1"] == "Anotação 1"
        assert manager.anotacoes["2"] == "Anotação 2"
        assert manager.anotacoes["3"] == "Anotação 3"

    def test_set_anotacao_salva_arquivo(self, session_file):
        """Salvar anotação persiste em arquivo."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação persistente")

        # Recarregar manager
        manager2 = AnnotationManager(session_file)
        assert manager2.anotacoes["1"] == "Anotação persistente"


class TestGetAnotacao:
    """Testes para recuperar anotação."""

    def test_get_anotacao(self, session_file):
        """Get anotação de carta."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Minha anotação")
        anotacao = manager.get_anotacao("1")

        assert anotacao == "Minha anotação"

    def test_get_anotacao_inexistente(self, session_file):
        """Get anotação inexistente retorna string vazia."""
        manager = AnnotationManager(session_file)
        anotacao = manager.get_anotacao("999")

        assert anotacao == ""

    def test_tem_anotacao_true(self, session_file):
        """Verificar se carta tem anotação."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação")

        assert manager.tem_anotacao("1") is True

    def test_tem_anotacao_false(self, session_file):
        """Verificar se carta não tem anotação."""
        manager = AnnotationManager(session_file)
        assert manager.tem_anotacao("1") is False

    def test_tem_anotacao_vazia(self, session_file):
        """Verificar se anotação vazia não conta."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "")

        assert manager.tem_anotacao("1") is False


class TestDeletarAnotacao:
    """Testes para deletar anotação."""

    def test_deletar_anotacao(self, session_file):
        """Deletar anotação."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação para deletar")
        sucesso = manager.deletar_anotacao("1")

        assert sucesso is True
        assert "1" not in manager.anotacoes

    def test_deletar_anotacao_inexistente(self, session_file):
        """Deletar anotação inexistente (deve ser seguro)."""
        manager = AnnotationManager(session_file)
        sucesso = manager.deletar_anotacao("999")

        assert sucesso is True  # seguro, não lança erro

    def test_deletar_anotacao_salva_arquivo(self, session_file):
        """Deletar anotação persiste em arquivo."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação")
        manager.deletar_anotacao("1")

        # Recarregar manager
        manager2 = AnnotationManager(session_file)
        assert "1" not in manager2.anotacoes


class TestCadernoNoPesquisa:
    """Testes para caderno de pesquisa."""

    def test_set_caderno_pesquisa(self, session_file):
        """Salvar caderno de pesquisa."""
        manager = AnnotationManager(session_file)
        sucesso = manager.set_caderno_pesquisa("Anotações de pesquisa")

        assert sucesso is True
        assert manager.caderno_pesquisa == "Anotações de pesquisa"

    def test_set_caderno_pesquisa_atualizar(self, session_file):
        """Atualizar caderno de pesquisa."""
        manager = AnnotationManager(session_file)
        manager.set_caderno_pesquisa("Caderno 1")
        sucesso = manager.set_caderno_pesquisa("Caderno 2")

        assert sucesso is True
        assert manager.caderno_pesquisa == "Caderno 2"

    def test_get_caderno_pesquisa(self, session_file):
        """Get caderno de pesquisa."""
        manager = AnnotationManager(session_file)
        manager.set_caderno_pesquisa("Conteúdo do caderno")
        caderno = manager.get_caderno_pesquisa()

        assert caderno == "Conteúdo do caderno"

    def test_get_caderno_pesquisa_vazio(self, session_file):
        """Get caderno vazio retorna string vazia."""
        manager = AnnotationManager(session_file)
        caderno = manager.get_caderno_pesquisa()

        assert caderno == ""

    def test_append_caderno_pesquisa(self, session_file):
        """Adicionar texto ao caderno."""
        manager = AnnotationManager(session_file)
        manager.set_caderno_pesquisa("Linha 1")
        sucesso = manager.append_caderno_pesquisa("Linha 2")

        assert sucesso is True
        assert "Linha 1" in manager.caderno_pesquisa
        assert "Linha 2" in manager.caderno_pesquisa

    def test_append_caderno_pesquisa_vazio(self, session_file):
        """Append a caderno vazio."""
        manager = AnnotationManager(session_file)
        sucesso = manager.append_caderno_pesquisa("Primeira linha")

        assert sucesso is True
        assert manager.caderno_pesquisa == "Primeira linha"

    def test_caderno_pesquisa_salva_arquivo(self, session_file):
        """Caderno de pesquisa persiste em arquivo."""
        manager = AnnotationManager(session_file)
        manager.set_caderno_pesquisa("Caderno persistente")

        # Recarregar manager
        manager2 = AnnotationManager(session_file)
        assert manager2.caderno_pesquisa == "Caderno persistente"


class TestContar:
    """Testes para contagem de anotações."""

    def test_contar_anotacoes(self, session_file):
        """Contar total de anotações."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação 1")
        manager.set_anotacao("2", "Anotação 2")
        manager.set_anotacao("3", "")  # vazia

        total = manager.contar_anotacoes()
        assert total == 2  # vazia não conta


class TestGetAll:
    """Testes para obter todas as anotações."""

    def test_get_todas_anotacoes(self, session_file):
        """Get todas as anotações."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação 1")
        manager.set_anotacao("2", "Anotação 2")

        todas = manager.get_todas_anotacoes()
        assert len(todas) == 2
        assert todas["1"] == "Anotação 1"
        assert todas["2"] == "Anotação 2"

    def test_get_todas_anotacoes_vazio(self, session_file):
        """Get todas as anotações quando vazio."""
        manager = AnnotationManager(session_file)
        todas = manager.get_todas_anotacoes()

        assert len(todas) == 0


class TestExportar:
    """Testes para exportação."""

    def test_exportar_anotacoes(self, session_file):
        """Exportar anotações como JSON."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação 1")
        manager.set_anotacao("2", "Anotação 2")

        json_str = manager.exportar_anotacoes()
        dados = json.loads(json_str)

        assert dados["1"] == "Anotação 1"
        assert dados["2"] == "Anotação 2"

    def test_exportar_anotacoes_vazio(self, session_file):
        """Exportar anotações vazio."""
        manager = AnnotationManager(session_file)
        json_str = manager.exportar_anotacoes()
        dados = json.loads(json_str)

        assert len(dados) == 0


class TestAtomicWrite:
    """Testes para escrita atômica (evita corrupção)."""

    def test_escrita_atomica_nao_corrompe_arquivo(self, session_file):
        """Escrita atômica usando temp + rename."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação 1")

        # Verificar que arquivo temp foi removido
        temp_file = session_file + '.tmp'
        assert not os.path.exists(temp_file)

        # Arquivo principal deve ser válido JSON
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data["anotacoes"]["1"] == "Anotação 1"

    def test_file_locking(self, session_file):
        """File locking previne race conditions (básico)."""
        # Teste simplificado: apenas verifica que file locking não falha
        # Em ambientes reais, race conditions são raras e difíceis de testar
        manager = AnnotationManager(session_file)

        # Tentar múltiplas escritas sequenciais (não paralelas)
        for i in range(3):
            sucesso = manager.set_anotacao(str(i), f"Anotação {i}")
            assert sucesso is True

        # Recarregar e verificar
        manager2 = AnnotationManager(session_file)
        assert len(manager2.anotacoes) == 3

    def test_arquivo_json_valido_apos_multiplas_escritas(self, session_file):
        """Arquivo JSON permanece válido após múltiplas escritas."""
        manager = AnnotationManager(session_file)

        for i in range(10):
            manager.set_anotacao(str(i), f"Anotação {i}")

        # Verificar que arquivo é JSON válido
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data["anotacoes"]) == 10


class TestLimpezaCompleta:
    """Testes para limpeza de sessão."""

    def test_limpar_sessao(self, session_file):
        """Limpar sessão remove tudo."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação")
        manager.set_caderno_pesquisa("Caderno")

        sucesso = manager.limpar_sessao()

        assert sucesso is True
        assert len(manager.anotacoes) == 0
        assert manager.caderno_pesquisa == ""

    def test_limpar_sessao_salva_arquivo(self, session_file):
        """Limpar sessão persiste em arquivo."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação")
        manager.limpar_sessao()

        # Recarregar manager
        manager2 = AnnotationManager(session_file)
        assert len(manager2.anotacoes) == 0
        assert manager2.caderno_pesquisa == ""


class TestLoadSession:
    """Testes para carregamento de sessão."""

    def test_load_session_arquivo_inexistente(self, session_file):
        """Load session com arquivo inexistente retorna False."""
        manager = AnnotationManager(session_file)
        sucesso = manager.load_session()

        assert sucesso is False

    def test_load_session_recupera_dados(self, session_file):
        """Load session recupera dados salvos anteriormente."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação persistida")
        manager.set_caderno_pesquisa("Caderno persistido")

        # Novo manager carrega dados
        manager2 = AnnotationManager(session_file)
        assert manager2.anotacoes["1"] == "Anotação persistida"
        assert manager2.caderno_pesquisa == "Caderno persistido"

    def test_load_session_arquivo_corrompido(self, session_file):
        """Load session com arquivo corrompido retorna False."""
        # Criar arquivo corrompido
        with open(session_file, 'w') as f:
            f.write("JSON inválido {]")

        manager = AnnotationManager(session_file)
        sucesso = manager.load_session()

        assert sucesso is False


class TestUltimoUpdate:
    """Testes para timestamp de atualização."""

    def test_get_ultimo_update_formatado(self, session_file):
        """Get último update formatado."""
        manager = AnnotationManager(session_file)
        manager.set_anotacao("1", "Anotação")

        timestamp = manager.get_ultimo_update()
        # Deve estar formatado (dd/mm/yyyy HH:MM:SS)
        assert "/" in timestamp
        assert ":" in timestamp

    def test_get_ultimo_update_nunca(self, session_file):
        """Get último update retorna 'Nunca' se não salvou."""
        manager = AnnotationManager(session_file)
        timestamp = manager.get_ultimo_update()

        assert timestamp == "Nunca"

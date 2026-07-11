"""
Gerenciador de anotações vinculadas a cartas e caderno de pesquisa global.
Responsável por persistência automática de anotações.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime


class AnnotationManager:
    """Gerencia anotações de cartas e caderno de pesquisa."""

    def __init__(self, session_file: str = "sessions/current_session.json"):
        """
        Inicializa o gerenciador de anotações.

        Args:
            session_file: Caminho do arquivo de sessão
        """
        self.session_file = session_file
        self.anotacoes: Dict[str, str] = {}  # carta_id -> anotação
        self.caderno_pesquisa: str = ""
        self.ultimo_update: str = ""
        self.load_session()

    def load_session(self) -> bool:
        """
        Carrega a sessão anterior se existir.

        Returns:
            True se carregou com sucesso
        """
        if not os.path.exists(self.session_file):
            return False

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.anotacoes = data.get('anotacoes', {})
            self.caderno_pesquisa = data.get('caderno_pesquisa', '')
            self.ultimo_update = data.get('ultimo_update', '')

            return True
        except Exception:
            return False

    def save_session(self, series: Optional[Dict] = None) -> bool:
        """
        Salva a sessão atual em arquivo.

        Args:
            series: Dicionário de séries (opcional). Se omitido, preserva as
                    séries que já estão gravadas no arquivo.

        Returns:
            True se salvou com sucesso
        """
        os.makedirs(os.path.dirname(self.session_file) or '.', exist_ok=True)

        try:
            # Se series não foi passado, lê do arquivo para não sobrescrever
            if series is None:
                series_to_save = {}
                if os.path.exists(self.session_file):
                    try:
                        with open(self.session_file, 'r', encoding='utf-8') as f:
                            series_to_save = json.load(f).get('series', {})
                    except Exception:
                        pass
            else:
                series_to_save = series

            data = {
                'anotacoes': self.anotacoes,
                'caderno_pesquisa': self.caderno_pesquisa,
                'series': series_to_save,
                'ultimo_update': datetime.now().isoformat()
            }

            # Escrita atômica: grava em temp e renomeia — evita corrupção em crash
            _tmp = self.session_file + '.tmp'
            with open(_tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            os.replace(_tmp, self.session_file)

            self.ultimo_update = data['ultimo_update']
            return True
        except Exception:
            return False

    def set_anotacao(self, carta_id: str, texto: str) -> bool:
        """
        Define/atualiza anotação de uma carta.

        Args:
            carta_id: ID da carta
            texto: Texto da anotação

        Returns:
            True se salvou com sucesso
        """
        self.anotacoes[carta_id] = texto.strip()
        return self.save_session()

    def get_anotacao(self, carta_id: str) -> str:
        """
        Retorna anotação de uma carta.

        Args:
            carta_id: ID da carta

        Returns:
            Texto da anotação ou string vazia
        """
        return self.anotacoes.get(carta_id, '')

    def tem_anotacao(self, carta_id: str) -> bool:
        """
        Verifica se carta tem anotação.

        Args:
            carta_id: ID da carta

        Returns:
            True se tem anotação não-vazia
        """
        return bool(self.anotacoes.get(carta_id, '').strip())

    def contar_anotacoes(self) -> int:
        """Retorna total de cartas com anotações."""
        return sum(1 for text in self.anotacoes.values() if text.strip())

    def deletar_anotacao(self, carta_id: str) -> bool:
        """
        Deleta anotação de uma carta.

        Args:
            carta_id: ID da carta

        Returns:
            True se deletou com sucesso
        """
        if carta_id in self.anotacoes:
            del self.anotacoes[carta_id]
            return self.save_session()
        return True

    def set_caderno_pesquisa(self, texto: str) -> bool:
        """
        Define/atualiza o caderno de pesquisa global.

        Args:
            texto: Texto do caderno

        Returns:
            True se salvou com sucesso
        """
        self.caderno_pesquisa = texto.strip()
        return self.save_session()

    def get_caderno_pesquisa(self) -> str:
        """Retorna o conteúdo do caderno de pesquisa."""
        return self.caderno_pesquisa

    def append_caderno_pesquisa(self, texto: str) -> bool:
        """
        Adiciona texto ao final do caderno.

        Args:
            texto: Texto a adicionar

        Returns:
            True se salvou com sucesso
        """
        if self.caderno_pesquisa:
            self.caderno_pesquisa += "\n\n" + texto
        else:
            self.caderno_pesquisa = texto

        return self.save_session()

    def get_todas_anotacoes(self) -> Dict[str, str]:
        """Retorna todas as anotações."""
        return self.anotacoes.copy()

    def exportar_anotacoes(self) -> str:
        """
        Exporta todas as anotações como JSON.

        Returns:
            String JSON
        """
        return json.dumps(self.anotacoes, ensure_ascii=False, indent=2)

    def get_ultimo_update(self) -> str:
        """Retorna timestamp da última modificação."""
        if self.ultimo_update:
            try:
                dt = datetime.fromisoformat(self.ultimo_update)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                return self.ultimo_update

        return "Nunca"

    def limpar_sessao(self) -> bool:
        """
        Limpa todas as anotações e caderno (começa novo).

        Returns:
            True se limpou com sucesso
        """
        self.anotacoes = {}
        self.caderno_pesquisa = ""
        return self.save_session()

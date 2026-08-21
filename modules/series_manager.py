"""
Gerenciador de séries temáticas.
Permite criar, editar, deletar séries e vincular cartas a elas com file locking para evitar race conditions.
"""

import json
import os
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from filelock import FileLock, Timeout


class SeriesManager:
    """Gerencia séries temáticas e vinculação com cartas."""

    def __init__(self, session_file: str = "sessions/current_session.json"):
        self.session_file = session_file
        self.series: Dict[str, Dict] = {}  # nome_serie -> {cartas: set, descricao: str}
        self._carta_index: Dict[str, Set[str]] = {}  # carta_id -> set de nomes de séries
        self.load_session()

    def _rebuild_carta_index(self) -> None:
        self._carta_index = {}
        for nome, serie_info in self.series.items():
            for carta_id in serie_info['cartas']:
                self._carta_index.setdefault(carta_id, set()).add(nome)

    def load_session(self) -> bool:
        """
        Carrega séries da sessão anterior.

        Returns:
            True se carregou com sucesso
        """
        if not os.path.exists(self.session_file):
            return False

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            series_data = data.get('series', {})

            for nome, serie_info in series_data.items():
                cartas = serie_info.get('cartas', [])
                descricao = serie_info.get('descricao', '')
                self.series[nome] = {
                    'cartas': set(cartas),
                    'descricao': descricao,
                    'criada_em': serie_info.get('criada_em', datetime.now().isoformat())
                }

            self._rebuild_carta_index()
            return True
        except Exception:
            return False

    def save_session(self, annotation_manager=None) -> bool:
        """
        Salva séries na sessão com file locking para evitar race conditions.

        Args:
            annotation_manager: AnnotationManager para salvar junto

        Returns:
            True se salvou com sucesso
        """
        os.makedirs(os.path.dirname(self.session_file) or '.', exist_ok=True)

        lock_path = self.session_file + '.lock'
        lock = FileLock(lock_path, timeout=5)

        try:
            with lock:
                # Converte sets para listas para JSON
                series_serializable = {}
                for nome, serie_info in self.series.items():
                    series_serializable[nome] = {
                        'cartas': list(serie_info['cartas']),
                        'descricao': serie_info.get('descricao', ''),
                        'criada_em': serie_info.get('criada_em', datetime.now().isoformat())
                    }

                # Se annotation_manager fornecido, salva tudo junto
                if annotation_manager:
                    data = {
                        'anotacoes': annotation_manager.anotacoes,
                        'caderno_pesquisa': annotation_manager.caderno_pesquisa,
                        'series': series_serializable,
                        'ultimo_update': datetime.now().isoformat()
                    }
                else:
                    # Carrega data anterior e atualiza series
                    if os.path.exists(self.session_file):
                        with open(self.session_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        data = {}

                    data['series'] = series_serializable
                    data['ultimo_update'] = datetime.now().isoformat()

                # Escrita atômica: grava em temp e renomeia — evita corrupção em crash
                _tmp = self.session_file + '.tmp'
                with open(_tmp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                os.replace(_tmp, self.session_file)

                return True
        except Timeout:
            return False
        except Exception:
            return False

    def criar_serie(self, nome: str, descricao: str = "") -> Tuple[bool, str]:
        """
        Cria uma nova série.

        Args:
            nome: Nome da série
            descricao: Descrição da série

        Returns:
            Tupla (sucesso, mensagem)
        """
        if nome in self.series:
            return False, "Série já existe"

        if not nome.strip():
            return False, "Nome da série não pode ser vazio"

        self.series[nome] = {
            'cartas': set(),
            'descricao': descricao.strip(),
            'criada_em': datetime.now().isoformat()
        }

        self.save_session()
        return True, f"Série '{nome}' criada com sucesso"

    def deletar_serie(self, nome: str) -> Tuple[bool, str]:
        """
        Deleta uma série.

        Args:
            nome: Nome da série

        Returns:
            Tupla (sucesso, mensagem)
        """
        if nome not in self.series:
            return False, "Série não encontrada"

        del self.series[nome]
        self._rebuild_carta_index()
        self.save_session()
        return True, f"Série '{nome}' deletada"

    def renomear_serie(self, nome_antigo: str, nome_novo: str) -> Tuple[bool, str]:
        """
        Renomeia uma série.

        Args:
            nome_antigo: Nome atual
            nome_novo: Novo nome

        Returns:
            Tupla (sucesso, mensagem)
        """
        if nome_antigo not in self.series:
            return False, "Série não encontrada"

        if nome_novo in self.series:
            return False, "Novo nome já existe"

        self.series[nome_novo] = self.series.pop(nome_antigo)
        self._rebuild_carta_index()
        self.save_session()
        return True, f"Série renomeada para '{nome_novo}'"

    def adicionar_carta_serie(self, nome_serie: str, carta_id: str) -> Tuple[bool, str]:
        """
        Adiciona uma carta a uma série.

        Args:
            nome_serie: Nome da série
            carta_id: ID da carta

        Returns:
            Tupla (sucesso, mensagem)
        """
        if nome_serie not in self.series:
            return False, "Série não encontrada"

        carta_id = str(carta_id)
        self.series[nome_serie]['cartas'].add(carta_id)
        self._carta_index.setdefault(carta_id, set()).add(nome_serie)
        self.save_session()
        return True, "Carta adicionada à série"

    def remover_carta_serie(self, nome_serie: str, carta_id: str) -> Tuple[bool, str]:
        """
        Remove uma carta de uma série.

        Args:
            nome_serie: Nome da série
            carta_id: ID da carta

        Returns:
            Tupla (sucesso, mensagem)
        """
        if nome_serie not in self.series:
            return False, "Série não encontrada"

        carta_id = str(carta_id)
        self.series[nome_serie]['cartas'].discard(carta_id)
        self._carta_index.get(carta_id, set()).discard(nome_serie)
        self.save_session()
        return True, "Carta removida da série"

    def atualizar_series_carta(self, carta_id: str, series_novas: List[str]) -> Tuple[bool, str]:
        """
        Reconcilia as séries de uma carta para corresponder exatamente a series_novas.
        Chama save_session() uma única vez independente do número de alterações.

        Args:
            carta_id: ID da carta
            series_novas: Lista de nomes de séries desejadas

        Returns:
            Tupla (sucesso, mensagem)
        """
        carta_id = str(carta_id)
        series_atuais = set(self._carta_index.get(carta_id, set()))
        series_desejadas = set(series_novas)

        remover = series_atuais - series_desejadas
        adicionar = series_desejadas - series_atuais

        for nome in remover:
            if nome in self.series:
                self.series[nome]['cartas'].discard(carta_id)
                self._carta_index.get(carta_id, set()).discard(nome)

        for nome in adicionar:
            if nome in self.series:
                self.series[nome]['cartas'].add(carta_id)
                self._carta_index.setdefault(carta_id, set()).add(nome)

        if remover or adicionar:
            self.save_session()

        return True, f"{len(adicionar)} adicionadas, {len(remover)} removidas"

    def get_series_carta(self, carta_id: str) -> List[str]:
        """
        Retorna lista de séries que contêm a carta.

        Args:
            carta_id: ID da carta

        Returns:
            Lista de nomes de séries (ordenada)
        """
        return sorted(self._carta_index.get(str(carta_id), set()))

    def get_cartas_serie(self, nome_serie: str) -> List[str]:
        """
        Retorna IDs de cartas de uma série.

        Args:
            nome_serie: Nome da série

        Returns:
            Lista de IDs (ordenada numericamente se possível)
        """
        if nome_serie not in self.series:
            return []

        cartas = list(self.series[nome_serie]['cartas'])

        try:
            return sorted(cartas, key=lambda x: int(x))
        except ValueError:
            return sorted(cartas)

    def get_todas_series(self) -> List[str]:
        """Retorna lista de todas as séries."""
        return sorted(self.series.keys())

    def get_info_serie(self, nome_serie: str) -> Optional[Dict]:
        """
        Retorna informações detalhadas de uma série.

        Args:
            nome_serie: Nome da série

        Returns:
            Dicionário com informações ou None
        """
        if nome_serie not in self.series:
            return None

        info = self.series[nome_serie].copy()
        info['cartas'] = self.get_cartas_serie(nome_serie)
        info['total_cartas'] = len(info['cartas'])

        return info

    def editar_descricao_serie(self, nome_serie: str, descricao: str) -> Tuple[bool, str]:
        """
        Edita descrição de uma série.

        Args:
            nome_serie: Nome da série
            descricao: Nova descrição

        Returns:
            Tupla (sucesso, mensagem)
        """
        if nome_serie not in self.series:
            return False, "Série não encontrada"

        self.series[nome_serie]['descricao'] = descricao.strip()
        self.save_session()
        return True, "Descrição atualizada"

    def exportar_series(self) -> str:
        """
        Exporta todas as séries como JSON.

        Returns:
            String JSON
        """
        series_export = {}
        for nome, serie_info in self.series.items():
            series_export[nome] = {
                'cartas': list(serie_info['cartas']),
                'descricao': serie_info.get('descricao', ''),
                'total_cartas': len(serie_info['cartas']),
                'criada_em': serie_info.get('criada_em', '')
            }

        return json.dumps(series_export, ensure_ascii=False, indent=2)

    def total_cartas_series(self) -> int:
        """Retorna total de cartas vinculadas a alguma série (com deduplicação)."""
        return len(self._carta_index)

    def total_series(self) -> int:
        """Retorna total de séries."""
        return len(self.series)

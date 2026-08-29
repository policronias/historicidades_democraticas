"""
Gerenciador de dados de cartas históricas.
Responsável por carregar, salvar e gerenciar múltiplas bases de dados.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import streamlit as st
import requests

# Cache de módulo: evita re-parsear JSON de 100+ MB a cada reinício de sessão.
# Chave = caminho absoluto do arquivo; valor = {'mtime': float, 'data': dict}
_PARSED_DB_CACHE: Dict[str, dict] = {}


GITHUB_OWNER = "policronias"
GITHUB_REPO = "historicidades_democraticas"
GITHUB_RELEASE_TAG = "dados-v1"          # a tag que você criou na Release
GITHUB_ASSET_NAME = "cartas_db.json"      # nome exato do arquivo anexado na Release


DADOS_URL = "https://github.com/policronias/historicidades-democraticas-dados/releases/download/dados-v1/cartas_db.json"


def garantir_base_baixada(destino: str = "cartas_db.json") -> None:
    """
    Garante que o arquivo de dados exista localmente antes do app tentar carregá-lo.
    Se não existir, baixa automaticamente de um link público.
    """
    if os.path.exists(destino):
        return

    with st.spinner("Baixando base de dados pela primeira vez (pode levar 1-2 minutos)..."):
        try:
            resp = requests.get(DADOS_URL, stream=True, timeout=180)
            resp.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.RequestException as e:
            st.error(f"Erro ao baixar a base de dados: {e}")
            st.stop()


class DataManager:
    """Gerencia carregamento, salvamento e manipulação de bases de dados de cartas."""

    def __init__(self, data_dir: str = ".", sessions_dir: str = "sessions"):
        """
        Inicializa o gerenciador de dados.

        Args:
            data_dir: Diretório contendo as bases de dados JSON
            sessions_dir: Diretório para salvar sessões
        """
        self.data_dir = data_dir
        self.sessions_dir = sessions_dir
        self.current_database: Dict = {}
        self.current_database_name: str = ""
        self.loaded_databases: Dict[str, Dict] = {}

    def _normalize_database(self, data: Dict) -> Dict:
        """
        Normaliza a estrutura da base de dados para o formato padrão.

        Detecta se é um resultado de busca (com chave 'cartas' como lista)
        e converte para o formato esperado (dicionário com IDs como chaves).
        """
        # Se tem a chave 'cartas' como lista, é um resultado de busca
        if isinstance(data.get('cartas'), list):
            normalized = {}
            for carta in data['cartas']:
                carta_id = str(carta.get('id', ''))
                if carta_id:
                    normalized[carta_id] = carta
            return normalized
        # Se é um dicionário direto, retorna como está
        elif isinstance(data, dict) and data:
            # Verifica se parece ser uma base normal (valores são dicts)
            first_value = next(iter(data.values()), None)
            if isinstance(first_value, dict):
                return data
        return data

    def load_database(self, filename: str) -> Tuple[bool, str]:
        """
        Carrega uma base de dados JSON.

        Args:
            filename: Nome do arquivo JSON

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            filepath = os.path.abspath(os.path.join(self.data_dir, filename))

            # Usa cache de módulo: só re-parseia se o arquivo mudou em disco
            try:
                mtime = os.path.getmtime(filepath)
            except OSError:
                return False, f"Arquivo '{filename}' não encontrado"

            cached = _PARSED_DB_CACHE.get(filepath)
            if cached is None or cached['mtime'] != mtime:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data = self._normalize_database(data)
                _PARSED_DB_CACHE[filepath] = {'mtime': mtime, 'data': data}
            else:
                data = cached['data']

            self.current_database = data
            self.current_database_name = filename
            self.loaded_databases[filename] = data
            self._ids_cache_db = None
            self._nome_index_db = None
            self._uv_db = None

            return True, f"Base de dados '{filename}' carregada com sucesso ({len(data)} cartas)"
        except FileNotFoundError:
            return False, f"Arquivo '{filename}' não encontrado"
        except json.JSONDecodeError:
            return False, f"Erro ao decodificar JSON em '{filename}'"
        except Exception as e:
            return False, f"Erro ao carregar base: {str(e)}"

    def load_all_databases(self) -> Dict[str, int]:
        """
        Carrega todas as bases de dados JSON disponíveis no diretório.

        Returns:
            Dicionário com nomes de bases e quantidade de cartas
        """
        databases = {}
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json') and filename != 'cartas_db.json':
                    continue
                if filename.endswith('.json'):
                    success, msg = self.load_database(filename)
                    if success:
                        databases[filename] = len(self.loaded_databases[filename])
        except Exception:
            pass

        return databases

    def get_carta(self, carta_id: str) -> Optional[Dict]:
        """
        Retorna uma carta específica pelo ID.

        Args:
            carta_id: ID da carta

        Returns:
            Dicionário com dados da carta ou None
        """
        return self.current_database.get(carta_id)

    def get_todas_cartas(self) -> Dict:
        """Retorna todas as cartas da base de dados atual."""
        return self.current_database

    def get_ids_cartas(self) -> List[str]:
        """Retorna lista de IDs de cartas, ordenadas numericamente (com cache interno)."""
        if getattr(self, '_ids_cache_db', None) != self.current_database_name:
            try:
                self._ids_cache = sorted(self.current_database.keys(), key=lambda x: int(x))
            except ValueError:
                self._ids_cache = sorted(self.current_database.keys())
            self._ids_cache_db = self.current_database_name
        return self._ids_cache

    def get_nome_index(self) -> Dict[str, str]:
        """Retorna índice {id: nome} para lookups rápidos (com cache interno)."""
        if getattr(self, '_nome_index_db', None) != self.current_database_name:
            self._nome_index = {k: v.get('nome', 'N/A') for k, v in self.current_database.items()}
            self._nome_index_db = self.current_database_name
        return self._nome_index

    def get_campo_unique_values(self, campo: str) -> List[str]:
        """Retorna valores únicos de um campo com cache interno por base de dados."""
        if getattr(self, '_uv_db', None) != self.current_database_name:
            self._uv_cache: Dict[str, List[str]] = {}
            self._uv_db = self.current_database_name
        if campo not in self._uv_cache:
            valores = set()
            for carta in self.current_database.values():
                valor = carta.get(campo)
                if valor and str(valor).strip() and str(valor) != 'nan' and str(valor) != 'None':
                    valores.add(str(valor).strip())
            self._uv_cache[campo] = sorted(list(valores))
        return self._uv_cache[campo]

    def get_campos_unique_values_for_subset(self, campos: Dict[str, str], carta_ids: set) -> Dict[str, List[str]]:
        """Retorna valores únicos para múltiplos campos, apenas para um subset de cartas (otimizado para filtros)."""
        if not self.current_database or not carta_ids:
            return {campo: [] for campo in campos}

        resultado = {}
        for campo in campos:
            valores = set()
            for cid in carta_ids:
                if cid in self.current_database:
                    carta = self.current_database[cid]
                    valor = carta.get(campo)
                    if valor and str(valor).strip() and str(valor) != 'nan' and str(valor) != 'None':
                        valores.add(str(valor).strip())
            resultado[campo] = sorted(list(valores))
        return resultado

    def get_proxima_carta_id(self, carta_id: str) -> Optional[str]:
        """Retorna ID da próxima carta."""
        ids = self.get_ids_cartas()
        try:
            idx = ids.index(carta_id)
            if idx < len(ids) - 1:
                return ids[idx + 1]
        except (ValueError, IndexError):
            pass
        return None

    def get_carta_anterior_id(self, carta_id: str) -> Optional[str]:
        """Retorna ID da carta anterior."""
        ids = self.get_ids_cartas()
        try:
            idx = ids.index(carta_id)
            if idx > 0:
                return ids[idx - 1]
        except (ValueError, IndexError):
            pass
        return None

    def get_total_cartas(self) -> int:
        """Retorna total de cartas na base atual."""
        return len(self.current_database)

    def switch_database(self, database_name: str) -> Tuple[bool, str]:
        """
        Alterna para outra base de dados carregada.

        Args:
            database_name: Nome da base

        Returns:
            Tupla (sucesso, mensagem)
        """
        if database_name in self.loaded_databases:
            self.current_database = self.loaded_databases[database_name]
            self.current_database_name = database_name
            return True, f"Alternado para '{database_name}'"
        return False, f"Base de dados '{database_name}' não carregada"

    def upload_database(self, file_content: str, filename: str) -> Tuple[bool, str]:
        """
        Carrega uma nova base de dados a partir de um arquivo.

        Args:
            file_content: Conteúdo do arquivo
            filename: Nome do arquivo

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            data = json.loads(file_content)
            if not isinstance(data, dict):
                return False, "Base de dados deve ser um objeto JSON"

            self.loaded_databases[filename] = data
            self.current_database = data
            self.current_database_name = filename
            self._ids_cache_db = None
            self._nome_index_db = None
            self._uv_db = None

            return True, f"Nova base de dados '{filename}' carregada ({len(data)} cartas)"
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {str(e)}"
        except Exception as e:
            return False, f"Erro ao carregar: {str(e)}"

    def export_database(self, database_name: Optional[str] = None) -> str:
        """
        Exporta uma base de dados como JSON string.

        Args:
            database_name: Nome da base (usa atual se None)

        Returns:
            String JSON
        """
        if database_name and database_name in self.loaded_databases:
            db = self.loaded_databases[database_name]
        else:
            db = self.current_database

        return json.dumps(db, ensure_ascii=False, indent=2)

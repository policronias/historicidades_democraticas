"""
Analisador de frequência de palavras, expressões e radicais.
Análise comparativa de termos em toda a base de dados.
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Set


class FrequencyAnalyzer:
    """Análise de frequência e estatísticas de termos."""

    # Cores automáticas em sequência (identidade "Policronias do presente":
    # selo terracota, musgo, tinta grafite, âmbar de arquivo — paleta
    # contida, sem cores saturadas de stock)
    COLOR_PALETTE = [
        "#9c3a26",  # Selo (terracota de carimbo)
        "#5c6a4c",  # Musgo
        "#1b1815",  # Tinta
        "#c98a2e",  # Âmbar de arquivo
        "#4f6472",  # Ardósia sóbria
        "#9c8f7d",  # Taupe
        "#6f2a1b",  # Selo escuro
        "#7a8f66",  # Verde claro
        "#56514a",  # Tinta suave
        "#d97a5e",  # Terracota clara
        "#8a9a76",  # Musgo claro
        "#b0a58c",  # Linha / areia
    ]

    def __init__(self):
        """Inicializa o analisador."""
        self.ultima_analise = None
        self.termos_config = {}  # termo -> {'tipo': 'exato'|'radical', 'cor': '#...'}

    @staticmethod
    def _strip_accents(text: str) -> str:
        """Remove acentos de um texto."""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    def parse_termos(self, input_text: str) -> List[str]:
        """
        Faz parse do texto de entrada, detectando separadores.
        Suporta: vírgula, ponto-e-vírgula, pipe (|)

        Args:
            input_text: Texto com termos separados

        Returns:
            Lista de termos limpos (sem espaços/vazios)
        """
        # Substitui todos os separadores por um único separador padrão
        texto_normalizado = input_text
        for sep in [';', '|']:
            texto_normalizado = texto_normalizado.replace(sep, ',')

        # Quebra por vírgula
        termos = texto_normalizado.split(',')

        # Limpa e filtra
        termos_limpos = [t.strip() for t in termos if t.strip()]
        return termos_limpos

    def contar_ocorrencias(
        self,
        cartas: Dict,
        termo: str,
        eh_radical: bool = False,
        case_sensitive: bool = False
    ) -> Dict[str, int]:
        """
        Conta ocorrências de um termo em todas as cartas.

        Args:
            cartas: Dicionário de cartas
            termo: Termo a procurar
            eh_radical: Se True, usa wildcard (termo*)
            case_sensitive: Se True, considera maiúsculas

        Returns:
            Dict {carta_id: num_ocorrencias}
        """
        resultados = {}

        for carta_id, carta in cartas.items():
            texto = carta.get('texto', '')

            if not case_sensitive:
                texto = texto.lower()
                termo_busca = termo.lower()
            else:
                termo_busca = termo

            # Remove acentos para busca
            texto_norm = self._strip_accents(texto)
            termo_norm = self._strip_accents(termo_busca)

            # Busca com ou sem wildcard
            if eh_radical:
                # Usa regex para wildcard: termo* = termo+qualquer_coisa
                padrao = re.escape(termo_norm) + r'\w*'
                # Usar finditer (generator) ao invés de findall (lista) para economizar memória
                ocorrencias = sum(1 for _ in re.finditer(padrao, texto_norm, re.IGNORECASE))
            else:
                # Busca exata (substring)
                ocorrencias = texto_norm.count(termo_norm)

            if ocorrencias > 0:
                resultados[carta_id] = ocorrencias

        return resultados

    def contar_documentos(
        self,
        cartas: Dict,
        termo: str,
        eh_radical: bool = False,
        case_sensitive: bool = False
    ) -> Tuple[int, Set[str]]:
        """
        Conta quantos documentos contêm o termo.

        Args:
            cartas: Dicionário de cartas
            termo: Termo a procurar
            eh_radical: Se True, usa wildcard
            case_sensitive: Se True, considera maiúsculas

        Returns:
            Tupla (num_documentos, conjunto de carta_ids)
        """
        ocorrencias = self.contar_ocorrencias(cartas, termo, eh_radical, case_sensitive)
        return len(ocorrencias), set(ocorrencias.keys())

    def analisar_multiplos_termos(
        self,
        cartas: Dict,
        termos: List[str],
        tipos: List[str] = None,
        case_sensitive: bool = False
    ) -> Dict:
        """
        Análise completa de múltiplos termos.

        Args:
            cartas: Dicionário de cartas
            termos: Lista de termos
            tipos: Lista de tipos ('exato' ou 'radical'), mesmo tamanho de termos
            case_sensitive: Se True, considera maiúsculas

        Returns:
            Dict com estatísticas completas
        """
        if tipos is None:
            tipos = ['exato'] * len(termos)

        resultado = {
            'termos': [],
            'total_cartas': len(cartas),
        }

        for idx, termo in enumerate(termos):
            eh_radical = tipos[idx] == 'radical'
            cor = self.COLOR_PALETTE[idx % len(self.COLOR_PALETTE)]

            # Conta ocorrências e documentos
            ocorrencias_dict = self.contar_ocorrencias(
                cartas, termo, eh_radical, case_sensitive
            )
            total_ocorrencias = sum(ocorrencias_dict.values())
            num_docs = len(ocorrencias_dict)
            doc_ids = set(ocorrencias_dict.keys())

            self.termos_config[termo] = {
                'tipo': 'radical' if eh_radical else 'exato',
                'cor': cor
            }

            resultado['termos'].append({
                'termo': termo,
                'tipo': 'radical' if eh_radical else 'exato',
                'cor': cor,
                'total_ocorrencias': total_ocorrencias,
                'num_documentos': num_docs,
                'cartas_ids': sorted(doc_ids),
                'ocorrencias_por_carta': ocorrencias_dict,
            })

        self.ultima_analise = resultado
        return resultado

    def obter_cartas_com_termo(
        self,
        cartas: Dict,
        termo: str,
        eh_radical: bool = False,
        case_sensitive: bool = False
    ) -> List[Dict]:
        """
        Retorna as cartas que contêm o termo, com ocorrências.

        Args:
            cartas: Dicionário de cartas
            termo: Termo a procurar
            eh_radical: Se True, usa wildcard
            case_sensitive: Se True, considera maiúsculas

        Returns:
            Lista de cartas ordenadas por num de ocorrências (desc)
        """
        ocorrencias = self.contar_ocorrencias(cartas, termo, eh_radical, case_sensitive)

        cartas_resultado = []
        for carta_id, num_ocorrencias in ocorrencias.items():
            carta = cartas.get(carta_id, {})
            cartas_resultado.append({
                'carta_id': carta_id,
                'nome': carta.get('nome', ''),
                'destinatario': carta.get('destinatario', ''),
                'texto': carta.get('texto', ''),
                'data': carta.get('data', ''),
                'uf': carta.get('uf', ''),
                'ocorrencias': num_ocorrencias,
            })

        # Ordena por ocorrências (decrescente)
        return sorted(cartas_resultado, key=lambda x: x['ocorrencias'], reverse=True)

    def gerar_estatisticas_comparativas(self, resultado_analise: Dict) -> Dict:
        """
        Gera dados formatados para gráficos comparativos.

        Args:
            resultado_analise: Resultado de analisar_multiplos_termos()

        Returns:
            Dict com dados estruturados para Plotly
        """
        termos_nomes = [t['termo'] for t in resultado_analise['termos']]
        ocorrencias = [t['total_ocorrencias'] for t in resultado_analise['termos']]
        num_docs = [t['num_documentos'] for t in resultado_analise['termos']]

        return {
            'termos': termos_nomes,
            'ocorrencias': ocorrencias,
            'num_documentos': num_docs,
            'cores': [self.COLOR_PALETTE[i % len(self.COLOR_PALETTE)] for i in range(len(termos_nomes))],
        }

    def encontrar_termo_em_texto(
        self,
        texto: str,
        termo: str,
        eh_radical: bool = False,
        case_sensitive: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Encontra todas as posições de um termo em um texto.

        Args:
            texto: Texto a buscar
            termo: Termo a procurar
            eh_radical: Se True, usa wildcard
            case_sensitive: Se True, considera maiúsculas

        Returns:
            Lista de tuplas (start, end)
        """
        if not case_sensitive:
            texto_busca = texto.lower()
            termo_busca = termo.lower()
        else:
            texto_busca = texto
            termo_busca = termo

        # Remove acentos
        texto_norm = self._strip_accents(texto_busca)
        termo_norm = self._strip_accents(termo_busca)

        posicoes = []

        if eh_radical:
            # Busca com regex
            padrao = re.escape(termo_norm) + r'\w*'
            for match in re.finditer(padrao, texto_norm, re.IGNORECASE):
                posicoes.append((match.start(), match.end()))
        else:
            # Busca exata
            start = 0
            while True:
                idx = texto_norm.find(termo_norm, start)
                if idx == -1:
                    break
                posicoes.append((idx, idx + len(termo_norm)))
                start = idx + 1

        return posicoes

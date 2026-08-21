"""
Fixtures compartilhadas para testes.
Dados sintéticos: 8 cartas fictícias representativas.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def test_cartas():
    """8 cartas fictícias para testes (não usa a base real de 72.719)."""
    return {
        "1": {
            "linha": "A001",
            "nome": "João da Silva",
            "destinatario": "Câmara Municipal",
            "texto": "Solicito melhorias na educação e democracia. A história de nosso país mostra a importância de valores democráticos.",
            "origem": "São Paulo",
            "data": "1970-01-15",
            "formul": "Ofício",
            "dv": "1",
            "data2": "1970-01-20",
            "municipio": "São Paulo",
            "uf": "SP",
            "cep": "01310-100",
            "sexo": "M",
            "morador": "S",
            "instrucao": "Fundamental",
            "estado_civil": "Casado",
            "faixa_etaria": "40-50",
            "faixa_renda": "1000-2000",
            "atividade": "Comerciante",
            "catalogo": "HC001",
            "indexacao": "educação democracia história",
            "anotacoes": "",
            "series": []
        },
        "2": {
            "linha": "A002",
            "nome": "Maria dos Santos",
            "destinatario": "Prefeitura",
            "texto": "Peço que considerem as histórias de luta democrática. A democracia é fundamental para nossa nação histórica.",
            "origem": "Rio de Janeiro",
            "data": "1971-03-20",
            "formul": "Carta",
            "dv": "2",
            "data2": "1971-03-25",
            "municipio": "Rio de Janeiro",
            "uf": "RJ",
            "cep": "20040020",
            "sexo": "F",
            "morador": "S",
            "instrucao": "Médio",
            "estado_civil": "Viúva",
            "faixa_etaria": "50-60",
            "faixa_renda": "800-1500",
            "atividade": "Dona de casa",
            "catalogo": "HC002",
            "indexacao": "democracia história lutas",
            "anotacoes": "",
            "series": []
        },
        "3": {
            "linha": "A003",
            "nome": "Carlos Oliveira",
            "destinatario": "Assembleia Legislativa",
            "texto": "Solicito reconsideração dos direitos políticos. Os direitos são fundamentais para a democracia política.",
            "origem": "Minas Gerais",
            "data": "1972-05-10",
            "formul": "Representação",
            "dv": "3",
            "data2": "1972-05-15",
            "municipio": "Belo Horizonte",
            "uf": "MG",
            "cep": "30130-100",
            "sexo": "M",
            "morador": "S",
            "instrucao": "Médio",
            "estado_civil": "Solteiro",
            "faixa_etaria": "25-35",
            "faixa_renda": "1500-2500",
            "atividade": "Professor",
            "catalogo": "HC003",
            "indexacao": "direitos políticos legislativa",
            "anotacoes": "",
            "series": []
        },
        "4": {
            "linha": "A004",
            "nome": "Ana Costa",
            "destinatario": "Ministério da Justiça",
            "texto": "Justiça é necessária para que a democracia funcione. Precisamos de uma justiça equitativa.",
            "origem": "Bahia",
            "data": "1973-07-05",
            "formul": "Petição",
            "dv": "4",
            "data2": "1973-07-10",
            "municipio": "Salvador",
            "uf": "BA",
            "cep": "40060160",
            "sexo": "F",
            "morador": "S",
            "instrucao": "Superior",
            "estado_civil": "Casada",
            "faixa_etaria": "35-45",
            "faixa_renda": "2000-3000",
            "atividade": "Advogada",
            "catalogo": "HC004",
            "indexacao": "justiça direitos civis",
            "anotacoes": "",
            "series": []
        },
        "5": {
            "linha": "A005",
            "nome": "Pedro Silva",
            "destinatario": "Governo do Estado",
            "texto": "Solicitamos ação governamental imediata para problemas socioeconômicos.",
            "origem": "Paraná",
            "data": "1974-09-12",
            "formul": "Abaixo-assinado",
            "dv": "5",
            "data2": "1974-09-18",
            "municipio": "Curitiba",
            "uf": "PR",
            "cep": "80010000",
            "sexo": "M",
            "morador": "S",
            "instrucao": "Fundamental",
            "estado_civil": "Casado",
            "faixa_etaria": "45-55",
            "faixa_renda": "500-1000",
            "atividade": "Operário",
            "catalogo": "HC005",
            "indexacao": "governo ação social",
            "anotacoes": "",
            "series": []
        },
        "6": {
            "linha": "A006",
            "nome": "Lucia Martins",
            "destinatario": "Ministério do Trabalho",
            "texto": "Demandamos proteção dos direitos trabalhistas. O trabalho digno é direito fundamental.",
            "origem": "São Paulo",
            "data": "1975-11-20",
            "formul": "Carta",
            "dv": "6",
            "data2": "1975-11-25",
            "municipio": "São Paulo",
            "uf": "SP",
            "cep": "01310-100",
            "sexo": "F",
            "morador": "S",
            "instrucao": "Médio",
            "estado_civil": "Casada",
            "faixa_etaria": "30-40",
            "faixa_renda": "1000-2000",
            "atividade": "Operária",
            "catalogo": "HC006",
            "indexacao": "trabalho direitos operário",
            "anotacoes": "",
            "series": []
        },
        "7": {
            "linha": "A007",
            "nome": "Roberto Santos",
            "destinatario": "Banco Central",
            "texto": "Preocupações econômicas e financeiras requerem intervenção estatal.",
            "origem": "Rio Grande do Sul",
            "data": "1976-12-30",
            "formul": "Memorando",
            "dv": "7",
            "data2": "1977-01-05",
            "municipio": "Porto Alegre",
            "uf": "RS",
            "cep": "90010140",
            "sexo": "M",
            "morador": "S",
            "instrucao": "Superior",
            "estado_civil": "Solteiro",
            "faixa_etaria": "28-38",
            "faixa_renda": "2500-3500",
            "atividade": "Economista",
            "catalogo": "HC007",
            "indexacao": "economia finanças banco",
            "anotacoes": "",
            "series": []
        },
        "8": {
            "linha": "A008",
            "nome": "Fernanda Rocha",
            "destinatario": "Ministério da Educação",
            "texto": "Educação como ferramenta para democracia. Precisamos valorizar educadores.",
            "origem": "Pernambuco",
            "data": "1977-02-14",
            "formul": "Representação",
            "dv": "8",
            "data2": "1977-02-20",
            "municipio": "Recife",
            "uf": "PE",
            "cep": "50010000",
            "sexo": "F",
            "morador": "S",
            "instrucao": "Superior",
            "estado_civil": "Solteira",
            "faixa_etaria": "25-35",
            "faixa_renda": "1500-2500",
            "atividade": "Educadora",
            "catalogo": "HC008",
            "indexacao": "educação democracia escola",
            "anotacoes": "",
            "series": []
        }
    }


@pytest.fixture
def temp_session_dir():
    """Cria diretório temporário para arquivos de sessão."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def session_file(temp_session_dir):
    """Caminho do arquivo de sessão."""
    return os.path.join(temp_session_dir, "current_session.json")


@pytest.fixture
def mock_stem_index(test_cartas):
    """
    Índice mock de stems para testes.
    Simula a estrutura retornada por StemmingEngine.load_index().
    """
    return {
        'fields': ['texto', 'nome', 'destinatario', 'catalogo', 'indexacao', 'origem'],
        'index': {
            'texto': {
                'democr': {'1': 2, '2': 2, '3': 1, '8': 1},
                'histor': {'1': 1, '2': 2},
                'lutar': {'2': 1},
                'direito': {'3': 2, '4': 1, '6': 1},
                'justic': {'4': 2},
                'equitat': {'4': 1},
                'trabalh': {'6': 2},
                'educac': {'1': 1, '8': 2},
                'educat': {'8': 1}
            },
            'nome': {},
            'destinatario': {},
            'catalogo': {},
            'indexacao': {
                'democr': {'1': 1, '2': 1, '8': 1},
                'histor': {'1': 1, '2': 1},
                'educac': {'1': 1, '8': 1},
                'direito': {'3': 1, '4': 1, '6': 1},
                'trabalh': {'6': 1}
            },
            'origem': {}
        },
        'forms': {
            'democr': ['democracia', 'democrático'],
            'histor': ['história', 'histórica', 'historias'],
            'lutar': ['luta', 'lutas'],
            'direito': ['direitos', 'direito'],
            'justic': ['justiça', 'justiceiros'],
            'equitat': ['equitativa'],
            'trabalh': ['trabalho', 'trabalhista', 'trabalho'],
            'educac': ['educação'],
            'educat': ['educadores']
        }
    }

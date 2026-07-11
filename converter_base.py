import pandas as pd
import json

# ===== EDITE AQUI =====
ARQUIVO_ENTRADA = "sugestoes_constituintes_72k.xlsx"  # Mude para o nome do seu arquivo
ARQUIVO_SAIDA = "cartas_db.json"
# ======================

print(f"📖 Lendo {ARQUIVO_ENTRADA}...")
df = pd.read_excel(ARQUIVO_ENTRADA)

print(f"✅ Lido: {len(df)} registros")
print(f"📋 Colunas encontradas: {list(df.columns)}")

# Converta para JSON
dados = {}
for idx, row in df.iterrows():
    try:
        # Tenta encontrar a coluna de ID/linha
        linha = str(row.get('LINHA_BASE_SAIC') or row.get('ID') or idx)

        # Captura todos os metadados
        nome = str(row.get('NOME', '')).strip() or 'Anônimo'
        texto = str(row.get('SUGESTAO.TEXTO') or row.get('TEXTO', '')).strip()

        # Metadados
        destinatario = str(row.get('DESTINATARIO', '')).strip() or None
        catalogo = str(row.get('CATALOGO', '')).strip() or None
        indexacao = str(row.get('INDEXACAO', '')).strip() or None
        origem = str(row.get('ORIGEM', '')).strip() or None
        data = str(row.get('DATA', '')).strip() or None
        formul = str(row.get('FORMUL', '')).strip() or None
        dv = str(row.get('DV', '')).strip() or None
        data2 = str(row.get('DATA2', '')).strip() or None
        municipio = str(row.get('MUNICIPIO', '')).strip() or None
        uf = str(row.get('UF', '')).strip() or None
        cep = str(row.get('CEP', '')).strip() or None
        sexo = str(row.get('SEXO', '')).strip() or None
        morador = str(row.get('MORADOR', '')).strip() or None
        instrucao = str(row.get('INSTRUCAO', '')).strip() or None
        estado_civil = str(row.get('ESTADO CIVIL', '')).strip() or None
        faixa_etaria = str(row.get('FAIXA ETÁRIA', '')).strip() or None
        faixa_renda = str(row.get('FAIXA RENDA', '')).strip() or None
        atividade = str(row.get('ATIVIDADE', '')).strip() or None

    except Exception as e:
        print(f"⚠️ Erro ao processar linha {idx}: {e}")
        linha = str(idx)
        nome = 'Anônimo'
        texto = ''
        destinatario = None
        catalogo = None
        indexacao = None
        origem = None
        data = None
        formul = None
        dv = None
        data2 = None
        municipio = None
        uf = None
        cep = None
        sexo = None
        morador = None
        instrucao = None
        estado_civil = None
        faixa_etaria = None
        faixa_renda = None
        atividade = None

    # Monta o dicionário da carta com todos os metadados
    dados[linha] = {
        'linha': linha,
        'nome': nome,
        'destinatario': destinatario,
        'catalogo': catalogo,
        'indexacao': indexacao,
        'texto': texto,
        'origem': origem,
        'data': data,
        'formul': formul,
        'dv': dv,
        'data2': data2,
        'municipio': municipio,
        'uf': uf,
        'cep': cep,
        'sexo': sexo,
        'morador': morador,
        'instrucao': instrucao,
        'estado_civil': estado_civil,
        'faixa_etaria': faixa_etaria,
        'faixa_renda': faixa_renda,
        'atividade': atividade,
        'anotacoes': '',
        'series': [],
    }

# Salve como JSON
with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print(f"💾 Salvo: {ARQUIVO_SAIDA}")
print(f"📊 Total de cartas: {len(dados)}")
print("✅ Conversão concluída!")
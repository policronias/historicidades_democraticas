"""
Gerenciador de exportação de dados em diversos formatos.
Suporta CSV, JSON, TXT/Markdown, ZIP e HTML com gráficos interativos.
"""

import json
import csv
import zipfile
import io
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter

try:
    import plotly.express as px
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ---------------------------------------------------------------------------
# CSS base compartilhado para todos os relatórios
# ---------------------------------------------------------------------------
_CSS = """
* { box-sizing: border-box; }
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0; padding: 0;
    background: #f0f4f8; color: #333;
}
.container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
.report-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: white; padding: 30px 35px; border-radius: 10px; margin-bottom: 25px;
}
.report-header h1 { margin: 0 0 8px; font-size: 26px; }
.report-header h2 { margin: 0 0 12px; font-size: 18px; opacity: 0.9; font-weight: normal; }
.report-header .meta { font-size: 13px; opacity: 0.85; }
.report-header .meta span { margin-right: 20px; }
.section {
    background: white; border-radius: 8px; padding: 25px 30px;
    margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.section h2 {
    color: #1e3a8a; margin-top: 0; padding-bottom: 10px;
    border-bottom: 2px solid #e5e7eb; font-size: 18px;
}
.section h3 { color: #3b82f6; font-size: 15px; }
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 12px; margin: 15px 0;
}
.stat-box {
    background: #f0f9ff; border: 1px solid #bfdbfe;
    border-radius: 8px; padding: 15px 12px; text-align: center;
}
.stat-value { font-size: 30px; font-weight: bold; color: #1e3a8a; line-height: 1.2; }
.stat-label { font-size: 11px; color: #6b7280; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
.charts-scroll { overflow-x: auto; }
.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(560px, 1fr));
    gap: 16px; margin: 15px 0;
    min-width: 560px;
}
.chart-box {
    background: #f9fafb; border: 1px solid #e5e7eb;
    border-radius: 8px; padding: 8px;
}
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #1e3a8a; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }
td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
tr:nth-child(even) td { background: #f9fafb; }
tr:hover td { background: #eff6ff; }
.tag {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 11px; font-weight: 600; margin: 2px;
}
.tag-blue { background: #dbeafe; color: #1e40af; }
.tag-green { background: #dcfce7; color: #166534; }
.tag-orange { background: #ffedd5; color: #9a3412; }
.filtro-tag {
    display: inline-block; background: #e0e7ff; color: #3730a3;
    border-left: 3px solid #6366f1; padding: 5px 12px;
    border-radius: 0 4px 4px 0; margin: 4px 6px 4px 0; font-size: 13px;
}
.text-snippet {
    background: #fef9c3; border-left: 3px solid #eab308;
    padding: 6px 10px; border-radius: 0 4px 4px 0;
    font-size: 12px; line-height: 1.5; color: #713f12;
}
.serie-card {
    border: 1px solid #e5e7eb; border-radius: 6px;
    padding: 12px 16px; margin: 8px 0; border-left: 4px solid #3b82f6;
}
.serie-card h4 { margin: 0 0 6px; color: #1e3a8a; }
.wildcard-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px; margin-top: 12px;
}
.wildcard-item {
    background: white; border: 1px solid #e0e7ff;
    border-left: 3px solid #6366f1; padding: 6px 10px;
    border-radius: 0 4px 4px 0; font-size: 12px;
}
.footer {
    text-align: center; color: #9ca3af; font-size: 12px;
    margin-top: 30px; padding: 20px; border-top: 1px solid #e5e7eb;
}
"""

_PLOTLY_CDN = '<script src="https://cdn.plot.ly/plotly-2.26.0.min.js" charset="utf-8"></script>'

_SKIP_VALS = {'nan', 'None', 'none', 'N/A', 'n/a', '', 'Não informado', 'NaN'}


# ---------------------------------------------------------------------------
# Helpers internos de módulo
# ---------------------------------------------------------------------------

def _contar_campo(cartas_dict: dict, campo: str, top_n: int = None) -> list:
    """Retorna lista de (valor, contagem) para um campo, ignorando nulos."""
    counter = Counter()
    for carta in cartas_dict.values():
        val = carta.get(campo)
        val_str = str(val).strip() if val is not None else ''
        if val_str and val_str not in _SKIP_VALS:
            counter[val_str] += 1
    return counter.most_common(top_n) if top_n else counter.most_common()


_FONT = dict(family='Segoe UI, Tahoma, Geneva, Verdana, sans-serif', size=13)
_CHART_W = 560   # largura fixa; autosize=False garante que nunca é alterada


def _gerar_graficos_html(cartas_dict: dict) -> str:
    """Gera HTML com gráficos Plotly embutidos para um conjunto de cartas."""
    if not PLOTLY_AVAILABLE or not cartas_dict:
        return "<p><em>Gráficos não disponíveis.</em></p>"

    charts = []

    def _to_html(fig):
        # responsive=False + autosize=False: Plotly usa exatamente width/height do layout,
        # independente do tamanho do container. Elimina qualquer escalonamento proporcional.
        return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                           config={'responsive': False, 'displayModeBar': False})

    def _hbar(fig, labels, values):
        """Barra horizontal com dimensões completamente fixas."""
        n = len(labels)
        max_label = max((len(str(lb)) for lb in labels), default=10)
        left_m = max(130, min(240, max_label * 8 + 20))
        height = max(280, n * 36 + 100)
        max_val = max(values) if values else 1

        fig.update_traces(
            texttemplate='%{x:.0f}',
            textposition='outside',
            cliponaxis=False,
            hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>',
        )
        fig.update_layout(
            width=_CHART_W,
            height=height,
            autosize=False,
            margin=dict(t=55, b=20, l=left_m, r=65),
            showlegend=False,
            coloraxis_showscale=False,
            xaxis=dict(
                title='Quantidade',
                showgrid=True, gridcolor='rgba(0,0,0,0.06)',
                range=[0, max_val * 1.18],
            ),
            yaxis=dict(title='', categoryorder='total ascending', tickfont=dict(size=12)),
            plot_bgcolor='white', paper_bgcolor='white',
            font=_FONT, title_font_size=15,
        )
        return _to_html(fig)

    def _vbar(fig, labels, values):
        """Barra vertical com dimensões completamente fixas."""
        max_label = max((len(str(lb)) for lb in labels), default=6)
        bottom_m = max(80, min(170, max_label * 5 + 55))
        max_val = max(values) if values else 1

        fig.update_traces(
            texttemplate='%{y:.0f}',
            textposition='outside',
            cliponaxis=False,
            hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<extra></extra>',
        )
        fig.update_layout(
            width=_CHART_W,
            height=440,
            autosize=False,
            margin=dict(t=55, b=bottom_m, l=65, r=25),
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(
                title='Quantidade',
                showgrid=True, gridcolor='rgba(0,0,0,0.06)',
                range=[0, max_val * 1.15],
            ),
            xaxis=dict(title='', tickfont=dict(size=12)),
            plot_bgcolor='white', paper_bgcolor='white',
            font=_FONT, title_font_size=15,
        )
        return _to_html(fig)

    # 1. Sexo — barra horizontal
    data = _contar_campo(cartas_dict, 'sexo')
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Distribuição por Sexo",
                     color=list(values), color_continuous_scale='Blues')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 2. UF — barra horizontal top 15
    data = _contar_campo(cartas_dict, 'uf', top_n=15)
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Cartas por Estado (Top 15)",
                     color=list(values), color_continuous_scale='Blues')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 3. Faixa Etária — barra vertical
    data = _contar_campo(cartas_dict, 'faixa_etaria')
    if data:
        data_sorted = sorted(data, key=lambda x: x[0])
        labels, values = zip(*data_sorted)
        fig = px.bar(x=list(labels), y=list(values), title="Distribuição por Faixa Etária",
                     color=list(values), color_continuous_scale='Teal')
        fig.update_xaxes(tickangle=-40)
        charts.append(f'<div class="chart-box">{_vbar(fig, labels, values)}</div>')

    # 4. Estado Civil — barra horizontal
    data = _contar_campo(cartas_dict, 'estado_civil')
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Estado Civil",
                     color=list(values), color_continuous_scale='Teal')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 5. Instrução — barra horizontal
    data = _contar_campo(cartas_dict, 'instrucao', top_n=10)
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Escolaridade",
                     color=list(values), color_continuous_scale='Greens')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 6. Faixa de Renda — barra horizontal
    data = _contar_campo(cartas_dict, 'faixa_renda', top_n=10)
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Faixa de Renda",
                     color=list(values), color_continuous_scale='Oranges')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 7. Atividade/Ocupação — barra horizontal top 15
    data = _contar_campo(cartas_dict, 'atividade', top_n=15)
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Atividade / Ocupação (Top 15)",
                     color=list(values), color_continuous_scale='Purples')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 8. Zona Urbana/Rural — barra horizontal
    data = _contar_campo(cartas_dict, 'morador')
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Zona (Urbana / Rural)",
                     color=list(values), color_continuous_scale='Greens')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    # 9. Origem — barra vertical top 10
    data = _contar_campo(cartas_dict, 'origem', top_n=10)
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(labels), y=list(values), title="Cartas por Origem",
                     color=list(values), color_continuous_scale='Reds')
        fig.update_xaxes(tickangle=-40)
        charts.append(f'<div class="chart-box">{_vbar(fig, labels, values)}</div>')

    # 10. Catálogos — barra horizontal top 10
    data = _contar_campo(cartas_dict, 'catalogo', top_n=10)
    if data:
        labels, values = zip(*data)
        fig = px.bar(x=list(values), y=list(labels), orientation='h',
                     title="Catálogos Mais Frequentes (Top 10)",
                     color=list(values), color_continuous_scale='Cividis')
        charts.append(f'<div class="chart-box">{_hbar(fig, labels, values)}</div>')

    if not charts:
        return "<p><em>Dados insuficientes para gerar gráficos com os campos disponíveis.</em></p>"

    return f'<div class="charts-scroll"><div class="charts-grid">{"".join(charts)}</div></div>'


def _gerar_graficos_pdf(cartas_dict: dict) -> list:
    """Gera lista de Table flowables com gráficos matplotlib para inserção em PDF."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    try:
        from reportlab.platypus import Image as RLImage, Table as RLTable, TableStyle
        from reportlab.lib.units import cm as RL_CM
    except ImportError:
        return []

    if not cartas_dict:
        return []

    CHART_W_CM = 7.8
    CHART_W_IN = CHART_W_CM / 2.54

    plt.rcParams.update({'font.size': 8, 'axes.titlesize': 9})

    def _make_hbar(data, titulo, color):
        labels, values = zip(*data)
        n = len(labels)
        h_in = max(2.2, n * 0.32 + 0.7)
        fig, ax = plt.subplots(figsize=(CHART_W_IN, h_in))
        ax.barh(range(n), values, color=color, edgecolor='white', linewidth=0.4)
        ax.set_yticks(range(n))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel('Qtd.', fontsize=7)
        ax.set_title(titulo, fontsize=8.5, fontweight='bold', pad=4)
        ax.set_xlim(0, max(values) * 1.18)
        for i, val in enumerate(values):
            ax.text(val + max(values) * 0.02, i, str(val), va='center', fontsize=6.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', alpha=0.25, linewidth=0.5)
        plt.tight_layout(pad=0.4)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return RLImage(buf, width=CHART_W_CM * RL_CM, height=h_in * 2.54 * RL_CM)

    specs = [
        ('sexo',        'Distribuição por Sexo',           '#3b82f6', None),
        ('uf',          'Cartas por Estado (Top 10)',       '#1d4ed8', 10),
        ('faixa_etaria','Faixa Etária',                    '#0891b2', None),
        ('estado_civil','Estado Civil',                    '#0891b2', None),
        ('instrucao',   'Escolaridade (Top 10)',            '#059669', 10),
        ('faixa_renda', 'Faixa de Renda (Top 10)',          '#d97706', 10),
        ('atividade',   'Atividade / Ocupação (Top 10)',    '#7c3aed', 10),
        ('morador',     'Zona (Urbana / Rural)',            '#059669', None),
    ]

    images = []
    for campo, titulo, color, top_n in specs:
        data = _contar_campo(cartas_dict, campo, top_n=top_n)
        if not data:
            continue
        try:
            images.append(_make_hbar(data, titulo, color))
        except Exception:
            continue

    if not images:
        return []

    col_w = 8.5 * RL_CM
    flowables = []
    for i in range(0, len(images), 2):
        row = [[images[i], images[i + 1] if i + 1 < len(images) else '']]
        t = RLTable(row, colWidths=[col_w, col_w])
        t.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 3),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 3),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables.append(t)

    return flowables


def _base_html(title: str, body: str) -> str:
    """Monta o documento HTML completo com head, CSS e Plotly CDN."""
    ts = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {_PLOTLY_CDN}
    <style>{_CSS}</style>
</head>
<body>
<div class="container">
{body}
<div class="footer">
    <p>📚 <strong>Historicidades Democráticas</strong> — Plataforma de Análise de Documentos Históricos</p>
    <p>Relatório gerado em {ts}</p>
</div>
</div>
</body>
</html>"""


def _tabela_cartas_html(cartas_dict: dict, ids_lista: list, anotacoes: dict,
                        ocorrencias: dict = None) -> str:
    """Gera tabela HTML detalhada com metadados completos de cada carta."""
    rows = ""
    for carta_id in ids_lista:
        c = cartas_dict.get(carta_id, {})
        autor = c.get('nome', 'N/A')
        municipio = c.get('municipio', '') or ''
        uf = c.get('uf', '') or ''
        local = f"{municipio}/{uf}" if municipio and uf and municipio not in _SKIP_VALS else (uf or "N/A")
        sexo = c.get('sexo', 'N/A') or 'N/A'
        estado_civil = c.get('estado_civil', 'N/A') or 'N/A'
        faixa_etaria = c.get('faixa_etaria', 'N/A') or 'N/A'
        faixa_renda = c.get('faixa_renda', 'N/A') or 'N/A'
        instrucao = c.get('instrucao', 'N/A') or 'N/A'
        atividade = c.get('atividade', 'N/A') or 'N/A'
        morador = c.get('morador', 'N/A') or 'N/A'
        catalogo = c.get('catalogo', '') or ''
        indexacao = c.get('indexacao', '') or ''
        data_carta = c.get('data', '') or ''
        anotacao = anotacoes.get(carta_id, '')
        texto = c.get('texto', '') or ''
        snippet = texto[:250].replace('\n', ' ').strip()
        if len(texto) > 250:
            snippet += "…"

        occ_cell = ""
        if ocorrencias:
            n_occ = ocorrencias.get(carta_id, 0)
            occ_cell = f'<br><small style="color:#6b7280">{n_occ} ocorr.</small>'

        anotacao_badge = '<span class="tag tag-green">✓ Sim</span>' if anotacao else \
                         '<span style="color:#d1d5db">—</span>'

        rows += f"""<tr>
            <td><strong>#{carta_id}</strong>{occ_cell}</td>
            <td>{autor}<br><small style="color:#9ca3af">{data_carta}</small></td>
            <td>{local}<br><small style="color:#9ca3af">{morador}</small></td>
            <td style="font-size:11px; line-height:1.6">
                <b>Sexo:</b> {sexo}<br>
                <b>Est.Civil:</b> {estado_civil}<br>
                <b>Idade:</b> {faixa_etaria}<br>
                <b>Renda:</b> {faixa_renda}<br>
                <b>Instrução:</b> {instrucao}<br>
                <b>Atividade:</b> {atividade}
            </td>
            <td style="font-size:11px">{catalogo}<br><em style="color:#6b7280">{indexacao}</em></td>
            <td><div class="text-snippet">{snippet}</div></td>
            <td style="text-align:center">{anotacao_badge}</td>
        </tr>"""

    return f"""<div style="overflow-x:auto"><table>
        <thead><tr>
            <th>ID</th><th>Autor / Data</th><th>Localidade / Zona</th>
            <th>Perfil Demográfico</th><th>Catálogo / Indexação</th>
            <th>Trecho do Texto</th><th>Anotação</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table></div>"""


# ---------------------------------------------------------------------------
# ExportManager
# ---------------------------------------------------------------------------

class ExportManager:
    """Gerencia exportação de dados em múltiplos formatos."""

    @staticmethod
    def exportar_serie_csv(
        cartas: Dict,
        ids_serie: List[str],
        nome_serie: str,
        anotacoes: Dict[str, str],
        series: Dict = None
    ) -> bytes:
        """Exporta lista de cartas como CSV com todos os metadados e séries vinculadas."""
        # Índice carta_id → séries (a partir do SeriesManager, se fornecido)
        carta_series_idx: Dict[str, list] = {}
        if series:
            for ns, si in series.items():
                for cid in si['cartas']:
                    carta_series_idx.setdefault(cid, []).append(ns)
            for cid in carta_series_idx:
                carta_series_idx[cid] = sorted(carta_series_idx[cid])

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)

        writer.writerow([
            'SERIES_TEMATICAS',
            'LINHA_BASE_SAIC', 'NOME', 'DESTINATARIO', 'CATALOGO', 'INDEXACAO', 'ORIGEM', 'DATA',
            'FORMUL', 'DV', 'DATA2', 'MUNICIPIO', 'UF', 'CEP', 'SEXO', 'MORADOR', 'INSTRUCAO',
            'ESTADO CIVIL', 'FAIXA ETÁRIA', 'FAIXA RENDA', 'ATIVIDADE', 'TEXTO', 'ANOTACOES'
        ])

        for carta_id in ids_serie:
            if carta_id in cartas:
                c = cartas[carta_id]
                series_str = ' | '.join(carta_series_idx.get(carta_id, []))
                writer.writerow([
                    series_str,
                    carta_id,
                    c.get('nome', ''),
                    c.get('destinatario', ''),
                    c.get('catalogo', ''),
                    c.get('indexacao', ''),
                    c.get('origem', ''),
                    c.get('data', ''),
                    c.get('formul', ''),
                    c.get('dv', ''),
                    c.get('data2', ''),
                    c.get('municipio', ''),
                    c.get('uf', ''),
                    c.get('cep', ''),
                    c.get('sexo', ''),
                    c.get('morador', ''),
                    c.get('instrucao', ''),
                    c.get('estado_civil', ''),
                    c.get('faixa_etaria', ''),
                    c.get('faixa_renda', ''),
                    c.get('atividade', ''),
                    c.get('texto', ''),
                    anotacoes.get(carta_id, '')
                ])

        return output.getvalue().encode('utf-8-sig')

    @staticmethod
    def exportar_serie_json(
        cartas: Dict,
        ids_serie: List[str],
        nome_serie: str,
        anotacoes: Dict[str, str]
    ) -> str:
        """Exporta lista de cartas como JSON com todos os metadados."""
        serie_data = {
            'nome': nome_serie,
            'data_exportacao': datetime.now().isoformat(),
            'total_cartas': len(ids_serie),
            'cartas': []
        }

        for carta_id in ids_serie:
            if carta_id in cartas:
                c = cartas[carta_id]
                serie_data['cartas'].append({
                    'linha': carta_id,
                    'nome': c.get('nome', ''),
                    'destinatario': c.get('destinatario', ''),
                    'catalogo': c.get('catalogo', ''),
                    'indexacao': c.get('indexacao', ''),
                    'origem': c.get('origem', ''),
                    'data': c.get('data', ''),
                    'formul': c.get('formul', ''),
                    'dv': c.get('dv', ''),
                    'data2': c.get('data2', ''),
                    'municipio': c.get('municipio', ''),
                    'uf': c.get('uf', ''),
                    'cep': c.get('cep', ''),
                    'sexo': c.get('sexo', ''),
                    'morador': c.get('morador', ''),
                    'instrucao': c.get('instrucao', ''),
                    'estado_civil': c.get('estado_civil', ''),
                    'faixa_etaria': c.get('faixa_etaria', ''),
                    'faixa_renda': c.get('faixa_renda', ''),
                    'atividade': c.get('atividade', ''),
                    'texto': c.get('texto', ''),
                    'anotacoes': anotacoes.get(carta_id, ''),
                    'series': c.get('series', [])
                })

        return json.dumps(serie_data, ensure_ascii=False, indent=2)

    @staticmethod
    def exportar_caderno_markdown(caderno_texto: str, titulo: str = "Caderno de Pesquisa") -> str:
        """Exporta caderno de pesquisa como Markdown."""
        return f"""# {titulo}

*Exportado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}*

---

{caderno_texto}

---

*Fim do documento*
"""

    @staticmethod
    def exportar_caderno_txt(caderno_texto: str, titulo: str = "Caderno de Pesquisa") -> str:
        """Exporta caderno de pesquisa como TXT."""
        return f"""{titulo}
{"=" * len(titulo)}

Exportado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

{"-" * 50}

{caderno_texto}

{"-" * 50}

Fim do documento
"""

    @staticmethod
    def exportar_todas_series_json(
        series: Dict,
        cartas: Dict,
        anotacoes: Dict[str, str]
    ) -> str:
        """Exporta todas as séries como JSON estruturado com metadados completos."""
        export_data = {
            'data_exportacao': datetime.now().isoformat(),
            'total_series': len(series),
            'series': {}
        }

        for nome_serie, serie_info in series.items():
            cartas_serie = []
            for carta_id in serie_info['cartas']:
                if carta_id in cartas:
                    c = cartas[carta_id]
                    cartas_serie.append({
                        'linha': carta_id,
                        'nome': c.get('nome', ''),
                        'destinatario': c.get('destinatario', ''),
                        'catalogo': c.get('catalogo', ''),
                        'indexacao': c.get('indexacao', ''),
                        'origem': c.get('origem', ''),
                        'data': c.get('data', ''),
                        'formul': c.get('formul', ''),
                        'dv': c.get('dv', ''),
                        'data2': c.get('data2', ''),
                        'municipio': c.get('municipio', ''),
                        'uf': c.get('uf', ''),
                        'cep': c.get('cep', ''),
                        'sexo': c.get('sexo', ''),
                        'morador': c.get('morador', ''),
                        'instrucao': c.get('instrucao', ''),
                        'estado_civil': c.get('estado_civil', ''),
                        'faixa_etaria': c.get('faixa_etaria', ''),
                        'faixa_renda': c.get('faixa_renda', ''),
                        'atividade': c.get('atividade', ''),
                        'texto': c.get('texto', ''),
                        'anotacoes': anotacoes.get(carta_id, ''),
                        'series': c.get('series', [])
                    })

            export_data['series'][nome_serie] = {
                'descricao': serie_info.get('descricao', ''),
                'criada_em': serie_info.get('criada_em', ''),
                'total_cartas': len(cartas_serie),
                'cartas': cartas_serie
            }

        return json.dumps(export_data, ensure_ascii=False, indent=2)

    @staticmethod
    def exportar_zip_completo(
        series: Dict,
        cartas: Dict,
        anotacoes: Dict[str, str],
        caderno: str
    ) -> bytes:
        """Exporta tudo (séries, caderno) como ZIP."""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            json_data = ExportManager.exportar_todas_series_json(series, cartas, anotacoes)
            zf.writestr('series.json', json_data)

            caderno_md = ExportManager.exportar_caderno_markdown(caderno)
            zf.writestr('caderno_pesquisa.md', caderno_md)

            for nome_serie, serie_info in series.items():
                ids_serie = list(serie_info['cartas'])
                csv_data = ExportManager.exportar_serie_csv(cartas, ids_serie, nome_serie, anotacoes, series=series)
                nome_arquivo = f"serie_{nome_serie.replace(' ', '_')}.csv"
                zf.writestr(nome_arquivo, csv_data)

            metadata = {
                'data_exportacao': datetime.now().isoformat(),
                'total_series': len(series),
                'total_cartas_com_anotacoes': sum(1 for a in anotacoes.values() if a.strip()),
                'tamanho_caderno_caracteres': len(caderno)
            }
            zf.writestr('metadados.json', json.dumps(metadata, ensure_ascii=False, indent=2))

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    # -----------------------------------------------------------------------
    # PDF
    # -----------------------------------------------------------------------

    @staticmethod
    def exportar_pdf(
        cartas: Dict,
        ids: List[str],
        titulo: str,
        anotacoes: Dict[str, str],
        scores: Optional[Dict[str, float]] = None,
        series: Dict = None
    ) -> bytes:
        """Gera PDF com capa e cartas completas (texto + todos os metadados e séries)."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )
        ss = getSampleStyleSheet()

        def _s(name, parent, **kw):
            return ParagraphStyle(name, parent=ss[parent], **kw)

        s_capa_titulo = _s('CapaTitulo', 'Title',
            fontSize=26, textColor=HexColor('#1e3a8a'),
            alignment=TA_CENTER, spaceAfter=6)
        s_capa_autor = _s('CapaAutor', 'Normal',
            fontSize=15, textColor=HexColor('#3b82f6'),
            alignment=TA_CENTER, spaceAfter=20)
        s_capa_doc = _s('CapaDoc', 'Normal',
            fontSize=17, textColor=HexColor('#1f2937'),
            fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=8)
        s_capa_meta = _s('CapaMeta', 'Normal',
            fontSize=11, textColor=HexColor('#6b7280'),
            alignment=TA_CENTER, spaceAfter=5)
        s_header = _s('CartaHeader', 'Heading2',
            fontSize=12, textColor=HexColor('#1e3a8a'),
            spaceBefore=10, spaceAfter=5)
        s_label = _s('MetaLabel', 'Normal',
            fontSize=9, textColor=HexColor('#374151'),
            fontName='Helvetica-Bold')
        s_meta = _s('MetaVal', 'Normal',
            fontSize=9, textColor=HexColor('#374151'))
        s_texto = _s('Texto', 'Normal',
            fontSize=10, textColor=HexColor('#111827'),
            alignment=TA_JUSTIFY, spaceAfter=4, leading=14)
        s_series_hl = _s('SeriesHL', 'Normal',
            fontSize=9, textColor=HexColor('#1e40af'),
            fontName='Helvetica-Bold',
            backColor=HexColor('#dbeafe'),
            borderColor=HexColor('#3b82f6'),
            borderWidth=0.5,
            borderPadding=5,
            spaceBefore=4, spaceAfter=6)

        def esc(txt):
            if not txt:
                return ''
            return str(txt).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        def fmt(val):
            v = str(val).strip() if val is not None else ''
            return v if v and v not in _SKIP_VALS else ''

        # Índice carta_id → séries (a partir do SeriesManager, se fornecido)
        carta_series_idx: Dict[str, list] = {}
        if series:
            for ns, si in series.items():
                for cid in si['cartas']:
                    carta_series_idx.setdefault(cid, []).append(ns)
            for cid in carta_series_idx:
                carta_series_idx[cid] = sorted(carta_series_idx[cid])

        story = []

        # ---- CAPA ----
        story.append(Spacer(1, 5*cm))
        story.append(Paragraph("Historicidades Democráticas", s_capa_titulo))
        story.append(Paragraph("por Walderez Ramalho", s_capa_autor))
        story.append(HRFlowable(width="70%", thickness=2,
                                 color=HexColor('#3b82f6'),
                                 spaceAfter=20, spaceBefore=10))
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph(esc(titulo), s_capa_doc))
        story.append(Spacer(1, 0.5*cm))
        n_validos = sum(1 for i in ids if i in cartas)
        story.append(Paragraph(f"Total de cartas: {n_validos}", s_capa_meta))
        story.append(Paragraph(
            f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            s_capa_meta))
        story.append(PageBreak())

        # ---- CARTAS ----
        # Usamos apenas Paragraph (nunca Table) para metadados, pois Table não
        # consegue quebrar uma linha maior que a página (LayoutError).
        for carta_id in ids:
            if carta_id not in cartas:
                continue
            c = cartas[carta_id]

            autor = fmt(c.get('nome'))
            header_txt = f"Carta #{esc(carta_id)}"
            if autor:
                header_txt += f" — {esc(autor)}"
            story.append(Paragraph(header_txt, s_header))

            campos = [
                ("Destinatário",  fmt(c.get('destinatario'))),
                ("Data",          fmt(c.get('data'))),
                ("Município",     fmt(c.get('municipio'))),
                ("UF",            fmt(c.get('uf'))),
                ("Catálogo",      fmt(c.get('catalogo'))),
                ("Indexação",     fmt(c.get('indexacao'))),
                ("Origem",        fmt(c.get('origem'))),
                ("Sexo",          fmt(c.get('sexo'))),
                ("Faixa Etária",  fmt(c.get('faixa_etaria'))),
                ("Instrução",     fmt(c.get('instrucao'))),
                ("Atividade",     fmt(c.get('atividade'))),
                ("Morador",       fmt(c.get('morador'))),
                ("Estado Civil",  fmt(c.get('estado_civil'))),
                ("Faixa Renda",   fmt(c.get('faixa_renda'))),
            ]
            if scores and carta_id in scores:
                campos.append(("Score", f"{scores[carta_id]:.4f}"))

            # Dois campos por linha separados por espaço — Paragraph quebra
            # naturalmente entre páginas, eliminando o LayoutError do Table.
            for i in range(0, len(campos), 2):
                l1, v1 = campos[i]
                v1_txt = esc(v1) if v1 else "—"
                if i + 1 < len(campos):
                    l2, v2 = campos[i + 1]
                    v2_txt = esc(v2) if v2 else "—"
                    line = (f"<b>{esc(l1)}:</b> {v1_txt}"
                            f"&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
                            f"<b>{esc(l2)}:</b> {v2_txt}")
                else:
                    line = f"<b>{esc(l1)}:</b> {v1_txt}"
                story.append(Paragraph(line, s_meta))

            story.append(Spacer(1, 0.2*cm))

            series_carta = carta_series_idx.get(carta_id, [])
            if series_carta:
                story.append(Paragraph(
                    f"Séries Temáticas: {esc(', '.join(series_carta))}",
                    s_series_hl))

            texto = (c.get('texto', '') or '').strip()
            if texto:
                story.append(Paragraph("<b>Texto:</b>", s_label))
                story.append(Paragraph(esc(texto), s_texto))

            anotacao = (anotacoes.get(carta_id, '') or '').strip()
            if anotacao:
                story.append(Paragraph("<b>Anotações:</b>", s_label))
                story.append(Paragraph(esc(anotacao), s_texto))

            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=HexColor('#d1d5db'),
                                     spaceAfter=6, spaceBefore=6))

        # ---- GRÁFICOS ----
        cartas_subset = {k: cartas[k] for k in ids if k in cartas}
        graficos = _gerar_graficos_pdf(cartas_subset)
        if graficos:
            story.append(PageBreak())
            from reportlab.lib.styles import ParagraphStyle as _PS
            s_sec = _PS('SecGraf', parent=ss['Heading1'],
                        fontSize=14, textColor=HexColor('#1e3a8a'),
                        spaceBefore=0, spaceAfter=8)
            story.append(Paragraph("Análise Estatística", s_sec))
            story.append(HRFlowable(width="100%", thickness=1.5,
                                     color=HexColor('#3b82f6'),
                                     spaceAfter=10, spaceBefore=2))
            story.extend(graficos)

        doc.build(story)
        return buf.getvalue()

    # -----------------------------------------------------------------------
    # RELATÓRIOS HTML
    # -----------------------------------------------------------------------

    @staticmethod
    def exportar_todas_series_csv(
        series: Dict,
        cartas: Dict,
        anotacoes: Dict[str, str]
    ) -> str:
        """Exporta todas as séries como CSV unificado.

        Cada carta aparece uma única vez. A coluna SERIES_TEMATICAS lista todas
        as séries às quais a carta pertence, separadas por ' | '.
        """
        # Índice invertido: carta_id → lista ordenada de séries
        carta_series: Dict[str, list] = {}
        for nome_serie, serie_info in series.items():
            for carta_id in serie_info['cartas']:
                carta_series.setdefault(carta_id, []).append(nome_serie)
        for cid in carta_series:
            carta_series[cid] = sorted(carta_series[cid])

        all_ids = list(carta_series.keys())
        try:
            all_ids = sorted(all_ids, key=lambda x: int(x))
        except (ValueError, TypeError):
            all_ids = sorted(all_ids)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)

        writer.writerow([
            'SERIES_TEMATICAS',
            'LINHA_BASE_SAIC', 'NOME', 'DESTINATARIO', 'CATALOGO', 'INDEXACAO', 'ORIGEM', 'DATA',
            'FORMUL', 'DV', 'DATA2', 'MUNICIPIO', 'UF', 'CEP', 'SEXO', 'MORADOR', 'INSTRUCAO',
            'ESTADO CIVIL', 'FAIXA ETÁRIA', 'FAIXA RENDA', 'ATIVIDADE', 'TEXTO', 'ANOTACOES'
        ])

        for carta_id in all_ids:
            if carta_id in cartas:
                c = cartas[carta_id]
                series_str = ' | '.join(carta_series.get(carta_id, []))
                writer.writerow([
                    series_str, carta_id,
                    c.get('nome', ''), c.get('destinatario', ''),
                    c.get('catalogo', ''), c.get('indexacao', ''),
                    c.get('origem', ''), c.get('data', ''),
                    c.get('formul', ''), c.get('dv', ''), c.get('data2', ''),
                    c.get('municipio', ''), c.get('uf', ''), c.get('cep', ''),
                    c.get('sexo', ''), c.get('morador', ''),
                    c.get('instrucao', ''), c.get('estado_civil', ''),
                    c.get('faixa_etaria', ''), c.get('faixa_renda', ''),
                    c.get('atividade', ''),
                    (c.get('texto', '') or '').replace('\n', ' '),
                    anotacoes.get(carta_id, '')
                ])

        return output.getvalue().encode('utf-8-sig')

    @staticmethod
    def exportar_todas_series_pdf(
        series: Dict,
        cartas: Dict,
        anotacoes: Dict[str, str]
    ) -> bytes:
        """Gera PDF unificado com todas as cartas vinculadas a séries.

        Cada carta aparece uma única vez, com destaque visual indicando todas as
        séries às quais pertence. Inclui índice de séries e gráficos estatísticos.
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )
        ss = getSampleStyleSheet()

        def _s(name, parent, **kw):
            return ParagraphStyle(name, parent=ss[parent], **kw)

        s_capa_titulo = _s('CapaTitulo2', 'Title',
            fontSize=26, textColor=HexColor('#1e3a8a'),
            alignment=TA_CENTER, spaceAfter=6)
        s_capa_autor = _s('CapaAutor2', 'Normal',
            fontSize=15, textColor=HexColor('#3b82f6'),
            alignment=TA_CENTER, spaceAfter=20)
        s_capa_doc = _s('CapaDoc2', 'Normal',
            fontSize=17, textColor=HexColor('#1f2937'),
            fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=8)
        s_capa_meta = _s('CapaMeta2', 'Normal',
            fontSize=11, textColor=HexColor('#6b7280'),
            alignment=TA_CENTER, spaceAfter=5)
        s_serie_titulo = _s('SerieTitulo2', 'Heading1',
            fontSize=16, textColor=HexColor('#1e3a8a'),
            spaceBefore=6, spaceAfter=4)
        s_serie_desc = _s('SerieDesc2', 'Normal',
            fontSize=11, textColor=HexColor('#4b5563'),
            spaceAfter=6)
        s_header = _s('CartaHeader2', 'Heading2',
            fontSize=12, textColor=HexColor('#1e3a8a'),
            spaceBefore=10, spaceAfter=5)
        s_label = _s('MetaLabel2', 'Normal',
            fontSize=9, textColor=HexColor('#374151'),
            fontName='Helvetica-Bold')
        s_meta = _s('MetaVal2', 'Normal',
            fontSize=9, textColor=HexColor('#374151'))
        s_texto = _s('Texto2', 'Normal',
            fontSize=10, textColor=HexColor('#111827'),
            alignment=TA_JUSTIFY, spaceAfter=4, leading=14)
        s_series_hl = _s('SeriesHL2', 'Normal',
            fontSize=9, textColor=HexColor('#1e40af'),
            fontName='Helvetica-Bold',
            backColor=HexColor('#dbeafe'),
            borderColor=HexColor('#3b82f6'),
            borderWidth=0.5,
            borderPadding=5,
            spaceBefore=4, spaceAfter=6)

        def esc(txt):
            if not txt:
                return ''
            return str(txt).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        def fmt(val):
            v = str(val).strip() if val is not None else ''
            return v if v and v not in _SKIP_VALS else ''

        # Índice invertido: carta_id → set de nomes de séries
        carta_series_index: Dict[str, list] = {}
        for nome_s, info_s in series.items():
            for cid in info_s['cartas']:
                carta_series_index.setdefault(cid, []).append(nome_s)
        for cid in carta_series_index:
            carta_series_index[cid] = sorted(carta_series_index[cid])

        story = []

        # ---- CAPA ----
        story.append(Spacer(1, 5*cm))
        story.append(Paragraph("Historicidades Democráticas", s_capa_titulo))
        story.append(Paragraph("por Walderez Ramalho", s_capa_autor))
        story.append(HRFlowable(width="70%", thickness=2,
                                 color=HexColor('#3b82f6'),
                                 spaceAfter=20, spaceBefore=10))
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph("Todas as Séries Temáticas", s_capa_doc))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Total de séries: {len(series)}", s_capa_meta))
        n_unicas = len(carta_series_index)
        story.append(Paragraph(f"Total de cartas únicas vinculadas: {n_unicas}", s_capa_meta))
        story.append(Paragraph(
            f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            s_capa_meta))
        story.append(PageBreak())

        # ---- ÍNDICE DE SÉRIES ----
        story.append(Paragraph("Índice de Séries", s_serie_titulo))
        story.append(HRFlowable(width="100%", thickness=1.5,
                                 color=HexColor('#3b82f6'),
                                 spaceAfter=8, spaceBefore=4))
        for i, nome_s in enumerate(sorted(series.keys()), 1):
            n_c = len(series[nome_s]['cartas'])
            desc_s = series[nome_s].get('descricao', '') or ''
            linha = f"<b>{i}. {esc(nome_s)}</b> — {n_c} carta(s)"
            if desc_s:
                linha += f" — <i>{esc(desc_s[:80])}{'…' if len(desc_s) > 80 else ''}</i>"
            story.append(Paragraph(linha, s_meta))
        story.append(PageBreak())

        # ---- CARTAS ÚNICAS ----
        all_ids = list(carta_series_index.keys())
        try:
            all_ids = sorted(all_ids, key=lambda x: int(x))
        except (ValueError, TypeError):
            all_ids = sorted(all_ids)

        story.append(Paragraph("Cartas Vinculadas às Séries", s_serie_titulo))
        story.append(HRFlowable(width="100%", thickness=1.5,
                                 color=HexColor('#3b82f6'),
                                 spaceAfter=6, spaceBefore=2))
        story.append(Paragraph(
            f"<b>Total de cartas únicas:</b> {len(all_ids)}",
            s_meta))
        story.append(Spacer(1, 0.3*cm))

        for carta_id in all_ids:
            if carta_id not in cartas:
                continue
            c = cartas[carta_id]

            autor = fmt(c.get('nome'))
            header_txt = f"Carta #{esc(carta_id)}"
            if autor:
                header_txt += f" — {esc(autor)}"
            story.append(Paragraph(header_txt, s_header))

            series_da_carta = carta_series_index.get(carta_id, [])
            story.append(Paragraph(
                f"Séries Temáticas: {esc(', '.join(series_da_carta))}",
                s_series_hl))

            campos = [
                ("Destinatário",  fmt(c.get('destinatario'))),
                ("Data",          fmt(c.get('data'))),
                ("Município",     fmt(c.get('municipio'))),
                ("UF",            fmt(c.get('uf'))),
                ("Catálogo",      fmt(c.get('catalogo'))),
                ("Indexação",     fmt(c.get('indexacao'))),
                ("Origem",        fmt(c.get('origem'))),
                ("Sexo",          fmt(c.get('sexo'))),
                ("Faixa Etária",  fmt(c.get('faixa_etaria'))),
                ("Instrução",     fmt(c.get('instrucao'))),
                ("Atividade",     fmt(c.get('atividade'))),
                ("Morador",       fmt(c.get('morador'))),
                ("Estado Civil",  fmt(c.get('estado_civil'))),
                ("Faixa Renda",   fmt(c.get('faixa_renda'))),
            ]

            for i in range(0, len(campos), 2):
                l1, v1 = campos[i]
                v1_txt = esc(v1) if v1 else "—"
                if i + 1 < len(campos):
                    l2, v2 = campos[i + 1]
                    v2_txt = esc(v2) if v2 else "—"
                    line = (f"<b>{esc(l1)}:</b> {v1_txt}"
                            f"&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
                            f"<b>{esc(l2)}:</b> {v2_txt}")
                else:
                    line = f"<b>{esc(l1)}:</b> {v1_txt}"
                story.append(Paragraph(line, s_meta))

            story.append(Spacer(1, 0.2*cm))

            texto = (c.get('texto', '') or '').strip()
            if texto:
                story.append(Paragraph("<b>Texto:</b>", s_label))
                story.append(Paragraph(esc(texto), s_texto))

            anotacao = (anotacoes.get(carta_id, '') or '').strip()
            if anotacao:
                story.append(Paragraph("<b>Anotações:</b>", s_label))
                story.append(Paragraph(esc(anotacao), s_texto))

            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=HexColor('#d1d5db'),
                                     spaceAfter=6, spaceBefore=6))

        # ---- GRÁFICOS ----
        cartas_series_subset = {cid: cartas[cid] for cid in carta_series_index if cid in cartas}
        graficos = _gerar_graficos_pdf(cartas_series_subset)
        if graficos:
            story.append(PageBreak())
            from reportlab.lib.styles import ParagraphStyle as _PS2
            s_sec2 = _PS2('SecGraf2', parent=ss['Heading1'],
                          fontSize=14, textColor=HexColor('#1e3a8a'),
                          spaceBefore=0, spaceAfter=8)
            story.append(Paragraph("Análise Estatística", s_sec2))
            story.append(HRFlowable(width="100%", thickness=1.5,
                                     color=HexColor('#3b82f6'),
                                     spaceAfter=10, spaceBefore=2))
            story.extend(graficos)

        doc.build(story)
        return buf.getvalue()

    @staticmethod
    def exportar_parquet(
        cartas: Dict,
        ids: List[str],
        anotacoes: Dict[str, str],
        series_idx: Dict[str, list] = None
    ) -> bytes:
        """Exporta lista de cartas como Parquet (via pandas + pyarrow)."""
        import pandas as pd

        rows = []
        for carta_id in ids:
            if carta_id not in cartas:
                continue
            c = cartas[carta_id]
            series_str = ' | '.join(sorted(series_idx.get(carta_id, []))) if series_idx else ''
            rows.append({
                'series_tematicas': series_str,
                'linha': carta_id,
                'nome': c.get('nome', '') or '',
                'destinatario': c.get('destinatario', '') or '',
                'catalogo': c.get('catalogo', '') or '',
                'indexacao': c.get('indexacao', '') or '',
                'origem': c.get('origem', '') or '',
                'data': c.get('data', '') or '',
                'formul': c.get('formul', '') or '',
                'dv': c.get('dv', '') or '',
                'data2': c.get('data2', '') or '',
                'municipio': c.get('municipio', '') or '',
                'uf': c.get('uf', '') or '',
                'cep': c.get('cep', '') or '',
                'sexo': c.get('sexo', '') or '',
                'morador': c.get('morador', '') or '',
                'instrucao': c.get('instrucao', '') or '',
                'estado_civil': c.get('estado_civil', '') or '',
                'faixa_etaria': c.get('faixa_etaria', '') or '',
                'faixa_renda': c.get('faixa_renda', '') or '',
                'atividade': c.get('atividade', '') or '',
                'texto': (c.get('texto', '') or '').replace('\n', ' '),
                'anotacoes': anotacoes.get(carta_id, '') or '',
            })

        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_parquet(buf, index=False, engine='pyarrow')
        buf.seek(0)
        return buf.getvalue()

    @staticmethod
    def gerar_relatorio_html(
        series: Dict,
        cartas: Dict,
        anotacoes: Dict[str, str],
        caderno: str
    ) -> str:
        """Relatório analítico completo da base com estatísticas, gráficos e séries."""
        n_total = len(cartas)
        n_annotated = sum(1 for a in anotacoes.values() if a.strip())
        n_series = len(series)

        ufs = {str(c.get('uf', '')).strip() for c in cartas.values()
               if c.get('uf') and str(c.get('uf')).strip() not in _SKIP_VALS}
        municipios = {str(c.get('municipio', '')).strip() for c in cartas.values()
                      if c.get('municipio') and str(c.get('municipio')).strip() not in _SKIP_VALS}
        autores = {str(c.get('nome', '')).strip() for c in cartas.values()
                   if c.get('nome') and str(c.get('nome')).strip() not in _SKIP_VALS | {'Anônimo'}}

        # Totais de cartas em séries
        total_cartas_series = sum(len(v.get('cartas', [])) for v in series.values())

        stats_html = f"""<div class="stats-grid">
            <div class="stat-box"><div class="stat-value">{n_total:,}</div><div class="stat-label">Total de Cartas</div></div>
            <div class="stat-box"><div class="stat-value">{len(ufs)}</div><div class="stat-label">Estados (UF)</div></div>
            <div class="stat-box"><div class="stat-value">{len(municipios):,}</div><div class="stat-label">Municípios</div></div>
            <div class="stat-box"><div class="stat-value">{len(autores):,}</div><div class="stat-label">Autores Únicos</div></div>
            <div class="stat-box"><div class="stat-value">{n_annotated}</div><div class="stat-label">Com Anotações</div></div>
            <div class="stat-box"><div class="stat-value">{n_series}</div><div class="stat-label">Séries Temáticas</div></div>
            <div class="stat-box"><div class="stat-value">{total_cartas_series}</div><div class="stat-label">Cartas em Séries</div></div>
        </div>"""

        # Gráficos
        graficos_html = _gerar_graficos_html(cartas)

        # Tabela Top Municípios
        mun_data = _contar_campo(cartas, 'municipio', top_n=20)
        mun_rows = "".join(
            f"<tr><td>{i+1}</td><td>{lb}</td><td>{ct}</td><td>{round(ct/n_total*100,1)}%</td></tr>"
            for i, (lb, ct) in enumerate(mun_data)
        )
        mun_table = f"""<table>
            <thead><tr><th>#</th><th>Município</th><th>Cartas</th><th>% do Total</th></tr></thead>
            <tbody>{mun_rows}</tbody>
        </table>"""

        # Tabela Top UFs
        uf_data = _contar_campo(cartas, 'uf')
        uf_rows = "".join(
            f"<tr><td>{i+1}</td><td>{lb}</td><td>{ct}</td><td>{round(ct/n_total*100,1)}%</td></tr>"
            for i, (lb, ct) in enumerate(uf_data)
        )
        uf_table = f"""<table>
            <thead><tr><th>#</th><th>Estado</th><th>Cartas</th><th>% do Total</th></tr></thead>
            <tbody>{uf_rows}</tbody>
        </table>"""

        # Séries
        series_html = ""
        if series:
            items = ""
            for nome, info in sorted(series.items()):
                total_s = len(info.get('cartas', []))
                descricao = info.get('descricao', '') or 'Sem descrição'
                criada = str(info.get('criada_em', ''))[:10] or 'N/A'
                pct_s = round(total_s / n_total * 100, 1) if n_total else 0
                items += f"""<div class="serie-card">
                    <h4>{nome} <span class="tag tag-blue">{total_s} cartas</span>
                        <span class="tag tag-orange">{pct_s}% da base</span></h4>
                    <p style="margin:4px 0;color:#555;font-size:13px">{descricao}</p>
                    <p style="margin:4px 0;color:#9ca3af;font-size:11px">Criada em: {criada}</p>
                </div>"""
            series_html = f'<div class="section"><h2>🗂️ Séries Temáticas</h2>{items}</div>'

        # Caderno
        caderno_html = ""
        if caderno and caderno.strip():
            esc = caderno.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            caderno_html = f"""<div class="section">
                <h2>📓 Caderno de Pesquisa</h2>
                <div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:6px;
                     padding:16px;white-space:pre-wrap;font-size:13px;line-height:1.7">{esc}</div>
            </div>"""

        body = f"""
        <div class="report-header">
            <h1>📚 Historicidades Democráticas</h1>
            <h2>Relatório Analítico da Base de Dados</h2>
            <div class="meta">
                <span>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                <span>📊 {n_total:,} documentos analisados</span>
            </div>
        </div>

        <div class="section">
            <h2>📊 Visão Geral da Base</h2>
            {stats_html}
        </div>

        <div class="section">
            <h2>📈 Análise Estatística — Gráficos Interativos</h2>
            <p style="color:#6b7280;font-size:13px;margin-top:0">
                Passe o mouse sobre os gráficos para ver valores detalhados.
                Os gráficos requerem conexão à internet para carregar.
            </p>
            {graficos_html}
        </div>

        <div class="section">
            <h2>🗺️ Distribuição Geográfica</h2>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
                <div>
                    <h3>Estados (UF) — Todos</h3>
                    {uf_table}
                </div>
                <div>
                    <h3>Municípios Mais Frequentes (Top 20)</h3>
                    {mun_table}
                </div>
            </div>
        </div>

        {series_html}
        {caderno_html}
        """

        return _base_html("Relatório Analítico — Historicidades Democráticas", body)

    @staticmethod
    def gerar_relatorio_busca_html(
        cartas: Dict,
        ids_resultado: List[str],
        ocorrencias: Dict,
        termo: str,
        escopo: str,
        anotacoes: Dict,
        wildcard_matches: Dict = None
    ) -> str:
        """Relatório HTML enriquecido dos resultados de busca, com gráficos e tabela completa."""
        if not ids_resultado:
            return "<html><body><h1>Nenhuma carta encontrada</h1></body></html>"

        n_base = len(cartas)
        n_resultado = len(ids_resultado)
        total_occ = sum(ocorrencias.values()) if ocorrencias else 0
        n_annotated = len([i for i in ids_resultado if anotacoes.get(i)])
        pct = round(n_resultado / n_base * 100, 1) if n_base else 0
        media_occ = round(total_occ / n_resultado, 1) if n_resultado else 0

        cartas_resultado = {k: cartas[k] for k in ids_resultado if k in cartas}

        stats_html = f"""<div class="stats-grid">
            <div class="stat-box"><div class="stat-value">{n_resultado}</div><div class="stat-label">Cartas Encontradas</div></div>
            <div class="stat-box"><div class="stat-value">{total_occ}</div><div class="stat-label">Ocorrências Totais</div></div>
            <div class="stat-box"><div class="stat-value">{media_occ}</div><div class="stat-label">Média por Carta</div></div>
            <div class="stat-box"><div class="stat-value">{n_annotated}</div><div class="stat-label">Com Anotações</div></div>
            <div class="stat-box"><div class="stat-value">{pct}%</div><div class="stat-label">da Base Total</div></div>
            <div class="stat-box"><div class="stat-value">{n_base:,}</div><div class="stat-label">Total na Base</div></div>
        </div>"""

        # Wildcard
        wildcard_html = ""
        if wildcard_matches:
            sorted_wc = sorted(wildcard_matches.items(), key=lambda x: -x[1])[:30]
            items = "".join(
                f'<div class="wildcard-item"><strong>{t}</strong> ({f}×)</div>'
                for t, f in sorted_wc
            )
            wildcard_html = f"""<div class="section">
                <h2>🔍 Formas Capturadas pelo Wildcard ({len(wildcard_matches)} distintas)</h2>
                <div class="wildcard-grid">{items}</div>
            </div>"""

        # Top 10 por ocorrências
        if ocorrencias:
            top10 = sorted(
                [(k, v) for k, v in ocorrencias.items() if k in cartas_resultado],
                key=lambda x: -x[1]
            )[:10]
            top10_rows = "".join(
                f"<tr><td>#{k}</td><td>{cartas.get(k, {}).get('nome', 'N/A')}</td>"
                f"<td>{cartas.get(k, {}).get('municipio', 'N/A')}/{cartas.get(k, {}).get('uf', '')}</td>"
                f"<td style='text-align:center'><strong>{v}</strong></td></tr>"
                for k, v in top10
            )
            top10_html = f"""<div class="section">
                <h2>🏆 Top 10 — Mais Ocorrências do Termo</h2>
                <table>
                    <thead><tr><th>ID</th><th>Autor</th><th>Localidade</th><th>Ocorrências</th></tr></thead>
                    <tbody>{top10_rows}</tbody>
                </table>
            </div>"""
        else:
            top10_html = ""

        graficos_html = _gerar_graficos_html(cartas_resultado)
        tabela_html = _tabela_cartas_html(cartas, ids_resultado, anotacoes, ocorrencias)

        body = f"""
        <div class="report-header">
            <h1>🔍 Relatório de Busca — Historicidades Democráticas</h1>
            <h2>Termo pesquisado: <em>"{termo}"</em></h2>
            <div class="meta">
                <span>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                <span>🔎 Escopo: {escopo}</span>
                <span>📊 Base total: {n_base:,} cartas</span>
            </div>
        </div>

        <div class="section">
            <h2>📊 Resumo dos Resultados</h2>
            {stats_html}
        </div>

        {wildcard_html}
        {top10_html}

        <div class="section">
            <h2>📈 Perfil dos Documentos Encontrados — Gráficos Interativos</h2>
            <p style="color:#6b7280;font-size:13px;margin-top:0">
                Análise demográfica e geográfica das {n_resultado} cartas encontradas.
            </p>
            {graficos_html}
        </div>

        <div class="section">
            <h2>📄 Listagem Completa das Cartas ({n_resultado})</h2>
            {tabela_html}
        </div>
        """

        return _base_html(f'Busca: "{termo}" — Historicidades Democráticas', body)

    @staticmethod
    def gerar_relatorio_filtros_html(
        cartas: Dict,
        ids_filtrados: List[str],
        filtros_ativos: Dict,
        campos_filtro_labels: Dict,
        anotacoes: Dict
    ) -> str:
        """Relatório HTML enriquecido dos resultados de filtragem, com gráficos e tabela completa."""
        if not ids_filtrados:
            return "<html><body><h1>Nenhuma carta encontrada com os filtros aplicados.</h1></body></html>"

        n_base = len(cartas)
        n_resultado = len(ids_filtrados)
        n_annotated = len([i for i in ids_filtrados if anotacoes.get(i)])
        pct = round(n_resultado / n_base * 100, 1) if n_base else 0
        n_filtros = len(filtros_ativos)

        cartas_filtradas = {k: cartas[k] for k in ids_filtrados if k in cartas}

        # Tags dos filtros
        filtros_tags = ""
        filtros_resumo_rows = ""
        for campo, valores in filtros_ativos.items():
            label = campos_filtro_labels.get(campo, campo)
            vals_str = ", ".join(str(v) for v in valores)
            filtros_tags += f'<span class="filtro-tag"><strong>{label}:</strong> {vals_str}</span>'
            filtros_resumo_rows += f"<tr><td>{label}</td><td>{vals_str}</td><td>{len(valores)}</td></tr>"

        filtros_table = f"""<table style="margin-top:12px">
            <thead><tr><th>Campo</th><th>Valores Selecionados</th><th>Qtd. Opções</th></tr></thead>
            <tbody>{filtros_resumo_rows}</tbody>
        </table>"""

        stats_html = f"""<div class="stats-grid">
            <div class="stat-box"><div class="stat-value">{n_resultado}</div><div class="stat-label">Cartas Encontradas</div></div>
            <div class="stat-box"><div class="stat-value">{n_filtros}</div><div class="stat-label">Filtros Ativos</div></div>
            <div class="stat-box"><div class="stat-value">{n_annotated}</div><div class="stat-label">Com Anotações</div></div>
            <div class="stat-box"><div class="stat-value">{pct}%</div><div class="stat-label">da Base Total</div></div>
            <div class="stat-box"><div class="stat-value">{n_base:,}</div><div class="stat-label">Total na Base</div></div>
        </div>"""

        # Distribuição geográfica nos resultados
        uf_data = _contar_campo(cartas_filtradas, 'uf')
        uf_rows = "".join(
            f"<tr><td>{lb}</td><td>{ct}</td><td>{round(ct/n_resultado*100,1)}%</td></tr>"
            for lb, ct in uf_data
        )
        uf_table = f"""<table>
            <thead><tr><th>Estado</th><th>Cartas</th><th>%</th></tr></thead>
            <tbody>{uf_rows}</tbody>
        </table>"""

        mun_data = _contar_campo(cartas_filtradas, 'municipio', top_n=15)
        mun_rows = "".join(
            f"<tr><td>{lb}</td><td>{ct}</td><td>{round(ct/n_resultado*100,1)}%</td></tr>"
            for lb, ct in mun_data
        )
        mun_table = f"""<table>
            <thead><tr><th>Município</th><th>Cartas</th><th>%</th></tr></thead>
            <tbody>{mun_rows}</tbody>
        </table>"""

        graficos_html = _gerar_graficos_html(cartas_filtradas)
        tabela_html = _tabela_cartas_html(cartas, ids_filtrados, anotacoes)

        body = f"""
        <div class="report-header">
            <h1>🎯 Relatório de Filtros — Historicidades Democráticas</h1>
            <h2>Filtragem avançada por características dos remetentes</h2>
            <div class="meta">
                <span>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                <span>⚙️ {n_filtros} filtro(s) aplicado(s)</span>
                <span>📊 Base total: {n_base:,} cartas</span>
            </div>
        </div>

        <div class="section">
            <h2>⚙️ Filtros Aplicados</h2>
            <div style="margin-bottom:12px">{filtros_tags}</div>
            {filtros_table}
        </div>

        <div class="section">
            <h2>📊 Resumo dos Resultados</h2>
            {stats_html}
        </div>

        <div class="section">
            <h2>🗺️ Distribuição Geográfica dos Resultados</h2>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
                <div><h3>Por Estado (UF)</h3>{uf_table}</div>
                <div><h3>Municípios (Top 15)</h3>{mun_table}</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Perfil dos Documentos Filtrados — Gráficos Interativos</h2>
            <p style="color:#6b7280;font-size:13px;margin-top:0">
                Análise demográfica e geográfica das {n_resultado} cartas filtradas.
            </p>
            {graficos_html}
        </div>

        <div class="section">
            <h2>📄 Listagem Completa das Cartas ({n_resultado})</h2>
            {tabela_html}
        </div>
        """

        return _base_html("Relatório de Filtros — Historicidades Democráticas", body)

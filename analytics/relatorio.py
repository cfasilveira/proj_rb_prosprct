"""Exportação das análises em PDF e CSV (PRD fase 2 — exportação de relatórios).

`gerar_pdf` é puro (sem Streamlit): recebe os blocos da página, usa kaleido
para rasterizar as figuras Plotly e reportlab para compor a página A4 na
horizontal. `gerar_csv` leva a mesma tabela exibida na tela, no formato que o
Excel em português abre no duplo clique (`;` + UTF-8 com BOM). Os botões de
download ficam em `ui.botao_pdf` e `ui.botao_csv`.
"""
from __future__ import annotations

import csv
from datetime import datetime
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

AZUL = colors.HexColor("#1B4DB1")
CINZA = colors.HexColor("#5F6368")
BORDA = colors.HexColor("#DADCE0")
FUNDO = colors.HexColor("#F7F8FA")

PAGINA = landscape(A4)
MARGEM = 14 * mm
# a frame do reportlab ainda desconta 6pt de padding de cada lado
LARGURA = PAGINA[0] - 2 * MARGEM - 12
ALTURA = PAGINA[1] - 2 * MARGEM - 12

_base = getSampleStyleSheet()
ST_TITULO = ParagraphStyle("titulo", parent=_base["Title"], fontSize=18, textColor=AZUL, spaceAfter=2)
ST_SUB = ParagraphStyle("sub", parent=_base["Normal"], fontSize=9, textColor=CINZA, spaceAfter=10)
ST_H2 = ParagraphStyle("h2", parent=_base["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
ST_CELULA = ParagraphStyle("celula", parent=_base["Normal"], fontSize=8.5, leading=11)
ST_LEGENDA = ParagraphStyle("legenda", parent=_base["Normal"], fontSize=8.5, textColor=CINZA, spaceBefore=2)
ST_KPI_ROTULO = ParagraphStyle("kpi_rotulo", parent=_base["Normal"], fontSize=8, textColor=CINZA)
ST_KPI_VALOR = ParagraphStyle("kpi_valor", parent=_base["Normal"], fontSize=18)


def grafico(titulo: str, figura, legenda: str | None = None) -> dict:
    return {"tipo": "grafico", "titulo": titulo, "figura": figura, "legenda": legenda}


def tabela(titulo: str, cabecalho: list[str], linhas: list[list]) -> dict:
    return {"tipo": "tabela", "titulo": titulo, "cabecalho": cabecalho, "linhas": linhas}


def kpis(itens: list[tuple[str, object]]) -> dict:
    return {"tipo": "kpis", "itens": itens}


def texto(conteudo: str) -> dict:
    return {"tipo": "texto", "conteudo": conteudo}


def _tabela(cabecalho: list[str], linhas: list[list]):
    dados = [[Paragraph(str(cab), ST_CELULA) for cab in cabecalho]]
    dados += [
        [Paragraph(str(celula) if celula is not None else "—", ST_CELULA) for celula in linha]
        for linha in (linhas or [])
    ]
    if len(dados) == 1:
        dados.append([Paragraph("—", ST_CELULA)] * len(cabecalho))
    largura = LARGURA / len(cabecalho)
    tabela_obj = Table(dados, colWidths=[largura] * len(cabecalho), repeatRows=1)
    tabela_obj.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), FUNDO),
                ("TEXTCOLOR", (0, 0), (-1, 0), CINZA),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFC")]),
            ]
        )
    )
    return tabela_obj


def _kpis(itens: list[tuple[str, object]]):
    rotulos = [Paragraph(str(rotulo), ST_KPI_ROTULO) for rotulo, _ in itens]
    valores = [Paragraph(f"<b>{valor}</b>", ST_KPI_VALOR) for _, valor in itens]
    coluna = LARGURA / max(len(itens), 1)
    tabela_obj = Table([rotulos, valores], colWidths=[coluna] * len(itens))
    tabela_obj.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDA),
                ("LINEAFTER", (0, 0), (-2, -1), 0.4, BORDA),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tabela_obj


def _figura(figura):
    """Rasteriza a figura Plotly com kaleido e devolve um bloco de imagem."""
    png = figura.to_image(format="png", width=1600, scale=2)
    largura_px, altura_px = ImageReader(BytesIO(png)).getSize()
    largura, altura = LARGURA, LARGURA * altura_px / largura_px
    if altura > ALTURA - 40:  # deixa espaço para o título do bloco
        escala = (ALTURA - 40) / altura
        largura, altura = largura * escala, ALTURA - 40
    return Image(BytesIO(png), width=largura, height=altura, hAlign="CENTER")


def gerar_pdf(titulo: str, subtitulo: str, blocos: list[dict]) -> bytes:
    """Compõe o PDF das análises e devolve os bytes prontos para download."""
    elementos: list = [
        Paragraph(titulo, ST_TITULO),
        Paragraph(f"{subtitulo} · Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ST_SUB),
    ]
    for bloco in blocos:
        tipo = bloco["tipo"]
        if tipo == "kpis":
            elementos.append(_kpis(bloco["itens"]))
        elif tipo == "grafico":
            blocinho = [Paragraph(bloco["titulo"], ST_H2), _figura(bloco["figura"])]
            if bloco.get("legenda"):
                blocinho.append(Paragraph(bloco["legenda"], ST_LEGENDA))
            elementos.append(KeepTogether(blocinho))
        elif tipo == "tabela":
            elementos.append(
                KeepTogether(
                    [Paragraph(bloco["titulo"], ST_H2), _tabela(bloco["cabecalho"], bloco["linhas"])]
                )
            )
        elif tipo == "texto":
            elementos.append(Paragraph(bloco["conteudo"], ST_LEGENDA))
        elementos.append(Spacer(1, 6))

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=PAGINA,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=MARGEM,
        bottomMargin=MARGEM,
        title=titulo,
        author="RB Prospecta",
    )
    documento.build(elementos)
    return buffer.getvalue()


SEPARADOR = ";"
BOM = "\ufeff"


def gerar_csv(linhas: list[dict], colunas: list[str] | None = None) -> bytes:
    """Tabela da análise em CSV: separador `;`, BOM e UTF-8 para o Excel pt-BR.

    `linhas` é o mesmo `list[dict]` entregue por `db.executar` (ou a projeção
    que a página exibe); `colunas` opcional fixa a ordem do cabeçalho. `None`
    vira célula vazia — é o que o `csv.writer` já faz.
    """
    colunas = colunas or (list(linhas[0]) if linhas else [])
    buffer = StringIO()
    escritor = csv.writer(buffer, delimiter=SEPARADOR, lineterminator="\r\n")
    escritor.writerow(colunas)
    for linha in linhas:
        escritor.writerow([linha.get(coluna) for coluna in colunas])
    return (BOM + buffer.getvalue()).encode("utf-8")


def completo(
    titulo: str = "RB Prospecta · Relatório completo",
    subtitulo: str = "Período: sempre · Todas as promotoras · Todas as cidades",
) -> bytes:
    """Roda A1–A4 com os filtros padrão e devolve um único PDF."""
    import db
    import graficos
    import queries

    filtros = dict(queries.PARAMS_PADRAO)
    a1 = db.executar(queries.SQL_A1, filtros)
    a2 = db.executar(queries.SQL_A2, filtros)[0]
    a2_cidade = db.executar(queries.SQL_A2_CIDADE, filtros)
    a3 = db.executar(queries.SQL_A3, filtros)
    a4 = db.executar(queries.SQL_A4, filtros)

    blocos: list[dict] = []
    if a1:
        total = sum(linha["cadastradas"] for linha in a1)
        ja_revendem = sum(linha["ja_revendem"] for linha in a1)
        blocos += [
            kpis(
                [("Cadastradas", total), ("Já revendem", ja_revendem), ("Promotoras ativas", len(a1))]
            ),
            grafico("A1 · Cadastros por promotora", graficos.a1(a1)),
            tabela(
                "A1 · Detalhe por promotora",
                ["Promotora", "Cadastradas", "Já revendem", "% já revendem"],
                [
                    [
                        linha["promotora_nome"],
                        linha["cadastradas"],
                        linha["ja_revendem"],
                        f'{linha["pct"] or 0}%',
                    ]
                    for linha in a1
                ],
            ),
        ]

    if a2["total"]:
        blocos += [
            kpis(
                [
                    ("Total cadastrado", a2["total"]),
                    ("Já revendem", a2["ja_revendem"]),
                    ("Conversão", f'{a2["pct"] or 0}%'),
                ]
            ),
            grafico("A2 · Quantas já revendem", graficos.a2(a2)),
        ]
        if a2_cidade:
            blocos.append(
                tabela(
                    "A2 · Por cidade",
                    ["Cidade", "Cadastradas", "Já revendem", "% já revendem"],
                    [
                        [c["cidade"], c["total"], c["ja_revendem"], f'{c["pct"] or 0}%']
                        for c in a2_cidade
                    ],
                )
            )

    if a3:
        blocos += [
            grafico("A3 · Marcas já revendidas", graficos.a3(a3)),
            tabela(
                "A3 · Detalhe por marca",
                ["Marca", "Revendedoras", "% das que já revendem"],
                [[m["marca"], m["revendedoras"], f'{m["pct"] or 0}%'] for m in a3],
            ),
        ]

    if a4:
        blocos += [
            grafico("A4 · Interesse em produtos", graficos.a4(a4)),
            tabela(
                "A4 · Detalhe por categoria",
                ["Categoria", "Interessadas", "%"],
                [[p["categoria"], p["interessadas"], f'{p["pct"] or 0}%'] for p in a4],
            ),
        ]

    if not blocos:
        blocos.append(texto("Nenhum dado no período selecionado."))

    return gerar_pdf(titulo, subtitulo, blocos)

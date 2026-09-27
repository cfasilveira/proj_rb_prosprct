"""Relatório em PDF do dashboard (PRD fase 2 — exportação de relatórios).

Só reportlab (sem navegador): o dashboard é texto + tabelas, não há gráfico
Plotly do lado Django — o PDF das análises fica em `analytics/relatorio.py`.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AZUL = colors.HexColor("#1B4DB1")
CINZA = colors.HexColor("#5F6368")
BORDA = colors.HexColor("#DADCE0")
FUNDO = colors.HexColor("#F7F8FA")
VERDE = colors.HexColor("#128C5A")

MARGEM = 16 * mm

_base = getSampleStyleSheet()
ST_TITULO = ParagraphStyle("titulo", parent=_base["Title"], fontSize=18, textColor=AZUL, spaceAfter=2)
ST_SUB = ParagraphStyle("sub", parent=_base["Normal"], fontSize=9, textColor=CINZA, spaceAfter=12)
ST_H2 = ParagraphStyle("h2", parent=_base["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=6)
ST_CELULA = ParagraphStyle("celula", parent=_base["Normal"], fontSize=9, leading=12)
ST_KPI_ROTULO = ParagraphStyle("kpi_rotulo", parent=_base["Normal"], fontSize=8, textColor=CINZA)
ST_KPI_VALOR = ParagraphStyle("kpi_valor", parent=_base["Normal"], fontSize=20, textColor=colors.black)


def _tabela(cabecalho: list[str], linhas: list[list], larguras: list[float] | None = None):
    dados = [cabecalho] + (linhas or [["—"] * len(cabecalho)])
    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), FUNDO),
                ("TEXTCOLOR", (0, 0), (-1, 0), CINZA),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFC")]),
            ]
        )
    )
    return tabela


def _kpis(total: int, ja_revendem: int, pct: int):
    rotulos = ["Cadastradas", "Já revendem", "Conversão"]
    valores = [str(total), str(ja_revendem), f"{pct}%"]
    linha_rotulo = [Paragraph(rotulo, ST_KPI_ROTULO) for rotulo in rotulos]
    linha_valor = [Paragraph(f"<b>{valor}</b>", ST_KPI_VALOR) for valor in valores]
    tabela = Table([linha_rotulo, linha_valor], colWidths=[56 * mm] * 3)
    tabela.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDA),
                ("LINEAFTER", (0, 0), (-2, -1), 0.4, BORDA),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tabela


def pdf_dashboard(
    *,
    perfil,
    periodo_nome: str,
    total: int,
    ja_revendem: int,
    pct: int,
    ultimos: list,
    por_promotora: list,
) -> bytes:
    """Monta o PDF do dashboard e devolve os bytes prontos para download."""
    escopo = "Carteira consolidada" if perfil.is_gestor else f"Carteira de {perfil.nome_completo}"
    elementos = [
        Paragraph("RB Prospecta — Dashboard", ST_TITULO),
        Paragraph(
            f"{escopo} · Período: {periodo_nome} · Emitido em "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
            ST_SUB,
        ),
        _kpis(total, ja_revendem, pct),
    ]

    if perfil.is_gestor:
        elementos.append(Paragraph("Cadastro por promotora", ST_H2))
        linhas = [
            [
                Paragraph(str(linha.get("promotora__perfil__nome_completo") or "—"), ST_CELULA),
                Paragraph(str(linha.get("promotora__perfil__territorio") or "—"), ST_CELULA),
                str(linha["total"]),
                str(linha["ja_revendem"]),
                f'{linha["pct"]}%',
            ]
            for linha in por_promotora
        ]
        elementos.append(
            _tabela(
                ["Promotora", "Território", "Cadastradas", "Já revendem", "Conversão"],
                linhas,
                [46 * mm, 38 * mm, 28 * mm, 28 * mm, 26 * mm],
            )
        )

    elementos.append(Paragraph("Últimos cadastros", ST_H2))
    linhas = [
        [
            Paragraph(r.nome_completo, ST_CELULA),
            Paragraph(str(r.cidade), ST_CELULA),
            Paragraph("sim" if r.ja_revende else "não", ST_CELULA),
            Paragraph(r.criado_em.strftime("%d/%m/%Y %H:%M"), ST_CELULA),
        ]
        for r in ultimos
    ]
    elementos.append(
        _tabela(
            ["Nome", "Cidade", "Já revende", "Cadastro"],
            linhas,
            [60 * mm, 45 * mm, 30 * mm, 41 * mm],
        )
    )

    elementos += [
        Spacer(1, 10),
        Paragraph(
            "Documento gerado pelo RB Prospecta. Dados pessoais (CPF, RG, e-mail) "
            "tratados conforme a política de privacidade (LGPD).",
            ST_SUB,
        ),
    ]

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=MARGEM,
        bottomMargin=MARGEM,
        title="RB Prospecta — Dashboard",
        author="RB Prospecta",
    )
    documento.build(elementos)
    return buffer.getvalue()

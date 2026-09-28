"""Exportação CSV do detalhe de revendedoras (PRD fase 2 — exportação de relatórios).

Formato pensado para o Excel em português: separador ``;`` e UTF-8 com BOM,
para o arquivo abrir no duplo clique com acentos e colunas corretas. O CSV é o
dado bruto por trás dos KPIs do dashboard — as agregações (A1–A4) saem nos CSVs
das análises. Cuidado LGPD: CPF, RG, e-mail e nascimento são exportados porque
o arquivo é do gestor, mas eles nunca aparecem nos relatórios em PDF.
"""
from __future__ import annotations

import csv
from io import StringIO

from django.db.models import Prefetch

from prospeccao.models import Telefone

SEPARADOR = ";"
BOM = "\ufeff"

COLUNAS = [
    "Nome completo",
    "CPF",
    "RG",
    "E-mail",
    "Data de nascimento",
    "Telefone(s)",
    "Cidade",
    "UF",
    "Bairro",
    "Endereço",
    "CEP",
    "Promotora",
    "Vende outras marcas",
    "Marcas revendidas",
    "Já revende",
    "Interesses",
    "Observação",
    "Cadastrada em",
]


def _sim_nao(valor) -> str:
    return "sim" if valor else "não"


def _data(valor, formato: str) -> str:
    return valor.strftime(formato) if valor else ""


def _cpf(valor: str | None) -> str:
    """CPF armazenado como 11 dígitos → máscara legível (o import volta a aceitar)."""
    if not valor or len(valor) != 11:
        return valor or ""
    return f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"


def _promotora(revendedora) -> str:
    perfil = getattr(revendedora.promotora, "perfil", None)
    return (perfil and perfil.nome_completo) or revendedora.promotora.email


def _prepara(queryset):
    """Seleciona o que o CSV lê para não disparar N+1 em cada linha."""
    return queryset.select_related("cidade", "promotora__perfil").prefetch_related(
        Prefetch("telefones", queryset=Telefone.objects.order_by("-principal", "numero")),
        "marcas_revendidas",
        "interesses",
    )


def csv_revendedoras(queryset) -> bytes:
    """Detalhe das revendedoras do escopo/período do dashboard, em CSV."""
    buffer = StringIO()
    escritor = csv.writer(buffer, delimiter=SEPARADOR, lineterminator="\r\n")
    escritor.writerow(COLUNAS)

    for r in _prepara(queryset):
        escritor.writerow(
            [
                r.nome_completo,
                _cpf(r.cpf),
                r.rg,
                r.email,
                _data(r.data_nascimento, "%d/%m/%Y"),
                " / ".join(t.numero for t in r.telefones.all()),
                r.cidade.nome,
                r.cidade.uf,
                r.bairro,
                r.endereco,
                r.cep,
                _promotora(r),
                _sim_nao(r.vende_outras_marcas),
                " / ".join(m.nome for m in r.marcas_revendidas.all()),
                _sim_nao(r.ja_revende),
                " / ".join(p.nome for p in r.interesses.all()),
                r.observacao,
                _data(r.criado_em, "%d/%m/%Y %H:%M"),
            ]
        )

    return (BOM + buffer.getvalue()).encode("utf-8")

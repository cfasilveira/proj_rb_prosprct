"""Responsividade mobile (docs/UI_UX_Brief.md — canvas 360–414px).

O PWA é usado em pé, no celular da promotora: nada aqui é lógica de negócio,
mas é o que faz a tela caber na mão (viewport, cards no lugar de tabela,
KPIs em 2 colunas, ação fixa no rodapé e alvos de toque ≥ 44px).
"""
from pathlib import Path

import pytest
from django.urls import reverse

from prospeccao.models import Cidade, ProdutoInteresse
from prospeccao.services import criar_revendedora

RAIZ = Path(__file__).resolve().parents[2]
CSS = (RAIZ / "backend" / "static" / "css" / "app.css").read_text(encoding="utf-8")

TEMPLATES_COM_TABELA = [
    "backend/templates/core/dashboard.html",
    "backend/templates/accounts/promotora_list.html",
    "backend/templates/prospeccao/revendedora_list.html",
    "backend/templates/prospeccao/importar.html",
]

pytestmark = pytest.mark.django_db


def test_pagina_declara_viewport_mobile_first(client):
    html = client.get(reverse("accounts:login")).content.decode()
    assert 'name="viewport" content="width=device-width, initial-scale=1"' in html
    assert "css/app.css" in html


def test_css_quebra_para_celular():
    assert "@media (max-width: 640px)" in CSS
    # tabela vira cards com rótulo da coluna no lugar do cabeçalho sumido
    assert ".tabela thead { display: none; }" in CSS
    assert "attr(data-label)" in CSS
    # ação principal colada no rodapé (Voltar/Próximo/Salvar)
    assert "position: sticky" in CSS and "bottom: 0" in CSS
    # alvos de toque do brief (§8)
    assert "min-height: 44px" in CSS


def test_kpis_duas_colunas_no_celular_e_no_maximo_no_desktop():
    """360px úteis = 328px: minmax(160px)+gap 16px só caberia 1 KPI por linha."""
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in CSS
    assert "@media (min-width: 641px)" in CSS
    assert "repeat(auto-fit, minmax(160px, 1fr))" in CSS


@pytest.mark.parametrize("template", TEMPLATES_COM_TABELA)
def test_tabelas_tem_rotulo_e_rolagem_horizontal(template):
    texto = (RAIZ / template).read_text(encoding="utf-8")
    assert 'class="tabela-scroll"' in texto, f"{template} sem wrapper de scroll"
    assert "data-label=" in texto, f"{template} sem rótulo de coluna para o card"


def test_dashboard_renderiza_os_rotulos_no_celular(client, django_user_model):
    """Sem rótulo, o card do celular vira uma pilha de números sem contexto."""
    gestor = django_user_model.objects.create_user(
        email="resp@t.com", password="x", username="resp"
    )
    gestor.perfil.role = "gestor"
    gestor.perfil.save()
    promotora = django_user_model.objects.create_user(
        email="promo@t.com", password="x", username="promo_resp"
    )
    cidade = Cidade.objects.create(nome="Curitiba", uf="PR")
    criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": "Ana", "cidade": cidade, "vende_outras_marcas": False},
        telefones=[{"numero": "41999998888"}],
        interesses=[ProdutoInteresse.objects.first().pk],
    )

    client.force_login(gestor)
    html = client.get(reverse("core:dashboard")).content.decode()

    assert 'class="tabela-scroll"' in html
    assert 'data-label="Cadastradas"' in html
    assert 'data-label="Cidade"' in html
    assert 'data-label="Cadastro"' in html

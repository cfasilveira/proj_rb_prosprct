"""Testes de E4: dashboard (agregações) e gestão de promotoras (PRD RF-02/RF-05)."""
import pytest
from django.urls import reverse

from prospeccao.models import Cidade, ProdutoInteresse, Revendedora
from prospeccao.services import criar_revendedora

pytestmark = pytest.mark.django_db


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@test.com", password="x", username="promo"
    )


@pytest.fixture
def promotora2(django_user_model):
    return django_user_model.objects.create_user(
        email="promo2@test.com", password="x", username="promo2"
    )


@pytest.fixture
def gestor(django_user_model):
    user = django_user_model.objects.create_user(
        email="gestor@test.com", password="x", username="gestor"
    )
    user.perfil.role = "gestor"
    user.perfil.save()
    return user


@pytest.fixture
def cidade():
    return Cidade.objects.create(nome="Curitiba", uf="PR")


def _cria(promotora, cidade, nome, com_marca=False):
    interesse = ProdutoInteresse.objects.first()
    marcas = ["Marca X"] if com_marca else None
    return criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": nome, "cidade": cidade, "vende_outras_marcas": com_marca},
        telefones=[{"numero": "41999998888"}],
        marcas=marcas,
        interesses=[interesse.pk],
    )


def test_dashboard_requer_login(client):
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 302


def test_dashboard_promotora_agrega_somente_as_suas(client, promotora, promotora2, cidade):
    _cria(promotora, cidade, "Ana", com_marca=True)
    _cria(promotora, cidade, "Bia", com_marca=False)
    _cria(promotora2, cidade, "Cris", com_marca=True)

    client.force_login(promotora)
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 200
    assert response.context["total"] == 2
    assert response.context["ja_revendem"] == 1
    assert response.context["pct"] == 50
    assert response.context["perfil"].is_gestor is False


def test_dashboard_gestor_consolidado_e_por_promotora(client, promotora, promotora2, gestor, cidade):
    _cria(promotora, cidade, "Ana", com_marca=True)
    _cria(promotora, cidade, "Bia", com_marca=False)
    _cria(promotora2, cidade, "Cris", com_marca=True)

    client.force_login(gestor)
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 200
    assert response.context["total"] == 3
    assert response.context["ja_revendem"] == 2

    por_promotora = response.context["por_promotora"]
    assert len(por_promotora) == 2
    totais = {linha["total"] for linha in por_promotora}
    assert totais == {2, 1}


def test_dashboard_filtro_periodo(client, promotora, cidade):
    from datetime import timedelta

    from django.utils import timezone

    antiga = _cria(promotora, cidade, "Antiga")
    Revendedora.objects.filter(pk=antiga.pk).update(
        criado_em=timezone.now() - timedelta(days=40)
    )
    _cria(promotora, cidade, "Recente")

    client.force_login(promotora)
    resposta_total = client.get(reverse("core:dashboard"))
    assert resposta_total.context["total"] == 2

    resposta_mes = client.get(reverse("core:dashboard"), {"periodo": "mes"})
    assert resposta_mes.context["total"] == 1
    assert resposta_mes.context["ultimos"][0].nome_completo == "Recente"


def test_gestor_crud_promotoras(client, gestor, promotora, django_user_model):
    client.force_login(gestor)

    lista = client.get(reverse("accounts:promotora_list"))
    assert lista.status_code == 200
    assert promotora.email.encode() in lista.content

    cria = client.post(reverse("accounts:promotora_nova"), {
        "nome_completo": "Nova Promo",
        "email": "nova@rb.com",
        "territorio": "Londrina/PR",
        "senha": "senha123",
    })
    assert cria.status_code == 302
    nova = django_user_model.objects.get(email="nova@rb.com")
    assert nova.perfil.role == "promotora"
    assert nova.check_password("senha123")

    edita = client.post(
        reverse("accounts:promotora_editar", args=[nova.perfil.pk]),
        {"nome_completo": "Nova Promo Editada", "email": "nova@rb.com",
         "territorio": "Maringá/PR", "senha": ""},
    )
    assert edita.status_code == 302
    nova.perfil.refresh_from_db()
    assert nova.perfil.nome_completo == "Nova Promo Editada"

    desativa = client.post(reverse("accounts:promotora_alternar", args=[nova.perfil.pk]))
    assert desativa.status_code == 302
    nova.perfil.refresh_from_db()
    assert nova.perfil.ativo is False

    # cadastros preservados na desativação
    assert Revendedora.objects.filter(promotora=nova).count() == 0


def test_promotora_nao_acessa_gestao(client, promotora):
    client.force_login(promotora)
    response = client.get(reverse("accounts:promotora_list"))
    assert response.status_code == 403


def test_gestor_nao_desativa_a_si_mesmo(client, gestor):
    client.force_login(gestor)
    client.post(reverse("accounts:promotora_alternar", args=[gestor.perfil.pk]))
    gestor.perfil.refresh_from_db()
    assert gestor.perfil.ativo is True


def test_login_de_inativo_bloqueado(client, promotora):
    client.post(reverse("accounts:login"), {
        "username": promotora.email, "password": "x",
    })
    assert "_auth_user_id" in client.session  # ativo loga normalmente
    client.logout()

    promotora.perfil.ativo = False
    promotora.perfil.save()
    resposta = client.post(reverse("accounts:login"), {
        "username": promotora.email, "password": "x",
    })
    assert "_auth_user_id" not in client.session
    assert resposta.status_code == 200

"""Testes de E2: flag derivada ja_revende (PRD RF-04)."""
import pytest

from prospeccao.models import Cidade, Marca, Revendedora
from prospeccao.services import criar_revendedora

pytestmark = pytest.mark.django_db


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@test.com", password="x", username="promo"
    )


@pytest.fixture
def cidade():
    return Cidade.objects.create(nome="Curitiba", uf="PR")


@pytest.fixture
def marca():
    return Marca.objects.create(nome="Marca X")


def test_sem_marcas_ja_revende_false(promotora, cidade):
    revendedora = Revendedora.objects.create(
        promotora=promotora, nome_completo="Ana Silva", cidade=cidade
    )
    assert revendedora.ja_revende is False


def test_adicionar_marca_via_manager_ativa_flag(promotora, cidade, marca):
    revendedora = Revendedora.objects.create(
        promotora=promotora, nome_completo="Ana Silva", cidade=cidade
    )
    revendedora.marcas_revendidas.add(marca)
    revendedora.refresh_from_db()
    assert revendedora.ja_revende is True


def test_remover_marca_desativa_flag(promotora, cidade, marca):
    revendedora = Revendedora.objects.create(
        promotora=promotora, nome_completo="Ana Silva", cidade=cidade
    )
    revendedora.marcas_revendidas.add(marca)
    revendedora.marcas_revendidas.remove(marca)
    revendedora.refresh_from_db()
    assert revendedora.ja_revende is False


def test_via_through_direto_tambem_atualiza(promotora, cidade, marca):
    from prospeccao.models import RevendedoraMarca

    revendedora = Revendedora.objects.create(
        promotora=promotora, nome_completo="Ana Silva", cidade=cidade
    )
    RevendedoraMarca.objects.create(revendedora=revendedora, marca=marca)
    revendedora.refresh_from_db()
    assert revendedora.ja_revende is True

    RevendedoraMarca.objects.filter(revendedora=revendedora).delete()
    revendedora.refresh_from_db()
    assert revendedora.ja_revende is False


def test_service_com_marcas_resulta_em_ja_revende_true(promotora, cidade):
    from prospeccao.models import ProdutoInteresse

    interesse = ProdutoInteresse.objects.first()
    revendedora = criar_revendedora(
        promotora=promotora,
        dados={
            "nome_completo": "Maria Souza",
            "cidade": cidade,
            "vende_outras_marcas": True,
        },
        telefones=[{"numero": "41999998888", "tipo": "whatsapp", "principal": True}],
        marcas=["Marca Livre"],
        interesses=[interesse.pk],
    )
    assert revendedora.ja_revende is True
    assert revendedora.marcas_revendidas.count() == 1

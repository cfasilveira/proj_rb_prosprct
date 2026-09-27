"""Testes de E2: CPF, regras do service e escopo por promotora (PRD RF-02/RF-03)."""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from prospeccao.models import Cidade, ProdutoInteresse, Revendedora
from prospeccao.services import criar_revendedora

pytestmark = pytest.mark.django_db


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@test.com", password="x", username="promo"
    )


@pytest.fixture
def outra_promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo2@test.com", password="x", username="promo2"
    )


@pytest.fixture
def cidade():
    return Cidade.objects.create(nome="Curitiba", uf="PR")


@pytest.fixture
def interesse():
    return ProdutoInteresse.objects.first()


def _dados(cidade, **extra):
    dados = {"nome_completo": "Ana Silva", "cidade": cidade}
    dados.update(extra)
    return dados


def test_cpf_duplicado_e_bloqueado(promotora, cidade):
    Revendedora.objects.create(promotora=promotora, **_dados(cidade, cpf="12345678901"))
    with pytest.raises(IntegrityError):
        Revendedora.objects.create(promotora=promotora, **_dados(cidade, cpf="12345678901"))


def test_cpf_invalido_falha_no_full_clean(promotora, cidade):
    revendedora = Revendedora(promotora=promotora, **_dados(cidade, cpf="123"))
    with pytest.raises(ValidationError):
        revendedora.full_clean()


def test_service_exige_telefone(promotora, cidade, interesse):
    with pytest.raises(ValidationError) as erro:
        criar_revendedora(
            promotora=promotora,
            dados=_dados(cidade),
            telefones=[],
            interesses=[interesse.pk],
        )
    assert "telefones" in erro.value.error_dict


def test_service_exige_interesse(promotora, cidade):
    with pytest.raises(ValidationError) as erro:
        criar_revendedora(
            promotora=promotora,
            dados=_dados(cidade),
            telefones=[{"numero": "41999998888"}],
            interesses=[],
        )
    assert "interesses" in erro.value.error_dict


def test_service_exige_marca_quando_vende_outras(promotora, cidade, interesse):
    with pytest.raises(ValidationError) as erro:
        criar_revendedora(
            promotora=promotora,
            dados=_dados(cidade, vende_outras_marcas=True),
            telefones=[{"numero": "41999998888"}],
            marcas=[],
            interesses=[interesse.pk],
        )
    assert "marcas" in erro.value.error_dict


def test_service_sem_vende_outras_nao_exige_marca(promotora, cidade, interesse):
    revendedora = criar_revendedora(
        promotora=promotora,
        dados=_dados(cidade, vende_outras_marcas=False),
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    assert revendedora.ja_revende is False
    assert revendedora.telefones.count() == 1


def test_escopo_por_promotora(promotora, outra_promotora, cidade, interesse):
    criar_revendedora(
        promotora=promotora,
        dados=_dados(cidade),
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    criar_revendedora(
        promotora=outra_promotora,
        dados=_dados(cidade, nome_completo="Outra Pessoa"),
        telefones=[{"numero": "41999997777"}],
        interesses=[interesse.pk],
    )
    assert Revendedora.para_promotora(promotora).count() == 1
    assert Revendedora.para_promotora(outra_promotora).count() == 1


def test_exclusao_logica_some_do_escopo(promotora, cidade, interesse):
    revendedora = criar_revendedora(
        promotora=promotora,
        dados=_dados(cidade),
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    revendedora.desativar()
    assert Revendedora.para_promotora(promotora).count() == 0
    assert Revendedora.ativas().count() == 0


def test_telefone_curto_rejeitado_pelo_service(promotora, cidade, interesse):
    with pytest.raises(ValidationError):
        criar_revendedora(
            promotora=promotora,
            dados=_dados(cidade),
            telefones=[{"numero": "99998888"}],
            interesses=[interesse.pk],
        )


def test_perfil_criado_automaticamente(django_user_model):
    user = django_user_model.objects.create_user(
        email="nova@test.com", password="x", username="nova"
    )
    assert user.perfil.role == "promotora"

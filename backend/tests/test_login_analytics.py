"""Testes do login do Streamlit contra o `auth_user` (PRD RF-06.3).

A tela de login do analytics chama `db.autentica_gestor`, que passa pelo
`AxesBackend` (F3.5) — sem um `request` ele lança
`AxesBackendRequestParameterRequired` e a página quebrava em vez de mostrar
"credenciais inválidas".
"""
import pytest
from axes.models import AccessAttempt

pytestmark = pytest.mark.django_db


@pytest.fixture
def gestor(django_user_model):
    user = django_user_model.objects.create_user(
        email="gestor@analytics.com", password="Segredo123", username="gestor_analytics"
    )
    user.perfil.role = "gestor"
    user.perfil.save()
    return user


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@analytics.com", password="Segredo123", username="promo_analytics"
    )


def _login(email, senha):
    import db

    return db.autentica_gestor(email, senha)


def test_senha_correta_de_gestor_entra(gestor):
    assert _login("gestor@analytics.com", "Segredo123") is True


def test_senha_errada_devolve_false_sem_estourar(gestor):
    assert _login("gestor@analytics.com", "outra-senha") is False


def test_email_inexistente_devolve_false():
    assert _login("ninguem@analytics.com", "Segredo123") is False


def test_promotora_nao_passa(promotora):
    assert _login("promo@analytics.com", "Segredo123") is False


def test_gestor_desativado_nao_passa(gestor):
    gestor.perfil.ativo = False
    gestor.perfil.save()
    assert _login("gestor@analytics.com", "Segredo123") is False


def test_login_valido_zera_o_contador(gestor):
    """`AXES_RESET_ON_SUCCESS` vale no analytics: o sinal `user_logged_in` não
    dispara no Streamlit, então o reset tem que ser feito em `autentica_gestor`."""
    for _ in range(4):
        assert _login("gestor@analytics.com", "errada") is False
    assert AccessAttempt.objects.count() == 1

    assert _login("gestor@analytics.com", "Segredo123") is True
    assert AccessAttempt.objects.count() == 0

    # contador zerado: mais 4 erros seguem sem bloquear (sem o reset já
    # travariam no primeiro, porque as 4 falhas antigas continuariam lá)
    for _ in range(4):
        assert _login("gestor@analytics.com", "errada") is False
    assert _login("gestor@analytics.com", "Segredo123") is True


def test_cinco_tentativas_erradas_sao_bloqueadas(gestor):
    """O lockout do django-axes vale também na tela do analytics."""
    for _ in range(5):
        assert _login("gestor@analytics.com", "errada") is False
    assert _login("gestor@analytics.com", "Segredo123") is False

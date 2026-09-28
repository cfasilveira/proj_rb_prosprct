"""Bloqueio de força bruta no login (django-axes, RNF de segurança)."""
import pytest
from axes.models import AccessAttempt
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def alvo(django_user_model):
    return django_user_model.objects.create_user(
        email="alvo@t.com", username="alvo@t.com", password="SenhaForte123"
    )


def _login(client, senha, usuario="alvo@t.com"):
    return client.post(
        reverse("accounts:login"), {"username": usuario, "password": senha}
    )


def test_bloqueia_apos_cinco_tentativas(client, alvo):
    for _ in range(5):
        _login(client, "senha-errada")

    # nem com a senha certa a conta/IP volta a responder normalmente
    resposta = _login(client, "SenhaForte123")

    assert resposta.status_code == 429
    assert "bloqueado" in resposta.content.decode().lower()
    assert AccessAttempt.objects.exists()


def test_login_valido_zera_o_contador(client, alvo):
    for _ in range(4):
        _login(client, "senha-errada")

    resposta = _login(client, "SenhaForte123")

    assert resposta.status_code == 302
    assert AccessAttempt.objects.count() == 0

    # contador zerado: 4 erros novos seguem sem bloquear (senão já seriam 429)
    for _ in range(4):
        assert _login(client, "senha-errada").status_code == 200
    # e o 5º erro volta a bloquear, contado do zero
    assert _login(client, "senha-errada").status_code == 429

import pytest


def test_login_page_ok(client):
    response = client.get("/contas/entrar/")
    assert response.status_code == 200
    assert b"RB Prospecta" in response.content


def test_dashboard_requer_login(client):
    response = client.get("/", follow=False)
    assert response.status_code == 302
    assert "/contas/entrar/" in response["Location"]


@pytest.mark.django_db
def test_health(client):
    response = client.get("/saude/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_health_responde_503_quando_o_banco_nao_responde(client, monkeypatch):
    from django.db import connection
    from django.db.utils import OperationalError

    def _sem_conexao(*args, **kwargs):
        raise OperationalError("sem conexão")

    monkeypatch.setattr(connection, "cursor", _sem_conexao)
    response = client.get("/saude/")

    assert response.status_code == 503
    assert response.json() == {"status": "erro", "banco": "indisponivel"}

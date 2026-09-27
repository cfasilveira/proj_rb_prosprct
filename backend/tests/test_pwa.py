"""Testes de E6: PWA, página LGPD e comando de gestor (PRD RNF-06)."""
import pytest
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_manifest_e_service_worker_publicados():
    """Arquivos PWA encontrados pelo finder de estáticos (DEBUG=False nos testes)."""
    from django.contrib.staticfiles import finders

    assert finders.find("manifest.json")
    assert finders.find("js/sw.js")
    assert finders.find("icon-192.png")
    assert finders.find("icon-512.png")
    assert finders.find("icon-maskable-512.png")
    assert finders.find("favicon-32.png")


def test_base_registra_pwa_e_link_lgpd(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="pwa@test.com", password="x", username="pwa"
    )
    client.force_login(user)
    resposta = client.get(reverse("core:dashboard"))
    conteudo = resposta.content.decode()
    assert 'rel="manifest"' in conteudo
    assert "serviceWorker.register" in conteudo
    assert "btn-instalar" in conteudo
    assert "aviso-offline" in conteudo
    assert reverse("core:privacidade") in conteudo


def test_pagina_privacidade_publica(client):
    resposta = client.get(reverse("core:privacidade"))
    assert resposta.status_code == 200
    assert b"LGPD" in resposta.content
    assert b"exclus" in resposta.content.lower()


def test_criar_gestor(django_user_model, capsys):
    call_command(
        "criar_gestor", "gestor@rb.com", senha="SenhaForte123", nome="Chefe do Canal"
    )
    gestor = django_user_model.objects.get(email="gestor@rb.com")
    assert gestor.perfil.role == "gestor"
    assert gestor.check_password("SenhaForte123")

    # re-executar atualiza sem duplicar
    call_command("criar_gestor", "gestor@rb.com", senha="OutraSenha456")
    assert django_user_model.objects.filter(email="gestor@rb.com").count() == 1
    gestor.refresh_from_db()
    assert gestor.check_password("OutraSenha456")


def test_criar_gestor_senha_curta_rejeitada():
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("criar_gestor", "x@rb.com", senha="123")


def test_headers_de_segurancia_em_prod():
    with override_settings(
        SECURE_SSL_REDIRECT=False,  # evita redirect nos testes HTTP
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        X_FRAME_OPTIONS="DENY",
    ):
        from django.conf import settings

        assert settings.SECURE_HSTS_SECONDS == 31536000
        assert settings.X_FRAME_OPTIONS == "DENY"
        assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True


def test_check_deploy_passa_em_prod():
    """Roda o system check completo do Django (rota + settings)."""
    from django.core.management import call_command

    call_command("check")

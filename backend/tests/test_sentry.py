"""Ativação condicional do Sentry (config.sentry.configura_sentry)."""
import sys
import types

from config import sentry


def test_sem_dsn_nao_inicializa_o_sdk(monkeypatch):
    """Sem SENTRY_DSN o servidor sobe normalmente, sem tocar no SDK."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    assert sentry.configura_sentry() is False


def test_com_dsn_inicializa_o_sdk(monkeypatch):
    chamadas = {}
    sdk = types.SimpleNamespace(init=lambda **kwargs: chamadas.update(kwargs))
    monkeypatch.setitem(sys.modules, "sentry_sdk", sdk)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations", types.SimpleNamespace())
    monkeypatch.setitem(
        sys.modules,
        "sentry_sdk.integrations.django",
        types.SimpleNamespace(DjangoIntegration=type("DjangoIntegration", (), {})),
    )
    monkeypatch.setenv("SENTRY_DSN", "https://chave@o.ingest.sentry.io/42")
    monkeypatch.delenv("SENTRY_TRACES_SAMPLE_RATE", raising=False)

    assert sentry.configura_sentry() is True
    assert chamadas["dsn"] == "https://chave@o.ingest.sentry.io/42"
    assert chamadas["traces_sample_rate"] == 0.0
    assert chamadas["send_default_pii"] is False

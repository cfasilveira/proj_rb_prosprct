"""Integração opcional com Sentry (erros em produção).

Ativa o SDK apenas quando `SENTRY_DSN` está no ambiente — sem a variável o
servidor sobe normalmente, sem serviço externo e sem dependência de rede.
"""
import os


def configura_sentry() -> bool:
    """Inicializa o Sentry; `False` quando não há DSN configurado."""
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0")),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        send_default_pii=False,
    )
    return True

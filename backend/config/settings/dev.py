"""Configurações de desenvolvimento local."""
import os

from .base import *  # noqa: F403

DEBUG = True

# Hosts extras em dev, lidos de ALLOWED_HOSTS no .env (separados por vírgula).
# Ex.: liberar o IP da LAN para testar no celular:
#   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.249
_hosts_dev = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
ALLOWED_HOSTS = list(dict.fromkeys(["localhost", "127.0.0.1", *_hosts_dev]))

_origins_dev = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
CSRF_TRUSTED_ORIGINS = _origins_dev

# Dev não usa manifest de estáticos (evita quebrar quando não coletado)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

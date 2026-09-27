"""Middleware que expõe a usuária logada para os signals de auditoria."""
import threading

_local = threading.local()


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            _local.user = None


def usuario_atual():
    return getattr(_local, "user", None)

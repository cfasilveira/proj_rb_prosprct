"""Conexão Postgres e helpers de consulta do app Streamlit."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgres://rb_prospecta:rb_prospecta@localhost:5432/rb_prospecta_dev",
)


def conexao():
    import psycopg

    return psycopg.connect(DATABASE_URL)


def executar(sql: str, params: dict) -> list[dict]:
    """Executa uma query e retorna linhas como dicts (Decimal vira float)."""
    from decimal import Decimal

    with conexao() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        colunas = [c.name for c in cur.description]
        linhas = []
        for valores in cur.fetchall():
            linhas.append(
                dict(
                    zip(
                        colunas,
                        (float(v) if isinstance(v, Decimal) else v for v in valores),
                        strict=True,
                    )
                )
            )
        return linhas


def opcoes_promotoras() -> list[dict]:
    return executar(
        "SELECT p.user_id AS id, p.nome_completo AS nome "
        "FROM core_perfil p WHERE p.role = 'promotora' AND p.ativo "
        "ORDER BY p.nome_completo;",
        {},
    )


def opcoes_cidades() -> list[dict]:
    return executar(
        "SELECT id, nome || '/' || uf AS nome FROM prospeccao_cidade ORDER BY nome, uf;",
        {},
    )


def configura_django_auth():
    """Prepara o Django para validar senhas no Streamlit (reuso do auth_user)."""
    backend = RAIZ / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


def autentica_gestor(email: str, senha: str) -> bool:
    """Valida credenciais e exige perfil de gestor ativo."""
    configura_django_auth()
    from django.contrib.auth import authenticate

    user = authenticate(username=email, password=senha)
    if not user:
        return False
    perfil = getattr(user, "perfil", None)
    return bool(perfil and perfil.is_gestor and perfil.ativo)

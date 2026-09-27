# RB Prospecta

Ferramenta de prospecção e cadastro de revendedoras para o canal de venda direta.

**Stack:** Django 5 · PostgreSQL 16 · Streamlit · PWA

## Documentação

| Documento | Descrição |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Requisitos, personas, escopo e critérios de aceite |
| [docs/TRD.md](docs/TRD.md) | Decisões técnicas, stack e arquitetura |
| [docs/App_Flow.md](docs/App_Flow.md) | Fluxos de navegação |
| [docs/UI_UX_Brief.md](docs/UI_UX_Brief.md) | Visual, cores, tipografia e componentes |
| [docs/Backend_Schema.md](docs/Backend_Schema.md) | Tabelas, regras e queries das análises |
| [docs/Plano_Implementacao.md](docs/Plano_Implementacao.md) | Etapas E1–E6 com checkpoints |

## Requisitos

- Python 3.12+
- Docker (Postgres 16)

## Como rodar

```bash
# 1. Banco
docker compose up -d db

# 2. Ambiente virtual
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# 3. Env
cp .env.example .env

# 4. Migrations (após existirem)
.venv/bin/python backend/manage.py migrate

# 5. Servidor
.venv/bin/python backend/manage.py runserver

# 6. Análises (Streamlit) - porta 8501, acesso restrito ao gestor
.venv/bin/streamlit run analytics/Home.py
```

## Verificação

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

## Estrutura

```
backend/     # Django (auth, cadastro, dashboard)
analytics/   # Streamlit (análises A1–A4)
docs/        # documentação do produto
```

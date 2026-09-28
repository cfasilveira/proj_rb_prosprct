# RB Prospecta

Ferramenta de prospecção e cadastro de revendedoras para o canal de venda direta.
Promotoras coletam os dados em campo (PWA no celular) e o gestor acompanha a carteira
por dashboard e análises.

**Stack:** Django 5 · PostgreSQL 16 · Streamlit (análises) · PWA

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

# 4. Migrations
.venv/bin/python backend/manage.py migrate

# 5. Gestor inicial
.venv/bin/python backend/manage.py criar_gestor gestor@suaempresa.com \
    --senha SuaSenhaForte123 --nome "Nome do Gestor"

# 6. Servidor web (PWA) - http://localhost:8000
.venv/bin/python backend/manage.py runserver

# 7. Análises (Streamlit) - http://localhost:8501 (só gestor)
.venv/bin/streamlit run analytics/Home.py
```

## Verificação

```bash
.venv/bin/ruff check .
.venv/bin/pytest          # 55 testes
```

## Estrutura

```
backend/     # Django: auth, wizard de cadastro, dashboard, PWA
  config/    # settings base/dev/prod
  core/      # Perfil, auditoria, dashboard, LGPD
  accounts/  # User, login, gestão de promotoras
  prospeccao/# Revendedora + N:N (marcas, produtos, redes)
analytics/   # Streamlit: análises A1–A4
docs/        # documentação do produto
```

## Deploy (Railway)

1. Conecte o repositório ao Railway (web service + Postgres gerenciado).
2. Variáveis de ambiente:
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`
   - `DATABASE_URL` (fornecido pelo Postgres do Railway)
   - `SECRET_KEY` (gerar: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
   - `ALLOWED_HOSTS=seu-app.up.railway.app`
   - `CSRF_TRUSTED_ORIGINS=https://seu-app.up.railway.app`
   - `SENTRY_DSN` (opcional — sem ela o Sentry fica desligado e o servidor
     sobe normalmente)
3. Build: `pip install -r requirements.txt && python backend/manage.py collectstatic --noinput`
4. Start: `python backend/manage.py migrate && gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:$PORT`
   (`migrate` no start, não no build: o build não alcança o Postgres e roda
   antes da primeira provisão do banco)
5. Segundo serviço (analytics): `streamlit run analytics/Home.py` com
   `requirements-analytics` do `analytics/requirements.txt`.
6. Após o deploy: `python backend/manage.py criar_gestor ...`

## LGPD — exclusão de dados pessoais (RNF-06)

A página `/privacidade/` promete exclusão sob demanda. Dois caminhos, ambos
auditados:

```bash
# comando (identifica por CPF ou e-mail; --usuario grava quem fez)
.venv/bin/python backend/manage.py excluir_dados --cpf 12345678901 \
    --usuario gestor@suaempresa.com
```

- admin → `Revendedora` → ação **“Excluir dados pessoais (LGPD RNF-06)”**.

Em ambos a revendedora é anonimizada no lugar (nome, CPF, RG, e-mail,
nascimento, endereço e observação apagados; telefones e redes removidos), a
linha permanece como registro sem identificação e a auditoria guarda apenas
quem fez, quando e qual ação.

## Checklist de aceite do MVP (PRD §7)

- [ ] AC-01 — cadastro completo em ≤ 2 min no celular
- [ ] AC-02 — CPF duplicado bloqueado com mensagem clara
- [ ] AC-03 — `ja_revende` coerente em 100% dos testes (automático: `pytest`)
- [ ] AC-04 — análises A1–A4 coerentes (automático: `pytest`)
- [ ] AC-05 — escopo por perfil (automático: `pytest`)
- [ ] AC-06 — PWA instalável (verificar no Chrome/Android após deploy)
- [ ] Lighthouse: PWA ≥ 90, A11y ≥ 90, Perf ≥ 80 (rodar em produção)

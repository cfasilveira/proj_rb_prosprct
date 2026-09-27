# TRD — RB Prospecta

**Versão:** 1.0 · **Data:** 27/09/2026 · **Status:** Aprovado
**Depende de:** PRD v1.0

## 1. Visão técnica

Dois aplicações compartilhando o mesmo **Postgres 16**:

```
┌─────────────────────┐         ┌──────────────────────┐
│  Django 5 (web)     │         │  Streamlit (análises)│
│  auth + cadastro    │         │  dashboards A1–A4    │
│  dashboard básico   │         │  público: gestor     │
└──────────┬──────────┘         └──────────┬───────────┘
           │                               │
           └───────────┬───────────────────┘
                       ▼
              ┌─────────────────┐
              │ PostgreSQL 16   │
              └─────────────────┘
```

- **Django**: PWA, login, formulário de campo, dashboard, gestão de promotoras.
- **Streamlit**: app separado só para as 4 análises do gestor (RF-06), lendo Postgres direto.
- **Por que separado:** Streamlit não substitui Django em formulário multiusuário/PWA/auth
  com perfis; Django não tem o mesmo ganho de velocidade em gráficos. Cada um no seu forte.

## 2. Stack

| Camada | Tecnologia | Versão | Justificativa |
|---|---|---|---|
| Backend web | Django | 5.x LTS | Admin embutido, ORM maduro, auth por perfil nativo |
| Templates | Django Templates + HTMX | — | Sem build de JS, SSR rápido, bom para PWA |
| Análises | Streamlit + Plotly | 1.x / 5.x | Dashboards em código, sem front separado |
| Banco | PostgreSQL | 16 | Escrita concorrente de promotoras, integridade forte |
| Conexão | psycopg (binaire) | 3.x | Driver oficial do Postgres |
| Pool de conexões | pgbouncer (host) ou `CONN_MAX_AGE` | — | Django com `CONN_MAX_AGE=60` no MVP |
| Estáticos | WhiteNoise | — | Serve CSS/JS coletados sem Nginx |
| Imagens | Pillow | — | Reservas futuras (foto da loja) |
| Validação BR | django-localflavor | 4.x | Validação de CPF/CEP |
| Testes | pytest + pytest-django | 8.x / 5.x | Fixtures legíveis |
| Lint/format | Ruff | — | Um tool só, rápido |
| Deploy | Railway (web + db) | — | PWA + Postgres gerenciado, disco persistente, backup nativo |
| PWA | manifest.json + Service Worker | — | Instalável, cache de shell |
| CI | GitHub Actions | — | ruff + pytest no push |

### 2.1 Decisões técnicas registradas

| # | Decisão | Opção escolhida | Alternativa descartada | Motivo |
|---|---|---|---|---|
| D1 | Framework | Django + HTMX | Next.js, Laravel, Streamlit | CRUD/auth/PWA prontos; Streamlit fraco em form de campo multiusuário |
| D2 | Banco | **Postgres 16** (dev e prod) | SQLite | Escrita concorrente; deploy efêmero destruiria arquivo SQLite; já decidido em reunião |
| D3 | Análises | Streamlit no mesmo Postgres | Relatórios dentro do Django | Vite para gráficos interativos, código pequeno, isola o dashboard do app de campo |
| D4 | Auth | Django auth nativo + Groups | allauth, JWT | Necessário só email/senha; Groups = perfis `promotora`/`gestor` |
| D5 | API | Não há API pública (HTML + HTMX) | DRF | Nenhum cliente externo no MVP |
| D6 | Multi-valor | Tabelas N:N | JSONB/CSV em coluna | Consulta nas análises exige `JOIN` + `GROUP BY` limpos |
| D7 | `ja_revende` | Flag materializada recalculada no save | Bool digitado + Coluna gerada | PRD exige derivar das marcas (RF-04); precisa ser filtrável em SQL |
| D8 | Deploy | Railway | VPS própria | Menos operação; escala horizontal futura |
| D9 | Sessão | Cookies Django, 24h | Token em localStorage | Menor superfície de ataque em PWA |
| D10 | Idioma | `LANGUAGE_CODE = 'pt-br'`, TZ `America/Sao_Paulo` | en-US | Usuárias brasileiras |

## 3. Arquitetura de pastas

```
proj_rb_prospect/
├── docs/                      # esta documentação
├── backend/
│   ├── manage.py
│   ├── config/                # settings, urls, wsgi/asgi
│   │   └── settings/
│   │       ├── base.py
│   │       ├── dev.py
│   │       └── prod.py
│   ├── core/                  # apps compartilhados (perfil, utilidades)
│   ├── accounts/              # User, Perfil, login, gestão de promotoras
│   ├── prospeccao/            # Revendedora, marcas, produtos, redes sociais
│   ├── templates/
│   ├── static/                # css, js, manifest.json, ícones
│   └── tests/
├── analytics/                 # app Streamlit
│   ├── Home.py
│   ├── pages/                 # A1..A4
│   ├── db.py                  # conexão e queries
│   └── requirements.txt
├── docker-compose.yml         # postgres local
├── .env.example
└── pyproject.toml             # ruff, pytest
```

## 4. Ambientes e configuração

| Variável | Dev | Prod |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | `config.settings.prod` |
| `DATABASE_URL` | `postgres://localhost:5432/rb_prospecta_dev` | Railway (gerada) |
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | domínio do Railway |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000` | `https://*.up.railway.app` |
| `SECURE_SSL_REDIRECT` | não | sim |
| `STRIPE`/e-mails | — | console backend (futuro SMTP) |

- **Dev:** `docker-compose up db` → Postgres 16 em container.
- **Nunca** SQLite, mesmo em dev (mesmo dia de Postgres = zero surpresa na migração).
- `.env` versionado via `.env.example`; secrets fora do repositório.

## 5. Autenticação e autorização

- `django.contrib.auth` com `User.email` único (`USERNAME_FIELD = 'email'`).
- `Group`: `promotora`, `gestor`.
- `Perfil` 1:1 com `User`: `role`, `nome_completo`, `territorio`, `ativo`.
- Regras:
  - `gestor`: acesso a tudo, cria/desativa promotoras, acesso ao Streamlit.
  - `promotora`: CRUD de revendedora **filtrado por `revendedora.promotora == request.user`**
    (queryset sempre filtrado no view; nunca só escondendo link).
- Proteção de views: mixin `LoginRequiredMixin` + mixin de papel (`RoleRequiredMixin`).
- Streamlit: tela de login própria validando `Group == gestor` (senha do mesmo `auth_user`).

## 6. PWA

| Item | Especificação |
|---|---|
| `manifest.json` | nome, ícones 192/512, `display: standalone`, tema `#123456` (ver UI brief) |
| Service Worker | Network-first para HTML/Dados; Cache-first para CSS/JS/ícones |
| Offline | Shell carrega; formulário mostra aviso "sem conexão" e bloqueia envio |
| HTTPS | Obrigatório (Railway já entrega) |

## 7. Segurança

- HTTPS com redirect; `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` em prod.
- `SecurityMiddleware` + HSTS em prod.
- Validação server-side sempre (client-side é só UX).
- CPF armazenado com criptografia em repouso? **MVP: não** — mitigar com acesso restrito + log;
  revisar em fase 2 (principal risco LGPD).
- Log de auditoria: `AuditLog(model, obj_id, acao, user, ts)` gravado em signals.
- Upload de arquivo: não havia no MVP; na fase 2 entrou a importação de planilha Excel
  de revendedoras (`.xlsx`, prévia com erros linha a linha antes de gravar, teto de
  1000 linhas por envio).
- Rate limit de login: `django-axes` (fase 2) — MVP: backoff manual simples.

## 8. Observabilidade e backup

- Logs: stdout JSON no Railway (12-factor), nível `INFO` prod / `DEBUG` dev.
- Métricas básicas: `/healthz` (ping + query simples no DB).
- Backup: PITR/backup diário gerenciado pelo Railway, retenção 7 dias (RNF-04).

## 9. Estratégia de testes

| Nível | Ferramenta | Cobertura alvo |
|---|---|---|
| Unit (models, services) | pytest | regras de `ja_revende`, validação CPF, escopo de queryset |
| View (client Django) | pytest-django | login, permissões, create/edit de revendedora |
| Query das análises | pytest | A1–A4 com fixture de ~50 revendedoras |
| Front | manual + Playwright (fase 2) | fluxo crítico do formulário |

Comando de verificação: `ruff check . && pytest`.

## 10. Fora do escopo técnico (MVP)

- Kubernetes, Redis/Celery, Elasticsearch, GraphQL, microserviços, Docker em prod
  (dev usa só o container do Postgres), testes E2E automatizados.

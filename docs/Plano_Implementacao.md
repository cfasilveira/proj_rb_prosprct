# Plano de Implementação — RB Prospecta

**Versão:** 1.0 · **Data:** 27/09/2026
**Depende de:** PRD, TRD, App Flow, UI/UX Brief, Backend Schema
**Stack:** Django 5 + Postgres 16 + Streamlit · **Estimativa:** 6 etapas, ~2 semanas

> **Status (27/09/2026): E1–E6 + Fase 2 CONCLUÍDAS.** 113 testes (`pytest`), `ruff` limpo.
> Pendências operacionais de produção: deploy Railway, auditoria Lighthouse em produção
> e validação AC-06 (instalação PWA) em dispositivo real — ver README.
> Fase 2: importação de planilha Excel de revendedoras (PWA) e exportação em PDF
> (dashboard Django + análises A1–A4). Ficou de fora: exportação CSV (PRD §4.2).

## Visão geral

| Etapa | Entrega | Depende de | Estimativa | Status |
|---|---|---|---|---|
| E1 | Setup do repositório e ambiente | — | 0,5 dia | ✅ concluída |
| E2 | Models, migrations e auth | E1 | 1,5 dia | ✅ concluída |
| E3 | Formulário de campo (PWA) | E2 | 2 dias | ✅ concluída |
| E4 | Dashboard (promotora e gestor) | E3 | 1 dia | ✅ concluída |
| E5 | Análises A1–A4 (Streamlit) | E2 | 1 dia | ✅ concluída |
| E6 | PWA, polimento e testes | E3–E5 | 1,5 dia | ✅ concluída |
| F2 | Importação Excel + exportação PDF | E4–E6 | 1,5 dia | ✅ concluída |

**Definição de pronto (todas as etapas):** `ruff check . && pytest` verdes +
aceite visual manual no celular (360px).

---

## E1 — Setup do repositório e ambiente

- [ ] Inicializar git, `.gitignore` (Python/Django/.env), `.editorconfig`
- [ ] Estrutura de pastas conforme TRD §3 (`backend/`, `analytics/`, `docs/`)
- [ ] `pyproject.toml` com ruff + pytest (`DJANGO_SETTINGS_MODULE`, `pythonpath = backend`)
- [ ] `docker-compose.yml` só com Postgres 16 (porta 5432, volume, healthcheck)
- [ ] venv + `requirements.txt`/`requirements-dev.txt` (Django, psycopg, localflavor, whitenoise, pytest-django, ruff)
- [ ] `config/settings/{base,dev,prod}.py` + `.env.example`
- [ ] `manage.py runserver` + `docker compose up -d db` funcionando
- [ ] README: como subir o projeto

**Checkpoint E1:** `./manage.py check` sem erro; Postgres acessível; `ruff check .` limpo.

---

## E2 — Models, migrations e auth

- [ ] App `core`: `Perfil`, `RoleRequiredMixin`, `AuditLog` + signal genérico
- [ ] App `accounts`: `User` custom (`email` como username), views de login/logout,
      CRUD de promotoras (só gestor)
- [ ] App `prospeccao`: modelos do Backend Schema §2
      (`Revendedora`, `Cidade`, `Telefone`, `Marca`, `ProdutoInteresse`, `RedeSocial`, `RedeSocialVinculo`)
- [ ] Signal `m2m_changed` → recalcula `ja_revende` (RF-04)
- [ ] `clean()` obrigatório: ≥1 telefone, ≥1 interesse, ≥1 marca se `vende_outras_marcas`
- [ ] Validação de CPF/CEP com `django-localflavor`; CPF `unique`
- [ ] Extensão `pg_trgm` + índices do schema §2.2
- [ ] Migrations data: grupos, cidades seed, produtos, marcas, redes
- [ ] Admin Django registrado (ferramenta de apoio do gestor)
- [ ] Fixtures de teste: 2 promotoras, ~50 revendedoras distribuídas
- [ ] Testes: regra `ja_revende`, CPF duplicado, escopo de queryset

**Checkpoint E2:** `pytest` verde; `manage.py migrate` limpo em DB novo;
criar revendedora via shell seta `ja_revende` correto nos 3 cenários
(sem marca / com marca / marcas removidas).

---

## E3 — Formulário de campo (PWA)

- [ ] Base template `base.html` + CSS design tokens (UI/UX Brief §2–5)
- [ ] Componentes CSS: botão, input, chip, stepper, card, KPI card, tabela, toast
- [ ] View `RevendedoraCreateView` com form em 4 etapas (HTMX ou form por etapa em session)
- [ ] Máscaras JS: telefone, CPF, CEP, data (progressive enhancement; validação server-side sempre)
- [ ] Tela de revisão (resumo + Editar por bloco) e tela de sucesso (App Flow §2)
- [ ] `RevendedoraListView` (escopo do perfil), `DetailView`, `UpdateView`, `DeleteView` (confirmação)
- [ ] Estados: vazio, loading, erro de validação, erro de rede com retry
- [ ] PRG em todo POST; `?next=` no login
- [ ] Testes de view: login obrigatório, 403 fora do escopo, create happy-path, CPF duplicado 400

**Checkpoint E3:** fluxo completo no celular real:
entrar → cadastrar → revisar → salvar → sucesso → ver na lista; dados corretos no banco.

---

## E4 — Dashboard

- [ ] `DashboardView` variante promotora: 3 KPI cards (total, já revendem, %), últimos 10
- [ ] Variante gestor: 4 KPI + quebra por promotora (query do Schema §4 ORM)
- [ ] Filtro por período (dia/semana/mês) via querystring
- [ ] Card link `Abrir análises ↗` (gestor) → URL do Streamlit
- [ ] Lista de promotoras (CRUD, desativação) com contagem de cadastros
- [ ] Testes: agregações com fixture conhecida (números batem 100%)

**Checkpoint E4:** números do dashboard = contagem manual da fixture.

---

## E5 — Análises A1–A4 (Streamlit)

- [ ] `analytics/` com `Home.py` (login gestor contra `auth_user` + group check)
- [ ] `db.py`: conexão via `DATABASE_URL`, helper de filtro (CTE `base` do Schema §4)
- [ ] `pages/1_A1_*.py` … `4_A4_*.py` com os 4 SQLs do Schema §4 + filtros
      (período, promotora, cidade) em `st.sidebar`
- [ ] Gráficos Plotly (barras A1/A3/A4, donut A2) + `st.dataframe` detalhe
- [ ] Tema Streamlit com as cores do brief (`~/.streamlit/config.toml` versionado)
- [ ] Testes: queries com fixture → A1 soma = total, A2 pct coerente, A3/A4 ordenados

**Checkpoint E5:** as 4 telas abrem com login de gestor; promotora é bloqueada;
números conferem com Django admin.

---

## E6 — PWA, polimento e testes

- [ ] `manifest.json` + ícones (192/512/maskable/favicon) + `theme_color`
- [ ] Service Worker: cache-first p/ estáticos, network-first p/ HTML/dados; aviso offline
- [ ] Botão "instalar app" (beforeinstallprompt)
- [ ] Auditoria Lighthouse: PWA ≥ 90, A11y ≥ 90, Perf ≥ 80 (3G)
- [ ] Checklist acessibilidade do brief §8
- [ ] LGPD: página de exclusão de dados, `AuditLog` gravando mudanças de revendedora
- [ ] `pytest` completo + `ruff check .` verdes
- [ ] Deploy Railway: web + Postgres, variáveis de ambiente, backup diário ativado
- [ ] Usuário gestor seed criado, troca de senha inicial
- [ ] README final: arquitetura, comandos, deploy

**Checkpoint E6 (aceite do MVP):** AC-01 a AC-06 do PRD marcados como cumpridos.

---

## Fase 2 — Importação Excel e exportação PDF

### F2.1 · Importação em lote de revendedoras (PWA)

- [x] `prospeccao/importacao.py`: leitura `.xlsx` (openpyxl), alias de cabeçalho
  (`nome`, `whatsapp`, `estado`, `produtos`…), validação linha a linha
- [x] Regras reaproveitadas do wizard: telefone 10–11 dígitos, UF, CPF (11 dígitos,
  único no banco e na planilha), e-mail, data futura, CEP, `vende_outras_marcas` ×
  `marcas`, catálogo de interesses
- [x] `GET /importar/?modelo=1` baixa planilha-modelo com 2 linhas de exemplo
- [x] Prévia em session (nada grava na análise) → confirmação revalida e grava
- [x] Gestor escolhe a promotora; promotoras importam para a própria carteira
- [x] Teto de 1000 linhas, linhas em branco ignoradas, colunas obrigatórias exigidas

### F2.2 · Exportação em PDF

- [x] Dashboard Django: `core/relatorios.py` (reportlab) + `?exportar=pdf`
- [x] Análises A1–A4: `analytics/relatorio.py` (kaleido + reportlab, A4 horizontal)
  + botão em cada página e relatório completo A1–A4 na Home
- [x] PDF regenerado só quando os dados mudam (kaleido custa ~2s por figura)
- [x] Requisitos: `openpyxl`/`reportlab` em `requirements.txt`, `kaleido` em
  `requirements-dev.txt` e `analytics/requirements.txt` (usa o Chrome do sistema)

**Checkpoint Fase 2:** `ruff check . && pytest` verdes (113 testes); prévia de
importação com erros linha a linha; PDFs abrem com gráfico e tabelas.

---

## F3 · Correções de produção (priorizadas após avaliação)

Ordem acordada com o cliente: 1) commit + SECRET_KEY/migrate, 2) escopo do
Service Worker, 3) LGPD, 4) CI, 5) saúde/rate limit, 6) deploy + Lighthouse,
7) Playwright/CPF/CSV.

### F3.1 · Escopo do Service Worker (AC-06)

- [x] `sw.js` sai de `static/js/` e vira template servido pela rota `core:sw`
  (`/sw.js`) → escopo padrão `/` e o worker passa a controlar navegações
- [x] precache usa a tag `static`, batendo com os nomes com hash do
  `ManifestStorage` em produção
- [x] testes da rota, do conteúdo e do `register()` no HTML

### F3.2 · LGPD / RNF-06 — exclusão real de dados pessoais

- [x] `Revendedora.excluir_dados_pessoais()`: anonimização no lugar
  (nome/CPF/RG/e-mail/nascimento/endereço/observação apagados, telefones e
  redes removidos), linha e vínculo com a promotora preservados
- [x] auditoria mínima: entrada própria `{"motivo": "lgpd"}` e apuração das
  entradas antigas que guardavam o nome; `post_delete` deixa de gravar nome
- [x] `manage.py excluir_dados --cpf/--email [--usuario]`
- [x] ação do admin “Excluir dados pessoais (LGPD RNF-06)”, com aviso de
  registros já anonimizados
- [x] testes `backend/tests/test_lgpd.py` (model, comando, admin, delete duro)

**Checkpoint F3.1+F3.2:** `ruff check . && pytest` verdes (125 testes).

### F3.3 · CI e deploy

- [x] README: `migrate` sai do build para o start (o build não alcança o
  Postgres) e `SECRET_KEY` com o comando de geração
- [x] `.github/workflows/ci.yml`: `ruff check` → `makemigrations --check` →
  `check --deploy --fail-level WARNING` → `pytest` com cobertura, contra um
  Postgres 16 como serviço
- [x] `pytest-cov` no `requirements-dev.txt` (cobertura atual: 90%)

**Checkpoint F3.3:** mesmos comandos do CI rodando verdes localmente
(125 testes, 90% de cobertura).

### F3.4 · Saúde do serviço

- [x] `/saude/` deixa de ser uma lamberta “ok”: consulta `SELECT 1` e
  responde **503** quando o banco não aceita conexão (contrato JSON
  original preservado); testes do caminho feliz e do 503

### F3.5 · Força bruta no login (django-axes)

- [x] `django-axes>=8` no `requirements.txt`; app, `AxesMiddleware` e
  `AxesBackend` (antes do `ModelBackend`) em `base.py`
- [x] 5 tentativas inválidas → **429** com página própria
  (`accounts/bloqueado.html`); login válido zera o contador
- [x] `AXES_USERNAME_FORM_FIELD = "username"`: o form usa o campo
  `username` do `AuthenticationForm`, rotulado como “E-mail”
- [x] testes `backend/tests/test_axes.py` (bloqueio e reset)

### F3.6 · Erros em produção (Sentry, opcional)

- [x] `sentry-sdk[django]` no `requirements.txt`; `config/sentry.py` com
  `configura_sentry()`, chamada ao final de `settings/prod.py`
- [x] só inicializa com `SENTRY_DSN` no ambiente — sem a variável não há
  efeito nem dependência de rede; `SENTRY_TRACES_SAMPLE_RATE` controla o
  sample (default `0`)
- [x] testes `backend/tests/test_sentry.py` (com e sem DSN)

### F3.7 · Lighthouse / AC-06 (medição local)

Ferramenta: **Lighthouse 11.7.1** — a v12+ **removeu a categoria `pwa`**, então
o aceite precisa deversão pinada (ou medição manual do install/offline).

| Página | PWA | A11y | Perf | BP | SEO |
|---|---|---|---|---|---|
| `/contas/entrar/` | 100 | 100 | 100 | 100 | 100 |
| `/` (dashboard, autenticado) | 100 | 100 | 100 | 100 | 100 |
| `/revendedoras/nova/` (wizard) | 100 | 100 | 100 | 100 | 98 |

- [x] Instalação confirmada (`installable-manifest` e `maskable-icon` PASS:
  manifest + service worker atendem os requisitos de instalabilidade)
- [x] Contraste apontado pela medição corrigido: novo token `--verde-700`
  (#0B6B44) para **texto** — `.badge.ok` estava 3.78:1 (mínimo 4.5); aplicado
  também em `.step.done` e no `.step-dot` (texto branco sobre verde)
- pendente: repetir em produção (HTTPS, assets com hash/compressão) antes de
  marcar o AC-06/Lighthouse no checklist do README

---

## Riscos do plano

| Risco | Impacto | Resposta |
|---|---|---|
| Form em 4 etapas mais lento que o esperado | Médio | E3 pode entregar form único scrollável e virar stepper depois |
| Deploy no Railway com CSRF/HTTPS | Baixo | Testar cedo (fim da E4) |
| Streamlit lendo DB junto com Django | Baixo | Postgres suporta; só leitura no analytics |
| Escopo cilar em detalhes visuais | Médio | Seguir o brief ao pé da letra, sem inventar na hora |

## Comandos de verificação (todo push)

```bash
ruff check .
pytest
./manage.py check --deploy   # prod
```

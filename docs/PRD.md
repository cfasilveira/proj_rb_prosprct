# PRD — RB Prospecta

**Versão:** 1.0 · **Data:** 27/09/2026 · **Status:** Aprovado

## 1. Visão do produto

O RB Prospecta é a ferramenta tecnológica do canal de venda direta para prospecção e
cadastro de revendedoras. Promotoras coletam os dados da revendedora **em campo, de forma
verbal**, preenchendo um formulário no celular. O gestor acompanha a carteira por meio de
análises de volume, perfil e interesse.

## 2. Objetivos

| # | Objetivo | Métrica (KPI) |
|---|---|---|
| O1 | Aumentar a base de revendedoras cadastradas | Cadastros/mês por promotora |
| O2 | Entender quantas já estão no mercado | % de revendedoras que já revendem |
| O3 | Mapear marcas concorrentes presentes na carteira | Nº de marcas distintas mapeadas |
| O4 | Direcionar o portfólio de vendas | Distribuição de interesse por categoria de produto |
| O5 | Cobrir território | Nº de cidades/bairros alcançados |

## 3. Personas

### 3.1 Promotora (usuária de campo)
- Usa o celular, em pé, conversando com a revendedora.
- Conexão instável; precisa de poucos cliques e linguagem simples.
- Cadastrou: só enxerga as revendedoras que ela própria cadastrou.

### 3.2 Gestor do canal
- Usa desktop.
- Acompanha o desempenho de todas as promotoras e a saúde da carteira.
- Acesso total: métricas consolidadas e cadastro de promotoras.

## 4. Escopo do MVP

### 4.1 Em escopo

**Autenticação e perfis**
- Login/senha com perfis `promotora` e `gestor`.
- Gestor cria, edita e desativa promotoras.
- Promotora visualiza somente os próprios cadastros.

**Cadastro de revendedora (formulário de campo)**
- Formulário em etapas (stepper), mobile-first, submissão online.
- Campos: ver seção 5.
- Edição e exclusão lógica do cadastro pela promotora.

**Dashboard**
- Visão da promotora: total de cadastros, quantas já revendem, últimos cadastrados.
- Visão do gestor: mesma visão consolidada + por promotora.

**Análises (Streamlit)**
- A1 — Quantidade de revendedoras cadastradas por promotora.
- A2 — Das revendedoras cadastradas, quantas já revendem.
- A3 — Quais marcas essas revendedoras já revendem.
- A4 — Quais produtos elas têm interesse em revender.

**PWA**
- Manifesto + service worker: instalável na tela inicial, cache do shell.

### 4.2 Fora de escopo (MVP)

- Cadastro offline com sincronização posterior.
- Integração com WhatsApp/envio automático de mensagens.
- Exportação CSV/PDF dos relatórios (fase 2).
- Multi-tenant (várias redes) — produto é single-tenant.
- Geolocalização/CEP automático.
- App nativo Android/iOS.
- ERP/integração com faturamento.

## 5. Requisitos funcionais

### RF-01 Login
- **RF-01.1:** Usuária informa e-mail e senha; erro claro em credenciais inválidas.
- **RF-01.2:** Sessão expira após inatividade (24h).
- **RF-01.3:** Promotora autenticada cai no dashboard próprio; gestor, no dashboard consolidado.

### RF-02 Gestão de promotoras (apenas gestor)
- Criar promotora: nome, e-mail, senha, território (cidade/estado).
- Editar dados; desativar (soft delete) sem apagar cadastros feitos por ela.

### RF-03 Cadastro de revendedora
- **RF-03.1:** Campos obrigatórios: nome completo, telefone/WhatsApp.
- **RF-03.2:** CPF com validação de dígito verificador; **único** no sistema.
- **RF-03.3:** RG, endereço, bairro, cidade, CEP, data de nascimento (data completa), e-mail são opcionais, com máscaras de validação.
- **RF-03.4:** Telefone/WhatsApp: aceitar múltiplos números (mínimo 1), com DDD e máscara.
- **RF-03.5:** "Vende outras marcas?": sim/não. Se sim → seleção múltipla de marcas (livre + pré-cadastradas).
- **RF-03.6:** Redes sociais: escolher qual é para contato e qual é para seguir; informar perfil/URL. Aceitar múltiplas.
- **RF-03.7:** Produtos de interesse: seleção múltipla entre categorias fixas
  (cosméticos, vitaminas, suplementos, alimentos, roupa íntima, roupa fitness,
  bijuteria, sapato, remédios, outros).
- **RF-03.8:** Toda revendedora é vinculada à promotora logada e à data/hora do cadastro.
- **RF-03.9:** Após salvar, exibir confirmação e opção "novo cadastro".
- **RF-03.10:** Erros de validação aparecem no campo, sem perder o que já foi digitado.

### RF-04 Indicador "já revende"
- **RF-04.1:** O campo **não é digitado**: é derivado. Se a revendedora tem 1 ou mais
  marcas marcadas em "vende outras marcas" → `ja_revende = true`; caso contrário, `false`.
- **RF-04.2:** Alterar as marcas revendidas recalcula o indicador automaticamente.

### RF-05 Dashboard
- **RF-05.1 (promotora):** total de cadastros, quantas já revendem, % de conversão,
  lista dos 10 últimos cadastros.
- **RF-05.2 (gestor):** tudo acima consolidado + quebra por promotora.
- **RF-05.3:** Métricas do dia/semana/mês.

### RF-06 Análises (Streamlit)
- **RF-06.1:** A1–A4 com filtros por período, promotora e cidade.
- **RF-06.2:** Gráficos de barras/pizza + tabela detalhada.
- **RF-06.3:** Acesso restrito ao perfil gestor.

### RF-07 PWA
- **RF-07.1:** Instalável na tela inicial (Android/iOS/desktop).
- **RF-07.2:** Shell estático em cache; requisições de dados sempre da rede.

## 6. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Primeira pintura do formulário < 2s em 3G |
| RNF-02 | Alvo de toque ≥ 44px; contraste AA |
| RNF-03 | Dados transmitidos por HTTPS |
| RNF-04 | Backup diário do Postgres (retensão 7 dias) |
| RNF-05 | Log de auditoria de criação/edição de revendedoras |
| RNF-06 | LGPD: dados pessoais (CPF, RG, e-mail) somente para as finalidades do canal; exclusão sob demanda |
| RNF-07 | Disponibilidade 99% em horário comercial |

## 7. Critérios de aceite (resumo)

- **AC-01:** Promotora consegue cadastrar uma revendedora completa em ≤ 2 minutos.
- **AC-02:** CPF duplicado é bloqueado com mensagem clara.
- **AC-03:** `ja_revende` bate 100% com a presença de marcas revendidas em qualquer teste.
- **AC-04:** As 4 análises mostram números coerentes com os dados de teste inseridos.
- **AC-05:** Gestor não enxerga cadastro de outra empresa (n/a single-tenant) e promotoras
  não enxergam carteira das colegas.
- **AC-06:** App instalado como PWA e navega sem erro offline no cache do shell.

## 8. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Coleta verbal gerar dado errado | Alto | Máscaras + validação inline + revisão antes do envio |
| Instabilidade de rede em campo | Médio | PWA com cache; exibir estado de erro com reenvio |
| Baixa adoção pela promotora | Alto | Stepper curto, linguagem simples, meta visível no dashboard |
| Dados pessoais vazados | Alto | HTTPS, perfis de acesso, log de auditoria |

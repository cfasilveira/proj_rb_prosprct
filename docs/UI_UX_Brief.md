# Brief de UI/UX — RB Prospecta

**Versão:** 1.0 · **Data:** 27/09/2026
**Depende de:** PRD v1.0, App Flow v1.0

## 1. Direção visual

**Tom:** profissional, direto, sem fricção. A promotora está em pé, conversando — a
interface deve desaparecer e deixar a conversa fluir.

- **Princípio 1 — Mobile-first:** 360–414px é o canvas principal. Desktop é derivado.
- **Princípio 2 — Poucos toques:** cada etapa do form ≤ 6 campos; alvo de toque ≥ 44px.
- **Princípio 3 — Um call-to-action por tela:** nunca dois botões primários competindo.
- **Princípio 4 — Feedback imediato:** todo envio tem estado visível (loading/sucesso/erro).

## 2. Cores

| Papel | Nome | Hex | Uso |
|---|---|---|---|
| Primária | Azul RB | `#1B4DB1` | Botões primários, links, topo do stepper, marca |
| Primária escura | Azul RB 800 | `#12357A` | Hover/pressed, textos sobre claro |
| Primária clara | Azul RB 50 | `#EAF1FD` | Fundos de destaque, chips ativos |
| Destaque | Verde conversão | `#128C5A` | Sucesso, indicador "já revende" positivo |
| Destaque claro | Verde 50 | `#E6F5EE` | Fundo de badge de sucesso |
| Atenção | Âmbar | `#C77700` | Avisos (ex.: CPF já existe) |
| Erro | Vermelho | `#C62828` | Mensagens de erro, validação |
| Neutro 900 | Grafite | `#1A1A1A` | Texto principal |
| Neutro 600 | Cinza | `#5F6368` | Texto secundário, labels |
| Neutro 300 | Cinza claro | `#DADCE0` | Bordas, divisores |
| Neutro 50 | Off-white | `#F7F8FA` | Fundo da página |
| Branco | — | `#FFFFFF` | Superfícies, cards |

**Regras:**
- Contraste mínimo **WCAG AA** (4.5:1 texto normal; 3:1 texto grande).
- Cor **nunca** é o único indicador de erro/sucesso (sempre ícone + texto).
- Modo de alto contraste: opcional, fase 2.

## 3. Tipografia

| Uso | Fonte | Tamanho / Line-height | Peso |
|---|---|---|---|
| Título de página (H1) | Inter | 24px / 32px | 700 |
| Título de seção (H2) | Inter | 20px / 28px | 600 |
| Corpo | Inter | 16px / 24px | 400 |
| Label de campo | Inter | 14px / 20px | 500 |
| Caption / ajuda | Inter | 13px / 18px | 400 |
| Número de KPI | Inter (tabular-nums) | 32px / 40px | 700 |
| Monetário/tabela | `font-variant-numeric: tabular-nums` | 14px | 500 |

- Fallback: `Inter, -apple-system, "Segoe UI", Roboto, sans-serif`.
- Inter via `woff2` self-host (sem CDN — PWA deve funcionar do cache).
- Corpo nunca < 16px no mobile (zoom iOS não distorce).

## 4. Espaçamento e grid

- Escala: `4 · 8 · 12 · 16 · 24 · 32 · 48px`.
- Padding de página mobile: `16px` laterais; desktop: `32px`, container `max-width: 1120px`.
- Grid de KPIs: 2 colunas no mobile, 4 no desktop, gap `16px`.
- Raio de borda: inputs/cards `12px`, botões `10px`, chips `999px`.

## 5. Componentes

### 5.1 Botão
| Variante | Aparência | Uso |
|---|---|---|
| Primário | fundo `#1B4DB1`, texto branco, h=48px | Salvar, Próximo, Entrar |
| Secundário | borda 1px `#DADCE0`, texto `#1B4DB1`, h=48px | Voltar, Cancelar |
| Fantasma | texto `#1B4DB1`, sem borda | Links de ação discretos |
| Perigo | fundo `#C62828`, texto branco | Excluir (só após confirmação) |

Estados: `default → hover (escurecer 8%) → active (scale .98) → disabled (40% opac) → loading (spinner + label "Salvando…")`.

### 5.2 Input
- Altura 48px, borda `#DADCE0`, foco: borda `#1B4DB1` + ring `0 0 0 3px #EAF1FD`.
- Erro: borda `#C62828`, mensagem sob o campo com ícone ⚠ + texto.
- Label sempre acima (nunca placeholder como label).
- Máscaras: telefone `(00) 00000-0000`, CPF `000.000.000-00`, CEP `00000-000`,
  data `DD/MM/AAAA` — com `inputmode` adequado (numeric/tel).

### 5.3 Chip / multiseleção (produtos, marcas, redes)
- Chip: padding `8px 14px`, raio 999px, borda `#DADCE0`.
- Selecionado: fundo `#EAF1FD`, borda `#1B4DB1`, texto `#12357A`, ✓ à esquerda.
- Área de toque inteira do chip ≥ 44px de altura.
- "Outro…" abre campo de texto inline para marca livre.

### 5.4 Stepper (formulário de campo)
- 4 passos: `Contato → Endereço → Mercado → Interesse`.
- Passo atual: círculo `#1B4DB1` com número branco.
- Concluído: círculo `#128C5A` com ✓. Futuro: círculo com borda `#DADCE0`.
- Barra de progresso linear sob os círculos.
- Passos concluídos são clicáveis (voltar); futuros, não.
- Fixo no rodapé: `← Voltar` (secundário) e `Próximo →` (primário).

### 5.5 Card
- Fundo branco, borda 1px `#DADCE0`, raio 12px, padding 16–24px,
  sombra `0 1px 3px rgba(0,0,0,.08)`.

### 5.6 KPI card
- Label 13px `#5F6368` · número 32px/700 · variação com seta ▲▼ verde/vermelho.
- Ex.: `Cadastradas 128`, `Já revendem 64 (50%)`.

### 5.7 Tabela
- Cabeçalho `#F7F8FA`, linhas alternadas sutis, hover `#EAF1FD`.
- Mobile: virar cards empilhados (não scroll horizontal).
- Ações da linha: botão fantasma `Ver`, `Editar`.

### 5.8 Toast/snackbar
- Inferior, largura auto, raio 8px. Sucesso `#128C5A` (3s), erro `#C62828` (fica até fechar).

## 6. Ícones e imagens

- Set: **Material Symbols Rounded** self-host (peso 400), tamanho 20–24px.
- Sem emoji como ícone funcional.
- Imagens: só logo (SVG) e ícones PWA; nenhuma foto decorativa no fluxo de campo
  (carrega rápido em 3G).

## 7. Microcopy (tom de voz)

- Português do Brasil, você, frases curtas, verbo no início.
- Sem jargão interno. "Revendedora", não "lead" ou "cliente".
- Erros orientam a ação: `Informe o telefone com DDD.` (não: `Campo inválido`).
- Sucesso celebra sem exagero: `Revendedora cadastrada ✓`.
- Obrigatórios marcados com `*` + texto no sumário: `Campos com * são obrigatórios`.

## 8. Acessibilidade (checklist obrigatório)

- [ ] Todos os inputs com `<label for>` associado.
- [ ] Navegação por teclado completa; foco visível (`:focus-visible`).
- [ ] Contraste AA em todos os pares de cor.
- [ ] Erros anunciados (`aria-live="polite"`) além de cor.
- [ ] Stepper com `aria-current="step"`.
- [ ] Alvos de toque ≥ 44×44px.
- [ ] Zoom de 200% sem quebrar layout.
- [ ] `lang="pt-BR"` no HTML.

## 9. PWA — visual

| Item | Definição |
|---|---|
| Ícone | Letra "RB" em branco sobre fundo `#1B4DB1`, raio adaptativo |
| Splash | Fundo `#1B4DB1`, logo centralizado |
| Barra do navegador | `theme_color: #1B4DB1`, `background_color: #F7F8FA` |
| Ícones | 192px, 512px, maskable 512px, favicon 32/16 |

## 10. Referências de tela

| Tela | Descrição |
|---|---|
| Login | Logo, email, senha, botão `Entrar` centralizado, max-width 400px |
| Dashboard promotora | Saudação + 3 KPI cards + lista `Últimos cadastros` + botão flutuante `+` |
| Dashboard gestor | 4 KPI cards + tabela por promotora + card link `Abrir análises ↗` |
| Form 4 etapas | Stepper no topo, campos no meio, nav fixa no rodapé (sticky) |
| Revisão | Lista `label: valor` com links `Editar` por bloco |
| Sucesso | Ícone ✓ verde, `Revendedora cadastrada`, botões `Nova revendedora` / `Ver lista` |
| Streamlit | Padrão nativo do Streamlit com o tema das cores acima (`config.toml`) |

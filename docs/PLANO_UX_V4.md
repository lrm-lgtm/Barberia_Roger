# Roger Barbearia — Plano de redesign UX V4

**Status:** planejamento para aprovação; nenhuma implementação de interface incluída neste documento.  
**Repositório oficial:** `lrm-lgtm/Barberia_Roger` — branch `main`.  
**Escopo:** jornada pública mobile-first de agendamento; não altera neste ciclo as regras financeiras nem expõe painéis internos.

## 1. Problema observado (V3)

Nos prints de teste no Android, os horários aparecem separados da faixa de datas por uma quantidade excessiva de conteúdo e rolagem vertical. A escolha do profissional ocupa espaço e gera uma decisão obrigatória aparente, mesmo quando "qualquer disponível" deveria ser padrão. Depois de tocar no horário, o cliente ainda precisa usar um CTA "Continuar". O cabeçalho do protótipo exibe áreas Cliente/Barbeiro/Gestor no contexto público.

**Hipótese de UX:** concentrar data + horários no primeiro viewport relevante, deixar o profissional opcional e remover a confirmação intermediária reduzirá esforço e tempo até a identificação.

## 2. Jornada-alvo

1. **Serviço:** cliente desliza cartões com foto, nome, preço e duração e toca no desejado.
2. **Quando:** próxima data com disponibilidade aparece destacada, com carrossel horizontal de dias e grade de horários imediatamente abaixo; sem escolher profissional obrigatoriamente.
3. **Horário:** tocar num horário avança à identificação/revisão, sem outro CTA intermediário.
4. **Identificação e confirmação:** nome + celular; resumo claro de serviço, data, horário, profissional designado ou preferência, preço e regra de cancelamento; ação final explícita "Confirmar agendamento".
5. **Sucesso:** somente após retorno de confirmação da API; exibir ID, data, hora e profissional atribuído. Modo demo nunca afirma uma reserva real.

Meta de projeto: **serviço → dia → horário**, sem bloqueios desnecessários. A data já destacada pode permitir serviço → horário para quem aceita a primeira opção.

## 3. Layout de tela "Escolha seu horário"

Hierarquia visual de cima para baixo:

- Cabeçalho público compacto `Roger Barbearia` + voltar (sem tabs de administração no link do cliente).
- Título `Escolha seu horário` (um título, sem barra de progresso alta).
- Resumo compacto do serviço `Corte + barba · 60 min · R$ 70` com `Trocar` discreto.
- Linha `Outubro 2026` + ícone de calendário mensal discreto; logo abaixo **carrossel horizontal de dias**, com parte do próximo item visível e rolagem por toque.
- Texto `Horários disponíveis` + dia selecionado; grade de até 3 colunas, com botões de toque confortáveis. Mostrar primeiro os horários mais próximos; se excederem o espaço, oferecer `Ver mais horários` ou rolagem somente da área de horários, sem esconder a faixa de datas.
- Filtro compacto após datas/horários `Qualquer barbeiro · Alterar` ou ícone secundário no cabeçalho de horários. Tocar abre bottom sheet com profissionais elegíveis para o serviço; tocar em profissional atualiza as opções do mesmo dia. Não abrir sheet automaticamente.
- Nenhum botão `Continuar` fixo na tela de horários: **toque no horário prossegue**. O usuário pode voltar e alterar escolhas antes de confirmar a reserva.

**Não usar:** um carrossel de horários, múltiplos CTAs concorrentes, calendário mensal sempre expandido, seção grande de profissional, altura grande de cabeçalho/hero e horários fictícios em produção.

### Exemplo textual (valores demonstrativos)

```text
< Roger Barbearia
Escolha seu horário
Corte + barba · 60 min · R$ 70           Trocar

OUTUBRO 2026                               [calendário]
[SEG 12] [TER 13] [QUA 14] [QUI 15] →  (rolagem horizontal)

Horários disponíveis · Seg, 12 de outubro
[09:00] [09:30] [10:00]
[10:30] [11:00] [11:30]
[13:00] [13:30] [14:00]
[Ver mais horários]

Qualquer barbeiro                          Alterar
```

Esse esboço NÃO é uma promessa de expediente em feriados; datas/horários no produto real vêm das regras da API.

## 4. Regras de interação

| Situação | Comportamento obrigatório |
| --- | --- |
| Entrou após serviço | Abrir no primeiro dia com vaga dentro de horizonte configurado; mostrar feedback enquanto busca. |
| Data sem vaga | Mostrar indisponibilidade; oferecer próximo dia com vaga, sem horários artificiais. |
| Seleção por swipe | Carrossel suporta scroll-snap horizontal; data selecionada visível, foco perceptível e ações acessíveis também por teclado/toque. |
| Escolheu horário | Salvar escolha em estado de interface e avançar à etapa de dados. Não criar reserva nesse momento. |
| Voltou da identificação | Preservar serviço, dia, horário e profissional, salvo quando a disponibilidade tiver mudado. |
| Alterou profissional ou data | Limpar horário anterior, recalcular disponibilidade; não manter horário inválido. |
| Reservas concorrentes | Backend revalida ao confirmar e retorna conflito; interface volta para escolha de horário com mensagem e novas opções. |
| Barbeiro "qualquer" | Somente preferência de consulta. Ao confirmar, backend atribui barbeiro elegível real. |
| Hoje / passado | Não oferecer horários passados e respeitar timezone da barbearia. |
| Feriado / folga | Obedecer escala/feriados/bloqueios configurados; não depender de disponibilidade simulada. |
| Modo demonstração | Mostrar selo claro `Demonstração`; não coletar telefone real nem criar falsa confirmação. |

## 5. Dados/API necessários

O backend atual possui `GET /api/catalog`, `GET /api/availability?service_id&date&barber_id` e `POST /api/bookings`. Preservar a API de reserva; **não** alterar regras de prevenção de conflito por mudança visual.

Para descobrir de maneira eficiente o *primeiro dia com vaga*, implementar um endpoint de resumo, por exemplo `GET /api/availability/days?service_id=...&barber_id=...&start=YYYY-MM-DD&count=14`, com resultado por dia (disponível/indisponível, opcionalmente primeiro horário), ou estratégia equivalente em lote. Evitar disparar 30 chamadas individuais simultâneas. Estabelecer cache curto, cancelamento de requisições obsoletas e atualização após mudança de filtro.

A lista de horários de uma data continua consultando o endpoint existente. A seleção atual não é reserva: o `POST /api/bookings` só acontece após confirmação final com identidade verificada quando a função pública for disponibilizada.

## 6. Organização de código (repositório oficial)

| Arquivo/módulo | Mudança planejada |
| --- | --- |
| `frontend/src/App.tsx` | Separar o agendamento em componentes `ServiceCarousel`, `DateRail`, `TimeSlotGrid`, `ProfessionalSheet`, `BookingReview`; remover CTA intermediário na etapa de horário e reduzir cabeçalhos. |
| `frontend/src/styles.css` | CSS mobile-first com `scroll-snap-type: x proximity`, dimensões compactas, foco/contraste, área segura e uso cuidadoso de `100dvh`; evitar múltiplas rolagens verticais concorrentes. |
| `frontend/src/api.ts` + `types.ts` | Adicionar resumo de disponibilidade por dia, estado de carregamento e tratamento de respostas defasadas. |
| `backend/app/main.py` | Acrescentar serviço agregado por dias sem remover validação no momento da reserva. |
| `backend/tests/test_api.py` | Testes de dias indisponíveis, elegibilidade, domingo/feriado conforme calendário configurado, limites e conflitos. |
| `docs/index.html` | **Eliminar divergência entre protótipo estático e React**: publicar um build da mesma interface em modo demonstração no Pages; evitar manter duas implementações manuais de UX. |
| `.github/workflows/ci.yml` | Build/checagem de frontend e backend; para Pages, publicar build demo com marcação explícita de simulação. |

A V3 publicada em `docs/index.html` hoje é uma prévia HTML independente, não a mesma aplicação de `frontend/src/App.tsx`. Esse desalinhamento deve ser corrigido como parte da V4.

## 7. Regras visuais / responsividade

- Primeiro viewport em 360 × 740 e 393 × 852: mostrar título, serviço, datas e **pelo menos 6 horários visíveis** sem precisar rolar a página principal, quando existirem 6 horários.
- Datas com altura compacta, estado ativo de alto contraste e indicação de disponibilidade, sem bolinhas decorativas que façam o cliente adivinhar o significado.
- Botões de horário com área tocável de pelo menos 44 × 44 CSS px; `aria-pressed` ou seleção equivalente.
- Animações discretas e `prefers-reduced-motion` respeitado; calendário mensal e bottom sheet fecham por botão, gesto/tecla quando aplicável.
- Se houver poucos horários, ocupar bem o espaço sem ampliar cartões demais. Se houver muitos, mostrar os primeiros e permitir acesso imediato ao restante.
- A marca/cores devem ser personalizáveis. Não usar preço/corte fictício em produção.

## 8. Critérios de aceite do redesign

1. Em Android e iPhone, deslizar os serviços e as datas não movimenta a página verticalmente de maneira indevida.
2. Após escolher serviço, pelo menos 6 horários (quando disponíveis) aparecem sem rolagem vertical principal em 360 × 740, com o navegador móvel aberto.
3. Profissional é opcional; o cliente chega aos horários sem tocar nesse filtro.
4. Ao tocar num horário disponível, a etapa de dados aparece imediatamente, com resumo e um **único** botão final de confirmação.
5. Voltar preserva escolhas válidas; trocar data/profissional limpa horário inválido.
6. Não é possível reservar o mesmo barbeiro em horários sobrepostos; conflito é tratado com recarregamento de vagas.
7. Demo pública não coleta dados pessoais, não chama backend real e não diz "agendado" sem registro confirmado.
8. O mesmo frontend alimenta a prévia publicada e a aplicação: não há dois projetos de interface divergentes.
9. Painel do barbeiro e gestor só aparecem em rotas autenticadas; não devem estar na interface pública do cliente.

## 9. Sequência recomendada

**Fase A — UX isolado**: componentes e estado, com dados mockados; validar em celular e ajustar densidade vertical. Entrega: prévia navegável e imagens reais da tela.

**Fase B — Disponibilidade**: endpoint agregado de dias, atualização dos horários e regras de conflitos; testes backend/frontend. Entrega: agenda de teste coerente.

**Fase C — Publicação unificada**: build frontend com modo demo, CI e GitHub Pages. Entrega: link estável no navegador do celular, sem dados pessoais.

**Fase D — Piloto seguro**: autenticação/verificação de telefone, bloqueios de abuso, LGPD, horários individuais reais, logs e QA. Só então permitir reservas públicas reais.

## 10. Fora deste ciclo

Financeiro, comissões, WhatsApp automático, fidelidade, pagamentos e painel completo não devem bloquear a V4. Permanecem no roadmap do sistema completo.

**Decisão sugerida para aprovação:** carrossel de serviços + carrossel de dias + grade compacta de horários + profissional opcional + avanço automático ao tocar no horário.
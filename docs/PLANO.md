# APP BARBEARIA — Planejamento incremental

## Produto

Agendamento mobile-first para cliente, agenda individual por barbeiro e administração separada para o gestor. O cliente chega por link, desliza pelos serviços em carrossel horizontal, escolhe barbeiro opcional, data e horário, informa nome/celular e confirma.

## Entrega inicial (v0.1)

- Frontend React/Vite/TypeScript responsivo e carrossel de serviços com rolagem horizontal.
- Consulta de catálogo/horários pela API FastAPI.
- Cadastro de reserva local em SQLite; suporta PostgreSQL via `DATABASE_URL`.
- Validação de conflitos de intervalos, duração, almoço, domingo, horizonte de 60 dias e reserva concorrente por barbeiro.
- Operação demo com serviços, preços e barbeiros fictícios. **Não é produção.**

## Próximas fases

1. **UX do cliente:** fotos de serviços fornecidas pelo estabelecimento, personalização e acessibilidade, testes reais no Android/iPhone.
2. **Segurança antes de acesso público:** identidade por código no celular, anti-spam e rate-limit, LGPD, consentimento separado para marketing, auditoria, políticas de retenção, migrations/Alembic.
3. **Agenda real:** horários individuais, folgas, feriados, intervalos, serviços por barbeiro, tempo de preparação, encaixes e cancelamento autenticado.
4. **Painel do profissional:** autenticação, agenda própria, check-in, concluir atendimento, justificativas de ausência.
5. **Gestão:** RBAC, visão multi-profissional, catálogo/fotos/preços, comandas, caixa, pagamento, despesas, comissões.
6. **Comunicação:** WhatsApp Business Platform, templates aprovados, lembretes, acompanhamento de entrega, retorno em 30 dias mediante consentimento; não comunicar agendamentos ainda existentes.
7. **Pagamentos:** Mercado Pago (Pix/cartão), webhook verificado e idempotência.
8. **PWA + deploy:** observabilidade, backups, monitoramento, CI e domínio público, sempre depois das etapas de segurança.

## Critérios de aceite principais

- Seleção do serviço por deslize horizontal com um toque.
- Em celular, parte do próximo cartão fica visível.
- Datas e barbeiros com rolagem horizontal independente.
- A API recalcula disponibilidade sob bloqueio de concorrência no instante de criar a reserva.
- Mesmo barbeiro não recebe agendamentos sobrepostos, ainda que diferentes serviços/durações.
- Atribuição `primeiro disponível` escolhe profissional real; nenhuma reserva fica com `barber_id=any`.
- Cliente não acessa painéis de gestão sem autenticação (painéis ainda não existem nesta versão).
- Modo sem API informa que é prévia, não confirma falsamente um agendamento.

## Decisões pendentes

Identidade visual e logotipo oficial; catálogo real (fotos, nomes, preços, duração); escala de trabalho individual; política de cancelamento/tolerância; telefone empresarial para WhatsApp oficial; hospedagem e domínio.

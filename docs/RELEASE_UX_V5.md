# Roger Barbearia — UX V5 (catálogo na primeira dobra)

## Entrega validada

- Abertura sem banner hero gigante. O serviço fica na primeira dobra do celular.
- Carrossel horizontal de serviços com cartões menores, próximo cartão parcialmente visível, indicação de posição e seleção em um toque.
- Data horizontal, horários em grade e avanço direto ao tocar num horário.
- Filtro de profissional opcional; mantém "qualquer barbeiro" como padrão.
- Calendário secundário em grade mensal com dias bloqueados pela disponibilidade consultada, e botões de trocar mês.
- A seleção prévia é preservada quando o cliente volta para alterar a data ou horário.
- Demonstração usa dados fictícios e não coleta nome ou telefone nem reserva de verdade.

## Caminho para testar

Uma única implementação React (`frontend/src/App.tsx`). A rotina `.github/workflows/publish-preview.yml` recompila e versiona `docs/index.html` e `docs/assets` ao alterar `frontend/**`.

Para abrir o HTML compilado, o repositório pode usar a prévia GitHack. Endereço oficial desejado: `https://lrm-lgtm.github.io/Barberia_Roger/` após ativação do GitHub Pages em `main` / `/docs`.

## Verificações

- Sintaxe TSX: compilação da prévia pela GitHub Actions.
- CSS: análise de sintaxe local com PostCSS.
- API: 10 testes automatizados passaram antes da publicação.
- Atalho de navegação: serviço → data → horário → revisão → conclusão simulada.

## Bloqueios para produção real

- Preços, duração e nomes de profissionais ainda são **exemplos**.
- Escalas e exceções por profissional ainda não estão cadastradas.
- Falta OTP/verificação de telefone, autenticação do gestor, proteção contra abuso, administração de equipe e migrações.
- Pagamento, WhatsApp e domínio próprio ainda não foram integrados.
- Antes do lançamento, validar visualmente em Android e iPhone reais e auditar proteção de dados.

**Não confundir prévia com aplicativo pronto para receber clientes.**

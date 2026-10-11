# Roger Barbearia — V6: configuração da operação

**Status:** backend para piloto local. Ainda não é painel administrativo de produção.

A versão V6 permite configurar serviços, profissionais, vínculo serviço/profissional, turnos semanais individuais e bloqueios excepcionais, sem números ou nomes inventados no ambiente real. A interface pública de demonstração continua sem conexão com a API.

## Decisões de segurança

- `BOOKING_ENABLED=false` e `SEED_DEMO_DATA=false` são os valores iniciais. Não habilitar em hospedagem pública sem verificação de telefone, rate limiting, autenticação e LGPD.
- Admin desativado por padrão; exige `ADMIN_API_KEY` com **mínimo de 32 caracteres aleatórios**, somente no servidor. Nunca publicar esta chave no React, GitHub Pages, repositório, URLs ou screenshots.
- Painel web administrativo, identidade individual/RBAC, trilha de auditoria e recuperação de acesso ainda não estão prontos. O Bearer de administrador é **apenas um mecanismo para piloto local**.
- Conectar o frontend a uma API acessível pela internet requer ambiente de produção com HTTPS, PostgreSQL e migrações (Alembic). O banco SQLite com `create_all` não é caminho de migração de produção.
- Os dados de clientes são privados e acessíveis apenas por endpoint administrativo protegido. Não exportá-los para a prévia pública.

## Iniciar piloto local

```bash
cd backend
pip install -r requirements-dev.txt
# Nunca cole a chave dentro do código ou do repositório.
export ADMIN_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(40))')"
export DATABASE_URL="sqlite:///./barberia.db"
export SEED_DEMO_DATA=false
export BOOKING_ENABLED=false
uvicorn app.main:app --reload --port 8000
```

Defina `SEED_DEMO_DATA=true` **apenas num banco novo de teste local** para criar nomes, preços e turnos fictícios. Ao migrar de versões antigas do banco de demonstração, **não** rode o seed em dados reais: o schema mudou, e uma migração formal é exigida antes de produção.

### Configurar dados

Os endpoints privados estão em `http://localhost:8000/docs`. Requerem cabeçalho `Authorization: Bearer <ADMIN_API_KEY>`. Use Swagger ou uma ferramenta local para as requisições. Não é necessário informar essa chave ao cliente.

| Endpoint | Função |
|---|---|
| `GET /api/admin/config` | Ler serviços, barbeiros, turnos e bloqueios |
| `PUT /api/admin/services/{id}` | Criar ou alterar serviço, valor em centavos, duração e status |
| `PUT /api/admin/barbers/{id}` | Criar/alterar profissional e serviços que executa |
| `PUT /api/admin/barbers/{id}/shifts` | Substituir todos os turnos semanais do profissional |
| `POST /api/admin/barbers/{id}/blocks` | Bloquear dia ou intervalo, sem deslocar reservas confirmadas |
| `DELETE /api/admin/barbers/{id}/blocks/{block_id}` | Excluir bloqueio existente |
| `GET /api/admin/bookings?day=AAAA-MM-DD` | Listar reservas e dados privados para operação autorizada |

Exemplo de turno (para a operação configurar conforme os dias reais):

```json
{"shifts":[
  {"weekday":0,"start":"09:00","end":"12:00"},
  {"weekday":0,"start":"13:00","end":"18:00"}
]}
```

Segunda-feira `0`, terça `1`, ..., domingo `6`. Os intervalos são de 30 minutos; o serviço deve caber integralmente num turno. É possível abrir aos domingos e ter folga noutro dia.

Exemplo de bloqueio parcial:

```json
{"date":"2026-10-19","start":"14:00","end":"16:00","reason":"Compromisso"}
```

Quando já existir uma reserva confirmada nesse horário, a resposta será `409`. É necessário reagendar primeiro; a V6 **não cancela nem remarca clientes automaticamente**.

## Critérios testados

- Leitura/administração sem chave -> bloqueada.
- Chave de servidor curta -> inicialização rejeitada.
- Profissional sem turno -> nenhum horário livre.
- Turnos separados por almoço e indisponibilidade parcial.
- Conflito de turnos e mudança que excluiria reservas -> rejeitados.
- Bloqueio em dia com reserva -> rejeitado; bloqueio removido reabre o horário.
- Reserva simultânea com bloqueio -> só uma operação ocupa o intervalo.
- Domingo com expediente explícito -> funciona.
- Dados pessoais não retornam na confirmação pública; aparecem somente na consulta administrativa autenticada.

Teste: `cd backend && pytest -q`.

## Próximo incremento

1. Formulário de gestão local com autenticação individual, papéis e auditoria.
2. Migração de produção e cadastro dos **serviços/preços/duração** reais.
3. Cadastro de **equipe, competências, horários e folgas** reais.
4. Políticas de cancelamento, atraso e reagendamento, sem mudanças silenciosas em reservas.
5. Verificação telefônica, limites de abuso e deploy privado/público adequado.

A V6 **não** envia mensagens, não cobra pagamentos e **não** abre reservas públicas.

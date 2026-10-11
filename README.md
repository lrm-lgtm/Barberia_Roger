# Roger Barbearia · App oficial

Projeto oficial de agendamento e gestão de barbearia. Repositório inicializado com a primeira versão executável do **fluxo de cliente mobile-first**: carrossel horizontal de serviços, seleção opcional de profissional, datas, horários e confirmação pela API local.

> **Status: v0.1 / piloto local. Não publicar para clientes ainda.** Serviço, preços, equipe e horários do seed são fictícios. A demonstração pública mostra horários simulados e percorre a jornada sem coletar dados pessoais ou gerar reservas. WhatsApp, pagamento e painel administrativo ainda não foram implementados.

## Testar no navegador

**Testar V4 no celular (sem backend):** https://raw.githack.com/lrm-lgtm/Barberia_Roger/main/docs/index.html

O workflow `publish-preview.yml` compila o mesmo frontend React em modo `VITE_DEMO_MODE=true` e salva os arquivos em `docs/`; assim o link de teste não usa uma interface paralela. Esse link usa um serviço externo de pré-visualização de HTML; no primeiro acesso pode aparecer uma tela de confirmação do serviço. A V4 oferece horários fictícios e simulação de conclusão sem perguntar nome/telefone, sem criar reservas, enviar WhatsApp ou processar pagamentos.

**Endereço oficial após habilitar GitHub Pages:** `https://lrm-lgtm.github.io/Barberia_Roger/`.

Para habilitar: `Settings > Pages > Build and deployment > Deploy from a branch > main > /docs > Save`. O GitHub publicará o conteúdo de `docs/index.html`.

## Tecnologias

- `frontend/`: React 19, TypeScript, Vite, CSS responsivo.
- `backend/`: FastAPI, SQLAlchemy, SQLite em desenvolvimento; preparado para PostgreSQL por `DATABASE_URL`.
- `docs/PLANO.md`: roteiro de implementação e critérios de aceite.
- `.github/workflows/ci.yml`: compilação do frontend e testes do backend.

## Como rodar localmente

**Terminal 1 — API** (Python 3.11+):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements-dev.txt
cp .env.example .env    # Windows: copy .env.example .env
# Carregue as variáveis .env pelo seu shell. Exemplo Linux/macOS:
set -a; source .env; set +a
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend** (Node 22+):

```bash
cd frontend
npm install --no-audit --no-fund
npm run dev
```

Abra `http://localhost:5173`. A API local estará em `http://localhost:8000/docs`. Para testar a confirmação de reservas, a API deve iniciar com `SEED_DEMO_DATA=true` e `BOOKING_ENABLED=true` **somente em ambiente local**.

## Testes

```bash
cd backend && pytest -q
cd ../frontend && npm run build
```

## Segurança e limites atuais

- API usa `BOOKING_ENABLED=false` como padrão seguro. Habilitar apenas para o piloto local.
- **Não há verificação de telefone, rate limiting, gestão autenticada nem administração de equipe.** Antes da exposição pública, implementar essas medidas e migrações do banco.
- Exibição de reserva pública não inclui nome/telefone na resposta; armazenamento pessoal existe e exige LGPD, política de retenção e operação segura.
- Horários demonstrativos são iguais para todos os barbeiros (seg-sáb 09–18h, almoço 12–13h). Escalas reais são fase posterior.
- Mensagens WhatsApp e pagamentos **não** são enviados.

Leia [o plano completo](docs/PLANO.md) e [o plano da experiência V4](docs/PLANO_UX_V4.md) para o backlog e decisões pendentes.

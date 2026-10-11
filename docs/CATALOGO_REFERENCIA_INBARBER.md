# Roger Barbearia — catálogo de referência do InBarber

Transcrição de capturas enviadas pelo usuário. Valores e durações extraídos dos prints (outubro/2026); **não validados para produção**. Alguns serviços anteriores não aparecem nas capturas.

| Serviço | Preço no print | Duração | Print | Confirmar? |
|---|---:|---:|---|---|
| Combo Prata — Cabelo + barba + sobrancelha | R$ 80,00 | 30 min | 1001684898.jpg | Não aparente |
| Combo Ouro — Cabelo + barba + nariz + orelha + sobrancelha (a confirmar) | R$ 100,00 | 30 min | 1001684902.jpg | Sim |
| Corte feminino | R$ 60,00 | 30 min | 1001684908.jpg | Não aparente |
| Corte & totalização — Nome a confirmar | R$ 75,00 | 30 min | 1001684910.jpg | Sim |
| Raspagem de cabelo na navalha | R$ 40,00 | 30 min | 1001684902.jpg | Sim |
| Pezinho | R$ 10,00 | 10 min | 1001684904.jpg | Não aparente |
| Cabelo & alisamento | R$ 70,00 | 30 min | 1001684900.jpg | Não aparente |
| Progressiva | R$ 60,00 | 40 min | 1001684910.jpg | Não aparente |
| Botox — Tratamento capilar | R$ 70,00 | 60 min | 1001684904.jpg | Não aparente |
| Luzes na touca | R$ 100,00 | 60 min | 1001684906.jpg | Não aparente |
| Platinado | R$ 120,00 | 60 min | 1001684906.jpg | Não aparente |
| Manutenção de prótese capilar | R$ 130,00 | 90 min | 1001684912.jpg | Não aparente |
| Sobrancelha | R$ 10,00 | 10 min | 1001684908.jpg | Não aparente |
| Sobrancelha (cera quente) — Grafia a confirmar | R$ 40,00 | 15 min | 1001684912.jpg | Sim |
| Remoção de pelo do nariz | R$ 15,00 | 10 min | 1001684898.jpg | Não aparente |
| Remoção de pelo da orelha | R$ 15,00 | 10 min | 1001684900.jpg | Não aparente |

## Pendências

- Parte inicial do catálogo não foi mostrada: não inventar serviços, preços nem profissionais.
- Combo Ouro: texto dos componentes sobrepõe o próximo cartão; revisar redação.
- Corte & totalização: confirmar nome. Raspagem na navalha e Sobrancelha (cera quente): conferir normalização de nomes.
- Fotos originais e consentimento para uso público são necessários; não copiar recortes de screenshots com rostos.
- Equipe e expediente semanal não aparecem. As vagas de 10 e 13/10/2026 são pontuais; não equivalem a escala, disponibilidade atual nem autorização para lançar reservas.
- Esta versão altera apenas dados da prévia React; não altera backend, banco de produção, mensagens ou reservas.
- Antes da produção confirmar serviço ativo, nomes, preços, duração, profissionais habilitados, intervalos e imagens.


## Complemento das capturas de 11/10/2026

Foram identificados **7 serviços avulsos** (somados aos 16 anteriores, total 23) e **3 planos mensais**, que não são agendamentos avulsos.

| Serviço | Preço mostrado | Duração | Captura |
|---|---:|---:|---|
| Corte de cabelo simples | R$ 40,00 | 30 min | 1001684888.jpg |
| Corte Degrade | R$ 40,00 | 30 min | 1001684888.jpg |
| Barba | R$ 40,00 | 30 min | 1001684890.jpg |
| Corte & Barba (Combo Bronze) | R$ 70,00 | 30 min | 1001684890.jpg |
| Cabelo & sobrancelha | R$ 50,00 | 30 min | 1001684892.jpg |
| Corte social na tesoura | R$ 40,00 | 30 min | 1001684892.jpg |
| "RAPAGEM UM PENTE SIMPLES" | R$ 30,00 | 30 min | 1001684894.jpg |

**Nome a confirmar:** "RAPAGEM UM PENTE SIMPLES" parece ser uma grafia com erro ou trecho truncado. A prévia normaliza para "Raspagem um pente simples". Confirmar o nome oficial.

### Planos separados

| Plano | Preço | Benefícios na imagem | Validade | Captura |
|---|---:|---|---|---|
| mensal(barba) | R$ 99,90 | 4 modelagens de barba | 30 dias | 1001684894.jpg |
| Plano Mensal (Corte de cabelo) | R$ 110,00 | 4 cortes | 30 dias | 1001684896.jpg |
| Plano mensal (Premium) | R$ 199,90 | 4 cortes + 4 barbas | 30 dias | 1001684896.jpg |

O InBarber apresenta "30min" nos cartões dos planos: isso **não** significa que o pacote dure 30 minutos ou que os atendimentos possam ser reservados em um único slot. Regras de adesão, pagamento, validade, consumo, cancelamento e renovação dependem da barbearia.

### Implementação segura na prévia

- Arquivo frontend/src/demo.ts: 23 serviços avulsos e 3 planos informativos.
- Arquivo frontend/src/App.tsx: planos em carrossel independente com modal de detalhes; não podem gerar reserva nem cobrança.
- Arquivo frontend/src/v6.css: barra de progresso para carrossel com catálogo maior.
- Fotografias dos prints não foram importadas: solicitar originais e autorização para uso público.
- A API V6 e os dados reais não foram alterados. Profissionais, escalas e horários da prévia ainda não são reais.

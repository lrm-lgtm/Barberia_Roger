import type { Catalog } from './types';

// Catálogo de REFERÊNCIA observado em capturas InBarber de outubro/2026.
// Não é cadastro validado; somente prévia React. NÃO usar como seed de produção.
// Fotos originais e equipe não foram fornecidas. Horários continuam fictícios.
// Preços/duração de 23 serviços transcritos dos prints, ainda não confirmados para uso real.
export const demoCatalog: Catalog = {
  services: [
    { id: 'corte-simples', name: 'Corte de cabelo simples', description: '', price_cents: 4000, duration_minutes: 30, image_url: null },
    { id: 'corte-degrade', name: 'Corte degradê', description: '', price_cents: 4000, duration_minutes: 30, image_url: null },
    { id: 'combo-bronze', name: 'Corte & barba', description: 'Combo Bronze', price_cents: 7000, duration_minutes: 30, image_url: null },
    { id: 'barba', name: 'Barba', description: '', price_cents: 4000, duration_minutes: 30, image_url: null },
    { id: 'social-tesoura', name: 'Corte social na tesoura', description: '', price_cents: 4000, duration_minutes: 30, image_url: null },
    { id: 'cabelo-sobrancelha', name: 'Cabelo & sobrancelha', description: '', price_cents: 5000, duration_minutes: 30, image_url: null },
    { id: 'raspagem-pente', name: 'Raspagem um pente simples', description: 'No InBarber: RAPAGEM UM PENTE SIMPLES (grafia a confirmar)', price_cents: 3000, duration_minutes: 30, image_url: null },
    { id: "combo-prata", name: "Combo Prata", description: "Cabelo + barba + sobrancelha", price_cents: 8000, duration_minutes: 30, image_url: null },
    { id: "combo-ouro", name: "Combo Ouro", description: "Cabelo + barba + nariz + orelha + sobrancelha (a confirmar)", price_cents: 10000, duration_minutes: 30, image_url: null },
    { id: "corte-feminino", name: "Corte feminino", description: "", price_cents: 6000, duration_minutes: 30, image_url: null },
    { id: "corte-totalizacao", name: "Corte & totalização", description: "Nome a confirmar", price_cents: 7500, duration_minutes: 30, image_url: null },
    { id: "raspagem-navalha", name: "Raspagem de cabelo na navalha", description: "", price_cents: 4000, duration_minutes: 30, image_url: null },
    { id: "pezinho", name: "Pezinho", description: "", price_cents: 1000, duration_minutes: 10, image_url: null },
    { id: "alisamento-cabelo", name: "Cabelo & alisamento", description: "", price_cents: 7000, duration_minutes: 30, image_url: null },
    { id: "progressiva", name: "Progressiva", description: "", price_cents: 6000, duration_minutes: 40, image_url: null },
    { id: "botox", name: "Botox", description: "Tratamento capilar", price_cents: 7000, duration_minutes: 60, image_url: null },
    { id: "luzes-touca", name: "Luzes na touca", description: "", price_cents: 10000, duration_minutes: 60, image_url: null },
    { id: "platinado", name: "Platinado", description: "", price_cents: 12000, duration_minutes: 60, image_url: null },
    { id: "manutencao-protese", name: "Manutenção de prótese capilar", description: "", price_cents: 13000, duration_minutes: 90, image_url: null },
    { id: "sobrancelha", name: "Sobrancelha", description: "", price_cents: 1000, duration_minutes: 10, image_url: null },
    { id: "sobrancelha-cera", name: "Sobrancelha (cera quente)", description: "Grafia a confirmar", price_cents: 4000, duration_minutes: 15, image_url: null },
    { id: "remocao-nariz", name: "Remoção de pelo do nariz", description: "", price_cents: 1500, duration_minutes: 10, image_url: null },
    { id: "remocao-orelha", name: "Remoção de pelo da orelha", description: "", price_cents: 1500, duration_minutes: 10, image_url: null },
  ],
  barbers: [],
};

/** Planos comerciais separados das reservas avulsas.
 * Os prints indicam 30 min no cartão: trata-se da duração exibida no agendador,
 * não da duração total do contrato/plano. Não associar pacote a um slot único.
 */
export type DemoPlan = {
  id: string; name: string; price_cents: number;
  validity_days: number; benefits: string; note: string;
};
export const demoPlans: DemoPlan[] = [
  { id: 'plano-barba', name: 'Plano mensal · Barba', price_cents: 9990, validity_days: 30,
    benefits: '4 modelagens de barba', note: 'Exibido no InBarber como mensal(barba)' },
  { id: 'plano-corte', name: 'Plano mensal · Corte', price_cents: 11000, validity_days: 30,
    benefits: '4 cortes', note: 'Exibido no InBarber como Plano Mensal (Corte de cabelo)' },
  { id: 'plano-premium', name: 'Plano mensal · Premium', price_cents: 19990, validity_days: 30,
    benefits: '4 cortes + 4 barbas', note: 'Exibido no InBarber como Plano mensal (Premium)' },
];

import type { Catalog } from './types';

// Catálogo de REFERÊNCIA observado em capturas InBarber de outubro/2026.
// Não é cadastro validado; somente prévia React. NÃO usar como seed de produção.
// Fotos originais e equipe não foram fornecidas. Horários continuam fictícios.
export const demoCatalog: Catalog = {
  services: [
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

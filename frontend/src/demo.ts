import type { Catalog } from './types';

// Only for visual preview when no API is connected; never creates a reservation.
export const demoCatalog: Catalog = {
  services: [
    { id: 'corte', name: 'Corte clássico', description: 'Seu estilo, no capricho.', price_cents: 4500, duration_minutes: 45, image_url: null },
    { id: 'degrade', name: 'Degradê', description: 'Precisão em cada detalhe.', price_cents: 5500, duration_minutes: 50, image_url: null },
    { id: 'combo', name: 'Corte + barba', description: 'Experiência completa.', price_cents: 7500, duration_minutes: 75, image_url: null },
    { id: 'barba', name: 'Barba', description: 'Alinhamento e acabamento.', price_cents: 3000, duration_minutes: 30, image_url: null },
  ],
  barbers: [
    { id: 'roger', name: 'Roger', service_ids: ['corte','degrade','combo','barba'] },
    { id: 'bruno', name: 'Bruno', service_ids: ['corte','degrade','combo','barba'] },
    { id: 'rafael', name: 'Rafael', service_ids: ['corte','combo','barba'] },
  ],
};

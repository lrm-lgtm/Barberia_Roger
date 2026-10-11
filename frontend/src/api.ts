import type { Availability, Booking, Catalog, DaysResponse } from './types';

async function jsonRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const json: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (json as { detail?: string }).detail;
    throw new Error(detail ?? 'Não foi possível completar sua solicitação.');
  }
  return json as T;
}

export const api = {
  catalog: () => jsonRequest<Catalog>('/api/catalog'),
  availability: (serviceId: string, date: string, barberId: string) => {
    const params = new URLSearchParams({ service_id: serviceId, date });
    if (barberId !== 'any') params.set('barber_id', barberId);
    return jsonRequest<Availability>(`/api/availability?${params}`);
  },
  days: (serviceId: string, start: string, barberId: string, count: number, signal?: AbortSignal) => {
    const params = new URLSearchParams({ service_id: serviceId, start, count: String(count) });
    if (barberId !== 'any') params.set('barber_id', barberId);
    return jsonRequest<DaysResponse>(`/api/availability/days?${params}`, { signal });
  },
  book: (values: {
    service_id: string;
    barber_id?: string;
    date: string;
    time: string;
    client_name: string;
    client_phone: string;
    marketing_opt_in: boolean;
  }) => jsonRequest<Booking>('/api/bookings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(values),
  }),
};

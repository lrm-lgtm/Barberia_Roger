export type Service = { id: string; name: string; description: string; price_cents: number; duration_minutes: number; image_url: string | null };
export type Barber = { id: string; name: string; service_ids: string[] };
export type Catalog = { services: Service[]; barbers: Barber[] };
export type Slot = { time: string; barber_id: string };
export type Availability = { date: string; slots: Slot[] };
export type DayAvailability = { date: string; available: boolean };
export type DaysResponse = { days: DayAvailability[] };
export type Booking = { id: string; service_id: string; barber_id: string; date: string; time: string; status: string };

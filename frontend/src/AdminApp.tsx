import { useEffect, useMemo, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { BarChart3, CalendarDays, Check, ChevronRight, LogOut, Search, Users, Wallet, X } from 'lucide-react';
import './admin.css';

type Booking = { id: string; barber_name: string; service_name: string; price_cents: number; client_name: string; client_phone: string; date: string; time: string; status: string };
type Customer = { phone: string; name: string; visits: number; spent_cents: number; last_visit: string | null };
type Dashboard = { metrics: { appointments: number; completed: number; cancelled: number; customers: number; revenue_cents: number }; ranking: Customer[]; bookings: Booking[] };
const brl = (cents: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(new Date());
const monthStart = () => `${today().slice(0, 8)}01`;
const horizon = () => { const value = new Date(`${today()}T12:00:00Z`); value.setUTCDate(value.getUTCDate() + 60); return value.toISOString().slice(0, 10); };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const key = sessionStorage.getItem('roger_admin_key') ?? '';
  const response = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}`, ...(init.headers ?? {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? 'Não foi possível concluir a operação.');
  return data as T;
}

export default function AdminApp() {
  const [key, setKey] = useState(sessionStorage.getItem('roger_admin_key') ?? '');
  const [authenticated, setAuthenticated] = useState(Boolean(sessionStorage.getItem('roger_admin_key')));
  const [start, setStart] = useState(monthStart());
  const [end, setEnd] = useState(horizon());
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'overview' | 'customers'>('overview');

  async function load() {
    setError('');
    try {
      const [summary, people] = await Promise.all([
        request<Dashboard>(`/api/admin/dashboard?start=${start}&end=${end}`),
        request<{ customers: Customer[] }>(`/api/admin/customers?q=${encodeURIComponent(query)}`),
      ]);
      setDashboard(summary); setCustomers(people.customers);
    } catch (err) { setError(err instanceof Error ? err.message : 'Falha ao carregar painel.'); }
  }
  useEffect(() => { if (authenticated) void load(); }, [authenticated, start, end]);

  function login(event: FormEvent) {
    event.preventDefault(); sessionStorage.setItem('roger_admin_key', key.trim()); setAuthenticated(true);
  }
  function logout() { sessionStorage.removeItem('roger_admin_key'); setAuthenticated(false); setDashboard(null); }
  async function updateStatus(id: string, status: string) {
    try { await request(`/api/admin/bookings/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Falha ao atualizar agendamento.'); }
  }

  if (!authenticated) return <main className="admin-login"><div className="admin-login-card"><div className="admin-logo">R</div><span className="admin-kicker">ROGER BARBEARIA</span><h1>Painel interno</h1><p>Acesso exclusivo para a equipe.</p><form onSubmit={login}><label>Chave administrativa<input type="password" value={key} onChange={e => setKey(e.target.value)} required minLength={32} placeholder="Cole a ADMIN_API_KEY" /></label><button>Entrar <ChevronRight size={17}/></button></form><small>A chave não é enviada nem salva no navegador além desta sessão.</small></div></main>;

  const metrics = dashboard?.metrics;
  const filteredCustomers = useMemo(() => customers.filter(c => !query || `${c.name} ${c.phone}`.toLowerCase().includes(query.toLowerCase())), [customers, query]);
  return <main className="admin-shell"><header className="admin-header"><div><span className="admin-kicker">ROGER BARBEARIA</span><h1>Painel interno</h1></div><button className="ghost-button" onClick={logout}><LogOut size={16}/> Sair</button></header><nav className="admin-nav"><button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}><BarChart3 size={16}/> Visão geral</button><button className={tab === 'customers' ? 'active' : ''} onClick={() => setTab('customers')}><Users size={16}/> Clientes</button></nav>{error && <div className="admin-error"><X size={16}/>{error}<button onClick={() => setError('')}>Fechar</button></div>}<section className="admin-filters"><label>De<input type="date" value={start} onChange={e => setStart(e.target.value)}/></label><label>Até<input type="date" value={end} onChange={e => setEnd(e.target.value)}/></label><button onClick={() => void load()}>Atualizar</button></section>{tab === 'overview' && <><section className="metric-grid"><Metric icon={<CalendarDays/>} label="Agendamentos" value={metrics?.appointments ?? 0}/><Metric icon={<Check/>} label="Concluídos" value={metrics?.completed ?? 0}/><Metric icon={<Wallet/>} label="Faturamento" value={brl(metrics?.revenue_cents ?? 0)}/><Metric icon={<Users/>} label="Clientes" value={metrics?.customers ?? 0}/></section><div className="admin-columns"><section className="admin-card"><div className="card-title"><div><span>AGENDA DO PERÍODO</span><h2>Agendamentos</h2></div></div><div className="booking-list">{(dashboard?.bookings ?? []).map(b => <article className="booking-row" key={b.id}><div><strong>{b.time} · {b.client_name}</strong><span>{b.date} · {b.service_name} · {b.barber_name}</span><small>{b.client_phone} · {brl(b.price_cents)}</small></div><select value={b.status} onChange={e => void updateStatus(b.id, e.target.value)}><option value="confirmed">Confirmado</option><option value="completed">Concluído</option><option value="cancelled">Cancelado</option><option value="no_show">Não compareceu</option></select></article>)}{!dashboard?.bookings.length && <p className="empty">Nenhum agendamento no período.</p>}</div></section><section className="admin-card"><div className="card-title"><div><span>FIDELIDADE</span><h2>Ranking de clientes</h2></div></div><div className="ranking-list">{(dashboard?.ranking ?? []).map((c, i) => <div className="ranking-row" key={c.phone}><b>{i + 1}</b><div><strong>{c.name}</strong><span>{c.visits} atendimento(s) · {c.phone}</span></div><em>{brl(c.spent_cents)}</em></div>)}{!dashboard?.ranking.length && <p className="empty">Ainda não há dados.</p>}</div></section></div></>}{tab === 'customers' && <section className="admin-card customers-card"><div className="card-title"><div><span>BASE INTERNA</span><h2>Clientes</h2></div><div className="search-box"><Search size={16}/><input placeholder="Nome ou celular" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && void load()}/></div></div><div className="customer-table"><div className="table-head"><span>Cliente</span><span>Celular</span><span>Visitas</span><span>Total</span><span>Última visita</span></div>{filteredCustomers.map(c => <div className="table-row" key={c.phone}><strong>{c.name}</strong><span>{c.phone}</span><span>{c.visits}</span><span>{brl(c.spent_cents)}</span><span>{c.last_visit ?? '—'}</span></div>)}{!filteredCustomers.length && <p className="empty">Nenhum cliente encontrado.</p>}</div></section>}<footer className="admin-footer">Dados internos da barbearia · acesso restrito à equipe</footer></main>;
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) { return <div className="metric"><span>{icon}</span><small>{label}</small><strong>{value}</strong></div>; }

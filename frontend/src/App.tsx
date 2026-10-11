import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, Check, ChevronLeft, ChevronRight, Clock3, MapPin, Scissors, ShieldCheck, UserRound, Users, X } from 'lucide-react';
import { api } from './api';
import { demoCatalog, demoPlans } from './demo';
import type { Availability, Booking, Catalog, DayAvailability } from './types';
import './v4.css';
import './v5.css';
import './v6.css';

type Step = 'services' | 'schedule' | 'identify' | 'success';
const brl = (cents: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
const dateFmt = (day: string, options: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat('pt-BR', { ...options, timeZone: 'UTC' }).format(new Date(`${day}T12:00:00Z`));
const pad = (n: number) => `${n}`.padStart(2, '0');
const todayInBrazil = () => {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
  const get = (type: string) => parts.find(p => p.type === type)?.value ?? '';
  return `${get('year')}-${get('month')}-${get('day')}`;
};
const addDays = (iso: string, n: number) => {
  const d = new Date(`${iso}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};
const sunday = (iso: string) => new Date(`${iso}T12:00:00Z`).getUTCDay() === 0;
const serviceGraphic = ['scissors', 'sparkle', 'combo', 'razor'];
const demoTimes = ['09:00', '09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30', '15:00', '16:00', '16:30', '17:00'];
const futureDemoSlots = (day: string) => {
  if (sunday(day)) return [];
  const today = todayInBrazil();
  if (day < today) return [];
  const current = new Intl.DateTimeFormat('en-GB', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date());
  return demoTimes.filter(time => day !== today || time > current);
};

export default function App() {
  const [catalog, setCatalog] = useState<Catalog>(demoCatalog);
  const [isPreview, setIsPreview] = useState(true);
  const [step, setStep] = useState<Step>('services');
  const [serviceId, setServiceId] = useState<string | null>(null);
  const [barberId, setBarberId] = useState('any');
  const [date, setDate] = useState(() => todayInBrazil());
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [daysSummary, setDaysSummary] = useState<DayAvailability[]>([]);
  const [loadingDays, setLoadingDays] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fullCalendar, setFullCalendar] = useState(false);
  const [showBarbers, setShowBarbers] = useState(false);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');
  const [marketingOptIn, setMarketingOptIn] = useState(false);
  const [booking, setBooking] = useState<Booking | null>(null);
  const dayRailRef = useRef<HTMLDivElement>(null);
  const servicesRailRef = useRef<HTMLDivElement>(null);
  const [serviceIndex, setServiceIndex] = useState(0);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [calendarMonth, setCalendarMonth] = useState(() => todayInBrazil().slice(0, 7));

  useEffect(() => {
    // The published preview is intentionally disconnected from the API.
    if (import.meta.env.VITE_DEMO_MODE === 'true') return;
    api.catalog().then(data => { setCatalog(data); setIsPreview(false); }).catch(() => setIsPreview(true));
  }, []);

  const service = catalog.services.find(x => x.id === serviceId);
  const selectedPlan = demoPlans.find(plan => plan.id === selectedPlanId);
  const eligible = catalog.barbers.filter(b => !serviceId || b.service_ids.includes(serviceId));
  const professional = catalog.barbers.find(b => b.id === (booking?.barber_id ?? barberId));
  const dateItems = useMemo(() => Array.from({ length: 30 }, (_, i) => addDays(todayInBrazil(), i)), []);
  const dayAvailability = useMemo(() => new Map(daysSummary.map(item => [item.date, item.available])), [daysSummary]);
  const initialMonth = dateItems[0].slice(0, 7);
  const lastMonth = dateItems[dateItems.length - 1].slice(0, 7);
  const shiftMonth = (month: string, delta: number) => {
    const [year, monthIndex] = month.split('-').map(Number);
    return new Date(Date.UTC(year, monthIndex - 1 + delta, 1)).toISOString().slice(0, 7);
  };
  const calendarDates = useMemo(() => {
    const [year, month] = calendarMonth.split('-').map(Number);
    const start = (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7;
    const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
    return [...Array.from({ length: start }, () => ''), ...Array.from({ length: days }, (_, i) => `${calendarMonth}-${pad(i + 1)}`)];
  }, [calendarMonth]);

  useEffect(() => {
    if (step !== 'schedule' || !serviceId) return;
    if (isPreview) {
      const summary = dateItems.map(day => ({ date: day, available: futureDemoSlots(day).length > 0 }));
      setDaysSummary(summary);
      // Keep the client's date when navigating back; otherwise select the next date with vacancies.
      if (!summary.find(x => x.date === date && x.available)) {
        setDate(summary.find(x => x.available)?.date ?? date);
      }
      return;
    }
    const controller = new AbortController();
    setLoadingDays(true);
    api.days(serviceId, dateItems[0], barberId, 30, controller.signal)
      .then(result => {
        if (controller.signal.aborted) return;
        setDaysSummary(result.days);
        setDate(previous => result.days.some(d => d.date === previous && d.available)
          ? previous : (result.days.find(d => d.available)?.date ?? previous));
      })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Erro ao consultar dias disponíveis.'); })
      .finally(() => { if (!controller.signal.aborted) setLoadingDays(false); });
    return () => controller.abort();
  }, [barberId, serviceId, isPreview, step, dateItems]);

  useEffect(() => {
    if (step !== 'schedule' || !serviceId) return;
    if (isPreview) {
      setAvailability({ date, slots: futureDemoSlots(date).map(time => ({ time, barber_id: barberId === 'any' ? 'preview' : barberId })) });
      setLoadingSlots(false);
      return;
    }
    let active = true;
    setAvailability(null);
    setLoadingSlots(true);
    setError(null);
    api.availability(serviceId, date, barberId)
      .then(data => { if (active) setAvailability(data); })
      .catch(err => { if (active) setError(err instanceof Error ? err.message : 'Erro ao consultar horários.'); })
      .finally(() => { if (active) setLoadingSlots(false); });
    return () => { active = false; };
  }, [serviceId, date, barberId, step, isPreview]);

  useEffect(() => {
    if (step !== 'schedule') return;
    const rail = dayRailRef.current;
    const target = rail?.querySelector<HTMLButtonElement>('[aria-pressed="true"]');
    if (!rail || !target) return;
    rail.scrollTo({ left: Math.max(0, target.offsetLeft - rail.offsetLeft - (rail.clientWidth - target.clientWidth) / 2), behavior: 'smooth' });
  }, [date, step, daysSummary]);

  function selectService(id: string) {
    setServiceId(id); setBarberId('any'); setSelectedTime(null); setDaysSummary([]);
    setShowMore(false); setStep('schedule'); setError(null);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function changeDay(day: string) {
    if (!day) return;
    if (dayAvailability.get(day) === false || day < dateItems[0] || day > dateItems[dateItems.length - 1]) return;
    setDate(day); setSelectedTime(null); setAvailability(null); setLoadingSlots(true); setShowMore(false); setError(null);
    setFullCalendar(false);
  }
  function changeBarber(id: string) {
    setBarberId(id); setSelectedTime(null); setAvailability(null); setLoadingSlots(true); setShowMore(false); setShowBarbers(false); setError(null);
  }
  function back() { setStep(step === 'identify' ? 'schedule' : 'services'); setError(null); window.scrollTo({top: 0, behavior: 'instant'}); }
  function pickTime(time: string) {
    if (loadingSlots || loadingDays || !slots.some(slot => slot.time === time)) return;
    setSelectedTime(time); setError(null); setStep('identify');
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  async function submitBooking(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!service || !selectedTime || isPreview) return;
    setSubmitting(true); setError(null);
    try {
      const result = await api.book({
        service_id: service.id,
        ...(barberId !== 'any' ? { barber_id: barberId } : {}),
        date, time: selectedTime, client_name: clientName.trim(),
        client_phone: clientPhone.replace(/\D/g, ''), marketing_opt_in: marketingOptIn,
      });
      setBooking(result); setStep('success'); window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao agendar.');
      setStep('schedule'); setSelectedTime(null);
    } finally { setSubmitting(false); }
  }
  const slots = availability?.slots ?? [];
  const visibleSlots = showMore ? slots : slots.slice(0, 9);

  return <div className="app-shell v4 v5">
    <div className="app-width">
      <header className="site-header">
        <div className="brand-icon"><Scissors size={24} strokeWidth={1.6} /></div>
        <div className="brand-text"><strong>ROGER</strong><span>BARBEARIA</span></div>
        <div className="header-status"><span className="pulse" /> {isPreview ? 'Prévia' : 'Agenda online'}</div>
      </header>

      {step === 'services' && <>
        <section className="v5-intro">
          <span className="eyebrow"><span className="v5-signal"/> AGENDAMENTO ONLINE</span>
          <h1>Qual vai ser <em>o corte?</em></h1>
          <p>Deslize, escolha seu serviço e encontre um horário.</p>
        </section>
        <div className="v5-carousel-title"><strong>Serviços</strong><span>DESLIZE <ArrowRight size={14}/></span></div>
        <div className="service-carousel" ref={servicesRailRef} onScroll={event => {
          const target = event.currentTarget;
          const first = target.querySelector<HTMLElement>('.service-card');
          if (!first) return;
          const width = first.offsetWidth + 14;
          setServiceIndex(Math.max(0, Math.min(catalog.services.length - 1, Math.round(target.scrollLeft / width))));
        }} aria-label="Serviços disponíveis. Deslize horizontalmente.">
          {catalog.services.map((s, i) => <button type="button" className={`service-card service-art-${i % 4}`} key={s.id} onClick={() => selectService(s.id)} aria-label={`${s.name}, ${s.duration_minutes} minutos, ${brl(s.price_cents)}. Escolher horário.`}>
            <div className="service-photo">{s.image_url ? <img src={s.image_url} alt="" loading="lazy"/> : <div className={`graphic graphic-${serviceGraphic[i % 4]}`}><Scissors size={58} strokeWidth={0.9}/><span>{pad(i + 1)}</span></div>}
              <span className="service-number">{pad(i + 1)}</span><span className="service-float"><ArrowRight size={19}/></span>
            </div>
            <div className="service-info"><h3>{s.name}</h3><div><span><Clock3 size={13}/> {s.duration_minutes} min</span><strong>{brl(s.price_cents)}</strong></div></div>
          </button>)}
        </div>
        <div className="v5-carousel-footer"><div className="v5-progress" aria-hidden="true"><span style={{ width: `${catalog.services.length ? (serviceIndex + 1) / catalog.services.length * 100 : 0}%` }} /></div><span>{serviceIndex + 1} de {catalog.services.length} · Toque para agendar</span></div>
        <div className="v5-benefit"><Check size={16}/> Sem instalar aplicativo <span>·</span> Escolha um horário em poucos toques</div>

        {isPreview && <section className="v6-plans" aria-label="Planos mensais da Roger Barbearia">
          <div className="v6-plans-title"><div><span>CLUBE ROGER</span><h2>Planos mensais</h2></div><span>Deslize <ArrowRight size={14}/></span></div>
          <div className="v6-plans-rail">
            {demoPlans.map(plan => <button key={plan.id} type="button" className="v6-plan-card" onClick={() => setSelectedPlanId(plan.id)} aria-label={plan.name + ', ' + brl(plan.price_cents) + ' por 30 dias. Ver detalhes.'}>
              <small>30 DIAS</small>
              <strong>{plan.name.replace('Plano mensal · ', '')}</strong>
              <span className="v6-plan-benefits">{plan.benefits}</span>
              <span className="v6-plan-price">{brl(plan.price_cents)}<ArrowRight size={17}/></span>
            </button>)}
          </div>
          <p>Planos informativos: contratação, regras e disponibilidade ainda serão configuradas.</p>
        </section>}
        {isPreview && <p className="v5-demo-footnote">Preços e durações transcritos de capturas do InBarber (out/2026), sujeitos a confirmação. Imagens, horários e equipe ainda não são oficiais.</p>}
      </>}

      {step === 'schedule' && service && <div className="v4-schedule">
        <div className="v4-nav"><button onClick={back} aria-label="Voltar para serviços" type="button"><ArrowLeft size={20}/></button><span>AGENDAMENTO</span></div>
        <h1>Escolha seu horário</h1>
        <div className="v4-service-summary"><span><strong>{service.name}</strong><small>{service.duration_minutes} min · {brl(service.price_cents)}</small></span><button type="button" onClick={back}>Trocar</button></div>
        <div className="v4-month"><strong>{dateFmt(date, { month: 'long', year: 'numeric' })}</strong><button type="button" onClick={() => { setCalendarMonth(date.slice(0, 7)); setFullCalendar(true); }} aria-label="Abrir calendário mensal"><CalendarDays size={18}/><span>Outras datas</span></button></div>
        <div ref={dayRailRef} className="v4-day-rail" aria-label="Escolha o dia. Deslize horizontalmente.">
          {dateItems.map(day => {
            const item = daysSummary.find(d => d.date === day);
            const unavailable = item ? !item.available : sunday(day);
            return <button key={day} type="button" aria-pressed={date === day} className={`v4-day ${date === day ? 'selected' : ''}`} disabled={loadingDays || unavailable} onClick={() => changeDay(day)}>
              <span>{dateFmt(day, { weekday: 'short' }).replace('.', '').toUpperCase()}</span>
              <strong>{dateFmt(day, { day: '2-digit' })}</strong>
              <small>{day === todayInBrazil() ? 'Hoje' : unavailable ? 'Sem vaga' : '•'}</small>
            </button>;
          })}
        </div>
        <div className="v4-times-heading"><div><strong>Horários disponíveis</strong><small>{dateFmt(date, { weekday: 'long', day: 'numeric', month: 'long' })}</small></div></div>
        {(loadingSlots || loadingDays) && <div className="v4-message" role="status">Buscando horários...</div>}
        {!loadingSlots && !loadingDays && slots.length === 0 && <div className="v4-message">Nenhum horário neste dia. Deslize para outra data.</div>}
        {!loadingSlots && !loadingDays && slots.length > 0 && <>
          <div className="v4-time-grid" aria-label="Horários disponíveis">
            {visibleSlots.map(slot => <button key={slot.time} type="button" onClick={() => pickTime(slot.time)} aria-label={`Agendar às ${slot.time}`}>
              {slot.time}<ArrowRight size={15}/>
            </button>)}
          </div>
          {slots.length > 9 && <button className="v4-more" type="button" onClick={() => setShowMore(!showMore)}>{showMore ? 'Ver menos' : `Ver mais ${slots.length - 9} horários`}</button>}
        </>}
        {error && <p className="error" role="alert">{error}</p>}
        {eligible.length > 0 && <button className="v4-professional" type="button" onClick={() => setShowBarbers(true)}>
          <span className="v4-person-icon"><Users size={19}/></span>
          <span><strong>{barberId === 'any' ? (eligible.length ? 'Qualquer barbeiro' : 'Profissionais a confirmar') : professional?.name}</strong><small>{barberId === 'any' ? 'Mais opções de horários' : 'Profissional escolhido'}</small></span>
          <span className="v4-change">Alterar <ArrowRight size={14}/></span>
        </button>}
        <p className="v4-hint">Toque no horário desejado para continuar.</p>
      </div>}

      {step === 'identify' && service && <>
        <CompactHeader onBack={back} title={isPreview ? 'Confira sua escolha' : 'Quase lá!'} />
        <div className="booking-summary"><span className="eyebrow">{isPreview ? 'SIMULAÇÃO DE AGENDAMENTO' : 'RESUMO DO AGENDAMENTO'}</span><h2>{service.name}</h2><div><Clock3 size={17}/> {dateFmt(date, { weekday: 'long', day: 'numeric', month: 'long' })} às {selectedTime}</div><div><UserRound size={17}/> {barberId === 'any' ? (eligible.length ? 'Primeiro profissional disponível' : 'Profissional não informado na prévia') : professional?.name}</div><strong>{brl(service.price_cents)} <small>pagar no local</small></strong></div>
        {isPreview ? <div className="v4-demo-review"><ShieldCheck size={25}/><strong>Esta é uma demonstração.</strong><p>Você pode experimentar a jornada sem informar nome ou telefone. Nenhum horário será reservado.</p><button type="button" className="confirm-button" onClick={() => setStep('success')}>Concluir simulação <ArrowRight size={18}/></button></div> :
          <form className="details-form" onSubmit={submitBooking}><label htmlFor="client-name">Seu nome</label><input id="client-name" required autoComplete="name" maxLength={80} minLength={2} placeholder="Nome e sobrenome" value={clientName} onChange={e => setClientName(e.target.value)}/><label htmlFor="client-phone">WhatsApp com DDD</label><input id="client-phone" required autoComplete="tel" inputMode="tel" pattern="[0-9() +\-]{10,20}" placeholder="(19) 99999-9999" value={clientPhone} onChange={e => setClientPhone(e.target.value)}/><div className="form-note"><ShieldCheck size={19}/> Usaremos seu celular para informações da reserva. A verificação de identidade será obrigatória antes da abertura pública.</div><label className="consent"><input type="checkbox" checked={marketingOptIn} onChange={e => setMarketingOptIn(e.target.checked)}/> Quero receber promoções e convites para voltar (opcional).</label>{error && <p className="error" role="alert">{error}</p>}<button className="confirm-button" disabled={submitting} type="submit">{submitting ? 'Confirmando...' : 'Confirmar agendamento'} <ArrowRight size={19}/></button></form>}
      </>}

      {step === 'success' && service && (isPreview || booking) && <div className="success-screen"><div className="success-check"><Check size={40}/></div><span className="eyebrow">{isPreview ? 'FIM DA DEMONSTRAÇÃO' : 'AGENDAMENTO CONFIRMADO'}</span><h1>{isPreview ? 'Tudo certo no teste!' : 'Te esperamos!'}</h1><p>{isPreview ? 'Essa foi só uma simulação. Nenhuma reserva foi feita e nenhum dado pessoal foi enviado.' : 'Seu horário foi reservado no sistema local de teste.'}</p><div className="booking-summary"><span className="eyebrow">{isPreview ? 'PRÉVIA' : `RESERVA ${booking?.id.slice(0, 8).toUpperCase()}`}</span><h2>{service.name}</h2><div><CalendarDays size={17}/>{dateFmt(date, { weekday: 'long', day: 'numeric', month: 'long' })} · {selectedTime}</div><div><UserRound size={17}/>{isPreview ? (barberId === 'any' ? 'Qualquer barbeiro' : professional?.name) : catalog.barbers.find(b => b.id === booking?.barber_id)?.name}</div><strong>{brl(service.price_cents)}</strong></div><button className="confirm-button" type="button" onClick={() => { setStep('services'); setServiceId(null); setSelectedTime(null); setBooking(null); }}>Testar outro serviço <ArrowRight size={18}/></button></div>}


      {isPreview && selectedPlan && <div className="calendar-overlay" onClick={() => setSelectedPlanId(null)}>
        <div className="calendar-sheet v6-plan-sheet" role="dialog" aria-modal="true" aria-label={'Detalhes do ' + selectedPlan.name} onClick={e => e.stopPropagation()}>
          <div className="sheet-head"><strong>Clube Roger</strong><button type="button" onClick={() => setSelectedPlanId(null)} aria-label="Fechar detalhes do plano"><X size={20}/></button></div>
          <span className="v6-plan-kicker">PLANO MENSAL · 30 DIAS</span>
          <h2>{selectedPlan.name.replace('Plano mensal · ', '')}</h2>
          <p className="v6-plan-modal-benefits">{selectedPlan.benefits}</p>
          <div className="v6-plan-modal-price">{brl(selectedPlan.price_cents)}<span> / plano</span></div>
          <p className="v6-plan-warning">Condições extraídas dos prints do InBarber, ainda não conferidas com a barbearia. Esta demonstração não permite contratar, pagar ou agendar serviços do plano.</p>
          <button type="button" className="v6-plan-close" onClick={() => setSelectedPlanId(null)}>Voltar aos serviços</button>
        </div>
      </div>}
      {fullCalendar && <div className="calendar-overlay" role="presentation" onClick={() => setFullCalendar(false)}>
        <div className="calendar-sheet v5-calendar-sheet" role="dialog" aria-modal="true" aria-label="Escolher data" onClick={e => e.stopPropagation()}>
          <div className="sheet-head"><strong>Escolha a data</strong><button onClick={() => setFullCalendar(false)} aria-label="Fechar calendário" type="button"><X size={19}/></button></div>
          <div className="v5-calendar-toolbar">
            <button type="button" aria-label="Mês anterior" disabled={calendarMonth <= initialMonth} onClick={() => setCalendarMonth(m => shiftMonth(m, -1))}><ChevronLeft size={19}/></button>
            <strong>{dateFmt(`${calendarMonth}-01`, { month: 'long', year: 'numeric' })}</strong>
            <button type="button" aria-label="Próximo mês" disabled={calendarMonth >= lastMonth} onClick={() => setCalendarMonth(m => shiftMonth(m, 1))}><ChevronRight size={19}/></button>
          </div>
          <div className="v5-calendar-grid" role="group" aria-label="Dias disponíveis">
            {['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'].map(d => <span key={d} className="v5-weekday">{d}</span>)}
            {calendarDates.map((day, i) => day ? <button type="button" key={day} disabled={!dateItems.includes(day) || dayAvailability.get(day) !== true} className={date === day ? 'selected' : ''} aria-pressed={date === day} onClick={() => changeDay(day)} aria-label={`${dateFmt(day,{weekday:'long',day:'numeric',month:'long'})}${dayAvailability.get(day) === false ? ', sem vaga' : ''}`}>{Number(day.slice(-2))}</button> : <span key={`empty-${i}`} />)}
          </div>
          <p className="v5-calendar-note">Dias apagados não têm vagas ou estão fora do período de agendamento.</p>
        </div>
      </div>}
      {showBarbers && <div className="calendar-overlay" role="dialog" aria-modal="true" aria-label="Escolher barbeiro" onClick={() => setShowBarbers(false)}><div className="calendar-sheet v4-barber-sheet" onClick={e => e.stopPropagation()}><div className="sheet-head"><strong>Com quem prefere cortar?</strong><button onClick={() => setShowBarbers(false)} aria-label="Fechar" type="button"><X size={19}/></button></div><div className="v4-barber-options"><button type="button" className={barberId === 'any' ? 'active' : ''} onClick={() => changeBarber('any')}><Users size={20}/> Primeiro disponível {barberId === 'any' && <Check size={17}/>}</button>{eligible.map(b => <button type="button" className={barberId === b.id ? 'active' : ''} key={b.id} onClick={() => changeBarber(b.id)}><UserRound size={20}/>{b.name}{barberId === b.id && <Check size={17}/>}</button>)}</div></div></div>}
      <footer className="site-footer"><span>ROGER BARBEARIA</span><span><MapPin size={13}/> Seu lugar, seu estilo.</span></footer>
    </div>
  </div>;
}

function CompactHeader({ onBack, title }: { onBack: () => void; title: string }) {
  return <div className="v4-compact-header"><button type="button" aria-label="Voltar" onClick={onBack}><ArrowLeft size={20}/></button><h1>{title}</h1></div>;
}

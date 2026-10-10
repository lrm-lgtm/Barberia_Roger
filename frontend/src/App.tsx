import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, Check, Clock3, MapPin, Scissors, ShieldCheck, UserRound, Users, X } from 'lucide-react';
import { api } from './api';
import { demoCatalog } from './demo';
import type { Availability, Booking, Catalog } from './types';

type Step = 'services' | 'schedule' | 'identify' | 'success';
const brl = (cents: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
const dateFmt = (day: string, options: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat('pt-BR', { ...options, timeZone: 'UTC' }).format(new Date(`${day}T12:00:00Z`));
const pad = (n: number) => `${n}`.padStart(2, '0');
const isoDay = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const daysAhead = (n: number) => { const d = new Date(); d.setDate(d.getDate() + n); return isoDay(d); };
const period = (time: string) => Number(time.slice(0, 2)) < 12 ? 'Manhã' : Number(time.slice(0, 2)) < 18 ? 'Tarde' : 'Noite';
const serviceGraphic = ['scissors', 'sparkle', 'combo', 'razor'];

export default function App() {
  const [catalog, setCatalog] = useState<Catalog>(demoCatalog);
  const [isPreview, setIsPreview] = useState(true);
  const [step, setStep] = useState<Step>('services');
  const [serviceId, setServiceId] = useState<string | null>(null);
  const [barberId, setBarberId] = useState('any');
  const [date, setDate] = useState(daysAhead(1));
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fullCalendar, setFullCalendar] = useState(false);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');
  const [marketingOptIn, setMarketingOptIn] = useState(false);
  const [booking, setBooking] = useState<Booking | null>(null);
  const calendarRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.catalog().then(data => { setCatalog(data); setIsPreview(false); }).catch(() => setIsPreview(true));
  }, []);

  const service = catalog.services.find(x => x.id === serviceId);
  const eligible = catalog.barbers.filter(b => !serviceId || b.service_ids.includes(serviceId));
  const professional = catalog.barbers.find(b => b.id === (booking?.barber_id ?? barberId));
  const dateItems = useMemo(() => Array.from({ length: 30 }, (_, i) => daysAhead(i)), []);

  useEffect(() => {
    if (step !== 'schedule' || !serviceId || isPreview) return;
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

  function selectService(id: string) {
    setServiceId(id); setBarberId('any'); setSelectedTime(null); setStep('schedule'); setError(null);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function changeDay(day: string) { setDate(day); setSelectedTime(null); setError(null); }
  function changeBarber(id: string) { setBarberId(id); setSelectedTime(null); setError(null); }
  function back() { setStep(step === 'identify' ? 'schedule' : 'services'); setError(null); }
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
  const groupSlots = (label: string) => availability?.slots.filter(x => period(x.time) === label) ?? [];

  return <div className="app-shell">
    <div className="app-width">
      <header className="site-header">
        <div className="brand-icon"><Scissors size={24} strokeWidth={1.6} /></div>
        <div className="brand-text"><strong>ROGER</strong><span>BARBEARIA</span></div>
        <div className="header-status"><span className="pulse" /> Agenda online</div>
      </header>
      {isPreview && <div className="demo-banner"><ShieldCheck size={15}/> Prévia visual: abra a API para consultar e confirmar horários reais de teste.</div>}

      {step === 'services' && <>
        <section className="hero">
          <div className="hero-glow" /><div className="hero-outline" />
          <div className="hero-kicker"><span /> SEU ESTILO. SEU MOMENTO.</div>
          <h1>Seu próximo corte<br /><em>começa aqui.</em></h1>
          <p>Escolha o serviço, encontre um horário e pronto. Simples assim.</p>
          <div className="hero-bottom"><span><Clock3 size={15}/> Leva menos de 1 minuto</span><ArrowRight size={20} /></div>
        </section>
        <section className="catalog-heading">
          <div><span className="eyebrow">AGENDAMENTO</span><h2>O que vamos fazer hoje?</h2><p>Deslize para escolher seu serviço.</p></div>
          <span className="swipe-hint">Deslize <ArrowRight size={15}/></span>
        </section>
        <div className="service-carousel" aria-label="Serviços disponíveis">
          {catalog.services.map((s, i) => <button type="button" className={`service-card service-art-${i % 4}`} key={s.id} onClick={() => selectService(s.id)}>
            <div className="service-photo">{s.image_url ? <img src={s.image_url} alt="" loading="lazy" /> : <div className={`graphic graphic-${serviceGraphic[i % 4]}`}><Scissors size={62} strokeWidth={0.8}/><span>{pad(i + 1)}</span></div>}
              <span className="service-number">0{i + 1}</span>
              <span className="service-float"><ArrowRight size={20} /></span>
            </div>
            <div className="service-info"><div><h3>{s.name}</h3><span><Clock3 size={13} /> {s.duration_minutes} min</span></div><strong>{brl(s.price_cents)}</strong></div>
          </button>)}
        </div>
        <div className="below-carousel"><span className="line" /> <span>Escolha um serviço para continuar</span> <span className="line" /></div>
        <div className="bottom-note"><ShieldCheck size={17} /> Agende sem instalar aplicativo. Preços e equipe acima são dados de demonstração até o cadastro oficial.</div>
      </>}

      {step === 'schedule' && service && <>
        <StepHeader step="02 / 03" onBack={back} title="Escolha seu horário" subtitle="Um horário bom para você, sem complicação." />
        <div className="selection-strip"><div className="selection-logo"><Scissors size={19}/></div><div><strong>{service.name}</strong><span>{service.duration_minutes} min · {brl(service.price_cents)}</span></div><button type="button" onClick={() => setStep('services')}>Trocar</button></div>
        <section className="choice-section"><div className="section-top"><div><span className="eyebrow">COM QUEM?</span><h2>Seu profissional</h2></div></div>
          <div className="barber-track" role="group" aria-label="Escolher barbeiro"><button className={`barber-pill ${barberId === 'any' ? 'active' : ''}`} onClick={() => changeBarber('any')} type="button"><span className="barber-avatar"><Users size={18}/></span><span>Primeiro disponível</span>{barberId === 'any' && <Check size={15}/>}</button>{eligible.map(b => <button key={b.id} type="button" onClick={() => changeBarber(b.id)} className={`barber-pill ${barberId === b.id ? 'active' : ''}`}><span className="barber-avatar">{b.name[0]}</span><span>{b.name}</span>{barberId === b.id && <Check size={15}/>}</button>)}</div>
        </section>
        <section className="choice-section"><div className="section-top"><div><span className="eyebrow">QUANDO?</span><h2>Escolha o dia</h2></div><button type="button" className="calendar-toggle" onClick={() => setFullCalendar(true)}><CalendarDays size={17} /> Calendário</button></div>
          <div className="calendar-track" aria-label="Datas disponíveis">{dateItems.map(day => <button key={day} type="button" onClick={() => changeDay(day)} className={`calendar-date ${day === date ? 'chosen' : ''}`}><span>{dateFmt(day, { weekday: 'short' }).replace('.', '')}</span><strong>{dateFmt(day, { day: '2-digit' })}</strong><small>{dateFmt(day, { month: 'short' }).replace('.', '')}</small></button>)}</div>
          <div className="date-subtext"><CalendarDays size={14} /> {dateFmt(date, { weekday: 'long', day: 'numeric', month: 'long' })}</div>
        </section>
        <section className="choice-section hours-section"><div className="section-top"><div><span className="eyebrow">HORÁRIOS DISPONÍVEIS</span><h2>Qual fica melhor?</h2></div></div>
          {loadingSlots && <div className="empty-state">Consultando horários...</div>}
          {!loadingSlots && isPreview && <div className="empty-state">Conecte a API local para exibir horários livres e testar a reserva.</div>}
          {!loadingSlots && !isPreview && availability?.slots.length === 0 && <div className="empty-state">Sem horários nesta data. Deslize para outro dia ou escolha outro profissional.</div>}
          {!loadingSlots && !isPreview && ['Manhã', 'Tarde', 'Noite'].map(label => { const slots = groupSlots(label); return slots.length ? <div className="period-block" key={label}><div className="period-title"><span>{label}</span><span /></div><div className="time-grid">{slots.map(slot => <button key={slot.time} type="button" aria-pressed={selectedTime === slot.time} onClick={() => setSelectedTime(slot.time)} className={`time-choice ${selectedTime === slot.time ? 'active' : ''}`}>{slot.time}</button>)}</div></div> : null; })}
          {error && <p className="error" role="alert">{error}</p>}
        </section>
        <div className="sticky-bar"><div><small>{selectedTime ? 'HORÁRIO SELECIONADO' : 'ESCOLHA UM HORÁRIO'}</small><strong>{selectedTime ?? '—'} <span>{selectedTime ? `· ${dateFmt(date, { day: '2-digit', month: 'short' })}` : ''}</span></strong></div><button type="button" disabled={!selectedTime} onClick={() => { setError(null); setStep('identify'); window.scrollTo({top:0,behavior:'instant'}); }}>Continuar <ArrowRight size={18}/></button></div>
        {fullCalendar && <div className="calendar-overlay" role="dialog" aria-modal="true" aria-label="Escolher data"><div className="calendar-sheet"><div className="sheet-head"><strong>Escolher data</strong><button onClick={() => setFullCalendar(false)} aria-label="Fechar" type="button"><X size={19}/></button></div><p>Selecione uma data nos próximos 60 dias.</p><input ref={calendarRef} type="date" min={daysAhead(0)} max={daysAhead(60)} value={date} onChange={e => { changeDay(e.target.value); setFullCalendar(false); }} /><button className="sheet-done" type="button" onClick={() => calendarRef.current?.showPicker?.()}>Abrir calendário <CalendarDays size={16}/></button></div></div>}
      </>}

      {step === 'identify' && service && <>
        <StepHeader step="03 / 03" onBack={back} title="Quase lá!" subtitle="Só precisamos saber quem vai chegar." />
        <div className="booking-summary"><span className="eyebrow">RESUMO DO AGENDAMENTO</span><h2>{service.name}</h2><div><Clock3 size={17}/> {dateFmt(date, { weekday: 'long', day: 'numeric', month: 'long' })} às {selectedTime}</div><div><UserRound size={17}/> {barberId === 'any' ? 'Profissional disponível' : professional?.name}</div><strong>{brl(service.price_cents)} <small>pagar no local</small></strong></div>
        <form className="details-form" onSubmit={submitBooking}><label htmlFor="client-name">Seu nome</label><input id="client-name" required autoComplete="name" maxLength={80} minLength={2} placeholder="Nome e sobrenome" value={clientName} onChange={e => setClientName(e.target.value)}/><label htmlFor="client-phone">WhatsApp com DDD</label><input id="client-phone" required autoComplete="tel" inputMode="tel" pattern="[0-9() +\-]{10,20}" placeholder="(19) 99999-9999" value={clientPhone} onChange={e => setClientPhone(e.target.value)}/><div className="form-note"><ShieldCheck size={19}/> Usaremos seu celular para informações da reserva. A verificação de identidade será obrigatória antes da abertura pública.</div><label className="consent"><input type="checkbox" checked={marketingOptIn} onChange={e => setMarketingOptIn(e.target.checked)}/> Quero receber promoções e convites para voltar (opcional).</label>{error && <p className="error" role="alert">{error}</p>}<button className="confirm-button" disabled={submitting || isPreview} type="submit">{submitting ? 'Confirmando...' : 'Confirmar agendamento'} <ArrowRight size={19}/></button>{isPreview && <small className="demo-disclaimer">Prévia sem API: não é possível confirmar reservas.</small>}</form>
      </>}

      {step === 'success' && booking && service && <div className="success-screen"><div className="success-check"><Check size={40}/></div><span className="eyebrow">AGENDAMENTO CONFIRMADO</span><h1>Te esperamos!</h1><p>Seu horário foi reservado no sistema local de teste.</p><div className="booking-summary"><span className="eyebrow">RESERVA {booking.id.slice(0, 8).toUpperCase()}</span><h2>{service.name}</h2><div><CalendarDays size={17}/>{dateFmt(booking.date, { weekday: 'long', day: 'numeric', month: 'long' })} · {booking.time}</div><div><UserRound size={17}/>{professional?.name ?? 'Profissional confirmado'}</div><strong>{brl(service.price_cents)}</strong></div><p className="success-note">Nenhuma mensagem WhatsApp ou cobrança foi enviada nesta fase.</p><button className="confirm-button" type="button" onClick={() => { setStep('services'); setServiceId(null); setSelectedTime(null); setBooking(null); }}>Novo agendamento <ArrowRight size={18}/></button></div>}
      <footer className="site-footer"><span>ROGER BARBEARIA</span><span><MapPin size={13}/> Seu lugar, seu estilo.</span></footer>
    </div>
  </div>;
}

function StepHeader({ step, onBack, title, subtitle }: { step: string; onBack: () => void; title: string; subtitle: string }) {
  return <div className="step-header"><div className="step-nav"><button onClick={onBack} aria-label="Voltar" type="button"><ArrowLeft size={20}/></button><span>PASSO {step}</span></div><div className="step-indicator"><div className="on"/><div className="on"/><div/></div><h1>{title}</h1><p>{subtitle}</p></div>;
}

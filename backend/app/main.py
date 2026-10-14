"""Booking vertical slice. Demo schedules only; not ready for public production."""
from __future__ import annotations

import hmac
import os
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine, delete, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

LOCAL_TZ = ZoneInfo('America/Sao_Paulo')
OPEN_MINUTE = 9 * 60
CLOSE_MINUTE = 18 * 60
LUNCH_START = 12 * 60
LUNCH_END = 13 * 60
INTERVAL = 30
HORIZON_DAYS = 60


class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = 'services'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(200), default='')
    price_cents: Mapped[int] = mapped_column(Integer)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Barber(Base):
    __tablename__ = 'barbers'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BarberService(Base):
    __tablename__ = 'barber_services'
    barber_id: Mapped[str] = mapped_column(ForeignKey('barbers.id'), primary_key=True)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.id'), primary_key=True)


class BarberShift(Base):
    """Weekly availability; multiple shifts per weekday represent breaks."""
    __tablename__ = 'barber_shifts'
    __table_args__ = (UniqueConstraint('barber_id', 'weekday', 'start_minute', name='uq_barber_shift_start'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    barber_id: Mapped[str] = mapped_column(ForeignKey('barbers.id'), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 Monday through 6 Sunday
    start_minute: Mapped[int] = mapped_column(Integer)
    end_minute: Mapped[int] = mapped_column(Integer)


class BarberBlock(Base):
    """One-off leave or blocked hours. Confirmed bookings are never silently displaced."""
    __tablename__ = 'barber_blocks'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    barber_id: Mapped[str] = mapped_column(ForeignKey('barbers.id'), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    start_minute: Mapped[int] = mapped_column(Integer)
    end_minute: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(120), default='')


class Booking(Base):
    __tablename__ = 'bookings'
    __table_args__ = (UniqueConstraint('barber_id', 'day', 'start_minute', name='uq_barber_start'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    barber_id: Mapped[str] = mapped_column(ForeignKey('barbers.id'), index=True)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.id'))
    client_name: Mapped[str] = mapped_column(String(100))
    client_phone: Mapped[str] = mapped_column(String(11))
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    day: Mapped[date] = mapped_column(Date, index=True)
    start_minute: Mapped[int] = mapped_column(Integer)
    end_minute: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='confirmed')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ServiceOut(BaseModel):
    id: str
    name: str
    description: str
    price_cents: int
    duration_minutes: int
    image_url: str | None
    model_config = {'from_attributes': True}


class BarberOut(BaseModel):
    id: str
    name: str
    service_ids: list[str]


class CatalogOut(BaseModel):
    services: list[ServiceOut]
    barbers: list[BarberOut]


class SlotOut(BaseModel):
    time: str
    barber_id: str


class AvailabilityOut(BaseModel):
    date: date
    slots: list[SlotOut]


class DaySummaryOut(BaseModel):
    date: date
    available: bool


class DaysSummaryOut(BaseModel):
    days: list[DaySummaryOut]


class BookingIn(BaseModel):
    service_id: str
    barber_id: str | None = None
    date: date
    time: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    client_name: str = Field(min_length=2, max_length=80)
    client_phone: str
    marketing_opt_in: bool = False

    @field_validator('client_phone')
    @classmethod
    def phone_digits(cls, raw: str) -> str:
        value = re.sub(r'\D', '', raw)
        if len(value) not in (10, 11):
            raise ValueError('Informe telefone brasileiro com DDD (10 ou 11 dígitos).')
        return value

    @field_validator('client_name')
    @classmethod
    def strip_name(cls, raw: str) -> str:
        value = raw.strip()
        if len(value) < 2:
            raise ValueError('Informe seu nome.')
        return value


class BookingOut(BaseModel):
    id: str
    service_id: str
    barber_id: str
    date: date
    time: str
    status: str


class AdminServiceIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default='', max_length=200)
    price_cents: int = Field(ge=0, le=1_000_000)
    duration_minutes: int = Field(ge=10, le=240)
    image_url: str | None = Field(default=None, max_length=500)
    active: bool = True


class AdminBarberIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    service_ids: list[str] = Field(default_factory=list)
    active: bool = True


class ShiftIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    end: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')


class BarberShiftIn(BaseModel):
    shifts: list[ShiftIn] = Field(max_length=28)


class BlockIn(BaseModel):
    date: date
    start: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    end: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    reason: str = Field(default='', max_length=120)


class BookingStatusIn(BaseModel):
    status: str = Field(pattern=r'^(confirmed|completed|cancelled|no_show)$')


class AdminBookingOut(BaseModel):
    id: str
    barber_id: str
    barber_name: str
    service_id: str
    service_name: str
    price_cents: int
    client_name: str
    client_phone: str
    date: date
    time: str
    status: str


def normalize_phone(raw: str) -> str:
    return re.sub(r'\D', '', raw)


def validate_business_id(value: str) -> None:
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', value):
        raise HTTPException(status_code=422, detail='ID inválido (use letras minúsculas, números, _ ou -).')


def validate_interval(start: int, end: int) -> None:
    if start < 0 or end > 24 * 60 or start >= end or start % INTERVAL != 0 or end % INTERVAL != 0:
        raise HTTPException(status_code=422, detail='Intervalos devem ter início/fim em blocos de 30 minutos e não atravessar meia-noite.')


def hhmm(value: int) -> str:
    return f'{value // 60:02}:{value % 60:02}'


def minutes(value: str) -> int:
    hour, minute = map(int, value.split(':'))
    return hour * 60 + minute


def check_day(day: date) -> None:
    today = datetime.now(LOCAL_TZ).date()
    if day < today or day > today + timedelta(days=HORIZON_DAYS):
        raise HTTPException(status_code=422, detail='Escolha uma data nos próximos 60 dias.')


def seeded(db: Session) -> None:
    if db.get(Service, 'corte') is not None:
        return
    services = [
        Service(id='corte', name='Corte clássico', description='Seu estilo, no capricho.', price_cents=4500, duration_minutes=45),
        Service(id='degrade', name='Degradê', description='Precisão em cada detalhe.', price_cents=5500, duration_minutes=50),
        Service(id='combo', name='Corte + barba', description='Experiência completa.', price_cents=7500, duration_minutes=75),
        Service(id='barba', name='Barba', description='Alinhamento e acabamento.', price_cents=3000, duration_minutes=30),
    ]
    barbers = [Barber(id='roger', name='Roger'), Barber(id='bruno', name='Bruno'), Barber(id='rafael', name='Rafael')]
    db.add_all(services + barbers)
    for barber in barbers:
        for service in services:
            if barber.id != 'rafael' or service.id != 'degrade':
                db.add(BarberService(barber_id=barber.id, service_id=service.id))
    for barber in barbers:
        for weekday in range(6):
            for start, end in ((OPEN_MINUTE, LUNCH_START), (LUNCH_END, CLOSE_MINUTE)):
                db.add(BarberShift(id=str(uuid.uuid4()), barber_id=barber.id, weekday=weekday,
                                   start_minute=start, end_minute=end))
    db.commit()


def available_barbers(db: Session, service_id: str, barber_id: str | None) -> list[Barber]:
    stmt = select(Barber).join(BarberService).where(
        BarberService.service_id == service_id, Barber.active.is_(True)
    ).order_by(Barber.id)
    if barber_id:
        stmt = stmt.where(Barber.id == barber_id)
    return list(db.scalars(stmt).all())


def available_start_times(db: Session, barber_id: str, service: Service, day: date, now: datetime) -> set[int]:
    """Availability is derived from actual shifts, blocks and existing bookings."""
    shifts = db.scalars(select(BarberShift).where(
        BarberShift.barber_id == barber_id, BarberShift.weekday == day.weekday()
    )).all()
    if not shifts:
        return set()
    blocks = db.scalars(select(BarberBlock).where(
        BarberBlock.barber_id == barber_id, BarberBlock.day == day
    )).all()
    existing = db.scalars(select(Booking).where(
        Booking.barber_id == barber_id, Booking.day == day, Booking.status == 'confirmed'
    )).all()
    result = set()
    for start in range(0, 24 * 60 - service.duration_minutes + 1, INTERVAL):
        end = start + service.duration_minutes
        if not any(shift.start_minute <= start and end <= shift.end_minute for shift in shifts):
            continue
        if any(block.start_minute < end and block.end_minute > start for block in blocks):
            continue
        if any(booking.start_minute < end and booking.end_minute > start for booking in existing):
            continue
        when = datetime(day.year, day.month, day.day, start // 60, start % 60, tzinfo=LOCAL_TZ)
        if when <= now:
            continue
        result.add(start)
    return result


def slot_valid(db: Session, barber_id: str, service: Service, day: date, start: int, now: datetime) -> bool:
    return start in available_start_times(db, barber_id, service, day, now)


def create_app(database_url: str | None = None, *, booking_enabled: bool | None = None,
               seed_demo: bool | None = None, admin_api_key: str | None = None) -> FastAPI:
    url = database_url or os.environ.get('DATABASE_URL', 'sqlite:///./barberia.db')
    enabled = booking_enabled if booking_enabled is not None else os.getenv('BOOKING_ENABLED', 'false').lower() == 'true'
    seed = seed_demo if seed_demo is not None else os.getenv('SEED_DEMO_DATA', 'false').lower() == 'true'
    secret = admin_api_key if admin_api_key is not None else os.getenv('ADMIN_API_KEY', '')
    if secret and len(secret) < 32:
        raise ValueError('ADMIN_API_KEY precisa ter ao menos 32 caracteres aleatórios.')
    connect_args = {'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite') else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    Base.metadata.create_all(engine)  # Dev pilot only; replace with Alembic migrations before production.
    SessionLocal = sessionmaker(engine, expire_on_commit=False)
    if seed:
        with SessionLocal() as db:
            seeded(db)

    app = FastAPI(title='Roger Barbearia API', version='0.1.0')
    origins = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'], allow_headers=['Content-Type', 'Authorization'])

    def get_db():
        with SessionLocal() as session:
            yield session

    def require_admin(authorization: str | None = Header(default=None)) -> None:
        # No fallback credentials. Disabled until a unique server-side key is configured.
        if not secret:
            raise HTTPException(status_code=503, detail='Administração ainda não configurada.')
        scheme, _, supplied = (authorization or '').partition(' ')
        if scheme.lower() != 'bearer' or not hmac.compare_digest(supplied, secret):
            raise HTTPException(status_code=401, detail='Acesso administrativo não autorizado.',
                                headers={'WWW-Authenticate': 'Bearer'})


    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'bookings_enabled': enabled}

    @app.get('/api/catalog', response_model=CatalogOut)
    def catalog(db: Session = Depends(get_db)):
        services = list(db.scalars(select(Service).where(Service.active.is_(True)).order_by(Service.id)).all())
        barbers = list(db.scalars(select(Barber).where(Barber.active.is_(True)).order_by(Barber.name)).all())
        pairs = db.execute(select(BarberService.barber_id, BarberService.service_id)).all()
        service_map: dict[str, list[str]] = {}
        for barber_id, service_id in pairs:
            service_map.setdefault(barber_id, []).append(service_id)
        return {'services': services, 'barbers': [BarberOut(id=b.id, name=b.name, service_ids=service_map.get(b.id, [])) for b in barbers]}

    @app.get('/api/availability/days', response_model=DaysSummaryOut)
    def availability_days(
        service_id: str,
        start: date,
        count: int = Query(default=30, ge=1, le=30),
        barber_id: str | None = None,
        db: Session = Depends(get_db),
    ):
        check_day(start)
        check_day(start + timedelta(days=count - 1))
        service = db.get(Service, service_id)
        if not service or not service.active:
            raise HTTPException(404, 'Serviço não encontrado.')
        barbers = available_barbers(db, service_id, barber_id)
        if barber_id and not barbers:
            raise HTTPException(422, 'Profissional indisponível para este serviço.')
        now = datetime.now(LOCAL_TZ)
        # Summary, not reservation: the booking endpoint always rechecks conflicts.
        days = []
        for i in range(count):
            day = start + timedelta(days=i)
            if not barbers:
                days.append(DaySummaryOut(date=day, available=False))
                continue
            has_slot = any(available_start_times(db, b.id, service, day, now) for b in barbers)
            days.append(DaySummaryOut(date=day, available=has_slot))
        return DaysSummaryOut(days=days)

    @app.get('/api/availability', response_model=AvailabilityOut)
    def availability(service_id: str, date_: date = Query(alias='date'), barber_id: str | None = None, db: Session = Depends(get_db)):
        check_day(date_)
        service = db.get(Service, service_id)
        if not service or not service.active:
            raise HTTPException(404, 'Serviço não encontrado.')
        barbers = available_barbers(db, service_id, barber_id)
        if barber_id and not barbers:
            raise HTTPException(422, 'Profissional indisponível para este serviço.')
        now = datetime.now(LOCAL_TZ)
        by_barber = {b.id: available_start_times(db, b.id, service, date_, now) for b in barbers}
        slots = [SlotOut(time=hhmm(start), barber_id=next(b.id for b in barbers if start in by_barber[b.id]))
                 for start in sorted(set().union(*by_barber.values()))] if by_barber else []
        return AvailabilityOut(date=date_, slots=slots)

    @app.post('/api/bookings', response_model=BookingOut, status_code=201)
    def book(payload: BookingIn, db: Session = Depends(get_db)):
        if not enabled:
            raise HTTPException(503, 'Agendamento público ainda não habilitado.')
        check_day(payload.date)
        start = minutes(payload.time)
        try:
            # SQLite serializes writers; PostgreSQL locks the candidate barber rows.
            # Rechecking conflicts after locking prevents overlapping reservations.
            if engine.dialect.name == 'sqlite':
                db.execute(text('BEGIN IMMEDIATE'))
            service = db.get(Service, payload.service_id)
            if not service or not service.active:
                raise HTTPException(404, 'Serviço não encontrado.')
            stmt = select(Barber).join(BarberService).where(
                Barber.active.is_(True), BarberService.service_id == service.id
            ).order_by(Barber.id)
            if payload.barber_id:
                stmt = stmt.where(Barber.id == payload.barber_id)
            if engine.dialect.name == 'postgresql':
                stmt = stmt.with_for_update(of=Barber)
            barbers = list(db.scalars(stmt).all())
            now = datetime.now(LOCAL_TZ)
            choice = next((b for b in barbers if slot_valid(db, b.id, service, payload.date, start, now)), None)
            if choice is None:
                raise HTTPException(409, 'Este horário não está mais disponível. Escolha outro.')
            new = Booking(id=str(uuid.uuid4()), barber_id=choice.id, service_id=service.id,
                          client_name=payload.client_name, client_phone=payload.client_phone,
                          day=payload.date, start_minute=start, end_minute=start + service.duration_minutes,
                          marketing_opt_in=payload.marketing_opt_in, status='confirmed')
            db.add(new)
            db.commit()
            return BookingOut(id=new.id, service_id=new.service_id, barber_id=new.barber_id,
                              date=new.day, time=hhmm(new.start_minute), status=new.status)
        except Exception:
            db.rollback()
            raise

    # Admin-only configuration endpoints for the local pilot. Real production must add
    # staff identities/RBAC, rate limiting, HTTPS and audited database migrations.
    def lock_barber_configuration(db: Session, barber_id: str) -> None:
        # Same locking order as public booking: serialize changes to shifts/blocks
        # with booking creation so a confirmed appointment is never orphaned.
        if engine.dialect.name == 'sqlite':
            db.execute(text('BEGIN IMMEDIATE'))
        elif engine.dialect.name == 'postgresql':
            db.execute(select(Barber.id).where(Barber.id == barber_id).with_for_update()).first()

    @app.get('/api/admin/config', dependencies=[Depends(require_admin)])
    def get_admin_config(db: Session = Depends(get_db)):
        services = db.scalars(select(Service).order_by(Service.name)).all()
        barbers = db.scalars(select(Barber).order_by(Barber.name)).all()
        pairs = db.execute(select(BarberService.barber_id, BarberService.service_id)).all()
        shifts = db.scalars(select(BarberShift).order_by(BarberShift.barber_id, BarberShift.weekday, BarberShift.start_minute)).all()
        blocks = db.scalars(select(BarberBlock).order_by(BarberBlock.day, BarberBlock.start_minute)).all()
        return {
            'services': [dict(id=s.id, name=s.name, description=s.description, price_cents=s.price_cents,
                              duration_minutes=s.duration_minutes, image_url=s.image_url, active=s.active) for s in services],
            'barbers': [dict(id=b.id, name=b.name, active=b.active,
                             service_ids=[sid for bid, sid in pairs if bid == b.id]) for b in barbers],
            'shifts': [dict(barber_id=s.barber_id, weekday=s.weekday, start=hhmm(s.start_minute), end=hhmm(s.end_minute)) for s in shifts],
            'blocks': [dict(id=b.id, barber_id=b.barber_id, date=b.day, start=hhmm(b.start_minute),
                            end=hhmm(b.end_minute), reason=b.reason) for b in blocks],
        }

    @app.put('/api/admin/services/{service_id}', response_model=ServiceOut, dependencies=[Depends(require_admin)])
    def upsert_service(service_id: str, payload: AdminServiceIn, db: Session = Depends(get_db)):
        validate_business_id(service_id)
        value = db.get(Service, service_id)
        if value is None:
            value = Service(id=service_id)
            db.add(value)
        for attr in ('name', 'description', 'price_cents', 'duration_minutes', 'image_url', 'active'):
            setattr(value, attr, getattr(payload, attr))
        db.commit()
        db.refresh(value)
        return value

    @app.put('/api/admin/barbers/{barber_id}', dependencies=[Depends(require_admin)])
    def upsert_barber(barber_id: str, payload: AdminBarberIn, db: Session = Depends(get_db)):
        validate_business_id(barber_id)
        requested = set(payload.service_ids)
        existing = set(db.scalars(select(Service.id).where(Service.id.in_(requested))).all()) if requested else set()
        if existing != requested:
            raise HTTPException(status_code=422, detail='Há serviços inexistentes na lista.')
        barber = db.get(Barber, barber_id)
        if barber is None:
            barber = Barber(id=barber_id)
            db.add(barber)
        barber.name = payload.name
        barber.active = payload.active
        db.execute(delete(BarberService).where(BarberService.barber_id == barber_id))
        db.flush()
        db.add_all([BarberService(barber_id=barber_id, service_id=service_id) for service_id in sorted(requested)])
        db.commit()
        return {'id': barber.id, 'name': barber.name, 'active': barber.active, 'service_ids': sorted(requested)}

    @app.put('/api/admin/barbers/{barber_id}/shifts', dependencies=[Depends(require_admin)])
    def replace_shifts(barber_id: str, payload: BarberShiftIn, db: Session = Depends(get_db)):
        lock_barber_configuration(db, barber_id)
        if db.get(Barber, barber_id) is None:
            raise HTTPException(status_code=404, detail='Profissional não encontrado.')
        ranges = []
        for s in payload.shifts:
            start, end = minutes(s.start), minutes(s.end)
            validate_interval(start, end)
            ranges.append((s.weekday, start, end))
        for day in range(7):
            windows = sorted((start, end) for wd, start, end in ranges if wd == day)
            if any(windows[i][0] < windows[i-1][1] for i in range(1, len(windows))):
                raise HTTPException(status_code=422, detail='Expedientes sobrepostos para o mesmo dia.')
        # Existing future appointments must still fit their professional's new schedule.
        future = db.scalars(select(Booking).where(
            Booking.barber_id == barber_id, Booking.day >= datetime.now(LOCAL_TZ).date(),
            Booking.status == 'confirmed'
        )).all()
        for booking in future:
            if not any(wd == booking.day.weekday() and start <= booking.start_minute
                       and booking.end_minute <= end for wd, start, end in ranges):
                raise HTTPException(status_code=409, detail='Mudança deixaria agendamentos existentes fora do expediente.')
        db.execute(delete(BarberShift).where(BarberShift.barber_id == barber_id))
        db.add_all([BarberShift(id=str(uuid.uuid4()), barber_id=barber_id, weekday=day,
                                start_minute=start, end_minute=end) for day, start, end in ranges])
        db.commit()
        return {'barber_id': barber_id, 'shifts': payload.shifts}

    @app.post('/api/admin/barbers/{barber_id}/blocks', status_code=201, dependencies=[Depends(require_admin)])
    def create_block(barber_id: str, payload: BlockIn, db: Session = Depends(get_db)):
        lock_barber_configuration(db, barber_id)
        if db.get(Barber, barber_id) is None:
            raise HTTPException(status_code=404, detail='Profissional não encontrado.')
        start, end = minutes(payload.start), minutes(payload.end)
        validate_interval(start, end)
        if payload.date < datetime.now(LOCAL_TZ).date():
            raise HTTPException(status_code=422, detail='Não é possível bloquear uma data passada.')
        collides = db.scalar(select(Booking.id).where(
            Booking.barber_id == barber_id, Booking.day == payload.date, Booking.status == 'confirmed',
            Booking.start_minute < end, Booking.end_minute > start
        ).limit(1))
        if collides:
            raise HTTPException(status_code=409, detail='Há reservas confirmadas no período. Reagende antes.')
        block = BarberBlock(id=str(uuid.uuid4()), barber_id=barber_id, day=payload.date,
                            start_minute=start, end_minute=end, reason=payload.reason)
        db.add(block)
        db.commit()
        return {'id': block.id, 'barber_id': barber_id, 'date': payload.date,
                'start': payload.start, 'end': payload.end, 'reason': payload.reason}

    @app.delete('/api/admin/barbers/{barber_id}/blocks/{block_id}', status_code=204, dependencies=[Depends(require_admin)])
    def delete_block(barber_id: str, block_id: str, db: Session = Depends(get_db)):
        lock_barber_configuration(db, barber_id)
        block = db.get(BarberBlock, block_id)
        if block is None or block.barber_id != barber_id:
            raise HTTPException(status_code=404, detail='Bloqueio não encontrado.')
        db.delete(block)
        db.commit()

    @app.get('/api/admin/bookings', dependencies=[Depends(require_admin)])
    def list_admin_bookings(day: date, db: Session = Depends(get_db)):
        rows = db.execute(select(Booking, Barber, Service)
                          .join(Barber, Barber.id == Booking.barber_id)
                          .join(Service, Service.id == Booking.service_id)
                          .where(Booking.day == day).order_by(Booking.start_minute)).all()
        return {'bookings': [admin_booking_dict(b, barber, service) for b, barber, service in rows]}

    def admin_booking_dict(booking: Booking, barber: Barber, service: Service) -> dict:
        return dict(id=booking.id, barber_id=barber.id, barber_name=barber.name,
                    service_id=service.id, service_name=service.name, price_cents=service.price_cents,
                    client_name=booking.client_name, client_phone=booking.client_phone,
                    date=booking.day, time=hhmm(booking.start_minute), status=booking.status)

    @app.patch('/api/admin/bookings/{booking_id}', dependencies=[Depends(require_admin)])
    def update_booking_status(booking_id: str, payload: BookingStatusIn, db: Session = Depends(get_db)):
        booking = db.get(Booking, booking_id)
        if booking is None:
            raise HTTPException(status_code=404, detail='Agendamento não encontrado.')
        booking.status = payload.status
        db.commit()
        return {'id': booking.id, 'status': booking.status}

    @app.get('/api/admin/dashboard', dependencies=[Depends(require_admin)])
    def dashboard(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
        today = datetime.now(LOCAL_TZ).date()
        start = start or today.replace(day=1)
        # The internal agenda needs to show upcoming reservations by default;
        # revenue still counts only completed visits below.
        end = end or today + timedelta(days=HORIZON_DAYS)
        if end < start:
            raise HTTPException(status_code=422, detail='Período inválido.')
        rows = db.execute(select(Booking, Barber, Service)
                          .join(Barber, Barber.id == Booking.barber_id)
                          .join(Service, Service.id == Booking.service_id)
                          .where(Booking.day >= start, Booking.day <= end)
                          .order_by(Booking.day, Booking.start_minute)).all()
        bookings = [admin_booking_dict(b, barber, service) for b, barber, service in rows]
        valid = [row for row in bookings if row['status'] != 'cancelled']
        completed = [row for row in valid if row['status'] == 'completed']
        people: dict[str, dict] = {}
        for row in valid:
            phone = row['client_phone']
            person = people.setdefault(phone, {'phone': phone, 'name': row['client_name'], 'visits': 0, 'spent_cents': 0})
            person['name'] = row['client_name']
            person['visits'] += 1
            if row['status'] in ('completed', 'confirmed'):
                person['spent_cents'] += row['price_cents']
        ranking = sorted(people.values(), key=lambda item: (-item['visits'], -item['spent_cents'], item['name'].lower()))
        revenue = sum(row['price_cents'] for row in completed)
        return {'period': {'start': start, 'end': end},
                'metrics': {'appointments': len(valid), 'completed': len(completed), 'cancelled': len([r for r in bookings if r['status'] == 'cancelled']),
                            'customers': len(people), 'revenue_cents': revenue},
                'ranking': ranking[:20], 'bookings': bookings}

    @app.get('/api/admin/customers', dependencies=[Depends(require_admin)])
    def customers(q: str = '', db: Session = Depends(get_db)):
        rows = db.execute(select(Booking, Service)
                          .join(Service, Service.id == Booking.service_id)
                          .order_by(Booking.day.desc(), Booking.start_minute.desc())).all()
        needle = q.strip().lower()
        grouped: dict[str, dict] = {}
        for booking, service in rows:
            if needle and needle not in booking.client_name.lower() and needle not in booking.client_phone:
                continue
            person = grouped.setdefault(booking.client_phone, {'phone': booking.client_phone, 'name': booking.client_name,
                                                               'visits': 0, 'spent_cents': 0, 'last_visit': None})
            person['name'] = booking.client_name
            if booking.status != 'cancelled':
                person['visits'] += 1
                person['spent_cents'] += service.price_cents
                person['last_visit'] = booking.day
        return {'customers': sorted(grouped.values(), key=lambda item: (item['name'].lower(), item['phone']))[:100]}

    @app.get('/api/admin/customers/{phone}/history', dependencies=[Depends(require_admin)])
    def customer_history(phone: str, db: Session = Depends(get_db)):
        phone = normalize_phone(phone)
        rows = db.execute(select(Booking, Barber, Service)
                          .join(Barber, Barber.id == Booking.barber_id)
                          .join(Service, Service.id == Booking.service_id)
                          .where(Booking.client_phone == phone)
                          .order_by(Booking.day.desc(), Booking.start_minute.desc())).all()
        if not rows:
            raise HTTPException(status_code=404, detail='Cliente não encontrado.')
        return {'customer': {'phone': phone, 'name': rows[0][0].client_name},
                'history': [admin_booking_dict(b, barber, service) for b, barber, service in rows]}

    return app


app = create_app()

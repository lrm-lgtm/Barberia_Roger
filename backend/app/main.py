"""Booking vertical slice. Demo schedules only; not ready for public production."""
from __future__ import annotations

import os
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine, select, text
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
    db.commit()


def available_barbers(db: Session, service_id: str, barber_id: str | None) -> list[Barber]:
    stmt = select(Barber).join(BarberService).where(
        BarberService.service_id == service_id, Barber.active.is_(True)
    ).order_by(Barber.id)
    if barber_id:
        stmt = stmt.where(Barber.id == barber_id)
    return list(db.scalars(stmt).all())


def slot_valid(db: Session, barber_id: str, service: Service, day: date, start: int, now: datetime) -> bool:
    end = start + service.duration_minutes
    if day.weekday() == 6 or start < OPEN_MINUTE or end > CLOSE_MINUTE or start % INTERVAL != 0:
        return False
    if start < LUNCH_END and end > LUNCH_START:
        return False
    start_dt = datetime(day.year, day.month, day.day, start // 60, start % 60, tzinfo=LOCAL_TZ)
    if start_dt <= now:
        return False
    conflict = db.scalar(select(Booking.id).where(
        Booking.barber_id == barber_id, Booking.day == day, Booking.status == 'confirmed',
        Booking.start_minute < end, Booking.end_minute > start
    ).limit(1))
    return conflict is None


def create_app(database_url: str | None = None, *, booking_enabled: bool | None = None, seed_demo: bool | None = None) -> FastAPI:
    url = database_url or os.environ.get('DATABASE_URL', 'sqlite:///./barberia.db')
    enabled = booking_enabled if booking_enabled is not None else os.getenv('BOOKING_ENABLED', 'false').lower() == 'true'
    seed = seed_demo if seed_demo is not None else os.getenv('SEED_DEMO_DATA', 'false').lower() == 'true'
    connect_args = {'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite') else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    Base.metadata.create_all(engine)  # Dev pilot only; replace with Alembic migrations before production.
    SessionLocal = sessionmaker(engine, expire_on_commit=False)
    if seed:
        with SessionLocal() as db:
            seeded(db)

    app = FastAPI(title='Roger Barbearia API', version='0.1.0')
    origins = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    def get_db():
        with SessionLocal() as session:
            yield session


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
            if day.weekday() == 6 or not barbers:
                days.append(DaySummaryOut(date=day, available=False))
                continue
            has_slot = any(
                slot_valid(db, b.id, service, day, minute, now)
                for minute in range(OPEN_MINUTE, CLOSE_MINUTE, INTERVAL)
                for b in barbers
            )
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
        slots = [SlotOut(time=hhmm(start), barber_id=b.id)
                 for start in range(OPEN_MINUTE, CLOSE_MINUTE, INTERVAL)
                 if (b := next((b for b in barbers if slot_valid(db, b.id, service, date_, start, now)), None))]
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

    return app


app = create_app()

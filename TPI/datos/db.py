import os
from dotenv import load_dotenv
from datetime import date, datetime
from typing import List, Optional

load_dotenv()

from sqlalchemy import (  # noqa: E402
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DateTime,
    Numeric,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship  # noqa: E402

# Import Business Objects
from business.entities import (  # noqa: E402
    Cliente as ClienteBO,
    Propietario as PropietarioBO,
    Agente as AgenteBO,
    Propiedad as PropiedadBO,
    Contrato as ContratoBO,
    AgenteAsignado as AgenteAsignadoBO,
    PagoInquilino as PagoInquilinoBO,
    PagoPropietario as PagoPropietarioBO,
    Clausula as ClausulaBO,
    AgendaVisita as AgendaVisitaBO,
    InscripcionVisita as InscripcionVisitaBO,
    Reclamo as ReclamoBO,
    AuditLog as AuditLogBO,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
SQLITE_DB_PATH = os.path.join(PROJECT_DIR, "tpi_inmobiliaria.db").replace("\\", "/")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:admin@localhost:5432/tpi_inmobiliaria",
)

# Connect to database with sqlite fallback
try:
    engine = create_engine(DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Warning: PostgreSQL failed ({e}). Falling back to SQLite.")
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Database Models ---


class PersonaTable(Base):
    __tablename__ = "persona"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_doc = Column(String(50), nullable=False)
    nro_doc = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    domicilio = Column(String(200), nullable=False)
    telefono = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    contrasegna_hash = Column(String(255), nullable=False)
    tipo_persona = Column(String(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": tipo_persona,
        "polymorphic_identity": "persona",
    }


class ClienteTable(PersonaTable):
    __tablename__ = "cliente"

    id = Column(Integer, ForeignKey("persona.id"), primary_key=True)
    id_agente_creador = Column(Integer, ForeignKey("agente.id"), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "cliente",
    }


class PropietarioTable(PersonaTable):
    __tablename__ = "propietario"

    id = Column(Integer, ForeignKey("persona.id"), primary_key=True)
    id_agente_creador = Column(Integer, ForeignKey("agente.id"), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "propietario",
    }


class AgenteTable(PersonaTable):
    __tablename__ = "agente"

    id = Column(Integer, ForeignKey("persona.id"), primary_key=True)
    cuil = Column(String(20), unique=True, nullable=False)
    matricula = Column(String(50), unique=True, nullable=False)
    rol = Column(String(50), default="Estándar", nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "agente",
    }


class PropiedadTable(Base):
    __tablename__ = "propiedad"

    id = Column(Integer, primary_key=True, autoincrement=True)
    direccion = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)
    zona = Column(String(100), nullable=False)
    estado = Column(
        String(50), default="disponible", nullable=False
    )
    fecha_disponibilidad = Column(Date, default=date.today, nullable=False)
    id_propietario = Column(
        Integer, ForeignKey("propietario.id"), nullable=False
    )

    propietario = relationship(
        "PropietarioTable", foreign_keys=[id_propietario]
    )


class ContratoTable(Base):
    __tablename__ = "contrato"

    nro_contrato = Column(Integer, primary_key=True, autoincrement=True)
    fecha_solicitud = Column(Date, default=date.today, nullable=False)
    estado = Column(
        String(50), default="solicitado", nullable=False
    )
    fecha_contrato = Column(Date, nullable=True)
    id_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    id_agente = Column(Integer, ForeignKey("agente.id"), nullable=False)
    id_propiedad = Column(Integer, ForeignKey("propiedad.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False, default=0.0)
    comision_porcentaje = Column(Numeric(5, 2), nullable=False, default=10.0)
    comision_agente_porcentaje = Column(Numeric(5, 2), nullable=False, default=3.0)
    tipo_contrato = Column(String(50), default="Alquiler", nullable=False)
    ruta_documento_respaldo = Column(String(500), nullable=True)
    fecha_ultimo_aviso_mora = Column(Date, nullable=True)
    recibos_sueldo_detalle = Column(String(2000), nullable=False, default="")
    garantias_detalle = Column(String(2000), nullable=False, default="")
    ruta_recibos_sueldo = Column(String(500), nullable=True)
    ruta_garantias = Column(String(500), nullable=True)
    decision_propietario = Column(String(20), nullable=False, default="pendiente")
    fecha_decision_propietario = Column(Date, nullable=True)
    observaciones_propietario = Column(String(2000), nullable=False, default="")

    cliente = relationship("ClienteTable", foreign_keys=[id_cliente])
    agente = relationship("AgenteTable", foreign_keys=[id_agente])
    propiedad = relationship("PropiedadTable", foreign_keys=[id_propiedad])


class AgenteAsignadoTable(Base):
    __tablename__ = "agente_asignado"

    id_agente = Column(Integer, ForeignKey("agente.id"), primary_key=True)
    id_propiedad = Column(
        Integer, ForeignKey("propiedad.id"), primary_key=True
    )
    fecha_hora_desde = Column(DateTime, primary_key=True, default=datetime.now)
    fecha_hora_hasta = Column(DateTime, nullable=True)

    agente = relationship("AgenteTable", foreign_keys=[id_agente])
    propiedad = relationship("PropiedadTable", foreign_keys=[id_propiedad])


class PagoInquilinoTable(Base):
    __tablename__ = "pago_inquilino"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nro_contrato = Column(
        Integer, ForeignKey("contrato.nro_contrato"), nullable=False
    )
    fecha_pago = Column(Date, default=date.today, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    mes_correspondiente = Column(String(7), nullable=False)
    fecha_vencimiento = Column(Date, nullable=True)
    dias_retraso = Column(Integer, default=0, nullable=False)
    monto_recargo = Column(Numeric(12, 2), default=0.0, nullable=False)
    monto_total_abonado = Column(Numeric(12, 2), nullable=True)
    ruta_comprobante = Column(String(500), nullable=True)

    contrato = relationship("ContratoTable", foreign_keys=[nro_contrato])


class PagoPropietarioTable(Base):
    __tablename__ = "pago_propietario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_propietario = Column(
        Integer, ForeignKey("propietario.id"), nullable=False
    )
    nro_contrato = Column(
        Integer, ForeignKey("contrato.nro_contrato"), nullable=False
    )
    fecha_liquidacion = Column(Date, default=date.today, nullable=False)
    fecha_pago = Column(Date, nullable=True)
    mes_correspondiente = Column(String(7), nullable=False)
    monto_bruto = Column(Numeric(12, 2), nullable=False)
    comision = Column(Numeric(12, 2), nullable=False)
    monto_neto = Column(Numeric(12, 2), nullable=False)
    estado = Column(
        String(20), default="pendiente", nullable=False
    )

    propietario = relationship(
        "PropietarioTable", foreign_keys=[id_propietario]
    )
    contrato = relationship("ContratoTable", foreign_keys=[nro_contrato])


class ClausulaTable(Base):
    __tablename__ = "clausula"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nro_contrato = Column(
        Integer, ForeignKey("contrato.nro_contrato"), nullable=False
    )
    orden = Column(Integer, nullable=False, default=1)
    titulo = Column(String(200), nullable=False)
    contenido = Column(String, nullable=False)

    contrato = relationship("ContratoTable", foreign_keys=[nro_contrato])


class AgendaVisitaTable(Base):
    __tablename__ = "agenda_visita"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_propiedad = Column(
        Integer, ForeignKey("propiedad.id"), nullable=False
    )
    id_agente = Column(Integer, ForeignKey("agente.id"), nullable=False)
    fecha_hora_visita = Column(DateTime, nullable=False)
    duracion_minutos = Column(Integer, default=30, nullable=False)
    cupo_maximo = Column(Integer, default=3, nullable=False)
    estado = Column(String(20), default="disponible", nullable=False)

    propiedad = relationship("PropiedadTable", foreign_keys=[id_propiedad])
    agente = relationship("AgenteTable", foreign_keys=[id_agente])


class InscripcionVisitaTable(Base):
    __tablename__ = "inscripcion_visita"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_agenda = Column(
        Integer, ForeignKey("agenda_visita.id"), nullable=False
    )
    id_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=True)
    nombre_visitante = Column(String(150), nullable=False)
    telefono_visitante = Column(String(50), nullable=False)
    email_visitante = Column(String(100), nullable=True)
    observaciones = Column(String(500), default="", nullable=True)
    fecha_registro = Column(
        DateTime, default=datetime.now, nullable=False
    )
    asistio = Column(Boolean, nullable=True)

    agenda = relationship("AgendaVisitaTable", foreign_keys=[id_agenda])
    cliente = relationship("ClienteTable", foreign_keys=[id_cliente])


class ReclamoTable(Base):
    __tablename__ = "reclamo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nro_contrato = Column(
        Integer, ForeignKey("contrato.nro_contrato"), nullable=False
    )
    id_propiedad = Column(
        Integer, ForeignKey("propiedad.id"), nullable=False
    )
    id_cliente = Column(
        Integer, ForeignKey("cliente.id"), nullable=False
    )
    fecha_reclamo = Column(Date, default=date.today, nullable=False)
    tipo_dano = Column(String(100), nullable=False)
    descripcion = Column(String(1000), nullable=False)
    urgencia = Column(String(20), default="Media", nullable=False)
    presupuesto_estimado = Column(Numeric(12, 2), default=0.0, nullable=False)
    estado = Column(String(30), default="pendiente", nullable=False)
    observaciones_resolucion = Column(String(1000), default="", nullable=True)
    fecha_resolucion = Column(Date, nullable=True)

    contrato = relationship("ContratoTable", foreign_keys=[nro_contrato])
    propiedad = relationship("PropiedadTable", foreign_keys=[id_propiedad])
    cliente = relationship("ClienteTable", foreign_keys=[id_cliente])


class AuditLogTable(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_hora = Column(DateTime, default=datetime.now, nullable=False)
    id_agente = Column(Integer, ForeignKey("persona.id"), nullable=True)
    entidad = Column(String(50), nullable=False)
    id_entidad = Column(Integer, nullable=True)
    accion = Column(String(50), nullable=False)
    descripcion = Column(String(500), nullable=False)

    agente = relationship("AgenteTable", foreign_keys=[id_agente])



# --- Database Schema Creation ---


def init_db(reset: bool = False):
    def recreate_all():
        try:
            if engine.dialect.name == "postgresql":
                with engine.begin() as conn:
                    from sqlalchemy import text
                    conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            else:
                Base.metadata.drop_all(bind=engine)
        except Exception:
            pass
        Base.metadata.create_all(bind=engine)

    if reset:
        recreate_all()

    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = [
            "persona",
            "agente",
            "propietario",
            "cliente",
            "propiedad",
            "contrato",
            "agente_asignado",
            "pago_inquilino",
            "pago_propietario",
            "clausula",
            "agenda_visita",
            "inscripcion_visita",
            "reclamo",
            "logs_auditoria",
        ]

        needs_recreate = False
        for tbl in required_tables:
            if tbl not in existing_tables:
                needs_recreate = True
                break

        if not needs_recreate and "pago_inquilino" in existing_tables:
            cols = [c["name"] for c in inspector.get_columns("pago_inquilino")]
            if "monto_recargo" not in cols:
                needs_recreate = True

        if not needs_recreate and "cliente" in existing_tables:
            cols_cliente = [c["name"] for c in inspector.get_columns("cliente")]
            if "id_agente_creador" not in cols_cliente:
                with engine.begin() as conn:
                    from sqlalchemy import text
                    conn.execute(text(
                        "ALTER TABLE cliente ADD COLUMN id_agente_creador INTEGER REFERENCES agente(id)"
                    ))

        if not needs_recreate and "propietario" in existing_tables:
            cols_prop = [c["name"] for c in inspector.get_columns("propietario")]
            if "id_agente_creador" not in cols_prop:
                with engine.begin() as conn:
                    from sqlalchemy import text
                    conn.execute(text(
                        "ALTER TABLE propietario ADD COLUMN id_agente_creador INTEGER REFERENCES agente(id)"
                    ))

        if not needs_recreate and "contrato" in existing_tables:
            cols_c = [c["name"] for c in inspector.get_columns("contrato")]
            required_columns = {
                "fecha_ultimo_aviso_mora": "DATE",
                "recibos_sueldo_detalle": "VARCHAR(2000) NOT NULL DEFAULT ''",
                "garantias_detalle": "VARCHAR(2000) NOT NULL DEFAULT ''",
                "ruta_recibos_sueldo": "VARCHAR(500)",
                "ruta_garantias": "VARCHAR(500)",
                "decision_propietario": "VARCHAR(20) NOT NULL DEFAULT 'pendiente'",
                "fecha_decision_propietario": "DATE",
                "observaciones_propietario": "VARCHAR(2000) NOT NULL DEFAULT ''",
            }
            missing_columns = [
                (name, definition)
                for name, definition in required_columns.items()
                if name not in cols_c
            ]
            if missing_columns:
                with engine.begin() as conn:
                    from sqlalchemy import text
                    for name, definition in missing_columns:
                        conn.execute(text(
                            f"ALTER TABLE contrato ADD COLUMN {name} {definition}"
                        ))

        if needs_recreate:
            recreate_all()
        else:
            Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Schema verification note: {e}")
        Base.metadata.create_all(bind=engine)


# Auto-initialize database tables on module import if needed
try:
    init_db()
except Exception:
    pass


# --- Conversions: DB Models -> Business Objects ---


def to_bo_cliente(db_obj: Optional[ClienteTable]) -> Optional[ClienteBO]:
    if not db_obj:
        return None
    return ClienteBO(
        id=db_obj.id,
        tipo_doc=db_obj.tipo_doc,
        nro_doc=db_obj.nro_doc,
        nombre=db_obj.nombre,
        apellido=db_obj.apellido,
        domicilio=db_obj.domicilio,
        telefono=db_obj.telefono,
        email=db_obj.email,
        contrasegna_hash=db_obj.contrasegna_hash,
        id_agente_creador=db_obj.id_agente_creador,
    )


def to_bo_propietario(
    db_obj: Optional[PropietarioTable],
) -> Optional[PropietarioBO]:
    if not db_obj:
        return None
    return PropietarioBO(
        id=db_obj.id,
        tipo_doc=db_obj.tipo_doc,
        nro_doc=db_obj.nro_doc,
        nombre=db_obj.nombre,
        apellido=db_obj.apellido,
        domicilio=db_obj.domicilio,
        telefono=db_obj.telefono,
        email=db_obj.email,
        contrasegna_hash=db_obj.contrasegna_hash,
        id_agente_creador=db_obj.id_agente_creador,
    )


def to_bo_agente(db_obj: Optional[AgenteTable]) -> Optional[AgenteBO]:
    if not db_obj:
        return None
    return AgenteBO(
        id=db_obj.id,
        tipo_doc=db_obj.tipo_doc,
        nro_doc=db_obj.nro_doc,
        nombre=db_obj.nombre,
        apellido=db_obj.apellido,
        domicilio=db_obj.domicilio,
        telefono=db_obj.telefono,
        email=db_obj.email,
        contrasegna_hash=db_obj.contrasegna_hash,
        cuil=db_obj.cuil,
        matricula=db_obj.matricula,
        rol=getattr(db_obj, "rol", "Estándar") or "Estándar",
    )


def to_bo_propiedad(db_obj: Optional[PropiedadTable]) -> Optional[PropiedadBO]:
    if not db_obj:
        return None
    return PropiedadBO(
        id=db_obj.id,
        direccion=db_obj.direccion,
        tipo=db_obj.tipo,
        zona=db_obj.zona,
        estado=db_obj.estado,
        id_propietario=db_obj.id_propietario,
        fecha_disponibilidad=getattr(db_obj, "fecha_disponibilidad", date.today()),
    )


def to_bo_contrato(db_obj: Optional[ContratoTable]) -> Optional[ContratoBO]:
    if not db_obj:
        return None
    return ContratoBO(
        nro_contrato=db_obj.nro_contrato,
        fecha_solicitud=db_obj.fecha_solicitud,
        estado=db_obj.estado,
        fecha_contrato=db_obj.fecha_contrato,
        id_cliente=db_obj.id_cliente,
        id_agente=db_obj.id_agente,
        id_propiedad=db_obj.id_propiedad,
        monto=float(db_obj.monto),
        comision_porcentaje=float(db_obj.comision_porcentaje),
        comision_agente_porcentaje=float(getattr(db_obj, "comision_agente_porcentaje", 3.0) or 3.0),
        tipo_contrato=getattr(db_obj, "tipo_contrato", "Alquiler") or "Alquiler",
        ruta_documento_respaldo=getattr(db_obj, "ruta_documento_respaldo", None),
        fecha_ultimo_aviso_mora=getattr(db_obj, "fecha_ultimo_aviso_mora", None),
        recibos_sueldo_detalle=getattr(db_obj, "recibos_sueldo_detalle", "") or "",
        garantias_detalle=getattr(db_obj, "garantias_detalle", "") or "",
        ruta_recibos_sueldo=getattr(db_obj, "ruta_recibos_sueldo", None),
        ruta_garantias=getattr(db_obj, "ruta_garantias", None),
        decision_propietario=getattr(db_obj, "decision_propietario", "pendiente") or "pendiente",
        fecha_decision_propietario=getattr(db_obj, "fecha_decision_propietario", None),
        observaciones_propietario=getattr(db_obj, "observaciones_propietario", "") or "",
    )


def to_bo_pago_inquilino(
    db_obj: Optional[PagoInquilinoTable],
) -> Optional[PagoInquilinoBO]:
    if not db_obj:
        return None
    return PagoInquilinoBO(
        id=db_obj.id,
        nro_contrato=db_obj.nro_contrato,
        fecha_pago=db_obj.fecha_pago,
        monto=float(db_obj.monto),
        mes_correspondiente=db_obj.mes_correspondiente,
        fecha_vencimiento=getattr(db_obj, "fecha_vencimiento", None),
        dias_retraso=int(getattr(db_obj, "dias_retraso", 0) or 0),
        monto_recargo=float(getattr(db_obj, "monto_recargo", 0.0) or 0.0),
        monto_total_abonado=float(getattr(db_obj, "monto_total_abonado", db_obj.monto) or db_obj.monto),
        ruta_comprobante=getattr(db_obj, "ruta_comprobante", None),
    )


def to_bo_pago_propietario(
    db_obj: Optional[PagoPropietarioTable],
) -> Optional[PagoPropietarioBO]:
    if not db_obj:
        return None
    return PagoPropietarioBO(
        id=db_obj.id,
        id_propietario=db_obj.id_propietario,
        nro_contrato=db_obj.nro_contrato,
        fecha_liquidacion=db_obj.fecha_liquidacion,
        fecha_pago=db_obj.fecha_pago,
        mes_correspondiente=db_obj.mes_correspondiente,
        monto_bruto=float(db_obj.monto_bruto),
        comision=float(db_obj.comision),
        monto_neto=float(db_obj.monto_neto),
        estado=db_obj.estado,
    )


def to_bo_agente_asignado(
    db_obj: Optional[AgenteAsignadoTable],
) -> Optional[AgenteAsignadoBO]:
    if not db_obj:
        return None
    return AgenteAsignadoBO(
        id_agente=db_obj.id_agente,
        id_propiedad=db_obj.id_propiedad,
        fecha_hora_desde=db_obj.fecha_hora_desde,
        fecha_hora_hasta=db_obj.fecha_hora_hasta,
    )


def to_bo_clausula(obj: Optional[ClausulaTable]) -> Optional[ClausulaBO]:
    if not obj:
        return None
    return ClausulaBO(
        id=obj.id,
        nro_contrato=obj.nro_contrato,
        orden=obj.orden,
        titulo=obj.titulo,
        contenido=obj.contenido,
    )


def to_bo_agenda_visita(
    db_obj: Optional[AgendaVisitaTable],
) -> Optional[AgendaVisitaBO]:
    if not db_obj:
        return None
    return AgendaVisitaBO(
        id=db_obj.id,
        id_propiedad=db_obj.id_propiedad,
        id_agente=db_obj.id_agente,
        fecha_hora_visita=db_obj.fecha_hora_visita,
        duracion_minutos=db_obj.duracion_minutos,
        cupo_maximo=db_obj.cupo_maximo,
        estado=db_obj.estado,
    )


def to_bo_inscripcion_visita(
    db_obj: Optional[InscripcionVisitaTable],
) -> Optional[InscripcionVisitaBO]:
    if not db_obj:
        return None
    return InscripcionVisitaBO(
        id=db_obj.id,
        id_agenda=db_obj.id_agenda,
        id_cliente=db_obj.id_cliente,
        nombre_visitante=db_obj.nombre_visitante,
        telefono_visitante=db_obj.telefono_visitante,
        email_visitante=db_obj.email_visitante,
        observaciones=db_obj.observaciones or "",
        fecha_registro=db_obj.fecha_registro,
        asistio=db_obj.asistio,
    )


def to_bo_reclamo(db_obj: Optional[ReclamoTable]) -> Optional[ReclamoBO]:
    if not db_obj:
        return None
    return ReclamoBO(
        id=db_obj.id,
        nro_contrato=db_obj.nro_contrato,
        id_propiedad=db_obj.id_propiedad,
        id_cliente=db_obj.id_cliente,
        fecha_reclamo=db_obj.fecha_reclamo,
        tipo_dano=db_obj.tipo_dano,
        descripcion=db_obj.descripcion,
        urgencia=db_obj.urgencia,
        presupuesto_estimado=float(db_obj.presupuesto_estimado or 0.0),
        estado=db_obj.estado,
        observaciones_resolucion=db_obj.observaciones_resolucion or "",
        fecha_resolucion=db_obj.fecha_resolucion,
    )


def to_bo_audit_log(obj: Optional[AuditLogTable]) -> Optional[AuditLogBO]:
    if not obj:
        return None
    return AuditLogBO(
        id=obj.id,
        fecha_hora=obj.fecha_hora,
        id_agente=obj.id_agente,
        entidad=obj.entidad,
        id_entidad=obj.id_entidad,
        accion=obj.accion,
        descripcion=obj.descripcion,
    )



# --- Data Access API ---


def get_cliente_by_id(id_cliente: int) -> Optional[ClienteBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ClienteTable)
            .filter(ClienteTable.id == id_cliente)
            .first()
        )
        return to_bo_cliente(obj)
    finally:
        db.close()


def get_cliente_by_email(email: str) -> Optional[ClienteBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ClienteTable)
            .filter(ClienteTable.email == email)
            .first()
        )
        return to_bo_cliente(obj)
    finally:
        db.close()


def get_cliente_by_doc(tipo_doc: str, nro_doc: str) -> Optional[ClienteBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ClienteTable)
            .filter(
                ClienteTable.tipo_doc == tipo_doc,
                ClienteTable.nro_doc == nro_doc,
            )
            .first()
        )
        return to_bo_cliente(obj)
    finally:
        db.close()


def save_cliente(bo: ClienteBO) -> ClienteBO:
    db = SessionLocal()
    try:
        if bo.id:
            db_obj = (
                db.query(ClienteTable)
                .filter(ClienteTable.id == bo.id)
                .first()
            )
            if db_obj:
                db_obj.tipo_doc = bo.tipo_doc
                db_obj.nro_doc = bo.nro_doc
                db_obj.nombre = bo.nombre
                db_obj.apellido = bo.apellido
                db_obj.domicilio = bo.domicilio
                db_obj.telefono = bo.telefono
                db_obj.email = bo.email
                db_obj.contrasegna_hash = bo.contrasegna_hash
                db_obj.id_agente_creador = bo.id_agente_creador
        else:
            db_obj = ClienteTable(
                tipo_doc=bo.tipo_doc,
                nro_doc=bo.nro_doc,
                nombre=bo.nombre,
                apellido=bo.apellido,
                domicilio=bo.domicilio,
                telefono=bo.telefono,
                email=bo.email,
                contrasegna_hash=bo.contrasegna_hash,
                id_agente_creador=bo.id_agente_creador,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_cliente(db_obj)
    finally:
        db.close()


def list_clientes() -> List[ClienteBO]:
    db = SessionLocal()
    try:
        objs = db.query(ClienteTable).all()
        return [to_bo_cliente(o) for o in objs]
    finally:
        db.close()


def list_clientes_by_agente(id_agente: int) -> List[ClienteBO]:
    """Lista clientes creados por un agente específico."""
    db = SessionLocal()
    try:
        objs = db.query(ClienteTable).filter(ClienteTable.id_agente_creador == id_agente).all()
        return [to_bo_cliente(o) for o in objs]
    finally:
        db.close()


def get_propietario_by_id(id_propietario: int) -> Optional[PropietarioBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PropietarioTable)
            .filter(PropietarioTable.id == id_propietario)
            .first()
        )
        return to_bo_propietario(obj)
    finally:
        db.close()


def get_propietario_by_email(email: str) -> Optional[PropietarioBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PropietarioTable)
            .filter(PropietarioTable.email == email)
            .first()
        )
        return to_bo_propietario(obj)
    finally:
        db.close()


def get_propietario_by_doc(
    tipo_doc: str, nro_doc: str
) -> Optional[PropietarioBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PropietarioTable)
            .filter(
                PropietarioTable.tipo_doc == tipo_doc,
                PropietarioTable.nro_doc == nro_doc,
            )
            .first()
        )
        return to_bo_propietario(obj)
    finally:
        db.close()


def save_propietario(bo: PropietarioBO) -> PropietarioBO:
    db = SessionLocal()
    try:
        if bo.id:
            db_obj = (
                db.query(PropietarioTable)
                .filter(PropietarioTable.id == bo.id)
                .first()
            )
            if db_obj:
                db_obj.tipo_doc = bo.tipo_doc
                db_obj.nro_doc = bo.nro_doc
                db_obj.nombre = bo.nombre
                db_obj.apellido = bo.apellido
                db_obj.domicilio = bo.domicilio
                db_obj.telefono = bo.telefono
                db_obj.email = bo.email
                db_obj.contrasegna_hash = bo.contrasegna_hash
                db_obj.id_agente_creador = bo.id_agente_creador
        else:
            db_obj = PropietarioTable(
                tipo_doc=bo.tipo_doc,
                nro_doc=bo.nro_doc,
                nombre=bo.nombre,
                apellido=bo.apellido,
                domicilio=bo.domicilio,
                telefono=bo.telefono,
                email=bo.email,
                contrasegna_hash=bo.contrasegna_hash,
                id_agente_creador=bo.id_agente_creador,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_propietario(db_obj)
    finally:
        db.close()


def list_propietarios() -> List[PropietarioBO]:
    db = SessionLocal()
    try:
        objs = db.query(PropietarioTable).all()
        return [to_bo_propietario(o) for o in objs]
    finally:
        db.close()


def list_propietarios_by_agente(id_agente: int) -> List[PropietarioBO]:
    """Lista propietarios creados por un agente específico."""
    db = SessionLocal()
    try:
        objs = db.query(PropietarioTable).filter(PropietarioTable.id_agente_creador == id_agente).all()
        return [to_bo_propietario(o) for o in objs]
    finally:
        db.close()


def get_agente_by_id(id_agente: int) -> Optional[AgenteBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(AgenteTable)
            .filter(AgenteTable.id == id_agente)
            .first()
        )
        return to_bo_agente(obj)
    finally:
        db.close()


def get_agente_by_email(email: str) -> Optional[AgenteBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(AgenteTable)
            .filter(AgenteTable.email == email)
            .first()
        )
        return to_bo_agente(obj)
    finally:
        db.close()


def get_agente_by_cuil(cuil: str) -> Optional[AgenteBO]:
    db = SessionLocal()
    try:
        obj = db.query(AgenteTable).filter(AgenteTable.cuil == cuil).first()
        return to_bo_agente(obj)
    finally:
        db.close()


def get_agente_by_matricula(matricula: str) -> Optional[AgenteBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(AgenteTable)
            .filter(AgenteTable.matricula == matricula)
            .first()
        )
        return to_bo_agente(obj)
    finally:
        db.close()


def save_agente(bo: AgenteBO) -> AgenteBO:
    db = SessionLocal()
    try:
        if bo.id:
            db_obj = (
                db.query(AgenteTable).filter(AgenteTable.id == bo.id).first()
            )
            if db_obj:
                db_obj.tipo_doc = bo.tipo_doc
                db_obj.nro_doc = bo.nro_doc
                db_obj.nombre = bo.nombre
                db_obj.apellido = bo.apellido
                db_obj.domicilio = bo.domicilio
                db_obj.telefono = bo.telefono
                db_obj.email = bo.email
                db_obj.contrasegna_hash = bo.contrasegna_hash
                db_obj.cuil = bo.cuil
                db_obj.matricula = bo.matricula
                db_obj.rol = bo.rol
        else:
            db_obj = AgenteTable(
                tipo_doc=bo.tipo_doc,
                nro_doc=bo.nro_doc,
                nombre=bo.nombre,
                apellido=bo.apellido,
                domicilio=bo.domicilio,
                telefono=bo.telefono,
                email=bo.email,
                contrasegna_hash=bo.contrasegna_hash,
                cuil=bo.cuil,
                matricula=bo.matricula,
                rol=bo.rol,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_agente(db_obj)
    finally:
        db.close()


def list_agentes() -> List[AgenteBO]:
    db = SessionLocal()
    try:
        objs = db.query(AgenteTable).all()
        return [to_bo_agente(o) for o in objs]
    finally:
        db.close()


def get_propiedad_by_id(id_propiedad: int) -> Optional[PropiedadBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PropiedadTable)
            .filter(PropiedadTable.id == id_propiedad)
            .first()
        )
        return to_bo_propiedad(obj)
    finally:
        db.close()


def save_propiedad(bo: PropiedadBO) -> PropiedadBO:
    db = SessionLocal()
    try:
        if bo.id:
            db_obj = (
                db.query(PropiedadTable)
                .filter(PropiedadTable.id == bo.id)
                .first()
            )
            if db_obj:
                db_obj.direccion = bo.direccion
                db_obj.tipo = bo.tipo
                db_obj.zona = bo.zona
                db_obj.estado = bo.estado
                db_obj.id_propietario = bo.id_propietario
                db_obj.fecha_disponibilidad = bo.fecha_disponibilidad
        else:
            db_obj = PropiedadTable(
                direccion=bo.direccion,
                tipo=bo.tipo,
                zona=bo.zona,
                estado=bo.estado,
                id_propietario=bo.id_propietario,
                fecha_disponibilidad=bo.fecha_disponibilidad,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_propiedad(db_obj)
    finally:
        db.close()


def list_propiedades() -> List[PropiedadBO]:
    db = SessionLocal()
    try:
        objs = db.query(PropiedadTable).all()
        return [to_bo_propiedad(o) for o in objs]
    finally:
        db.close()


def list_propiedades_by_agente(id_agente: int) -> List[PropiedadBO]:
    """
    Lista propiedades actualmente asignadas a un agente específico.
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        # Obtener todas las asignaciones activas del agente
        asignaciones = (
            db.query(AgenteAsignadoTable)
            .filter(
                AgenteAsignadoTable.id_agente == id_agente,
                AgenteAsignadoTable.fecha_hora_desde <= now,
                (AgenteAsignadoTable.fecha_hora_hasta.is_(None))
                | (AgenteAsignadoTable.fecha_hora_hasta >= now),
            )
            .all()
        )
        
        # Obtener las propiedades de esas asignaciones
        propiedad_ids = [asig.id_propiedad for asig in asignaciones]
        if not propiedad_ids:
            return []
        
        objs = db.query(PropiedadTable).filter(PropiedadTable.id.in_(propiedad_ids)).all()
        return [to_bo_propiedad(o) for o in objs]
    finally:
        db.close()


def get_contrato_by_id(nro_contrato: int) -> Optional[ContratoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ContratoTable)
            .filter(ContratoTable.nro_contrato == nro_contrato)
            .first()
        )
        return to_bo_contrato(obj)
    finally:
        db.close()


def list_contratos() -> List[ContratoBO]:
    db = SessionLocal()
    try:
        objs = db.query(ContratoTable).all()
        return [to_bo_contrato(o) for o in objs]
    finally:
        db.close()


def list_contratos_by_propiedad(id_propiedad: int) -> List[ContratoBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(ContratoTable)
            .filter(ContratoTable.id_propiedad == id_propiedad)
            .all()
        )
        return [to_bo_contrato(o) for o in objs]
    finally:
        db.close()


def save_contrato(bo: ContratoBO) -> ContratoBO:
    db = SessionLocal()
    try:
        if bo.nro_contrato:
            db_obj = (
                db.query(ContratoTable)
                .filter(ContratoTable.nro_contrato == bo.nro_contrato)
                .first()
            )
            if db_obj:
                db_obj.fecha_solicitud = bo.fecha_solicitud
                db_obj.estado = bo.estado
                db_obj.fecha_contrato = bo.fecha_contrato
                db_obj.id_cliente = bo.id_cliente
                db_obj.id_agente = bo.id_agente
                db_obj.id_propiedad = bo.id_propiedad
                db_obj.monto = bo.monto
                db_obj.comision_porcentaje = bo.comision_porcentaje
                db_obj.comision_agente_porcentaje = bo.comision_agente_porcentaje
                db_obj.tipo_contrato = bo.tipo_contrato
                db_obj.ruta_documento_respaldo = bo.ruta_documento_respaldo
                db_obj.fecha_ultimo_aviso_mora = bo.fecha_ultimo_aviso_mora
                db_obj.recibos_sueldo_detalle = bo.recibos_sueldo_detalle
                db_obj.garantias_detalle = bo.garantias_detalle
                db_obj.ruta_recibos_sueldo = bo.ruta_recibos_sueldo
                db_obj.ruta_garantias = bo.ruta_garantias
                db_obj.decision_propietario = bo.decision_propietario
                db_obj.fecha_decision_propietario = bo.fecha_decision_propietario
                db_obj.observaciones_propietario = bo.observaciones_propietario
        else:
            db_obj = ContratoTable(
                fecha_solicitud=bo.fecha_solicitud,
                estado=bo.estado,
                fecha_contrato=bo.fecha_contrato,
                id_cliente=bo.id_cliente,
                id_agente=bo.id_agente,
                id_propiedad=bo.id_propiedad,
                monto=bo.monto,
                comision_porcentaje=bo.comision_porcentaje,
                comision_agente_porcentaje=bo.comision_agente_porcentaje,
                tipo_contrato=bo.tipo_contrato,
                ruta_documento_respaldo=bo.ruta_documento_respaldo,
                fecha_ultimo_aviso_mora=bo.fecha_ultimo_aviso_mora,
                recibos_sueldo_detalle=bo.recibos_sueldo_detalle,
                garantias_detalle=bo.garantias_detalle,
                ruta_recibos_sueldo=bo.ruta_recibos_sueldo,
                ruta_garantias=bo.ruta_garantias,
                decision_propietario=bo.decision_propietario,
                fecha_decision_propietario=bo.fecha_decision_propietario,
                observaciones_propietario=bo.observaciones_propietario,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_contrato(db_obj)
    finally:
        db.close()


def actualizar_ultimo_aviso_mora(
    nro_contrato: int, fecha: date
) -> Optional[ContratoBO]:
    db = SessionLocal()
    try:
        db_obj = (
            db.query(ContratoTable)
            .filter(ContratoTable.nro_contrato == nro_contrato)
            .first()
        )
        if db_obj:
            db_obj.fecha_ultimo_aviso_mora = fecha
            db.commit()
            db.refresh(db_obj)
            return to_bo_contrato(db_obj)
        return None
    finally:
        db.close()


def get_agente_asignado(
    id_agente: int, id_propiedad: int, desde: datetime
) -> Optional[AgenteAsignadoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(AgenteAsignadoTable)
            .filter(
                AgenteAsignadoTable.id_agente == id_agente,
                AgenteAsignadoTable.id_propiedad == id_propiedad,
                AgenteAsignadoTable.fecha_hora_desde == desde,
            )
            .first()
        )
        return to_bo_agente_asignado(obj)
    finally:
        db.close()


def get_active_agent_assignment_for_property(
    id_propiedad: int,
) -> Optional[AgenteAsignadoBO]:
    db = SessionLocal()
    try:
        now = datetime.now()
        obj = (
            db.query(AgenteAsignadoTable)
            .filter(
                AgenteAsignadoTable.id_propiedad == id_propiedad,
                AgenteAsignadoTable.fecha_hora_desde <= now,
                (AgenteAsignadoTable.fecha_hora_hasta.is_(None))
                | (AgenteAsignadoTable.fecha_hora_hasta >= now),
            )
            .first()
        )
        return to_bo_agente_asignado(obj)
    finally:
        db.close()


def get_active_assignments_by_agent(id_agente: int) -> List[AgenteAsignadoBO]:
    db = SessionLocal()
    try:
        now = datetime.now()
        objs = (
            db.query(AgenteAsignadoTable)
            .filter(
                AgenteAsignadoTable.id_agente == id_agente,
                AgenteAsignadoTable.fecha_hora_desde <= now,
                (AgenteAsignadoTable.fecha_hora_hasta.is_(None))
                | (AgenteAsignadoTable.fecha_hora_hasta >= now),
            )
            .all()
        )
        return [to_bo_agente_asignado(o) for o in objs]
    finally:
        db.close()


def save_agente_asignado(bo: AgenteAsignadoBO) -> AgenteAsignadoBO:
    db = SessionLocal()
    try:
        db_obj = (
            db.query(AgenteAsignadoTable)
            .filter(
                AgenteAsignadoTable.id_agente == bo.id_agente,
                AgenteAsignadoTable.id_propiedad == bo.id_propiedad,
                AgenteAsignadoTable.fecha_hora_desde == bo.fecha_hora_desde,
            )
            .first()
        )
        if db_obj:
            db_obj.fecha_hora_hasta = bo.fecha_hora_hasta
        else:
            db_obj = AgenteAsignadoTable(
                id_agente=bo.id_agente,
                id_propiedad=bo.id_propiedad,
                fecha_hora_desde=bo.fecha_hora_desde,
                fecha_hora_hasta=bo.fecha_hora_hasta,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_agente_asignado(db_obj)
    finally:
        db.close()


def list_asignaciones_by_propiedad(
    id_propiedad: int,
) -> List[AgenteAsignadoBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(AgenteAsignadoTable)
            .filter(AgenteAsignadoTable.id_propiedad == id_propiedad)
            .all()
        )
        return [to_bo_agente_asignado(o) for o in objs]
    finally:
        db.close()


def get_pago_inquilino_by_id(id_pago: int) -> Optional[PagoInquilinoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PagoInquilinoTable)
            .filter(PagoInquilinoTable.id == id_pago)
            .first()
        )
        return to_bo_pago_inquilino(obj)
    finally:
        db.close()


def save_pago_inquilino(bo: PagoInquilinoBO) -> PagoInquilinoBO:
    db = SessionLocal()
    try:
        if bo.id:
            db_obj = (
                db.query(PagoInquilinoTable)
                .filter(PagoInquilinoTable.id == bo.id)
                .first()
            )
            if db_obj:
                db_obj.nro_contrato = bo.nro_contrato
                db_obj.fecha_pago = bo.fecha_pago
                db_obj.monto = bo.monto
                db_obj.mes_correspondiente = bo.mes_correspondiente
                db_obj.fecha_vencimiento = bo.fecha_vencimiento
                db_obj.dias_retraso = bo.dias_retraso
                db_obj.monto_recargo = bo.monto_recargo
                db_obj.monto_total_abonado = bo.monto_total_abonado
                db_obj.ruta_comprobante = bo.ruta_comprobante
        else:
            db_obj = PagoInquilinoTable(
                nro_contrato=bo.nro_contrato,
                fecha_pago=bo.fecha_pago,
                monto=bo.monto,
                mes_correspondiente=bo.mes_correspondiente,
                fecha_vencimiento=bo.fecha_vencimiento,
                dias_retraso=bo.dias_retraso,
                monto_recargo=bo.monto_recargo,
                monto_total_abonado=bo.monto_total_abonado,
                ruta_comprobante=bo.ruta_comprobante,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_pago_inquilino(db_obj)
    finally:
        db.close()


def get_pago_propietario_by_id(id_pago: int) -> Optional[PagoPropietarioBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PagoPropietarioTable)
            .filter(PagoPropietarioTable.id == id_pago)
            .first()
        )
        return to_bo_pago_propietario(obj)
    finally:
        db.close()


def save_pago_propietario(bo: PagoPropietarioBO) -> PagoPropietarioBO:
    db = SessionLocal()
    try:
        if bo.id:
            db_obj = (
                db.query(PagoPropietarioTable)
                .filter(PagoPropietarioTable.id == bo.id)
                .first()
            )
            if db_obj:
                db_obj.id_propietario = bo.id_propietario
                db_obj.nro_contrato = bo.nro_contrato
                db_obj.fecha_liquidacion = bo.fecha_liquidacion
                db_obj.fecha_pago = bo.fecha_pago
                db_obj.mes_correspondiente = bo.mes_correspondiente
                db_obj.monto_bruto = bo.monto_bruto
                db_obj.comision = bo.comision
                db_obj.monto_neto = bo.monto_neto
                db_obj.estado = bo.estado
        else:
            db_obj = PagoPropietarioTable(
                id_propietario=bo.id_propietario,
                nro_contrato=bo.nro_contrato,
                fecha_liquidacion=bo.fecha_liquidacion,
                fecha_pago=bo.fecha_pago,
                mes_correspondiente=bo.mes_correspondiente,
                monto_bruto=bo.monto_bruto,
                comision=bo.comision,
                monto_neto=bo.monto_neto,
                estado=bo.estado,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_pago_propietario(db_obj)
    finally:
        db.close()


def list_pagos_inquilinos() -> List[PagoInquilinoBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(PagoInquilinoTable)
            .order_by(PagoInquilinoTable.fecha_pago.desc())
            .all()
        )
        return [to_bo_pago_inquilino(o) for o in objs]
    finally:
        db.close()


def list_pagos_propietarios() -> List[PagoPropietarioBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(PagoPropietarioTable)
            .order_by(PagoPropietarioTable.fecha_liquidacion.desc())
            .all()
        )
        return [to_bo_pago_propietario(o) for o in objs]
    finally:
        db.close()


def get_pago_inquilino_by_period(
    nro_contrato: int, mes: str
) -> Optional[PagoInquilinoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PagoInquilinoTable)
            .filter(
                PagoInquilinoTable.nro_contrato == nro_contrato,
                PagoInquilinoTable.mes_correspondiente == mes,
            )
            .first()
        )
        return to_bo_pago_inquilino(obj)
    finally:
        db.close()


def get_pago_propietario_by_period(
    nro_contrato: int, mes: str
) -> Optional[PagoPropietarioBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(PagoPropietarioTable)
            .filter(
                PagoPropietarioTable.nro_contrato == nro_contrato,
                PagoPropietarioTable.mes_correspondiente == mes,
            )
            .first()
        )
        return to_bo_pago_propietario(obj)
    finally:
        db.close()


def save_clausula(bo: ClausulaBO) -> ClausulaBO:
    db = SessionLocal()
    try:
        if bo.id:
            table_obj = (
                db.query(ClausulaTable)
                .filter(ClausulaTable.id == bo.id)
                .first()
            )
            if table_obj:
                table_obj.nro_contrato = bo.nro_contrato
                table_obj.orden = bo.orden
                table_obj.titulo = bo.titulo
                table_obj.contenido = bo.contenido
        else:
            table_obj = ClausulaTable(
                nro_contrato=bo.nro_contrato,
                orden=bo.orden,
                titulo=bo.titulo,
                contenido=bo.contenido,
            )
            db.add(table_obj)

        db.commit()
        db.refresh(table_obj)
        return to_bo_clausula(table_obj)
    finally:
        db.close()


def get_clausulas_by_contrato(nro_contrato: int) -> List[ClausulaBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(ClausulaTable)
            .filter(ClausulaTable.nro_contrato == nro_contrato)
            .order_by(ClausulaTable.orden.asc(), ClausulaTable.id.asc())
            .all()
        )
        return [to_bo_clausula(o) for o in objs]
    finally:
        db.close()


def get_clausula_by_id(id_clausula: int) -> Optional[ClausulaBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ClausulaTable)
            .filter(ClausulaTable.id == id_clausula)
            .first()
        )
        return to_bo_clausula(obj)
    finally:
        db.close()


def delete_clausula(id_clausula: int) -> bool:
    db = SessionLocal()
    try:
        obj = (
            db.query(ClausulaTable)
            .filter(ClausulaTable.id == id_clausula)
            .first()
        )
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False
    finally:
        db.close()


def update_contrato_comision(
    nro_contrato: int,
    comision_porcentaje: float,
    comision_agente_porcentaje: Optional[float] = None,
) -> Optional[ContratoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ContratoTable)
            .filter(ContratoTable.nro_contrato == nro_contrato)
            .first()
        )
        if obj:
            obj.comision_porcentaje = comision_porcentaje
            if comision_agente_porcentaje is not None:
                obj.comision_agente_porcentaje = comision_agente_porcentaje
            db.commit()
            db.refresh(obj)
            return to_bo_contrato(obj)
        return None
    finally:
        db.close()


# --- Agenda & Visitas Data Access ---


def save_agenda_visita(bo: AgendaVisitaBO) -> AgendaVisitaBO:
    db = SessionLocal()
    try:
        if bo.id:
            table_obj = (
                db.query(AgendaVisitaTable)
                .filter(AgendaVisitaTable.id == bo.id)
                .first()
            )
            if table_obj:
                table_obj.id_propiedad = bo.id_propiedad
                table_obj.id_agente = bo.id_agente
                table_obj.fecha_hora_visita = bo.fecha_hora_visita
                table_obj.duracion_minutos = bo.duracion_minutos
                table_obj.cupo_maximo = bo.cupo_maximo
                table_obj.estado = bo.estado
        else:
            table_obj = AgendaVisitaTable(
                id_propiedad=bo.id_propiedad,
                id_agente=bo.id_agente,
                fecha_hora_visita=bo.fecha_hora_visita,
                duracion_minutos=bo.duracion_minutos,
                cupo_maximo=bo.cupo_maximo,
                estado=bo.estado,
            )
            db.add(table_obj)

        db.commit()
        db.refresh(table_obj)
        return to_bo_agenda_visita(table_obj)
    finally:
        db.close()


def get_agenda_visita_by_id(id_agenda: int) -> Optional[AgendaVisitaBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(AgendaVisitaTable)
            .filter(AgendaVisitaTable.id == id_agenda)
            .first()
        )
        return to_bo_agenda_visita(obj)
    finally:
        db.close()


def list_agendas_visitas_by_propiedad(id_propiedad: int) -> List[AgendaVisitaBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(AgendaVisitaTable)
            .filter(AgendaVisitaTable.id_propiedad == id_propiedad)
            .order_by(AgendaVisitaTable.fecha_hora_visita.asc())
            .all()
        )
        return [to_bo_agenda_visita(o) for o in objs]
    finally:
        db.close()


def list_todas_agendas_visitas() -> List[AgendaVisitaBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(AgendaVisitaTable)
            .order_by(AgendaVisitaTable.fecha_hora_visita.asc())
            .all()
        )
        return [to_bo_agenda_visita(o) for o in objs]
    finally:
        db.close()


def save_inscripcion_visita(bo: InscripcionVisitaBO) -> InscripcionVisitaBO:
    db = SessionLocal()
    try:
        if bo.id:
            table_obj = (
                db.query(InscripcionVisitaTable)
                .filter(InscripcionVisitaTable.id == bo.id)
                .first()
            )
            if table_obj:
                table_obj.id_agenda = bo.id_agenda
                table_obj.id_cliente = bo.id_cliente
                table_obj.nombre_visitante = bo.nombre_visitante
                table_obj.telefono_visitante = bo.telefono_visitante
                table_obj.email_visitante = bo.email_visitante
                table_obj.observaciones = bo.observaciones
                table_obj.asistio = bo.asistio
        else:
            table_obj = InscripcionVisitaTable(
                id_agenda=bo.id_agenda,
                id_cliente=bo.id_cliente,
                nombre_visitante=bo.nombre_visitante,
                telefono_visitante=bo.telefono_visitante,
                email_visitante=bo.email_visitante,
                observaciones=bo.observaciones,
                fecha_registro=bo.fecha_registro or datetime.now(),
                asistio=bo.asistio,
            )
            db.add(table_obj)

        db.commit()
        db.refresh(table_obj)
        return to_bo_inscripcion_visita(table_obj)
    finally:
        db.close()


def list_inscripciones_by_agenda(id_agenda: int) -> List[InscripcionVisitaBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(InscripcionVisitaTable)
            .filter(InscripcionVisitaTable.id_agenda == id_agenda)
            .order_by(InscripcionVisitaTable.fecha_registro.asc())
            .all()
        )
        return [to_bo_inscripcion_visita(o) for o in objs]
    finally:
        db.close()


def count_inscripciones_by_agenda(id_agenda: int) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(InscripcionVisitaTable)
            .filter(InscripcionVisitaTable.id_agenda == id_agenda)
            .count()
        )
    finally:
        db.close()


# --- Reclamos Data Access ---


def save_reclamo(bo: ReclamoBO) -> ReclamoBO:
    db = SessionLocal()
    try:
        if bo.id:
            table_obj = (
                db.query(ReclamoTable)
                .filter(ReclamoTable.id == bo.id)
                .first()
            )
            if table_obj:
                table_obj.nro_contrato = bo.nro_contrato
                table_obj.id_propiedad = bo.id_propiedad
                table_obj.id_cliente = bo.id_cliente
                table_obj.fecha_reclamo = bo.fecha_reclamo
                table_obj.tipo_dano = bo.tipo_dano
                table_obj.descripcion = bo.descripcion
                table_obj.urgencia = bo.urgencia
                table_obj.presupuesto_estimado = bo.presupuesto_estimado
                table_obj.estado = bo.estado
                table_obj.observaciones_resolucion = bo.observaciones_resolucion
                table_obj.fecha_resolucion = bo.fecha_resolucion
        else:
            table_obj = ReclamoTable(
                nro_contrato=bo.nro_contrato,
                id_propiedad=bo.id_propiedad,
                id_cliente=bo.id_cliente,
                fecha_reclamo=bo.fecha_reclamo or date.today(),
                tipo_dano=bo.tipo_dano,
                descripcion=bo.descripcion,
                urgencia=bo.urgencia,
                presupuesto_estimado=bo.presupuesto_estimado,
                estado=bo.estado,
                observaciones_resolucion=bo.observaciones_resolucion,
                fecha_resolucion=bo.fecha_resolucion,
            )
            db.add(table_obj)

        db.commit()
        db.refresh(table_obj)
        return to_bo_reclamo(table_obj)
    finally:
        db.close()


def get_reclamo_by_id(id_reclamo: int) -> Optional[ReclamoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ReclamoTable)
            .filter(ReclamoTable.id == id_reclamo)
            .first()
        )
        return to_bo_reclamo(obj)
    finally:
        db.close()


def list_reclamos() -> List[ReclamoBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(ReclamoTable)
            .order_by(ReclamoTable.fecha_reclamo.desc(), ReclamoTable.id.desc())
            .all()
        )
        return [to_bo_reclamo(o) for o in objs]
    finally:
        db.close()


def list_reclamos_by_contrato(nro_contrato: int) -> List[ReclamoBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(ReclamoTable)
            .filter(ReclamoTable.nro_contrato == nro_contrato)
            .order_by(ReclamoTable.fecha_reclamo.desc())
            .all()
        )
        return [to_bo_reclamo(o) for o in objs]
    finally:
        db.close()


def save_audit_log(bo: AuditLogBO) -> AuditLogBO:
    db = SessionLocal()
    try:
        table_obj = AuditLogTable(
            fecha_hora=bo.fecha_hora,
            id_agente=bo.id_agente,
            entidad=bo.entidad,
            id_entidad=bo.id_entidad,
            accion=bo.accion,
            descripcion=bo.descripcion,
        )
        db.add(table_obj)
        db.commit()
        db.refresh(table_obj)
        return to_bo_audit_log(table_obj)
    finally:
        db.close()


def list_audit_logs() -> List[AuditLogBO]:
    db = SessionLocal()
    try:
        objs = (
            db.query(AuditLogTable)
            .order_by(AuditLogTable.fecha_hora.desc(), AuditLogTable.id.desc())
            .all()
        )
        return [to_bo_audit_log(o) for o in objs]
    finally:
        db.close()


def get_inscripcion_visita_by_id(id_inscripcion: int) -> Optional[InscripcionVisitaBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(InscripcionVisitaTable)
            .filter(InscripcionVisitaTable.id == id_inscripcion)
            .first()
        )
        return to_bo_inscripcion_visita(obj)
    finally:
        db.close()


def delete_inscripcion_visita(id_inscripcion: int) -> bool:
    db = SessionLocal()
    try:
        obj = (
            db.query(InscripcionVisitaTable)
            .filter(InscripcionVisitaTable.id == id_inscripcion)
            .first()
        )
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False
    finally:
        db.close()


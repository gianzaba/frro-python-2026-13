import os
from dotenv import load_dotenv
from datetime import date, datetime
from typing import List, Optional

load_dotenv()

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DateTime,
    Numeric,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Import Business Objects
from business.entities import (
    Cliente as ClienteBO,
    Propietario as PropietarioBO,
    Agente as AgenteBO,
    Propiedad as PropiedadBO,
    Contrato as ContratoBO,
    AgenteAsignado as AgenteAsignadoBO,
    PagoInquilino as PagoInquilinoBO,
    PagoPropietario as PagoPropietarioBO,
    Clausula as ClausulaBO,
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

    __mapper_args__ = {
        "polymorphic_identity": "cliente",
    }


class PropietarioTable(PersonaTable):
    __tablename__ = "propietario"

    id = Column(Integer, ForeignKey("persona.id"), primary_key=True)

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
    )  # disponible, alquilada, vendida
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
    )  # solicitado, activo, finalizado, cancelado
    fecha_contrato = Column(Date, nullable=True)
    id_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    id_agente = Column(Integer, ForeignKey("agente.id"), nullable=False)
    id_propiedad = Column(Integer, ForeignKey("propiedad.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False, default=0.0)
    comision_porcentaje = Column(Numeric(5, 2), nullable=False, default=10.0)
    tipo_contrato = Column(String(50), default="Alquiler", nullable=False)  # Alquiler / Compraventa
    ruta_documento_respaldo = Column(String(500), nullable=True)

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
    mes_correspondiente = Column(String(7), nullable=False)  # "YYYY-MM"

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
    mes_correspondiente = Column(String(7), nullable=False)  # "YYYY-MM"
    monto_bruto = Column(Numeric(12, 2), nullable=False)
    comision = Column(Numeric(12, 2), nullable=False)
    monto_neto = Column(Numeric(12, 2), nullable=False)
    estado = Column(
        String(20), default="pendiente", nullable=False
    )  # pendiente, pagado

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
        ]
        
        needs_recreate = False
        for tbl in required_tables:
            if tbl not in existing_tables:
                needs_recreate = True
                break
        
        if not needs_recreate and "agente" in existing_tables:
            cols = [c["name"] for c in inspector.get_columns("agente")]
            if "rol" not in cols:
                needs_recreate = True
                
        if not needs_recreate and "propiedad" in existing_tables:
            cols = [c["name"] for c in inspector.get_columns("propiedad")]
            if "fecha_disponibilidad" not in cols:
                needs_recreate = True

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
        tipo_contrato=getattr(db_obj, "tipo_contrato", "Alquiler") or "Alquiler",
        ruta_documento_respaldo=getattr(db_obj, "ruta_documento_respaldo", None),
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
            db.query(ClienteTable).filter(ClienteTable.email == email).first()
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
                db.query(ClienteTable).filter(ClienteTable.id == bo.id).first()
            )
            if db_obj:
                db_obj.tipo_doc = bo.tipo_doc
                db_obj.nro_doc = bo.nro_doc
                db_obj.nombre = bo.nombre
                db_obj.apellido = bo.apellido
                db_obj.domicilio = bo.domicilio
                db_obj.telefono = bo.telefono
                db_obj.email = bo.email
                if bo.contrasegna_hash:
                    db_obj.contrasegna_hash = bo.contrasegna_hash
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
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_cliente(db_obj)
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
                if bo.contrasegna_hash:
                    db_obj.contrasegna_hash = bo.contrasegna_hash
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
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_propietario(db_obj)
    finally:
        db.close()


def get_agente_by_id(id_agente: int) -> Optional[AgenteBO]:
    db = SessionLocal()
    try:
        obj = db.query(AgenteTable).filter(AgenteTable.id == id_agente).first()
        return to_bo_agente(obj)
    finally:
        db.close()


def get_agente_by_email(email: str) -> Optional[AgenteBO]:
    db = SessionLocal()
    try:
        obj = db.query(AgenteTable).filter(AgenteTable.email == email).first()
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
                db_obj.cuil = bo.cuil
                db_obj.matricula = bo.matricula
                db_obj.rol = bo.rol
                if bo.contrasegna_hash:
                    db_obj.contrasegna_hash = bo.contrasegna_hash
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
                fecha_disponibilidad=bo.fecha_disponibilidad or date.today(),
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_propiedad(db_obj)
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
                db_obj.tipo_contrato = bo.tipo_contrato
                db_obj.ruta_documento_respaldo = bo.ruta_documento_respaldo
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
                tipo_contrato=bo.tipo_contrato,
                ruta_documento_respaldo=bo.ruta_documento_respaldo,
            )
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return to_bo_contrato(db_obj)
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
        return to_bo_agente_asignado(db_obj)
    finally:
        db.close()


# List helper queries to feed view lists


def list_clientes() -> List[ClienteBO]:
    db = SessionLocal()
    try:
        objs = db.query(ClienteTable).all()
        return [to_bo_cliente(o) for o in objs]
    finally:
        db.close()


def list_propietarios() -> List[PropietarioBO]:
    db = SessionLocal()
    try:
        objs = db.query(PropietarioTable).all()
        return [to_bo_propietario(o) for o in objs]
    finally:
        db.close()


def list_agentes() -> List[AgenteBO]:
    db = SessionLocal()
    try:
        objs = db.query(AgenteTable).all()
        return [to_bo_agente(o) for o in objs]
    finally:
        db.close()


def list_propiedades() -> List[PropiedadBO]:
    db = SessionLocal()
    try:
        objs = db.query(PropiedadTable).all()
        return [to_bo_propiedad(o) for o in objs]
    finally:
        db.close()


def list_contratos() -> List[ContratoBO]:
    db = SessionLocal()
    try:
        objs = db.query(ContratoTable).all()
        return [to_bo_contrato(o) for o in objs]
    finally:
        db.close()


def list_active_agent_assignments() -> List[AgenteAsignadoBO]:
    db = SessionLocal()
    try:
        now = datetime.now()
        objs = (
            db.query(AgenteAsignadoTable)
            .filter(
                (AgenteAsignadoTable.fecha_hora_hasta.is_(None))
                | (AgenteAsignadoTable.fecha_hora_hasta >= now)
            )
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
        else:
            db_obj = PagoInquilinoTable(
                nro_contrato=bo.nro_contrato,
                fecha_pago=bo.fecha_pago,
                monto=bo.monto,
                mes_correspondiente=bo.mes_correspondiente,
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
    nro_contrato: int, nueva_comision: float
) -> Optional[ContratoBO]:
    db = SessionLocal()
    try:
        obj = (
            db.query(ContratoTable)
            .filter(ContratoTable.nro_contrato == nro_contrato)
            .first()
        )
        if obj:
            obj.comision_porcentaje = nueva_comision
            db.commit()
            db.refresh(obj)
            return to_bo_contrato(obj)
        return None
    finally:
        db.close()


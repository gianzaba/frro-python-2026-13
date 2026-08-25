from datetime import date, datetime
from typing import Optional


class Persona:
    def __init__(
        self,
        id: Optional[int] = None,
        tipo_doc: str = "",
        nro_doc: str = "",
        nombre: str = "",
        apellido: str = "",
        domicilio: str = "",
        telefono: str = "",
        email: str = "",
        contrasegna_hash: str = "",
    ):
        self.id = id
        self.tipo_doc = tipo_doc
        self.nro_doc = nro_doc
        self.nombre = nombre
        self.apellido = apellido
        self.domicilio = domicilio
        self.telefono = telefono
        self.email = email
        self.contrasegna_hash = contrasegna_hash

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


class Cliente(Persona):
    pass


class Propietario(Persona):
    pass


class Agente(Persona):
    def __init__(
        self,
        id: Optional[int] = None,
        tipo_doc: str = "",
        nro_doc: str = "",
        nombre: str = "",
        apellido: str = "",
        domicilio: str = "",
        telefono: str = "",
        email: str = "",
        contrasegna_hash: str = "",
        cuil: str = "",
        matricula: str = "",
        rol: str = "Estándar",
    ):
        super().__init__(
            id=id,
            tipo_doc=tipo_doc,
            nro_doc=nro_doc,
            nombre=nombre,
            apellido=apellido,
            domicilio=domicilio,
            telefono=telefono,
            email=email,
            contrasegna_hash=contrasegna_hash,
        )
        self.cuil = cuil
        self.matricula = matricula
        self.rol = rol


class Propiedad:
    def __init__(
        self,
        id: Optional[int] = None,
        direccion: str = "",
        tipo: str = "",
        zona: str = "",
        estado: str = "disponible",
        id_propietario: int = 0,
        fecha_disponibilidad: Optional[date] = None,
    ):
        self.id = id
        self.direccion = direccion
        self.tipo = tipo
        self.zona = zona
        self.estado = estado
        self.id_propietario = id_propietario
        self.fecha_disponibilidad = fecha_disponibilidad or date.today()


class Contrato:
    def __init__(
        self,
        nro_contrato: Optional[int] = None,
        fecha_solicitud: Optional[date] = None,
        estado: str = "solicitado",
        fecha_contrato: Optional[date] = None,
        id_cliente: int = 0,
        id_agente: int = 0,
        id_propiedad: int = 0,
        monto: float = 0.0,
        comision_porcentaje: float = 10.0,
        comision_agente_porcentaje: float = 3.0,
        tipo_contrato: str = "Alquiler",
        ruta_documento_respaldo: Optional[str] = None,
        fecha_ultimo_aviso_mora: Optional[date] = None,
    ):
        self.nro_contrato = nro_contrato
        self.fecha_solicitud = fecha_solicitud or date.today()
        self.estado = estado
        self.fecha_contrato = fecha_contrato
        self.id_cliente = id_cliente
        self.id_agente = id_agente
        self.id_propiedad = id_propiedad
        self.monto = monto
        self.comision_porcentaje = comision_porcentaje
        self.comision_agente_porcentaje = comision_agente_porcentaje
        self.tipo_contrato = tipo_contrato
        self.ruta_documento_respaldo = ruta_documento_respaldo
        self.fecha_ultimo_aviso_mora = fecha_ultimo_aviso_mora

    @property
    def monto_honorarios_totales(self) -> float:
        return round(self.monto * (self.comision_porcentaje / 100.0), 2)

    @property
    def monto_comision_agente(self) -> float:
        return round(self.monto * (self.comision_agente_porcentaje / 100.0), 2)

    @property
    def monto_comision_inmobiliaria(self) -> float:
        return round(
            max(0.0, self.monto_honorarios_totales - self.monto_comision_agente),
            2,
        )


class Clausula:
    def __init__(
        self,
        id: Optional[int] = None,
        nro_contrato: int = 0,
        orden: int = 1,
        titulo: str = "",
        contenido: str = "",
    ):
        self.id = id
        self.nro_contrato = nro_contrato
        self.orden = orden
        self.titulo = titulo
        self.contenido = contenido


class AgenteAsignado:
    def __init__(
        self,
        id_agente: int,
        id_propiedad: int,
        fecha_hora_desde: datetime,
        fecha_hora_hasta: Optional[datetime] = None,
    ):
        self.id_agente = id_agente
        self.id_propiedad = id_propiedad
        self.fecha_hora_desde = fecha_hora_desde
        self.fecha_hora_hasta = fecha_hora_hasta


class PagoInquilino:
    def __init__(
        self,
        id: Optional[int] = None,
        nro_contrato: int = 0,
        fecha_pago: Optional[date] = None,
        monto: float = 0.0,
        mes_correspondiente: str = "",
        fecha_vencimiento: Optional[date] = None,
        dias_retraso: int = 0,
        monto_recargo: float = 0.0,
        monto_total_abonado: Optional[float] = None,
        ruta_comprobante: Optional[str] = None,
    ):
        self.id = id
        self.nro_contrato = nro_contrato
        self.fecha_pago = fecha_pago or date.today()
        self.monto = monto
        self.mes_correspondiente = mes_correspondiente
        self.fecha_vencimiento = fecha_vencimiento
        self.dias_retraso = dias_retraso
        self.monto_recargo = monto_recargo
        self.monto_total_abonado = (
            monto_total_abonado
            if monto_total_abonado is not None
            else round(monto + monto_recargo, 2)
        )
        self.ruta_comprobante = ruta_comprobante


class PagoPropietario:
    def __init__(
        self,
        id: Optional[int] = None,
        id_propietario: int = 0,
        nro_contrato: int = 0,
        fecha_liquidacion: Optional[date] = None,
        fecha_pago: Optional[date] = None,
        mes_correspondiente: str = "",
        monto_bruto: float = 0.0,
        comision: float = 0.0,
        monto_neto: float = 0.0,
        estado: str = "pendiente",
    ):
        self.id = id
        self.id_propietario = id_propietario
        self.nro_contrato = nro_contrato
        self.fecha_liquidacion = fecha_liquidacion or date.today()
        self.fecha_pago = fecha_pago
        self.mes_correspondiente = mes_correspondiente
        self.monto_bruto = monto_bruto
        self.comision = comision
        self.monto_neto = monto_neto
        self.estado = estado


class AgendaVisita:
    def __init__(
        self,
        id: Optional[int] = None,
        id_propiedad: int = 0,
        id_agente: int = 0,
        fecha_hora_visita: Optional[datetime] = None,
        duracion_minutos: int = 30,
        cupo_maximo: int = 3,
        estado: str = "disponible",
    ):
        self.id = id
        self.id_propiedad = id_propiedad
        self.id_agente = id_agente
        self.fecha_hora_visita = fecha_hora_visita or datetime.now()
        self.duracion_minutos = duracion_minutos
        self.cupo_maximo = cupo_maximo
        self.estado = estado


class InscripcionVisita:
    def __init__(
        self,
        id: Optional[int] = None,
        id_agenda: int = 0,
        id_cliente: Optional[int] = None,
        nombre_visitante: str = "",
        telefono_visitante: str = "",
        email_visitante: str = "",
        observaciones: str = "",
        fecha_registro: Optional[datetime] = None,
        asistio: Optional[bool] = None,
    ):
        self.id = id
        self.id_agenda = id_agenda
        self.id_cliente = id_cliente
        self.nombre_visitante = nombre_visitante
        self.telefono_visitante = telefono_visitante
        self.email_visitante = email_visitante
        self.observaciones = observaciones
        self.fecha_registro = fecha_registro or datetime.now()
        self.asistio = asistio


class Reclamo:
    def __init__(
        self,
        id: Optional[int] = None,
        nro_contrato: int = 0,
        id_propiedad: int = 0,
        id_cliente: int = 0,
        fecha_reclamo: Optional[date] = None,
        tipo_dano: str = "Estructural",
        descripcion: str = "",
        urgencia: str = "Media",
        presupuesto_estimado: float = 0.0,
        estado: str = "pendiente",
        observaciones_resolucion: str = "",
        fecha_resolucion: Optional[date] = None,
    ):
        self.id = id
        self.nro_contrato = nro_contrato
        self.id_propiedad = id_propiedad
        self.id_cliente = id_cliente
        self.fecha_reclamo = fecha_reclamo or date.today()
        self.tipo_dano = tipo_dano
        self.descripcion = descripcion
        self.urgencia = urgencia
        self.presupuesto_estimado = presupuesto_estimado
        self.estado = estado
        self.observaciones_resolucion = observaciones_resolucion
        self.fecha_resolucion = fecha_resolucion

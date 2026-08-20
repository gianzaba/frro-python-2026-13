from typing import Optional
from datetime import date, datetime


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
        return f"{self.nombre} {self.apellido}"


class Cliente(Persona):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Propietario(Persona):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Agente(Persona):
    def __init__(
        self,
        cuil: str = "",
        matricula: str = "",
        rol: str = "Estándar",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
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
        id_propietario: Optional[int] = None,
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
        id_cliente: Optional[int] = None,
        id_agente: Optional[int] = None,
        id_propiedad: Optional[int] = None,
        monto: float = 0.0,
        comision_porcentaje: float = 10.0,
        tipo_contrato: str = "Alquiler",
        ruta_documento_respaldo: Optional[str] = None,
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
        self.tipo_contrato = tipo_contrato
        self.ruta_documento_respaldo = ruta_documento_respaldo

    @property
    def monto_comision_agente(self) -> float:
        """Calcula el monto que cobra el agente al celebrarse el contrato."""
        return round(self.monto * (self.comision_porcentaje / 100.0), 2)


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
    ):
        self.id = id
        self.nro_contrato = nro_contrato
        self.fecha_pago = fecha_pago or date.today()
        self.monto = monto
        self.mes_correspondiente = mes_correspondiente


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

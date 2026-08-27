import os
import smtplib
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from werkzeug.security import generate_password_hash, check_password_hash

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
    AgendaVisita as AgendaVisitaBO,
    InscripcionVisita as InscripcionVisitaBO,
    Reclamo as ReclamoBO,
    AuditLog as AuditLogBO,
)

# Import Data Access Layer
import datos.db as db

# --- Business Logic & Controller API ---


def autenticar_agente(email: str, password: str) -> Optional[AgenteBO]:
    """
    Autentica a un agente usando su email y contraseña.
    Devuelve el AgenteBO si la autenticación es exitosa, sino None.
    """
    agente = db.get_agente_by_email(email)
    if not agente:
        return None
    if check_password_hash(agente.contrasegna_hash, password):
        return agente
    return None


def es_administrador(id_agente: Optional[int]) -> bool:
    """
    Verifica si el agente especificado tiene el rol de Administrador.
    """
    if not id_agente:
        return False
    agente = db.get_agente_by_id(id_agente)
    return agente is not None and agente.rol == "Administrador"


def registrar_agente(
    nombre: str,
    apellido: str,
    email: str,
    password: str,
    cuil: str,
    matricula: str,
    tipo_doc: str,
    nro_doc: str,
    domicilio: str,
    telefono: str,
    rol: str = "Estándar",
) -> AgenteBO:
    """
    Registra un nuevo agente con contraseña encriptada y asignación de rol.
    """
    existing = db.get_agente_by_email(email)
    if existing:
        raise ValueError("Ya existe un agente con ese correo electrónico.")

    hash_pwd = generate_password_hash(password)
    bo = AgenteBO(
        id=None,
        tipo_doc=tipo_doc,
        nro_doc=nro_doc,
        nombre=nombre,
        apellido=apellido,
        domicilio=domicilio,
        telefono=telefono,
        email=email,
        contrasegna_hash=hash_pwd,
        cuil=cuil,
        matricula=matricula,
        rol=rol,
    )
    return db.save_agente(bo)


def registrar_cliente(
    nombre: str,
    apellido: str,
    email: str,
    tipo_doc: str,
    nro_doc: str,
    domicilio: str,
    telefono: str,
) -> ClienteBO:
    """
    Registra un nuevo cliente interesado en contratos.
    """
    existing = db.get_cliente_by_doc(tipo_doc, nro_doc)
    if existing:
        raise ValueError(
            "Ya existe un cliente con ese tipo y número de documento."
        )

    bo = ClienteBO(
        id=None,
        tipo_doc=tipo_doc,
        nro_doc=nro_doc,
        nombre=nombre,
        apellido=apellido,
        domicilio=domicilio,
        telefono=telefono,
        email=email,
        contrasegna_hash="",
    )
    return db.save_cliente(bo)


def registrar_propietario(
    nombre: str,
    apellido: str,
    email: str,
    tipo_doc: str,
    nro_doc: str,
    domicilio: str,
    telefono: str,
) -> PropietarioBO:
    """
    Registra un nuevo propietario de inmuebles.
    """
    existing = db.get_propietario_by_doc(tipo_doc, nro_doc)
    if existing:
        raise ValueError(
            "Ya existe un propietario con ese tipo y número de documento."
        )

    bo = PropietarioBO(
        id=None,
        tipo_doc=tipo_doc,
        nro_doc=nro_doc,
        nombre=nombre,
        apellido=apellido,
        domicilio=domicilio,
        telefono=telefono,
        email=email,
        contrasegna_hash="",
    )
    return db.save_propietario(bo)


def registrar_propiedad(
    direccion: str,
    tipo: str,
    zona: str,
    id_propietario: int,
    fecha_disponibilidad: Optional[date] = None,
) -> PropiedadBO:
    """
    Registra una nueva propiedad en la inmobiliaria.
    """
    propietario = db.get_propietario_by_id(id_propietario)
    if not propietario:
        raise ValueError("El propietario especificado no existe.")

    bo = PropiedadBO(
        id=None,
        direccion=direccion,
        tipo=tipo,
        zona=zona,
        estado="disponible",
        id_propietario=id_propietario,
        fecha_disponibilidad=fecha_disponibilidad or date.today(),
    )
    return db.save_propiedad(bo)


def asignar_agente_a_propiedad(
    id_agente: int,
    id_propiedad: int,
    desde: datetime,
    hasta: Optional[datetime] = None,
) -> AgenteAsignadoBO:
    """
    Asigna un agente a una propiedad disponible. Un agente puede gestionar múltiples propiedades.
    """
    agente = db.get_agente_by_id(id_agente)
    if not agente:
        raise ValueError("El agente especificado no existe.")

    propiedad = db.get_propiedad_by_id(id_propiedad)
    if not propiedad:
        raise ValueError("La propiedad especificada no existe.")

    if propiedad.estado != "disponible":
        raise ValueError(
            "Solo se pueden asignar agentes a propiedades con estado 'disponible'."
        )

    if hasta and hasta <= desde:
        raise ValueError("La fecha/hora 'hasta' debe ser posterior a 'desde'.")

    current_prop_assignment = db.get_active_agent_assignment_for_property(
        id_propiedad
    )
    if current_prop_assignment:
        current_prop_assignment.fecha_hora_hasta = desde
        db.save_agente_asignado(current_prop_assignment)

    bo = AgenteAsignadoBO(
        id_agente=id_agente,
        id_propiedad=id_propiedad,
        fecha_hora_desde=desde,
        fecha_hora_hasta=hasta,
    )
    return db.save_agente_asignado(bo)


def solicitar_contrato(
    id_cliente: int,
    id_agente: int,
    id_propiedad: int,
    monto: float = 0.0,
    comision_porcentaje: float = 10.0,
    comision_agente_porcentaje: float = 3.0,
    tipo_contrato: str = "Alquiler",
    ruta_documento_respaldo: Optional[str] = None,
) -> ContratoBO:
    """
    Solicita un nuevo contrato.
    Valida cliente, propiedad disponible y que el agente sea el asignado actualmente.
    """
    cliente = db.get_cliente_by_id(id_cliente)
    if not cliente:
        raise ValueError("El cliente especificado no existe.")

    agente = db.get_agente_by_id(id_agente)
    if not agente:
        raise ValueError("El agente especificado no existe.")

    propiedad = db.get_propiedad_by_id(id_propiedad)
    if not propiedad:
        raise ValueError("La propiedad especificada no existe.")

    if propiedad.estado != "disponible":
        raise ValueError(
            "Solo se pueden solicitar contratos para propiedades disponibles."
        )

    active_assignment = db.get_active_agent_assignment_for_property(
        id_propiedad
    )
    if not active_assignment or active_assignment.id_agente != id_agente:
        raise ValueError(
            f"El agente {agente.nombre_completo} no está asignado actualmente a esta propiedad."
        )

    bo = ContratoBO(
        nro_contrato=None,
        fecha_solicitud=date.today(),
        estado="solicitado",
        fecha_contrato=None,
        id_cliente=id_cliente,
        id_agente=id_agente,
        id_propiedad=id_propiedad,
        monto=monto,
        comision_porcentaje=comision_porcentaje,
        comision_agente_porcentaje=comision_agente_porcentaje,
        tipo_contrato=tipo_contrato,
        ruta_documento_respaldo=ruta_documento_respaldo,
    )
    saved_contrato = db.save_contrato(bo)
    cargar_clausulas_predeterminadas(saved_contrato.nro_contrato, tipo_contrato)
    return saved_contrato


def firmar_contrato(
    nro_contrato: int,
    fecha_contrato: Optional[date] = None,
    id_agente_solicitante: Optional[int] = None,
) -> ContratoBO:
    """
    Firma un contrato.
    Actualiza el estado del contrato a 'activo' y el estado de la propiedad.
    Inmuta cláusulas y parámetros.
    """
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")

    if contrato.estado != "solicitado":
        raise ValueError(
            "Solo se pueden firmar contratos en estado 'solicitado'."
        )

    propiedad = db.get_propiedad_by_id(contrato.id_propiedad)
    if not propiedad:
        raise ValueError("La propiedad asociada al contrato no existe.")

    if propiedad.estado != "disponible":
        raise ValueError(
            "La propiedad no está disponible para firmar este contrato."
        )

    contrato.estado = "activo"
    contrato.fecha_contrato = fecha_contrato or date.today()
    saved_contrato = db.save_contrato(contrato)

    if contrato.tipo_contrato.lower() == "alquiler":
        propiedad.estado = "alquilada"
    else:
        propiedad.estado = "vendida"
    db.save_propiedad(propiedad)

    agente_nombre = "Sistema"
    if id_agente_solicitante:
        ag = db.get_agente_by_id(id_agente_solicitante)
        if ag:
            agente_nombre = ag.nombre_completo

    registrar_log_auditoria(
        id_agente=id_agente_solicitante,
        entidad="Contrato",
        id_entidad=nro_contrato,
        accion="Firmar",
        descripcion=f"El agente {agente_nombre} firmó el contrato #{nro_contrato} de tipo {contrato.tipo_contrato} (Propiedad: {propiedad.direccion})."
    )

    return saved_contrato


def cargar_clausulas_predeterminadas(
    nro_contrato: int, tipo_contrato: str = "Alquiler"
) -> List[ClausulaBO]:
    """
    Carga el cuerpo de cláusulas legales predeterminadas para un contrato.
    """
    clausulas_base = []
    if tipo_contrato.lower() == "alquiler":
        clausulas_base = [
            (
                1,
                "PRIMERA (OBJETO Y DESTINO)",
                "El LOCADOR cede en locación al LOCATARIO y éste acepta, el inmueble individualizado "
                "en este acuerdo, con destino exclusivo a vivienda familiar habitual.",
            ),
            (
                2,
                "SEGUNDA (PLAZO)",
                "El término de duración del presente contrato se fija de común acuerdo, comenzando a "
                "regir a partir de la fecha de suscripción del acuerdo y toma de posesión.",
            ),
            (
                3,
                "TERCERA (PRECIO Y PAGO)",
                "El precio del alquiler mensual se estipula en la suma pactada en la carátula, debiendo "
                "abonarse por adelantado del 1 al 10 de cada mes calendario.",
            ),
            (
                4,
                "CUARTA (SERVICIOS Y EXPENSAS)",
                "Estarán a cargo exclusivo del LOCATARIO el pago de los servicios de energía eléctrica, "
                "gas natural, agua corriente, tasas de servicios y las expensas ordinarias.",
            ),
            (
                5,
                "QUINTA (ESTADO DEL INMUEBLE)",
                "El LOCATARIO declara recibir el inmueble en perfecto estado de conservación, uso y aseo, "
                "obligándose a restituirlo en las mismas condiciones al finalizar el vínculo.",
            ),
            (
                6,
                "SEXTA (PROHIBICIÓN DE MODIFICACIONES)",
                "Queda expresamente prohibido al LOCATARIO realizar modificaciones o mejoras estructurales "
                "en el inmueble sin autorización previa y por escrito del LOCADOR.",
            ),
            (
                7,
                "SÉPTIMA (HONORARIOS DE INTERMEDIACIÓN)",
                "Las partes dejan constancia de la intermediación profesional de la inmobiliaria interviniente, "
                "obligándose al pago de los honorarios profesionales correspondientes.",
            ),
        ]
    else:
        clausulas_base = [
            (
                1,
                "PRIMERA (COMPRAVENTA)",
                "El VENDEDOR vende y transfiere al COMPRADOR, quien acepta y adquiere, el bien inmueble "
                "individualizado en este instrumento libre de todo gravamen, embargo o inhibición.",
            ),
            (
                2,
                "SEGUNDA (PRECIO Y FORMA DE PAGO)",
                "El precio total y convenido de la compraventa se fija en el monto consignado en la carátula, "
                "abonándose en los plazos e instrumentos acordados entre las partes.",
            ),
            (
                3,
                "TERCERA (ESCRITURACIÓN)",
                "La escritura traslativa de dominio se otorgará ante el escribano público designado "
                "una vez cancelada la totalidad del precio y satisfechos los certificados de ley.",
            ),
            (
                4,
                "CUARTA (POSESIÓN)",
                "La posesión real, material y pacífica del inmueble se entregará al COMPRADOR en el acto "
                "de firma de la escritura o según acta de entrega de posesión suscripta conjuntamente.",
            ),
            (
                5,
                "QUINTA (HONORARIOS DE INTERMEDIACIÓN)",
                "Las partes reconocen la labor de intermediación inmobiliaria y asumen el pago de los honorarios "
                "pactados según lo establecido en el presente acuerdo.",
            ),
        ]

    saved_clausulas = []
    for orden, titulo, contenido in clausulas_base:
        cl_bo = ClausulaBO(
            id=None,
            nro_contrato=nro_contrato,
            orden=orden,
            titulo=titulo,
            contenido=contenido,
        )
        saved_clausulas.append(db.save_clausula(cl_bo))
    return saved_clausulas


def listar_clausulas_contrato(nro_contrato: int) -> List[ClausulaBO]:
    return db.get_clausulas_by_contrato(nro_contrato)


def agregar_clausula_contrato(
    nro_contrato: int, titulo: str, contenido: str, orden: Optional[int] = None
) -> ClausulaBO:
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")
    if contrato.estado != "solicitado":
        raise ValueError(
            "El contrato ya ha sido firmado. No se pueden modificar ni agregar cláusulas en un contrato firmado."
        )

    if orden is None:
        existentes = db.get_clausulas_by_contrato(nro_contrato)
        orden = len(existentes) + 1

    cl_bo = ClausulaBO(
        id=None,
        nro_contrato=nro_contrato,
        orden=orden,
        titulo=titulo,
        contenido=contenido,
    )
    return db.save_clausula(cl_bo)


def editar_clausula_contrato(
    nro_contrato_or_id: int,
    id_clausula_or_titulo: any,
    titulo_or_contenido: str = "",
    contenido: Optional[str] = None,
) -> ClausulaBO:
    if contenido is not None:
        nro_contrato = nro_contrato_or_id
        id_clausula = id_clausula_or_titulo
        titulo = titulo_or_contenido
        contenido_real = contenido
    else:
        id_clausula = nro_contrato_or_id
        titulo = id_clausula_or_titulo
        contenido_real = titulo_or_contenido
        nro_contrato = None

    cl = db.get_clausula_by_id(id_clausula)
    if not cl:
        raise ValueError("La cláusula especificada no existe.")

    contrato = db.get_contrato_by_id(cl.nro_contrato)
    if not contrato or contrato.estado != "solicitado":
        raise ValueError(
            "El contrato ya ha sido firmado. No se pueden modificar cláusulas en un contrato firmado o inactivo."
        )

    if nro_contrato and cl.nro_contrato != nro_contrato:
        raise ValueError("La cláusula especificada no existe en este contrato.")

    cl.titulo = titulo
    cl.contenido = contenido_real
    return db.save_clausula(cl)


def modificar_clausula_contrato(
    id_clausula: int, titulo: str, contenido: str
) -> ClausulaBO:
    """
    Alias compatible para modificar una cláusula.
    """
    return editar_clausula_contrato(id_clausula, titulo, contenido)


def eliminar_clausula_contrato(
    id_or_nro: int, id_clausula_opt: Optional[int] = None
) -> bool:
    if id_clausula_opt is not None:
        id_clausula = id_clausula_opt
    else:
        id_clausula = id_or_nro

    cl = db.get_clausula_by_id(id_clausula)
    if not cl:
        raise ValueError("La cláusula especificada no existe.")

    contrato = db.get_contrato_by_id(cl.nro_contrato)
    if not contrato or contrato.estado != "solicitado":
        raise ValueError(
            "El contrato ya ha sido firmado. No se pueden eliminar cláusulas en un contrato firmado o inactivo."
        )

    return db.delete_clausula(id_clausula)


def modificar_comisiones_contrato(
    nro_contrato: int,
    comision_porcentaje: float,
    comision_agente_porcentaje: Optional[float] = None,
) -> ContratoBO:
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")
    if contrato.estado != "solicitado":
        raise ValueError(
            "El contrato ya ha sido firmado. No se pueden modificar honorarios en un contrato ya firmado."
        )

    if comision_porcentaje < 0 or (
        comision_agente_porcentaje is not None and comision_agente_porcentaje < 0
    ):
        raise ValueError("Los porcentajes de comisión no pueden ser negativos.")

    updated = db.update_contrato_comision(
        nro_contrato, comision_porcentaje, comision_agente_porcentaje
    )
    return updated or contrato


def actualizar_comision_contrato(
    nro_contrato: int,
    comision_porcentaje: float,
    comision_agente_porcentaje: Optional[float] = None,
) -> ContratoBO:
    """
    Alias compatible con tests para modificar comisiones de un contrato.
    """
    return modificar_comisiones_contrato(
        nro_contrato, comision_porcentaje, comision_agente_porcentaje
    )


def obtener_detalle_contrato(nro_contrato: int) -> dict:
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")

    cliente = db.get_cliente_by_id(contrato.id_cliente)
    agente = db.get_agente_by_id(contrato.id_agente)
    propiedad = db.get_propiedad_by_id(contrato.id_propiedad)
    propietario = (
        db.get_propietario_by_id(propiedad.id_propietario)
        if propiedad
        else None
    )
    clausulas = db.get_clausulas_by_contrato(nro_contrato)
    reclamos = db.list_reclamos_by_contrato(nro_contrato)

    return {
        "contrato": contrato,
        "cliente": cliente,
        "agente": agente,
        "propiedad": propiedad,
        "propietario": propietario,
        "clausulas": clausulas,
        "reclamos": reclamos,
        "monto_honorarios_totales": contrato.monto_honorarios_totales,
        "monto_comision_agente": contrato.monto_comision_agente,
        "monto_comision_inmobiliaria": contrato.monto_comision_inmobiliaria,
    }


def obtener_detalles_contrato_completo(nro_contrato: int) -> dict:
    """
    Alias compatible con tests y templates.
    """
    return obtener_detalle_contrato(nro_contrato)


# --- Queries exposing data objects to Presentation Layer ---


def obtener_propiedad(id_propiedad: int) -> Optional[PropiedadBO]:
    return db.get_propiedad_by_id(id_propiedad)


def obtener_cliente(id_cliente: int) -> Optional[ClienteBO]:
    return db.get_cliente_by_id(id_cliente)


def obtener_propietario(id_propietario: int) -> Optional[PropietarioBO]:
    return db.get_propietario_by_id(id_propietario)


def obtener_agente(id_agente: int) -> Optional[AgenteBO]:
    return db.get_agente_by_id(id_agente)


def obtener_contrato(nro_contrato: int) -> Optional[ContratoBO]:
    return db.get_contrato_by_id(nro_contrato)


def listar_propiedades() -> List[PropiedadBO]:
    return db.list_propiedades()


def listar_clientes() -> List[ClienteBO]:
    return db.list_clientes()


def listar_propietarios() -> List[PropietarioBO]:
    return db.list_propietarios()


def listar_agentes() -> List[AgenteBO]:
    return db.list_agentes()


def listar_contratos() -> List[ContratoBO]:
    return db.list_contratos()


def obtener_asignacion_activa_propiedad(
    id_propiedad: int,
) -> Optional[AgenteAsignadoBO]:
    return db.get_active_agent_assignment_for_property(id_propiedad)


# --- Late Fees, Rent Billing & Payments ---


def calcular_recargo_mora(
    monto_alquiler: float,
    mes: str,
    fecha_pago: Optional[date] = None,
    dia_vencimiento: int = 10,
    tasa_diaria: float = 0.002,
) -> dict:
    """
    Calcula si un pago de alquiler se realiza fuera de término.
    Retorna fecha_vencimiento, dias_retraso, monto_recargo y monto_total.
    """
    if not mes or len(mes) != 7 or mes[4] != "-":
        raise ValueError("El período debe tener el formato YYYY-MM.")

    if fecha_pago is None:
        fecha_pago = date.today()

    year = int(mes[:4])
    month = int(mes[5:7])
    fecha_vencimiento = date(year, month, min(dia_vencimiento, 28))

    if fecha_pago > fecha_vencimiento:
        dias_retraso = (fecha_pago - fecha_vencimiento).days
        monto_recargo = round(float(monto_alquiler) * (tasa_diaria * dias_retraso), 2)
    else:
        dias_retraso = 0
        monto_recargo = 0.0

    monto_total = round(float(monto_alquiler) + monto_recargo, 2)

    return {
        "fecha_vencimiento": fecha_vencimiento,
        "dias_retraso": dias_retraso,
        "monto_recargo": monto_recargo,
        "monto_total": monto_total,
    }


def registrar_pago_inquilino(
    nro_contrato: int,
    mes: str,
    monto: float,
    fecha_pago: Optional[date] = None,
    ruta_comprobante: Optional[str] = None,
    monto_recargo: Optional[float] = None,
    id_agente_solicitante: Optional[int] = None,
) -> PagoInquilinoBO:
    """
    Registra el pago de alquiler realizado por un inquilino, calculando recargos por mora si corresponde
    y vinculando el comprobante adjunto.
    """
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")

    if contrato.estado != "activo":
        raise ValueError(
            "Solo se pueden registrar pagos para contratos activos."
        )

    if not mes or len(mes) != 7 or mes[4] != "-":
        raise ValueError("El período debe tener el formato YYYY-MM.")

    existing = db.get_pago_inquilino_by_period(nro_contrato, mes)
    if existing:
        raise ValueError(f"Ya se ha registrado el pago para el período {mes}.")

    fecha_real_pago = fecha_pago or date.today()

    if monto_recargo is None:
        calc = calcular_recargo_mora(monto, mes, fecha_real_pago)
        fecha_vencimiento = calc["fecha_vencimiento"]
        dias_retraso = calc["dias_retraso"]
        monto_recargo = calc["monto_recargo"]
        monto_total = calc["monto_total"]
    else:
        calc = calcular_recargo_mora(monto, mes, fecha_real_pago)
        fecha_vencimiento = calc["fecha_vencimiento"]
        dias_retraso = calc["dias_retraso"]
        monto_total = round(monto + monto_recargo, 2)

    bo = PagoInquilinoBO(
        id=None,
        nro_contrato=nro_contrato,
        fecha_pago=fecha_real_pago,
        monto=monto,
        mes_correspondiente=mes,
        fecha_vencimiento=fecha_vencimiento,
        dias_retraso=dias_retraso,
        monto_recargo=monto_recargo,
        monto_total_abonado=monto_total,
        ruta_comprobante=ruta_comprobante,
    )
    saved_pago = db.save_pago_inquilino(bo)

    agente_nombre = "Sistema"
    if id_agente_solicitante:
        ag = db.get_agente_by_id(id_agente_solicitante)
        if ag:
            agente_nombre = ag.nombre_completo

    registrar_log_auditoria(
        id_agente=id_agente_solicitante,
        entidad="PagoInquilino",
        id_entidad=saved_pago.id,
        accion="RegistrarPago",
        descripcion=f"El agente {agente_nombre} registró el pago del período {mes} para el contrato #{nro_contrato}. Monto: ${monto:,.2f}, Recargo: ${saved_pago.monto_recargo:,.2f}."
    )

    return saved_pago


def obtener_datos_boleta_alquiler(nro_contrato: int, mes: str) -> dict:
    """
    Consolida la información completa para emitir la Boleta de Pago / Aviso de Cobro Mensual en PDF.
    """
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")

    cliente = db.get_cliente_by_id(contrato.id_cliente)
    propiedad = db.get_propiedad_by_id(contrato.id_propiedad)
    propietario = (
        db.get_propietario_by_id(propiedad.id_propietario)
        if propiedad
        else None
    )
    agente = db.get_agente_by_id(contrato.id_agente)

    year = int(mes[:4])
    month = int(mes[5:7])
    fecha_1er_vencimiento = date(year, month, 10)
    fecha_2do_vencimiento = date(year, month, 20)

    monto_base = contrato.monto
    recargo_estimado_2do_venc = round(monto_base * 0.02, 2)
    total_2do_vencimiento = round(monto_base + recargo_estimado_2do_venc, 2)

    pago_existente = db.get_pago_inquilino_by_period(nro_contrato, mes)

    return {
        "nro_contrato": contrato.nro_contrato,
        "mes": mes,
        "cliente": cliente,
        "propiedad": propiedad,
        "propietario": propietario,
        "agente": agente,
        "monto_base": monto_base,
        "fecha_1er_vencimiento": fecha_1er_vencimiento,
        "fecha_2do_vencimiento": fecha_2do_vencimiento,
        "recargo_estimado_2do_venc": recargo_estimado_2do_venc,
        "total_2do_vencimiento": total_2do_vencimiento,
        "pago_registrado": pago_existente,
        "codigo_barras_ref": f"INMO-{contrato.nro_contrato:04d}-{mes.replace('-', '')}",
    }


# --- Vacancies & Market Price Analysis ---


def calcular_dias_vacante(propiedad: PropiedadBO) -> int:
    """
    Calcula el tiempo que una propiedad lleva inactiva restando la fecha actual con fecha_disponibilidad.
    """
    if not propiedad or not propiedad.fecha_disponibilidad:
        return 0
    hoy = date.today()
    diferencia = (hoy - propiedad.fecha_disponibilidad).days
    return max(0, diferencia)


def obtener_ranking_propiedades_vacantes() -> List[dict]:
    """
    KPI para el Dashboard: Genera un ranking de propiedades vacantes ordenadas de mayor a menor tiempo.
    """
    propiedades = db.list_propiedades()
    disponibles = [p for p in propiedades if p.estado.lower() == "disponible"]

    ranking = []
    for prop in disponibles:
        dias = calcular_dias_vacante(prop)
        propietario = db.get_propietario_by_id(prop.id_propietario)
        ranking.append(
            {
                "propiedad": prop,
                "dias_vacante": dias,
                "propietario": propietario,
            }
        )

    ranking.sort(key=lambda x: x["dias_vacante"], reverse=True)
    return ranking


def obtener_analisis_propiedades_inactivas() -> List[dict]:
    """
    Sección de Propiedades: Análisis estratégico de inmuebles con diagnósticos y recomendaciones.
    """
    propiedades = db.list_propiedades()
    disponibles = [p for p in propiedades if p.estado.lower() == "disponible"]

    analisis = []
    for prop in disponibles:
        dias = calcular_dias_vacante(prop)
        propietario = db.get_propietario_by_id(prop.id_propietario)
        agente_asig = db.get_active_agent_assignment_for_property(prop.id)
        agente = (
            db.get_agente_by_id(agente_asig.id_agente)
            if agente_asig
            else None
        )

        if dias <= 30:
            nivel_riesgo = "Bajo"
            badge_class = "badge-activo"
            diagnostico = "Inmueble publicado recientemente dentro del período promedio de colocación."
            ajuste_sugerido_pct = 0
            accion_recomendada = "Mantener precio actual y continuar con difusión en canales digitales."
        elif dias <= 60:
            nivel_riesgo = "Moderado"
            badge_class = "badge-admin"
            diagnostico = "Tiempo de oferta prolongado. Se observa menor flujo de consultas."
            ajuste_sugerido_pct = 5
            accion_recomendada = (
                "Incrementar difusión en portales destacados y coordinar jornadas de Open House."
            )
        elif dias <= 90:
            nivel_riesgo = "Alto"
            badge_class = "badge-solicitado"
            diagnostico = "Inmueble con baja competitividad frente a la oferta zonal."
            ajuste_sugerido_pct = 10
            accion_recomendada = (
                "Recomendar al propietario reducción de precio del 10% o mejora fotográfica."
            )
        else:
            nivel_riesgo = "Crítico"
            badge_class = "badge-pendiente"
            diagnostico = "Inactividad crítica (> 90 días). Alto costo de oportunidad y expensas acumuladas."
            ajuste_sugerido_pct = 15
            accion_recomendada = (
                "Reunión urgente con dueño: proponer baja del 15% o flexibilización de garantías."
            )

        analisis.append(
            {
                "propiedad": prop,
                "dias_vacante": dias,
                "propietario": propietario,
                "agente": agente,
                "nivel_riesgo": nivel_riesgo,
                "badge_class": badge_class,
                "diagnostico": diagnostico,
                "ajuste_sugerido_pct": ajuste_sugerido_pct,
                "accion_recomendada": accion_recomendada,
            }
        )

    analisis.sort(key=lambda x: x["dias_vacante"], reverse=True)
    return analisis


# --- Agenda & Property Visit Appointments ---


def crear_agenda_visita(
    id_propiedad: int,
    id_agente: int,
    fecha_hora_visita: datetime,
    duracion_minutos: int = 30,
    cupo_maximo: int = 3,
) -> AgendaVisitaBO:
    """
    Registra un nuevo turno/agenda de visitas para una propiedad disponible.
    """
    propiedad = db.get_propiedad_by_id(id_propiedad)
    if not propiedad:
        raise ValueError("La propiedad especificada no existe.")

    if propiedad.estado.lower() != "disponible":
        raise ValueError(
            "Solo se pueden coordinar visitas para propiedades disponibles."
        )

    agente = db.get_agente_by_id(id_agente)
    if not agente:
        raise ValueError("El agente especificado no existe.")

    if cupo_maximo < 1:
        raise ValueError("El cupo máximo de la visita debe ser al menos 1.")

    fin_visita = fecha_hora_visita + timedelta(minutes=duracion_minutos)

    # Validar superposición con otras agendas del mismo agente
    agendas_agente = db.list_todas_agendas_visitas()
    for ag in agendas_agente:
        if ag.id_agente == id_agente and ag.estado != "cancelada":
            ag_fin = ag.fecha_hora_visita + timedelta(
                minutes=ag.duracion_minutos
            )
            if max(fecha_hora_visita, ag.fecha_hora_visita) < min(
                fin_visita, ag_fin
            ):
                fecha_str = ag.fecha_hora_visita.strftime("%d/%m/%Y %H:%M")
                raise ValueError(
                    f"El agente {agente.nombre_completo} ya tiene otra visita agendada en ese horario ({fecha_str})."
                )

    bo = AgendaVisitaBO(
        id=None,
        id_propiedad=id_propiedad,
        id_agente=id_agente,
        fecha_hora_visita=fecha_hora_visita,
        duracion_minutos=duracion_minutos,
        cupo_maximo=cupo_maximo,
        estado="disponible",
    )
    return db.save_agenda_visita(bo)


def inscribir_visitante_a_turno(
    id_agenda: int,
    nombre_visitante: str,
    telefono_visitante: str,
    email_visitante: str = "",
    id_cliente: Optional[int] = None,
    observaciones: str = "",
) -> InscripcionVisitaBO:
    """
    Inscribe a un interesado en una agenda de visita respetando el cupo máximo.
    """
    agenda = db.get_agenda_visita_by_id(id_agenda)
    if not agenda:
        raise ValueError("El turno de visita especificado no existe.")

    propiedad = db.get_propiedad_by_id(agenda.id_propiedad)
    if not propiedad or propiedad.estado.lower() != "disponible":
        raise ValueError("No se pueden inscribir visitantes en propiedades que no estén disponibles.")

    inscriptos_actuales = db.count_inscripciones_by_agenda(id_agenda)
    if agenda.estado != "disponible" or inscriptos_actuales >= agenda.cupo_maximo:
        agenda.estado = "completo"
        db.save_agenda_visita(agenda)
        raise ValueError("El cupo para este turno de visita está agotado.")

    if not nombre_visitante.strip():
        raise ValueError("El nombre del visitante es obligatorio.")

    if not telefono_visitante.strip():
        raise ValueError("El teléfono de contacto es obligatorio.")

    bo = InscripcionVisitaBO(
        id=None,
        id_agenda=id_agenda,
        id_cliente=id_cliente,
        nombre_visitante=nombre_visitante.strip(),
        telefono_visitante=telefono_visitante.strip(),
        email_visitante=email_visitante.strip(),
        observaciones=observaciones.strip(),
        fecha_registro=datetime.now(),
        asistio=None,
    )
    saved_inscripcion = db.save_inscripcion_visita(bo)

    if inscriptos_actuales + 1 >= agenda.cupo_maximo:
        agenda.estado = "completo"
        db.save_agenda_visita(agenda)

    return saved_inscripcion


def cancelar_agenda_visita(id_agenda: int) -> AgendaVisitaBO:
    agenda = db.get_agenda_visita_by_id(id_agenda)
    if not agenda:
        raise ValueError("El turno de visita especificado no existe.")
    agenda.estado = "cancelada"
    return db.save_agenda_visita(agenda)


def obtener_agenda_con_inscriptos(id_agenda: int) -> dict:
    agenda = db.get_agenda_visita_by_id(id_agenda)
    if not agenda:
        raise ValueError("El turno de visita especificado no existe.")

    propiedad = db.get_propiedad_by_id(agenda.id_propiedad)
    agente = db.get_agente_by_id(agenda.id_agente)
    inscriptos = db.list_inscripciones_by_agenda(id_agenda)
    cupo_disponible = max(0, agenda.cupo_maximo - len(inscriptos))

    return {
        "agenda": agenda,
        "propiedad": propiedad,
        "agente": agente,
        "inscriptos": inscriptos,
        "total_inscriptos": len(inscriptos),
        "cupo_disponible": cupo_disponible,
    }


def listar_agendas_propiedad_con_metricas(id_propiedad: int) -> List[dict]:
    agendas = db.list_agendas_visitas_by_propiedad(id_propiedad)
    propiedad = db.get_propiedad_by_id(id_propiedad)

    resultado = []
    for ag in agendas:
        inscriptos = db.list_inscripciones_by_agenda(ag.id)
        agente = db.get_agente_by_id(ag.id_agente)
        cupo_disponible = max(0, ag.cupo_maximo - len(inscriptos))
        resultado.append(
            {
                "agenda": ag,
                "propiedad": propiedad,
                "agente": agente,
                "inscriptos": inscriptos,
                "total_inscriptos": len(inscriptos),
                "cupo_disponible": cupo_disponible,
            }
        )
    return resultado


def listar_todas_las_agendas_con_metricas() -> List[dict]:
    agendas = db.list_todas_agendas_visitas()
    resultado = []
    for ag in agendas:
        propiedad = db.get_propiedad_by_id(ag.id_propiedad)
        agente = db.get_agente_by_id(ag.id_agente)
        inscriptos = db.list_inscripciones_by_agenda(ag.id)
        cupo_disponible = max(0, ag.cupo_maximo - len(inscriptos))
        resultado.append(
            {
                "agenda": ag,
                "propiedad": propiedad,
                "agente": agente,
                "inscriptos": inscriptos,
                "total_inscriptos": len(inscriptos),
                "cupo_disponible": cupo_disponible,
            }
        )
    return resultado


def obtener_agenda_visita(id_agenda: int) -> Optional[AgendaVisitaBO]:
    return db.get_agenda_visita_by_id(id_agenda)


def listar_inscripciones_de_agenda(
    id_agenda: int,
) -> List[InscripcionVisitaBO]:
    return db.list_inscripciones_by_agenda(id_agenda)


# --- Liquidations & Financial Reports ---


def generar_liquidaciones_mes(
    mes_correspondiente: str,
    id_agente_solicitante: Optional[int] = None,
) -> List[PagoPropietarioBO]:
    """
    Genera liquidaciones a propietarios para contratos activos.
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Se requieren permisos de Administrador para generar liquidaciones."
        )

    if (
        not mes_correspondiente
        or len(mes_correspondiente) != 7
        or mes_correspondiente[4] != "-"
    ):
        raise ValueError("El período debe tener el formato YYYY-MM.")

    contratos = db.list_contratos()
    liquidaciones_generadas = []

    for c in contratos:
        if c.estado != "activo":
            continue

        propiedad = db.get_propiedad_by_id(c.id_propiedad)
        if not propiedad or propiedad.tipo.lower() != "alquiler":
            continue

        pago_inq = db.get_pago_inquilino_by_period(
            c.nro_contrato, mes_correspondiente
        )
        if not pago_inq:
            continue

        existing_payout = db.get_pago_propietario_by_period(
            c.nro_contrato, mes_correspondiente
        )
        if existing_payout:
            continue

        monto_bruto = c.monto
        comision = monto_bruto * (c.comision_porcentaje / 100.0)
        monto_neto = monto_bruto - comision

        payout = PagoPropietarioBO(
            id=None,
            id_propietario=propiedad.id_propietario,
            nro_contrato=c.nro_contrato,
            fecha_liquidacion=date.today(),
            fecha_pago=None,
            mes_correspondiente=mes_correspondiente,
            monto_bruto=monto_bruto,
            comision=comision,
            monto_neto=monto_neto,
            estado="pendiente",
        )
        saved_payout = db.save_pago_propietario(payout)
        liquidaciones_generadas.append(saved_payout)

    return liquidaciones_generadas


def registrar_transferencia_propietario(
    id_pago_propietario: int,
    fecha_pago: Optional[date] = None,
    id_agente_solicitante: Optional[int] = None,
) -> PagoPropietarioBO:
    """
    Registra el pago de la liquidación transferido al propietario.
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Se requieren permisos de Administrador para registrar transferencias."
        )

    payout = db.get_pago_propietario_by_id(id_pago_propietario)
    if not payout:
        raise ValueError("La liquidación especificada no existe.")

    if payout.estado != "pendiente":
        raise ValueError("Esta liquidación ya fue transferida y pagada.")

    payout.estado = "pagado"
    payout.fecha_pago = fecha_pago or date.today()
    saved = db.save_pago_propietario(payout)

    # Notificar automáticamente al propietario
    try:
        notificar_transferencia_propietario(saved.id)
    except Exception as e:
        print(f"Aviso de transferencia no enviado por correo: {e}")

    return saved


def listar_pagos_inquilinos() -> List[PagoInquilinoBO]:
    return db.list_pagos_inquilinos()


def listar_pagos_propietarios() -> List[PagoPropietarioBO]:
    return db.list_pagos_propietarios()


def obtener_pago_inquilino(id_pago: int) -> Optional[PagoInquilinoBO]:
    return db.get_pago_inquilino_by_id(id_pago)


def obtener_pago_propietario(id_pago: int) -> Optional[PagoPropietarioBO]:
    return db.get_pago_propietario_by_id(id_pago)


def exportar_reporte_financiero_csv(
    tipo_reporte: str,
    id_agente_solicitante: Optional[int] = None,
) -> str:
    """
    Genera un archivo CSV con el reporte financiero.
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Solo los Administradores pueden exportar reportes financieros."
        )

    lines = []
    if tipo_reporte == "cobros":
        lines.append("ID Pago,Fecha Pago,Nro Contrato,Cliente,Mes,Monto Base,Dias Mora,Recargo,Monto Total")
        pagos = db.list_pagos_inquilinos()
        for p in pagos:
            c = db.get_contrato_by_id(p.nro_contrato)
            cliente = db.get_cliente_by_id(c.id_cliente) if c else None
            cliente_nombre = cliente.nombre_completo if cliente else "N/A"
            lines.append(
                f"{p.id},{p.fecha_pago},{p.nro_contrato},\"{cliente_nombre}\","
                f"{p.mes_correspondiente},{p.monto:.2f},{p.dias_retraso},"
                f"{p.monto_recargo:.2f},{p.monto_total_abonado:.2f}"
            )
    elif tipo_reporte == "liquidaciones":
        lines.append(
            "ID Liquidacion,Período,Nro Contrato,Propietario,Monto Bruto,Comision,Monto Neto,Estado,Fecha Pago"
        )
        liquidaciones = db.list_pagos_propietarios()
        for liq in liquidaciones:
            prop = db.get_propietario_by_id(liq.id_propietario)
            nombre_prop = prop.nombre_completo if prop else "N/A"
            fecha_pago_str = (
                liq.fecha_pago.strftime("%Y-%m-%d") if liq.fecha_pago else "Pendiente"
            )
            lines.append(
                f"{liq.id},{liq.mes_correspondiente},{liq.nro_contrato},\"{nombre_prop}\","
                f"{liq.monto_bruto:.2f},{liq.comision:.2f},{liq.monto_neto:.2f},{liq.estado},{fecha_pago_str}"
            )
    else:
        raise ValueError("Tipo de reporte no válido. Use 'cobros' o 'liquidaciones'.")

    return "\n".join(lines)


def obtener_estadisticas_financieras(
    id_propietario: Optional[int] = None,
    id_cliente: Optional[int] = None,
    mes: Optional[str] = None,
    id_agente_solicitante: Optional[int] = None,
) -> dict:
    """
    Calcula las estadísticas financieras para un período.
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Se requieren permisos de Administrador para consultar estadísticas financieras."
        )

    if not mes:
        mes = datetime.now().strftime("%Y-%m")

    contratos = db.list_contratos()

    if id_cliente:
        contratos = [c for c in contratos if c.id_cliente == id_cliente]
    elif id_propietario:
        filtered_contratos = []
        for c in contratos:
            prop = db.get_propiedad_by_id(c.id_propiedad)
            if prop and prop.id_propietario == id_propietario:
                filtered_contratos.append(c)
        contratos = filtered_contratos

    total_cobrado_mes = 0.0
    total_pendiente_cobrar_mes = 0.0
    contratos_atrasados = []

    for c in contratos:
        if c.estado != "activo":
            continue
        prop = db.get_propiedad_by_id(c.id_propiedad)
        if not prop or prop.tipo.lower() != "alquiler":
            continue

        pago_inq = db.get_pago_inquilino_by_period(c.nro_contrato, mes)
        if pago_inq:
            total_cobrado_mes += pago_inq.monto
        else:
            total_pendiente_cobrar_mes += c.monto
            cliente = db.get_cliente_by_id(c.id_cliente)
            contratos_atrasados.append(
                {"contrato": c, "cliente": cliente, "propiedad": prop}
            )

    liquidaciones = db.list_pagos_propietarios()
    if id_cliente:
        client_contract_nros = {
            c.nro_contrato
            for c in db.list_contratos()
            if c.id_cliente == id_cliente
        }
        liquidaciones = [
            liq
            for liq in liquidaciones
            if liq.nro_contrato in client_contract_nros
        ]
    elif id_propietario:
        liquidaciones = [
            liq for liq in liquidaciones if liq.id_propietario == id_propietario
        ]

    total_pendiente_pagar_propietario = sum(
        liq.monto_neto for liq in liquidaciones if liq.estado == "pendiente"
    )
    total_comisiones = sum(liq.comision for liq in liquidaciones)

    return {
        "total_cobrado_mes": total_cobrado_mes,
        "total_pendiente_cobrar_mes": total_pendiente_cobrar_mes,
        "total_pendiente_pagar_propietario": total_pendiente_pagar_propietario,
        "total_comisiones": total_comisiones,
        "contratos_atrasados": contratos_atrasados,
        "periodo": mes,
    }


# --- Módulo de Reclamos e Incidencias ---


def registrar_reclamo(
    nro_contrato: int,
    tipo_dano: str,
    descripcion: str,
    urgencia: str = "Media",
    presupuesto_estimado: float = 0.0,
    fecha_reclamo: Optional[date] = None,
) -> ReclamoBO:
    """
    Registra un reclamo o daño estructural asociado a un contrato activo.
    Extrae automáticamente la propiedad y el cliente (inquilino) del contrato.
    """
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El número de contrato especificado no existe.")

    if contrato.estado != "activo":
        raise ValueError(
            "Solo se pueden registrar reclamos sobre contratos activos."
        )

    if not descripcion.strip():
        raise ValueError("La descripción del reclamo es obligatoria.")

    if presupuesto_estimado < 0:
        raise ValueError("El presupuesto estimado no puede ser negativo.")

    urgencias_validas = ["Baja", "Media", "Alta", "Urgente"]
    if urgencia not in urgencias_validas:
        urgencia = "Media"

    tipos_validos = [
        "Estructural / Techos / Muros",
        "Plomería / Humedad",
        "Electricidad",
        "Gas / Calefacción",
        "Cerrajería / Aberturas",
        "Otro",
    ]
    if tipo_dano not in tipos_validos:
        tipo_dano = "Estructural / Techos / Muros"

    bo = ReclamoBO(
        id=None,
        nro_contrato=nro_contrato,
        id_propiedad=contrato.id_propiedad,
        id_cliente=contrato.id_cliente,
        fecha_reclamo=fecha_reclamo or date.today(),
        tipo_dano=tipo_dano,
        descripcion=descripcion.strip(),
        urgencia=urgencia,
        presupuesto_estimado=round(float(presupuesto_estimado), 2),
        estado="pendiente",
        observaciones_resolucion="",
        fecha_resolucion=None,
    )
    return db.save_reclamo(bo)


def actualizar_estado_reclamo(
    id_reclamo: int,
    nuevo_estado: str,
    presupuesto_actualizado: Optional[float] = None,
    observaciones_resolucion: str = "",
) -> ReclamoBO:
    """
    Actualiza el estado de un reclamo (pendiente, informado_propietario, en_reparacion, resuelto, desestimado).
    """
    reclamo = db.get_reclamo_by_id(id_reclamo)
    if not reclamo:
        raise ValueError("El reclamo especificado no existe.")

    estados_validos = [
        "pendiente",
        "informado_propietario",
        "en_reparacion",
        "resuelto",
        "desestimado",
    ]
    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado '{nuevo_estado}' no válido.")

    reclamo.estado = nuevo_estado
    if presupuesto_actualizado is not None and presupuesto_actualizado >= 0:
        reclamo.presupuesto_estimado = round(float(presupuesto_actualizado), 2)

    if observaciones_resolucion.strip():
        reclamo.observaciones_resolucion = observaciones_resolucion.strip()

    if nuevo_estado in ["resuelto", "desestimado"]:
        reclamo.fecha_resolucion = date.today()
    else:
        reclamo.fecha_resolucion = None

    return db.save_reclamo(reclamo)


def obtener_detalle_reclamo(id_reclamo: int) -> dict:
    """
    Obtiene el detalle completo de un reclamo consolidando contrato,
    inquilino, propiedad y propietario para el informe de presupuesto.
    """
    reclamo = db.get_reclamo_by_id(id_reclamo)
    if not reclamo:
        raise ValueError("El reclamo especificado no existe.")

    contrato = db.get_contrato_by_id(reclamo.nro_contrato)
    propiedad = db.get_propiedad_by_id(reclamo.id_propiedad)
    cliente = db.get_cliente_by_id(reclamo.id_cliente)
    propietario = (
        db.get_propietario_by_id(propiedad.id_propietario)
        if propiedad
        else None
    )

    return {
        "reclamo": reclamo,
        "contrato": contrato,
        "propiedad": propiedad,
        "cliente": cliente,
        "propietario": propietario,
    }


def listar_reclamos_con_detalle(
    nro_contrato: Optional[int] = None, estado: Optional[str] = None
) -> List[dict]:
    """
    Lista todos los reclamos enriquecidos con datos relacionados.
    """
    if nro_contrato:
        reclamos = db.list_reclamos_by_contrato(nro_contrato)
    else:
        reclamos = db.list_reclamos()

    if estado:
        reclamos = [r for r in reclamos if r.estado.lower() == estado.lower()]

    resultado = []
    for r in reclamos:
        prop = db.get_propiedad_by_id(r.id_propiedad)
        cli = db.get_cliente_by_id(r.id_cliente)
        proprio = db.get_propietario_by_id(prop.id_propietario) if prop else None
        resultado.append(
            {
                "reclamo": r,
                "propiedad": prop,
                "cliente": cli,
                "propietario": proprio,
            }
        )
    return resultado


# --- Servicio de Notificaciones y Email Corporativo ---


def enviar_email(destinatario: str, asunto: str, cuerpo_texto: str) -> bool:
    """
    Envía un correo electrónico utilizando smtplib y configuración desde .env.
    Si MAIL_SUPPRESS_SEND es True o faltan credenciales, simula el envío con log seguro.
    """
    mail_server = os.environ.get("MAIL_SERVER", "").strip()
    mail_port = int(os.environ.get("MAIL_PORT", "587"))
    mail_user = os.environ.get("MAIL_USERNAME", "").strip()
    mail_pass = os.environ.get("MAIL_PASSWORD", "").strip()
    sender = os.environ.get(
        "MAIL_DEFAULT_SENDER", "notificaciones@inmogestion.com"
    ).strip()
    suppress_send = os.environ.get(
        "MAIL_SUPPRESS_SEND", "true"
    ).lower() in ["true", "1", "yes"]

    if not destinatario or not destinatario.strip():
        return False

    if suppress_send or not mail_server or not mail_user:
        # Modo seguro / desarrollo: registrar en consola sin fallar
        print(f"[MAIL SIMULADO] A: {destinatario} | Asunto: {asunto}")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = destinatario
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))

        with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
            if os.environ.get("MAIL_USE_TLS", "true").lower() in [
                "true",
                "1",
                "yes",
            ]:
                server.starttls()
            if mail_user and mail_pass:
                server.login(mail_user, mail_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR ENVIO EMAIL] {e}")
        return False


def enviar_alertas_mora_inquilinos(
    mes: Optional[str] = None, id_agente_solicitante: Optional[int] = None
) -> dict:
    """
    Evalúa y envía alertas de mora a los inquilinos que no hayan abonado su alquiler
    después del día 10 del mes correspondiente.
    Incluye prevención de spam/duplicados mediante fecha_ultimo_aviso_mora.
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Solo los Administradores pueden ejecutar el envío de alertas de mora."
        )

    hoy = date.today()
    mes_evaluar = mes or hoy.strftime("%Y-%m")

    # Obtener contratos de alquiler activos
    contratos = [
        c
        for c in db.list_contratos()
        if c.estado == "activo" and c.tipo_contrato.lower() == "alquiler"
    ]

    notificados = []
    omitidos = []

    for c in contratos:
        # Verificar si ya pagó este período
        pago_registrado = db.get_pago_inquilino_by_period(
            c.nro_contrato, mes_evaluar
        )
        if pago_registrado:
            continue

        # Evaluar mora (vencimiento día 10)
        calc_mora = calcular_recargo_mora(c.monto, mes_evaluar, hoy)
        dias_retraso = calc_mora["dias_retraso"]
        monto_recargo = calc_mora["monto_recargo"]
        monto_total = calc_mora["monto_total"]

        if dias_retraso > 0:
            # Control de SPAM: Si ya se notificó hoy, omitir
            if c.fecha_ultimo_aviso_mora == hoy:
                omitidos.append(
                    {
                        "contrato": c.nro_contrato,
                        "motivo": "Ya fue notificado hoy.",
                    }
                )
                continue

            cliente = db.get_cliente_by_id(c.id_cliente)
            propiedad = db.get_propiedad_by_id(c.id_propiedad)
            if not cliente or not cliente.email:
                continue

            asunto = (
                f"[AVISO DE VENCIMIENTO Y MORA] Alquiler Período {mes_evaluar} - "
                f"InmoGestión B2B"
            )
            cuerpo = (
                f"Estimado/a {cliente.nombre_completo}:\n\n"
                f"Le informamos que al día de la fecha ({hoy.strftime('%d/%m/%Y')}) "
                f"registramos un saldo pendiente de pago correspondiente al período {mes_evaluar} "
                f"para el inmueble ubicado en:\n"
                f"Dirección: {propiedad.direccion if propiedad else 'Inmueble locado'}\n"
                f"Contrato N°: #{c.nro_contrato}\n\n"
                f"--- DETALLE DE LA LIQUIDACIÓN ---\n"
                f"Canon de Alquiler Base: ${c.monto:,.2f}\n"
                f"Fecha de 1° Vencimiento: 10/{mes_evaluar[5:7]}/{mes_evaluar[:4]}\n"
                f"Días de Mora Acumulados: {dias_retraso} días\n"
                f"Recargo por Pago Fuera de Término (0.2% diario): ${monto_recargo:,.2f}\n"
                f"TOTAL A REGULARIZAR: ${monto_total:,.2f}\n\n"
                f"--- DATOS PARA TRANSFERENCIA BANCARIA ---\n"
                f"Banco: Banco Santander Río\n"
                f"Titular: InmoGestión B2B S.A.\n"
                f"CUIT: 30-71889900-4\n"
                f"CBU: 0720123420000000456789\n"
                f"Alias: INMO.GESTION.PAGOS\n\n"
                f"Una vez realizada la transferencia, recuerde enviar o adjuntar su comprobante.\n"
                f"Si ya ha regularizado este concepto en las últimas 24 horas, "
                f"por favor desestime el presente aviso.\n\n"
                f"Atentamente,\n"
                f"Departamento de Cobranzas y Finanzas\n"
                f"InmoGestión B2B — Av. Pellegrini 250, Rosario"
            )

            enviado = enviar_email(cliente.email, asunto, cuerpo)
            if enviado:
                db.actualizar_ultimo_aviso_mora(c.nro_contrato, hoy)
                notificados.append(
                    {
                        "nro_contrato": c.nro_contrato,
                        "inquilino": cliente.nombre_completo,
                        "email": cliente.email,
                        "dias_retraso": dias_retraso,
                        "monto_total": monto_total,
                    }
                )

    return {
        "periodo": mes_evaluar,
        "total_enviados": len(notificados),
        "notificados": notificados,
        "omitidos": omitidos,
    }


def obtener_estado_cobros_alquileres_mes(mes: Optional[str] = None) -> list:
    """
    Retorna el estado de cobro de cada contrato de alquiler activo para el período indicado,
    indicando si está pagado, en término o vencido con mora, y si se puede enviar mail.
    """
    hoy = date.today()
    mes_evaluar = mes or hoy.strftime("%Y-%m")
    contratos = [
        c
        for c in db.list_contratos()
        if c.estado == "activo" and c.tipo_contrato.lower() == "alquiler"
    ]

    resultado = []
    for c in contratos:
        cliente = db.get_cliente_by_id(c.id_cliente)
        propiedad = db.get_propiedad_by_id(c.id_propiedad)
        pago = db.get_pago_inquilino_by_period(c.nro_contrato, mes_evaluar)

        calc_mora = calcular_recargo_mora(c.monto, mes_evaluar, hoy)
        dias_retraso = calc_mora["dias_retraso"]
        monto_recargo = calc_mora["monto_recargo"]
        monto_total = calc_mora["monto_total"]

        esta_pagado = pago is not None
        esta_vencido = (not esta_pagado) and (dias_retraso > 0)
        puede_mandar_mail = esta_vencido

        resultado.append(
            {
                "contrato": c,
                "cliente": cliente,
                "propiedad": propiedad,
                "pago": pago,
                "mes": mes_evaluar,
                "esta_pagado": esta_pagado,
                "esta_vencido": esta_vencido,
                "dias_retraso": dias_retraso,
                "monto_recargo": monto_recargo,
                "monto_total": monto_total,
                "puede_mandar_mail": puede_mandar_mail,
                "fecha_ultimo_aviso_mora": c.fecha_ultimo_aviso_mora,
            }
        )

    return resultado


def enviar_alerta_mora_individual(
    nro_contrato: int,
    mes: Optional[str] = None,
    id_agente_solicitante: Optional[int] = None,
) -> dict:
    """
    Envía la alerta de mora por correo a un contrato de alquiler individual.
    Valida que el contrato esté activo, sea de alquiler y se encuentre vencido (posterior al día 10).
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Se requieren permisos de Administrador para enviar alertas de mora."
        )

    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El número de contrato especificado no existe.")

    if (
        contrato.estado != "activo"
        or contrato.tipo_contrato.lower() != "alquiler"
    ):
        raise ValueError(
            "Solo se pueden enviar alertas de mora a contratos de alquiler activos."
        )

    hoy = date.today()
    mes_evaluar = mes or hoy.strftime("%Y-%m")

    # Verificar si ya está pagado
    pago_registrado = db.get_pago_inquilino_by_period(nro_contrato, mes_evaluar)
    if pago_registrado:
        raise ValueError(
            f"El alquiler del período {mes_evaluar} ya fue abonado por el inquilino."
        )

    calc_mora = calcular_recargo_mora(contrato.monto, mes_evaluar, hoy)
    dias_retraso = calc_mora["dias_retraso"]
    monto_recargo = calc_mora["monto_recargo"]
    monto_total = calc_mora["monto_total"]

    if dias_retraso <= 0:
        raise ValueError(
            f"El alquiler del período {mes_evaluar} aún no está vencido (vencimiento día 10). "
            f"El botón de 'Mandar Mail' solo se habilita cuando el pago está vencido."
        )

    cliente = db.get_cliente_by_id(contrato.id_cliente)
    propiedad = db.get_propiedad_by_id(contrato.id_propiedad)

    if not cliente or not cliente.email:
        raise ValueError(
            "El cliente asociado no posee una dirección de correo electrónico registrada."
        )

    asunto = (
        f"[AVISO DE VENCIMIENTO Y MORA] Alquiler Período {mes_evaluar} - "
        f"InmoGestión B2B"
    )
    cuerpo = (
        f"Estimado/a {cliente.nombre_completo}:\n\n"
        f"Le informamos que al día de la fecha ({hoy.strftime('%d/%m/%Y')}) "
        f"registramos un saldo pendiente de pago correspondiente al período {mes_evaluar} "
        f"para el inmueble ubicado en:\n"
        f"Dirección: {propiedad.direccion if propiedad else 'Inmueble locado'}\n"
        f"Contrato N°: #{contrato.nro_contrato}\n\n"
        f"--- DETALLE DE LA LIQUIDACIÓN ---\n"
        f"Canon de Alquiler Base: ${contrato.monto:,.2f}\n"
        f"Fecha de 1° Vencimiento: 10/{mes_evaluar[5:7]}/{mes_evaluar[:4]}\n"
        f"Días de Mora Acumulados: {dias_retraso} días\n"
        f"Recargo por Pago Fuera de Término (0.2% diario): ${monto_recargo:,.2f}\n"
        f"TOTAL A REGULARIZAR: ${monto_total:,.2f}\n\n"
        f"--- DATOS PARA TRANSFERENCIA BANCARIA ---\n"
        f"Banco: Banco Santander Río\n"
        f"Titular: InmoGestión B2B S.A.\n"
        f"CUIT: 30-71889900-4\n"
        f"CBU: 0720123420000000456789\n"
        f"Alias: INMO.GESTION.PAGOS\n\n"
        f"Una vez realizada la transferencia, recuerde enviar o adjuntar su comprobante.\n"
        f"Si ya ha regularizado este concepto en las últimas 24 horas, "
        f"por favor desestime el presente aviso.\n\n"
        f"Atentamente,\n"
        f"Departamento de Cobranzas y Finanzas\n"
        f"InmoGestión B2B — Av. Pellegrini 250, Rosario"
    )

    enviar_email(cliente.email, asunto, cuerpo)
    db.actualizar_ultimo_aviso_mora(contrato.nro_contrato, hoy)

    return {
        "nro_contrato": contrato.nro_contrato,
        "inquilino": cliente.nombre_completo,
        "email": cliente.email,
        "dias_retraso": dias_retraso,
        "monto_recargo": monto_recargo,
        "monto_total": monto_total,
        "periodo": mes_evaluar,
    }


def notificar_transferencia_propietario(id_pago_propietario: int) -> bool:
    """
    Envía un correo de aviso formal al dueño del inmueble en el momento exacto
    en que se asienta el pago/transferencia de su liquidación.
    """
    payout = db.get_pago_propietario_by_id(id_pago_propietario)
    if not payout or payout.estado != "pagado":
        return False

    propietario = db.get_propietario_by_id(payout.id_propietario)
    if not propietario or not propietario.email:
        return False

    contrato = db.get_contrato_by_id(payout.nro_contrato)
    propiedad = (
        db.get_propiedad_by_id(contrato.id_propiedad) if contrato else None
    )
    fecha_pago_str = (
        payout.fecha_pago.strftime("%d/%m/%Y")
        if payout.fecha_pago
        else date.today().strftime("%d/%m/%Y")
    )

    asunto = (
        f"[LIQUIDACIÓN TRANSFERIDA] Pago de Renta Período {payout.mes_correspondiente} - "
        f"InmoGestión B2B"
    )
    cuerpo = (
        f"Estimado/a {propietario.nombre_completo}:\n\n"
        f"Le informamos que con fecha {fecha_pago_str} se ha efectuado la transferencia bancaria "
        f"correspondiente a la liquidación de alquiler del período {payout.mes_correspondiente}.\n\n"
        f"--- DETALLE DE LA LIQUIDACIÓN ---\n"
        f"Inmueble: {propiedad.direccion if propiedad else 'Propiedad en administración'}\n"
        f"Contrato N°: #{payout.nro_contrato}\n"
        f"Monto Bruto Cobrado: ${payout.monto_bruto:,.2f}\n"
        f"Honorarios Inmobiliarios Retenidos: ${payout.comision:,.2f}\n"
        f"MONTO NETO TRANSFERIDO: ${payout.monto_neto:,.2f}\n\n"
        f"El importe ya se encuentra transferido a su cuenta bancaria registrada.\n"
        f"Ante cualquier duda o consulta contable, estamos a su entera disposición.\n\n"
        f"Atentamente,\n"
        f"Administración de Propiedades & Cajas\n"
        f"InmoGestión B2B — Av. Pellegrini 250, Rosario"
    )

    return enviar_email(propietario.email, asunto, cuerpo)


def registrar_log_auditoria(
    id_agente: Optional[int],
    entidad: str,
    id_entidad: Optional[int],
    accion: str,
    descripcion: str,
) -> AuditLogBO:
    """
    Registra una acción en el log de auditoría del sistema.
    """
    bo = AuditLogBO(
        id=None,
        fecha_hora=datetime.now(),
        id_agente=id_agente,
        entidad=entidad,
        id_entidad=id_entidad,
        accion=accion,
        descripcion=descripcion,
    )
    return db.save_audit_log(bo)


def listar_logs_auditoria(id_agente_solicitante: int) -> List[AuditLogBO]:
    """
    Retorna todos los registros de auditoría del sistema.
    Requiere que el agente solicitante sea Administrador.
    """
    if not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Solo los Administradores pueden ver el log de auditoría."
        )
    return db.list_audit_logs()


def cancelar_inscripcion_visita(
    id_inscripcion: int, id_agente_solicitante: Optional[int] = None
) -> bool:
    """
    Cancela la inscripción de un visitante a un turno de visita.
    Si el turno estaba completo, se vuelve a poner disponible.
    """
    db_obj = db.get_inscripcion_visita_by_id(id_inscripcion)
    if not db_obj:
        raise ValueError("La inscripción especificada no existe.")

    id_agenda = db_obj.id_agenda
    
    agente_nombre = "Sistema"
    if id_agente_solicitante:
        ag = db.get_agente_by_id(id_agente_solicitante)
        if ag:
            agente_nombre = ag.nombre_completo

    exito = db.delete_inscripcion_visita(id_inscripcion)
    if exito:
        agenda = db.get_agenda_visita_by_id(id_agenda)
        if agenda:
            inscriptos_actuales = db.count_inscripciones_by_agenda(id_agenda)
            if inscriptos_actuales < agenda.cupo_maximo and agenda.estado == "completo":
                agenda.estado = "disponible"
                db.save_agenda_visita(agenda)
            
            # Registrar auditoría
            registrar_log_auditoria(
                id_agente=id_agente_solicitante,
                entidad="InscripcionVisita",
                id_entidad=id_inscripcion,
                accion="Cancelar",
                descripcion=f"El agente {agente_nombre} canceló la inscripción de {db_obj.nombre_visitante} a la agenda #{id_agenda}."
            )
        return True
    return False


def obtener_contratos_por_vencer(dias_anticipacion: int = 90) -> List[dict]:
    """
    Retorna contratos de alquiler activos que vencerán en los próximos dias_anticipacion días.
    Asume una duración típica de 2 años (730 días) para contratos de alquiler desde la fecha de firma.
    """
    contratos = db.list_contratos()
    por_vencer = []
    hoy = date.today()

    for c in contratos:
        if c.estado == "activo" and c.tipo_contrato.lower() == "alquiler" and c.fecha_contrato:
            vencimiento = c.fecha_contrato + timedelta(days=730)
            dias_restantes = (vencimiento - hoy).days
            if 0 <= dias_restantes <= dias_anticipacion:
                cliente = db.get_cliente_by_id(c.id_cliente)
                propiedad = db.get_propiedad_by_id(c.id_propiedad)
                por_vencer.append({
                    "contrato": c,
                    "cliente": cliente,
                    "propiedad": propiedad,
                    "fecha_vencimiento": vencimiento,
                    "dias_restantes": dias_restantes,
                })
    
    por_vencer.sort(key=lambda x: x["dias_restantes"])
    return por_vencer


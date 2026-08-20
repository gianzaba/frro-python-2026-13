from datetime import date, datetime
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
)

# Import Data Access Layer (aliased to db to conform to guidelines)
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
    Registra un nuevo agente con contraseña encriptada y asignación de rol ("Estándar" o "Administrador").
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
    Registra un propietario de propiedades.
    """
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
    estado: str = "disponible",
    fecha_disponibilidad: Optional[date] = None,
) -> PropiedadBO:
    """
    Registra una propiedad para la venta o alquiler con su fecha de disponibilidad.
    """
    # Verificar que exista el propietario
    prop = db.get_propietario_by_id(id_propietario)
    if not prop:
        raise ValueError("El propietario especificado no existe.")

    bo = PropiedadBO(
        id=None,
        direccion=direccion,
        tipo=tipo,
        zona=zona,
        estado=estado,
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
    Asigna un agente a una propiedad.
    REGLA DE NEGOCIO 2: El agente no debe tener otra asignación activa que se superponga.
    """
    agente = db.get_agente_by_id(id_agente)
    if not agente:
        raise ValueError("El agente especificado no existe.")

    propiedad = db.get_propiedad_by_id(id_propiedad)
    if not propiedad:
        raise ValueError("La propiedad especificada no existe.")

    if hasta and desde > hasta:
        raise ValueError(
            "La fecha de inicio de asignación debe ser anterior a la fecha de fin."
        )

    # Validar superposición de asignaciones para este agente
    assignments = db.get_active_assignments_by_agent(id_agente)
    for assoc in assignments:
        # Rule: agent cannot be assigned if they have overlaps in this period
        a_start = assoc.fecha_hora_desde
        a_end = assoc.fecha_hora_hasta or datetime.max

        b_start = desde
        b_end = hasta or datetime.max

        if a_start <= b_end and b_start <= a_end:
            raise ValueError(
                f"El agente ya está asignado a la propiedad con ID {assoc.id_propiedad} "
                f"en un período que se superpone ({a_start.strftime('%Y-%m-%d %H:%M')} - "
                f"{assoc.fecha_hora_hasta.strftime('%Y-%m-%d %H:%M') if assoc.fecha_hora_hasta else 'actualidad'})."
            )

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
    tipo_contrato: str = "Alquiler",
    ruta_documento_respaldo: Optional[str] = None,
    fecha_solicitud: Optional[date] = None,
) -> ContratoBO:
    """
    Crea una solicitud de contrato especificando tipo (Alquiler/Compraventa) y documento de respaldo.
    REGLA DE NEGOCIO 3: El agente que realiza el contrato debe estar asignado a la propiedad.
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

    # Verificar si el agente está asignado a la propiedad actualmente
    assignment = db.get_active_agent_assignment_for_property(id_propiedad)
    if not assignment or assignment.id_agente != id_agente:
        raise ValueError(
            "El agente seleccionado no está asignado actualmente a esta propiedad."
        )

    bo = ContratoBO(
        nro_contrato=None,
        fecha_solicitud=fecha_solicitud or date.today(),
        estado="solicitado",
        fecha_contrato=None,
        id_cliente=id_cliente,
        id_agente=id_agente,
        id_propiedad=id_propiedad,
        monto=monto,
        comision_porcentaje=comision_porcentaje,
        tipo_contrato=tipo_contrato,
        ruta_documento_respaldo=ruta_documento_respaldo,
    )
    return db.save_contrato(bo)


def firmar_contrato(nro_contrato: int) -> ContratoBO:
    """
    Firma y activa un contrato solicitado.
    REGLA DE NEGOCIO 1: Solo se puede firmar si la propiedad está disponible.
    Actualiza el estado de la propiedad a 'alquilada' o 'vendida' según el tipo.
    """
    contrato = db.get_contrato_by_id(nro_contrato)
    if not contrato:
        raise ValueError("El contrato especificado no existe.")

    if contrato.estado == "activo":
        raise ValueError("El contrato ya está firmado y activo.")

    propiedad = db.get_propiedad_by_id(contrato.id_propiedad)
    if not propiedad:
        raise ValueError("La propiedad asociada al contrato no existe.")

    # REGLA DE NEGOCIO 1: Propiedad debe estar disponible
    if propiedad.estado != "disponible":
        raise ValueError(
            f"La propiedad no está disponible. Estado actual: {propiedad.estado}"
        )

    # REGLA DE NEGOCIO 3 (Double check at signing time): Agente debe estar asignado
    assignment = db.get_active_agent_assignment_for_property(
        contrato.id_propiedad
    )
    if not assignment or assignment.id_agente != contrato.id_agente:
        raise ValueError(
            "El agente del contrato ya no está asignado a esta propiedad."
        )

    # Firmar contrato
    contrato.estado = "activo"
    contrato.fecha_contrato = date.today()
    db.save_contrato(contrato)

    # Actualizar estado de propiedad
    # Determinamos el estado final en base al tipo de propiedad
    if propiedad.tipo.lower() == "alquiler":
        propiedad.estado = "alquilada"
    elif propiedad.tipo.lower() == "venta":
        propiedad.estado = "vendida"
    else:
        propiedad.estado = "contratada"

    db.save_propiedad(propiedad)
    return contrato


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


def registrar_pago_inquilino(
    nro_contrato: int,
    mes: str,
    monto: float,
    fecha_pago: Optional[date] = None,
) -> PagoInquilinoBO:
    """
    Registra el pago de alquiler realizado por un inquilino.
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

    bo = PagoInquilinoBO(
        id=None,
        nro_contrato=nro_contrato,
        fecha_pago=fecha_pago or date.today(),
        monto=monto,
        mes_correspondiente=mes,
    )
    return db.save_pago_inquilino(bo)


def calcular_dias_vacante(propiedad: PropiedadBO) -> int:
    """
    Calcula el tiempo que una propiedad lleva inactiva / vacante ("tiempo sin alquilar" o "tiempo sin vender")
    restando la fecha actual con la fecha_disponibilidad de la propiedad.
    """
    if not propiedad or not propiedad.fecha_disponibilidad:
        return 0
    hoy = date.today()
    diferencia = (hoy - propiedad.fecha_disponibilidad).days
    return max(0, diferencia)


def obtener_ranking_propiedades_vacantes() -> List[dict]:
    """
    KPI para el Dashboard: Genera un ranking de propiedades vacantes (estado 'disponible')
    ordenadas de mayor a menor tiempo sin alquilar/vender.
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


def generar_liquidaciones_mes(
    mes_correspondiente: str,
    id_agente_solicitante: Optional[int] = None,
) -> List[PagoPropietarioBO]:
    """
    REGLA DE NEGOCIO 4: Genera liquidaciones a propietarios para contratos activos.
    Verifica que el agente solicitante tenga el rol de 'Administrador'.
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

        # Verificar si el inquilino pagó el alquiler
        pago_inq = db.get_pago_inquilino_by_period(
            c.nro_contrato, mes_correspondiente
        )
        if not pago_inq:
            continue

        # Evitar duplicados
        existing_payout = db.get_pago_propietario_by_period(
            c.nro_contrato, mes_correspondiente
        )
        if existing_payout:
            continue

        # Calcular valores
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
    Verifica que el agente solicitante tenga el rol de 'Administrador'.
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
    return db.save_pago_propietario(payout)


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
    Genera un archivo CSV con el reporte de cobros de inquilinos o transferencias a propietarios.
    Valida que el agente solicitante tenga el rol de 'Administrador'.
    """
    if id_agente_solicitante and not es_administrador(id_agente_solicitante):
        raise PermissionError(
            "Acceso denegado: Solo los Administradores pueden exportar reportes financieros."
        )

    lines = []
    if tipo_reporte == "cobros":
        lines.append("ID Pago,Fecha Pago,Nro Contrato,Cliente,Mes,Monto")
        pagos = db.list_pagos_inquilinos()
        for p in pagos:
            c = db.get_contrato_by_id(p.nro_contrato)
            cliente = db.get_cliente_by_id(c.id_cliente) if c else None
            cliente_nombre = cliente.nombre_completo if cliente else "N/A"
            lines.append(
                f"{p.id},{p.fecha_pago},{p.nro_contrato},\"{cliente_nombre}\",{p.mes_correspondiente},{p.monto:.2f}"
            )
    elif tipo_reporte == "liquidaciones":
        lines.append("ID Liquidacion,Período,Nro Contrato,Propietario,Monto Bruto,Comision,Monto Neto,Estado,Fecha Pago")
        liquidaciones = db.list_pagos_propietarios()
        for liq in liquidaciones:
            prop = db.get_propietario_by_id(liq.id_propietario)
            nombre_prop = prop.nombre_completo if prop else "N/A"
            fecha_pago_str = liq.fecha_pago.strftime("%Y-%m-%d") if liq.fecha_pago else "Pendiente"
            lines.append(
                f"{liq.id},{liq.mes_correspondiente},{liq.nro_contrato},\"{nombre_prop}\",{liq.monto_bruto:.2f},{liq.comision:.2f},{liq.monto_neto:.2f},{liq.estado},{fecha_pago_str}"
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
    Valida el rol de Administrador si se requiere consulta exclusiva.
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

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    abort,
    Response,
)
from functools import wraps
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Import Business Controller
import business.controller as controller

views_blueprint = Blueprint("views", __name__)

# --- Authentication Decorator ---


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "agente_id" not in session:
            flash(
                "Debes iniciar sesión para acceder a esta página.", "warning"
            )
            return redirect(url_for("views.login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        agente_id = session.get("agente_id")
        if not agente_id or not controller.es_administrador(agente_id):
            flash(
                "Acceso denegado: Se requieren permisos de Administrador para realizar esta acción.",
                "danger",
            )
            return redirect(url_for("views.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


# --- Context Processor for Global Variables ---


@views_blueprint.context_processor
def inject_user():
    agente_id = session.get("agente_id")
    es_admin = controller.es_administrador(agente_id) if agente_id else False
    return {
        "logged_in": "agente_id" in session,
        "current_username": session.get("agente_name", ""),
        "es_admin": es_admin,
        "agente_rol": session.get("agente_rol", "Estándar"),
    }


# --- HTTP Error Handlers ---


@views_blueprint.app_errorhandler(403)
def forbidden_error(error):
    return render_template("errors/403.html"), 403


@views_blueprint.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


# --- Authentication Routes ---


@views_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if "agente_id" in session:
        return redirect(url_for("views.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        agente = controller.autenticar_agente(email, password)
        if agente:
            session["agente_id"] = agente.id
            session["agente_name"] = agente.nombre_completo
            session["agente_rol"] = agente.rol
            flash(
                f"¡Bienvenido, {agente.nombre}! Has iniciado sesión ({agente.rol}).",
                "success",
            )
            return redirect(url_for("views.dashboard"))
        else:
            flash("Correo electrónico o contraseña incorrectos.", "danger")

    return render_template("login.html")


@views_blueprint.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("views.login"))


@views_blueprint.route("/admin/audit-logs")
@login_required
@admin_required
def audit_logs():
    agente_id = session.get("agente_id")
    logs = controller.listar_logs_auditoria(agente_id)
    
    enriched_logs = []
    for log in logs:
        agente = controller.obtener_agente(log.id_agente) if log.id_agente else None
        enriched_logs.append({
            "log": log,
            "agente": agente
        })
        
    return render_template("admin/audit_logs.html", logs=enriched_logs)


@views_blueprint.route("/visitas/inscripciones/<int:id_inscripcion>/cancelar", methods=["POST"])
@login_required
def inscripcion_cancelar(id_inscripcion: int):
    id_agenda = request.form.get("id_agenda", type=int)
    id_propiedad = request.form.get("id_propiedad", type=int)
    id_agente_solicitante = session.get("agente_id")
    try:
        controller.cancelar_inscripcion_visita(id_inscripcion, id_agente_solicitante=id_agente_solicitante)
        flash("Inscripción de visita cancelada exitosamente y cupo liberado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    if id_propiedad:
        return redirect(url_for("views.propiedad_visitas", id_propiedad=id_propiedad))
    return redirect(url_for("views.propiedades_list"))


# --- Dashboard Routes ---


@views_blueprint.route("/")
@views_blueprint.route("/dashboard")
@login_required
def dashboard():
    id_propietario = request.args.get("id_propietario", type=int)
    id_cliente = request.args.get("id_cliente", type=int)
    mes = request.args.get("mes", type=str)
    agente_id = session.get("agente_id")

    stats = controller.obtener_estadisticas_financieras(
        id_propietario=id_propietario,
        id_cliente=id_cliente,
        mes=mes,
        id_agente_solicitante=agente_id,
    )

    propiedades = controller.listar_propiedades(id_agente=agente_id)
    disponibles = sum(
        1 for p in propiedades if p.estado.lower() == "disponible"
    )
    alquiladas = sum(1 for p in propiedades if p.estado.lower() == "alquilada")
    vendidas = sum(1 for p in propiedades if p.estado.lower() == "vendida")

    clientes = controller.listar_clientes(id_agente=agente_id)
    propietarios = controller.listar_propietarios(id_agente=agente_id)
    contratos = controller.listar_contratos(id_agente=agente_id)
    ranking_vacantes = controller.obtener_ranking_propiedades_vacantes()

    cobrado_mes = stats.get("total_cobrado_mes", 0.0)
    pendiente_cobrar_mes = stats.get("total_pendiente_cobrar_mes", 0.0)
    total_esperado = cobrado_mes + pendiente_cobrar_mes
    cobro_eficiencia = (
        round((cobrado_mes / total_esperado) * 100, 1)
        if total_esperado > 0
        else 100.0
    )

    dashboard_stats = {
        "total_propiedades": len(propiedades),
        "disponibles": disponibles,
        "alquiladas": alquiladas,
        "vendidas": vendidas,
        "clientes_count": len(clientes),
        "propietarios_count": len(propietarios),
        "contratos_count": len(contratos),
        "cobrado_mes": cobrado_mes,
        "pendiente_cobrar_mes": pendiente_cobrar_mes,
        "pendiente_pagar_propietario": stats.get(
            "total_pendiente_pagar_propietario", 0.0
        ),
        "comisiones": stats.get("total_comisiones", 0.0),
        "cobro_eficiencia": cobro_eficiencia,
        "contratos_atrasados": stats.get("contratos_atrasados", []),
        "ranking_vacantes": ranking_vacantes,
        "periodo": stats.get("periodo", datetime.now().strftime("%Y-%m")),
    }

    return render_template(
        "dashboard.html",
        stats=dashboard_stats,
        propietarios=propietarios,
        clientes=clientes,
        selected_propietario=id_propietario,
        selected_cliente=id_cliente,
        selected_mes=mes or datetime.now().strftime("%Y-%m"),
    )


# --- Propiedades Routes ---


@views_blueprint.route("/propiedades")
@login_required
def propiedades_list():
    agente_id = session.get("agente_id")
    propiedades = controller.listar_propiedades(id_agente=agente_id)
    prop_with_owners = []
    for p in propiedades:
        propietario = controller.obtener_propietario(p.id_propietario)
        active_assignment = (
            controller.obtener_asignacion_activa_propiedad(p.id)
        )
        agente = (
            controller.obtener_agente(active_assignment.id_agente)
            if active_assignment
            else None
        )
        prop_with_owners.append(
            {
                "propiedad": p,
                "propietario": propietario,
                "agente_asignado": agente,
            }
        )
    return render_template(
        "propiedades/list.html", propiedades=prop_with_owners
    )


@views_blueprint.route("/propiedades/inactivas")
@login_required
def propiedades_inactivas():
    analisis = controller.obtener_analisis_propiedades_inactivas()
    return render_template("propiedades/inactivas.html", analisis=analisis)


@views_blueprint.route("/propiedades/nueva", methods=["GET", "POST"])
@login_required
def propiedad_crear():
    agente_id = session.get("agente_id")
    propietarios = controller.listar_propietarios(id_agente=agente_id)

    if request.method == "POST":
        direccion = request.form.get("direccion", "").strip()
        tipo = request.form.get("tipo", "")
        zona = request.form.get("zona", "").strip()
        id_propietario = request.form.get("id_propietario", type=int)

        try:
            controller.registrar_propiedad(
                direccion, tipo, zona, id_propietario
            )
            flash("Propiedad registrada exitosamente.", "success")
            return redirect(url_for("views.propiedades_list"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template(
        "propiedades/form.html", propietarios=propietarios
    )


@views_blueprint.route("/propiedades/<int:id_propiedad>")
@login_required
def propiedad_detalle(id_propiedad: int):
    agente_id = session.get("agente_id")
    
    # Verificar si el agente tiene permiso para acceder a esta propiedad
    if not controller.puede_acceder_propiedad(agente_id, id_propiedad):
        flash(
            "No tienes permiso para acceder a esta propiedad.",
            "danger",
        )
        return redirect(url_for("views.propiedades_list"))
    
    p = controller.obtener_propiedad(id_propiedad)
    if not p:
        abort(404)

    propietario = controller.obtener_propietario(p.id_propietario)
    assignment = controller.obtener_asignacion_activa_propiedad(p.id)
    agente = (
        controller.obtener_agente(assignment.id_agente) if assignment else None
    )

    contratos = controller.listar_contratos(id_agente=session.get("agente_id"))
    contratos_prop = []
    for c in contratos:
        if c.id_propiedad == p.id:
            cliente = controller.obtener_cliente(c.id_cliente)
            agente_c = controller.obtener_agente(c.id_agente)
            contratos_prop.append(
                {"contrato": c, "cliente": cliente, "agente": agente_c}
            )

    return render_template(
        "propiedades/detail.html",
        p=p,
        propietario=propietario,
        agente_asignado=agente,
        assignment=assignment,
        contratos=contratos_prop,
    )


@views_blueprint.route(
    "/propiedades/<int:id_propiedad>/asignar", methods=["GET", "POST"]
)
@login_required
def propiedad_asignar(id_propiedad: int):
    agente_id = session.get("agente_id")
    
    # Solo admin puede asignar agentes
    if not controller.es_administrador(agente_id):
        flash(
            "No tienes permiso para asignar agentes a propiedades.",
            "danger",
        )
        return redirect(url_for("views.propiedades_list"))
    
    p = controller.obtener_propiedad(id_propiedad)
    if not p:
        abort(404)

    agentes = controller.listar_agentes()

    if request.method == "POST":
        id_agente = request.form.get("id_agente", type=int)
        desde_str = request.form.get("desde", "")
        hasta_str = request.form.get("hasta", "")

        try:
            desde = datetime.strptime(desde_str, "%Y-%m-%dT%H:%M")
            hasta = (
                datetime.strptime(hasta_str, "%Y-%m-%dT%H:%M")
                if hasta_str
                else None
            )

            controller.asignar_agente_a_propiedad(
                id_agente, p.id, desde, hasta
            )
            flash("Agente asignado a la propiedad exitosamente.", "success")
            return redirect(
                url_for("views.propiedad_detalle", id_propiedad=p.id)
            )
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Formato de fecha inválido.", "danger")

    return render_template("propiedades/asignar.html", p=p, agentes=agentes)


# --- Visitas & Agenda Routes ---


@views_blueprint.route("/propiedades/<int:id_propiedad>/visitas")
@login_required
def propiedad_visitas(id_propiedad: int):
    agente_id = session.get("agente_id")
    
    # Verificar si el agente tiene permiso para acceder a esta propiedad
    if not controller.puede_acceder_propiedad(agente_id, id_propiedad):
        flash(
            "No tienes permiso para acceder a esta propiedad.",
            "danger",
        )
        return redirect(url_for("views.propiedades_list"))
    
    p = controller.obtener_propiedad(id_propiedad)
    if not p:
        abort(404)

    agendas = controller.listar_agendas_propiedad_con_metricas(id_propiedad)
    agentes = controller.listar_agentes()
    clientes = controller.listar_clientes()

    return render_template(
        "propiedades/visitas.html",
        propiedad=p,
        agendas=agendas,
        agentes=agentes,
        clientes=clientes,
    )


@views_blueprint.route(
    "/propiedades/<int:id_propiedad>/visitas/crear", methods=["POST"]
)
@login_required
def agenda_visita_crear(id_propiedad: int):
    fecha_hora_str = request.form.get("fecha_hora_visita", "")
    duracion = request.form.get("duracion_minutos", type=int) or 30
    cupo = request.form.get("cupo_maximo", type=int) or 3
    id_agente = request.form.get("id_agente", type=int) or session.get("agente_id")

    try:
        fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%dT%H:%M")
        controller.crear_agenda_visita(
            id_propiedad=id_propiedad,
            id_agente=id_agente,
            fecha_hora_visita=fecha_hora,
            duracion_minutos=duracion,
            cupo_maximo=cupo,
        )
        flash("Turno de visita agendado exitosamente con cupo limitado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Error al registrar el turno de visita.", "danger")

    return redirect(url_for("views.propiedad_visitas", id_propiedad=id_propiedad))


@views_blueprint.route("/visitas/<int:id_agenda>/inscribir", methods=["POST"])
@login_required
def agenda_visita_inscribir(id_agenda: int):
    id_propiedad = request.form.get("id_propiedad", type=int)
    nombre = request.form.get("nombre_visitante", "").strip()
    telefono = request.form.get("telefono_visitante", "").strip()
    email = request.form.get("email_visitante", "").strip()
    id_cliente = request.form.get("id_cliente", type=int)
    observaciones = request.form.get("observaciones", "").strip()

    try:
        controller.inscribir_visitante_a_turno(
            id_agenda=id_agenda,
            nombre_visitante=nombre,
            telefono_visitante=telefono,
            email_visitante=email,
            id_cliente=id_cliente,
            observaciones=observaciones,
        )
        flash("Visitante inscripto exitosamente en el turno.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    if id_propiedad:
        return redirect(url_for("views.propiedad_visitas", id_propiedad=id_propiedad))
    return redirect(url_for("views.propiedades_list"))


@views_blueprint.route("/visitas/<int:id_agenda>/cancelar", methods=["POST"])
@login_required
def agenda_visita_cancelar(id_agenda: int):
    id_propiedad = request.form.get("id_propiedad", type=int)
    try:
        controller.cancelar_agenda_visita(id_agenda)
        flash("Turno de visita cancelado exitosamente.", "info")
    except ValueError as e:
        flash(str(e), "danger")

    if id_propiedad:
        return redirect(url_for("views.propiedad_visitas", id_propiedad=id_propiedad))
    return redirect(url_for("views.propiedades_list"))


# --- Clientes Routes ---


@views_blueprint.route("/clientes")
@login_required
def clientes_list():
    agente_id = session.get("agente_id")
    clientes = controller.listar_clientes(id_agente=agente_id)
    return render_template("clientes/list.html", clientes=clientes)


@views_blueprint.route("/clientes/nuevo", methods=["GET", "POST"])
@login_required
def cliente_crear():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        email = request.form.get("email", "").strip()
        tipo_doc = request.form.get("tipo_doc", "")
        nro_doc = request.form.get("nro_doc", "").strip()
        domicilio = request.form.get("domicilio", "").strip()
        telefono = request.form.get("telefono", "").strip()
        agente_id = session.get("agente_id")

        try:
            controller.registrar_cliente(
                nombre, apellido, email, tipo_doc, nro_doc, domicilio, telefono,
                id_agente_creador=agente_id
            )
            flash("Cliente registrado exitosamente.", "success")
            return redirect(url_for("views.clientes_list"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("clientes/form.html")


# --- Propietarios Routes ---


@views_blueprint.route("/propietarios")
@login_required
def propietarios_list():
    agente_id = session.get("agente_id")
    propietarios = controller.listar_propietarios(id_agente=agente_id)
    return render_template("propietarios/list.html", propietarios=propietarios)


@views_blueprint.route("/propietarios/nuevo", methods=["GET", "POST"])
@login_required
def propietario_crear():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        email = request.form.get("email", "").strip()
        tipo_doc = request.form.get("tipo_doc", "")
        nro_doc = request.form.get("nro_doc", "").strip()
        domicilio = request.form.get("domicilio", "").strip()
        telefono = request.form.get("telefono", "").strip()
        agente_id = session.get("agente_id")

        try:
            controller.registrar_propietario(
                nombre, apellido, email, tipo_doc, nro_doc, domicilio, telefono,
                id_agente_creador=agente_id
            )
            flash("Propietario registrado exitosamente.", "success")
            return redirect(url_for("views.propietarios_list"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("propietarios/form.html")


# --- Contratos Routes ---


@views_blueprint.route("/contratos")
@login_required
def contratos_list():
    contratos = controller.listar_contratos(id_agente=session.get("agente_id"))
    contratos_info = []
    for c in contratos:
        cliente = controller.obtener_cliente(c.id_cliente)
        agente = controller.obtener_agente(c.id_agente)
        propiedad = controller.obtener_propiedad(c.id_propiedad)
        contratos_info.append(
            {
                "contrato": c,
                "cliente": cliente,
                "agente": agente,
                "propiedad": propiedad,
            }
        )
    return render_template("contratos/list.html", contratos=contratos_info)


@views_blueprint.route("/contratos/nuevo", methods=["GET", "POST"])
@login_required
def contrato_crear():
    agente_id = session.get("agente_id")
    clientes = controller.listar_clientes(id_agente=agente_id)
    propiedades = controller.listar_propiedades(id_agente=agente_id)

    # Filtrar solo propiedades disponibles con agentes asignados
    propiedades_disponibles = []
    for p in propiedades:
        if p.estado == "disponible":
            assignment = (
                controller.obtener_asignacion_activa_propiedad(p.id)
            )
            if assignment:
                agente = controller.obtener_agente(assignment.id_agente)
                propiedades_disponibles.append(
                    {"prop": p, "agente": agente, "assignment": assignment}
                )

    if request.method == "POST":
        id_cliente = request.form.get("id_cliente", type=int)
        prop_agente = request.form.get("prop_agente", "")
        if ":" in prop_agente:
            id_propiedad_str, id_agente_str = prop_agente.split(":")
            id_propiedad = int(id_propiedad_str)
            id_agente = int(id_agente_str)
        else:
            id_propiedad = request.form.get("id_propiedad", type=int)
            id_agente = request.form.get("id_agente", type=int)

        monto = request.form.get("monto", type=float)
        comision_porcentaje = request.form.get(
            "comision_porcentaje", type=float
        )
        comision_agente_porcentaje = (
            request.form.get("comision_agente_porcentaje", type=float) or 3.0
        )
        tipo_contrato = request.form.get("tipo_contrato", "Alquiler")
        recibos_sueldo_detalle = request.form.get("recibos_sueldo_detalle", "").strip()
        garantias_detalle = request.form.get("garantias_detalle", "").strip()

        # Manejo de archivo adjunto
        file = request.files.get("documento_respaldo")
        ruta_documento = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(
                upload_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            )
            file.save(filepath)
            ruta_documento = filepath

        def guardar_adjunto(nombre_campo):
            adjunto = request.files.get(nombre_campo)
            if not adjunto or not adjunto.filename:
                return None
            filename = secure_filename(adjunto.filename)
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(
                upload_dir,
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_campo}_{filename}",
            )
            adjunto.save(filepath)
            return filepath

        ruta_recibos = guardar_adjunto("recibos_sueldo")
        ruta_garantias = guardar_adjunto("garantias")

        try:
            controller.solicitar_contrato(
                id_cliente,
                id_agente,
                id_propiedad,
                monto,
                comision_porcentaje,
                comision_agente_porcentaje=comision_agente_porcentaje,
                tipo_contrato=tipo_contrato,
                ruta_documento_respaldo=ruta_documento,
                recibos_sueldo_detalle=recibos_sueldo_detalle,
                garantias_detalle=garantias_detalle,
                ruta_recibos_sueldo=ruta_recibos,
                ruta_garantias=ruta_garantias,
            )
            flash(
                "Solicitud de contrato creada exitosamente. Oferta enviada al propietario para su aprobación.",
                "success",
            )
            return redirect(url_for("views.contratos_list"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template(
        "contratos/form.html",
        clientes=clientes,
        propiedades=propiedades_disponibles,
    )


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/firmar", methods=["POST"]
)
@login_required
def contrato_firmar(nro_contrato: int):
    try:
        controller.firmar_contrato(nro_contrato, id_agente_solicitante=session.get("agente_id"))
        flash("Contrato firmado y activado exitosamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(
        url_for("views.contrato_detalle", nro_contrato=nro_contrato)
    )


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/decision-propietario", methods=["POST"]
)
@login_required
def contrato_decision_propietario(nro_contrato: int):
    decision = request.form.get("decision", "").strip().lower()
    observaciones = request.form.get("observaciones_propietario", "")
    if decision not in ("aprobar", "rechazar"):
        flash("Debe indicar si el propietario aprueba o rechaza la oferta.", "danger")
        return redirect(url_for("views.contrato_detalle", nro_contrato=nro_contrato))
    try:
        controller.decidir_contrato_propietario(
            nro_contrato, decision == "aprobar", observaciones
        )
        mensaje = "Oferta aprobada por el propietario." if decision == "aprobar" else "Oferta rechazada por el propietario."
        flash(mensaje, "success" if decision == "aprobar" else "warning")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("views.contrato_detalle", nro_contrato=nro_contrato))


@views_blueprint.route("/contratos/<int:nro_contrato>")
@login_required
def contrato_detalle(nro_contrato: int):
    try:
        contrato = controller.obtener_contrato(nro_contrato)
        if not contrato:
            abort(404)
        if not controller.puede_acceder_contrato(
            session.get("agente_id"), contrato
        ):
            flash("No tienes permiso para acceder a este contrato.", "danger")
            return redirect(url_for("views.contratos_list"))
        detalles = controller.obtener_detalle_contrato(nro_contrato)
        return render_template("contratos/detalle.html", **detalles)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("views.contratos_list"))


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/clausulas/agregar", methods=["POST"]
)
@login_required
def clausula_agregar(nro_contrato: int):
    titulo = request.form.get("titulo", "").strip()
    contenido = request.form.get("contenido", "").strip()

    if not titulo or not contenido:
        flash("El título y contenido de la cláusula son obligatorios.", "danger")
        return redirect(
            url_for("views.contrato_detalle", nro_contrato=nro_contrato)
        )

    try:
        controller.agregar_clausula_contrato(nro_contrato, titulo, contenido)
        flash("Cláusula agregada exitosamente al contrato.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(
        url_for("views.contrato_detalle", nro_contrato=nro_contrato)
    )


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/clausulas/<int:id_clausula>/editar",
    methods=["POST"],
)
@login_required
def clausula_editar(nro_contrato: int, id_clausula: int):
    titulo = request.form.get("titulo", "").strip()
    contenido = request.form.get("contenido", "").strip()

    try:
        controller.editar_clausula_contrato(
            nro_contrato, id_clausula, titulo, contenido
        )
        flash("Cláusula modificada exitosamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(
        url_for("views.contrato_detalle", nro_contrato=nro_contrato)
    )


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/clausulas/<int:id_clausula>/eliminar",
    methods=["POST"],
)
@login_required
def clausula_eliminar(nro_contrato: int, id_clausula: int):
    try:
        controller.eliminar_clausula_contrato(nro_contrato, id_clausula)
        flash("Cláusula eliminada del contrato.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(
        url_for("views.contrato_detalle", nro_contrato=nro_contrato)
    )


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/comision/actualizar", methods=["POST"]
)
@login_required
def contrato_comision_actualizar(nro_contrato: int):
    comision_porcentaje = request.form.get("comision_porcentaje", type=float)
    comision_agente_porcentaje = request.form.get(
        "comision_agente_porcentaje", type=float
    )

    if comision_porcentaje is None:
        flash("Debe ingresar un porcentaje de honorarios válido.", "danger")
        return redirect(
            url_for("views.contrato_detalle", nro_contrato=nro_contrato)
        )

    try:
        controller.modificar_comisiones_contrato(
            nro_contrato, comision_porcentaje, comision_agente_porcentaje
        )
        flash(
            "Porcentajes de honorarios y comisión actualizados exitosamente.",
            "success",
        )
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(
        url_for("views.contrato_detalle", nro_contrato=nro_contrato)
    )


@views_blueprint.route("/contratos/<int:nro_contrato>/imprimir")
@login_required
def contrato_imprimir(nro_contrato: int):
    try:
        detalles = controller.obtener_detalle_contrato(nro_contrato)
        return render_template("contratos/imprimir.html", **detalles)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("views.contratos_list"))


# --- Finanzas & Boletas Routes ---


@views_blueprint.route("/finanzas", methods=["GET"])
@login_required
def finanzas_dashboard():
    agente_id = session.get("agente_id")
    pagos_inquilinos = controller.listar_pagos_inquilinos(agente_id)
    liquidaciones = controller.listar_pagos_propietarios(agente_id)
    contratos = controller.listar_contratos(id_agente=agente_id)

    # Filter active contracts that belong to properties of type "Alquiler"
    active_lease_contratos = []
    for c in contratos:
        if c.estado == "activo":
            prop = controller.obtener_propiedad(c.id_propiedad)
            if prop and prop.tipo.lower() == "alquiler":
                cliente = controller.obtener_cliente(c.id_cliente)
                active_lease_contratos.append(
                    {"contrato": c, "cliente": cliente, "propiedad": prop}
                )

    # Calculations for stats cards
    total_cobrado = sum(
        getattr(p, "monto_total_abonado", p.monto) or p.monto
        for p in pagos_inquilinos
    )
    total_comision = sum(liq.comision for liq in liquidaciones)
    payout_pendiente = sum(
        liq.monto_neto for liq in liquidaciones if liq.estado == "pendiente"
    )

    enriched_pagos_inq = []
    for p in pagos_inquilinos:
        c = controller.obtener_contrato(p.nro_contrato)
        cliente = controller.obtener_cliente(c.id_cliente) if c else None
        prop = controller.obtener_propiedad(c.id_propiedad) if c else None
        enriched_pagos_inq.append({"pago": p, "cliente": cliente, "contrato": c, "propiedad": prop})

    enriched_liquidaciones = []
    for liq in liquidaciones:
        c = controller.obtener_contrato(liq.nro_contrato)
        propietario = controller.obtener_propietario(liq.id_propietario)
        enriched_liquidaciones.append(
            {"liq": liq, "propietario": propietario, "contrato": c}
        )

    estado_alquileres = controller.obtener_estado_cobros_alquileres_mes(
        id_agente=agente_id
    )
    contratos_por_vencer = controller.obtener_contratos_por_vencer(
        90, id_agente=agente_id
    )

    return render_template(
        "finanzas.html",
        pagos_inquilinos=enriched_pagos_inq,
        liquidaciones=enriched_liquidaciones,
        contratos=active_lease_contratos,
        estado_alquileres=estado_alquileres,
        total_cobrado=total_cobrado,
        total_comision=total_comision,
        payout_pendiente=payout_pendiente,
        contratos_por_vencer=contratos_por_vencer,
    )


@views_blueprint.route("/finanzas/pagos-inquilinos/nuevo", methods=["POST"])
@login_required
def pago_inquilino_crear():
    nro_contrato = request.form.get("nro_contrato", type=int)
    mes = request.form.get("mes", "").strip()
    monto = request.form.get("monto", type=float) or 0.0
    fecha_pago_str = request.form.get("fecha_pago", "").strip()
    fecha_pago = (
        datetime.strptime(fecha_pago_str, "%Y-%m-%d").date()
        if fecha_pago_str
        else None
    )

    # Manejo de comprobante adjunto
    file = request.files.get("comprobante")
    ruta_comprobante = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join("static", "uploads", "comprobantes")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(
            upload_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        )
        file.save(filepath)
        ruta_comprobante = filepath

    try:
        pago = controller.registrar_pago_inquilino(
            nro_contrato=nro_contrato,
            mes=mes,
            monto=monto,
            fecha_pago=fecha_pago,
            ruta_comprobante=ruta_comprobante,
            id_agente_solicitante=session.get("agente_id"),
        )
        if pago.dias_retraso > 0:
            flash(
                f"Pago registrado con {pago.dias_retraso} días de demora. "
                f"Recargo: ${pago.monto_recargo:.2f} (Total: ${pago.monto_total_abonado:.2f}).",
                "warning",
            )
        else:
            flash(f"Pago del período {mes} registrado exitosamente a término.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error al registrar el pago: {e}", "danger")

    return redirect(url_for("views.finanzas_dashboard"))


@views_blueprint.route("/finanzas/boleta/<int:nro_contrato>/<string:mes>")
@login_required
def boleta_alquiler(nro_contrato: int, mes: str):
    try:
        datos_boleta = controller.obtener_datos_boleta_alquiler(nro_contrato, mes)
        return render_template("finanzas/boleta.html", **datos_boleta)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("views.finanzas_dashboard"))


@views_blueprint.route("/finanzas/liquidar", methods=["POST"])
@login_required
@admin_required
def liquidar_mes():
    mes = request.form.get("mes", "").strip()
    agente_id = session.get("agente_id")
    try:
        liquidaciones = controller.generar_liquidaciones_mes(
            mes, id_agente_solicitante=agente_id
        )
        if liquidaciones:
            flash(
                f"Se generaron {len(liquidaciones)} liquidaciones de propietarios para el período {mes}.",
                "success",
            )
        else:
            flash(
                f"No hay nuevos pagos cobrados por liquidar para el período {mes}.",
                "warning",
            )
    except (ValueError, PermissionError) as e:
        flash(str(e), "danger")
    except Exception:
        flash("Error al procesar las liquidaciones.", "danger")

    return redirect(url_for("views.finanzas_dashboard"))


@views_blueprint.route(
    "/finanzas/liquidaciones/<int:id_pago>/pagar", methods=["POST"]
)
@login_required
@admin_required
def liquidacion_pagar(id_pago: int):
    agente_id = session.get("agente_id")
    try:
        controller.registrar_transferencia_propietario(
            id_pago, id_agente_solicitante=agente_id
        )
        flash(
            "Transferencia al propietario registrada exitosamente.", "success"
        )
    except (ValueError, PermissionError) as e:
        flash(str(e), "danger")
    except Exception:
        flash("Error al registrar la transferencia.", "danger")

    return redirect(url_for("views.finanzas_dashboard"))


@views_blueprint.route("/finanzas/exportar/<tipo_reporte>", methods=["GET"])
@login_required
@admin_required
def finanzas_exportar(tipo_reporte: str):
    agente_id = session.get("agente_id")
    try:
        csv_data = controller.exportar_reporte_financiero_csv(
            tipo_reporte, id_agente_solicitante=agente_id
        )
        filename = f"reporte_{tipo_reporte}_{datetime.now().strftime('%Y%m%d')}.csv"
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )
    except (ValueError, PermissionError) as e:
        flash(str(e), "danger")
        return redirect(url_for("views.finanzas_dashboard"))


@views_blueprint.route(
    "/finanzas/notificaciones/mora", methods=["POST"]
)
@login_required
@admin_required
def finanzas_enviar_alertas_mora():
    agente_id = session.get("agente_id")
    mes = request.form.get("mes", "").strip() or None
    try:
        resultado = controller.enviar_alertas_mora_inquilinos(
            mes=mes, id_agente_solicitante=agente_id
        )
        total_env = resultado["total_enviados"]
        if total_env > 0:
            flash(
                f"Se enviaron exitosamente {total_env} alertas de demora por correo a inquilinos "
                f"para el período {resultado['periodo']}.",
                "success",
            )
        else:
            flash(
                f"No se registraron nuevos inquilinos en demora pendientes de notificación "
                f"para el período {resultado['periodo']} (o ya fueron notificados en el día de hoy).",
                "info",
            )
    except (ValueError, PermissionError) as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error al procesar el envío de notificaciones: {e}", "danger")

    return redirect(url_for("views.finanzas_dashboard"))


@views_blueprint.route(
    "/finanzas/notificaciones/mora/contrato/<int:nro_contrato>",
    methods=["POST"],
)
@login_required
@admin_required
def finanzas_enviar_alerta_mora_individual(nro_contrato: int):
    agente_id = session.get("agente_id")
    mes = request.form.get("mes", "").strip() or None
    try:
        resultado = controller.enviar_alerta_mora_individual(
            nro_contrato=nro_contrato,
            mes=mes,
            id_agente_solicitante=agente_id,
        )
        flash(
            f"📧 Correo de Alerta de Demora enviado con éxito a {resultado['inquilino']} "
            f"({resultado['email']}) por el Contrato #{resultado['nro_contrato']} "
            f"(Período {resultado['periodo']} - {resultado['dias_retraso']} días de retraso - "
            f"Total: ${resultado['monto_total']:,.2f}).",
            "success",
        )
    except (ValueError, PermissionError) as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error al enviar correo de alerta: {e}", "danger")

    return redirect(url_for("views.finanzas_dashboard"))


# --- Reclamos e Incidencias Routes ---


@views_blueprint.route("/reclamos")
@login_required
def reclamos_dashboard():
    agente_id = session.get("agente_id")
    estado_filtro = request.args.get("estado", "").strip()
    nro_contrato_filtro = request.args.get("nro_contrato", type=int)

    reclamos_detallados = controller.listar_reclamos_con_detalle(
        nro_contrato=nro_contrato_filtro,
        estado=estado_filtro if estado_filtro else None,
        id_agente=agente_id,
    )

    todos_reclamos = [
        r["reclamo"]
        for r in controller.listar_reclamos_con_detalle(id_agente=agente_id)
    ]
    total_reclamos = len(todos_reclamos)
    total_pendientes = len(
        [r for r in todos_reclamos if r.estado == "pendiente"]
    )
    total_en_reparacion = len(
        [
            r
            for r in todos_reclamos
            if r.estado in ["informado_propietario", "en_reparacion"]
        ]
    )
    total_resueltos = len(
        [r for r in todos_reclamos if r.estado == "resuelto"]
    )
    total_presupuesto = sum(r.presupuesto_estimado for r in todos_reclamos)

    return render_template(
        "reclamos/list.html",
        reclamos=reclamos_detallados,
        total_reclamos=total_reclamos,
        total_pendientes=total_pendientes,
        total_en_reparacion=total_en_reparacion,
        total_resueltos=total_resueltos,
        total_presupuesto=total_presupuesto,
        estado_filtro=estado_filtro,
        nro_contrato_filtro=nro_contrato_filtro,
    )


@views_blueprint.route("/reclamos/nuevo", methods=["GET", "POST"])
@login_required
def reclamo_nuevo():
    nro_contrato_param = request.args.get("nro_contrato", type=int)
    contratos_activos = [
        c
        for c in controller.listar_contratos(id_agente=session.get("agente_id"))
        if c.estado == "activo"
    ]
    contratos_opciones = []
    for c in contratos_activos:
        cli = controller.obtener_cliente(c.id_cliente)
        prop = controller.obtener_propiedad(c.id_propiedad)
        contratos_opciones.append(
            {
                "contrato": c,
                "cliente": cli,
                "propiedad": prop,
            }
        )

    if request.method == "POST":
        nro_contrato = request.form.get("nro_contrato", type=int)
        tipo_dano = request.form.get("tipo_dano", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        urgencia = request.form.get("urgencia", "Media")
        presupuesto = (
            request.form.get("presupuesto_estimado", type=float) or 0.0
        )

        try:
            reclamo = controller.registrar_reclamo(
                nro_contrato=nro_contrato,
                tipo_dano=tipo_dano,
                descripcion=descripcion,
                urgencia=urgencia,
                presupuesto_estimado=presupuesto,
            )
            flash(
                f"Reclamo #{reclamo.id} registrado exitosamente para el contrato #{nro_contrato}.",
                "success",
            )
            return redirect(url_for("views.reclamos_dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Error al registrar reclamo: {e}", "danger")

    return render_template(
        "reclamos/form.html",
        contratos=contratos_opciones,
        nro_contrato_seleccionado=nro_contrato_param,
    )


@views_blueprint.route(
    "/reclamos/<int:id_reclamo>/estado", methods=["POST"]
)
@login_required
def reclamo_actualizar_estado(id_reclamo: int):
    nuevo_estado = request.form.get("nuevo_estado", "").strip()
    presupuesto = request.form.get("presupuesto_estimado", type=float)
    observaciones = request.form.get("observaciones_resolucion", "").strip()
    origen = request.form.get("origen", "reclamos")

    try:
        detalles = controller.obtener_detalle_reclamo(id_reclamo)
        if not controller.puede_acceder_contrato(
            session.get("agente_id"), detalles["contrato"]
        ):
            flash("No tienes permiso para modificar este reclamo.", "danger")
            return redirect(url_for("views.reclamos_dashboard"))
        controller.actualizar_estado_reclamo(
            id_reclamo=id_reclamo,
            nuevo_estado=nuevo_estado,
            presupuesto_actualizado=presupuesto,
            observaciones_resolucion=observaciones,
        )
        flash(
            f"Estado del reclamo #{id_reclamo} actualizado a '{nuevo_estado}'.",
            "success",
        )
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error al actualizar estado del reclamo: {e}", "danger")

    if origen.startswith("contrato_"):
        nro_c = origen.replace("contrato_", "")
        return redirect(
            url_for("views.contrato_detalle", nro_contrato=int(nro_c))
        )
    return redirect(url_for("views.reclamos_dashboard"))


@views_blueprint.route("/reclamos/<int:id_reclamo>/presupuesto")
@login_required
def reclamo_presupuesto_informe(id_reclamo: int):
    try:
        detalles = controller.obtener_detalle_reclamo(id_reclamo)
        if not controller.puede_acceder_contrato(
            session.get("agente_id"), detalles["contrato"]
        ):
            flash("No tienes permiso para acceder a este reclamo.", "danger")
            return redirect(url_for("views.reclamos_dashboard"))
        return render_template("reclamos/presupuesto.html", **detalles)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("views.reclamos_dashboard"))


# --- Agentes Management Routes (Admin only) ---


@views_blueprint.route("/agentes")
@login_required
@admin_required
def agentes_list():
    agentes = controller.listar_agentes()
    return render_template("agentes/list.html", agentes=agentes)


@views_blueprint.route("/agentes/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def agente_crear():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        rol = request.form.get("rol", "Estándar")
        cuil = request.form.get("cuil", "").strip()
        matricula = request.form.get("matricula", "").strip()
        tipo_doc = request.form.get("tipo_doc", "DNI")
        nro_doc = request.form.get("nro_doc", "").strip()
        domicilio = request.form.get("domicilio", "").strip()
        telefono = request.form.get("telefono", "").strip()

        try:
            agente = controller.registrar_agente(
                nombre=nombre,
                apellido=apellido,
                email=email,
                password=password,
                cuil=cuil,
                matricula=matricula,
                tipo_doc=tipo_doc,
                nro_doc=nro_doc,
                domicilio=domicilio,
                telefono=telefono,
                rol=rol,
            )
            flash(
                f"Agente {agente.nombre_completo} ({agente.rol}) registrado exitosamente.",
                "success",
            )
            return redirect(url_for("views.agentes_list"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Error al registrar agente: {e}", "danger")

    return render_template("agentes/form.html")

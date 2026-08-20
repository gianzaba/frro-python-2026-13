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
            flash("Credenciales inválidas. Inténtalo de nuevo.", "danger")

    return render_template("login.html")


@views_blueprint.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("views.login"))


# --- Main Application Routes ---


@views_blueprint.route("/")
@login_required
def dashboard():
    id_propietario = request.args.get("id_propietario", type=int)
    id_cliente = request.args.get("id_cliente", type=int)
    mes = request.args.get("mes", "").strip() or None

    # Get full entity lists for filter dropdowns
    propiedades = controller.listar_propiedades()
    clientes = controller.listar_clientes()
    propietarios = controller.listar_propietarios()
    contratos = controller.listar_contratos()

    # Simple catalog counts
    total_props = len(propiedades)
    props_avail = sum(1 for p in propiedades if p.estado == "disponible")
    props_rented = sum(1 for p in propiedades if p.estado == "alquilada")
    props_sold = sum(1 for p in propiedades if p.estado == "vendida")

    # Financial stats with filters
    stats_fin = controller.obtener_estadisticas_financieras(
        id_propietario=id_propietario, id_cliente=id_cliente, mes=mes
    )

    rentas_totales_mes = (
        stats_fin["total_cobrado_mes"]
        + stats_fin["total_pendiente_cobrar_mes"]
    )
    cobro_eficiencia = (
        (stats_fin["total_cobrado_mes"] / rentas_totales_mes * 100.0)
        if rentas_totales_mes > 0
        else 100.0
    )

    # Ranking de propiedades con más tiempo vacantes (KPI)
    ranking_vacantes = controller.obtener_ranking_propiedades_vacantes()

    stats = {
        "total_propiedades": total_props,
        "disponibles": props_avail,
        "alquiladas": props_rented,
        "vendidas": props_sold,
        "clientes_count": len(clientes),
        "propietarios_count": len(propietarios),
        "contratos_count": len(contratos),
        "cobrado_mes": stats_fin["total_cobrado_mes"],
        "pendiente_cobrar_mes": stats_fin["total_pendiente_cobrar_mes"],
        "pendiente_pagar_propietario": stats_fin[
            "total_pendiente_pagar_propietario"
        ],
        "comisiones": stats_fin["total_comisiones"],
        "contratos_atrasados": stats_fin["contratos_atrasados"],
        "periodo": stats_fin["periodo"],
        "cobro_eficiencia": round(cobro_eficiencia, 1),
        "ranking_vacantes": ranking_vacantes,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        clientes=clientes,
        propietarios=propietarios,
        selected_propietario=id_propietario,
        selected_cliente=id_cliente,
        selected_mes=stats_fin["periodo"],
    )


# --- Propiedades Routes ---


@views_blueprint.route("/propiedades")
@login_required
def propiedades_list():
    propiedades = controller.listar_propiedades()
    # Enriquecer con el propietario y el agente asignado actual
    enriched_props = []
    for p in propiedades:
        prop = controller.obtener_propietario(p.id_propietario)
        assignment = controller.obtener_asignacion_activa_propiedad(p.id)
        agente = (
            controller.obtener_agente(assignment.id_agente)
            if assignment
            else None
        )

        enriched_props.append(
            {"propiedad": p, "propietario": prop, "agente_asignado": agente}
        )
    return render_template("propiedades/list.html", propiedades=enriched_props)


@views_blueprint.route("/propiedades/nueva", methods=["GET", "POST"])
@login_required
def propiedad_crear():
    propietarios = controller.listar_propietarios()
    if request.method == "POST":
        direccion = request.form.get("direccion", "").strip()
        tipo = request.form.get("tipo", "")  # Alquiler / Venta / etc.
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

    return render_template("propiedades/form.html", propietarios=propietarios)


@views_blueprint.route("/propiedades/<int:id_propiedad>")
@login_required
def propiedad_detalle(id_propiedad: int):
    p = controller.obtener_propiedad(id_propiedad)
    if not p:
        abort(404)

    propietario = controller.obtener_propietario(p.id_propietario)
    assignment = controller.obtener_asignacion_activa_propiedad(p.id)
    agente = (
        controller.obtener_agente(assignment.id_agente) if assignment else None
    )

    # Filtrar contratos asociados a esta propiedad
    contratos = controller.listar_contratos()
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


# --- Clientes Routes ---


@views_blueprint.route("/clientes")
@login_required
def clientes_list():
    clientes = controller.listar_clientes()
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

        try:
            controller.registrar_cliente(
                nombre, apellido, email, tipo_doc, nro_doc, domicilio, telefono
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
    propietarios = controller.listar_propietarios()
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

        try:
            controller.registrar_propietario(
                nombre, apellido, email, tipo_doc, nro_doc, domicilio, telefono
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
    contratos = controller.listar_contratos()
    enriched_contratos = []
    for c in contratos:
        cliente = controller.obtener_cliente(c.id_cliente)
        agente = controller.obtener_agente(c.id_agente)
        prop = controller.obtener_propiedad(c.id_propiedad)
        enriched_contratos.append(
            {
                "contrato": c,
                "cliente": cliente,
                "agente": agente,
                "propiedad": prop,
            }
        )
    return render_template("contratos/list.html", contratos=enriched_contratos)


@views_blueprint.route("/contratos/nuevo", methods=["GET", "POST"])
@login_required
def contrato_crear():
    clientes = controller.listar_clientes()
    propiedades = controller.listar_propiedades()

    # Filter properties to only those that are 'disponible' and have an assigned agent
    available_props = []
    for p in propiedades:
        if p.estado == "disponible":
            assignment = controller.obtener_asignacion_activa_propiedad(p.id)
            if assignment:
                agente = controller.obtener_agente(assignment.id_agente)
                available_props.append({"prop": p, "agente": agente})

    if request.method == "POST":
        id_cliente = request.form.get("id_cliente", type=int)
        prop_agente_pair = request.form.get("prop_agente", "")

        if not prop_agente_pair:
            flash(
                "Debes seleccionar una propiedad disponible con agente asignado.",
                "danger",
            )
        else:
            try:
                # Format: "id_propiedad:id_agente"
                id_propiedad_str, id_agente_str = prop_agente_pair.split(":")
                id_propiedad = int(id_propiedad_str)
                id_agente = int(id_agente_str)
                monto = request.form.get("monto", type=float) or 0.0
                comision_porcentaje = (
                    request.form.get("comision_porcentaje", type=float) or 10.0
                )
                tipo_contrato = request.form.get("tipo_contrato", "Alquiler")

                # Manejo de archivo adjunto (contrato físico / garantías PDF o imágenes)
                file = request.files.get("documento_respaldo")
                ruta_documento = None
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    upload_dir = os.path.join("static", "uploads")
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
                    file.save(filepath)
                    ruta_documento = filepath

                controller.solicitar_contrato(
                    id_cliente,
                    id_agente,
                    id_propiedad,
                    monto,
                    comision_porcentaje,
                    tipo_contrato=tipo_contrato,
                    ruta_documento_respaldo=ruta_documento,
                )
                flash("Solicitud de contrato creada exitosamente.", "success")
                return redirect(url_for("views.contratos_list"))
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                flash(f"Error al procesar la solicitud: {e}", "danger")

    return render_template(
        "contratos/form.html", clientes=clientes, propiedades=available_props
    )


@views_blueprint.route(
    "/contratos/<int:nro_contrato>/firmar", methods=["POST"]
)
@login_required
def contrato_firmar(nro_contrato: int):
    try:
        controller.firmar_contrato(nro_contrato)
        flash(
            f"Contrato N° {nro_contrato} firmado y activado exitosamente.",
            "success",
        )
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("views.contratos_list"))


@views_blueprint.route("/contratos/<int:nro_contrato>/detalle")
@login_required
def contrato_detalle(nro_contrato: int):
    try:
        detalles = controller.obtener_detalles_contrato_completo(nro_contrato)
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
    try:
        controller.agregar_clausula_contrato(nro_contrato, titulo, contenido)
        flash("Cláusula agregada correctamente al contrato.", "success")
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
        controller.modificar_clausula_contrato(id_clausula, titulo, contenido)
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
        controller.eliminar_clausula_contrato(id_clausula)
        flash("Cláusula eliminada del contrato.", "info")
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
    if comision_porcentaje is None:
        flash("Debe ingresar un porcentaje de comisión válido.", "danger")
        return redirect(
            url_for("views.contrato_detalle", nro_contrato=nro_contrato)
        )

    try:
        controller.actualizar_comision_contrato(
            nro_contrato, comision_porcentaje
        )
        flash(
            f"Porcentaje de comisión del agente actualizado a {comision_porcentaje}%.",
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
        detalles = controller.obtener_detalles_contrato_completo(nro_contrato)
        return render_template("contratos/imprimir.html", **detalles)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("views.contratos_list"))



# --- Finanzas Routes ---


@views_blueprint.route("/finanzas", methods=["GET"])
@login_required
def finanzas_dashboard():
    pagos_inquilinos = controller.listar_pagos_inquilinos()
    liquidaciones = controller.listar_pagos_propietarios()
    contratos = controller.listar_contratos()

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
    total_cobrado = sum(p.monto for p in pagos_inquilinos)
    total_comision = sum(liq.comision for liq in liquidaciones)
    payout_pendiente = sum(
        liq.monto_neto for liq in liquidaciones if liq.estado == "pendiente"
    )

    # Enriched payments with contract/client information for list views
    enriched_pagos_inq = []
    for p in pagos_inquilinos:
        c = controller.obtener_contrato(p.nro_contrato)
        cliente = controller.obtener_cliente(c.id_cliente) if c else None
        enriched_pagos_inq.append({"pago": p, "cliente": cliente})

    enriched_liquidaciones = []
    for liq in liquidaciones:
        c = controller.obtener_contrato(liq.nro_contrato)
        propietario = controller.obtener_propietario(liq.id_propietario)
        enriched_liquidaciones.append(
            {"liq": liq, "propietario": propietario, "contrato": c}
        )

    return render_template(
        "finanzas.html",
        pagos_inquilinos=enriched_pagos_inq,
        liquidaciones=enriched_liquidaciones,
        contratos=active_lease_contratos,
        total_cobrado=total_cobrado,
        total_comision=total_comision,
        payout_pendiente=payout_pendiente,
    )


@views_blueprint.route("/finanzas/pagos-inquilinos/nuevo", methods=["POST"])
@login_required
def pago_inquilino_crear():
    nro_contrato = request.form.get("nro_contrato", type=int)
    mes = request.form.get("mes", "").strip()
    monto = request.form.get("monto", type=float) or 0.0

    try:
        controller.registrar_pago_inquilino(nro_contrato, mes, monto)
        flash(f"Pago del período {mes} registrado exitosamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Error al registrar el pago.", "danger")

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

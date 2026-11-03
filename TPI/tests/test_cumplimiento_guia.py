import io
import os
from datetime import date, datetime

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import business.controller as controller  # noqa: E402
import datos.db as db  # noqa: E402
from app import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    db.init_db(reset=True)
    yield
    db.Base.metadata.drop_all(bind=db.engine)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _agente(email, doc, rol="Estándar"):
    return controller.registrar_agente(
        "Ag", "Test", email, "pass123", f"20-{doc}-9", f"MAT-{doc}",
        "DNI", doc, "Calle 1", "341000", rol,
    )


def _base():
    admin = _agente("admin@t.com", "10000001", "Administrador")
    owner = controller.registrar_propietario(
        "Mario", "Dueño", "mario@t.com", "DNI", "20000001", "Mitre 1", "341111"
    )
    cliente = controller.registrar_cliente(
        "Laura", "Inq", "laura@t.com", "DNI", "30000001", "Rioja 1", "341222"
    )
    prop = controller.registrar_propiedad(
        "Oroño 100", "Departamento", "Centro", owner.id, tipo_operacion="Alquiler"
    )
    controller.asignar_agente_a_propiedad(admin.id, prop.id, datetime(2026, 1, 1))
    contrato = controller.solicitar_contrato(
        cliente.id, admin.id, prop.id, monto=100000.0,
        comision_porcentaje=10.0, tipo_contrato="Alquiler",
    )
    return admin, owner, cliente, prop, contrato


def _login(client, agente):
    with client.session_transaction() as sess:
        sess["agente_id"] = agente.id
        sess["agente_name"] = agente.nombre_completo
        sess["agente_rol"] = agente.rol


# --- Modelo de propiedad ---

def test_propiedad_valida_tipo_y_operacion():
    owner = controller.registrar_propietario(
        "M", "D", "m@t.com", "DNI", "20000002", "x", "1"
    )
    with pytest.raises(ValueError):
        controller.registrar_propiedad("Dir", "Alquiler", "Centro", owner.id)
    with pytest.raises(ValueError):
        controller.registrar_propiedad(
            "Dir", "Casa", "Centro", owner.id, tipo_operacion="Permuta"
        )
    p = controller.registrar_propiedad(
        "Dir", "Local", "Centro", owner.id, tipo_operacion="Venta"
    )
    assert (p.tipo, p.tipo_operacion) == ("Local", "Venta")


def test_contrato_debe_coincidir_con_operacion_de_la_propiedad():
    admin, owner, cliente, _, _ = _base()
    venta = controller.registrar_propiedad(
        "Sur 5", "Casa", "Sur", owner.id, tipo_operacion="Venta"
    )
    controller.asignar_agente_a_propiedad(admin.id, venta.id, datetime(2026, 1, 1))
    with pytest.raises(ValueError, match="venta"):
        controller.solicitar_contrato(
            cliente.id, admin.id, venta.id, 50000.0, 10.0, tipo_contrato="Alquiler"
        )


def test_migracion_tipo_operacion_desde_esquema_legado():
    from sqlalchemy import text
    owner = controller.registrar_propietario(
        "M", "D", "m2@t.com", "DNI", "20000003", "x", "1"
    )
    controller.registrar_propiedad("Alberdi 850, Casa con Jardín", "Casa", "A", owner.id)
    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE propiedad DROP COLUMN tipo_operacion"))
        conn.execute(text("UPDATE propiedad SET tipo = 'Venta'"))
    db.init_db()
    p = db.list_propiedades()[0]
    assert p.tipo == "Casa" and p.tipo_operacion == "Venta"


# --- Permisos y mora ---

def test_operaciones_financieras_exigen_administrador_identificado():
    std = _agente("std@t.com", "10000002")
    for solicitante in (None, std.id):
        with pytest.raises(PermissionError):
            controller.generar_liquidaciones_mes("2026-08", id_agente_solicitante=solicitante)
        with pytest.raises(PermissionError):
            controller.exportar_reporte_financiero_csv("cobros", id_agente_solicitante=solicitante)


def test_alta_de_agente_desde_ui_requiere_admin():
    std = _agente("std2@t.com", "10000003")
    with pytest.raises(PermissionError):
        _alta = controller.registrar_agente(
            "N", "A", "n@t.com", "x", "20-1-9", "M", "DNI", "55", "d", "t",
            id_agente_solicitante=std.id,
        )
        assert _alta is None


def test_mora_no_admite_recargo_manual():
    admin, _, _, _, contrato = _base()
    controller.firmar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    with pytest.raises(TypeError):
        controller.registrar_pago_inquilino(
            contrato.nro_contrato, "2026-08", 100000.0, monto_recargo=0.0
        )
    pago = controller.registrar_pago_inquilino(
        contrato.nro_contrato, "2026-08", 100000.0, fecha_pago=date(2026, 8, 20),
        id_agente_solicitante=admin.id,
    )
    assert pago.dias_retraso == 10
    assert pago.monto_recargo == pytest.approx(2000.0)


# --- Contratos ---

def test_clausulas_editables_en_borrador_e_inmutables_al_firmar():
    admin, _, _, _, contrato = _base()
    controller.decidir_contrato_propietario(contrato.nro_contrato, True)
    cl = controller.listar_clausulas_contrato(contrato.nro_contrato)[0]
    controller.editar_clausula_contrato(cl.id, "Nuevo título", "Nuevo contenido")
    controller.firmar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    with pytest.raises(ValueError, match="inmutables"):
        controller.editar_clausula_contrato(cl.id, "x", "y")
    with pytest.raises(ValueError, match="inmutables"):
        controller.modificar_comisiones_contrato(contrato.nro_contrato, 5.0)


def test_honorarios_modificables_en_borrador():
    _, _, _, _, contrato = _base()
    c = controller.modificar_comisiones_contrato(contrato.nro_contrato, 8.0, 2.5)
    assert c.comision_porcentaje == 8.0 and c.comision_agente_porcentaje == 2.5


def test_finalizar_contrato_libera_el_inmueble():
    admin, _, _, prop, contrato = _base()
    controller.firmar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    assert controller.obtener_propiedad(prop.id).estado == "alquilada"
    c = controller.finalizar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    assert c.estado == "finalizado"
    assert controller.obtener_propiedad(prop.id).estado == "disponible"
    with pytest.raises(ValueError):
        controller.finalizar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)


def test_cliente_con_correo_duplicado_es_rechazado():
    controller.registrar_cliente("A", "B", "dup@t.com", "DNI", "1", "d", "t")
    with pytest.raises(ValueError, match="correo"):
        controller.registrar_cliente("C", "D", "dup@t.com", "DNI", "2", "d", "t")


# --- Web ---

def test_visitas_global_y_catalogo(client):
    admin, *_ = _base()
    _login(client, admin)
    assert client.get("/visitas").status_code == 200
    resp = client.get("/propiedades")
    assert resp.status_code == 200 and b"zona-filter" in resp.data
    assert client.get("/propiedades/nueva").status_code == 200


def test_boleta_y_presupuesto_en_pdf(client):
    admin, _, _, _, contrato = _base()
    controller.firmar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    _login(client, admin)
    resp = client.get(f"/finanzas/boleta/{contrato.nro_contrato}/2026-08/pdf")
    assert resp.status_code == 200 and resp.data.startswith(b"%PDF")
    assert client.get(f"/finanzas/boleta/{contrato.nro_contrato}/2026-08").status_code == 200
    reclamo = controller.registrar_reclamo(
        contrato.nro_contrato, "Plomería / Humedad", "Pérdida en baño", "Alta", 25000.0
    )
    resp = client.get(f"/reclamos/{reclamo.id}/presupuesto/pdf")
    assert resp.status_code == 200 and resp.data.startswith(b"%PDF")


def test_boleta_pdf_de_contrato_ajeno_da_403(client):
    admin, _, _, _, contrato = _base()
    otro = _agente("otro@t.com", "10000009")
    _login(client, otro)
    assert client.get(f"/finanzas/boleta/{contrato.nro_contrato}/2026-08/pdf").status_code == 403


def test_comprobante_con_extension_invalida_se_rechaza(client):
    admin, _, _, _, contrato = _base()
    controller.firmar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    _login(client, admin)
    resp = client.post(
        "/finanzas/pagos-inquilinos/nuevo",
        data={
            "nro_contrato": contrato.nro_contrato, "mes": "2026-08", "monto": "100000",
            "fecha_pago": "2026-08-05",
            "comprobante": (io.BytesIO(b"MZ"), "virus.exe"),
        },
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"Formato de archivo no permitido" in resp.data
    assert db.get_pago_inquilino_by_period(contrato.nro_contrato, "2026-08") is None


def test_adjuntos_requieren_sesion(client):
    assert client.get("/uploads/comprobantes/x.pdf").status_code == 302

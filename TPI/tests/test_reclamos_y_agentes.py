import os
from datetime import date, datetime
import pytest

# Force database to use an in-memory SQLite for isolated tests
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
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def setup_base_data():
    admin = controller.registrar_agente(
        "Carlos", "Admin", "carlos.admin@inmogestion.com", "pass123",
        "20-11111111-9", "MAT-101", "DNI", "11111111", "Pellegrini 100", "3415550001", "Administrador"
    )
    propietario = controller.registrar_propietario(
        "Mario", "Dueño", "mario@gmail.com", "DNI", "22222222", "Mitre 500", "3415550002"
    )
    cliente = controller.registrar_cliente(
        "Laura", "Inquilina", "laura@gmail.com", "DNI", "33333333", "Rioja 800", "3415550003"
    )
    prop = controller.registrar_propiedad(
        "Bv. Oroño 1200, Rosario", "Alquiler", "Centro", propietario.id
    )
    controller.asignar_agente_a_propiedad(admin.id, prop.id, datetime.now())
    contrato = controller.solicitar_contrato(
        cliente.id, admin.id, prop.id, monto=150000.0, tipo_contrato="Alquiler"
    )
    contrato_firmado = controller.firmar_contrato(contrato.nro_contrato)

    return admin, propietario, cliente, prop, contrato_firmado


def test_registrar_reclamo_validacion_y_presupuesto():
    """
    Verifica el registro de reclamos con presupuesto estimado asociado a un contrato activo.
    """
    admin, prop_dueno, cliente, prop, contrato = setup_base_data()

    # 1. Registrar reclamo estructural válido
    reclamo = controller.registrar_reclamo(
        nro_contrato=contrato.nro_contrato,
        tipo_dano="Plomería / Humedad",
        descripcion="Pérdida de agua bajo la bacha de la cocina que afecta el mueble bajo mesada.",
        urgencia="Alta",
        presupuesto_estimado=45000.0,
    )

    assert reclamo.id is not None
    assert reclamo.nro_contrato == contrato.nro_contrato
    assert reclamo.id_propiedad == prop.id
    assert reclamo.id_cliente == cliente.id
    assert reclamo.estado == "pendiente"
    assert reclamo.presupuesto_estimado == 45000.0
    assert reclamo.urgencia == "Alta"

    # 2. Rechazar reclamo sobre contrato inexistente
    with pytest.raises(ValueError, match="El número de contrato especificado no existe"):
        controller.registrar_reclamo(
            nro_contrato=99999,
            tipo_dano="Electricidad",
            descripcion="Corte de luz",
            presupuesto_estimado=10000.0,
        )

    # 3. Rechazar descripción vacía
    with pytest.raises(ValueError, match="La descripción del reclamo es obligatoria"):
        controller.registrar_reclamo(
            nro_contrato=contrato.nro_contrato,
            tipo_dano="Electricidad",
            descripcion="   ",
            presupuesto_estimado=10000.0,
        )


def test_actualizar_estado_reclamo_y_resolucion():
    """
    Verifica el ciclo de vida del reclamo: pendiente -> informado al dueño -> en reparación -> resuelto.
    """
    admin, prop_dueno, cliente, prop, contrato = setup_base_data()

    reclamo = controller.registrar_reclamo(
        nro_contrato=contrato.nro_contrato,
        tipo_dano="Estructural / Techos / Muros",
        descripcion="Rajadura en pared medianera con filtración de lluvia.",
        urgencia="Urgente",
        presupuesto_estimado=85000.0,
    )

    # Paso 1: Informar al propietario con presupuesto actualizado
    r_informado = controller.actualizar_estado_reclamo(
        id_reclamo=reclamo.id,
        nuevo_estado="informado_propietario",
        presupuesto_actualizado=90000.0,
        observaciones_resolucion="Presupuesto enviado al dueño por WhatsApp y email.",
    )
    assert r_informado.estado == "informado_propietario"
    assert r_informado.presupuesto_estimado == 90000.0
    assert r_informado.fecha_resolucion is None

    # Paso 2: Marcar en reparación
    r_reparacion = controller.actualizar_estado_reclamo(
        id_reclamo=reclamo.id,
        nuevo_estado="en_reparacion",
        observaciones_resolucion="Técnico asignado para comenzar obra el lunes.",
    )
    assert r_reparacion.estado == "en_reparacion"

    # Paso 3: Marcar como resuelto
    r_resuelto = controller.actualizar_estado_reclamo(
        id_reclamo=reclamo.id,
        nuevo_estado="resuelto",
        observaciones_resolucion="Obra concluida satisfactoriamente.",
    )
    assert r_resuelto.estado == "resuelto"
    assert r_resuelto.fecha_resolucion == date.today()


def test_obtener_detalle_reclamo_para_presupuesto_propietario():
    """
    Verifica la consolidación de datos para la emisión del informe de presupuesto al dueño.
    """
    admin, prop_dueno, cliente, prop, contrato = setup_base_data()

    reclamo = controller.registrar_reclamo(
        nro_contrato=contrato.nro_contrato,
        tipo_dano="Gas / Calefacción",
        descripcion="Pérdida en la llave de paso de gas de la cocina.",
        urgencia="Urgente",
        presupuesto_estimado=60000.0,
    )

    detalle = controller.obtener_detalle_reclamo(reclamo.id)
    assert detalle["reclamo"].id == reclamo.id
    assert detalle["contrato"].nro_contrato == contrato.nro_contrato
    assert detalle["propiedad"].direccion == "Bv. Oroño 1200, Rosario"
    assert detalle["cliente"].nombre == "Laura"
    assert detalle["propietario"].nombre == "Mario"


def test_crear_agente_admin_y_roles():
    """
    Verifica el registro de agentes por el administrador y sus atributos.
    """
    agente_nuevo = controller.registrar_agente(
        nombre="Valeria",
        apellido="Torres",
        email="valeria.torres@inmogestion.com",
        password="securepass123",
        cuil="27-35667788-4",
        matricula="MAT-9050",
        tipo_doc="DNI",
        nro_doc="35667788",
        domicilio="Corrientes 1000",
        telefono="3415559988",
        rol="Administrador",
    )

    assert agente_nuevo.id is not None
    assert agente_nuevo.rol == "Administrador"
    assert controller.es_administrador(agente_nuevo.id) is True

    # Verificar autenticación
    auth = controller.autenticar_agente("valeria.torres@inmogestion.com", "securepass123")
    assert auth is not None
    assert auth.id == agente_nuevo.id


def test_web_routes_reclamos_y_agentes(client):
    """
    Verifica que las rutas HTTP web de reclamos y agentes respondan 200 OK con sesión activa.
    """
    admin, prop_dueno, cliente, prop, contrato = setup_base_data()

    # Iniciar sesión de admin
    with client.session_transaction() as sess:
        sess["agente_id"] = admin.id
        sess["agente_name"] = admin.nombre_completo
        sess["agente_rol"] = "Administrador"

    # 1. GET /reclamos
    resp = client.get("/reclamos")
    assert resp.status_code == 200
    assert b"Reclamos" in resp.data

    # 2. GET /reclamos/nuevo
    resp = client.get(f"/reclamos/nuevo?nro_contrato={contrato.nro_contrato}")
    assert resp.status_code == 200
    assert b"Registrar Reclamo" in resp.data

    # 3. POST /reclamos/nuevo
    resp = client.post("/reclamos/nuevo", data={
        "nro_contrato": contrato.nro_contrato,
        "tipo_dano": "Plomería / Humedad",
        "descripcion": "Goteo persistente en cañería de baño",
        "urgencia": "Media",
        "presupuesto_estimado": "35000",
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 4. GET /agentes (Admin only)
    resp = client.get("/agentes")
    assert resp.status_code == 200
    assert b"Comerciales" in resp.data

    # 5. GET /agentes/nuevo (Admin only)
    resp = client.get("/agentes/nuevo")
    assert resp.status_code == 200
    assert b"Cargar Nuevo Agente" in resp.data

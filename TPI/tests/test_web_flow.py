from datetime import datetime
import os
import pytest

# Force database to use an in-memory SQLite for isolated tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app  # noqa: E402
import datos.db as db  # noqa: E402
import business.controller as controller  # noqa: E402


@pytest.fixture
def client():
    """
    Flask test client fixture.
    """
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    db.init_db()

    # Create seed data for web test
    # 1. Agent
    controller.registrar_agente(
        nombre="Agente",
        apellido="Web",
        email="agente.web@test.com",
        password="webpassword",
        cuil="20-99888777-9",
        matricula="MAT-777",
        tipo_doc="DNI",
        nro_doc="99888777",
        domicilio="Pellegrini 250",
        telefono="341555888",
    )
    # 2. Owner
    owner = controller.registrar_propietario(
        nombre="Propietario",
        apellido="Web",
        email="owner.web@test.com",
        tipo_doc="DNI",
        nro_doc="88777666",
        domicilio="Corrientes 500",
        telefono="341555777",
    )
    # 3. Client
    controller.registrar_cliente(
        nombre="Cliente",
        apellido="Web",
        email="client.web@test.com",
        tipo_doc="DNI",
        nro_doc="77666555",
        domicilio="Mitre 900",
        telefono="341555666",
    )
    # 4. Property and assign agent
    prop = controller.registrar_propiedad(
        direccion="San Martin 100",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=owner.id,
    )
    agent = controller.autenticar_agente("agente.web@test.com", "webpassword")
    controller.asignar_agente_a_propiedad(agent.id, prop.id, datetime.now())

    with app.test_client() as client:
        yield client

    db.Base.metadata.drop_all(bind=db.engine)


def test_login_flow(client):
    """
    Tests web login logic and redirection.
    """
    # Try accessing dashboard without login (should redirect to login)
    response = client.get("/", follow_redirects=True)
    html = response.data.decode("utf-8")
    assert "Debes iniciar sesión" in html or "Iniciar Sesión" in html

    # Log in with valid credentials
    response = client.post(
        "/login",
        data={"email": "agente.web@test.com", "password": "webpassword"},
        follow_redirects=True,
    )
    html = response.data.decode("utf-8")
    assert "Bienvenido" in html
    assert "Dashboard General" in html

    # Access dashboard
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert "Dashboard General" in html


def test_contract_request_and_sign_flow(client):
    """
    Tests request creation, contract signing and property state transition in presentation layer.
    """
    # Log in
    client.post(
        "/login",
        data={"email": "agente.web@test.com", "password": "webpassword"},
        follow_redirects=True,
    )

    # Get IDs from database
    agente = controller.autenticar_agente("agente.web@test.com", "webpassword")
    clientes = controller.listar_clientes()
    propiedades = controller.listar_propiedades()

    c_id = clientes[0].id
    p_id = propiedades[0].id
    a_id = agente.id

    response = client.post(
        "/contratos/nuevo",
        data={"id_cliente": c_id, "prop_agente": f"{p_id}:{a_id}"},
        follow_redirects=True,
    )

    html = response.data.decode("utf-8")
    assert "Solicitud de contrato creada exitosamente" in html

    # Check that contract was created and is in 'solicitado' state
    contratos = controller.listar_contratos()
    assert len(contratos) == 1
    contrato = contratos[0]
    assert contrato.estado == "solicitado"

    # Sign contract
    response = client.post(
        f"/contratos/{contrato.nro_contrato}/firmar", follow_redirects=True
    )
    html = response.data.decode("utf-8")
    assert "firmado y activado exitosamente" in html

    # Verify contract state and property state
    updated_contrato = controller.obtener_contrato(contrato.nro_contrato)
    assert updated_contrato.estado == "activo"

    updated_prop = controller.obtener_propiedad(p_id)
    assert updated_prop.estado == "alquilada"


def test_custom_error_pages(client):
    """
    Tests that 404 handler returns our custom styled template.
    """
    # access invalid url
    response = client.get("/invalid-page-does-not-exist")
    assert response.status_code == 404
    html = response.data.decode("utf-8")
    assert "Página No Encontrada" in html
    assert "404" in html

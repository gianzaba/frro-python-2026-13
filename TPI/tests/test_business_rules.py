import os
import pytest
from datetime import datetime

# Force database to use an in-memory SQLite for isolated tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import datos.db as db  # noqa: E402
import business.controller as controller  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Initializes a fresh database for each test.
    """
    db.init_db(reset=True)
    yield
    db.Base.metadata.drop_all(bind=db.engine)


def test_agent_registration_and_authentication():
    """
    Tests registering an agent and verifying password cryptography.
    """
    # Register agent
    agent = controller.registrar_agente(
        nombre="Test",
        apellido="Agent",
        email="testagent@test.com",
        password="securepassword123",
        cuil="20-11111111-9",
        matricula="MAT-9999",
        tipo_doc="DNI",
        nro_doc="11111111",
        domicilio="Calle Falsa 123",
        telefono="341666777",
    )

    assert agent.id is not None
    assert agent.email == "testagent@test.com"
    # Verify password was hashed and is not saved in cleartext
    assert agent.contrasegna_hash != "securepassword123"

    # Test valid authentication
    auth_agent = controller.autenticar_agente(
        "testagent@test.com", "securepassword123"
    )
    assert auth_agent is not None
    assert auth_agent.id == agent.id

    # Test invalid authentication
    assert (
        controller.autenticar_agente("testagent@test.com", "wrongpassword")
        is None
    )
    assert (
        controller.autenticar_agente(
            "nonexistent@test.com", "securepassword123"
        )
        is None
    )


def test_business_rule_1_signing_property_not_available():
    """
    Rule 1: A contract can only be signed if the property is available.
    """
    # Create Agent, Owner, Client
    agent = controller.registrar_agente(
        "Agent",
        "One",
        "a1@test.com",
        "pwd",
        "20-1",
        "M-1",
        "DNI",
        "1",
        "Dom",
        "1",
    )
    owner = controller.registrar_propietario(
        "Owner", "One", "o1@test.com", "DNI", "2", "Dom", "2"
    )
    client = controller.registrar_cliente(
        "Client", "One", "c1@test.com", "DNI", "3", "Dom", "3"
    )

    # Create Property and assign agent
    prop = controller.registrar_propiedad(
        "Calle 1", "Alquiler", "Norte", owner.id
    )
    controller.asignar_agente_a_propiedad(agent.id, prop.id, datetime.now())

    # Solicit contract (should succeed because property is available)
    contract = controller.solicitar_contrato(client.id, agent.id, prop.id)
    assert contract.estado == "solicitado"

    # Manually change property state to 'alquilada' to simulate unavailable
    prop.estado = "alquilada"
    db.save_propiedad(prop)

    # Try signing contract (Rule 1 violation)
    with pytest.raises(ValueError, match="La propiedad no está disponible"):
        controller.firmar_contrato(contract.nro_contrato)

    # Reset property to available and sign (should succeed)
    prop.estado = "disponible"
    db.save_propiedad(prop)
    signed_contract = controller.firmar_contrato(contract.nro_contrato)

    assert signed_contract.estado == "activo"

    # Verify property state was updated to 'alquilada' after successful signing
    updated_prop = controller.obtener_propiedad(prop.id)
    assert updated_prop.estado == "alquilada"


def test_business_rule_2_agent_multiple_property_assignments():
    """
    Rule 2: An agent CAN be assigned to multiple properties simultaneously.
    """
    agent = controller.registrar_agente(
        "Agent",
        "One",
        "a1@test.com",
        "pwd",
        "20-1",
        "M-1",
        "DNI",
        "1",
        "Dom",
        "1",
    )
    owner = controller.registrar_propietario(
        "Owner", "One", "o1@test.com", "DNI", "2", "Dom", "2"
    )

    prop1 = controller.registrar_propiedad(
        "Calle 1", "Alquiler", "Norte", owner.id
    )
    prop2 = controller.registrar_propiedad("Calle 2", "Venta", "Sur", owner.id)

    now = datetime.now()

    # Assign agent to prop1
    assoc1 = controller.asignar_agente_a_propiedad(
        agent.id, prop1.id, desde=now
    )
    assert assoc1.id_agente == agent.id
    assert assoc1.id_propiedad == prop1.id

    # Assign same agent to prop2 concurrently (should succeed!)
    assoc2 = controller.asignar_agente_a_propiedad(
        agent.id, prop2.id, desde=now
    )
    assert assoc2.id_agente == agent.id
    assert assoc2.id_propiedad == prop2.id

    # Verify both assignments exist and are active
    active1 = controller.obtener_asignacion_activa_propiedad(prop1.id)
    active2 = controller.obtener_asignacion_activa_propiedad(prop2.id)

    assert active1 is not None and active1.id_agente == agent.id
    assert active2 is not None and active2.id_agente == agent.id


def test_business_rule_3_agent_performing_contract_must_be_assigned():
    """
    Rule 3: The agent executing the contract must be assigned to the property.
    """
    agent1 = controller.registrar_agente(
        "Agent",
        "One",
        "a1@test.com",
        "pwd",
        "20-1",
        "M-1",
        "DNI",
        "1",
        "Dom",
        "1",
    )
    agent2 = controller.registrar_agente(
        "Agent",
        "Two",
        "a2@test.com",
        "pwd",
        "20-2",
        "M-2",
        "DNI",
        "2",
        "Dom",
        "2",
    )
    owner = controller.registrar_propietario(
        "Owner", "One", "o1@test.com", "DNI", "3", "Dom", "3"
    )
    client = controller.registrar_cliente(
        "Client", "One", "c1@test.com", "DNI", "4", "Dom", "4"
    )

    prop = controller.registrar_propiedad(
        "Calle 1", "Alquiler", "Norte", owner.id
    )

    # Assign agent1 to property
    controller.asignar_agente_a_propiedad(agent1.id, prop.id, datetime.now())

    # Client requests contract with agent2 (should fail because agent2 is not assigned)
    with pytest.raises(ValueError, match="no está asignado actualmente"):
        controller.solicitar_contrato(client.id, agent2.id, prop.id)

    # Client requests contract with agent1 (should succeed)
    contract = controller.solicitar_contrato(client.id, agent1.id, prop.id)
    assert contract is not None
    assert contract.id_agente == agent1.id

"""
Test para validar que cada agente solo vea y agregue sus propios clientes y propietarios.
Solo los administradores pueden ver TODO.
"""
import os
import pytest

# Force database to use an in-memory SQLite for isolated tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import datos.db as db  # noqa: E402
from business.controller import (
    registrar_agente,
    registrar_cliente,
    registrar_propietario,
    listar_clientes,
    listar_propietarios,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Initializes a fresh database for each test.
    """
    db.init_db(reset=True)
    yield
    db.Base.metadata.drop_all(bind=db.engine)


def test_agente_estandar_solo_ve_sus_clientes():
    """Un agente estándar solo ve los clientes que él registró."""
    # Crear dos agentes estándar
    agente1 = registrar_agente(
        nombre="Juan", apellido="García",
        email="juan.garcia@test.com", password="pass123",
        cuil="20-11223344-9", matricula="MAT-001",
        tipo_doc="DNI", nro_doc="11223344",
        domicilio="Calle 1", telefono="1234567890",
        rol="Estándar"
    )
    agente2 = registrar_agente(
        nombre="María", apellido="López",
        email="maria.lopez@test.com", password="pass123",
        cuil="27-22334455-4", matricula="MAT-002",
        tipo_doc="DNI", nro_doc="22334455",
        domicilio="Calle 2", telefono="0987654321",
        rol="Estándar"
    )

    # Agente1 registra 2 clientes
    cliente1_agente1 = registrar_cliente(
        nombre="Carlos", apellido="Pérez",
        email="carlos@test.com", tipo_doc="DNI", nro_doc="33445566",
        domicilio="Calle A", telefono="1111111111",
        id_agente_creador=agente1.id
    )
    cliente2_agente1 = registrar_cliente(
        nombre="Ana", apellido="Martínez",
        email="ana@test.com", tipo_doc="DNI", nro_doc="44556677",
        domicilio="Calle B", telefono="2222222222",
        id_agente_creador=agente1.id
    )

    # Agente2 registra 1 cliente
    cliente1_agente2 = registrar_cliente(
        nombre="Pedro", apellido="Rodríguez",
        email="pedro@test.com", tipo_doc="DNI", nro_doc="55667788",
        domicilio="Calle C", telefono="3333333333",
        id_agente_creador=agente2.id
    )

    # Agente1 solo ve sus 2 clientes
    clientes_agente1 = listar_clientes(id_agente=agente1.id)
    assert len(clientes_agente1) == 2
    cliente_ids_agente1 = [c.id for c in clientes_agente1]
    assert cliente1_agente1.id in cliente_ids_agente1
    assert cliente2_agente1.id in cliente_ids_agente1

    # Agente2 solo ve su 1 cliente
    clientes_agente2 = listar_clientes(id_agente=agente2.id)
    assert len(clientes_agente2) == 1
    assert clientes_agente2[0].id == cliente1_agente2.id


def test_agente_estandar_solo_ve_sus_propietarios():
    """Un agente estándar solo ve los propietarios que él registró."""
    # Crear dos agentes estándar
    agente1 = registrar_agente(
        nombre="Juan", apellido="García",
        email="juan.garcia@test.com", password="pass123",
        cuil="20-11223344-9", matricula="MAT-001",
        tipo_doc="DNI", nro_doc="11223344",
        domicilio="Calle 1", telefono="1234567890",
        rol="Estándar"
    )
    agente2 = registrar_agente(
        nombre="María", apellido="López",
        email="maria.lopez@test.com", password="pass123",
        cuil="27-22334455-4", matricula="MAT-002",
        tipo_doc="DNI", nro_doc="22334455",
        domicilio="Calle 2", telefono="0987654321",
        rol="Estándar"
    )

    # Agente1 registra 2 propietarios
    prop1_agente1 = registrar_propietario(
        nombre="Roberto", apellido="Álvarez",
        email="roberto@test.com", tipo_doc="DNI", nro_doc="66778899",
        domicilio="Calle X", telefono="4444444444",
        id_agente_creador=agente1.id
    )
    prop2_agente1 = registrar_propietario(
        nombre="Silvia", apellido="Fernández",
        email="silvia@test.com", tipo_doc="DNI", nro_doc="77889900",
        domicilio="Calle Y", telefono="5555555555",
        id_agente_creador=agente1.id
    )

    # Agente2 registra 1 propietario
    prop1_agente2 = registrar_propietario(
        nombre="Jorge", apellido="Mendoza",
        email="jorge@test.com", tipo_doc="DNI", nro_doc="88990011",
        domicilio="Calle Z", telefono="6666666666",
        id_agente_creador=agente2.id
    )

    # Agente1 solo ve sus 2 propietarios
    propietarios_agente1 = listar_propietarios(id_agente=agente1.id)
    assert len(propietarios_agente1) == 2
    prop_ids_agente1 = [p.id for p in propietarios_agente1]
    assert prop1_agente1.id in prop_ids_agente1
    assert prop2_agente1.id in prop_ids_agente1

    # Agente2 solo ve su 1 propietario
    propietarios_agente2 = listar_propietarios(id_agente=agente2.id)
    assert len(propietarios_agente2) == 1
    assert propietarios_agente2[0].id == prop1_agente2.id


def test_administrador_ve_todos_clientes_y_propietarios():
    """Un administrador ve todos los clientes y propietarios."""
    # Crear un agente administrador y dos agentes estándar
    admin = registrar_agente(
        nombre="Admin", apellido="Sistema",
        email="admin@test.com", password="admin123",
        cuil="20-99999999-9", matricula="MAT-ADMIN",
        tipo_doc="DNI", nro_doc="99999999",
        domicilio="Calle Admin", telefono="0000000000",
        rol="Administrador"
    )
    agente1 = registrar_agente(
        nombre="Juan", apellido="García",
        email="juan.garcia@test.com", password="pass123",
        cuil="20-11223344-9", matricula="MAT-001",
        tipo_doc="DNI", nro_doc="11223344",
        domicilio="Calle 1", telefono="1234567890",
        rol="Estándar"
    )
    agente2 = registrar_agente(
        nombre="María", apellido="López",
        email="maria.lopez@test.com", password="pass123",
        cuil="27-22334455-4", matricula="MAT-002",
        tipo_doc="DNI", nro_doc="22334455",
        domicilio="Calle 2", telefono="0987654321",
        rol="Estándar"
    )

    # Crear clientes y propietarios para cada agente estándar
    # Clientes
    cliente1_ag1 = registrar_cliente(
        nombre="Carlos", apellido="Pérez",
        email="carlos@test.com", tipo_doc="DNI", nro_doc="33445566",
        domicilio="Calle A", telefono="1111111111",
        id_agente_creador=agente1.id
    )
    cliente1_ag2 = registrar_cliente(
        nombre="Pedro", apellido="Rodríguez",
        email="pedro@test.com", tipo_doc="DNI", nro_doc="55667788",
        domicilio="Calle C", telefono="3333333333",
        id_agente_creador=agente2.id
    )

    # Propietarios
    prop1_ag1 = registrar_propietario(
        nombre="Roberto", apellido="Álvarez",
        email="roberto@test.com", tipo_doc="DNI", nro_doc="66778899",
        domicilio="Calle X", telefono="4444444444",
        id_agente_creador=agente1.id
    )
    prop1_ag2 = registrar_propietario(
        nombre="Jorge", apellido="Mendoza",
        email="jorge@test.com", tipo_doc="DNI", nro_doc="88990011",
        domicilio="Calle Z", telefono="6666666666",
        id_agente_creador=agente2.id
    )

    # Admin ve todos los clientes (2)
    clientes_admin = listar_clientes(id_agente=admin.id)
    assert len(clientes_admin) == 2
    cliente_ids = [c.id for c in clientes_admin]
    assert cliente1_ag1.id in cliente_ids
    assert cliente1_ag2.id in cliente_ids

    # Admin ve todos los propietarios (2)
    propietarios_admin = listar_propietarios(id_agente=admin.id)
    assert len(propietarios_admin) == 2
    prop_ids = [p.id for p in propietarios_admin]
    assert prop1_ag1.id in prop_ids
    assert prop1_ag2.id in prop_ids


def test_cliente_sin_agente_asignado():
    """Un cliente registrado sin especificar agente creador debe ser visible para todos los admins."""
    # Crear un admin y un agente estándar
    admin = registrar_agente(
        nombre="Admin", apellido="Sistema",
        email="admin@test.com", password="admin123",
        cuil="20-99999999-9", matricula="MAT-ADMIN",
        tipo_doc="DNI", nro_doc="99999999",
        domicilio="Calle Admin", telefono="0000000000",
        rol="Administrador"
    )
    agente1 = registrar_agente(
        nombre="Juan", apellido="García",
        email="juan.garcia@test.com", password="pass123",
        cuil="20-11223344-9", matricula="MAT-001",
        tipo_doc="DNI", nro_doc="11223344",
        domicilio="Calle 1", telefono="1234567890",
        rol="Estándar"
    )

    # Crear un cliente sin asignar a ningún agente (id_agente_creador=None)
    cliente_sin_agente = registrar_cliente(
        nombre="Carlos", apellido="Pérez",
        email="carlos@test.com", tipo_doc="DNI", nro_doc="33445566",
        domicilio="Calle A", telefono="1111111111",
        id_agente_creador=None
    )

    # Admin ve el cliente
    clientes_admin = listar_clientes(id_agente=admin.id)
    cliente_ids = [c.id for c in clientes_admin]
    assert cliente_sin_agente.id in cliente_ids

    # Agente1 NO ve el cliente (porque no es su id_agente_creador)
    clientes_agente1 = listar_clientes(id_agente=agente1.id)
    cliente_ids_ag1 = [c.id for c in clientes_agente1]
    assert cliente_sin_agente.id not in cliente_ids_ag1


def test_listar_sin_especificar_agente():
    """Cuando no se especifica id_agente, se listan todos (comportamiento backward compatible)."""
    # Crear dos agentes y registrar clientes
    agente1 = registrar_agente(
        nombre="Juan", apellido="García",
        email="juan.garcia@test.com", password="pass123",
        cuil="20-11223344-9", matricula="MAT-001",
        tipo_doc="DNI", nro_doc="11223344",
        domicilio="Calle 1", telefono="1234567890",
        rol="Estándar"
    )
    agente2 = registrar_agente(
        nombre="María", apellido="López",
        email="maria.lopez@test.com", password="pass123",
        cuil="27-22334455-4", matricula="MAT-002",
        tipo_doc="DNI", nro_doc="22334455",
        domicilio="Calle 2", telefono="0987654321",
        rol="Estándar"
    )

    # Crear clientes para cada agente
    registrar_cliente(
        nombre="Carlos", apellido="Pérez",
        email="carlos@test.com", tipo_doc="DNI", nro_doc="33445566",
        domicilio="Calle A", telefono="1111111111",
        id_agente_creador=agente1.id
    )
    registrar_cliente(
        nombre="Pedro", apellido="Rodríguez",
        email="pedro@test.com", tipo_doc="DNI", nro_doc="55667788",
        domicilio="Calle C", telefono="3333333333",
        id_agente_creador=agente2.id
    )

    # Sin especificar id_agente, se listan todos
    todos_clientes = listar_clientes(id_agente=None)
    assert len(todos_clientes) == 2

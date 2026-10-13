import os
import sys
import pytest
from datetime import datetime

# Ensure parent directory is in sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import datos.db as db  # noqa: E402
import business.controller as controller  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db():
    db.init_db(reset=True)
    yield
    db.Base.metadata.drop_all(bind=db.engine)


def test_cartera_propia_agente_clientes_y_propietarios():
    """
    Test que verifica que cada agente pueda ver y gestionar su propia cartera
    de clientes y propietarios, mientras que el Administrador puede listar todos.
    """
    # 1. Crear dos agentes comerciales
    agente1 = controller.registrar_agente(
        nombre="Agente",
        apellido="Uno",
        email="agente1@test.com",
        password="pass",
        cuil="20-11111111-1",
        matricula="MAT-001",
        tipo_doc="DNI",
        nro_doc="10000001",
        domicilio="Dom 1",
        telefono="111",
    )
    agente2 = controller.registrar_agente(
        nombre="Agente",
        apellido="Dos",
        email="agente2@test.com",
        password="pass",
        cuil="20-22222222-2",
        matricula="MAT-002",
        tipo_doc="DNI",
        nro_doc="20000002",
        domicilio="Dom 2",
        telefono="222",
    )

    # 2. Registrar clientes asignados a cada agente
    c1 = controller.registrar_cliente(
        "Cliente", "Uno", "c1@test.com", "DNI", "30000001", "Dir 1", "333", id_agente=agente1.id
    )
    c2 = controller.registrar_cliente(
        "Cliente", "Dos", "c2@test.com", "DNI", "30000002", "Dir 2", "444", id_agente=agente2.id
    )

    # 3. Registrar propietarios asignados a cada agente
    p1 = controller.registrar_propietario(
        "Prop", "Uno", "p1@test.com", "DNI", "40000001", "Dir 1", "555", id_agente=agente1.id
    )
    p2 = controller.registrar_propietario(
        "Prop", "Dos", "p2@test.com", "DNI", "40000002", "Dir 2", "666", id_agente=agente2.id
    )

    # 4. Verificar filtrado de clientes por agente
    clientes_agente1 = controller.listar_clientes(id_agente=agente1.id)
    assert len(clientes_agente1) == 1
    assert clientes_agente1[0].id == c1.id
    assert clientes_agente1[0].id_agente == agente1.id

    clientes_agente2 = controller.listar_clientes(id_agente=agente2.id)
    assert len(clientes_agente2) == 1
    assert clientes_agente2[0].id == c2.id
    assert clientes_agente2[0].id_agente == agente2.id

    # Vista global (administrador)
    todos_clientes = controller.listar_clientes(id_agente=None)
    assert len(todos_clientes) == 2

    # 5. Verificar filtrado de propietarios por agente
    props_agente1 = controller.listar_propietarios(id_agente=agente1.id)
    assert len(props_agente1) == 1
    assert props_agente1[0].id == p1.id
    assert props_agente1[0].id_agente == agente1.id

    props_agente2 = controller.listar_propietarios(id_agente=agente2.id)
    assert len(props_agente2) == 1
    assert props_agente2[0].id == p2.id
    assert props_agente2[0].id_agente == agente2.id

    # Vista global (administrador)
    todos_props = controller.listar_propietarios(id_agente=None)
    assert len(todos_props) == 2


def test_cancelacion_automatica_solicitudes_al_firmar_contrato():
    """
    Test que verifica que cuando existen múltiples solicitudes en estado 'solicitado'
    para una misma propiedad, al firmarse una en concreto, todas las otras solicitudes
    para esa misma propiedad pasan automáticamente al estado 'cancelado'.
    """
    # 1. Setup agente, propietario y propiedad
    agente = controller.registrar_agente(
        nombre="Carlos",
        apellido="Martillero",
        email="carlos@test.com",
        password="pass",
        cuil="20-33333333-3",
        matricula="MAT-777",
        tipo_doc="DNI",
        nro_doc="33333333",
        domicilio="Oficina",
        telefono="777",
        rol="Administrador",
    )
    propietario = controller.registrar_propietario(
        "Dueño", "Inmueble", "duenio@test.com", "DNI", "55555555", "Casa 1", "555"
    )
    propiedad = controller.registrar_propiedad(
        "Mitre 500, Rosario", "Alquiler", "Centro", propietario.id
    )
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime.now())

    # 2. Registrar 3 clientes interesados
    cliente1 = controller.registrar_cliente("Interesado", "Uno", "i1@test.com", "DNI", "90000001", "D1", "1")
    cliente2 = controller.registrar_cliente("Interesado", "Dos", "i2@test.com", "DNI", "90000002", "D2", "2")
    cliente3 = controller.registrar_cliente("Interesado", "Tres", "i3@test.com", "DNI", "90000003", "D3", "3")

    # 3. Crear 3 solicitudes de contrato sobre la misma propiedad
    solicitud1 = controller.solicitar_contrato(cliente1.id, agente.id, propiedad.id, monto=150000.0, comision_porcentaje=10.0)
    solicitud2 = controller.solicitar_contrato(cliente2.id, agente.id, propiedad.id, monto=150000.0, comision_porcentaje=10.0)
    solicitud3 = controller.solicitar_contrato(cliente3.id, agente.id, propiedad.id, monto=150000.0, comision_porcentaje=10.0)

    assert solicitud1.estado == "solicitado"
    assert solicitud2.estado == "solicitado"
    assert solicitud3.estado == "solicitado"

    # 4. Firmar la solicitud 2
    contrato_firmado = controller.firmar_contrato(solicitud2.nro_contrato, id_agente_solicitante=agente.id)
    assert contrato_firmado.estado == "activo"

    # 5. Verificar que la propiedad ahora esté alquilada
    prop_actualizada = controller.obtener_propiedad(propiedad.id)
    assert prop_actualizada is not None
    assert prop_actualizada.estado == "alquilada"

    # 6. Verificar que solicitud1 y solicitud3 hayan cambiado automáticamente a 'cancelado'
    s1_check = controller.obtener_contrato(solicitud1.nro_contrato)
    s2_check = controller.obtener_contrato(solicitud2.nro_contrato)
    s3_check = controller.obtener_contrato(solicitud3.nro_contrato)

    assert s1_check is not None and s1_check.estado == "cancelado"
    assert s2_check is not None and s2_check.estado == "activo"
    assert s3_check is not None and s3_check.estado == "cancelado"

    # 7. Verificar que los logs de auditoría contengan el registro de cancelación automática
    logs = controller.listar_logs_auditoria(agente.id)
    descripciones = [l.descripcion for l in logs]
    assert any("cancelada automáticamente" in d and f"#{solicitud1.nro_contrato}" in d for d in descripciones)
    assert any("cancelada automáticamente" in d and f"#{solicitud3.nro_contrato}" in d for d in descripciones)


def test_traspasar_titularidad_a_comprador_al_vender():
    """
    Test que verifica el ciclo completo de venta y traspaso de titularidad:
    1. Propiedad a la venta con dueño original.
    2. Contrato de Compraventa celebrado con cliente comprador.
    3. Firma del contrato -> propiedad vendida.
    4. Traspaso de titularidad al comprador -> se crea o asocia como nuevo Propietario,
       se reactiva la propiedad en estado 'disponible' (ej. para Alquiler),
       el contrato de venta pasa a 'finalizado' y se audita la operación.
    """
    agente = controller.registrar_agente(
        nombre="Laura",
        apellido="Broker",
        email="laura.broker@test.com",
        password="pass",
        cuil="27-44444444-4",
        matricula="MAT-888",
        tipo_doc="DNI",
        nro_doc="44444444",
        domicilio="Central",
        telefono="888",
        rol="Administrador",
    )
    vendedor_original = controller.registrar_propietario(
        "Vendedor", "Original", "vendedor@test.com", "DNI", "60000001", "Calle Vieja 123", "999"
    )
    propiedad = controller.registrar_propiedad(
        "Av. Pellegrini 2000, Rosario", "Venta", "Centro", vendedor_original.id
    )
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime.now())

    # Comprador
    comprador_cliente = controller.registrar_cliente(
        "Nicolás", "Comprador", "nicolas.compra@test.com", "DNI", "70000001", "Calle Nueva 456", "341111222", id_agente=agente.id
    )

    # Crear contrato de compraventa
    contrato_venta = controller.solicitar_contrato(
        id_cliente=comprador_cliente.id,
        id_agente=agente.id,
        id_propiedad=propiedad.id,
        monto=120000.0,
        comision_porcentaje=3.0,
        tipo_contrato="Compraventa",
    )

    # Firmar la compraventa
    contrato_firmado = controller.firmar_contrato(contrato_venta.nro_contrato, id_agente_solicitante=agente.id)
    assert contrato_firmado.estado == "activo"

    prop_vendida = controller.obtener_propiedad(propiedad.id)
    assert prop_vendida is not None
    assert prop_vendida.estado == "vendida"
    assert prop_vendida.id_propietario == vendedor_original.id

    # Ejecutar Traspaso de Titularidad al Comprador para ponerla en Alquiler
    prop_traspasada = controller.traspasar_titularidad_a_comprador(
        id_propiedad=propiedad.id,
        nuevo_tipo_operacion="Alquiler",
        id_agente_solicitante=agente.id,
    )

    # Validaciones:
    assert prop_traspasada.estado == "disponible"
    assert prop_traspasada.tipo == "Alquiler"
    assert prop_traspasada.id_propietario != vendedor_original.id

    # El comprador ahora figura como Propietario en la capa de datos y negocio
    nuevo_propietario = controller.obtener_propietario(prop_traspasada.id_propietario)
    assert nuevo_propietario is not None
    assert nuevo_propietario.nro_doc == comprador_cliente.nro_doc
    assert nuevo_propietario.nombre == comprador_cliente.nombre
    assert nuevo_propietario.apellido == comprador_cliente.apellido

    # El contrato original de compraventa ahora está finalizado
    contrato_venta_actualizado = controller.obtener_contrato(contrato_venta.nro_contrato)
    assert contrato_venta_actualizado is not None
    assert contrato_venta_actualizado.estado == "finalizado"

    # Se registró el log de auditoría del traspaso
    logs = controller.listar_logs_auditoria(agente.id)
    descripciones = [l.descripcion for l in logs]
    assert any("traspasó la titularidad" in d and nuevo_propietario.nombre_completo in d for d in descripciones)

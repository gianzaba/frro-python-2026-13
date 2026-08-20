import os
import pytest
from datetime import datetime

# Force database to use an in-memory SQLite for isolated tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import datos.db as db  # noqa: E402
import business.controller as controller  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db():
    db.init_db(reset=True)
    yield
    db.Base.metadata.drop_all(bind=db.engine)


def test_clausulas_predeterminadas_alquiler_y_compraventa():
    """
    Verifica que se generen automáticamente las cláusulas modelo según el tipo de contrato.
    """
    # Setup test entities
    agente = controller.registrar_agente(
        nombre="Mario",
        apellido="Agente",
        email="mario@inmogestion.com",
        password="password123",
        cuil="20-30000000-9",
        matricula="MAT-100",
        tipo_doc="DNI",
        nro_doc="30000000",
        domicilio="Av. Siempre Viva 123",
        telefono="3415000000",
    )
    propietario = controller.registrar_propietario(
        nombre="Roberto",
        apellido="Duenyo",
        email="roberto@gmail.com",
        tipo_doc="DNI",
        nro_doc="12000000",
        domicilio="San Martin 450",
        telefono="3414000000",
    )
    cliente = controller.registrar_cliente(
        nombre="Lucia",
        apellido="Inquilina",
        email="lucia@gmail.com",
        tipo_doc="DNI",
        nro_doc="35000000",
        domicilio="Cordoba 1000",
        telefono="3413000000",
    )

    prop_alquiler = controller.registrar_propiedad(
        direccion="Laprida 800, Rosario",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=propietario.id,
    )
    controller.asignar_agente_a_propiedad(
        id_agente=agente.id, id_propiedad=prop_alquiler.id, desde=datetime.now()
    )

    # 1. Solicitar contrato de Alquiler
    contrato_alq = controller.solicitar_contrato(
        id_cliente=cliente.id,
        id_agente=agente.id,
        id_propiedad=prop_alquiler.id,
        monto=150000.0,
        comision_porcentaje=10.0,
        tipo_contrato="Alquiler",
    )

    clausulas_alq = controller.listar_clausulas_contrato(contrato_alq.nro_contrato)
    assert len(clausulas_alq) >= 5
    assert "LOCADOR" in clausulas_alq[0].contenido

    # 2. Solicitar contrato de Compraventa
    agente_venta = controller.registrar_agente(
        nombre="Carlos",
        apellido="Vendedor",
        email="carlos@inmogestion.com",
        password="password123",
        cuil="20-31000000-9",
        matricula="MAT-101",
        tipo_doc="DNI",
        nro_doc="31000000",
        domicilio="Av. Pellegrini 500",
        telefono="3415111111",
    )
    prop_venta = controller.registrar_propiedad(
        direccion="Pellegrini 1200, Rosario",
        tipo="Venta",
        zona="Centro",
        id_propietario=propietario.id,
    )
    controller.asignar_agente_a_propiedad(
        id_agente=agente_venta.id, id_propiedad=prop_venta.id, desde=datetime.now()
    )

    contrato_ven = controller.solicitar_contrato(
        id_cliente=cliente.id,
        id_agente=agente_venta.id,
        id_propiedad=prop_venta.id,
        monto=50000000.0,
        comision_porcentaje=3.0,
        tipo_contrato="Compraventa",
    )


    clausulas_ven = controller.listar_clausulas_contrato(contrato_ven.nro_contrato)
    assert len(clausulas_ven) >= 5
    assert "VENDEDOR" in clausulas_ven[0].contenido


def test_crud_clausulas_y_modificacion_comision_agente():
    """
    Prueba añadir, modificar y eliminar cláusulas y actualizar el % de comisión del agente.
    """
    agente = controller.registrar_agente(
        nombre="Agente",
        apellido="Prueba",
        email="agente@test.com",
        password="pass",
        cuil="20-40000000-9",
        matricula="MAT-200",
        tipo_doc="DNI",
        nro_doc="40000000",
        domicilio="Mitre 123",
        telefono="3412000000",
    )
    propietario = controller.registrar_propietario(
        nombre="Juan",
        apellido="Perez",
        email="juan@test.com",
        tipo_doc="DNI",
        nro_doc="15000000",
        domicilio="Rioja 555",
        telefono="3411000000",
    )
    cliente = controller.registrar_cliente(
        nombre="Elena",
        apellido="Gomez",
        email="elena@test.com",
        tipo_doc="DNI",
        nro_doc="32000000",
        domicilio="Santa Fe 777",
        telefono="3410000000",
    )
    prop = controller.registrar_propiedad(
        direccion="Entre Rios 300, Rosario",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=propietario.id,
    )
    controller.asignar_agente_a_propiedad(
        id_agente=agente.id, id_propiedad=prop.id, desde=datetime.now()
    )

    contrato = controller.solicitar_contrato(
        id_cliente=cliente.id,
        id_agente=agente.id,
        id_propiedad=prop.id,
        monto=200000.0,
        comision_porcentaje=10.0,
        tipo_contrato="Alquiler",
    )

    # Verificación de honorarios iniciales: 10% de 200,000 = 20,000 (3% agente = 6,000)
    assert contrato.monto_honorarios_totales == 20000.0
    assert contrato.monto_comision_agente == 6000.0

    # 1. Modificar porcentaje de honorarios y comisión del agente
    updated_contrato = controller.actualizar_comision_contrato(
        contrato.nro_contrato, comision_porcentaje=12.5, comision_agente_porcentaje=4.0
    )
    assert updated_contrato.comision_porcentaje == 12.5
    assert updated_contrato.monto_honorarios_totales == 25000.0
    assert updated_contrato.monto_comision_agente == 8000.0


    # 2. Agregar nueva cláusula
    nueva_cl = controller.agregar_clausula_contrato(
        contrato.nro_contrato,
        titulo="OCTAVA (DEPÓSITO DE GARANTÍA)",
        contenido="El locatario entrega la suma de $200.000 en concepto de depósito.",
    )
    assert nueva_cl.id is not None
    assert nueva_cl.titulo == "OCTAVA (DEPÓSITO DE GARANTÍA)"

    # 3. Editar cláusula
    cl_editada = controller.modificar_clausula_contrato(
        nueva_cl.id,
        titulo="OCTAVA (DEPÓSITO EN GARANTÍA ACTUALIZADO)",
        contenido="El locatario entrega en este acto la suma de $200.000.",
    )
    assert cl_editada.titulo == "OCTAVA (DEPÓSITO EN GARANTÍA ACTUALIZADO)"

    # 4. Eliminar cláusula
    res = controller.eliminar_clausula_contrato(nueva_cl.id)
    assert res is True

    clausulas_finales = controller.listar_clausulas_contrato(contrato.nro_contrato)
    assert not any(c.id == nueva_cl.id for c in clausulas_finales)


def test_desglose_honorarios_e_inmutabilidad_al_firmar():
    """
    Verifica el desglose entre honorarios totales, comisión de agente e inmobiliaria,
    y que al firmar el contrato se bloquee cualquier intento de modificación.
    """
    agente = controller.registrar_agente(
        nombre="Firma",
        apellido="Tester",
        email="firma@test.com",
        password="pass",
        cuil="20-50000000-9",
        matricula="MAT-300",
        tipo_doc="DNI",
        nro_doc="50000000",
        domicilio="Pellegrini 100",
        telefono="341999888",
    )
    propietario = controller.registrar_propietario(
        nombre="Owner",
        apellido="Test",
        email="owner@test.com",
        tipo_doc="DNI",
        nro_doc="16000000",
        domicilio="Mitre 100",
        telefono="341888777",
    )
    cliente = controller.registrar_cliente(
        nombre="Client",
        apellido="Test",
        email="client@test.com",
        tipo_doc="DNI",
        nro_doc="33000000",
        domicilio="San Martin 100",
        telefono="341777666",
    )
    prop = controller.registrar_propiedad(
        direccion="San Lorenzo 1500, Rosario",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=propietario.id,
    )
    controller.asignar_agente_a_propiedad(
        id_agente=agente.id, id_propiedad=prop.id, desde=datetime.now()
    )

    contrato = controller.solicitar_contrato(
        id_cliente=cliente.id,
        id_agente=agente.id,
        id_propiedad=prop.id,
        monto=100000.0,
        comision_porcentaje=10.0,  # 10% Honorario Total = $10.000
        comision_agente_porcentaje=3.0,  # 3% Comisión Agente = $3.000
        tipo_contrato="Alquiler",
    )

    # Verificación del desglose interno
    detalles = controller.obtener_detalles_contrato_completo(contrato.nro_contrato)
    assert detalles["monto_honorarios_totales"] == 10000.0
    assert detalles["monto_comision_agente"] == 3000.0
    assert detalles["monto_comision_inmobiliaria"] == 7000.0

    # Firmar el contrato
    signed = controller.firmar_contrato(contrato.nro_contrato)
    assert signed.estado == "activo"

    # Intentar modificar cláusulas o honorarios debe lanzar ValueError
    with pytest.raises(ValueError, match="El contrato ya ha sido firmado"):
        controller.agregar_clausula_contrato(
            contrato.nro_contrato, "NUEVA", "Contenido no permitido"
        )

    with pytest.raises(ValueError, match="El contrato ya ha sido firmado"):
        controller.actualizar_comision_contrato(contrato.nro_contrato, 15.0, 5.0)

    clausulas = controller.listar_clausulas_contrato(contrato.nro_contrato)
    if clausulas:
        with pytest.raises(ValueError, match="El contrato ya ha sido firmado"):
            controller.modificar_clausula_contrato(
                clausulas[0].id, "TITULO MODIFICADO", "Texto modificado"
            )

        with pytest.raises(ValueError, match="El contrato ya ha sido firmado"):
            controller.eliminar_clausula_contrato(clausulas[0].id)


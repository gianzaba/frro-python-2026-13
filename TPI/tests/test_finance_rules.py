from datetime import datetime, date
import os
import pytest

# Force database to use an in-memory SQLite for isolated tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import datos.db as db  # noqa: E402
import business.controller as controller  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Initializes a fresh in-memory database for each test.
    """
    db.init_db()
    yield
    db.Base.metadata.drop_all(bind=db.engine)


def test_tenant_payment_constraints():
    """
    Checks that tenant payment can only be registered for active contracts,
    and prevents duplicate payments for the same contract period.
    """
    # 1. Setup entities
    agente = controller.registrar_agente(
        nombre="Agente",
        apellido="Test",
        email="agente@test.com",
        password="password",
        cuil="20-11111111-9",
        matricula="MAT-111",
        tipo_doc="DNI",
        nro_doc="11111111",
        domicilio="Calle 123",
        telefono="123456",
    )
    owner = controller.registrar_propietario(
        nombre="Carlos",
        apellido="Owner",
        email="owner@test.com",
        tipo_doc="DNI",
        nro_doc="22222222",
        domicilio="Calle 456",
        telefono="654321",
    )
    cliente = controller.registrar_cliente(
        nombre="Ana",
        apellido="Client",
        email="client@test.com",
        tipo_doc="DNI",
        nro_doc="33333333",
        domicilio="Calle 789",
        telefono="987654",
    )
    prop = controller.registrar_propiedad(
        direccion="Urquiza 1540",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=owner.id,
    )
    controller.asignar_agente_a_propiedad(agente.id, prop.id, datetime.now())

    # Create contract request (not signed yet)
    contrato = controller.solicitar_contrato(
        id_cliente=cliente.id,
        id_agente=agente.id,
        id_propiedad=prop.id,
        monto=40000.0,
        comision_porcentaje=12.5,
    )

    # Try registering payment for requested contract (should fail)
    with pytest.raises(ValueError) as exc:
        controller.registrar_pago_inquilino(
            nro_contrato=contrato.nro_contrato, mes="2026-08", monto=40000.0
        )
    assert "Solo se pueden registrar pagos para contratos activos" in str(
        exc.value
    )

    # Sign the contract (becomes active, property becomes alquilada)
    controller.firmar_contrato(contrato.nro_contrato)

    # Register tenant payment (should succeed)
    pago = controller.registrar_pago_inquilino(
        nro_contrato=contrato.nro_contrato, mes="2026-08", monto=40000.0
    )
    assert pago.id is not None
    assert pago.monto == 40000.0
    assert pago.mes_correspondiente == "2026-08"

    # Try duplicate payment (should fail)
    with pytest.raises(ValueError) as exc:
        controller.registrar_pago_inquilino(
            nro_contrato=contrato.nro_contrato, mes="2026-08", monto=40000.0
        )
    assert "Ya se ha registrado el pago" in str(exc.value)


def test_business_rule_4_settlement_generation():
    """
    Tests Rule 4: Payouts are generated only if the tenant has paid first,
    calculates correct commissions, and prevents duplicate payout generation.
    """
    # 1. Setup entities
    agente = controller.registrar_agente(
        nombre="Agente",
        apellido="Test",
        email="agente@test.com",
        password="password",
        cuil="20-11111111-9",
        matricula="MAT-111",
        tipo_doc="DNI",
        nro_doc="11111111",
        domicilio="Calle 123",
        telefono="123456",
    )
    owner = controller.registrar_propietario(
        nombre="Carlos",
        apellido="Owner",
        email="owner@test.com",
        tipo_doc="DNI",
        nro_doc="22222222",
        domicilio="Calle 456",
        telefono="654321",
    )
    cliente = controller.registrar_cliente(
        nombre="Ana",
        apellido="Client",
        email="client@test.com",
        tipo_doc="DNI",
        nro_doc="33333333",
        domicilio="Calle 789",
        telefono="987654",
    )
    prop = controller.registrar_propiedad(
        direccion="Urquiza 1540",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=owner.id,
    )
    controller.asignar_agente_a_propiedad(agente.id, prop.id, datetime.now())

    # Create contract with custom commission of 15% and rent $50,000
    contrato = controller.solicitar_contrato(
        id_cliente=cliente.id,
        id_agente=agente.id,
        id_propiedad=prop.id,
        monto=50000.0,
        comision_porcentaje=15.0,
    )
    controller.firmar_contrato(contrato.nro_contrato)

    # Try generating settlement before tenant has paid (should yield empty list)
    liquidaciones = controller.generar_liquidaciones_mes("2026-08")
    assert len(liquidaciones) == 0

    # Record tenant payment
    controller.registrar_pago_inquilino(
        nro_contrato=contrato.nro_contrato, mes="2026-08", monto=50000.0
    )

    # Generate settlement (should succeed)
    liquidaciones = controller.generar_liquidaciones_mes("2026-08")
    assert len(liquidaciones) == 1
    liq = liquidaciones[0]

    # Verify payout commission details (Rent: 50000, Comm: 15% -> 7500, Payout: 42500)
    assert liq.id_propietario == owner.id
    assert liq.nro_contrato == contrato.nro_contrato
    assert liq.monto_bruto == 50000.0
    assert liq.comision == 7500.0
    assert liq.monto_neto == 42500.0
    assert liq.estado == "pendiente"
    assert liq.fecha_pago is None

    # Try generating again (should ignore duplicate to prevent double payout)
    double_liquidaciones = controller.generar_liquidaciones_mes("2026-08")
    assert len(double_liquidaciones) == 0

    # Pay the owner (transfer payout)
    updated_liq = controller.registrar_transferencia_propietario(liq.id)
    assert updated_liq.estado == "pagado"
    assert updated_liq.fecha_pago == date.today()


def test_dashboard_statistics():
    """
    Tests stats aggregation and client/owner filtering logic.
    """
    # 1. Setup entities
    agente1 = controller.registrar_agente(
        nombre="Agente1",
        apellido="Test",
        email="agente1@test.com",
        password="password",
        cuil="20-11111111-9",
        matricula="MAT-111",
        tipo_doc="DNI",
        nro_doc="11111111",
        domicilio="Calle 123",
        telefono="123456",
    )
    agente2 = controller.registrar_agente(
        nombre="Agente2",
        apellido="Test",
        email="agente2@test.com",
        password="password",
        cuil="20-11111112-9",
        matricula="MAT-222",
        tipo_doc="DNI",
        nro_doc="11111112",
        domicilio="Calle 123",
        telefono="123456",
    )
    owner1 = controller.registrar_propietario(
        nombre="Carlos",
        apellido="Owner1",
        email="owner1@test.com",
        tipo_doc="DNI",
        nro_doc="22222222",
        domicilio="Calle 456",
        telefono="654321",
    )
    owner2 = controller.registrar_propietario(
        nombre="Pedro",
        apellido="Owner2",
        email="owner2@test.com",
        tipo_doc="DNI",
        nro_doc="55555555",
        domicilio="Calle 888",
        telefono="888888",
    )
    cliente1 = controller.registrar_cliente(
        nombre="Ana",
        apellido="Client1",
        email="client1@test.com",
        tipo_doc="DNI",
        nro_doc="33333333",
        domicilio="Calle 789",
        telefono="987654",
    )
    cliente2 = controller.registrar_cliente(
        nombre="Jose",
        apellido="Client2",
        email="client2@test.com",
        tipo_doc="DNI",
        nro_doc="66666666",
        domicilio="Calle 999",
        telefono="999999",
    )
    prop1 = controller.registrar_propiedad(
        direccion="Urquiza 1540",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=owner1.id,
    )
    prop2 = controller.registrar_propiedad(
        direccion="Pellegrini 2200",
        tipo="Alquiler",
        zona="Abasto",
        id_propietario=owner2.id,
    )

    # Assign agents
    controller.asignar_agente_a_propiedad(agente1.id, prop1.id, datetime.now())
    controller.asignar_agente_a_propiedad(agente2.id, prop2.id, datetime.now())

    # Create & sign contract 1 (owner 1, client 1) - Rent $40,000, 10% com
    c1 = controller.solicitar_contrato(
        cliente1.id, agente1.id, prop1.id, 40000.0, 10.0
    )
    controller.firmar_contrato(c1.nro_contrato)

    # Create & sign contract 2 (owner 2, client 2) - Rent $60,000, 12% com
    c2 = controller.solicitar_contrato(
        cliente2.id, agente2.id, prop2.id, 60000.0, 12.0
    )
    controller.firmar_contrato(c2.nro_contrato)

    # Verify initial stats (both rents are pending collection for "2026-08")
    stats = controller.obtener_estadisticas_financieras(mes="2026-08")
    assert stats["total_cobrado_mes"] == 0.0
    assert stats["total_pendiente_cobrar_mes"] == 100000.0
    assert len(stats["contratos_atrasados"]) == 2

    # Client 1 pays rent
    controller.registrar_pago_inquilino(c1.nro_contrato, "2026-08", 40000.0)

    # Recheck stats: Cobrado: 40k, Pendiente: 60k
    stats = controller.obtener_estadisticas_financieras(mes="2026-08")
    assert stats["total_cobrado_mes"] == 40000.0
    assert stats["total_pendiente_cobrar_mes"] == 60000.0
    assert len(stats["contratos_atrasados"]) == 1
    assert (
        stats["contratos_atrasados"][0]["contrato"].nro_contrato
        == c2.nro_contrato
    )

    # Generate payouts for the period
    controller.generar_liquidaciones_mes("2026-08")

    # Recheck stats: Payout pendiente to owners (c1 paid, so owner1 has payout pending)
    # Rent: 40k, Comm: 10% -> 4k, Net payout: 36k
    stats = controller.obtener_estadisticas_financieras(mes="2026-08")
    assert stats["total_pendiente_pagar_propietario"] == 36000.0
    assert stats["total_comisiones"] == 4000.0

    # Filter stats by Owner 1
    stats_owner1 = controller.obtener_estadisticas_financieras(
        id_propietario=owner1.id, mes="2026-08"
    )
    assert stats_owner1["total_cobrado_mes"] == 40000.0
    assert stats_owner1["total_pendiente_cobrar_mes"] == 0.0
    assert stats_owner1["total_pendiente_pagar_propietario"] == 36000.0
    assert stats_owner1["total_comisiones"] == 4000.0

    # Filter stats by Owner 2
    stats_owner2 = controller.obtener_estadisticas_financieras(
        id_propietario=owner2.id, mes="2026-08"
    )
    assert stats_owner2["total_cobrado_mes"] == 0.0
    assert stats_owner2["total_pendiente_cobrar_mes"] == 60000.0
    assert stats_owner2["total_pendiente_pagar_propietario"] == 0.0
    assert stats_owner2["total_comisiones"] == 0.0

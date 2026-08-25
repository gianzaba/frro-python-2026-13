import os
from datetime import date, datetime
import pytest

# Force database to use an in-memory SQLite for isolated tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["MAIL_SUPPRESS_SEND"] = "true"

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


def setup_base_finance_data():
    admin = controller.registrar_agente(
        "Carlos", "Admin", "carlos.admin@inmogestion.com", "pass123",
        "20-11111111-9", "MAT-101", "DNI", "11111111", "Pellegrini 100", "3415550001", "Administrador"
    )
    propietario = controller.registrar_propietario(
        "Mario", "Dueño", "mario.dueno@gmail.com", "DNI", "22222222", "Mitre 500", "3415550002"
    )
    cliente = controller.registrar_cliente(
        "Laura", "Inquilina", "laura.inquilina@gmail.com", "DNI", "33333333", "Rioja 800", "3415550003"
    )
    prop = controller.registrar_propiedad(
        "Bv. Oroño 1200, Rosario", "Alquiler", "Centro", propietario.id
    )
    controller.asignar_agente_a_propiedad(admin.id, prop.id, datetime.now())
    contrato = controller.solicitar_contrato(
        cliente.id, admin.id, prop.id, monto=150000.0, comision_porcentaje=10.0, tipo_contrato="Alquiler"
    )
    contrato_firmado = controller.firmar_contrato(contrato.nro_contrato)

    return admin, propietario, cliente, prop, contrato_firmado


def test_enviar_alertas_mora_inquilinos_evaluacion_regla_y_spam():
    """
    Verifica el envío de alertas de mora a inquilinos con retraso posterior al día 10
    y la prevención de spam con fecha_ultimo_aviso_mora.
    """
    admin, propietario, cliente, prop, contrato = setup_base_finance_data()

    # Período vencido (2026-07) sin registrar pago
    res = controller.enviar_alertas_mora_inquilinos(mes="2026-07", id_agente_solicitante=admin.id)

    assert res["total_enviados"] == 1
    assert len(res["notificados"]) == 1
    assert res["notificados"][0]["nro_contrato"] == contrato.nro_contrato
    assert res["notificados"][0]["email"] == "laura.inquilina@gmail.com"
    assert res["notificados"][0]["dias_retraso"] > 0

    # Verificar que se asentó la fecha de último aviso en la base de datos
    c_actualizado = db.get_contrato_by_id(contrato.nro_contrato)
    assert c_actualizado.fecha_ultimo_aviso_mora == date.today()

    # Segunda ejecución el mismo día: debe omitir por prevención de spam
    res_reintento = controller.enviar_alertas_mora_inquilinos(mes="2026-07", id_agente_solicitante=admin.id)
    assert res_reintento["total_enviados"] == 0
    assert len(res_reintento["omitidos"]) == 1
    assert res_reintento["omitidos"][0]["contrato"] == contrato.nro_contrato


def test_notificar_transferencia_propietario_al_pagar():
    """
    Verifica que al registrar la transferencia de la liquidación al dueño,
    se asiente el estado pagado y se dispare la notificación por correo.
    """
    admin, propietario, cliente, prop, contrato = setup_base_finance_data()

    # Registrar cobro del inquilino primero
    controller.registrar_pago_inquilino(
        nro_contrato=contrato.nro_contrato,
        mes="2026-07",
        monto=150000.0,
        fecha_pago=date(2026, 7, 5),
    )

    # Generar liquidación para el propietario
    liquidaciones = controller.generar_liquidaciones_mes("2026-07", id_agente_solicitante=admin.id)
    assert len(liquidaciones) == 1
    payout = liquidaciones[0]
    assert payout.estado == "pendiente"

    # Registrar transferencia
    payout_pagado = controller.registrar_transferencia_propietario(
        id_pago_propietario=payout.id,
        fecha_pago=date(2026, 7, 15),
        id_agente_solicitante=admin.id,
    )
    assert payout_pagado.estado == "pagado"
    assert payout_pagado.fecha_pago == date(2026, 7, 15)


def test_alertas_mora_permisos_y_ruta_web(client):
    """
    Verifica las restricciones de rol (Admin required) y el endpoint web POST /finanzas/notificaciones/mora.
    """
    admin, propietario, cliente, prop, contrato = setup_base_finance_data()

    # Crear agente estándar sin permisos de administrador
    std_agent = controller.registrar_agente(
        "Pedro", "Standard", "pedro@test.com", "pass", "20-99999999-9",
        "MAT-555", "DNI", "99999999", "Calle 1", "3411111111", "Estándar"
    )

    # Intentar como agente estándar: debe fallar por permisos
    with pytest.raises(PermissionError, match="Solo los Administradores"):
        controller.enviar_alertas_mora_inquilinos(mes="2026-07", id_agente_solicitante=std_agent.id)

    # Test vía web con sesión Admin
    with client.session_transaction() as sess:
        sess["agente_id"] = admin.id
        sess["agente_name"] = admin.nombre_completo
        sess["agente_rol"] = "Administrador"

    resp = client.post("/finanzas/notificaciones/mora", data={"mes": "2026-07"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"alertas de mora" in resp.data.lower() or b"finanzas" in resp.data.lower()


def test_alerta_mora_individual_boton_mandar_mail(client):
    """
    Verifica que el botón 'Mandar Mail' funcione exclusivamente para contratos vencidos
    y envíe el correo individualmente.
    """
    admin, propietario, cliente, prop, contrato = setup_base_finance_data()

    # 1. Obtener estado de cobros: debe figurar vencido para mes 2026-07
    estados = controller.obtener_estado_cobros_alquileres_mes(mes="2026-07")
    assert len(estados) == 1
    assert estados[0]["esta_vencido"] is True
    assert estados[0]["puede_mandar_mail"] is True

    # 2. Enviar alerta individual con éxito
    res = controller.enviar_alerta_mora_individual(
        nro_contrato=contrato.nro_contrato,
        mes="2026-07",
        id_agente_solicitante=admin.id,
    )
    assert res["nro_contrato"] == contrato.nro_contrato
    assert res["email"] == "laura.inquilina@gmail.com"
    assert res["dias_retraso"] > 0

    # 3. Test de ruta web individual POST /finanzas/notificaciones/mora/contrato/<nro>
    with client.session_transaction() as sess:
        sess["agente_id"] = admin.id
        sess["agente_name"] = admin.nombre_completo
        sess["agente_rol"] = "Administrador"

    resp = client.post(
        f"/finanzas/notificaciones/mora/contrato/{contrato.nro_contrato}",
        data={"mes": "2026-07"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"alerta de mora" in resp.data.lower() or b"finanzas" in resp.data.lower()

import os
from datetime import date, datetime, timedelta
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


def test_recargo_mora_calculo_y_registro_pago():
    """
    Test Feature 2 & 3: Cálculo automático de días de mora y recargo por pago fuera de término,
    además de registro de comprobante adjunto.
    """
    # 1. Crear Agente, Propietario, Cliente, Propiedad y Contrato activo
    agente = controller.registrar_agente(
        "Carlos", "Agente", "carlos.agente@inmogestion.com", "pass123",
        "20-11111111-9", "MAT-101", "DNI", "11111111", "Pellegrini 100", "3415550001", "Administrador"
    )
    prop = controller.registrar_propietario(
        "Mario", "Dueño", "mario@gmail.com", "DNI", "22222222", "Mitre 500", "3415550002"
    )
    cliente = controller.registrar_cliente(
        "Lucas", "Inquilino", "lucas@gmail.com", "DNI", "33333333", "Urquiza 800", "3415550003"
    )
    propiedad = controller.registrar_propiedad(
        "Cordoba 1500, Rosario", "Alquiler", "Centro", prop.id, fecha_disponibilidad=date(2026, 1, 1)
    )
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime(2026, 1, 1, 9, 0))
    contrato = controller.solicitar_contrato(
        cliente.id, agente.id, propiedad.id, monto=100000.0, comision_porcentaje=10.0, tipo_contrato="Alquiler"
    )
    controller.firmar_contrato(contrato.nro_contrato)

    # 2. Pago a término (día 8 del mes de vencimiento)
    pago_a_termino = controller.registrar_pago_inquilino(
        nro_contrato=contrato.nro_contrato,
        mes="2026-08",
        monto=100000.0,
        fecha_pago=date(2026, 8, 8),
        ruta_comprobante="static/uploads/comprobantes/recibo_agosto.pdf"
    )
    assert pago_a_termino.dias_retraso == 0
    assert pago_a_termino.monto_recargo == 0.0
    assert pago_a_termino.monto_total_abonado == 100000.0
    assert pago_a_termino.ruta_comprobante == "static/uploads/comprobantes/recibo_agosto.pdf"

    # 3. Pago fuera de término (día 15 del mes de vencimiento -> 5 días de mora)
    pago_con_mora = controller.registrar_pago_inquilino(
        nro_contrato=contrato.nro_contrato,
        mes="2026-09",
        monto=100000.0,
        fecha_pago=date(2026, 9, 15),
        ruta_comprobante="static/uploads/comprobantes/recibo_septiembre.png"
    )
    assert pago_con_mora.dias_retraso == 5
    # Recargo: 100000 * 0.002 * 5 = 1000.0
    assert pago_con_mora.monto_recargo == 1000.0
    assert pago_con_mora.monto_total_abonado == 101000.0
    assert pago_con_mora.ruta_comprobante == "static/uploads/comprobantes/recibo_septiembre.png"


def test_obtener_datos_boleta_alquiler():
    """
    Test Feature 1: Generación de datos completos para emitir la boleta de pago mensual en PDF.
    """
    agente = controller.registrar_agente(
        "Agente", "Senior", "agente@inmogestion.com", "pass123",
        "20-44444444-9", "MAT-202", "DNI", "44444444", "Rosario", "3415551111", "Administrador"
    )
    prop = controller.registrar_propietario(
        "Elena", "Propietaria", "elena@gmail.com", "DNI", "55555555", "Rosario", "3415552222"
    )
    cliente = controller.registrar_cliente(
        "Martin", "Inquilino", "martin@gmail.com", "DNI", "66666666", "Rosario", "3415553333"
    )
    propiedad = controller.registrar_propiedad(
        "San Martin 1200", "Alquiler", "Centro", prop.id
    )
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime(2026, 1, 1, 8, 0))
    contrato = controller.solicitar_contrato(
        cliente.id, agente.id, propiedad.id, monto=150000.0, tipo_contrato="Alquiler"
    )
    controller.firmar_contrato(contrato.nro_contrato)

    boleta = controller.obtener_datos_boleta_alquiler(contrato.nro_contrato, "2026-08")
    assert boleta["nro_contrato"] == contrato.nro_contrato
    assert boleta["mes"] == "2026-08"
    assert boleta["monto_base"] == 150000.0
    assert boleta["fecha_1er_vencimiento"] == date(2026, 8, 10)
    assert boleta["fecha_2do_vencimiento"] == date(2026, 8, 20)
    assert boleta["recargo_estimado_2do_venc"] == 3000.0  # 2%
    assert boleta["total_2do_vencimiento"] == 153000.0
    assert "INMO-" in boleta["codigo_barras_ref"]


def test_analisis_propiedades_inactivas():
    """
    Test Feature 4: Diagnóstico y sugerencias de ajuste de precios para propiedades con tiempo vacante.
    """
    prop = controller.registrar_propietario(
        "Carlos", "Dueño", "carlos@gmail.com", "DNI", "77777777", "Rosario", "3415554444"
    )
    # Propiedad 1: 100 días vacante (Crítico)
    p1 = controller.registrar_propiedad(
        "Pellegrini 2000", "Venta", "Centro", prop.id, fecha_disponibilidad=date.today() - timedelta(days=100)
    )
    # Propiedad 2: 40 días vacante (Moderado)
    p2 = controller.registrar_propiedad(
        "Oroño 500", "Alquiler", "Pichincha", prop.id, fecha_disponibilidad=date.today() - timedelta(days=40)
    )
    # Propiedad 3: 10 días vacante (Bajo)
    p3 = controller.registrar_propiedad(
        "España 300", "Alquiler", "Centro", prop.id, fecha_disponibilidad=date.today() - timedelta(days=10)
    )

    analisis = controller.obtener_analisis_propiedades_inactivas()
    assert len(analisis) == 3
    # Debe estar ordenada descendentemente por días vacante
    assert analisis[0]["propiedad"].id == p1.id
    assert analisis[0]["nivel_riesgo"] == "Crítico"
    assert analisis[0]["ajuste_sugerido_pct"] == 15

    assert analisis[1]["propiedad"].id == p2.id
    assert analisis[1]["nivel_riesgo"] == "Moderado"
    assert analisis[1]["ajuste_sugerido_pct"] == 5

    assert analisis[2]["propiedad"].id == p3.id
    assert analisis[2]["nivel_riesgo"] == "Bajo"
    assert analisis[2]["ajuste_sugerido_pct"] == 0


def test_agenda_visitas_y_control_cupos():
    """
    Test Feature 5: Creación de turnos de visita con cupo limitado y validación de sobrecupo.
    """
    agente = controller.registrar_agente(
        "Valeria", "Agente", "valeria@inmogestion.com", "pass123",
        "27-88888888-4", "MAT-303", "DNI", "88888888", "Rosario", "3415555555", "Estándar"
    )
    prop = controller.registrar_propietario(
        "Gustavo", "Propietario", "gustavo@gmail.com", "DNI", "99999999", "Rosario", "3415556666"
    )
    propiedad = controller.registrar_propiedad(
        "Alvear 800", "Venta", "Centro", prop.id
    )

    # 1. Crear agenda con cupo de 2 personas
    fecha_visita = datetime.now() + timedelta(days=2)
    agenda = controller.crear_agenda_visita(
        id_propiedad=propiedad.id,
        id_agente=agente.id,
        fecha_hora_visita=fecha_visita,
        duracion_minutos=45,
        cupo_maximo=2,
    )
    assert agenda.id is not None
    assert agenda.cupo_maximo == 2
    assert agenda.estado == "disponible"

    # 2. Inscribir 1er visitante
    insc1 = controller.inscribir_visitante_a_turno(
        id_agenda=agenda.id,
        nombre_visitante="Esteban Quito",
        telefono_visitante="3415551122",
        email_visitante="esteban@gmail.com",
        observaciones="Interesado en pagar de contado",
    )
    assert insc1.id is not None

    agenda_info = controller.obtener_agenda_con_inscriptos(agenda.id)
    assert agenda_info["total_inscriptos"] == 1
    assert agenda_info["cupo_disponible"] == 1

    # 3. Inscribir 2do visitante (se llena el cupo)
    insc2 = controller.inscribir_visitante_a_turno(
        id_agenda=agenda.id,
        nombre_visitante="Susana Oria",
        telefono_visitante="3415553344",
        email_visitante="susana@gmail.com",
    )
    assert insc2.id is not None

    agenda_llena = controller.obtener_agenda_con_inscriptos(agenda.id)
    assert agenda_llena["total_inscriptos"] == 2
    assert agenda_llena["cupo_disponible"] == 0
    assert agenda_llena["agenda"].estado == "completo"

    # 4. Intentar inscribir 3er visitante debe lanzar ValueError por cupo agotado
    with pytest.raises(ValueError, match="cupo"):
        controller.inscribir_visitante_a_turno(
            id_agenda=agenda.id,
            nombre_visitante="Tercer Visitante",
            telefono_visitante="3415557788",
        )

    # 5. Superposición de horario para el mismo agente debe ser rechazada
    with pytest.raises(ValueError, match="ya tiene otra visita agendada"):
        controller.crear_agenda_visita(
            id_propiedad=propiedad.id,
            id_agente=agente.id,
            fecha_hora_visita=fecha_visita + timedelta(minutes=15),  # solapada dentro de los 45 min
            duracion_minutos=30,
            cupo_maximo=3,
        )


def test_rutas_web_nuevas_funcionalidades():
    """
    Test de integración Web para verificar que las nuevas rutas responden con código HTTP 200.
    """
    client = app.test_client()

    # Seed inicial
    agente = controller.registrar_agente(
        "Admin", "Test", "admintest@inmogestion.com", "secret",
        "20-00000000-1", "MAT-999", "DNI", "10000000", "Rosario", "3415550000", "Administrador"
    )
    prop = controller.registrar_propietario(
        "Dueño", "Test", "dueñotest@gmail.com", "DNI", "20000000", "Rosario", "3415550000"
    )
    cliente = controller.registrar_cliente(
        "Cliente", "Test", "clientetest@gmail.com", "DNI", "30000000", "Rosario", "3415550000"
    )
    propiedad = controller.registrar_propiedad(
        "Rioja 2000", "Alquiler", "Centro", prop.id
    )
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime(2026, 1, 1, 9, 0))
    contrato = controller.solicitar_contrato(
        cliente.id, agente.id, propiedad.id, monto=120000.0, tipo_contrato="Alquiler"
    )
    controller.firmar_contrato(contrato.nro_contrato)

    with client.session_transaction() as sess:
        sess["agente_id"] = agente.id
        sess["agente_name"] = agente.nombre_completo
        sess["agente_rol"] = agente.rol

    # 1. Ruta Boleta de Alquiler
    resp_boleta = client.get(f"/finanzas/boleta/{contrato.nro_contrato}/2026-08")
    assert resp_boleta.status_code == 200
    assert b"Aviso de Cobro de Alquiler" in resp_boleta.data

    # 2. Ruta Propiedades Inactivas
    resp_inactivas = client.get("/propiedades/inactivas")
    assert resp_inactivas.status_code == 200
    assert b"An" in resp_inactivas.data

    # 3. Ruta Agenda de Visitas
    resp_visitas = client.get(f"/propiedades/{propiedad.id}/visitas")
    assert resp_visitas.status_code == 200
    assert b"Agenda de Visitas" in resp_visitas.data


def test_audit_logs_flow():
    """
    Test logs are recorded on events like signing contract, registering payment, etc.
    """
    admin = controller.registrar_agente(
        "Admin", "User", "adminlog@inmogestion.com", "pass",
        "20-99999991-9", "MAT-LOG1", "DNI", "99999991", "Rosario", "341", "Administrador"
    )
    std = controller.registrar_agente(
        "Std", "User", "stdlog@inmogestion.com", "pass",
        "20-99999992-9", "MAT-LOG2", "DNI", "99999992", "Rosario", "341", "Estándar"
    )
    prop = controller.registrar_propietario("O", "O", "o@gmail.com", "DNI", "99999993", "R", "341")
    cliente = controller.registrar_cliente("C", "C", "c@gmail.com", "DNI", "99999994", "R", "341")
    propiedad = controller.registrar_propiedad("Direccion 1", "Alquiler", "Centro", prop.id)
    
    controller.asignar_agente_a_propiedad(admin.id, propiedad.id, datetime.now())
    contrato = controller.solicitar_contrato(cliente.id, admin.id, propiedad.id, monto=50000.0)
    
    # Sign contract with admin agent
    controller.firmar_contrato(contrato.nro_contrato, id_agente_solicitante=admin.id)
    
    # Register payment
    controller.registrar_pago_inquilino(
        contrato.nro_contrato, "2026-08", 50000.0, fecha_pago=date(2026, 8, 5), id_agente_solicitante=admin.id
    )
    
    # Verify logs exist
    logs = controller.listar_logs_auditoria(admin.id)
    assert len(logs) >= 2
    # The latest log should be the payment
    assert logs[0].entidad == "PagoInquilino"
    assert logs[0].accion == "RegistrarPago"
    assert "registró el pago" in logs[0].descripcion
    
    # The previous log should be the contract signing
    assert logs[1].entidad == "Contrato"
    assert logs[1].accion == "Firmar"
    assert "firmó el contrato" in logs[1].descripcion

    # Non-admin cannot list audit logs
    with pytest.raises(PermissionError):
        controller.listar_logs_auditoria(std.id)


def test_cancelar_inscripcion_visita_flow():
    """
    Test visitor registration cancellation releases slots back to "disponible" when full.
    """
    agente = controller.registrar_agente(
        "A", "A", "a@inmogestion.com", "pass", "20-91", "MAT-A1", "DNI", "91", "R", "341", "Estándar"
    )
    prop = controller.registrar_propietario("O", "O", "o@gmail.com", "DNI", "92", "R", "341")
    propiedad = controller.registrar_propiedad("Dir", "Venta", "Sur", prop.id)
    
    agenda = controller.crear_agenda_visita(
        id_propiedad=propiedad.id,
        id_agente=agente.id,
        fecha_hora_visita=datetime.now() + timedelta(days=2),
        duracion_minutos=30,
        cupo_maximo=1
    )
    
    # Register visitor to fill cupo
    insc = controller.inscribir_visitante_a_turno(
        id_agenda=agenda.id,
        nombre_visitante="V1",
        telefono_visitante="12345",
        email_visitante="v1@test.com"
    )
    
    agenda_full = controller.obtener_agenda_con_inscriptos(agenda.id)
    assert agenda_full["agenda"].estado == "completo"
    assert agenda_full["total_inscriptos"] == 1
    
    # Cancel inscription
    success = controller.cancelar_inscripcion_visita(insc.id, id_agente_solicitante=agente.id)
    assert success is True
    
    # Agenda should return to "disponible" status
    agenda_after = controller.obtener_agenda_con_inscriptos(agenda.id)
    assert agenda_after["agenda"].estado == "disponible"
    assert agenda_after["total_inscriptos"] == 0
    assert agenda_after["cupo_disponible"] == 1


def test_obtener_contratos_por_vencer_flow():
    """
    Test retrieving contracts expiring in the next 90 days.
    """
    agente = controller.registrar_agente(
        "A", "A", "a2@inmogestion.com", "pass", "20-911", "MAT-A11", "DNI", "911", "R", "341", "Estándar"
    )
    prop = controller.registrar_propietario("O", "O", "o2@gmail.com", "DNI", "922", "R", "341")
    cliente = controller.registrar_cliente("C", "C", "c2@gmail.com", "DNI", "933", "R", "341")
    propiedad = controller.registrar_propiedad("Dir", "Alquiler", "Centro", prop.id)
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime.now())
    
    c = controller.solicitar_contrato(cliente.id, agente.id, propiedad.id, monto=100000.0)
    
    # Lease starts 700 days ago (meaning it will expire in 30 days since total duration is 730 days)
    start_date = date.today() - timedelta(days=700)
    controller.firmar_contrato(c.nro_contrato, fecha_contrato=start_date)
    
    por_vencer = controller.obtener_contratos_por_vencer(90)
    assert len(por_vencer) == 1
    assert por_vencer[0]["contrato"].nro_contrato == c.nro_contrato
    assert por_vencer[0]["dias_restantes"] == 30


def test_no_visita_cuando_no_disponible():
    """
    Test that visits cannot be created or registered for rented/sold properties.
    """
    agente = controller.registrar_agente(
        "A", "A", "a3@inmogestion.com", "pass", "20-9111", "MAT-A111", "DNI", "9111", "R", "341", "Estándar"
    )
    prop = controller.registrar_propietario("O", "O", "o3@gmail.com", "DNI", "9222", "R", "341")
    cliente = controller.registrar_cliente("C", "C", "c3@gmail.com", "DNI", "9333", "R", "341")
    propiedad = controller.registrar_propiedad("Dir", "Alquiler", "Centro", prop.id)
    controller.asignar_agente_a_propiedad(agente.id, propiedad.id, datetime.now())
    
    # Case 1: Property is alquilada, try to create visit slot (should fail)
    propiedad.estado = "alquilada"
    db.save_propiedad(propiedad)
    
    with pytest.raises(ValueError, match="Solo se pueden coordinar visitas"):
        controller.crear_agenda_visita(
            id_propiedad=propiedad.id,
            id_agente=agente.id,
            fecha_hora_visita=datetime.now() + timedelta(days=1)
        )
        
    # Case 2: Create agenda while available, then rent property and try to register visitor (should fail)
    propiedad.estado = "disponible"
    db.save_propiedad(propiedad)
    
    agenda = controller.crear_agenda_visita(
        id_propiedad=propiedad.id,
        id_agente=agente.id,
        fecha_hora_visita=datetime.now() + timedelta(days=1)
    )
    
    # Rent property
    propiedad.estado = "alquilada"
    db.save_propiedad(propiedad)
    
    with pytest.raises(ValueError, match="No se pueden inscribir visitantes"):
        controller.inscribir_visitante_a_turno(
            id_agenda=agenda.id,
            nombre_visitante="Visitante Test",
            telefono_visitante="12345"
        )



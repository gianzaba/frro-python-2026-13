import os
import sys
from datetime import date, timedelta

# Ensure parent directory is in sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest
import datos.db as db
import business.controller as controller


@pytest.fixture(autouse=True)
def setup_test_db():
    db.init_db(reset=True)
    yield
    db.Base.metadata.drop_all(bind=db.engine)


def test_agente_rol_and_admin_validation():
    # Create standard agent and admin agent
    agente_std = controller.registrar_agente(
        nombre="Agente",
        apellido="Estandar",
        email="std@inmo.com",
        password="pwd",
        cuil="20-11111111-1",
        matricula="MAT-001",
        tipo_doc="DNI",
        nro_doc="11111111",
        domicilio="Calle 1",
        telefono="12345",
        rol="Estándar",
    )

    agente_admin = controller.registrar_agente(
        nombre="Agente",
        apellido="Admin",
        email="admin@inmo.com",
        password="pwd",
        cuil="20-22222222-2",
        matricula="MAT-002",
        tipo_doc="DNI",
        nro_doc="22222222",
        domicilio="Calle 2",
        telefono="54321",
        rol="Administrador",
    )

    assert controller.es_administrador(agente_std.id) is False
    assert controller.es_administrador(agente_admin.id) is True

    # Check permission restriction for liquidations
    with pytest.raises(PermissionError):
        controller.generar_liquidaciones_mes("2026-08", id_agente_solicitante=agente_std.id)

    with pytest.raises(PermissionError):
        controller.exportar_reporte_financiero_csv("cobros", id_agente_solicitante=agente_std.id)


def test_dias_vacante_and_ranking():
    propietario = controller.registrar_propietario(
        nombre="Juan",
        apellido="Perez",
        email="juan@perez.com",
        tipo_doc="DNI",
        nro_doc="33333333",
        domicilio="Calle 3",
        telefono="9999",
    )

    fecha_antigua = date.today() - timedelta(days=45)
    prop = controller.registrar_propiedad(
        direccion="San Martin 100",
        tipo="Alquiler",
        zona="Centro",
        id_propietario=propietario.id,
        fecha_disponibilidad=fecha_antigua,
    )

    dias = controller.calcular_dias_vacante(prop)
    assert dias >= 45

    ranking = controller.obtener_ranking_propiedades_vacantes()
    assert len(ranking) > 0
    assert ranking[0]["dias_vacante"] >= 45

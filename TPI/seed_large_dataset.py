from datetime import date, datetime, timedelta
import business.controller as controller
import datos.db as db


def seed_large_dataset():
    print("Iniciando inyeccion masiva de datos en la base de datos...")

    # 1. Agentes
    agentes_data = [
        ("Admin", "Principal", "admin@inmogestion.com", "adminpassword", "20-33445566-9",
         "MAT-8844", "DNI", "33445566", "Av. Pellegrini 250, Rosario", "3415556677", "Administrador"),
        ("Valeria", "Torres", "valeria.torres@inmogestion.com", "pass123", "27-35667788-4",
         "MAT-9012", "DNI", "35667788", "Bv. Oroño 1120, Rosario", "3415558899", "Administrador"),
        ("Martín", "Gómez", "martin.gomez@inmogestion.com", "pass123", "20-38112233-9",
         "MAT-9450", "DNI", "38112233", "Cordoba 1850, Rosario", "3415551133", "Estándar"),
        ("Lucas", "Benítez", "lucas.benitez@inmogestion.com", "pass123", "20-39445566-9",
         "MAT-9820", "DNI", "39445566", "Santa Fe 2100, Rosario", "3415554466", "Estándar"),
        ("Carolina", "Díaz", "carolina.diaz@inmogestion.com", "pass123", "27-41223344-4",
         "MAT-9955", "DNI", "41223344", "Rioja 1400, Rosario", "3415557788", "Estándar"),
    ]

    agentes_map = {}
    for nom, ape, mail, pwd, cuil, mat, tdoc, ndoc, dom, tel, rol in agentes_data:
        ag = db.get_agente_by_email(mail)
        if not ag:
            ag = controller.registrar_agente(nom, ape, mail, pwd, cuil, mat, tdoc, ndoc, dom, tel, rol)
            print(f" [+] Agente creado: {ag.nombre_completo} ({rol})")
        agentes_map[mail] = ag

    # 2. Propietarios
    propietarios_data = [
        ("Roberto", "Álvarez", "roberto.alvarez@gmail.com", "DNI", "14223344",
         "Paraguay 750, Rosario", "3414221100"),
        ("Silvia", "Fernández", "silvia.fernandez@hotmail.com", "DNI", "16554433",
         "Alvear 1250, Rosario", "3414332211"),
        ("Jorge", "Mendoza", "jorge.mendoza@yahoo.com", "DNI", "18776655",
         "Balcarce 420, Rosario", "3414443322"),
        ("Claudia", "Rossi", "claudia.rossi@gmail.com", "DNI", "20998877",
         "San Lorenzo 1680, Rosario", "3414554433"),
        ("Esteban", "Castro", "esteban.castro@outlook.com", "DNI", "22114477",
         "Italia 930, Rosario", "3414665544"),
        ("Beatriz", "Vázquez", "beatriz.vazquez@gmail.com", "DNI", "23445588",
         "Jujuy 2200, Rosario", "3414776655"),
        ("Mariano", "Herrera", "mariano.herrera@gmail.com", "DNI", "25667799",
         "Dorrego 1450, Rosario", "3414887766"),
        ("Lucía", "Peralta", "lucia.peralta@gmail.com", "DNI", "27889900",
         "España 620, Rosario", "3414998877"),
    ]

    propietarios_list = []
    for nom, ape, mail, tdoc, ndoc, dom, tel in propietarios_data:
        p = db.get_propietario_by_doc(tdoc, ndoc)
        if not p:
            p = controller.registrar_propietario(nom, ape, mail, tdoc, ndoc, dom, tel)
            print(f" [+] Propietario creado: {p.nombre_completo}")
        propietarios_list.append(p)

    # 3. Clientes / Inquilinos
    clientes_data = [
        ("Gonzalo", "Martínez", "gonzalo.martinez@gmail.com", "DNI", "34112233",
         "Pellegrini 1420, Rosario", "3415112233"),
        ("Florencia", "Suárez", "florencia.suarez@gmail.com", "DNI", "35223344",
         "Urquiza 2050, Rosario", "3415223344"),
        ("Matías", "Romero", "matias.romero@hotmail.com", "DNI", "36334455",
         "Tucumán 1780, Rosario", "3415334455"),
        ("Camila", "López", "camila.lopez@yahoo.com", "DNI", "37445566",
         "San Juan 850, Rosario", "3415445566"),
        ("Nicolás", "Gutiérrez", "nicolas.guti@gmail.com", "DNI", "38556677",
         "Moreno 1100, Rosario", "3415556677"),
        ("Julieta", "Acosta", "julieta.acosta@gmail.com", "DNI", "39667788",
         "Catamarca 1950, Rosario", "3415667788"),
        ("Agustín", "Navarro", "agustin.navarro@gmail.com", "DNI", "40778899",
         "Zeballos 1300, Rosario", "3415778899"),
        ("Sofía", "Domínguez", "sofia.dominguez@gmail.com", "DNI", "41889900",
         "Laprida 1140, Rosario", "3415889900"),
        ("Tomás", "Ríos", "tomas.rios@gmail.com", "DNI", "42990011",
         "9 de Julio 1720, Rosario", "3415990011"),
        ("Valentina", "Paz", "valentina.paz@gmail.com", "DNI", "43112200",
         "Salta 2400, Rosario", "3415001122"),
    ]

    clientes_list = []
    for nom, ape, mail, tdoc, ndoc, dom, tel in clientes_data:
        c = db.get_cliente_by_doc(tdoc, ndoc)
        if not c:
            c = controller.registrar_cliente(nom, ape, mail, tdoc, ndoc, dom, tel)
            print(f" [+] Cliente creado: {c.nombre_completo}")
        clientes_list.append(c)

    # 4. Propiedades
    hoy = date.today()
    propiedades_catalogo = [
        # Inmuebles Críticos (>90 días)
        ("Bv. Oroño 350, Piso 8 (Semi-piso)", "Alquiler", "Centro", propietarios_list[0].id, hoy - timedelta(days=115)),
        ("Av. Carballo 180, Puerto Norte", "Venta", "Puerto Norte", propietarios_list[1].id, hoy - timedelta(days=102)),
        ("Córdoba 2800, Local Comercial", "Alquiler", "Echesortu", propietarios_list[2].id, hoy - timedelta(days=95)),

        # Inmuebles Riesgo Alto (61-90 días)
        ("Pellegrini 1750, 2 Dormitorios", "Alquiler", "Abasto", propietarios_list[3].id, hoy - timedelta(days=82)),
        ("Mitre 650, Monoambiente c/ Balcón", "Alquiler", "Centro", propietarios_list[4].id, hoy - timedelta(days=70)),
        ("Alberdi 850, Casa con Jardín", "Venta", "Alberdi", propietarios_list[5].id, hoy - timedelta(days=65)),

        # Inmuebles Riesgo Moderado (31-60 días)
        ("Jujuy 2100, 1 Dormitorio", "Alquiler", "Pichincha", propietarios_list[6].id, hoy - timedelta(days=52)),
        ("España 1400, Oficina Corporativa", "Alquiler", "Centro", propietarios_list[7].id, hoy - timedelta(days=44)),
        ("Fisherton - Wilde 400, Residencia", "Venta", "Fisherton", propietarios_list[0].id, hoy - timedelta(days=38)),

        # Inmuebles Recientes / Normal (<=30 días)
        ("Urquiza 1950, Dúplex de Categoría", "Alquiler", "Centro", propietarios_list[1].id, hoy - timedelta(days=18)),
        ("Santa Fe 2800, 2 Dormitorios", "Alquiler", "Lourdes", propietarios_list[2].id, hoy - timedelta(days=12)),
        ("San Lorenzo 1200, Piso Exclusivo", "Venta", "Centro", propietarios_list[3].id, hoy - timedelta(days=5)),
        ("Rioja 2200, Casa de Pasillo", "Alquiler", "Centro", propietarios_list[4].id, hoy - timedelta(days=2)),
    ]

    agentes_pool = list(agentes_map.values())
    propiedades_creadas = []

    for idx, (dir_p, tipo_p, zona_p, id_prop, f_disp) in enumerate(propiedades_catalogo):
        # Buscar si ya existe por dirección
        existentes = [p for p in db.list_propiedades() if p.direccion == dir_p]
        if existentes:
            prop = existentes[0]
        else:
            prop = controller.registrar_propiedad(dir_p, tipo_p, zona_p, id_prop, fecha_disponibilidad=f_disp)
            agente_asig = agentes_pool[idx % len(agentes_pool)]
            controller.asignar_agente_a_propiedad(agente_asig.id, prop.id, desde=datetime.now() - timedelta(days=30))
            print(f" [+] Propiedad registrada: {prop.direccion} (Asignada a {agente_asig.nombre})")
        propiedades_creadas.append(prop)

    # 5. Contratos
    contratos_firmados = []

    # Helper to solicit and sign
    def crear_y_firmar(idx_cli, idx_prop, monto, comision, comision_agente, tipo):
        prop = propiedades_creadas[idx_prop]
        if prop.estado != "disponible":
            return None
        asig = controller.obtener_asignacion_activa_propiedad(prop.id)
        if not asig:
            return None
        c = controller.solicitar_contrato(
            id_cliente=clientes_list[idx_cli].id,
            id_agente=asig.id_agente,
            id_propiedad=prop.id,
            monto=monto,
            comision_porcentaje=comision,
            comision_agente_porcentaje=comision_agente,
            tipo_contrato=tipo
        )
        return controller.firmar_contrato(c.nro_contrato)

    c1_firmado = crear_y_firmar(0, 0, 180000.0, 10.0, 3.5, "Alquiler")
    if c1_firmado:
        contratos_firmados.append(c1_firmado)

    c2_firmado = crear_y_firmar(1, 3, 140000.0, 10.0, 3.0, "Alquiler")
    if c2_firmado:
        contratos_firmados.append(c2_firmado)

    c3_firmado = crear_y_firmar(2, 6, 120000.0, 12.0, 4.0, "Alquiler")
    if c3_firmado:
        contratos_firmados.append(c3_firmado)

    c4_firmado = crear_y_firmar(3, 1, 75000000.0, 3.0, 1.0, "Compraventa")
    if c4_firmado:
        contratos_firmados.append(c4_firmado)

    # Contratos de Alquiler Activos con Alquiler Vencido (Pendientes de Pago y con Alerta de Mora Habilitada)
    c6_firmado = crear_y_firmar(4, 2, 195000.0, 10.0, 3.0, "Alquiler")
    if c6_firmado:
        contratos_firmados.append(c6_firmado)

    c7_firmado = crear_y_firmar(7, 5, 230000.0, 10.0, 3.5, "Alquiler")
    if c7_firmado:
        contratos_firmados.append(c7_firmado)

    # Contrato solicitado (pendiente de firma)
    p_solic = propiedades_creadas[9]
    if p_solic.estado == "disponible":
        asig_solic = controller.obtener_asignacion_activa_propiedad(p_solic.id)
        if asig_solic:
            c5 = controller.solicitar_contrato(
                clientes_list[4].id, asig_solic.id_agente, p_solic.id,
                monto=160000.0, comision_porcentaje=10.0, comision_agente_porcentaje=3.0, tipo_contrato="Alquiler"
            )
            controller.agregar_clausula_contrato(
                c5.nro_contrato, "OCTAVA (SEGURO DE CAUCIÓN)",
                "El LOCATARIO deberá contratar un seguro de caución con póliza endosada a favor de la inmobiliaria."
            )

    print(" [+] Contratos generados y activados en el sistema.")

    # 6. Historial de Pagos de Inquilinos
    if c1_firmado:
        if not db.get_pago_inquilino_by_period(c1_firmado.nro_contrato, "2026-06"):
            controller.registrar_pago_inquilino(
                nro_contrato=c1_firmado.nro_contrato,
                mes="2026-06",
                monto=180000.0,
                fecha_pago=date(2026, 6, 8),
                ruta_comprobante="static/uploads/comprobantes/recibo_ejemplo_1.pdf"
            )
        if not db.get_pago_inquilino_by_period(c1_firmado.nro_contrato, "2026-07"):
            controller.registrar_pago_inquilino(
                nro_contrato=c1_firmado.nro_contrato,
                mes="2026-07",
                monto=180000.0,
                fecha_pago=date(2026, 7, 17),
                ruta_comprobante="static/uploads/comprobantes/recibo_ejemplo_2.pdf"
            )
        if not db.get_pago_inquilino_by_period(c1_firmado.nro_contrato, "2026-08"):
            controller.registrar_pago_inquilino(
                nro_contrato=c1_firmado.nro_contrato,
                mes="2026-08",
                monto=180000.0,
                fecha_pago=date(2026, 8, 9),
                ruta_comprobante="static/uploads/comprobantes/recibo_ejemplo_3.pdf"
            )

    if c2_firmado:
        if not db.get_pago_inquilino_by_period(c2_firmado.nro_contrato, "2026-07"):
            controller.registrar_pago_inquilino(
                nro_contrato=c2_firmado.nro_contrato,
                mes="2026-07",
                monto=140000.0,
                fecha_pago=date(2026, 7, 10),
            )
        if not db.get_pago_inquilino_by_period(c2_firmado.nro_contrato, "2026-08"):
            controller.registrar_pago_inquilino(
                nro_contrato=c2_firmado.nro_contrato,
                mes="2026-08",
                monto=140000.0,
                fecha_pago=date(2026, 8, 18),
            )

    if c3_firmado:
        if not db.get_pago_inquilino_by_period(c3_firmado.nro_contrato, "2026-08"):
            controller.registrar_pago_inquilino(
                nro_contrato=c3_firmado.nro_contrato,
                mes="2026-08",
                monto=120000.0,
                fecha_pago=date(2026, 8, 6),
            )

    print(" [+] Historial de pagos registrado con éxito.")

    # 7. Liquidaciones
    admin_id = agentes_pool[0].id
    controller.generar_liquidaciones_mes("2026-06", id_agente_solicitante=admin_id)
    controller.generar_liquidaciones_mes("2026-07", id_agente_solicitante=admin_id)
    controller.generar_liquidaciones_mes("2026-08", id_agente_solicitante=admin_id)

    todas_liq = [liq for liq in db.list_pagos_propietarios() if liq.estado == "pendiente"]
    if len(todas_liq) >= 2:
        controller.registrar_transferencia_propietario(
            todas_liq[0].id, fecha_pago=date(2026, 6, 15), id_agente_solicitante=admin_id
        )
        controller.registrar_transferencia_propietario(
            todas_liq[1].id, fecha_pago=date(2026, 7, 20), id_agente_solicitante=admin_id
        )

    print(" [+] Liquidaciones y transferencias a propietarios generadas.")

    # 8. Agendas de Visitas con Cupos Limitados
    if not db.list_todas_agendas_visitas():
        disponibles = [p for p in db.list_propiedades() if p.estado.lower() == "disponible"]
        if len(disponibles) >= 3:
            p1, p2, p3 = disponibles[0], disponibles[1], disponibles[2]

        ag1 = controller.crear_agenda_visita(
            id_propiedad=p1.id,
            id_agente=agentes_pool[1].id,
            fecha_hora_visita=datetime.now() + timedelta(days=1, hours=2),
            duracion_minutos=30,
            cupo_maximo=3,
        )
        controller.inscribir_visitante_a_turno(
            ag1.id, "Dr. Ramiro Varela", "3415123456", "r.varela@medicos.org",
            observaciones="Busca piso alto con cochera"
        )
        controller.inscribir_visitante_a_turno(
            ag1.id, "Cecilia Marín", "3415654321", "ceci.marin@gmail.com",
            observaciones="Mudanza prevista para fin de mes"
        )

        ag2 = controller.crear_agenda_visita(
            id_propiedad=p2.id,
            id_agente=agentes_pool[2].id,
            fecha_hora_visita=datetime.now() + timedelta(days=2, hours=4),
            duracion_minutos=45,
            cupo_maximo=2,
        )
        controller.inscribir_visitante_a_turno(
            ag2.id, "Ing. Pablo Giménez", "3415998877", "pgimenez@tech.com",
            observaciones="Pago contado efectivo con seña"
        )
        controller.inscribir_visitante_a_turno(
            ag2.id, "Lorena Bianchi", "3415887766", "lore.bianchi@hotmail.com",
            observaciones="Evaluando permuta"
        )

        ag3 = controller.crear_agenda_visita(
            id_propiedad=p3.id,
            id_agente=agentes_pool[3].id,
            fecha_hora_visita=datetime.now() + timedelta(days=4, hours=1),
            duracion_minutos=60,
            cupo_maximo=4,
        )
        controller.inscribir_visitante_a_turno(
            ag3.id, "Federico Sanz", "3415776655", "fede.sanz@gmail.com",
            observaciones="Consulta por expensas e impuestos"
        )
    # 9. Reclamos e Incidencias Estructurales
    if not db.list_reclamos():
        c_alq = [
            c for c in db.list_contratos()
            if c.tipo_contrato.lower() == "alquiler" and c.estado.lower() == "activo"
        ]
        if c_alq:
            # Reclamo 1 (Pendiente)
            controller.registrar_reclamo(
                nro_contrato=c_alq[0].nro_contrato,
                tipo_dano="Plomería / Humedad",
                descripcion=(
                    "Filtración constante en cañería de descarga del baño principal "
                    "que afecta el cielorraso inferior."
                ),
                urgencia="Alta",
                presupuesto_estimado=45000.0,
            )
            # Reclamo 2 (Informado al Dueño con presupuesto)
            r2 = controller.registrar_reclamo(
                nro_contrato=c_alq[0].nro_contrato,
                tipo_dano="Estructural / Techos / Muros",
                descripcion=(
                    "Rajadura exterior con desprendimiento parcial de revoque en balcón "
                    "con riesgo a la vereda."
                ),
                urgencia="Urgente",
                presupuesto_estimado=95000.0,
            )
            controller.actualizar_estado_reclamo(
                r2.id,
                nuevo_estado="informado_propietario",
                observaciones_resolucion=(
                    "Presupuesto de albañilería remitido al propietario para su autorización."
                ),
            )

        if len(c_alq) > 1:
            # Reclamo 3 (En Reparación)
            r3 = controller.registrar_reclamo(
                nro_contrato=c_alq[1].nro_contrato,
                tipo_dano="Electricidad",
                descripcion="Falso contacto y recalentamiento en disyuntor principal del tablero seccional.",
                urgencia="Alta",
                presupuesto_estimado=32000.0,
            )
            controller.actualizar_estado_reclamo(
                r3.id,
                nuevo_estado="en_reparacion",
                observaciones_resolucion="Electricista matriculado asignado, trabajos en ejecución.",
            )

            # Reclamo 4 (Resuelto)
            r4 = controller.registrar_reclamo(
                nro_contrato=c_alq[1].nro_contrato,
                tipo_dano="Cerrajería / Aberturas",
                descripcion="Traba trabada en cerradura de puerta blindada de acceso.",
                urgencia="Media",
                presupuesto_estimado=18000.0,
            )
            controller.actualizar_estado_reclamo(
                r4.id,
                nuevo_estado="resuelto",
                observaciones_resolucion="Cambio de cilindro y copia de llaves entregadas al inquilino.",
            )

        print(" [+] Reclamos e incidencias de prueba registrados.")

    print("\n[OK] Inyeccion masiva de datos completada exitosamente!")


if __name__ == "__main__":
    seed_large_dataset()

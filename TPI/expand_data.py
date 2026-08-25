from datetime import date
import business.controller as controller
import datos.db as db

def expand_financial_and_visit_data():
    print("Expandiendo datos de cobros, liquidaciones y visitas...")
    contratos = db.list_contratos()
    admin = db.get_agente_by_email("admin@inmogestion.com")
    
    for c in contratos:
        if c.estado == "activo" and c.tipo_contrato == "Alquiler":
            # Mes 2026-06
            if not db.get_pago_inquilino_by_period(c.nro_contrato, "2026-06"):
                try:
                    controller.registrar_pago_inquilino(
                        c.nro_contrato, "2026-06", c.monto, fecha_pago=date(2026, 6, 8)
                    )
                except Exception as e:
                    print(f"Nota: {e}")
            
            # Mes 2026-07
            if not db.get_pago_inquilino_by_period(c.nro_contrato, "2026-07"):
                try:
                    # Alternamos algunos con mora de 4 dias
                    controller.registrar_pago_inquilino(
                        c.nro_contrato, "2026-07", c.monto, fecha_pago=date(2026, 7, 14)
                    )
                except Exception as e:
                    print(f"Nota: {e}")

            # Mes 2026-08
            if not db.get_pago_inquilino_by_period(c.nro_contrato, "2026-08"):
                try:
                    controller.registrar_pago_inquilino(
                        c.nro_contrato, "2026-08", c.monto, fecha_pago=date(2026, 8, 9)
                    )
                except Exception as e:
                    print(f"Nota: {e}")

    # Generar liquidaciones para todos los meses cobrados
    if admin:
        controller.generar_liquidaciones_mes("2026-06", id_agente_solicitante=admin.id)
        controller.generar_liquidaciones_mes("2026-07", id_agente_solicitante=admin.id)
        controller.generar_liquidaciones_mes("2026-08", id_agente_solicitante=admin.id)

    print("Expansión financiera finalizada.")

if __name__ == "__main__":
    expand_financial_and_visit_data()

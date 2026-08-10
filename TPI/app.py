import os
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask

load_dotenv()

# Import DB and Controller functions
from datos.db import (
    init_db,
    get_agente_by_email,
    list_propietarios,
    list_clientes,
    list_propiedades,
)
from business.controller import (
    registrar_agente,
    registrar_propietario,
    registrar_cliente,
    registrar_propiedad,
    asignar_agente_a_propiedad,
)
from views.views import views_blueprint

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "inmogestion_premium_super_secret_key_12345"
)

# Register Blueprints
app.register_blueprint(views_blueprint)


# Inject current date into context processor
@app.context_processor
def inject_now():
    return {"date_today": datetime.now().strftime("%d/%m/%Y")}


def seed_data():
    """
    Seed initial testing data if the database is empty.
    """
    print("Seeding database with default test data...")
    # 1. Create a default Agent
    try:
        if not get_agente_by_email("admin@inmogestion.com"):
            agente = registrar_agente(
                nombre="Agente",
                apellido="Senior",
                email="admin@inmogestion.com",
                password="adminpassword",
                cuil="20-33445566-9",
                matricula="MAT-8844",
                tipo_doc="DNI",
                nro_doc="33445566",
                domicilio="Av. Pellegrini 250, Rosario",
                telefono="3415556677",
            )
            print(f"Agent created: {agente.email} (pwd: adminpassword)")
    except Exception as e:
        print(f"Error seeding Agent: {e}")

    # 2. Create a default Propietario
    try:
        if not list_propietarios():
            propietario = registrar_propietario(
                nombre="Carlos",
                apellido="Perez",
                email="carlos.perez@gmail.com",
                tipo_doc="DNI",
                nro_doc="11223344",
                domicilio="Corrientes 500, Rosario",
                telefono="3415551122",
            )
            print(
                f"Default Propietario created: {propietario.nombre_completo}"
            )
    except Exception as e:
        print(f"Error seeding Propietario: {e}")

    # 3. Create a default Cliente
    try:
        if not list_clientes():
            cliente = registrar_cliente(
                nombre="Ana",
                apellido="Rodriguez",
                email="ana.rod@gmail.com",
                tipo_doc="DNI",
                nro_doc="22334455",
                domicilio="Mitre 900, Rosario",
                telefono="3415552233",
            )
            print(f"Default Cliente created: {cliente.nombre_completo}")
    except Exception as e:
        print(f"Error seeding Cliente: {e}")

    # 4. Create a default Propiedad and assign agent
    try:
        if not list_propiedades():
            propietarios = list_propietarios()
            if propietarios:
                prop = registrar_propiedad(
                    direccion="Urquiza 1540, Rosario",
                    tipo="Alquiler",
                    zona="Centro",
                    id_propietario=propietarios[0].id,
                )
                print(f"Default Propiedad created: {prop.direccion}")

                # Assign default agent to this property
                agente = get_agente_by_email("admin@inmogestion.com")
                if agente:
                    asignar_agente_a_propiedad(
                        id_agente=agente.id,
                        id_propiedad=prop.id,
                        desde=datetime.now(),
                    )
                    print("Agent assigned to default Propiedad.")
    except Exception as e:
        print(f"Error seeding Propiedad: {e}")


if __name__ == "__main__":
    # Initialize SQLAlchemy database tables
    print("Initializing database...")
    init_db()

    # Seed data
    seed_data()

    # Run server
    print("Starting Flask web server...")
    app.run(debug=True, host="127.0.0.1", port=5000)

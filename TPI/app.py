import os
import secrets
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

# Import Database and Controller initialization
from datos.db import init_db  # noqa: E402
from seed_large_dataset import seed_large_dataset  # noqa: E402
from views.views import views_blueprint  # noqa: E402


def obtener_clave_secreta() -> str:
    """
    Lee la clave de sesión desde el entorno (SECRET_KEY o FLASK_SECRET_KEY).
    Si no está configurada se genera una aleatoria (las sesiones se pierden al reiniciar);
    nunca se usa una clave escrita en el código.
    """
    clave = os.environ.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY")
    if not clave:
        print("Aviso: SECRET_KEY no configurada; se usa una clave temporal aleatoria.")
        clave = secrets.token_hex(32)
    return clave


# Initialize Flask App
app = Flask(__name__)
app.secret_key = obtener_clave_secreta()
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB por solicitud
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Register Blueprints
app.register_blueprint(views_blueprint)


# Inject current date into context processor
@app.context_processor
def inject_now():
    return {"date_today": datetime.now().strftime("%d/%m/%Y")}


def seed_data():
    """
    Seed initial testing data if the database is empty or needs populating.
    """
    try:
        seed_large_dataset()
    except Exception as e:
        print(f"Error seeding large dataset: {e}")


if __name__ == "__main__":
    # Initialize SQLAlchemy database tables
    print("Initializing database...")
    init_db()

    # Seed rich default data
    seed_data()

    # Run server (debug solo si FLASK_DEBUG=True en el .env)
    print("Starting Flask web server...")
    modo_debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(
        debug=modo_debug,
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )

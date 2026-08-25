import os
from flask import Flask
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import Database and Controller initialization
from datos.db import init_db
from seed_large_dataset import seed_large_dataset
from views.views import views_blueprint

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "inmogestion_secret_key_2026")

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

    # Run server
    print("Starting Flask web server...")
    app.run(debug=True, host="127.0.0.1", port=5000)

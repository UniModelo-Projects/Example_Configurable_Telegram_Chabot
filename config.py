import os
from dotenv import load_dotenv

# Determinar la ruta base del proyecto ANTES de cargar el .env
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Forzar la carga del .env usando la ruta absoluta
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Config:
    """Configuración de la aplicación Flask."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    
    # En PythonAnywhere es fundamental usar rutas absolutas para SQLite
    default_db_path = os.path.join(BASE_DIR, "instance", "bot_config.db")
    if not os.path.exists(os.path.join(BASE_DIR, "instance")):
        os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
        
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{default_db_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Limpiar posibles comillas de las variables de entorno
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip().replace('"', '').replace("'", "")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip().replace('"', '').replace("'", "")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip().replace('"', '').replace("'", "")
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Determinar la ruta base del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuración de la aplicación Flask."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    
    # En PythonAnywhere es fundamental usar rutas absolutas para SQLite
    default_db_path = os.path.join(BASE_DIR, "instance", "bot_config.db")
    # Asegurar que el directorio instance existe
    if not os.path.exists(os.path.join(BASE_DIR, "instance")):
        os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
        
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{default_db_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip().replace('"', '').replace("'", "")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
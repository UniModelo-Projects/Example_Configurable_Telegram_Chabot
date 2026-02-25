import os
from dotenv import load_dotenv

load_dotenv()

# Obtener la ruta base del proyecto para rutas absolutas
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuración de la aplicación Flask."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    
    # Usar ruta absoluta para la base de datos SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'bot_config.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
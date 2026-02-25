import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración de la aplicación Flask."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///bot_config.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip().replace('"', '').replace("'", "")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
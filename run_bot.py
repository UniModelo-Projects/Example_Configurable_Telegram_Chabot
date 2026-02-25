import os
import asyncio
import logging
import sys

# Agregar el directorio raíz al path de Python
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from app import app
from bot.telegram_bot import setup_bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_bot")

def run_bot_polling():
    """Ejecuta el bot de Telegram en modo polling."""
    # Crear un nuevo loop de eventos para este proceso
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # El bot necesita el contexto de la app de Flask para SQLAlchemy
    telegram_app = setup_bot(app)
    
    if telegram_app:
        logger.info("🤖 Iniciando bot en modo polling para PythonAnywhere...")
        # run_polling() bloquea el hilo principal
        telegram_app.run_polling()
    else:
        logger.error("❌ No se pudo inicializar el bot. Verifica TELEGRAM_BOT_TOKEN en .env")

if __name__ == "__main__":
    try:
        run_bot_polling()
    except KeyboardInterrupt:
        logger.info("Bot detenido manualmente.")
    except Exception as e:
        logger.error(f"Error fatal: {e}")

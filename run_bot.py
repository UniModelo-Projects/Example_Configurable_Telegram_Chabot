import logging
from app import app
from bot.telegram_bot import setup_bot

# Configuración básica de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Ejecuta el bot de Telegram de forma independiente."""
    # El bot necesita el contexto de Flask para que las tareas en bot_data
    # o cualquier consulta a la DB funcione correctamente.
    telegram_app = setup_bot(app)
    
    if telegram_app:
        logger.info("Iniciando bot de Telegram para PythonAnywhere...")
        # run_polling() es un método bloqueante ideal para Always-on tasks.
        telegram_app.run_polling()
    else:
        logger.error("No se pudo inicializar el bot de Telegram. Verifica tu TOKEN.")

if __name__ == "__main__":
    main()

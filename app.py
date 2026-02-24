import os
import logging
import threading
import asyncio
from flask import Flask, render_template, request, redirect, url_for, jsonify

from config import Config
from models import db, BotConfig
from bot.telegram_bot import setup_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar SQLAlchemy
db.init_app(app)

# Bot de Telegram
telegram_app = None


def run_bot_polling():
    """Ejecuta el bot de Telegram en modo polling."""
    global telegram_app
    
    # Crear un nuevo loop de eventos para este hilo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    telegram_app = setup_bot(app)
    if telegram_app:
        logger.info("Iniciando bot en modo polling...")
        # run_polling maneja su propio bucle si se llama correctamente
        telegram_app.run_polling(close_loop=False)
    else:
        logger.error("No se pudo inicializar el bot de Telegram. Verifica el TOKEN.")


@app.route("/")
def index():
    """Página principal."""
    return redirect(url_for("config_view"))


@app.route("/config", methods=["GET", "POST"])
def config_view():
    """Vista de configuración del bot."""
    config = BotConfig.query.first()

    if request.method == "POST":
        name = request.form.get("name", "Grooming Bot").strip()
        use_emojis = request.form.get("use_emojis") == "on"
        greeting = request.form.get("greeting", "").strip()
        tone = request.form.get("tone", "amigable")
        topic = request.form.get("topic", "estética canina").strip()

        if not greeting:
            greeting = "¡Hola! ¿En qué puedo ayudarte?"

        if config:
            # Actualizar configuración existente
            config.name = name
            config.use_emojis = use_emojis
            config.greeting = greeting
            config.tone = tone
            config.topic = topic
        else:
            # Crear nueva configuración
            config = BotConfig(
                name=name,
                use_emojis=use_emojis,
                greeting=greeting,
                tone=tone,
                topic=topic
            )
            db.session.add(config)

        db.session.commit()
        return redirect(url_for("config_view"))

    return render_template("config.html", config=config)


def init_db():
    """Inicializa la base de datos."""
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    # Inicializar base de datos
    init_db()
    
    # Iniciar el bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()
    
    # Ejecutar Flask
    # Nota: use_reloader=False es importante cuando se usan hilos para evitar
    # que el bot se inicie dos veces.
    app.run(host="0.0.0.0", port=80, debug=False)

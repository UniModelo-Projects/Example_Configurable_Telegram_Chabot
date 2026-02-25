import os
import logging
import asyncio
from flask import Flask, render_template, request, redirect, url_for, jsonify
from telegram import Update

from config import Config
from models import db, BotConfig
from bot.telegram_bot import setup_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Asegurar que la carpeta instance existe para la DB
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Inicializar SQLAlchemy
db.init_app(app)

# Configurar el bot de Telegram (Modo Webhook)
# Nota: No iniciamos polling aquí.
telegram_app = setup_bot(app)

@app.route("/webhook", methods=["POST"])
def webhook():
    """Endpoint para recibir actualizaciones de Telegram via Webhook."""
    if request.method == "POST":
        try:
            # 1. Obtener el JSON de la petición
            json_string = request.get_json(force=True)
            
            # 2. Convertir a objeto Update de Telegram
            update = Update.de_json(json_string, telegram_app.bot)
            
            # 3. Procesar la actualización de forma asíncrona
            # PythonAnywhere corre Flask de forma sincrónica, por lo que creamos un loop temporal
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Es vital inicializar la aplicación si no lo está para que los handlers funcionen
            if not telegram_app.running:
                loop.run_until_complete(telegram_app.initialize())
            
            loop.run_until_complete(telegram_app.process_update(update))
            loop.close()
            
            return "OK", 200
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            return "Error", 500
    return "Method Not Allowed", 405


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
            config.name = name
            config.use_emojis = use_emojis
            config.greeting = greeting
            config.tone = tone
            config.topic = topic
        else:
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

# Inicializar base de datos
init_db()

if __name__ == "__main__":
    # Local development
    app.run(host="0.0.0.0", port=8080, debug=True)

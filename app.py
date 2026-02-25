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

# Inicializar SQLAlchemy
db.init_app(app)

# Bot de Telegram (se inicializará una sola vez)
telegram_app = setup_bot(app)
_bot_initialized = False

async def _init_bot_instance():
    global _bot_initialized
    if not _bot_initialized:
        await telegram_app.initialize()
        _bot_initialized = True

@app.route("/")
def index():
    """Página principal."""
    return redirect(url_for("config_view"))

@app.route("/config", methods=["GET", "POST"])
def config_view():
    """Vista de configuración del bot."""
    config = BotConfig.query.first()
    # ... (resto de la función)

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

@app.route("/webhook", methods=["POST"])
def webhook():
    """Endpoint para recibir actualizaciones de Telegram."""
    if request.method == "POST":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Asegurar inicialización
            loop.run_until_complete(_init_bot_instance())
            
            update = Update.de_json(request.get_json(force=True), telegram_app.bot)
            loop.run_until_complete(telegram_app.process_update(update))
        finally:
            loop.close()
            
        return "OK", 200
    return "Forbidden", 403

@app.route("/set_webhook")
def set_webhook():
    """Ruta para registrar el webhook en Telegram."""
    webhook_url = Config.WEBHOOK_URL
    if not webhook_url:
        return "Error: WEBHOOK_URL no está configurado en .env. Debe ser https://TU_USUARIO.pythonanywhere.com", 400
    
    # Asegurar que termina en /webhook
    actual_webhook_url = webhook_url if webhook_url.endswith("/webhook") else f"{webhook_url.rstrip('/')}/webhook"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Asegurar inicialización
        loop.run_until_complete(_init_bot_instance())
        success = loop.run_until_complete(telegram_app.bot.set_webhook(url=actual_webhook_url))
    finally:
        loop.close()

    if success:
        return f"Webhook configurado correctamente en: {actual_webhook_url}", 200
    else:
        return "Fallo al configurar el Webhook", 500

def init_db():
    """Inicializa la base de datos."""
    with app.app_context():
        db.create_all()

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)

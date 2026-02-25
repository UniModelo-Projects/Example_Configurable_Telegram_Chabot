import os
import logging
import threading
import asyncio
from flask import Flask, render_template, request, redirect, url_for, jsonify

from config import Config
from models import db, BotConfig, Service, Lead
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
        # En Linux/Unix, los hilos secundarios no pueden manejar señales (SIGINT, etc.)
        # stop_signals=None es necesario para evitar el error 'set_wakeup_fd'
        telegram_app.run_polling(stop_signals=None, close_loop=False)
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
    services = Service.query.all()

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "save_config":
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
        
        elif action == "add_service":
            service_name = request.form.get("service_name", "").strip()
            if service_name:
                existing = Service.query.filter_by(name=service_name).first()
                if not existing:
                    new_service = Service(name=service_name)
                    db.session.add(new_service)
        
        elif action == "delete_service":
            service_id = request.form.get("service_id")
            if service_id:
                service = Service.query.get(service_id)
                if service:
                    db.session.delete(service)

        db.session.commit()
        return redirect(url_for("config_view"))

    return render_template("config.html", config=config, services=services)


@app.route("/leads")
def leads_view():
    """Vista del panel de leads."""
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("leads.html", leads=leads)


def init_db():
    """Inicializa la base de datos, servicios y configuración por defecto."""
    with app.app_context():
        db.create_all()
        
        # Agregar servicios por defecto
        if Service.query.count() == 0:
            default_services = ["Pintura", "Costura", "Grooming", "Consulta"]
            for s_name in default_services:
                db.session.add(Service(name=s_name))
        
        # Agregar configuración por defecto si no existe
        if BotConfig.query.first() is None:
            default_config = BotConfig(
                name="PechuleBuddy",
                use_emojis=False,
                greeting="¡Hola amiguito, soy PechuleBuddy! ¿En qué complacerte hoy?",
                tone="divertido",
                topic="Tienda de peluches"
            )
            db.session.add(default_config)
            
        db.session.commit()
        logger.info("Base de datos v2 inicializada con valores por defecto.")

# Inicializar base de datos al importar (para que funcione con cualquier runner)
init_db()

if __name__ == "__main__":
    # Iniciar el bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()
    
    # Ejecutar Flask
    # Nota: use_reloader=False es importante cuando se usan hilos para evitar
    # que el bot se inicie dos veces.
    app.run(host="0.0.0.0", port=80, debug=False)

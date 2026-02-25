import os
import logging
from flask import Flask, render_template, request, redirect, url_for

from config import Config
from models import db, BotConfig

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

# Inicializar base de datos al arrancar
init_db()

if __name__ == "__main__":
    # Local development: Ejecutar Flask en puerto 8080 (o el que prefieras)
    # Nota: En PythonAnywhere, este bloque no se ejecuta; el servidor WSGI lo maneja.
    app.run(host="0.0.0.0", port=8080, debug=True)

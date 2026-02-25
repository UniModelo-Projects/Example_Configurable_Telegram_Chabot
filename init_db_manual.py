from app import app, db
from models import BotConfig

def init_default_config():
    with app.app_context():
        db.create_all()
        if not BotConfig.query.first():
            config = BotConfig(
                name="Grooming Bot",
                use_emojis=True,
                greeting="¡Hola! Soy tu asistente experto. ¿En qué puedo ayudarte?",
                tone="amigable",
                topic="estética canina"
            )
            db.session.add(config)
            db.session.commit()
            print("✅ Configuración inicial creada.")
        else:
            print("ℹ️ Ya existe una configuración.")

if __name__ == "__main__":
    init_default_config()

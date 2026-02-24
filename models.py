from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BotConfig(db.Model):
    """Modelo de configuración del bot."""

    __tablename__ = "bot_config"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="Grooming Bot", nullable=False)
    use_emojis = db.Column(db.Boolean, default=True, nullable=False)
    greeting = db.Column(db.String(200), default="¡Hola! ¿En qué puedo ayudarte?", nullable=False)
    tone = db.Column(db.String(50), default="amigable", nullable=False)
    topic = db.Column(db.String(200), default="estética canina", nullable=False)

    def to_dict(self):
        """Convierte el modelo a diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "use_emojis": self.use_emojis,
            "greeting": self.greeting,
            "tone": self.tone,
            "topic": self.topic,
        }
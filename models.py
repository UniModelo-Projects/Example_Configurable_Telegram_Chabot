from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BotConfig(db.Model):
    """Modelo de configuración del bot."""

    __tablename__ = "bot_config"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="PechuleBuddy", nullable=False)
    use_emojis = db.Column(db.Boolean, default=False, nullable=False)
    greeting = db.Column(db.String(200), default="¡Hola amiguito, soy PechuleBuddy! ¿En qué complacerte hoy?", nullable=False)
    tone = db.Column(db.String(50), default="divertido", nullable=False)
    topic = db.Column(db.String(200), default="Tienda de peluches", nullable=False)

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


class Service(db.Model):
    """Modelo para los servicios ofrecidos."""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Service {self.name}>"


class Lead(db.Model):
    """Modelo para los leads (clientes potenciales)."""

    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    service = db.relationship(
        "Service", 
        backref=db.backref("leads", lazy=True, cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<Lead {self.name} - {self.phone}>"
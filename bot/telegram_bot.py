import os
import logging
import re
from datetime import datetime, date
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    ContextTypes, 
    MessageHandler, 
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    PicklePersistence,
    filters
)
from telegram.request import HTTPXRequest
from icrawler.builtin import BingImageCrawler
from icrawler import ImageDownloader

# Importar configuración
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from models import db, BotConfig, Service, Lead

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estados de la conversación
NAME, PHONE, SERVICE_STATE, DATE_STATE = range(4)

import httpx

# Cliente OpenAI con soporte para proxy de PythonAnywhere
client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
    http_client=httpx.Client(
        proxy="http://proxy.server:3128" if os.environ.get("PYTHONANYWHERE_DOMAIN") else None
    )
)


class UrlDownloader(ImageDownloader):
    """Custom downloader to just capture the URL instead of downloading."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_url = None

    def download(self, task, default_ext, timeout=5, max_retry=3, **kwargs):
        self.captured_url = task['file_url']
        return


def build_system_prompt(config: BotConfig, services: list) -> str:
    """Construye el prompt del sistema basado en la configuración."""
    emoji_instruction = """SIEMPRE incluye emojis relevantes en tus respuestas.""" if config.use_emojis else "NO uses emojis."
    
    services_list = ", ".join([s.name for s in services])
    
    tone_instructions = {
        "amigable": "Sé cálido, cercano y friendly.",
        "formal": "Sé profesional y formal.",
        "divertido": "Sé divertido y con humor.",
        "profesional": "Sé experto y directo.",
        "elegante": "Sé refinado y sofisticado."
    }
    tone_instruction = tone_instructions.get(config.tone, tone_instructions["amigable"])
    
    prompt = f"""Eres {config.name}, un experto apasionado en: {config.topic}.
Tu tono es {config.tone} ({tone_instruction}).

SERVICIOS DISPONIBLES: {services_list}.

INSTRUCCIONES CRÍTICAS:
1. FOCO ABSOLUTO: Tienes terminantemente prohibido realizar cualquier tarea que no sea sobre {config.topic}.
2. AGENDAR CITA: Si el usuario quiere agendar, solicitar un servicio o pregunta por disponibilidad, infórmale que puede hacerlo presionando el botón de agendar o usando /solicitar.
3. SERVICIOS: Si el usuario pregunta qué servicios ofreces, lístalos claramente: {services_list}.
4. IMÁGENES: ÚNICAMENTE si el usuario pide "ver", "foto" o "imagen", DEBES incluir al final de tu respuesta el tag [[IMAGE: search_term]].
5. NO REPETIR SALUDO: No uses la frase "{config.greeting}" en tus respuestas normales.

{emoji_instruction}
Responde con autoridad sobre {config.topic}."""
    
    return prompt


async def search_image(query: str) -> str:
    """Busca una imagen en Bing usando icrawler y retorna el URL."""
    try:
        if not os.path.exists('tmp_icrawler'):
            os.makedirs('tmp_icrawler')
            
        crawler = BingImageCrawler(
            downloader_cls=UrlDownloader,
            downloader_threads=1,
            storage={'root_dir': 'tmp_icrawler'},
            log_level=logging.ERROR
        )
        crawler.crawl(keyword=query, max_num=1)
        url = crawler.downloader.captured_url
        return url
    except Exception as e:
        logger.error(f"Error en búsqueda de imagen icrawler: {e}")
    return None


# --- FLOW DE SOLICITUD DE SERVICIO ---

async def start_solicitud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de solicitud de servicio."""
    message = update.message if update.message else update.callback_query.message
    
    await message.reply_text(
        "¡Excelente! Vamos a registrar tu solicitud. ¿Cuál es tu nombre completo?",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Valida y guarda el nombre."""
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("Por favor, ingresa un nombre válido (mínimo 3 caracteres).")
        return NAME
    
    context.user_data["lead_name"] = name
    await update.message.reply_text(f"Mucho gusto, {name}. Ahora, por favor ingresa tu número de teléfono:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Valida y guarda el teléfono, asegurando que sea único por usuario."""
    phone = update.message.text.strip()
    # Validación simple de teléfono
    if not re.match(r'^\+?[\d\s-]{7,15}$', phone):
        await update.message.reply_text("Por favor, ingresa un número de teléfono válido (ej: +123456789 o 12345678).")
        return PHONE
    
    # Verificar si el teléfono ya existe con otro nombre
    app = context.application.bot_data.get("flask_app")
    name = context.user_data["lead_name"]
    
    with app.app_context():
        # Buscar cualquier registro previo con este teléfono
        existing_lead = Lead.query.filter_by(phone=phone).first()
        if existing_lead and existing_lead.name.strip().lower() != name.strip().lower():
            await update.message.reply_text(
                f"Lo siento, el número {phone} ya se encuentra registrado con otro nombre. "
                "Por favor, verifica tu número o contacta a soporte si crees que esto es un error."
            )
            return PHONE

    context.user_data["lead_phone"] = phone
    
    # Mostrar servicios disponibles
    app = context.application.bot_data.get("flask_app")
    with app.app_context():
        services = Service.query.all()
        if not services:
            await update.message.reply_text("Lo siento, no hay servicios configurados en este momento. Intenta más tarde.")
            return ConversationHandler.END
        
        keyboard = [[service.name] for service in services]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "¿Qué servicio necesitas?",
            reply_markup=reply_markup
        )
    return SERVICE_STATE


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Valida el servicio seleccionado."""
    service_name = update.message.text
    app = context.application.bot_data.get("flask_app")
    
    with app.app_context():
        service = Service.query.filter_by(name=service_name).first()
        if not service:
            await update.message.reply_text("Por favor, selecciona un servicio de la lista.")
            return SERVICE_STATE
        
        context.user_data["lead_service_id"] = service.id
        context.user_data["lead_service_name"] = service.name
    
    await update.message.reply_text(
        "¿Para qué fecha lo necesitas? (Usa el formato: DD/MM/AAAA, ej: 25/02/2026)",
        reply_markup=ReplyKeyboardRemove()
    )
    return DATE_STATE


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Valida la fecha usando OpenAI para lenguaje natural y guarda el Lead."""
    user_date_text = update.message.text.strip()
    today = date.today()
    
    # 1. USAR OPENAI PARA INTERPRETAR LA FECHA
    try:
        prompt = f"""Extrae la fecha del siguiente texto y devuélvela ÚNICAMENTE en formato AAAA-MM-DD. 
Si el usuario dice 'mañana', 'hoy' o usa nombres de meses, calcúlalo basándote en que hoy es {today}.
Si no puedes determinar una fecha clara, responde 'ERROR'.

Texto: "{user_date_text}"
Fecha:"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Eres un extractor de fechas preciso."},
                      {"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0
        )
        
        parsed_response = response.choices[0].message.content.strip()
        
        # Usar regex para buscar el patrón AAAA-MM-DD en cualquier parte de la respuesta
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', parsed_response)
        
        if not date_match:
            # Fallback a intento de parseo manual simple si falla la AI
            try:
                chosen_date = datetime.strptime(user_date_text, "%d/%m/%Y").date()
            except ValueError:
                await update.message.reply_text("No entendí la fecha. Por favor, intenta algo como '25 de Febrero' o 'DD/MM/AAAA':")
                return DATE_STATE
        else:
            chosen_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()

        # 2. VALIDACIONES DE NEGOCIO
        if chosen_date < today:
            await update.message.reply_text(f"La fecha ({chosen_date.strftime('%d/%m/%Y')}) ya pasó. Por favor elige una fecha futura:")
            return DATE_STATE
        
        if chosen_date.year > today.year + 1:
            await update.message.reply_text("Por favor, elige una fecha más cercana (máximo 1 año a futuro).")
            return DATE_STATE

    except Exception as e:
        logger.error(f"Error parsing date with AI: {e}")
        await update.message.reply_text("Hubo un problema procesando la fecha. Por favor usa el formato DD/MM/AAAA:")
        return DATE_STATE

    # 3. VERIFICAR DUPLICADO Y GUARDAR (Resto del código igual)
    app = context.application.bot_data.get("flask_app")
    name = context.user_data["lead_name"]
    phone = context.user_data["lead_phone"]
    service_id = context.user_data["lead_service_id"]
    service_name = context.user_data["lead_service_name"]

    with app.app_context():
        duplicate = Lead.query.filter_by(
            name=name,
            phone=phone,
            service_id=service_id,
            date=chosen_date
        ).first()

        if duplicate:
            await update.message.reply_text(
                f"Lo sentimos, ya tienes una solicitud registrada para '{service_name}' el {chosen_date.strftime('%d/%m/%Y')}. "
                "Por favor, elige otra fecha para este servicio:"
            )
            return DATE_STATE

        # Guardar Lead
        new_lead = Lead(
            name=name,
            phone=phone,
            service_id=service_id,
            date=chosen_date
        )
        db.session.add(new_lead)
        db.session.commit()

    await update.message.reply_text(
        f"¡Listo {name}! Hemos registrado tu solicitud para {service_name} el día {chosen_date.strftime('%d/%m/%Y')}. "
        "Nos pondremos en contacto contigo pronto. 😊"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la conversación."""
    await update.message.reply_text(
        "Solicitud cancelada. Si necesitas algo más, aquí estoy.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# --- MANEJO DE MENSAJES NORMALES (AI) ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes recibidos por el bot."""
    logger.info(f"DEBUG: handle_message iniciado para el mensaje: {update.message.text if update.message else 'N/A'}")
    app = context.application.bot_data.get("flask_app")
    if not app: return

    try:
        if not update.message or not update.message.text: return
        user_message = update.message.text
        chat_id = update.message.chat_id

        with app.app_context():
            config = BotConfig.query.first()
            services = Service.query.all()
            if not config: return

            # 1. MEJORAR SALUDO INICIAL
            greeting_keywords = ["hola", "buen", "buenas", "buenos", "saludos", "que tal", "qué tal", "hi", "hello"]
            user_msg_lower = user_message.lower().strip()
            
            is_greeting = any(user_msg_lower.startswith(kw) for kw in greeting_keywords) or user_message.startswith('/start')
            
            if is_greeting:
                services_text = "\n".join([f"• {s.name}" for s in services])
                welcome_msg = (
                    f"{config.greeting}\n\n"
                    f"🌟 *Nuestros servicios son:*\n{services_text}\n\n"
                    f"Puedes usar el comando /solicitar para agendar una cita directamente o simplemente preguntarme lo que necesites."
                )
                
                keyboard = [[InlineKeyboardButton("📝 Agendar Servicio", callback_data="start_flow")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=welcome_msg, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return

            # 2. DETECCIÓN DE INTENCIÓN DE SERVICIO
            service_intents = ["cita", "turno", "agendar", "quiero", "necesito", "precio", "costo", "solicitar", "reserva", "servicio", "haces", "ofrecen"]
            has_service_intent = any(kw in user_msg_lower for kw in service_intents)
            # También checar si menciona algún nombre de servicio
            mentions_service = any(s.name.lower() in user_msg_lower for s in services)

            # 3. PROCESAR CON OPENAI
            try:
                system_prompt = build_system_prompt(config, services)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                bot_response = response.choices[0].message.content
            except Exception as ai_err:
                logger.error(f"Error de OpenAI: {ai_err}")
                bot_response = "¡Hola! Estoy teniendo problemas para conectar con mi cerebro de IA (OpenAI está bloqueado en el plan gratuito de PythonAnywhere). Pero puedo ayudarte a agendar si usas el comando /solicitar o presionas el botón de abajo."

            # Detectar intención de imagen
            intent_pattern = r'\b(ver|foto|imagen|imágenes|fotos|muéstrame|muestrame|enséñame|ensename|pásame|pasame|show|image|picture|photo)\b'
            has_image_intent = bool(re.search(intent_pattern, user_message.lower()))
            
            image_tag_match = re.search(r'\[\[IMAGE:\s*(.*?)\]\]', bot_response, re.IGNORECASE)
            clean_response = re.sub(r'\[\[IMAGE:.*?\]\]', '', bot_response, flags=re.IGNORECASE).strip()

            reply_markup = None
            if has_service_intent or mentions_service:
                keyboard = [[InlineKeyboardButton("📝 Agendar ahora", callback_data="start_flow")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

            if image_tag_match and has_image_intent:
                search_query = image_tag_match.group(1)
                if clean_response:
                    await context.bot.send_message(chat_id=chat_id, text=clean_response, reply_markup=reply_markup)
                
                image_url = await search_image(search_query)
                if image_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=image_url)
                    except Exception:
                        await context.bot.send_message(chat_id=chat_id, text="No pude enviar la imagen. 🍔")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="No encontré una foto de eso. 🍔")
            else:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=clean_response or bot_response,
                    reply_markup=reply_markup
                )

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los clics en botones inline."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_flow":
        return await start_solicitud(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(f"DEBUG: Exception while handling an update: {context.error}")

def setup_bot(app=None):
    """Configura y retorna la aplicación del bot."""
    token = Config.TELEGRAM_BOT_TOKEN
    if not token: return None

    # Configurar proxy para PythonAnywhere si estamos en su dominio
    proxy_url = "http://proxy.server:3128" if os.environ.get("PYTHONANYWHERE_DOMAIN") else None
    request_obj = HTTPXRequest(proxy_url=proxy_url) if proxy_url else None

    # Agregar persistencia para que el estado de la conversación no se pierda en PythonAnywhere
    persistence = PicklePersistence(filepath="bot_persistence.pickle")

    builder = Application.builder().token(token).persistence(persistence)
    if request_obj:
        builder = builder.request(request_obj)
        
    application = builder.build()
    
    if app: application.bot_data["flask_app"] = app
    
    # Agregar handler de errores
    application.add_error_handler(error_handler)
    
    # Handler para la solicitud de servicio (ConversationHandler)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("solicitar", start_solicitud),
            CallbackQueryHandler(callback_handler, pattern="^start_flow$")
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SERVICE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            DATE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Handler normal para mensajes AI
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application

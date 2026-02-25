import os
import logging
import re
from datetime import datetime, date, timedelta
import asyncio
import httpx
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    ContextTypes, 
    MessageHandler, 
    CommandHandler,
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

# Definición de estados manuales
STATE_NONE = None
STATE_NAME = "NAME"
STATE_PHONE = "PHONE"
STATE_SERVICE = "SERVICE"
STATE_DATE = "DATE"

# Cliente OpenAI con soporte para proxy de PythonAnywhere
client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
    http_client=httpx.Client(
        proxy="http://proxy.server:3128" if os.environ.get("PYTHONANYWHERE_DOMAIN") else None
    )
)

class UrlDownloader(ImageDownloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_url = None

    def download(self, task, default_ext, timeout=5, max_retry=3, **kwargs):
        self.captured_url = task['file_url']
        return

def build_system_prompt(config: BotConfig, services: list) -> str:
    emoji_instruction = "SIEMPRE incluye emojis relevantes." if config.use_emojis else "NO uses emojis."
    services_list = ", ".join([s.name for s in services])
    tone_instructions = {
        "amigable": "Sé cálido y cercano.",
        "formal": "Sé profesional y formal.",
        "divertido": "Sé divertido y con humor.",
        "profesional": "Sé experto y directo.",
        "elegante": "Sé refinado y sofisticado."
    }
    tone_instruction = tone_instructions.get(config.tone, tone_instructions["amigable"])
    
    return f"""Eres {config.name}, experto en: {config.topic}. Tono: {config.tone} ({tone_instruction}).
SERVICIOS: {services_list}.
INSTRUCCIONES:
1. Si quieren agendar, diles que usen el botón o /solicitar.
2. Si piden ver fotos, usa [[IMAGE: term]].
3. No repitas el saludo inicial.
{emoji_instruction}"""

def parse_spanish_date(text: str) -> date:
    """Procesador manual de fechas en español (no requiere IA)."""
    text = text.lower().strip()
    today = date.today()
    
    if "hoy" in text: return today
    if "pasado mañana" in text: return today + timedelta(days=2)
    if "mañana" in text: return today + timedelta(days=1)
    
    # Extraer el día (número de 1 o 2 dígitos)
    day_match = re.search(r'\b(\d{1,2})\b', text)
    # Lista de meses para búsqueda
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    month_match = re.search(r'(' + '|'.join(months) + r')', text)
    
    if day_match:
        day = int(day_match.group(1))
        # Caso: "26 de febrero" o "febrero 26"
        if month_match:
            month_idx = months.index(month_match.group(1)) + 1
            year = today.year
            try:
                res = date(year, month_idx, day)
                if res < today: res = date(year + 1, month_idx, day)
                return res
            except: return None
        # Caso: "el 26" (asumir mes actual o siguiente)
        else:
            try:
                res = date(today.year, today.month, day)
                if res < today:
                    if today.month == 12: res = date(today.year + 1, 1, day)
                    else: res = date(today.year, today.month + 1, day)
                return res
            except: return None
    return None

async def search_image(query: str) -> str:
    try:
        if not os.path.exists('tmp_icrawler'): os.makedirs('tmp_icrawler')
        crawler = BingImageCrawler(downloader_cls=UrlDownloader, downloader_threads=1, storage={'root_dir': 'tmp_icrawler'}, log_level=logging.ERROR)
        crawler.crawl(keyword=query, max_num=1)
        return crawler.downloader.captured_url
    except: return None

# --- LÓGICA DE REGISTRO MANUAL ---

async def start_solicitud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = STATE_NAME
    target = update.message if update.message else update.callback_query.message
    await target.reply_text("¡Excelente! Vamos a registrar tu solicitud. ¿Cuál es tu nombre completo?", reply_markup=ReplyKeyboardRemove())
    return

async def process_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
    global _flask_app
    text = update.message.text.strip()
    
    if state == STATE_NAME:
        if len(text) < 3:
            await update.message.reply_text("Por favor, ingresa un nombre válido (mínimo 3 caracteres).")
            return
        context.user_data["lead_name"] = text
        context.user_data["state"] = STATE_PHONE
        await update.message.reply_text(f"Mucho gusto, {text}. Ahora, por favor ingresa tu número de teléfono:")
        
    elif state == STATE_PHONE:
        if not re.match(r'^\+?[\d\s-]{7,15}$', text):
            await update.message.reply_text("Por favor, ingresa un teléfono válido.")
            return
        
        name = context.user_data["lead_name"]
        with _flask_app.app_context():
            existing = Lead.query.filter_by(phone=text).first()
            if existing and existing.name.strip().lower() != name.strip().lower():
                await update.message.reply_text(f"El número {text} ya está registrado con otro nombre. Verifica tu número:")
                return

        context.user_data["lead_phone"] = text
        context.user_data["state"] = STATE_SERVICE
        
        with _flask_app.app_context():
            services = Service.query.all()
            keyboard = [[s.name] for s in services]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("¿Qué servicio necesitas?", reply_markup=reply_markup)

    elif state == STATE_SERVICE:
        with _flask_app.app_context():
            service = Service.query.filter_by(name=text).first()
            if not service:
                await update.message.reply_text("Selecciona un servicio de la lista.")
                return
            context.user_data["lead_service_id"] = service.id
            context.user_data["lead_service_name"] = service.name
        
        context.user_data["state"] = STATE_DATE
        await update.message.reply_text("¿Para qué fecha? (ej: mañana, 25 de febrero)", reply_markup=ReplyKeyboardRemove())

    elif state == STATE_DATE:
        today = date.today()
        chosen_date = None
        
        # 1. Intentar localmente primero (Plan Gratuito / Eficiencia)
        chosen_date = parse_spanish_date(text)
        
        # 2. Si falló y no estamos en local, intentar con IA (Solo si el plan es de pago)
        if not chosen_date:
            try:
                prompt = f"Extrae la fecha en formato AAAA-MM-DD del texto: '{text}'. Hoy es {today}. Si no hay fecha responde ERROR."
                response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"user", "content":prompt}], max_tokens=20, temperature=0)
                parsed = response.choices[0].message.content.strip()
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', parsed)
                if date_match:
                    chosen_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
            except:
                pass # Falló IA por plan gratuito, ya intentamos local

        # 3. Fallback final: Formato estricto DD/MM/AAAA
        if not chosen_date:
            try:
                chosen_date = datetime.strptime(text, "%d/%m/%Y").date()
            except:
                await update.message.reply_text("No entendí la fecha. Prueba con 'mañana', '26 de febrero' o '26/02/2026':")
                return

        # 4. Validar y Guardar
        if chosen_date < today:
            await update.message.reply_text(f"La fecha {chosen_date.strftime('%d/%m/%Y')} ya pasó. Elige una futura:")
            return

            # Guardar
            name = context.user_data["lead_name"]
            phone = context.user_data["lead_phone"]
            sid = context.user_data["lead_service_id"]
            
            with _flask_app.app_context():
                dup = Lead.query.filter_by(name=name, phone=phone, service_id=sid, date=chosen_date).first()
                if dup:
                    await update.message.reply_text("Ya tienes ese servicio agendado para ese día. Elige otra fecha:")
                    return
                db.session.add(Lead(name=name, phone=phone, service_id=sid, date=chosen_date))
                db.session.commit()

            await update.message.reply_text(f"¡Listo {name}! Agendado para el {chosen_date.strftime('%d/%m/%Y')}. 😊")
            context.user_data["state"] = STATE_NONE
        except Exception as e:
            logger.error(f"Error en fecha: {e}")
            await update.message.reply_text("Hubo un error. Intenta de nuevo la fecha:")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = STATE_NONE
    await update.message.reply_text("Solicitud cancelada.", reply_markup=ReplyKeyboardRemove())

# --- MANEJO DE MENSAJES (IA + MACHINE) ---

_flask_app = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _flask_app
    state = context.user_data.get("state")
    
    # Si hay un estado activo, procesar como parte del registro
    if state:
        await process_registration(update, context, state)
        return

    # Si no hay estado, procesar como IA normal
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    with _flask_app.app_context():
        config = BotConfig.query.first()
        services = Service.query.all()
        
        greeting_keywords = ["hola", "buen", "buenas", "hi", "hello"]
        if any(user_message.lower().startswith(kw) for kw in greeting_keywords):
            services_text = "\n".join([f"• {s.name}" for s in services])
            welcome_msg = f"{config.greeting}\n\n🌟 *Servicios:*\n{services_text}\n\nUsa /solicitar para agendar."
            keyboard = [[InlineKeyboardButton("📝 Agendar Servicio", callback_data="start_flow")]]
            await context.bot.send_message(chat_id=chat_id, text=welcome_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # IA
        try:
            prompt = build_system_prompt(config, services)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"system","content":prompt},{"role":"user","content":user_message}], max_tokens=300, temperature=0.3)
            bot_response = response.choices[0].message.content
        except:
            bot_response = "Tengo problemas con mi IA, pero puedo ayudarte a agendar con /solicitar."

        # Botón dinámico
        reply_markup = None
        service_intents = ["cita", "turno", "agendar", "quiero", "necesito", "precio", "costo", "servicio"]
        if any(kw in user_message.lower() for kw in service_intents):
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📝 Agendar ahora", callback_data="start_flow")]])

        # Imagen
        image_tag_match = re.search(r'\[\[IMAGE:\s*(.*?)\]\]', bot_response, re.IGNORECASE)
        clean_response = re.sub(r'\[\[IMAGE:.*?\]\]', '', bot_response, flags=re.IGNORECASE).strip()

        if image_tag_match:
            if clean_response: await context.bot.send_message(chat_id=chat_id, text=clean_response, reply_markup=reply_markup)
            url = await search_image(image_tag_match.group(1))
            if url: await context.bot.send_photo(chat_id=chat_id, photo=url)
        else:
            await context.bot.send_message(chat_id=chat_id, text=clean_response or bot_response, reply_markup=reply_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_flow":
        await start_solicitud(update, context)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"DEBUG Error: {context.error}")

def setup_bot(app=None):
    global _flask_app
    token = Config.TELEGRAM_BOT_TOKEN
    if not token: return None
    if app: _flask_app = app

    proxy_url = "http://proxy.server:3128" if os.environ.get("PYTHONANYWHERE_DOMAIN") else None
    request_obj = HTTPXRequest(proxy_url=proxy_url) if proxy_url else None
    persistence = PicklePersistence(filepath="bot_persistence.pickle")

    builder = Application.builder().token(token).persistence(persistence)
    if request_obj: builder = builder.request(request_obj)
    application = builder.build()
    
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("solicitar", start_solicitud))
    application.add_handler(CommandHandler("cancelar", cancel))
    application.add_handler(CallbackQueryHandler(callback_handler, pattern="^start_flow$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application

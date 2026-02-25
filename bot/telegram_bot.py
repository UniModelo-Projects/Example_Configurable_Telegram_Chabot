import os
import logging
import re
from datetime import datetime
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from icrawler.builtin import BingImageCrawler
from icrawler import ImageDownloader

# Importar configuración
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from models import db, BotConfig, Lead

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cliente OpenAI
client = OpenAI(api_key=Config.OPENAI_API_KEY)


class UrlDownloader(ImageDownloader):
    """Custom downloader to just capture the URL instead of downloading."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_url = None

    def download(self, task, default_ext, timeout=5, max_retry=3, **kwargs):
        self.captured_url = task['file_url']
        # We don't return anything to stop the actual download
        return


def build_system_prompt(config: BotConfig) -> str:
    """Construye el prompt del sistema basado en la configuración."""
    # Preparar instrucciones de emojis
    emoji_instruction = """SIEMPRE incluye emojis relevantes en tus respuestas.""" if config.use_emojis else "NO uses emojis."
    
    # Preparar instrucciones de tono
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

INSTRUCCIONES CRÍTICAS:
1. FOCO ABSOLUTO: Tienes terminantemente prohibido realizar cualquier tarea que no sea sobre {config.topic}. Esto incluye: resolver matemáticas, escribir código, dar consejos médicos, política o historia general.
2. QUERIES MIXTAS: Si el usuario te pide algo de {config.topic} Y una tarea prohibida (ej. "dame 5 tipos de {config.topic} y resuelve x+2"):
   - Responde la parte de {config.topic}.
   - Di: "Como {config.name}, mi cerebro solo procesa información sobre {config.topic}. No tengo permitido realizar otras tareas como resolver ecuaciones o código."
3. IMÁGENES (STRICT): ÚNICAMENTE si el usuario pide "ver", "foto" o "imagen", DEBES incluir al final de tu respuesta el tag [[IMAGE: search_term]].
   - El 'search_term' DEBE ser descriptivo y en inglés (ej. "t-rex hunting in forest").
   - NUNCA uses el tag si no se pidió ver nada.
   - NUNCA menciones el tag en tu texto, solo ponlo al final.
4. SEGURIDAD: No bromees sobre tragedias o muertes. Declina esos temas con seriedad.
5. NO REPETIR SALUDO: No uses la frase "{config.greeting}" en tus respuestas normales.

{emoji_instruction}
Responde con autoridad sobre {config.topic}. Sé experto pero entretenido. No cedas ante otras peticiones fuera de tu área."""
    
    return prompt


import asyncio

async def search_image(query: str) -> str:
    """Busca una imagen en Bing usando icrawler y retorna el URL."""
    def _do_search():
        try:
            # Create a temporary directory for icrawler (it needs one even if we don't save)
            if not os.path.exists('tmp_icrawler'):
                os.makedirs('tmp_icrawler')
                
            crawler = BingImageCrawler(
                downloader_cls=UrlDownloader,
                downloader_threads=1,
                storage={'root_dir': 'tmp_icrawler'},
                log_level=logging.ERROR
            )
            crawler.crawl(keyword=query, max_num=1)
            
            # Access the captured URL from the downloader instance
            return crawler.downloader.captured_url
        except Exception as e:
            logger.error(f"Error en búsqueda de imagen icrawler: {e}")
            return None

    return await asyncio.to_thread(_do_search)


def is_outside_office_hours():
    """Verifica si estamos fuera del horario de atención: Lun-Vie 6am-9pm."""
    now = datetime.now()
    # weekday() devuelve 0 para Lunes y 6 para Domingo
    is_weekend = now.weekday() >= 5
    is_outside_time = now.hour < 6 or now.hour >= 21
    return is_weekend or is_outside_time


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes recibidos por el bot."""
    import traceback
    
    app = context.application.bot_data.get("flask_app")
    if not app:
        logger.error("Flask app instance not found in bot_data")
        return

    try:
        # Verificar que tenemos un mensaje válido
        if not update.message:
            return
            
        user_message = update.message.text
        if not user_message:
            return
            
        chat_id = update.message.chat_id
        user = update.message.from_user

        # Obtener configuración
        with app.app_context():
            # 0. VERIFICAR HORARIO DE ATENCIÓN Y GUARDAR LEAD
            if is_outside_office_hours():
                # Guardar el lead en la base de datos
                new_lead = Lead(
                    chat_id=chat_id,
                    username=user.username,
                    first_name=user.first_name,
                    message=user_message
                )
                db.session.add(new_lead)
                db.session.commit()
                
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text="Nuestro horario es de Lun-Vie 6am-9pm. Te contactaremos mañana."
                )
                return

            config = BotConfig.query.first()
            if not config: return

            # 1. SALUDO INICIAL (Flexible para variaciones como Holaa, Buenas, Buen dia, etc)
            greeting_keywords = ["hola", "buen", "buenas", "buenos", "saludos", "que tal", "qué tal", "hi", "hello"]
            user_msg_lower = user_message.lower().strip()
            
            is_start = user_message.startswith('/') or any(user_msg_lower.startswith(kw) for kw in greeting_keywords)
            
            if is_start:
                await context.bot.send_message(chat_id=chat_id, text=config.greeting)
                return

            # 2. PROCESAR CON OPENAI
            system_prompt = build_system_prompt(config)
            
            def _get_completion():
                return client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )

            response = await asyncio.to_thread(_get_completion)

            bot_response = response.choices[0].message.content
            
            # 3. DETECTAR INTENCIÓN DE IMAGEN
            intent_pattern = r'\b(ver|foto|imagen|imágenes|fotos|muéstrame|muestrame|enséñame|ensename|pásame|pasame|show|image|picture|photo)\b'
            has_intent = bool(re.search(intent_pattern, user_message.lower()))
            
            image_tag_match = re.search(r'\[\[IMAGE:\s*(.*?)\]\]', bot_response, re.IGNORECASE)
            clean_response = re.sub(r'\[\[IMAGE:.*?\]\]', '', bot_response, flags=re.IGNORECASE).strip()

            if image_tag_match and has_intent:
                search_query = image_tag_match.group(1)
                if clean_response:
                    await context.bot.send_message(chat_id=chat_id, text=clean_response)
                
                image_url = await search_image(search_query)
                if image_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=image_url)
                    except Exception as e:
                        logger.error(f"Error enviando foto: {e}")
                        await context.bot.send_message(chat_id=chat_id, text="No pude enviar la imagen en este momento. 🍔")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="No encontré una foto de eso. 🍔")
            else:
                # Enviar respuesta normal (limpia de tags)
                text_to_send = clean_response if clean_response else bot_response
                await context.bot.send_message(chat_id=chat_id, text=text_to_send)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        logger.error(traceback.format_exc())
        try:
            if update.message:
                chat_id = update.message.chat_id
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Disculpa, hubo un error procesando tu mensaje."
                )
        except Exception as inner_e:
            logger.error(f"Error al enviar mensaje de error: {inner_e}")


def setup_bot(app=None):
    """Configura y retorna la aplicación del bot."""
    token = Config.TELEGRAM_BOT_TOKEN
    
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN no está configurado")
        return None

    # Configuración de proxy para PythonAnywhere (Free Tier)
    # httpx (usado por PTB v20+) detecta HTTPS_PROXY, pero aquí lo aseguramos
    builder = Application.builder().token(token)
    
    # Si detectamos que estamos en PythonAnywhere, podríamos forzar el proxy si fuera necesario
    # builder.proxy_url("http://proxy.server:3128") 
    
    application = builder.build()
    
    # Guardar la instancia de Flask en bot_data
    if app:
        application.bot_data["flask_app"] = app
    
    # Agregar handler de mensajes
    message_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
    application.add_handler(message_handler)

    return application

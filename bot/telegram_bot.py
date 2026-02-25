import os
import logging
import re
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from icrawler.builtin import BingImageCrawler
from icrawler import ImageDownloader

# Importar configuración
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from models import db, BotConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# El cliente se inicializará dentro de las funciones para asegurar que use la Config actualizada
def get_openai_client():
    return OpenAI(api_key=Config.OPENAI_API_KEY)


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

ESPECIALIDADES:
- COMPRA: Gestiona pedidos y guía en la compra de productos de {config.topic}.
- COTIZACIÓN: Proporciona presupuestos y precios para servicios de {config.topic}.
- INVENTARIO: Informa sobre stock y disponibilidad de {config.topic}.

INSTRUCCIONES CRÍTICAS:
1. FOCO ABSOLUTO: Prohibido hablar de temas ajenos a {config.topic}.
2. INTENCIONES: Sé proactivo en Compras, Cotizaciones e Inventario.
3. IMÁGENES (STRICT): ÚNICAMENTE si el usuario pide "ver", "foto" o "imagen", DEBES incluir al final de tu respuesta el tag [[IMAGE: search_term]]. El 'search_term' DEBE ser descriptivo y en inglés.
4. NO REPETIR SALUDO: No uses la frase "{config.greeting}" en tus respuestas normales.

{emoji_instruction}
Responde con autoridad sobre {config.topic}. Sé experto pero entretenido."""
    
    return prompt


async def search_image(query: str) -> str:
    """Busca una imagen en Bing usando icrawler y retorna el URL."""
    try:
        # Usar ruta absoluta para el directorio temporal
        tmp_dir = os.path.join(Config.BASE_DIR if hasattr(Config, 'BASE_DIR') else os.getcwd(), 'tmp_icrawler')
        
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
            
        crawler = BingImageCrawler(
            downloader_cls=UrlDownloader,
            downloader_threads=1,
            storage={'root_dir': tmp_dir},
            log_level=logging.ERROR
        )
        crawler.crawl(keyword=query, max_num=1)
        
        # Access the captured URL from the downloader instance
        url = crawler.downloader.captured_url
        return url
    except Exception as e:
        logger.error(f"Error en búsqueda de imagen icrawler: {e}")
    return None


async def detect_intent(user_message: str, config: BotConfig) -> str:
    """Clasifica la intención del usuario usando OpenAI."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un clasificador de intenciones experto para un bot de {config.topic}. Clasifica el mensaje del usuario en UNA de estas categorías: 'compra', 'cotizacion', 'inventario', 'consulta'. Responde SOLO con la palabra de la categoría."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=10,
            temperature=0
        )
        intent = response.choices[0].message.content.lower().strip()
        # Limpiar posibles respuestas ruidosas
        for valid_intent in ['compra', 'cotizacion', 'inventario', 'consulta']:
            if valid_intent in intent:
                return valid_intent
        return "consulta"
    except Exception as e:
        logger.error(f"Error detectando intención: {e}")
        return "consulta"


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
        user_msg_lower = user_message.lower().strip()

        # Obtener configuración
        with app.app_context():
            config = BotConfig.query.first()
            if not config: return

            # Teclado de opciones
            keyboard = [
                ['🛒 Compra', '💰 Cotización'],
                ['📦 Inventario', '❓ Consulta General']
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

            # 1. SALUDO INICIAL (Flexible para variaciones)
            greeting_keywords = ["hola", "buen", "buenas", "buenos", "saludos", "que tal", "qué tal", "hi", "hello"]
            is_start = user_message.startswith('/') or any(user_msg_lower.startswith(kw) for kw in greeting_keywords)
            
            if is_start:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"{config.greeting}\n\nSoy experto en {config.topic}. ¿En qué puedo ayudarte hoy?",
                    reply_markup=reply_markup
                )
                return

            # 2. DETECTAR INTENCIÓN
            intent = await detect_intent(user_message, config)
            logger.info(f"Intención detectada: {intent}")

            # 3. PROCESAR SEGÚN INTENCIÓN (Flujos específicos)
            intent_context = ""
            if "compra" in user_msg_lower or intent == "compra":
                intent_context = f"El usuario tiene intención de COMPRA. Proporciona opciones de compra relacionadas con {config.topic}."
            elif "cotiza" in user_msg_lower or intent == "cotizacion":
                intent_context = f"El usuario pide una COTIZACIÓN. Ofrece estimaciones o solicita detalles para cotizar servicios de {config.topic}."
            elif "inventario" in user_msg_lower or intent == "inventario":
                intent_context = f"El usuario consulta el INVENTARIO. Informa sobre la disponibilidad de productos o stock de {config.topic}."
            
            # 4. GENERAR RESPUESTA CON OPENAI
            system_prompt = build_system_prompt(config)
            if intent_context:
                system_prompt += f"\n\nCONTEXTO ACTUAL: {intent_context}"
            
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=400,
                temperature=0.3
            )

            bot_response = response.choices[0].message.content
            
            # 5. DETECTAR INTENCIÓN DE IMAGEN
            intent_pattern = r'\b(ver|foto|imagen|imágenes|fotos|muéstrame|muestrame|enséñame|ensename|pásame|pasame|show|image|picture|photo)\b'
            has_intent = bool(re.search(intent_pattern, user_message.lower()))
            
            image_tag_match = re.search(r'\[\[IMAGE:\s*(.*?)\]\]', bot_response, re.IGNORECASE)
            clean_response = re.sub(r'\[\[IMAGE:.*?\]\]', '', bot_response, flags=re.IGNORECASE).strip()

            if image_tag_match and has_intent:
                search_query = image_tag_match.group(1)
                if clean_response:
                    await context.bot.send_message(chat_id=chat_id, text=clean_response, reply_markup=reply_markup)
                
                image_url = await search_image(search_query)
                if image_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=image_url, reply_markup=reply_markup)
                    except Exception as e:
                        logger.error(f"Error enviando foto: {e}")
                        await context.bot.send_message(chat_id=chat_id, text="No pude enviar la imagen en este momento. 🍔", reply_markup=reply_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text="No encontré una foto de eso. 🍔", reply_markup=reply_markup)
            else:
                # Enviar respuesta normal (limpia de tags)
                text_to_send = clean_response if clean_response else bot_response
                await context.bot.send_message(chat_id=chat_id, text=text_to_send, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        logger.error(traceback.format_exc())
        try:
            if update.message:
                chat_id = update.message.chat_id
                # Mostrar el error real para diagnosticar
                error_type = type(e).__name__
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Error ({error_type}): {str(e)}"
                )
        except Exception as inner_e:
            logger.error(f"Error al enviar mensaje de error: {inner_e}")


def setup_bot(app=None):
    """Configura y retorna la aplicación del bot."""
    token = Config.TELEGRAM_BOT_TOKEN
    
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN no está configurado")
        return None

    application = Application.builder().token(token).build()
    
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

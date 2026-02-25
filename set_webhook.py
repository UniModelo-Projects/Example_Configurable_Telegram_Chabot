import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def set_webhook():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    # Tu URL en PythonAnywhere: https://tusuario.pythonanywhere.com/webhook
    webhook_url = input("Ingresa la URL pública de tu webhook (ej: https://tusuario.pythonanywhere.com/webhook): ")
    
    if not token or not webhook_url:
        print("Error: TOKEN o URL faltantes.")
        return

    bot = Bot(token)
    success = await bot.set_webhook(webhook_url)
    
    if success:
        print(f"✅ Webhook configurado correctamente en: {webhook_url}")
    else:
        print("❌ Error al configurar el webhook.")

if __name__ == "__main__":
    asyncio.run(set_webhook())

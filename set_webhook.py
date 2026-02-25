import requests
import sys
import os

# Asegurar que podemos importar Config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

def set_webhook():
    token = Config.TELEGRAM_BOT_TOKEN
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN no encontrado en .env o config.")
        return

    # Preguntar por el usuario de PythonAnywhere si no está en Config
    username = input("Introduce tu nombre de usuario de PythonAnywhere: ").strip()
    
    # La URL debe ser HTTPS y apuntar al endpoint que creamos en app.py
    webhook_url = f"https://{username}.pythonanywhere.com/webhook"
    
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    print(f"Intentando configurar webhook en: {webhook_url}")
    
    response = requests.post(api_url, data={"url": webhook_url})
    result = response.json()
    
    if result.get("ok"):
        print("✅ ¡Éxito! El webhook ha sido configurado correctamente.")
    else:
        print("❌ Error configurando el webhook:")
        print(result.get("description"))

if __name__ == "__main__":
    set_webhook()

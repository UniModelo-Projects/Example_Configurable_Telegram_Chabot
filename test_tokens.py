import os
import asyncio
from telegram import Bot
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

async def test_tokens():
    print("--- Probando Tokens ---")
    
    # Telegram
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    try:
        bot = Bot(token=tg_token)
        me = await bot.get_me()
        print(f"✅ Telegram: Conectado como @{me.username}")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

    # OpenAI
    oa_key = os.environ.get("OPENAI_API_KEY")
    try:
        client = OpenAI(api_key=oa_key)
        client.models.list()
        print("✅ OpenAI: Llave válida")
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tokens())

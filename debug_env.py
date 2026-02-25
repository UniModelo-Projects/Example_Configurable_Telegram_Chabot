import os
from dotenv import load_dotenv

# Forzar la recarga del archivo .env
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        print("--- Contenido detectado en .env (resumido) ---")
        for line in f:
            if 'OPENAI' in line:
                key = line.split('=')[-1].strip().replace('"', '').replace("'", "")
                print(f"Llave configurada termina en: ...{key[-4:]}")

load_dotenv(override=True)
env_key = os.environ.get("OPENAI_API_KEY", "")
if env_key:
    print(f"Llave en memoria termina en: ...{env_key[-4:]}")
else:
    print("No se encontró OPENAI_API_KEY en el entorno.")

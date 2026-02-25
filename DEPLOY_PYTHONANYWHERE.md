# 🚀 Guía de Despliegue en PythonAnywhere (Free Tier)

Esta guía detalla los pasos para desplegar el **Telegram Configurable Bot** utilizando **Webhooks**, que es el método más estable para el plan gratuito de PythonAnywhere.

## 1. Preparación en PythonAnywhere

1. Abre una **Bash Console** y clona tu repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   cd TU_REPOSITORIO
   ```

2. Crea el entorno virtual e instala las dependencias:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 venv
   pip install -r requirements.txt
   ```

## 2. Configuración de Variables de Entorno

Crea el archivo `.env` en la raíz del proyecto:
```bash
nano .env
```

Pega el siguiente contenido (reemplaza con tus datos reales):
```env
TELEGRAM_BOT_TOKEN=tu_token_de_bot
OPENAI_API_KEY=tu_api_key_de_openai
SECRET_KEY=una_clave_segura_aleatoria
WEBHOOK_URL=https://TU_USUARIO.pythonanywhere.com
```
*(Presiona `Ctrl+O`, `Enter` y `Ctrl+X` para guardar y salir)*.

## 3. Configuración de la Web App

1. Ve a la pestaña **Web** en el panel de PythonAnywhere.
2. Haz clic en **Add a new web app**.
3. Elige **Manual Configuration** y selecciona **Python 3.10**.
4. En la sección **Code**:
   - **Source code:** `/home/TU_USUARIO/TU_REPOSITORIO`
   - **Working directory:** `/home/TU_USUARIO/TU_REPOSITORIO`
5. En la sección **Virtualenv**:
   - Ruta: `/home/TU_USUARIO/.virtualenvs/venv`
6. Edita el **WSGI configuration file** (enlace en la sección Code) y reemplaza todo por:
   ```python
   import os
   import sys

   path = '/home/TU_USUARIO/TU_REPOSITORIO'
   if path not in sys.path:
       sys.path.append(path)

   from wsgi import application
   ```

## 4. Activación del Webhook (PASO CRÍTICO)

Una vez configurado todo, haz clic en el botón verde **Reload** en la pestaña Web. Luego, para vincular el bot con Telegram, visita la siguiente URL en tu navegador:

👉 `https://TU_USUARIO.pythonanywhere.com/set_webhook`

Si ves el mensaje *"Webhook configurado correctamente"*, tu bot ya está listo y escuchando mensajes en Telegram.

## 📝 Notas importantes para el Free Tier

- **Whitelist:** PythonAnywhere permite conexiones a Telegram y OpenAI en el plan gratuito sin problemas.
- **Mantenimiento:** Las cuentas gratuitas requieren que entres al panel de control una vez cada 3 meses y hagas clic en el botón para extender la vida de la Web App.
- **Sin Consolas:** Con este método de Webhook, **no necesitas** dejar ninguna consola abierta. El bot responde automáticamente cuando recibe un mensaje.
- **Logs:** Si algo no funciona, revisa el **Error Log** en la pestaña Web para diagnosticar el problema.

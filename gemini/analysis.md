# Análisis del Proyecto: Example Configurable Telegram Bot

Este proyecto es un bot de Telegram altamente configurable mediante una interfaz web, diseñado para actuar como un experto en un tema específico utilizando Inteligencia Artificial (OpenAI).

## 1. Arquitectura General

El proyecto utiliza una arquitectura híbrida que combina un servidor web y un bot de mensajería:

*   **Servidor Web (Flask):** Proporciona una interfaz para que el usuario configure el comportamiento del bot (nombre, tema, tono, saludo, etc.).
*   **Bot de Telegram (python-telegram-bot):** Ejecuta la lógica de interacción con los usuarios finales en Telegram.
*   **Base de Datos (SQLite + SQLAlchemy):** Almacena la configuración definida en la interfaz web.
*   **IA (OpenAI API):** Procesa los mensajes de los usuarios y genera respuestas coherentes basadas en la configuración activa.

## 2. Componentes Principales

### `app.py`
Es el punto de entrada de la aplicación.
*   Inicializa la base de datos.
*   Lanza el bot de Telegram en un hilo (thread) separado utilizando `threading.Thread` para que coexista con el servidor web.
*   Define las rutas de Flask:
    *   `/`: Redirige a la configuración.
    *   `/config`: Permite ver y actualizar los parámetros del bot (POST/GET).

### `bot/telegram_bot.py`
Contiene la "inteligencia" del bot.
*   **Prompt Dinámico:** Construye un `system_prompt` para OpenAI basado en la configuración de la DB. Esto define la personalidad y las restricciones del bot.
*   **Restricción de Tema:** Implementa instrucciones estrictas para que el bot solo responda sobre el tema configurado (ej. "estética canina").
*   **Búsqueda de Imágenes:** Utiliza `icrawler` (Bing) para buscar imágenes cuando detecta que el usuario las solicita (ej. "muéstrame una foto de...").
*   **Manejo de Mensajes:** Procesa saludos iniciales y delega el resto a OpenAI.

### `models.py`
Define la estructura de la tabla `bot_config`:
*   `name`: Nombre del bot.
*   `use_emojis`: Booleano para activar/desactivar emojis.
*   `greeting`: Mensaje de bienvenida.
*   `tone`: Tono de la conversación (amigable, formal, etc.).
*   `topic`: El tema experto del bot.

### `config.py`
Gestiona las variables de entorno (`.env`):
*   `TELEGRAM_BOT_TOKEN`
*   `OPENAI_API_KEY`
*   `DATABASE_URL`

## 3. Flujo de Funcionamiento

1.  **Configuración:** El administrador accede a la web, define que el bot se llama "CanineExpert" y que su tema es "Cuidado de Perros".
2.  **Interacción:** Un usuario escribe al bot en Telegram: "¿Cómo baño a mi Husky?".
3.  **Procesamiento:**
    *   El bot recupera la configuración actual de la DB.
    *   Envía la pregunta a OpenAI con un prompt que dice: "Eres CanineExpert, solo sabes de Cuidado de Perros...".
    *   OpenAI genera la respuesta técnica.
4.  **Respuesta:** El usuario recibe una respuesta profesional sobre el baño del Husky. Si el usuario pregunta por "matemáticas", el bot declinará la respuesta siguiendo sus instrucciones.

## 4. Características Destacadas

*   **Soporte Multi-hilo:** Permite que el bot y la web funcionen simultáneamente.
*   **Inyección de Imágenes:** Si el bot decide que debe mostrar una imagen, inserta un tag `[[IMAGE: query]]` que el código de Python intercepta para realizar una búsqueda real en Bing y enviar la foto al chat.
*   **Personalización UI:** Incluye una plantilla HTML (`templates/config.html`) y CSS (`static/style.css`) para una gestión amigable.

## 5. Dependencias Clave
*   `Flask`: Framework web.
*   `python-telegram-bot`: Integración con Telegram.
*   `openai`: Motor de IA.
*   `SQLAlchemy`: ORM para la base de datos.
*   `icrawler`: Motor de búsqueda de imágenes.

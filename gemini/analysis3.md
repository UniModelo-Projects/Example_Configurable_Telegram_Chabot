# Análisis Técnico del Proyecto: Example Configurable Telegram Chatbot

Este documento presenta un análisis detallado de la arquitectura, funcionalidades y flujo de trabajo del proyecto "Example Configurable Telegram Chatbot".

## 1. Arquitectura General
El proyecto es una aplicación híbrida que combina un servidor web (Flask) con un bot de Telegram integrado. Utiliza una arquitectura orientada a la configuración dinámica, permitiendo que el comportamiento del bot sea modificado en tiempo de ejecución a través de una interfaz web.

### Componentes Principales:
- **Backend Web (Flask):** Gestiona la configuración del bot y sirve como el endpoint para el Webhook de Telegram.
- **Bot de Telegram (python-telegram-bot):** Procesa los mensajes de los usuarios de forma asíncrona.
- **Inteligencia Artificial (OpenAI GPT-3.5):** Motor de procesamiento de lenguaje natural que genera las respuestas del bot.
- **Base de Datos (SQLAlchemy/SQLite):** Persiste la configuración del bot y los "leads" capturados.
- **Buscador de Imágenes (icrawler):** Utiliza Bing para buscar y retornar imágenes bajo demanda.

## 2. Modelos de Datos
El sistema utiliza dos modelos principales definidos en `models.py`:
- **BotConfig:** Almacena la personalidad del bot (nombre, tono, tema, saludo inicial y preferencia de emojis).
- **Lead:** Almacena información de contacto y mensajes de usuarios que escriben fuera del horario de atención.

## 3. Flujo de Procesamiento de Mensajes
El bot opera bajo un flujo lógico condicional:

1.  **Recepción (Webhook):** Telegram envía una actualización al endpoint `/webhook` en Flask.
2.  **Verificación de Horario:**
    - Si el mensaje llega fuera del horario laboral (Lun-Vie, 6am-9pm), se guarda como un **Lead** y se envía una respuesta automática de "fuera de oficina".
3.  **Detección de Saludos:** Si el mensaje es un saludo genérico (ej. "Hola"), el bot responde con el saludo configurado en la base de datos sin consultar a la IA, ahorrando tokens.
4.  **Procesamiento IA:**
    - Se construye un **System Prompt** dinámico basado en la configuración actual.
    - Se realiza la consulta a OpenAI (`gpt-3.5-turbo`).
5.  **Manejo de Imágenes:**
    - Si la IA genera un tag `[[IMAGE: query]]` y el usuario solicitó explícitamente una imagen, el bot activa el `BingImageCrawler`.
    - Se extrae la URL de la imagen y se envía como un objeto `photo` en Telegram.

## 4. Características Destacadas
- **Persona Configurable:** El sistema permite cambiar el "tema" del bot (ej. de un experto en estética canina a un asesor de marketing) instantáneamente desde la web.
- **Restricción de Dominio:** El prompt del sistema incluye instrucciones estrictas para que el bot no responda sobre temas ajenos a su configuración ("Foco Absoluto").
- **Custom Downloader:** Implementa una clase `UrlDownloader` personalizada para capturar URLs de imágenes sin necesidad de almacenarlas localmente, optimizando el uso de disco.
- **Compatibilidad con PythonAnywhere:** El manejo de loops de `asyncio` dentro de las rutas de Flask está diseñado para funcionar en entornos WSGI sincrónicos.

## 5. Puntos de Mejora Identificados
1.  **Memoria de Conversación:** Actualmente el bot no mantiene el contexto de mensajes anteriores (stateless). Implementar un historial por `chat_id` mejoraría la experiencia.
2.  **Validación de Webhook:** Se recomienda añadir un token de seguridad en la URL del webhook o validar los rangos de IP de Telegram para evitar peticiones malintencionadas.
3.  **Manejo de Errores en Imágenes:** La búsqueda de imágenes depende de `icrawler` y Bing; una caída en el scraping podría dejar la funcionalidad inactiva. Una API oficial (Google Custom Search o Unsplash) sería más robusta.
4.  **UI de Configuración:** La interfaz actual es funcional pero básica; podría beneficiarse de feedback visual (toasts) tras guardar los cambios.

## 6. Configuración del Entorno
El proyecto requiere las siguientes variables de entorno:
- `OPENAI_API_KEY`: Para el acceso a GPT.
- `TELEGRAM_BOT_TOKEN`: Token obtenido vía BotFather.
- `WEBHOOK_URL`: URL pública (necesaria para el despliegue).

---
*Análisis generado por Gemini CLI - 25 de febrero de 2026*

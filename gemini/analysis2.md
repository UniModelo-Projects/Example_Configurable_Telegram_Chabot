# Análisis del Proyecto: Example Configurable Telegram Chatbot

## Descripción General
Este proyecto es un chatbot de Telegram altamente personalizable y configurable a través de una interfaz web (Flask). El bot utiliza inteligencia artificial (OpenAI GPT-3.5 Turbo) para actuar como un experto en un tema específico definido por el usuario, con la capacidad adicional de buscar y enviar imágenes de internet.

## Arquitectura del Sistema
El sistema emplea una arquitectura híbrida que combina un servidor web Flask para la gestión y configuración, con un cliente de Telegram que se ejecuta en un hilo separado.

### Componentes Principales:
1.  **Backend (Flask):** Gestiona la interfaz de configuración y la base de datos de persistencia.
2.  **Base de Datos (SQLAlchemy/SQLite):** Almacena la configuración de la personalidad del bot y los "leads" capturados fuera del horario de atención.
3.  **Bot de Telegram (python-telegram-bot):** Gestiona la interacción en tiempo real con los usuarios, integrando capacidades de IA y búsqueda de imágenes.
4.  **IA (OpenAI API):** Proporciona la lógica de procesamiento de lenguaje natural y el cumplimiento de la personalidad del bot.
5.  **Búsqueda de Imágenes (icrawler):** Utiliza el motor de Bing para encontrar contenido visual bajo demanda.

## Análisis Técnico de Archivos

### `app.py` (Punto de Entrada)
- Inicializa la aplicación Flask y la base de datos.
- Lanza el bot de Telegram en un hilo dedicado (`threading.Thread`) con un loop de eventos propio (`asyncio.new_event_loop()`).
- Define rutas para la visualización y actualización de la configuración del bot (`/config`).

### `models.py` (Modelado de Datos)
- **`BotConfig`**: Almacena el nombre del bot, saludo, tono, tema y preferencia de emojis.
- **`Lead`**: Registra información de contacto de usuarios que envían mensajes fuera del horario de oficina (ID de chat, nombre de usuario, mensaje y marca de tiempo).

### `bot/telegram_bot.py` (Lógica del Chatbot)
- **Gestión de Personalidad**: Construye un prompt del sistema dinámico basado en la configuración guardada en la base de datos.
- **Restricción de Temas**: Implementa instrucciones críticas para que la IA se mantenga enfocada exclusivamente en el tema configurado.
- **Integración de Imágenes**: Utiliza expresiones regulares para detectar la intención de búsqueda de imágenes y el tag `[[IMAGE: search_term]]` generado por la IA para realizar la búsqueda mediante `icrawler`.
- **Horario de Atención**: Implementa una restricción de horario (Lunes a Viernes, 6:00 AM - 9:00 PM), guardando mensajes en la tabla `Lead` si se reciben fuera de este intervalo.

## Características Destacadas
- **Configuración en Caliente**: Los cambios realizados en el panel web se reflejan inmediatamente en el comportamiento del bot sin necesidad de reiniciar el servicio.
- **Modo Polling Robusto**: Configurado para funcionar en entornos de servidor (como AWS Lightsail) sin necesidad de configurar webhooks complejos o túneles como ngrok.
- **Captura de Prospectos**: Funcionalidad de CRM básico para capturar el interés de los usuarios incluso cuando el bot no está "en servicio".

## Posibles Áreas de Mejora
- **Persistencia del Historial**: Actualmente, el bot procesa cada mensaje de forma independiente (stateless). Implementar un historial de conversación mejoraría la coherencia en diálogos largos.
- **Gestión de Errores**: Se podría robustecer la descarga de imágenes, ya que `icrawler` a veces puede fallar debido a bloqueos de los motores de búsqueda.
- **Seguridad**: La interfaz de configuración `/config` no tiene autenticación, lo que permitiría a cualquier usuario con la IP del servidor modificar la personalidad del bot.

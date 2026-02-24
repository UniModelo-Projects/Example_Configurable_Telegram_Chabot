# Configurable Telegram Chatbot with Image Search 🤖🍔🦕

A highly flexible Telegram chatbot built with Flask and `python-telegram-bot` that uses OpenAI's GPT-3.5 to act as an expert on any topic of your choice.

## Features ✨

*   **Custom Identity**: Fully configurable name, greeting, tone, and topic via a web dashboard.
*   **Polling Mode**: Runs directly without the need for webhooks or public URLs (like ngrok).
*   **Intelligent Image Search**: Automatically searches and sends real images from the internet (using Bing) when requested.
*   **Strict Topic Focus**: Advanced system prompting ensures the bot stays on topic and refuses unrelated tasks (like math or coding).
*   **Contextual Rejections**: Provides smart, topic-related explanations when declining off-topic questions.
*   **Safety First**: Built-in rules to avoid sensitive or tragic historical topics.

## Installation 🚀

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd example-configurable-telegram-chatbot
    ```

2.  **Set up the environment**:
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY="your_openai_api_key"
    TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
    SECRET_KEY="a_secure_random_string"
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    python app.py
    ```
    *Note: The app runs on port 80 by default. On some systems, you may need administrator/sudo privileges.*

## Usage 🛠️

1.  Navigate to `http://localhost/config` (or your server's IP) to set up your bot's personality.
2.  Open your bot on Telegram.
3.  Start chatting! Use keywords like "ver", "foto", or "muéstrame" to see images related to your topic.

## Tech Stack 📚

*   **Backend**: Flask (Python)
*   **Bot Framework**: `python-telegram-bot` (v21.6+)
*   **AI**: OpenAI GPT-3.5 Turbo
*   **Database**: SQLite (SQLAlchemy)
*   **Image Search**: `icrawler` (Bing engine)

## License 📄

This project is open-source and available under the MIT License.

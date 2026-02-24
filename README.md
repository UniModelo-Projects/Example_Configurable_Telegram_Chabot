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

## Deployment (AWS Lightsail) ☁️

To deploy this bot on an AWS Lightsail instance (Ubuntu), follow these steps:

### 1. Configure the Firewall
In your Lightsail console, go to the **Networking** tab and ensure **Port 80 (HTTP)** is open to the public.

### 2. Prepare the Instance
```bash
sudo apt update && sudo apt install python3-pip python3-venv -y
git clone <your-repo-url>
cd example-configurable-telegram-chatbot
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create the `.env` file as described in the Installation section.

### 4. Run in the Background
Since the app binds to port 80, you **must** use `sudo`. To keep it running after you close the terminal, use `nohup`:
```bash
sudo nohup env/bin/python app.py > app.log 2>&1 &
```

### 5. Managing the Process
*   **View Logs**: `tail -f app.log`
*   **Check if it's running**: `ps aux | grep python` (Look for the `app.py` process).
*   **Stop the App**: `sudo kill <PID>` (Replace `<PID>` with the process ID found in the previous step).

> **Warning**: Never run more than one instance of the bot at the same time, as this will cause "Conflict" errors with the Telegram API.

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

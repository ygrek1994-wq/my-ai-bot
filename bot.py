import os
import logging
from flask import Flask, request
import telegram
import time
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
YOUR_CHAT_ID = 1548065812  # Ваш ID

if not TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен!")
    exit(1)

# Создаем Flask приложение
app = Flask(__name__)

# Создаем бота (используем синхронную версию)
bot = telegram.Bot(token=TOKEN)

def send_message_sync(chat_id, text):
    """Синхронная отправка сообщения"""
    try:
        bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Сообщение отправлено в {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return False

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Обработка входящих сообщений"""
    try:
        data = request.get_json(force=True)
        logger.info(f"Webhook получен: {data.get('update_id')}")
        
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            text = data['message']['text']
            
            logger.info(f"Сообщение от {chat_id}: {text}")
            
            # Отправляем ответ
            send_message_sync(chat_id, f"Ты написал: {text}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return "OK", 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

def setup_webhook_sync():
    """Синхронная настройка webhook"""
    try:
        render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        if render_hostname:
            webhook_url = f"https://{render_hostname}/{TOKEN}"
            logger.info(f"Устанавливаем webhook на {webhook_url}")
            
            bot.delete_webhook()
            success = bot.set_webhook(url=webhook_url)
            
            if success:
                logger.info("Webhook установлен!")
                send_message_sync(YOUR_CHAT_ID, "✅ Бот запущен!")
            else:
                logger.error("Не удалось установить webhook")
    except Exception as e:
        logger.error(f"Ошибка настройки webhook: {e}")

if __name__ == "__main__":
    # Настраиваем webhook синхронно
    setup_webhook_sync()
    
    # Запускаем Flask (без asyncio, без потоков)
    logger.info(f"Запуск Flask на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT)

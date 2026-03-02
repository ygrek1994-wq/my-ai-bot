import os
import logging
from flask import Flask, request
import telegram
import asyncio

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

# Создаем бота
bot = telegram.Bot(token=TOKEN)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Обработка входящих сообщений"""
    try:
        # Получаем обновление от Telegram
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        logger.info(f"Получено обновление: {update.update_id}")
        
        # Если есть сообщение
        if update.message and update.message.text:
            chat_id = update.message.chat.id
            text = update.message.text
            
            logger.info(f"Сообщение от {chat_id}: {text}")
            
            # Отправляем ответ (просто эхо)
            bot.send_message(
                chat_id=chat_id,
                text=f"Ты написал: {text}"
            )
            logger.info(f"Ответ отправлен в чат {chat_id}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        return "Error", 500

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

async def setup_webhook():
    """Настройка webhook"""
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    
    if render_hostname:
        webhook_url = f"https://{render_hostname}/{TOKEN}"
        logger.info(f"Устанавливаем webhook на {webhook_url}")
        
        # Удаляем старый webhook
        await bot.delete_webhook()
        
        # Устанавливаем новый
        success = await bot.set_webhook(url=webhook_url)
        
        if success:
            logger.info("Webhook успешно установлен!")
            # Отправляем тестовое сообщение вам
            await bot.send_message(
                chat_id=YOUR_CHAT_ID,
                text="✅ Бот запущен и работает через простую версию!"
            )
        else:
            logger.error("Не удалось установить webhook")

def run_flask():
    """Запуск Flask"""
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == "__main__":
    # Настраиваем webhook
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    
    # Запускаем Flask в отдельном потоке
    import threading
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    logger.info("Бот запущен и готов к работе!")
    
    # Держим программу работающей
    loop.run_forever()

import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

if not TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен!")
    exit(1)

# Создаем Flask приложение
app = Flask(__name__)

# Создаем приложение Telegram бота
telegram_app = Application.builder().token(TOKEN).build()

async def start(update, context):
    """Обработчик команды /start"""
    logger.info(f"Команда /start от пользователя {update.effective_user.id}")
    await update.message.reply_text("👋 Привет! Я тестовый бот. Я работаю!")

async def handle_message(update, context):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Сообщение от {user_id}: {user_message}")
    
    # Просто отвечаем
    await update.message.reply_text(f"Ты написал: {user_message}")
    
    logger.info(f"Ответ отправлен пользователю {user_id}")

# Добавляем обработчики
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Создаем event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Endpoint для получения обновлений от Telegram"""
    logger.info("Получен webhook запрос")
    update = telegram.Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    return "OK", 200

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
        
        await telegram_app.bot.delete_webhook()
        success = await telegram_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=telegram.Update.ALL_TYPES
        )
        
        if success:
            logger.info("Webhook успешно установлен!")
        else:
            logger.error("Не удалось установить webhook")

def run_flask():
    """Запуск Flask"""
    logger.info(f"Запускаем Flask на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == "__main__":
    # Настраиваем webhook
    loop.run_until_complete(setup_webhook())
    
    # Запускаем Flask в отдельном потоке
    import threading
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запускаем event loop
    loop.run_forever()

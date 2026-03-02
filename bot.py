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

# Глобальный event loop для асинхронных операций
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def send_telegram_message(chat_id, text):
    """Синхронная отправка сообщения в Telegram"""
    try:
        # Используем asyncio.run_coroutine_threadsafe для отправки из другого потока
        future = asyncio.run_coroutine_threadsafe(
            bot.send_message(chat_id=chat_id, text=text),
            loop
        )
        # Ждем результат не больше 10 секунд
        future.result(timeout=10)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return False

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Обработка входящих сообщений"""
    try:
        # Получаем данные от Telegram
        data = request.get_json(force=True)
        logger.info(f"Получен webhook: {data.get('update_id')}")
        
        # Проверяем, есть ли сообщение
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            text = data['message']['text']
            
            logger.info(f"Сообщение от {chat_id}: {text}")
            
            # Отправляем ответ (синхронно)
            success = send_telegram_message(chat_id, f"Ты написал: {text}")
            
            if success:
                logger.info(f"Ответ отправлен в чат {chat_id}")
            else:
                logger.error(f"Не удалось отправить ответ в чат {chat_id}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}", exc_info=True)
        return "OK", 200  # Все равно возвращаем 200, чтобы Telegram не слал повторно

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
                text="✅ Бот запущен и работает!"
            )
        else:
            logger.error("Не удалось установить webhook")

def run_flask():
    """Запуск Flask"""
    logger.info(f"Запускаем Flask на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Настраиваем webhook в главном потоке
    loop.run_until_complete(setup_webhook())
    
    # Запускаем Flask в отдельном потоке
    import threading
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        # Запускаем event loop в главном потоке
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
        loop.close()

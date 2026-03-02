import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import openai
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.proxyapi.ru/openai/v1")
PORT = int(os.environ.get("PORT", 10000))

# Проверка наличия токенов
if not TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен!")
    exit(1)
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY не установлен!")
    exit(1)

# Инициализация OpenAI
openai.api_key = OPENAI_API_KEY
openai.api_base = OPENAI_API_BASE

# Создаем Flask приложение
app = Flask(__name__)

# Словарь для хранения счетчиков запросов
user_requests = {}

# Создаем и инициализируем приложение Telegram бота
telegram_app = Application.builder().token(TOKEN).build()

async def start(update, context):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник с доступом к нейросети.\n"
        "У тебя есть 3 бесплатных запроса в день.\n"
        "Просто напиши мне свой вопрос!"
    )

async def handle_message(update, context):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Простой счетчик запросов
    if user_id not in user_requests:
        user_requests[user_id] = 0
    
    if user_requests[user_id] >= 3:
        await update.message.reply_text(
            "❌ Лимит бесплатных запросов на сегодня исчерпан.\n"
            "Скоро добавим подписку за Telegram Stars!"
        )
        return
    
    # Показываем, что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.constants.ChatAction.TYPING)
    
    try:
        # Отправляем запрос к нейросети через ProxyAPI
        logger.info(f"Запрос от пользователя {user_id}: {user_message[:50]}...")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            timeout=30
        )
        
        answer = response.choices[0].message.content
        user_requests[user_id] += 1
        
        # Отправляем ответ (с разбивкой, если длинный)
        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i+4096])
        else:
            await update.message.reply_text(answer)
            
        logger.info(f"Ответ отправлен пользователю {user_id}")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")

# Добавляем обработчики
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Создаем event loop для асинхронных операций
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Endpoint для получения обновлений от Telegram"""
    update = telegram.Update.de_json(request.get_json(force=True), telegram_app.bot)
    
    # Запускаем обработку обновления в event loop
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    
    return "OK", 200

@app.route("/health", methods=["GET"])
def health():
    """Health check для Render"""
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

async def setup_webhook():
    """Настройка webhook"""
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    
    if render_hostname:
        webhook_url = f"https://{render_hostname}/{TOKEN}"
    else:
        webhook_url = f"https://localhost:{PORT}/{TOKEN}"
    
    logger.info(f"Устанавливаем webhook на {webhook_url}")
    
    # Удаляем старый webhook, если был
    await telegram_app.bot.delete_webhook()
    
    # Устанавливаем новый webhook
    success = await telegram_app.bot.set_webhook(
        url=webhook_url,
        allowed_updates=telegram.Update.ALL_TYPES
    )
    
    if success:
        logger.info("Webhook успешно установлен!")
    else:
        logger.error("Не удалось установить webhook")

def run_flask():
    """Запуск Flask приложения"""
    logger.info(f"Запускаем Flask на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == "__main__":
    # Настраиваем webhook в event loop
    loop.run_until_complete(setup_webhook())
    
    # Запускаем Flask в отдельном потоке, чтобы не блокировать event loop
    import threading
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем event loop
    loop.run_forever()

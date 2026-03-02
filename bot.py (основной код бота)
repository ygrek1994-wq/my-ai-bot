import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import openai

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.proxyapi.ru/openai/v1")
PORT = int(os.environ.get("PORT", 10000))

# Инициализация OpenAI
openai.api_key = OPENAI_API_KEY
openai.api_base = OPENAI_API_BASE

# Создаем Flask приложение
app = Flask(__name__)

# Словарь для хранения счетчиков запросов (в реальном проекте лучше использовать БД)
user_requests = {}

async def start(update, context):
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник с доступом к нейросети.\n"
        "У тебя есть 3 бесплатных запроса в день.\n"
        "Просто напиши мне свой вопрос!"
    )

async def handle_message(update, context):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Простой счетчик запросов (для демо)
    if user_id not in user_requests:
        user_requests[user_id] = 0
    
    if user_requests[user_id] >= 3:
        await update.message.reply_text(
            "❌ Лимит бесплатных запросов на сегодня исчерпан.\n"
            "Скоро добавим подписку за Telegram Stars!"
        )
        return
    
    try:
        # Отправляем запрос к нейросети через ProxyAPI
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
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")

# Создаем приложение Telegram бота
telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Endpoint для получения обновлений от Telegram"""
    update = telegram.Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

@app.route("/health", methods=["GET"])
def health():
    """Health check для Render"""
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

async def run_bot():
    """Запуск бота"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/{TOKEN}"
    await telegram_app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook установлен на {webhook_url}")

if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())
    app.run(host="0.0.0.0", port=PORT)

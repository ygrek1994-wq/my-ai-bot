async def handle_message(update, context):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Получено сообщение от пользователя {user_id}: {user_message[:50]}...")
    
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
        # Проверяем наличие API ключа
        if not openai.api_key:
            logger.error("OPENAI_API_KEY не установлен!")
            await update.message.reply_text("Ошибка: не настроен API ключ")
            return
            
        logger.info("Отправляем запрос к OpenAI...")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            timeout=30
        )
        
        logger.info("Получен ответ от OpenAI")
        
        answer = response.choices[0].message.content
        user_requests[user_id] += 1
        
        # Отправляем ответ
        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i+4096])
        else:
            await update.message.reply_text(answer)
            
        logger.info(f"Ответ успешно отправлен пользователю {user_id}")
            
    except openai.error.AuthenticationError as e:
        logger.error(f"Ошибка аутентификации OpenAI: {e}")
        await update.message.reply_text("Ошибка: неверный API ключ")
    except openai.error.RateLimitError as e:
        logger.error(f"Превышен лимит запросов: {e}")
        await update.message.reply_text("Превышен лимит запросов. Попробуйте позже.")
    except openai.error.Timeout as e:
        logger.error(f"Таймаут при запросе к OpenAI: {e}")
        await update.message.reply_text("Сервис временно недоступен. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")

import logging
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import aiohttp

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токены из переменных окружения (Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
SUPPORT_USERNAME = "tgcumpot"  # или os.getenv("SUPPORT_USERNAME")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

# Пути к медиа (они уже в корне проекта)
WELCOME_PHOTO_PATH = "настя.jpg"
PAYMENT_VIDEO_PATH = "крипта.mp4"

# Тарифы
TARIFFS = {
    "1week": {"name": "1 неделя", "display_price": "$5", "amount": 5.0, "currency": "USDT"},
    "1month": {"name": "1 месяц", "display_price": "$10", "amount": 10.0, "currency": "USDT"},
    "3months": {"name": "3 месяца", "display_price": "$25", "amount": 25.0, "currency": "USDT"},
    "forever": {"name": "Навсегда", "display_price": "$50", "amount": 50.0, "currency": "USDT"},
}

# Инвойс
async def create_crypto_invoice(amount: float, currency: str, description: str, payload: str):
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}
    data = {
        "asset": "USDT",
        "amount": str(amount),
        "description": description,
        "payload": payload,
        "allow_comments": False,
        "allow_anonymous": False,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as resp:
            if resp.status == 200:
                return (await resp.json()).get("result")
            else:
                logger.error(f"Ошибка инвойса: {await resp.text()}")
                return None

# [Остальные функции: start, show_tariffs, show_tariff, button_callback, handle_message — без изменений]
# ... (вставь свой текущий код функций start, show_tariffs и т.д. здесь)

# === ВСТАВЬ СЮДА ВСЕ СВОИ ФУНКЦИИ (start, show_tariffs, show_tariff, button_callback, handle_message) ===

# Главная функция — ЗАПУСК С WEBHOOK
def main():
    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if not BOT_TOKEN or not CRYPTO_BOT_TOKEN or not ADMIN_USER_ID:
        raise ValueError("❌ Отсутствуют переменные окружения: BOT_TOKEN, CRYPTO_BOT_TOKEN, ADMIN_USER_ID")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_URL:
        secret_path = BOT_TOKEN.split(":")[1]
        webhook_url = f"{WEBHOOK_URL}/{secret_path}"
        logger.info(f"Setting webhook to: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=secret_path,
            webhook_url=webhook_url
        )
    else:
        # Для локального запуска (не используется на Render)
        import asyncio
        asyncio.run(app.run_polling())

if __name__ == "__main__":
    main()

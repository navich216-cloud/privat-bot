import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import aiohttp

# 🔑 Твои данные
BOT_TOKEN = "8575361693:AAGiuaEMLoiwQCp9TueKzwX-9ZYRXAaCpH0"
CRYPTO_BOT_TOKEN = "493736:AAPmbol8ZKIjLo0RvTswT64OnKZSzM1H4ZU"
SUPPORT_USERNAME = "Alexxxey_pet"  # Теперь используется в тексте
MAIN_CHANNEL = "https://t.me/your_channel"
ADMIN_USER_ID = 8103143973  # Твой ID

# Пути к медиа
WELCOME_PHOTO_PATH = "настя.jpg"
PAYMENT_VIDEO_PATH = "крипта.mp4"

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Тарифы в USD
TARIFFS = {
    "1week": {"name": "1 неделя", "display_price": "$5", "amount": 5.0, "currency": "USDT"},
    "1month": {"name": "1 месяц", "display_price": "$10", "amount": 10.0, "currency": "USDT"},
    "3months": {"name": "3 месяца", "display_price": "$25", "amount": 25.0, "currency": "USDT"},
    "forever": {"name": "Навсегда", "display_price": "$50", "amount": 50.0, "currency": "USDT"},
}

# Создание инвойса в CryptoBot
async def create_crypto_invoice(amount: float, currency: str, description: str, payload: str):
    url = "https://pay.crypt.bot/api/createInvoice"  # ← без пробелов!
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

# /start — ловим реферрера (p1, p2, p3)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ref = context.args[0] if context.args and context.args[0] in ["p1", "p2", "p3"] else "unknown"
    context.user_data["referrer"] = ref
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} пришёл от: {ref}")

    welcome_text = (
        "Привет, мой любимый 💋\n\n"
        "В этом боте ты можешь купить подписки на мой канал 18+\n\n"
        "Не забудь подписаться на основной канал\n\n"
        "Чтобы выбрать тариф тыкай ниже ⬇️\n\n"
        "🔞 Внимание! Покупая подписку, вы соглашаетесь, что вам больше 18 лет! 🔞"
    )
    keyboard = [
        [KeyboardButton("💰 Тарифы")],
        [KeyboardButton("⏳ Моя подписка")],
        [KeyboardButton("💖 Основной канал")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    try:
        with open(WELCOME_PHOTO_PATH, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=welcome_text, reply_markup=reply_markup)
    except FileNotFoundError:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)

# Тарифы
async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tariff_text = "📋 Выберите тариф:"
    keyboard = [
        [KeyboardButton("1️⃣ 1 неделя • full")],
        [KeyboardButton("2️⃣ 1 месяц • full")],
        [KeyboardButton("3️⃣ 3 месяца • full")],
        [KeyboardButton("♾️ навсегда • full")],
        [KeyboardButton("👈 Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(text=tariff_text, reply_markup=reply_markup)

# Показ тарифа
async def show_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_key: str):
    if tariff_key not in TARIFFS:
        await update.message.reply_text("Тариф не найден.")
        return

    tariff = TARIFFS[tariff_key]
    video_caption = (
        f"📦 Тариф: {tariff['name']} • full\n"
        f"💰 Стоимость: {tariff['display_price']}\n\n"
        "Оплата в USDT это не сложно, занимает 5-10 минут\n\n"
        "Если вы первый раз покупаете USDT/TON, то рекомендую к просмотру эту видеоинструкцию \n\n"
        "❗️ПОРЯДОК ДЕЙСТВИЙ:\n"
        "1) Сначала покупаем USDT/TON в @CryptoBot\n"
        "2) Возвращаемся в ЭТОТ бот\n"
        "3) Нажимаем нужную кнопку ниже\n\n"
        "Если у Вас есть USDT/TON в другом кошельке, то переведите его на свой кошелек в @CryptoBot\n"
        "А после этого оплачивайте подписку, так оплата пройдет без задержек.\n\n"
        "Рекомендую покупать немного больше USDT/TON, буквально на 20-30 рублей, чтобы покрыть скачки курса.\n\n"
        "По вопросам оплаты: @Alexxxey_pet"
    )

    tariff_names = {
        "1week": "1 неделю",
        "1month": "1 месяц",
        "3months": "3 месяца",
        "forever": "навсегда"
    }
    button_text = f"Купить подписку на {tariff_names[tariff_key]}"

    keyboard = [
        [InlineKeyboardButton(button_text, callback_data=f"pay_{tariff_key}")],
        [InlineKeyboardButton("Назад", callback_data="back_to_tariffs")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open(PAYMENT_VIDEO_PATH, 'rb') as video:
            await update.message.reply_video(
                video=video,
                caption=video_caption,
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "⚠️ Видео временно недоступно. Обратитесь в поддержку: @tgcumpot",
            reply_markup=reply_markup
        )

# Обработка inline-кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_tariffs":
        await show_tariffs(update, context)

    elif data.startswith("pay_"):
        tariff_key = data[4:]
        if tariff_key not in TARIFFS:
            await query.message.reply_text("Тариф не найден.")
            return

        tariff = TARIFFS[tariff_key]
        user = update.effective_user
        user_id = user.id
        username = f"@{user.username}" if user.username else f"ID: {user_id}"
        payload = f"{user_id}_{tariff_key}"
        referrer = context.user_data.get("referrer", "unknown")

        invoice = await create_crypto_invoice(
            amount=tariff["amount"],
            currency="USDT",
            description=f"Подписка: {tariff['name']} • {username}",
            payload=payload
        )

        if invoice:
            pay_url = invoice["pay_url"]
            # Обновлённый текст с менеджером и @Alexxxey_pet
            await query.message.reply_text(
                f"✨ Отлично! Ты выбрал тариф «{tariff['name']}» ({tariff['display_price']}).\n\n"
                f"✅ Оплати по кнопке ниже:  \n"
                f"🔐 [Перейти к оплате]({pay_url})\n\n"
                f"⏳ После оплаты **менеджер вручную проверит твой платёж** и пришлёт **ссылку на приватный канал** в течение 10–30 минут.\n\n"
                f"❗ Если возникли вопросы с оплатой или что-то не получается — пиши напрямую: [@{SUPPORT_USERNAME}](https://t.me/{SUPPORT_USERNAME})",
                parse_mode="Markdown"
            )

            # Уведомление тебе
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=(
                        f"🔔 НОВАЯ ОПЛАТА ОЖИДАЕТСЯ!\n\n"
                        f"Пользователь: {username} ({user_id})\n"
                        f"Тариф: {tariff['name']} ({tariff['display_price']})\n"
                        f"Сумма: {tariff['amount']} USDT\n"
                        f"Источник: {referrer}\n"
                        f"Payload: `{payload}`\n\n"
                        f"Проверь в @CryptoBot → Invoices"
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить админа: {e}")
        else:
            await query.message.reply_text(f"❌ Ошибка. Напиши @{SUPPORT_USERNAME}")

# Остальные команды
async def show_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ У вас нет активной подписки.\nВыберите тариф в меню → 💰 Тарифы"
    )

async def show_main_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💖 Основной канал:\n{MAIN_CHANNEL}\n\nПодпишись, чтобы не пропустить новое! ❤️"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ["👈 Назад", "Назад"]:
        await start(update, context)
    elif text == "💰 Тарифы":
        await show_tariffs(update, context)
    elif text == "⏳ Моя подписка":
        await show_subscription(update, context)
    elif text == "💖 Основной канал":
        await show_main_channel(update, context)
    elif text == "1️⃣ 1 неделя • full":
        await show_tariff(update, context, "1week")
    elif text == "2️⃣ 1 месяц • full":
        await show_tariff(update, context, "1month")
    elif text == "3️⃣ 3 месяца • full":
        await show_tariff(update, context, "3months")
    elif text == "♾️ навсегда • full":
        await show_tariff(update, context, "forever")
    else:
        await update.message.reply_text("Используйте кнопки меню 👇")

# Запуск
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен!")
    print("🔗 Правильные ссылки для партнёров (БЕЗ @):")
    print("  Партнёр 1 → https://t.me/privat_nastenki_bot?start=p1")
    print("  Партнёр 2 → https://t.me/privat_nastenki_bot?start=p2")
    print("  Партнёр 3 → https://t.me/privat_nastenki_bot?start=p3")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

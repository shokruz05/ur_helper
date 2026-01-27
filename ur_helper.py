import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8447190645:AAGJoE-mSIUoPUnSPJAZV5VYd3dLIoVLd40'
ADMIN_ID = 8239382195 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Мини-сервер для "обмана" Render
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ВАШИ ТЕКСТЫ ---
user_languages = {}
TEXTS = {
    'ru': {
        'main_menu': "<b>👋 Shokirjon’s Assistant.</b> Выберите услугу:",
        'kurs': "👨‍🏫 Курсовые работы",
        'mustaqil': "📝 Самостоятельные",
        'dev': "💻 Разработка",
        'other': "❓ Другое",
        'wait': "<b>📨 Запрос отправлен!</b> Подождите ответа.",
        'order_msg': "🔔 <b>НОВЫЙ ЗАПРОС</b>"
    },
    'uz': {
        'main_menu': "<b>👋 Shokirjon’s Assistant.</b> Xizmatni tanlang:",
        'kurs': "👨‍🏫 Kurs ishlari",
        'mustaqil': "📝 Mustaqil ishlar",
        'dev': "💻 Dasturlash",
        'other': "❓ Boshqa savollar",
        'wait': "<b>📨 So'rovingiz yuborildi!</b> Javobni kuting."
    }
}

# --- КЛАВИАТУРЫ ---
def get_lang_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Русский 🇷🇺", callback_data="setlang_ru"))
    builder.row(types.InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="setlang_uz"))
    return builder.as_markup()

def get_main_menu(lang):
    builder = InlineKeyboardBuilder()
    t = TEXTS[lang]
    builder.row(types.InlineKeyboardButton(text=t['kurs'], callback_data="service_kurs"))
    builder.row(types.InlineKeyboardButton(text=t['mustaqil'], callback_data="service_mustaqil"))
    builder.row(types.InlineKeyboardButton(text=t['dev'], callback_data="service_dev"))
    builder.row(types.InlineKeyboardButton(text=t['other'], callback_data="service_other"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=get_lang_kb())

@dp.callback_query(F.data.startswith("setlang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    await callback.message.edit_text(TEXTS[lang]['main_menu'], reply_markup=get_main_menu(lang), parse_mode="HTML")

@dp.callback_query(F.data.startswith("service_"))
async def handle_service(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    service_name = TEXTS[lang][callback.data.split("_")[1]]
    await callback.message.answer(TEXTS[lang]['wait'], parse_mode="HTML")
    await bot.send_message(ADMIN_ID, f"🔔 <b>НОВЫЙ ЗАПРОС</b>\n🆔 ID: <code>{user_id}</code>\n🛠 Услуга: {service_name}", parse_mode="HTML")

# Ответ админа (через Reply)
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_ID)
async def admin_response(message: types.Message):
    if message.reply_to_message and "🆔 ID:" in message.reply_to_message.text:
        try:
            target_user_id = int(message.reply_to_message.text.split("🆔 ID: <code>")[1].split("</code>")[0])
            if message.document:
                await bot.send_document(target_user_id, message.document.file_id, caption="✅ Ваш заказ готов!")
            else:
                await bot.send_message(target_user_id, f"✉️ <b>Ответ:</b>\n\n{message.text}", parse_mode="HTML")
            await message.answer("🚀 Отправлено!")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

# --- ЗАПУСК ---
async def main():
    await start_web_server() # Критически важно для Render!
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    

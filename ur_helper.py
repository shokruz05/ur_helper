import asyncio
import os
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8185440589:AAGmDK8dqi0ZNUOjWw2-jy1mtKTspDKWO4Y'
ADMIN_ID = 8692969555 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Состояния для ввода текста
class UserState(StatesGroup):
    waiting_for_text = State()

# --- МИНИ-СЕРВЕР ДЛЯ RENDER ---
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

# --- ЛОКАЛИЗАЦИЯ ---
user_languages = {}
TEXTS = {
    'ru': {
        'welcome': "<b>Выберите язык / Tilni tanlang:</b>",
        'main_menu': "<b>👋 Shokirjon’s Assistant.</b> Выберите услугу:",
        'kurs': "👨‍🏫 Курсовые работы",
        'mustaqil': "📝 Самостоятельные / ИДЗ",
        'dev': "💻 Разработка (Bots/Web)",
        'other': "❓ Другое / Личный вопрос",
        'ask_text': "📝 <b>Напишите ваше сообщение или проблему:</b>",
        'wait': "<b>📨 Ваш запрос отправлен!</b> Шокиржон ответит вам скоро.",
        'order_msg': "🔔 <b>НОВЫЙ ЗАПРОС</b>"
    },
    'uz': {
        'welcome': "<b>Tilni tanlang / Выберите язык:</b>",
        'main_menu': "<b>👋 Shokirjon’s Assistant.</b> Xizmatni tanlang:",
        'kurs': "👨‍🏫 Kurs ishlari",
        'mustaqil': "📝 Mustaqil ishlar / IDZ",
        'dev': "💻 Dasturlash (Bot/Web)",
        'other': "❓ Boshqa savollar",
        'ask_text': "📝 <b>Xabaringizni yoki muammoingizni yozing:</b>",
        'wait': "<b>📨 So'rovingiz yuborildi!</b> Shokirjon tez orada javob beradi."
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
    await message.answer(TEXTS['ru']['welcome'], reply_markup=get_lang_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("setlang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    await callback.message.edit_text(TEXTS[lang]['main_menu'], reply_markup=get_main_menu(lang), parse_mode="HTML")

# Нажатие на кнопки услуг
@dp.callback_query(F.data.startswith("service_"))
async def handle_service(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    service_key = callback.data.split("_")[1]
    
    if service_key == 'other':
        # Включаем режим ожидания текста от пользователя
        await callback.message.answer(TEXTS[lang]['ask_text'], parse_mode="HTML")
        await state.set_state(UserState.waiting_for_text)
    else:
        service_name = TEXTS[lang][service_key]
        await callback.message.answer(TEXTS[lang]['wait'], parse_mode="HTML")
        await bot.send_message(ADMIN_ID, f"🔔 <b>НОВЫЙ ЗАПРОС</b>\n🌍 Язык: {lang.upper()}\n🛠 Услуга: {service_name}\n👤 Клиент: @{callback.from_user.username or 'NoUser'}\n🆔 ID: <code>{user_id}</code>", parse_mode="HTML")
    await callback.answer()

# Получение произвольного текста от пользователя (для "Другое")
@dp.message(UserState.waiting_for_text)
async def process_user_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    await message.answer(TEXTS[lang]['wait'], parse_mode="HTML")
    await bot.send_message(
        ADMIN_ID,
        f"📩 <b>ЛИЧНОЕ СООБЩЕНИЕ</b>\n"
        f"👤 Клиент: @{message.from_user.username or 'NoUser'}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💬 Текст: <i>{message.text}</i>",
        parse_mode="HTML"
    )
    await state.clear()

# --- ИСПРАВЛЕННЫЙ ОТВЕТ АДМИНА ---
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_ID)
async def admin_response(message: types.Message):
    if message.reply_to_message:
        try:
            # Ищем ID в тексте сообщения, на которое ты ответил
            match = re.search(r'ID: (\d+)', message.reply_to_message.text) or \
                    re.search(r'ID: <code>(\d+)</code>', message.reply_to_message.text)
            
            if match:
                target_user_id = int(match.group(1))
                if message.document:
                    await bot.send_document(target_user_id, message.document.file_id, caption="✅ Ваш заказ готов!")
                elif message.photo:
                    await bot.send_photo(target_user_id, message.photo[-1].file_id, caption="✅ Файл прикреплен!")
                else:
                    await bot.send_message(target_user_id, f"✉️ <b>Ответ от Шокиржона:</b>\n\n{message.text}", parse_mode="HTML")
                await message.answer("🚀 Отправлено!")
            else:
                await message.answer("❌ ID не найден. Отвечайте только на сообщения с ID.")
        except Exception as e:
            await message.answer(f"❌ Ошибка отправки: {e}")

async def main():
    await start_web_server()
    print("🚀 Shokirjon's Assistant запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    

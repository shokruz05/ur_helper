import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8447190645:AAGJoE-mSIUoPUnSPJAZV5VYd3dLIoVLd40'
ADMIN_ID = 8239382195 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Временное хранилище выбранного языка
user_languages = {}

# --- ТЕКСТЫ И ЛОКАЛИЗАЦИЯ ---
TEXTS = {
    'ru': {
        'welcome': "<b>Выберите язык / Tilni tanlang:</b>",
        'main_menu': (
            "<b>👋 Здравствуйте! Вас приветствует Shokirjon’s Assistant.</b>\n\n"
            "Я помогу вам решить учебные задачи или создать IT-проект.\n"
            "<i>Выберите нужный раздел ниже:</i>"
        ),
        'kurs': "👨‍🏫 Курсовые работы",
        'mustaqil': "📝 Самостоятельные / ИДЗ",
        'dev': "💻 Разработка (Bots/Web)",
        'other': "❓ Другое / Личный вопрос",
        'wait': (
            "<b>📨 Запрос отправлен Шокиржону!</b>\n\n"
            "Пожалуйста, подождите. Он ответит вам прямо в этом чате в ближайшее время."
        ),
        'order_msg': "🔔 <b>НОВЫЙ ЗАПРОС</b>",
        'lang_confirm': "Язык установлен: Русский 🇷🇺"
    },
    'uz': {
        'welcome': "<b>Tilni tanlang / Выберите язык:</b>",
        'main_menu': (
            "<b>👋 Salom! Sizni Shokirjon’s Assistant qutlaydi.</b>\n\n"
            "Men sizga o'quv vazifalarini bajarishda yoki IT-loyihalarni yaratishda yordam beraman.\n"
            "<i>Kerakli bo'limni tanlang:</i>"
        ),
        'kurs': "👨‍🏫 Kurs ishlari",
        'mustaqil': "📝 Mustaqil ishlar / IDZ",
        'dev': "💻 Dasturlash (Bot/Web)",
        'other': "❓ Boshqa savollar",
        'wait': (
            "<b>📨 So'rovingiz Shokirjonga yuborildi!</b>\n\n"
            "Iltimos, biroz kuting. U tez orada sizga javob beradi."
        ),
        'order_msg': "🔔 <b>YANGI SO'ROV</b>",
        'lang_confirm': "Til tanlandi: O'zbekcha 🇺🇿"
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

# --- ОБРАБОТЧИКИ (HANDLERS) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(TEXTS['ru']['welcome'], reply_markup=get_lang_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("setlang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    await callback.answer(TEXTS[lang]['lang_confirm'])
    await callback.message.edit_text(TEXTS[lang]['main_menu'], reply_markup=get_main_menu(lang), parse_mode="HTML")

@dp.callback_query(F.data.startswith("service_"))
async def handle_service(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    service_key = callback.data.split("_")[1]
    service_name = TEXTS[lang][service_key]

    # Ответ пользователю
    await callback.message.answer(TEXTS[lang]['wait'], parse_mode="HTML")
    
    # Уведомление тебе (Админу)
    await bot.send_message(
        ADMIN_ID,
        f"{TEXTS[lang]['order_msg']}\n"
        f"🌍 Язык: {lang.upper()}\n"
        f"🛠 Услуга: <b>{service_name}</b>\n"
        f"👤 Клиент: @{callback.from_user.username or 'NoUser'}\n"
        f"🆔 ID: <code>{user_id}</code>",
        parse_mode="HTML"
    )
    await callback.answer()

# --- ЛОГИКА ОТВЕТА АДМИНА (ОТПРАВКА ФАЙЛОВ И ТЕКСТА) ---
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_ID)
async def admin_response(message: types.Message):
    # Проверяем, что ты отвечаешь (Reply) на уведомление с ID
    if message.reply_to_message and "🆔 ID:" in message.reply_to_message.text:
        try:
            # Извлекаем ID из текста уведомления
            target_user_id = int(message.reply_to_message.text.split("🆔 ID: <code>")[1].split("</code>")[0])
            
            if message.document:
                await bot.send_document(target_user_id, message.document.file_id, 
                                        caption="✅ <b>Ваш заказ готов!</b>", parse_mode="HTML")
            elif message.photo:
                await bot.send_photo(target_user_id, message.photo[-1].file_id, 
                                     caption="✅ <b>Ваш проект готов!</b>", parse_mode="HTML")
            else:
                await bot.send_message(target_user_id, f"✉️ <b>Сообщение от Шокиржона:</b>\n\n{message.text}", parse_mode="HTML")
            
            await message.answer("🚀 Отправлено клиенту!")
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке: {e}")

# --- ЗАПУСК ---
async def main():
    print("---")
    print("🚀 Shokirjon's Assistant запущен!")
    print("---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
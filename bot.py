import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo

# --- Конфигурация ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "9254789151:AAEZVzTwkydtrrW-DCTUn37VX4cjx589KW0")
# Ссылка на ваш Web App, размещенный на GitHub Pages
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://ВАШ_ЛОГИН.github.io/ВАШ_РЕПОЗИТОРИЙ/index.html")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет сообщение с кнопкой для запуска Web App."""
    # Создаем клавиатуру с кнопкой Web App
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [types.KeyboardButton(
                text="🚀 Открыть Web App",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )]
        ]
    )
    await message.answer(
        "Нажмите на кнопку ниже, чтобы открыть приложение:",
        reply_markup=markup
    )

@dp.message(lambda message: message.web_app_data is not None)
async def handle_web_app_data(message: types.Message):
    """Обрабатывает данные, присланные из Web App через tg.sendData()."""
    # Получаем строку JSON, которую отправил Web App
    raw_data = message.web_app_data.data
    try:
        data = json.loads(raw_data)
        await message.answer(f"✅ Данные из Web App получены!\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        await message.answer(f"Получены данные (не JSON): {raw_data}")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

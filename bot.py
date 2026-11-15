import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
BOT_TOKEN = os.getenv("9254789151:AAEZVzTwkydtrrW-DCTUn37VX4cjx589KW0")
WEB_APP_URL = os.getenv("https://pokupkacom84-creator.github.io/mrkt-parser-bot/")

# Настройка логов
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем inline-кнопку
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Открыть панель управления", web_app=WebAppInfo(url=WEB_APP_URL))]
        ]
    )
    await message.answer(
        "Добро пожаловать в Mrkt Parser Bot!\nНажмите кнопку ниже, чтобы настроить парсинг товаров:",
        reply_markup=markup
    )

@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    raw_data = message.web_app_data.data
    try:
        data = json.loads(raw_data)
        logging.info(f"Получены данные от {message.from_user.id}: {data}")
        
        # Здесь можно добавить логику проверки данных (валидация)
        if "action" not in data:
            await message.answer("❌ Ошибка: неверный формат данных.")
            return

        # Отвечаем пользователю
        await message.answer(f"✅ Данные приняты в работу!\nВы отправили: {data.get('action')}")
        
        # TODO: Передать данные в ваш парсер (например, в Celery или asyncio.create_task)

    except json.JSONDecodeError:
        await message.answer("❌ Ошибка: получен невалидный JSON.")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("❌ Произошла внутренняя ошибка при обработке данных.")

async def main():
    logging.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

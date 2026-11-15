import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp
from db import Database
from parser import MrktParser

logging.basicConfig(level=logging.INFO)

# FILL: вставь токен от @BotFather
BOT_TOKEN = "9254789151:AAEZVzTwkydtrrW-DCTUn37VX4cjx589KW0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()
parser = MrktParser()

# ─── /start ───────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск по рынку",   callback_data="menu_search")
    kb.button(text="➕ Добавить трекер",   callback_data="menu_tracker")
    kb.button(text="📋 Мои отслеживания", callback_data="menu_my")
    kb.button(text="🔔 Вкл уведомления",  callback_data="notif_on")
    kb.button(text="🔕 Выкл уведомления", callback_data="notif_off")
    kb.button(text="⚙️ Фильтры",          callback_data="menu_filter")
    kb.adjust(2)
    await message.answer(
        "👾 <b>MRKT Parser</b>\n\nМониторю новые листинги на GetGems (MRKT).\nВыбери действие:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

# ─── Уведомления вкл/выкл ─────────────────────────────────
@dp.callback_query(lambda c: c.data == "notif_on")
async def notif_on(call: CallbackQuery):
    db.set_notifications(call.from_user.id, True)
    await call.answer("✅ Уведомления включены")

@dp.callback_query(lambda c: c.data == "notif_off")
async def notif_off(call: CallbackQuery):
    db.set_notifications(call.from_user.id, False)
    await call.answer("🔕 Уведомления выключены")

# ─── Фильтры ──────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "menu_filter")
async def menu_filter(call: CallbackQuery):
    user_id = call.from_user.id
    f = db.get_filter(user_id)
    text = (
        f"⚙️ <b>Текущие фильтры</b>\n\n"
        f"Коллекция: <code>{f.get('collection', 'любая')}</code>\n"
        f"Макс цена: <code>{f.get('max_price', '∞')} TON</code>\n\n"
        f"Команды:\n"
        f"/setcollection &lt;название&gt;\n"
        f"/setprice &lt;макс TON&gt;\n"
        f"/resetfilter"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@dp.message(Command("setcollection"))
async def set_collection(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /setcollection Money Pot")
        return
    db.set_filter(message.from_user.id, "collection", args[1])
    await message.answer(f"✅ Коллекция: <code>{args[1]}</code>", parse_mode="HTML")

@dp.message(Command("setprice"))
async def set_price(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].replace(".", "").isdigit():
        await message.answer("Использование: /setprice 10.5")
        return
    db.set_filter(message.from_user.id, "max_price", float(args[1]))
    await message.answer(f"✅ Макс цена: <code>{args[1]} TON</code>", parse_mode="HTML")

@dp.message(Command("resetfilter"))
async def reset_filter(message: Message):
    db.reset_filter(message.from_user.id)
    await message.answer("✅ Фильтры сброшены")

# ─── Мои отслеживания ─────────────────────────────────────
@dp.callback_query(lambda c: c.data == "menu_my")
async def menu_my(call: CallbackQuery):
    items = db.get_tracked(call.from_user.id)
    if not items:
        await call.message.answer("📋 Нет отслеживаний. Добавь через ➕ Добавить трекер")
        await call.answer()
        return
    text = "📋 <b>Твои отслеживания:</b>\n\n"
    for item in items:
        text += f"• {item['collection']} #{item['number']} — {item['price']} TON\n"
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

# ─── Трекер ───────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "menu_tracker")
async def menu_tracker(call: CallbackQuery):
    await call.message.answer(
        "➕ Отправь команду:\n/track &lt;коллекция&gt; &lt;номер&gt;\n\nПример:\n/track MoneyPot 5736",
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(Command("track"))
async def track_nft(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /track MoneyPot 5736")
        return
    collection, number = args[1], args[2]
    db.add_tracked(message.from_user.id, collection, number)
    await message.answer(f"✅ Отслеживаю <code>{collection} #{number}</code>", parse_mode="HTML")

# ─── Поиск ────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "menu_search")
async def menu_search(call: CallbackQuery):
    await call.message.answer(
        "🔍 Отправь:\n/search &lt;коллекция&gt;\n\nПример:\n/search Money Pot",
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(Command("search"))
async def search_nft(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /search Money Pot")
        return
    await message.answer("⏳ Ищу...")
    results = await parser.search_collection(args[1], limit=5)
    if not results:
        await message.answer("❌ Ничего не найдено")
        return
    for nft in results:
        await send_nft_card(message.chat.id, nft)

# ─── Отправка карточки NFT ────────────────────────────────
async def send_nft_card(chat_id: int, nft: dict):
    traits = nft.get("traits", {})
    floor  = nft.get("floor_collection", 0)
    price  = nft.get("price", 0)
    pct    = ((price - floor) / floor * 100) if floor else 0
    sign   = "+" if pct >= 0 else ""

    text = (
        f"<b>{nft.get('name', '—')}</b>\n"
        f"🏪 Площадка: MRKT\n"
        f"коллекция: {nft.get('collection', '—')}\n"
        f"номер: #{nft.get('number', '—')}\n"
        f"модель: {traits.get('model', '—')}\n"
        f"фон: {traits.get('background', '—')}\n"
        f"цена: <b>{price} TON</b>\n"
        f"🏷 Флор NFT: {floor} TON ({sign}{pct:.1f}% к флору)\n"
    )
    if nft.get("floor_model"):
        text += f"🧩 Флор модели: {nft['floor_model']} TON\n"
    if nft.get("url"):
        text += f'\n<a href="{nft["url"]}">открыть лот на MRKT</a>'

    if nft.get("image"):
        await bot.send_photo(chat_id, nft["image"], caption=text, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML")

# ─── Фоновый мониторинг ───────────────────────────────────
async def monitor_loop():
    seen = set()
    while True:
        try:
            listings = await parser.get_new_listings()
            for nft in listings:
                nft_id = nft.get("id")
                if nft_id in seen:
                    continue
                seen.add(nft_id)
                # не копим больше 10000 id
                if len(seen) > 10000:
                    seen.pop()

                users = db.get_subscribed_users()
                for user_id, user_filter in users:
                    if not passes_filter(nft, user_filter):
                        continue
                    await send_nft_card(user_id, nft)
        except Exception as e:
            logging.error(f"monitor error: {e}")
        await asyncio.sleep(15)  # поллинг каждые 15 сек

def passes_filter(nft: dict, f: dict) -> bool:
    if f.get("collection"):
        if f["collection"].lower() not in nft.get("collection", "").lower():
            return False
    if f.get("max_price"):
        if nft.get("price", 9999) > f["max_price"]:
            return False
    return True

# ─── Main ─────────────────────────────────────────────────
async def main():
    asyncio.create_task(monitor_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
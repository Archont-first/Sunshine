import json
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DATA_FILE = "clients.json"
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()

waiting_for_apartment = set()


def load_clients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_clients(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


clients = load_clients()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in clients:
        waiting_for_apartment.add(user_id)
        await message.answer("Введите номер апартамента:")
    else:
        await message.answer("Вы уже зарегистрированы. Ожидайте рассылку.")


@dp.message()
async def process_message(message: Message):
    user_id = str(message.from_user.id)
    if user_id in waiting_for_apartment:
        clients[user_id] = {
            "username": message.from_user.username,
            "apartment": message.text.strip()
        }
        save_clients(clients)
        waiting_for_apartment.remove(user_id)
        await message.answer("Спасибо! Вы зарегистрированы.")
    elif message.text in {"Конечно", "Нет, спасибо"}:
        await handle_response(message)


async def handle_response(message: Message):
    if message.text == "Конечно":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Пончики"), KeyboardButton("Кофе"))
        await message.answer("Что желаете?", reply_markup=markup)
    else:
        await message.answer("Хорошего дня!")


async def send_offer():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Конечно"), KeyboardButton("Нет, спасибо"))
    for user_id in clients:
        try:
            await bot.send_message(user_id, "Хотите начать свой день с кофе?", reply_markup=markup)
        except Exception as e:
            print(f"Не удалось отправить сообщение {user_id}: {e}")


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_offer, "interval", days=2)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

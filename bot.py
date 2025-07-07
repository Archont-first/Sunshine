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
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
import telebot
from telebot import types

# Настройки
DATA_FILE = "clients.json"  # База клиентов
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ Токен бота не найден! Добавь его в .env")

bot = telebot.TeleBot(TOKEN)
waiting_for_apartment = set()  # Для хранения ID пользователей, которые вводят номер апартамента

# Загрузка базы клиентов
def load_clients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохранение базы клиентов
def save_clients(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

clients = load_clients()

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in clients:
        waiting_for_apartment.add(user_id)
        bot.send_message(message.chat.id, "☕ Добро пожаловать! Введите номер апартамента:")
    else:
        bot.send_message(message.chat.id, "✅ Вы уже зарегистрированы. Ожидайте рассылку!")

# Обработка сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    # Если пользователь вводит номер апартамента
    if user_id in waiting_for_apartment:
        clients[user_id] = {
            "username": message.from_user.username,
            "apartment": text,
        }
        save_clients(clients)
        waiting_for_apartment.remove(user_id)
        bot.send_message(message.chat.id, "✅ Спасибо! Теперь вы в базе. Ожидайте утренний кофе!")
    
    # Если отвечает на рассылку
    elif text == "Конечно":
        show_menu(message)
    elif text == "Нет, спасибо":
        bot.send_message(message.chat.id, "☀️ Хорошего дня!")
    
    # Если выбирает из меню
    elif text in ["Пончики", "Кофе"]:
        send_price(message)

# Показ меню
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Пончики"), types.KeyboardButton("Кофе"))
    bot.send_message(message.chat.id, "🍩 Выберите что-нибудь вкусное:", reply_markup=markup)

# Отправка цены и реквизитов
def send_price(message):
    item = message.text
    prices = {
        "Пончики": "5$",
        "Кофе": "3$",
    }
    if item in prices:
        bot.send_message(
            message.chat.id,
            f"💰 {item}: {prices[item]}\n"
            f"💳 Реквизиты для оплаты: **1234 5678 9012 3456**\n"
            f"📝 В комментарии укажите номер апартамента!"
        )

# Рассылка "Хотите кофе?"
def send_coffee_offer():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Конечно"), types.KeyboardButton("Нет, спасибо"))
    
    for user_id in clients:
        try:
            bot.send_message(user_id, "☕ Хотите начать день с кофе?", reply_markup=markup)
        except Exception as e:
            print(f"❌ Ошибка отправки для {user_id}: {e}")

# Запуск бота + рассылка
if __name__ == "__main__":
    bot.remove_webhook()
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_coffee_offer, "interval", days=1)  # Рассылка каждый день
    scheduler.start()
    print("Бот запущен! 🚀")
    bot.infinity_polling()

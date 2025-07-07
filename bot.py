import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
import telebot
from telebot import types

DATA_FILE = "clients.json"
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

bot = telebot.TeleBot(TOKEN)
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


@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = str(message.from_user.id)
    if user_id not in clients:
        waiting_for_apartment.add(user_id)
        bot.send_message(message.chat.id, "Введите номер апартамента:")
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы. Ожидайте рассылку.")


@bot.message_handler(func=lambda m: True)
def process_message(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    if user_id in waiting_for_apartment:
        clients[user_id] = {
            "username": message.from_user.username,
            "apartment": text,
        }
        save_clients(clients)
        waiting_for_apartment.remove(user_id)
        bot.send_message(message.chat.id, "Спасибо! Вы зарегистрированы.")
    elif text in {"Конечно", "Нет, спасибо"}:
        handle_response(message)
    elif text in {"Пончики", "Кофе"}:
        send_price_info(message)


def handle_response(message):
    if message.text == "Конечно":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Пончики"), types.KeyboardButton("Кофе"))
        bot.send_message(message.chat.id, "Что желаете?", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Хорошего дня!")


def send_price_info(message):
    prices = {"Пончики": "5$", "Кофе": "3$"}
    item = message.text
    price = prices.get(item)
    if price:
        bot.send_message(message.chat.id, f"Стоимость {item.lower()} {price}. Оплата на счёт 123-456.")


def send_offer():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Конечно"), types.KeyboardButton("Нет, спасибо"))
    for user_id in clients:
        try:
            bot.send_message(user_id, "Хотите начать свой день с кофе?", reply_markup=markup)
        except Exception as e:
            print(f"Не удалось отправить сообщение {user_id}: {e}")


def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_offer, "interval", days=2)
    scheduler.start()
    bot.infinity_polling()


if __name__ == "__main__":
    main()

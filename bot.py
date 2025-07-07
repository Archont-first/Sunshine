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

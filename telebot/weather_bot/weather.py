import os
import emoji
import telebot
import datetime
from telebot import types
from telebot import apihelper
from weather_data import Weather
from apscheduler.schedulers.background import BackgroundScheduler

login = ''
password = ''
ip = ''
port = ''

apihelper.proxy = {
    'https': 'socks5://{}:{}@{}:{}'.format(login, password, ip, port)
}

API_TOKEN = ""
bot = telebot.TeleBot(API_TOKEN)
data = Weather()

commands = {"commands": '/weather - погода сейчас\n'
                        '/sub - подписаться на уведомления\n'
                        '/unsub - отписаться от уведомлений\n'
                        '/map - карта осадков'}


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            f_message = open("history.txt", 'a', encoding='utf-8')
            f_message.write(datetime.datetime.fromtimestamp(int(m.date)).strftime("%d.%m.%Y %H:%M:%S") + "[" + str(
                m.chat.id) + "]" + m.chat.first_name + ": " + m.text + "\n")
            f_message.close()
bot.set_update_listener(listener)


@bot.message_handler(commands=['start', 'help'])
def start_cmd(m):
    cid = m.chat.id
    bot.send_message(cid, commands['commands'])


@bot.message_handler(commands=['weather'])
def select_source(m):
    cid = m.chat.id
    btns = []
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    call_back = ['openweathermap', 'yandex', 'yahoo']
    subjects = ['OpenWeatherMap', 'Yandex', 'Yahoo']
    for data, text in zip(call_back, subjects):
        data = types.InlineKeyboardButton(text=text, callback_data=data)
        btns.append(data)
    keyboard.add(*btns)
    bot.send_message(cid, "Выберите источник погоды:", reply_markup=keyboard)


@bot.message_handler(commands=['sub'])
def sub(m):
    cid = m.chat.id
    sub = [line.rstrip('\n') for line in open("sub.txt", 'rt')]
    if str(cid) in sub:
        bot.send_message(cid, "Вы уже подписаны...")
    else:
        with open("sub.txt", 'a') as f:
            f.write(str(cid) + "\n")
        bot.send_message(cid, "Вы успешно подписаны!")


@bot.message_handler(commands=['unsub'])
def unsub(m):
    cid = m.chat.id
    with open("sub.txt", 'r') as f:
        lines = f.readlines()
        h = str(cid) + "\n"
        if h in lines:
            lines.remove(h)
            with open("sub.txt", 'w') as f2:
                f2.writelines(lines)
                bot.send_message(cid, "Вы отписались :с")
        else:
            bot.send_message(cid, "Вы еще не подписаны...")


@bot.message_handler(commands=['map'])
def rain_map(m):
    cid = m.chat.id
    # admin m.chat.id
    if cid == 123:
        await bot.send_chat_action(cid, 'upload_photo')
        data.rain_map()
        if os.path.exists("rain.png"):
            bot.send_photo(cid, types.InputFile("rain.png"))


@bot.callback_query_handler(func=lambda call: True)
def ans(call):
    kb = types.InlineKeyboardMarkup()
    cid = call.message.chat.id
    mid = call.message.message_id
    if call.data == "openweathermap":
        bot.edit_message_text(data.openweathermap(), cid, mid, reply_markup=kb, parse_mode='Markdown')
    elif call.data == "yandex":
        bot.edit_message_text(data.yandex(), cid, mid, reply_markup=kb, parse_mode='Markdown')
    elif call.data == 'yahoo':
        bot.edit_message_text(data.yahoo(), cid, mid, reply_markup=kb, parse_mode='Markdown')


def weather_schedule():
    subs = [line.rstrip('\n') for line in open("sub.txt", 'r')]
    if os.stat("sub.txt").st_size != 0:
        for cid in subs:
            res = data.openweathermap() + "\n\n" + data.yandex() + "\n\n" + data.yahoo()
            bot.send_message(cid, res, parse_mode='Markdown')


@bot.message_handler(
    content_types=['photo', 'video', 'voice', 'location', 'contact', 'sticker', 'audio', 'document', 'text'])
def command_echo(m):
    cid = m.chat.id
    bot.send_message(cid, emoji.emojize(":thinking_face:") + "\nПопробуй команду /help\n")


if __name__ == "__main__":
    dt = datetime.datetime.now()
    # specific time to start sending notifications (18:00:00)
    dt = dt.replace(hour=18, minute=0, second=0, microsecond=0)
    scheduler = BackgroundScheduler()
    scheduler.add_job(weather_schedule, 'interval', hours=6, start_date=dt)
    scheduler.start()
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)

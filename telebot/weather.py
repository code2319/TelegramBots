import emoji
import telebot
import requests
import datetime
from telebot import types
from telebot import apihelper
from googletrans import Translator
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

commands = {"commands": '/weather - погода сейчас\n'
                        '/sub - подписаться на уведомления\n'
                        '/unsub - отписаться от уведомлений'}


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            f_message = open("history.txt", 'a')
            f_message.write(datetime.datetime.fromtimestamp(int(m.date)).strftime("%d.%m.%Y %H:%M:%S") + "[" + str(
                m.chat.id) + "]" + m.chat.first_name + ": " + m.text + "\n")
            f_message.close()
bot.set_update_listener(listener)


@bot.message_handler(commands=['start', 'help'])
def start_cmd(m):
    cid = m.chat.id
    bot.send_message(cid, commands['commands'])


# 60 req/min - max
def openweathermap():
    translator = Translator()
    API_KEY = ''
    s_city = "Moscow,RU"
    r = requests.get("http://api.openweathermap.org/data/2.5/find",
                     params={'q': s_city, 'units': 'metric', 'APPID': API_KEY})
    data = r.json()

    temp = data['list'][0]['main']
    wind = data['list'][0]['wind']['speed']
    clouds = data['list'][0]['clouds']['all']
    wtype = data['list'][0]['weather'][0]['main']
    wdesc = data['list'][0]['weather'][0]['description']

    wtype_tr = translator.translate(wtype, dest="ru").text + " ("
    wdesc_tr = translator.translate(wdesc, dest="ru").text + ")"

    res = "Температура: `" + str(temp['temp']) + "°`" + \
          "\nМинимальная: `" + str(temp['temp_min']) + "°`" + \
          "\nМаксимальная: `" + str(temp['temp_max']) + "°`" + \
          "\nДавление: `" + str(temp['pressure'] * 0.75) + " мм рт. ст.`" + \
          "\nВлажность: `" + str(temp['humidity']) + "%`" + \
          "\nВетер: `" + str(wind) + " (м/с)`" + \
          "\nОблачность: `" + str(clouds) + "%`" + \
          "\nСейчас: `" + wtype_tr + wdesc_tr + "`"
    return res


# 50 req/day - max
def yandex():
    API_KEY = ''
    url = 'https://api.weather.yandex.ru/v1/forecast?'

    headers = {
        'X-Yandex-API-Key': API_KEY
    }
    data = {
        'lat': 55.7,
        'lon': 37.6,
        'lang': 'ru_RU',
    }

    r = requests.get(url, headers=headers, data=data)
    data = r.json()

    temp = data['fact']['temp']
    feels_temp = data['fact']['feels_like']
    condition = data['fact']['condition']
    wind = data['fact']['wind_speed']
    pressure = data['fact']['pressure_mm']
    humidity = data['fact']['humidity']

    cond = {'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно с прояснениями',
            'overcast': 'пасмурно', 'partly-cloudy-and-light-rain': 'небольшой дождь',
            'partly-cloudy-and-rain': 'дождь', 'overcast-and-rain': 'сильный дождь',
            'overcast-thunderstorms-with-rain': 'сильный дождь, гроза', 'cloudy-and-light-rain': 'небольшой дождь',
            'overcast-and-light-rain': 'небольшой дождь', 'cloudy-and-rain': 'дождь',
            'overcast-and-wet-snow': 'дождь со снегом', 'partly-cloudy-and-light-snow': 'небольшой снег',
            'partly-cloudy-and-snow': 'снег', 'overcast-and-snow': 'снегопад',
            'cloudy-and-light-snow': 'небольшой снег', 'overcast-and-light-snow': 'небольшой снег',
            'cloudy-and-snow': 'снег'}

    res = "*По данным Яндекс.Погоды:*\nТемпература: `" + str(temp) + "°`" + \
          "\nОщущается как: `" + str(feels_temp) + "°`" + \
          "\nДавление: `" + str(pressure) + " мм рт. ст.`" + \
          "\nВлажность: `" + str(humidity) + "%`" + \
          "\nВетер: `" + str(wind) + " (м/с)`" + \
          "\nСейчас: `" + cond[condition] + "`"
    return res


@bot.message_handler(commands=['weather'])
def select_source(m):
    cid = m.chat.id
    btns = []
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    call_back = ['openweathermap', 'yandex']
    subjects = ['OpenWeatherMap', 'Yandex']
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


@bot.callback_query_handler(func=lambda call: True)
def ans(call):
    kb = types.InlineKeyboardMarkup()
    cid = call.message.chat.id
    mid = call.message.message_id
    if call.data == "openweathermap":
        bot.edit_message_text(openweathermap(), cid, mid, reply_markup=kb, parse_mode='Markdown')
    elif call.data == "yandex":
        bot.edit_message_text(yandex(), cid, mid, reply_markup=kb, parse_mode='Markdown')


def weather_schedule():
    subs = [line.rstrip('\n') for line in open("sub.txt", 'r')]
    for sub in subs:
        bot.send_message(sub, openweathermap(), parse_mode='Markdown')
        bot.send_message(sub, yandex(), parse_mode='Markdown')


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

import telebot
import requests
from googletrans import Translator
from apscheduler.schedulers.background import BackgroundScheduler

from telebot import apihelper

login = ''
password = ''
ip = ''
port = ''

apihelper.proxy = {
    'https': 'socks5://{}:{}@{}:{}'.format(login, password, ip, port)
}

API_TOKEN = ""
bot = telebot.TeleBot(API_TOKEN)

commands = {"commands": '/weather - погода сейчас'}

@bot.message_handler(commands=['start', 'help'])
def start_cmd(m):
    cid = m.chat.id
    bot.send_message(cid, commands['commands'])


def weather():
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
          "\nСейчас: `" + wtype_tr + wdesc_tr
    return res


@bot.message_handler(commands=['weather'])
def weather_now(m):
    cid = m.chat.id
    bot.send_message(cid, weather(), parse_mode='Markdown')


def weather_schedule():
    bot.send_message(123, weather(), parse_mode='Markdown')


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(weather_schedule, 'interval', hours=6)
    scheduler.start()
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)

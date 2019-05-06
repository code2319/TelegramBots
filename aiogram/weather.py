import requests
import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode, ContentType
from aiogram.utils.markdown import text, italic, code
from aiogram.utils.emoji import emojize
from googletrans import Translator
from apscheduler.schedulers.asyncio import AsyncIOScheduler

login = ''
password = ''
ip = ''
port = ''

PROXY_URL = f'socks5://{login}:{password}@{ip}:{port}'
API_TOKEN = ""

bot = Bot(token=API_TOKEN, proxy=PROXY_URL)
dp = Dispatcher(bot)

commands = {"commands": '/weather - погода сейчас\n'
                        '/subscribe - информация о погоде каждые 6 часов'}


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, commands['commands'])


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

    res = "*По данным OpenWeatherMap:*\nТемпература: `" + str(temp['temp']) + "°`" + \
          "\nМинимальная: `" + str(temp['temp_min']) + "°`" + \
          "\nМаксимальная: `" + str(temp['temp_max']) + "°`" + \
          "\nДавление: `" + str(temp['pressure'] * 0.75) + " мм рт. ст.`" + \
          "\nВлажность: `" + str(temp['humidity']) + "%`" + \
          "\nВетер: `" + str(wind) + " (м/с)`" + \
          "\nОблачность: `" + str(clouds) + "%`" + \
          "\nСейчас: `" + wtype_tr + wdesc_tr + "`"
    return res


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
            'partly-cloudy-and-snow': 'снег', 'overcast-and-snow': 'снегопад', 'cloudy-and-light-snow': 'небольшой снег',
            'overcast-and-light-snow': 'небольшой снег', 'cloudy-and-snow': 'снег'}

    res = "*По данным Яндекс.Погоды:*\nТемпература: `" + str(temp) + "°`" + \
        "\nОщущается как: `" + str(feels_temp) + "°`" + \
        "\nДавление: `" + str(pressure) + " мм рт. ст.`" + \
        "\nВлажность: `" + str(humidity) + "%`" + \
        "\nВетер: `" + str(wind) + " (м/с)`" + \
        "\nСейчас: `" + cond[condition] + "`"
    return res


@dp.message_handler(commands=['weather'])
async def select_source(m: types.Message):
    cid = m.chat.id
    btns = []
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    call_back = ['openweathermap', 'yandex']
    subjects = ['OpenWeatherMap', 'Yandex']
    for data, text in zip(call_back, subjects):
        data = types.InlineKeyboardButton(text=text, callback_data=data)
        btns.append(data)
    keyboard.add(*btns)
    await bot.send_message(cid, "Выберите источник погоды:", reply_markup=keyboard)


@dp.message_handler(commands=['subscribe'])
async def sub(m):
    cid = m.chat.id
    sub = [line.rstrip('\n') for line in open("sub.txt", 'rt')]
    if str(cid) in sub:
        await bot.send_message(cid, "Вы уже подписаны...")
    else:
        with open("sub.txt", 'a') as f:
            f.write(str(cid) + "\n")
        await bot.send_message(cid, "Вы успешно подписаны!")


@dp.callback_query_handler(lambda callback_query: True)
async def ans(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    cid = call.message.chat.id
    mid = call.message.message_id
    if call.data == "openweathermap":
        await bot.edit_message_text(openweathermap(), cid, mid, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif call.data == "yandex":
        await bot.edit_message_text(yandex(), cid, mid, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


async def weather_schedule():
    subs = [line.rstrip('\n') for line in open("sub.txt", 'r')]
    for sub in subs:
        await bot.send_message(sub, openweathermap(), parse_mode=ParseMode.MARKDOWN)
        await bot.send_message(sub, yandex(), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(msg: types.Message):
    message_text = text(emojize('Я не знаю, что с этим делать :astonished:'),
                        italic('\nЯ просто напомню,'), 'что есть',
                        code('команда'), '/help')

    if msg.content_type == "text":
        with open("history/history.txt", 'a') as f:
            f.write(str(msg.date) +
                    " [" + str(msg.chat.id) + "] " +
                    msg.chat.first_name + ": " +
                    msg.text + "\n")
            f.close()

    await msg.reply(message_text, parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    dt = datetime.datetime.now()
    # specific time to start sending notifications (18:00:00)
    dt = dt.replace(hour=18, minute=0, second=0, microsecond=0)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(weather_schedule, 'interval', hours=6, start_date=dt)
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)

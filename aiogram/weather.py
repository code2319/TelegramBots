import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode, ContentType
from aiogram.utils.markdown import text, italic, code
from aiogram.utils.emoji import emojize
from googletrans import Translator


API_TOKEN = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

commands = {"commands": '/weather - погода сейчас'}


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, commands['commands'])


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

    res = text("Температура: " + code(str(temp['temp']) + "°") + \
               "\nМинимальная: " + code(str(temp['temp_min']) + "°") + \
               "\nМаксимальная: " + code(str(temp['temp_max']) + "°") + \
               "\nДавление: " + code(str(temp['pressure'] * 0.75) + " мм рт. ст.") + \
               "\nВлажность: " + code(str(temp['humidity']) + "%") + \
               "\nВетер: " + code(str(wind) + " (м/с)") + \
               "\nОблачность: " + code(str(clouds) + "%") + \
               "\nСейчас: " + code(wtype_tr + wdesc_tr))
    return res


@dp.message_handler(commands=['weather'])
async def weather_now(m):
    cid = m.chat.id
    await bot.send_message(cid, weather(), parse_mode=ParseMode.MARKDOWN)


async def weather_schedule():
    await bot.send_message(123, weather(), parse_mode=ParseMode.MARKDOWN)


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
    scheduler = AsyncIOScheduler()
    scheduler.add_job(weather_schedule, 'interval', hours=6)
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)

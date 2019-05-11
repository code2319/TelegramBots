import os
import logging
import datetime
from weather_data import Weather
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode, ContentType
from aiogram.utils.markdown import text, italic, code
from aiogram.utils.emoji import emojize
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(
        filename="source/botlog.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

login = ''
password = ''
ip = ''
port = ''

PROXY_URL = f'socks5://{login}:{password}@{ip}:{port}'
API_TOKEN = ""

bot = Bot(token=API_TOKEN, proxy=PROXY_URL)
dp = Dispatcher(bot)
data = Weather()

commands = {"commands": '/weather - погода сейчас\n'
                        '/sub - подписаться на уведомления\n'
                        '/unsub - отписаться от уведомлений\n'
                        '/map - карта осадков'}


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, commands['commands'])


@dp.message_handler(commands=['weather'])
async def select_source(m: types.Message):
    cid = m.chat.id
    btns = []
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    call_back = ['openweathermap', 'yandex', 'yahoo', 'accuweather']
    subjects = ['OpenWeatherMap', 'Yandex', 'Yahoo', 'AccuWeather']
    for data, text in zip(call_back, subjects):
        data = types.InlineKeyboardButton(text=text, callback_data=data)
        btns.append(data)
    keyboard.add(*btns)
    await bot.send_message(cid, "Выберите источник погоды:", reply_markup=keyboard)


@dp.message_handler(commands=['sub'])
async def sub(m):
    cid = m.chat.id
    sub = [line.rstrip('\n') for line in open("source/sub.txt", 'rt')]
    if str(cid) in sub:
        await bot.send_message(cid, "Вы уже подписаны...")
    else:
        with open("source/sub.txt", 'a') as f:
            f.write(str(cid) + "\n")
        await bot.send_message(cid, "Вы успешно подписаны!")


@dp.message_handler(commands=['unsub'])
async def unsub(m):
    cid = m.chat.id
    with open("source/sub.txt", 'r') as f:
        lines = f.readlines()
        h = str(cid) + "\n"
        if h in lines:
            lines.remove(h)
            with open("source/sub.txt", 'w') as f2:
                f2.writelines(lines)
                await bot.send_message(cid, "Вы отписались :с")
        else:
            await bot.send_message(cid, "Вы еще не подписаны...")


@dp.message_handler(commands=['map'])
async def rain_map(m):
    cid = m.chat.id
    # admin m.chat.id
    if cid == 123:
        await bot.send_chat_action(cid, 'upload_photo')
        data.rain_map()
        if os.path.exists("source/rain.png"):
            await bot.send_photo(cid, types.InputFile("source/rain.png"))


@dp.callback_query_handler(lambda callback_query: True)
async def ans(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    cid = call.message.chat.id
    mid = call.message.message_id
    if call.data == "openweathermap":
        await bot.edit_message_text(data.openweathermap(), cid, mid, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif call.data == "yandex":
        await bot.edit_message_text(data.yandex(), cid, mid, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif call.data == "yahoo":
        await bot.edit_message_text(data.yahoo(), cid, mid, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif call.data == "accuweather":
        await bot.edit_message_text(data.accuweather(), cid, mid, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


async def weather_schedule():
    subs = [line.rstrip('\n') for line in open("source/sub.txt", 'r')]
    if os.stat("source/sub.txt").st_size != 0:
        for cid in subs:
            res = data.openweathermap() + "\n\n" + data.yandex() + "\n\n" + data.yahoo() + "\n\n" + data.accuweather()
            await bot.send_message(cid, res, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(msg: types.Message):
    message_text = text(emojize('Я не знаю, что с этим делать :astonished:'),
                        italic('\nЯ просто напомню,'), 'что есть',
                        code('команда'), '/help')

    if msg.content_type == "text":
        with open("source/history.txt", 'a') as f:
            f.write(str(msg.date) +
                    " [" + str(msg.chat.id) + "] " +
                    msg.chat.first_name + ": " +
                    msg.text + "\n")

    await msg.reply(message_text, parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    dt = datetime.datetime.now()
    # specific time to start sending notifications (18:00:00)
    dt = dt.replace(hour=18, minute=0, second=0, microsecond=0)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(weather_schedule, 'interval', hours=6, start_date=dt)
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)

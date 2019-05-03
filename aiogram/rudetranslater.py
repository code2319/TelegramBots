import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode, ContentType
from aiogram.utils.markdown import text, italic, code
from aiogram.utils.emoji import emojize
from googletrans import Translator
from gtts import gTTS

API_TOKEN = ''

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

commands = {"commands": '/ru - перевод на немецкий\n/de - перевод на русский'}


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, commands['commands'])


@dp.message_handler(commands=['ru'])
async def from_ru_to_de(message: types.Message):
    cid = message.chat.id
    translator = Translator()
    ts_text = translator.translate(message.text[4:], dest='de').text
    if ts_text != "":
        await bot.send_message(cid, ts_text)
        tts = gTTS(text=ts_text, lang='de', lang_check=True)
        tts.save("voice/ans.oga")
        tts_sl = gTTS(text=ts_text, lang='de', lang_check=True, slow=True)
        tts_sl.save("voice/ans_sl.oga")
        try:
            with open('voice/ans.oga', 'rb') as f1, open("voice/ans_sl.oga", 'rb') as f2:
                await bot.send_voice(cid, f1, None)
                await bot.send_voice(cid, f2, None)
        except Exception as e:
            await bot.send_message(cid, str(e))
    else:
        await bot.send_message(cid, "/ru <текст>")


@dp.message_handler(commands=['de'])
async def from_de_to_ru(message: types.Message):
    cid = message.chat.id
    translator = Translator()
    ts_text = translator.translate(message.text[4:], dest='ru').text
    if ts_text is not "":
        await bot.send_message(cid, ts_text)
    else:
        await bot.send_message(cid, "/de <текст>")


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
    executor.start_polling(dp, skip_updates=True)
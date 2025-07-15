import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputMediaPhoto, InputMediaVideo
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
user_data = {}

logging.basicConfig(level=logging.INFO)

@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_message(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        user_data[uid] = {"media": [], "text": ""}

    if message.photo:
        file_id = message.photo[-1].file_id
        user_data[uid]["media"].append(InputMediaPhoto(media=file_id))
    elif message.video:
        file_id = message.video.file_id
        user_data[uid]["media"].append(InputMediaVideo(media=file_id))
    elif message.text:
        user_data[uid]["text"] = message.text

    await message.reply("✅ Сообщение сохранено.")

@dp.message_handler(commands=["publish"])
async def publish(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid]["media"]:
        await bot.send_media_group(CHANNEL_ID, user_data[uid]["media"])
        await bot.send_message(CHANNEL_ID, user_data[uid]["text"])
        await message.reply("🚀 Опубликовано.")
        del user_data[uid]
    else:
        await message.reply("Нет данных для публикации.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
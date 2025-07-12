
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputMediaPhoto, InputMediaVideo
import os

BOT_TOKEN = "7835488554:AAE4W01kbQtbvd3rCFaf2YKVr4FbeWBfKa4"
ADMIN_ID = 8195384163
CHANNEL_ID = -1002859167638  # Замените на фактический ID вашего канала, если он другой

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class Form(StatesGroup):
    media = State()
    wechat_vin_info = State()
    brand_model = State()
    year_month = State()
    mileage = State()
    drive = State()
    color = State()
    options = State()
    condition = State()
    dealer_price = State()

user_data = {}

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_data[message.from_user.id] = {
        "media": [],
        "wechat": [],
        "vin": [],
        "info_list": [],
        "text": {}
    }
    await message.answer("Загрузите фото/видео автомобиля. После этого нажмите 'Далее ▶️'.", reply_markup=next_button())
    await Form.media.set()

def next_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Далее ▶️", callback_data="next"))
    return markup

@dp.message_handler(content_types=types.ContentType.ANY, state=Form.media)
async def collect_media(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if message.photo:
        user_data[uid]["media"].append(message.photo[-1].file_id)
    elif message.video:
        user_data[uid]["media"].append(message.video.file_id)
    await message.answer("Файл получен. Нажмите 'Далее ▶️' когда готовы.", reply_markup=next_button())

@dp.callback_query_handler(lambda c: c.data == 'next', state=Form.media)
async def next_to_wechat(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Загрузите фото WeChat, VIN и инфо лист.")
    await Form.wechat_vin_info.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.wechat_vin_info)
async def collect_wechat_vin_info(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if len(user_data[uid]["wechat"]) < 1:
        user_data[uid]["wechat"].append(message.photo[-1].file_id)
    elif len(user_data[uid]["vin"]) < 1:
        user_data[uid]["vin"].append(message.photo[-1].file_id)
    else:
        user_data[uid]["info_list"].append(message.photo[-1].file_id)
    if len(user_data[uid]["info_list"]) >= 1:
        await message.answer("Укажите марку и модель.")
        await Form.brand_model.set()

@dp.message_handler(state=Form.brand_model)
async def brand_model(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["brand_model"] = message.text
    await message.answer("Год и месяц выпуска:")
    await Form.year_month.set()

@dp.message_handler(state=Form.year_month)
async def year_month(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["year_month"] = message.text
    await message.answer("Пробег:")
    await Form.mileage.set()

@dp.message_handler(state=Form.mileage)
async def mileage(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["mileage"] = message.text
    await message.answer("Привод:")
    await Form.drive.set()

@dp.message_handler(state=Form.drive)
async def drive(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["drive"] = message.text
    await message.answer("Цвет кузова/салона:")
    await Form.color.set()

@dp.message_handler(state=Form.color)
async def color(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["color"] = message.text
    await message.answer("Дополнительные опции:")
    await Form.options.set()

@dp.message_handler(state=Form.options)
async def options(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["options"] = message.text
    await message.answer("Состояние авто:")
    await Form.condition.set()

@dp.message_handler(state=Form.condition)
async def condition(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]["text"]["condition"] = message.text
    await message.answer("Цена от дилера (числом):")
    await Form.dealer_price.set()

@dp.message_handler(state=Form.dealer_price)
async def dealer_price(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    dealer_price = int(message.text)
    final_price = dealer_price + 15000
    user_data[uid]["text"]["dealer_price"] = dealer_price
    user_data[uid]["text"]["final_price"] = final_price

    media = [InputMediaPhoto(m) if m.startswith("Ag") else InputMediaVideo(m) for m in user_data[uid]["media"]]
    caption = f"""
Марка и модель: {user_data[uid]["text"]["brand_model"]}
Год и месяц выпуска: {user_data[uid]["text"]["year_month"]}
Пробег: {user_data[uid]["text"]["mileage"]}
Привод: {user_data[uid]["text"]["drive"]}
Цвет: {user_data[uid]["text"]["color"]}
Опции: {user_data[uid]["text"]["options"]}
Состояние: {user_data[uid]["text"]["condition"]}
💰 Цена: {final_price} ¥
    """

    await bot.send_media_group(ADMIN_ID, media)
    await bot.send_message(ADMIN_ID, caption.strip(), reply_markup=admin_keyboard(uid))
    await message.answer("Спасибо! Заявка отправлена админу.")
    await state.finish()

def admin_keyboard(uid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish:{uid}"))
    markup.add(types.InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{uid}"))
    return markup

@dp.callback_query_handler(lambda c: c.data.startswith("publish:"))
async def publish_handler(callback_query: types.CallbackQuery):
    uid = int(callback_query.data.split(":")[1])
    media = [InputMediaPhoto(m) if m.startswith("Ag") else InputMediaVideo(m) for m in user_data[uid]["media"]]
    text = user_data[uid]["text"]
    caption = f"""
Марка и модель: {text["brand_model"]}
Год и месяц выпуска: {text["year_month"]}
Пробег: {text["mileage"]}
Привод: {text["drive"]}
Цвет: {text["color"]}
Опции: {text["options"]}
Состояние: {text["condition"]}
💰 Цена: {text["final_price"]} ¥
    """
    await bot.send_media_group(CHANNEL_ID, media)
    await bot.send_message(CHANNEL_ID, caption.strip())
    await callback_query.message.answer("Опубликовано ✅")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

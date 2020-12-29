import config
import os
import logging
import urllib.request
import asyncio
import calendar
import re

from day_counter import time_period
from transliterate import translit
from datetime import date, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from sqliter import Client
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# Инициализируем работу с базой данных
db = Client()

# задаем уровень логов
logging.basicConfig(level=logging.INFO)

# инициализируем бота
bot = Bot(token=config.API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    dob = State()  # Will be represented in storage as 'Form:dob'
    start_date = State()  # Will be represented in storage as 'Form:start_date'
    image = State()  # Will be represented in storage as 'Form:image'


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Все операции отменены.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['showactive'])
async def cmd_showactive(message: types.Message):
    """
    This handler will be called when user sends `/showactive` command
    """
    search_results = db.get_activeclients(message.from_user.id)
    await message.answer(search_results, parse_mode='HTML')


@dp.message_handler(commands=['showall'])
async def cmd_showall(message: types.Message):
    """
    This handler will be called when user sends `/showall` command
    """
    search_results = db.get_allclients(message.from_user.id)
    await message.answer(search_results, parse_mode='HTML')


@dp.message_handler(commands=['add'])
async def cmd_add(message: types.Message):
    """
    This handler will be called when user sends `/add` command
    """
    # Set state
    await Form.name.set()
    await message.reply("Введите ФИО нового клиента")


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process client name
    """
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.reply("А теперь его/её дату рождения")


@dp.message_handler(state=Form.dob)
async def process_dob(message: types.Message, state: FSMContext):
    """
    Process client date of birth
    """
    async with state.proxy() as data:
        data['dob'] = message.text

    await Form.next()
    await message.reply("С какого числа начинается работа с клиентом?")


@dp.message_handler(state=Form.start_date)
async def process_startdate(message: types.Message, state: FSMContext):
    """
    Process client start date
    """
    async with state.proxy() as data:
        data['start_date'] = message.text

    await Form.next()
    await message.reply("А теперь отправьте мне фотографию клиента, я её сохраню у себя в базе")


@dp.message_handler(state=Form.image, content_types=["photo"])
async def process_startdate(message: types.Message, state: FSMContext):
    """
    Process client photo
    """
    async with state.proxy() as data:
        data['file_id'] = await bot.get_file(message.photo[-1].file_id)

        # Process client's name
        nm0 = data['name']
        fullname = str(nm0).title().strip().replace('  ', ' ')

        # Process date of birth
        bdt = re.search(r"(?P<day>\d{1,2})[^a-zA-Z\d](?P<month>\d{1,2})[^a-zA-Z\d](?P<year>\d{2,4})", str(data['dob']))
        cy = date.today().year % 100
        by = int(bdt.group('year')) % 100
        if by > cy:
            byr = 1900 + by
        else:
            byr = 2000 + by
        birth_date = date(year=byr, month=int(bdt.group('month')), day=int(bdt.group('day')))


        # Process date of payment
        sdt = re.search(r"(?P<day>\d{1,2})[^a-zA-Z\d](?P<month>\d{1,2})[^a-zA-Z\d](?P<year>\d{2,4})", str(data['start_date']))
        start_date = date(year=int(sdt.group('year')), month=int(sdt.group('month')), day=int(sdt.group('day')))

        # Process image
        file_id = data['file_id']

        # Prepare complete file URL for downloading
        file_url = str(file_id["file_path"]).split('/')
        extension = file_url[-1].split('.')

        # Create folder
        uid = str(message.from_user.id)
        folder_path = os.path.join(os.getcwd(), uid)
        os.makedirs(folder_path, exist_ok=True)

        # Build filename
        latin_fullname = str(translit(fullname, 'ru', reversed=True)).replace(' ', '_').replace("'", '').upper()
        set_id = db.get_maxid() + 1
        file_name = f'{set_id}_{latin_fullname}.{extension[-1]}'
        destination = os.path.join(folder_path, file_name)
        urllib.request.urlretrieve(f"https://api.telegram.org/file/bot{config.API_TOKEN}/{file_id['file_path']}", filename=destination)

        # Add client to database
        operator_id = message.from_user.id
        result_message = db.add_client(operator_id, fullname, birth_date, start_date, file_name)

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        # And send message
        await bot.send_message(
            message.from_user.id,
            result_message,
            reply_markup=markup,
            parse_mode='HTML',
        )

    # Finish conversation
    await state.finish()


@dp.message_handler()
async def find_client(message: types.Message):
    """
    This handler will return a list of clients
    """
    query = str(message.text).replace('/id', '')
    search_results = db.search_clients(query)
    if search_results[1] == 1:
        client_id = int(search_results[2])
        status = int(search_results[3])
        inline_btn_1 = InlineKeyboardButton('🖼️ Показать фото', callback_data=f'/id{client_id}')
        if status == 0:
            inline_btn_2 = InlineKeyboardButton('👍 Активировать!', callback_data=f'activate {client_id}')
        else:
            inline_btn_2 = InlineKeyboardButton('👎 Деактивировать!', callback_data=f'deactivate {client_id}')
        inline_kb1 = InlineKeyboardMarkup(row_width=2).add(inline_btn_1, inline_btn_2)
        await message.answer(search_results[0], parse_mode='HTML', reply_markup=inline_kb1)
    else:
        await message.answer(search_results[0], parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('/id'))
async def process_callback_button1(callback_query: types.CallbackQuery):
    client_id = int(str(callback_query.data).replace('/id', ''))
    client = db.search_clients(client_id)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_photo(callback_query.from_user.id, photo=open(os.path.join(os.getcwd(), str(callback_query.from_user.id), client[4]), 'rb'))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('activate'))
async def process_callback_button21(callback_query: types.CallbackQuery):
    user_id = str(callback_query.data).split()
    uid = int(user_id[-1])
    confirmation = db.activate_client(uid, callback_query.from_user.id, start_date=date.today())
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, confirmation, parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('deactivate'))
async def process_callback_button22(callback_query: types.CallbackQuery):
    user_id = str(callback_query.data).split()
    uid = int(user_id[-1])
    confirmation = db.deactivate_client(uid, callback_query.from_user.id, end_date=date.today())
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, confirmation, parse_mode='HTML')


# отправляем сообщение о приближающихся датах оплаты
async def payment_notification(wait_for):
    while True:

        await asyncio.sleep(wait_for)

        search_results = db.get_reminderlist('822653560')
        result_list = list()
        for client in search_results:
            payment_day = date.fromisoformat(client['start_date']).day
            if payment_day >= date.today().day:
                payment_date = date.today().replace(day=payment_day)
            else:
                payment_date = date.today().replace(day=payment_day) + timedelta(days=calendar.monthrange(year=date.today().year, month=date.today().month)[1])
            days_left = payment_date - date.today()
            if days_left.days <= 2:
                client_info = time_period(client['fullname'], client['birth_date'], client['start_date'], client['end_date'])
                result_list.append(client_info)
        if len(result_list):
            message_part1 = "<b>💰 ПРИБЛИЖАЮТСЯ ДАТЫ ОПЛАТЫ 💰</b>\n\n"
            message_text = message_part1 + '\n\n'.join(result_list)
            await bot.send_message(text=message_text, chat_id='789561316', parse_mode='HTML')
            await bot.send_message(text=message_text, chat_id='822653560', parse_mode='HTML')
        else:
            pass


if __name__ == '__main__':
    dp.loop.create_task(payment_notification(60*60*24))  # пока что оставим 10 секунд (в качестве теста)
    executor.start_polling(dp, skip_updates=True)

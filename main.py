import asyncio
import os
from datetime import datetime
from time import sleep, localtime
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, TelegramObject, Update, \
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from sqlalchemy import Column, Integer, String, DateTime, func, select, ForeignKey, Boolean
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

token = '7874928619:AAGq2IJMNjvUjpJ2vU3N9L85frcGhhykDKU'
bot = Bot(token=token)
dp = Dispatcher()

# ------------------------------------database--------------------------------------------------------------------------#
DATABASE_URL = "sqlite+aiosqlite:///database.sqlite3"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


# ----------------------------------create table and its volumes--------------------------------------------------------#
class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False, unique=True)
    FIO = Column(String, nullable=True)
    tg_name = Column(String, nullable=False)
    tg_username = Column(String, nullable=True)
    tg_number = Column(Integer, unique=True, nullable=True)
    gender = Column(String, nullable=True)
    born_year = Column(Integer, nullable=True)
    language = Column(String, nullable=False)
    role = Column(String, nullable=False, default='User')
    registered = Column(Boolean, nullable=False, default=False)


class Registering(Base):
    __tablename__ = 'Register'
    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    number = Column(String, nullable=False)
    course = Column(String, nullable=False)
    born_year = Column(String, nullable=False)
    level = Column(String, nullable=True, default='Not chosen')
    time = Column(String, nullable=True)
    telegram_information = Column(Integer, ForeignKey(User.tg_id, ondelete='CASCADE'))
    is_connected = Column(Boolean, nullable=True, default=False)
    registered_time = Column(DateTime, default=func.now())


class Results_English(Base):
    __tablename__ = 'Results_English'
    id = Column(Integer, primary_key=True)
    fullname = Column(String, nullable=False)
    writing = Column(String, nullable=False)
    speaking = Column(String, nullable=False)
    reading = Column(String, nullable=False)
    listening = Column(String, nullable=False)
    Overall_Band = Column(String, nullable=False)
    image = Column(String, nullable=False)


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -------------------------------------Database Functions---------------------------------------------------------------#
async def get_user_language(tg_id) -> str:
    async with async_session() as session:
        stmt = select(User.language).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user_language = result.scalar_one_or_none()
        return user_language


async def add_user(tg_id: int, username: str, name: str) -> None:
    async with async_session() as session:
        new_user = User(tg_id=tg_id, tg_username=username, tg_name=name, language="en"  # default language if needed
                        )
        session.add(new_user)
        await session.commit()


async def set_user_language(tg_id, language: str):
    async with async_session() as session:
        # Check if the user exists
        stmt = select(User).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        # If user exists, update their language
        if user:
            user.language = language
        else:
            # If user does not exist, create a new entry
            session.add(User(tg_id=tg_id, language=language))

        # Commit the changes
        await session.commit()


async def register_result_en(fullname: str, writing: str, listening, reading: str, speaking: str, image: str,
                             band: str):
    async with async_session() as session:
        new_user = Results_English(fullname=fullname, writing=writing, listening=listening, reading=reading,
                                   speaking=speaking, image=image, Overall_Band=band)
        session.add(new_user)
        await session.commit()


async def register(tg_id, name: str, phone_number: str, course, level: str, course_time: str, user_gender: str,
                   born_year: str) -> None:
    async with async_session() as session:
        new_user = Registering(user_name=name, number=phone_number, course=course, level=level, time=course_time,
                               gender=user_gender, telegram_information=tg_id, born_year=born_year)
        session.add(new_user)
        await session.commit()


async def get_user_by_tg_id(tg_id):
    async with async_session() as session:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        return user


async def get_results_en():
    async with async_session() as session:
        stmt = select(Results_English)
        result = await session.execute(stmt)
        user_language = result.scalar_one_or_none()
        return user_language


# -------------------------------------time-----------------------------------------------------------------------------#
current_time = localtime()
current_year = current_time.tm_year
start_time = datetime.now()
formatted_time = start_time.strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------State Group----------------------------------------------------------------------#
class Register(StatesGroup):
    start = State()
    fullname = State()
    number = State()
    gender = State()
    course = State()
    level = State()
    year = State()
    month = State()
    fake_month = State()
    day = State()
    time = State()
    fake_number = State()
    number2 = State()
    fake_gender = State()


class Register_full(StatesGroup):
    start = State()
    fullname = State()
    number = State()
    gender = State()
    year = State()
    month = State()
    day = State()
    fake_number = State()
    number2 = State()
    fake_gender = State()


class Certificate(StatesGroup):
    start = State()
    fullname = State()
    band = State()
    image = State()
    speaking = State()
    writing = State()
    listening = State()
    reading = State()


# --------------------------------------KEYBOARDS-----------------------------------------------------------------------#
async def languages():
    lan = ['uz🇺🇿 O\'zbek tili 🇺🇿', 'ru🇷🇺 Russian 🇷🇺', 'en🇺🇸 English 🇺🇸']
    inline_button = []
    row = []
    for i in lan:
        row.append(InlineKeyboardButton(text=f'{i[2:]}', callback_data=f"lan_{i[:2]}"))
        if len(row) == 3:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def scores(language, category, before, band):
    inline_button = []
    row = []

    # Setting text based on the language
    if language == 'en':
        text1 = '🚫 Cancel'
        text2 = '⬅️ Back'
    elif language == 'uz':
        text1 = '🚫 Bekor qilish'
        text2 = '⬅️ Orqaga'
    else:
        text1 = '🚫 Bekor qilish'
        text2 = '⬅️ Orqaga'

    # If the category is 'photo'
    if category == 'photo':
        if band and before:
            inline_button.append([InlineKeyboardButton(text=text1, callback_data='menu_'),
                                  InlineKeyboardButton(text=text2, callback_data=f'score_{before}_{band}')])
        else:
            inline_button.append([InlineKeyboardButton(text=text1, callback_data='menu_')])
    else:
        # Generating score buttons from 1 to 9 with half increments
        scores = [i / 2 for i in range(2, 19)]  # Generates [1, 1.5, 2, ..., 9]

        for score in scores:
            # Add fire emoji for scores higher than 7
            emoji = " 🔥" if score > 7 else ""
            button_text = f"{score}{emoji}"
            b = row.append(
                InlineKeyboardButton(text=button_text, callback_data=f"score_{str(category)}_{score}{emoji}"))
            if len(row) == 3:
                inline_button.append(row)
                row = []

        # Append remaining row if not empty
        if row:
            inline_button.append(row)

        # Adding cancel and back buttons
        if band and before:
            inline_button.append([InlineKeyboardButton(text=text1, callback_data='menu_'),
                                  InlineKeyboardButton(text=text2, callback_data=f'score_{before}_{band}')])
        else:
            inline_button.append([InlineKeyboardButton(text=text1, callback_data='menu_')])

    # Creating InlineKeyboardMarkup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def gender(language, is_state):
    match language:
        case 'uz':
            menu = ['gender_man.🤵 Erkak kishi', 'gender_women.👩 Ayol kishi']
        case 'ru':
            menu = ['gender_man.🤵 Erkak kishi', 'gender_women.👩 Ayol kishi']
        case 'en':
            menu = ['gender_man.🤵 Man', 'gender_women.👩 Woman']
        case _:
            menu = ['gender_man.🤵 Erkak kishi', 'gender_women.👩 Ayol kishi']

    inline_button = []
    row = []
    for i in menu:
        if is_state == True:
            row.append(InlineKeyboardButton(text=f"{i.split('_')[1].split('.')[1]}",
                                            callback_data=f"state.{i.split('_')[0]}_{i.split('_')[1]}"))
        else:
            row.append(InlineKeyboardButton(text=f"{i.split('_')[1].split('.')[1]}", callback_data=f"{i}"))
        if len(row) == 2:  # Corrected here
            inline_button.append(row)
            row = []
    inline_button.append([InlineKeyboardButton(text='🏠 Bosh menu', callback_data=f"menu_")])
    if row:
        inline_button.append(row)

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def home(language):
    if language == 'uz':
        menu = ['courses_.✍️ Kursga yozilish', 'results.🏆 Natijalar', 'audio_.🔊 Audio materiallar', 'complain_.📌 '
                                                                                                    'Shikoyat qilish ',
                'settings.⚙️ Sozlamalar']
        inline_button = []
        row = []
        for i in menu:
            row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f"{i.split('.')[0]}"))
            if len(row) == 3:
                inline_button.append(row)
                row = []
        if row:
            inline_button.append(row)
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
        return inline_keyboard
    if language == 'en':
        menu = ['courses_.✍️ Kursga yozilish', 'results.🏆 Natijalar', 'audio_.🔊 Audio materiallar', 'complain_.📌 '
                                                                                                    'Shikoyat qilish ',
                'settings.⚙️ Sozlamalar']
        inline_button = []
        row = []
        for i in menu:
            row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f"{i.split('.')[0]}"))
            if len(row) == 3:
                inline_button.append(row)
                row = []
        if row:
            inline_button.append(row)
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
        return inline_keyboard
    if language == 'ru':
        menu = ['courses_.✍️ Kursga yozilish', 'results.🏆 Natijalar', 'audio_.🔊 Audio materiallar', 'complain_.📌 '
                                                                                                    'Shikoyat qilish ',
                'settings.⚙️ Sozlamalar']
        inline_button = []
        row = []
        for i in menu:
            row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f"{i.split('.')[0]}"))
            if len(row) == 3:
                inline_button.append(row)
                row = []
        if row:
            inline_button.append(row)
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
        return inline_keyboard


async def result_home(language):
    match language:
        case 'uz':
            menu = ['result_English.🇺🇸 Ingilis tilidan natijalar', 'result_IT.💻 IT dan natijalar',
                    'menu_.🏠 Bosh sahifaga qaytish']
        case 'ru':
            menu = ['result_English.🇺🇸 Ingilis tilidan natijalar', 'result_IT.💻 IT dan natijalar']
        case _:
            menu = ['result_English.🇺🇸 Ingilis tilidan natijalar', 'result_IT.💻 IT dan natijalar']
    inline_button = []
    row = []
    for i in menu:
        row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f"{i.split('.')[0]}"))
        if len(row) == 2:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def tuition(language):
    match language:
        case 'uz':
            menu = ['English_🇺🇸 Ingilis tili', 'IT_💻 IT', 'Matematika_✒️ Matematika', 'Tarix_🔶 Tarix',
                    'Arab tili_🔶 Arab tili']
            inline_button = []
            row = []
            for i in menu:
                row.append(InlineKeyboardButton(text=f'{i.split("_")[1]}', callback_data=f"register_{i.split('_')[0]}"))
                if len(row) == 3:
                    inline_button.append(row)
                    row = []
            if row:
                inline_button.append(row)
            inline_button.append([InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')])
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
            return inline_keyboard
        case 'ru':
            menu = ['englis tili_🇺🇸 Ingilis tili', 'IT_💻 IT', 'Matematika_✒️ Matematika', 'Tarix_🔶 Tarix',
                    'Arab tili_🔶 Arab tili']
            inline_button = []
            row = []
            for i in menu:
                row.append(InlineKeyboardButton(text=f'{i.split("-")[1]}', callback_data=f"register_{i.split('_')[0]}"))
                if len(row) == 3:
                    inline_button.append(row)
                    row = []
            if row:
                inline_button.append(row)
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
            return inline_keyboard
        case 'en':
            menu = ['englis tili_🇺🇸 Ingilis tili', 'IT_💻 IT', 'Matematika_✒️ Matematika', 'Tarix_🔶 Tarix',
                    'Arab tili_🔶 Arab tili']
            inline_button = []
            row = []
            for i in menu:
                row.append(InlineKeyboardButton(text=f'{i.split("-")[1]}', callback_data=f"register_{i.split('_')[0]}"))
                if len(row) == 3:
                    inline_button.append(row)
                    row = []
            if row:
                inline_button.append(row)
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
            return inline_keyboard


async def month(language, gender):
    # Month dictionary with custom names
    inline_buttons = []
    row = []
    match language:
        case 'uz':
            months = {
                12: '12🎄 Dekabr',  # December (Christmas tree)
                1: '01❄️ Yanvar',  # January (snowflake)
                2: '02🌸 Fevral',  # February (flower)
                3: '03🌷 Mart',  # March (spring flowers)
                4: '04🌱 Aprel',  # April (growth, spring)
                5: '05🌞 May',  # May (sun, summer approach)
                6: '06☀️ Iyun',  # June (hot weather)
                7: '07🌞 Iyun',  # July (summer)
                8: '08🌅 Avgust',  # August (sunrise, end of summer)
                9: '09🎒 Sentabr',  # September (back to school)
                10: '10🍂 Oktabr',  # October (fall leaves)
                11: '11🌧️ Noyabr'  # November (rain)
            }
        case 'ru':
            months = {
                12: '12🎄 Dekabr',  # December (Christmas tree)
                1: '01❄️ Yanvar',  # January (snowflake)
                2: '02🌸 Fevral',  # February (flower)
                3: '03🌷 Mart',  # March (spring flowers)
                4: '04🌱 Aprel',  # April (growth, spring)
                5: '05🌞 May',  # May (sun, summer approach)
                6: '06☀️ Iyun',  # June (hot weather)
                7: '07🌞 Iyun',  # July (summer)
                8: '08🌅 Avgust',  # August (sunrise, end of summer)
                9: '09🎒 Sentabr',  # September (back to school)
                10: '10🍂 Oktabr',  # October (fall leaves)
                11: '11🌧️ Noyabr'  # November (rain)
            }
        case _:
            months = {
                12: '12🎄 Dekabr',  # December (Christmas tree)
                1: '01❄️ Yanvar',  # January (snowflake)
                2: '02🌸 Fevral',  # February (flower)
                3: '03🌷 Mart',  # March (spring flowers)
                4: '04🌱 Aprel',  # April (growth, spring)
                5: '05🌞 May',  # May (sun, summer approach)
                6: '06☀️ Iyun',  # June (hot weather)
                7: '07🌞 Iyun',  # July (summer)
                8: '08🌅 Avgust',  # August (sunrise, end of summer)
                9: '09🎒 Sentabr',  # September (back to school)
                10: '10🍂 Oktabr',  # October (fall leaves)
                11: '11🌧️ Noyabr'  # November (rain)
            }

    for num, label in months.items():
        row.append(InlineKeyboardButton(text=label[2:], callback_data=f'month_{label[:2]}_{label}'))
        if len(row) == 3:  # Limit to 2 buttons per row
            inline_buttons.append(row)
            row = []
    match language:
        case 'en':
            row.append(InlineKeyboardButton(text="🏠 Home", callback_data='menu_'))
            row.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f'gender_.{gender}'))
        case 'ru':
            row.append(InlineKeyboardButton(text="🏠 Home", callback_data='menu'))
            row.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f'gender_.{gender}'))
        case 'uz':
            row.append(InlineKeyboardButton(text="🏠 Bosh menu", callback_data='menu_'))
            row.append(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f'gender_.{gender}'))
    if row:  # Add any remaining buttons to the last row
        inline_buttons.append(row)

    # Create an inline keyboard with the buttons
    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_kb


async def days(month, year):
    # Define days in each month
    month_days = {'01': 31, '02': 29 if (int(year) % 4 == 0) else 28,  # Leap year logic
                  '03': 31, '04': 30, '05': 31, '06': 30, '07': 31, '08': 31, '09': 30, '10': 31, '11': 30, '12': 31}

    days_in_month = month_days[month]  # Get the number of days for the selected month
    inline_buttons = []
    row = []
    days_in_month = month_days[month]  # Get the number of days for the selected month
    inline_buttons = []
    row = []

    for num in range(1, days_in_month + 1):
        row.append(InlineKeyboardButton(text=f'{num}', callback_data=f'day_{num}'))
        if len(row) == 5:  # Limit to 3 buttons per row
            inline_buttons.append(row)
            row = []  # Reset the row for the next set of buttons
    if row:  # Add any remaining buttons to the last row
        inline_buttons.append(row)
    inline_buttons.append([InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_'),
                           InlineKeyboardButton(text='⬅️ Orqaga', callback_data=f'year_{year}')])
    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_kb


async def share_phone_number(language):
    # Define the text for the button based on the language
    match language:
        case 'en':
            button_text = "📱 Share phone number"
        case 'uz':
            button_text = "📱 Telefon raqamni yuborish"
        case 'ru':
            button_text = "📱 Поделиться номером телефона"
        case _:
            button_text = "📞 Share number"

    # Create the button with the appropriate text
    share_phone_button = KeyboardButton(text=button_text, request_contact=True)

    # Define the keyboard layout with the button directly
    keyboard = ReplyKeyboardMarkup(keyboard=[[share_phone_button]],  # List of rows, each row as a list of buttons
                                   resize_keyboard=True, one_time_keyboard=True, selective=True,
                                   input_field_placeholder="Enter your phone number")
    return keyboard


async def create_inline_keyboard(menu, max_buttons_per_row=2):
    inline_button = []
    row = []
    for item in menu:
        row.append(
            InlineKeyboardButton(text=item.split(".")[1], callback_data=f'level_{item.split(".")[0]}'# Changed to level_
                                 ))
        if len(row) == max_buttons_per_row:
            inline_button.append(row)
            row = []
    row.append(InlineKeyboardButton(text='🏠 Bosh sahifaga otish', callback_data='menu_'))
    if row:
        inline_button.append(row)
    return InlineKeyboardMarkup(inline_keyboard=inline_button)


async def tuition_en(language, year):
    current_year = datetime.now().year
    age = int(current_year) - int(year)
    match language:
        case 'uz':
            if age <= 12:
                menu = ['kids.⭐️ Kids', 'more.⚙️ Boshqa oyni tanlash']
                return await create_inline_keyboard(menu, max_buttons_per_row=2)
            elif age <= 14:
                menu = ['kids.⭐️ Kids', 'intermittent.⭐️ Intermittent', 'more.⚙️ Boshqa oyni tanlash']
                return await create_inline_keyboard(menu, max_buttons_per_row=3)
            elif age >= 16:
                menu = ['kids.⭐️ Kids', 'Intermittent.⭐️ Intermittent', 'adult.⭐️ Adult', 'ielt.⭐️ IELTS']
                return await create_inline_keyboard(menu, max_buttons_per_row=4)
        case 'ru':
            if age <= 12:
                menu = ['kids.⭐️ Kids', 'more.⚙️ Boshqa oyni tanlash']
                return await create_inline_keyboard(menu, max_buttons_per_row=2)
            elif age <= 14:
                menu = ['kids.⭐️ Kids', 'intermittent.⭐️ Intermittent', 'more.⚙️ Boshqa oyni tanlash']
                return await create_inline_keyboard(menu, max_buttons_per_row=3)
            elif age >= 16:
                menu = ['kids.⭐️ Kids', 'intermittent.⭐️ Intermittent', 'adult.⭐️ Adult', 'ielt.⭐️ IELTS']
                return await create_inline_keyboard(menu, max_buttons_per_row=4)
        case 'en':
            if age <= 12:
                menu = ['kids.⭐️ Kids', 'more.⚙️ Boshqa oyni tanlash']
                return await create_inline_keyboard(menu, max_buttons_per_row=2)
            elif age <= 14:
                menu = ['kids.⭐️ Kids', 'intermittent.⭐️ Intermittent', 'more.⚙️ Boshqa oyni tanlash']
                return await create_inline_keyboard(menu, max_buttons_per_row=3)
            elif age >= 16:
                menu = ['kids.⭐️ Kids', 'intermittent.⭐️ Intermittent', 'adult.⭐️ Adult', 'ielt.⭐️ IELTS']
                return await create_inline_keyboard(menu, max_buttons_per_row=4)

    return None


async def level_more(language):
    if language == 'uz':
        menu = ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', 'menu_.🚫 Bekor qilish']
    if language == 'ru':
        menu = ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', 'menu_.🚫 Bekor qilish']
    if language == 'en':
        menu = ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', 'menu_.🚫 Bekor qilish']
    else:
        menu = ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', 'menu_.🚫 Bekor qilish']

    inline_button = []
    row = []
    for i in menu:
        row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}'))
        if len(row) == 3:
            inline_button.append(row)
    if row:
        inline_button.append(row)
    inline_button = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_button


async def confirmt(language, is_state):
    if language == 'uz':
        menu = ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash ', 'menu_.🚫 Bekore qilish']
    elif language == 'ru':
        menu = ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash ', 'menu_.🚫 Bekore qilish']
    elif language == 'en':
        menu = ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash ', 'menu_.🚫 Bekore qilish']
    else:
        menu = ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash ', 'menu_.🚫 Bekore qilish']

    inline_buttons = []
    row = []

    for i in menu:
        if is_state == True:
            button_text = i.split(".")[1]
            callback_data = f'state_{i.split(".")[0]}'
            row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        else:
            button_text = i.split(".")[1]
            callback_data = i.split('.')[0]
            row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))

        # Append row to buttons every 2 items
        if len(row) == 2:
            inline_buttons.append(row)
            row = []

    # Append any remaining buttons in the last row
    if row:
        inline_buttons.append(row)

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_keyboard


async def time_en(language, day):
    match language:
        case 'uz':
            menu = ['time_08:00 dan 09:30.', 'time_09:30 dan 11:00.', 'time_11:00 dan 12:30.', 'time_13:00 dan 14:30.',
                    'time_16:00 dan 5:30.']
        case 'ru':
            menu = ['time_08:00 dan 09:30', 'time_09:30 dan 11:00', 'time_11:00 dan 12:30', 'time_13:00 dan 14:30',
                    'time_16:00 dan 5:30', f'level_⬅️ Orqaga.{day}']
        case 'en':
            menu = ['time_08:00 dan 09:30', 'time_09:30 dan 11:00', 'time_11:00 dan 12:30', 'time_13:00 dan 14:30',
                    'time_16:00 dan 5:30', f'level_⬅️ Orqaga.{day}']
        case _:
            menu = ['time_08:00 dan 09:30', 'time_09:30 dan 11:00', 'time_11:00 dan 12:30', 'time_13:00 dan 14:30',
                    'time_16:00 dan 5:30', f'level_⬅️ Orqaga.{day}']
    inline_button = []
    row = []
    for i in menu:
        row.append(InlineKeyboardButton(text=f'{i.split("_")[1].split(".")[0]}',
                                        callback_data=f'{i.split("_")[0]}_{i.split("_")[1]}'))
        if len(row) == 3:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_button.append([InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_'),
                          InlineKeyboardButton(text='⬅️ Orqaga', callback_data=f'confirm_{day}')])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def settings(language):
    text = {'uz': ['registration/full_.🖊️ Toliq registratsiyadan o\'tish', 'menu_.🏠 Bosh menu'],
        'ru': ['registration/full_.🖊️ Toliq registratsiyadan o\'tish', 'menu_.🏠 Bosh menu'],
        'en': ['registration/full_.🖊️ Toliq registratsiyadan o\'tish', 'menu_.🏠 Bosh menu'], }
    inline_button = []
    row = []
    for i in text.get(language):
        row.append(InlineKeyboardButton(text=f'{i.split('.')[1]}', callback_data=f'{i.split('.')[0]}'))
        if len(row) == 2:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def audio_home(language):
    text = {
        'uz': ['/audio_home_vt_.📹 (VT) materiallar', '/audio_home_mt_.👨‍🏫 (MT) materiallar', 'menu_.🏠 Bosh menu'],
        'ru': ['/audio_home_vt_.📹 (VT) materiallar', '/audio_home_mt_.👨‍🏫 (MT) materiallar', 'menu_.🏠 Bosh menu'],
        'en': ['/audio_home_vt_.📹 (VT) materiallar', '/audio_home_mt_.👨‍🏫 (MT) materiallar', 'menu_.🏠 Bosh menu'],
    }
    inline_button = []
    row = []

    for i in text.get(language):
        row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f'{i.split(".")[0]}'))
        if len(row) == 2:
            inline_button.append(row)
            row = []

    if row:
        inline_button.append(row)

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def audio_month(language, data):
    inline_button = []
    row = []

    for i in range(1,17):
        row.append(InlineKeyboardButton(text=f'{i} Month', callback_data=f'.audio_month_{i}_{data}'))
        if len(row) == 3:
            inline_button.append(row)
            row = []

    if row:
        inline_button.append(row)

    text = {
        'uz': 'menu_.🏠 Bosh sahifa',
        'ru': 'menu_.🏠 Bosh sahifa',
        'en': 'menu_.🏠 Bosh sahifa',
    }

    inline_button.append([InlineKeyboardButton(text=text.get(language).split('_')[1],
                                               callback_data=f"{text.get(language).split('_')[0]}")])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard

# ---------------------------------------functions ---------------------------------------------------------------------#


async def delete_previous_messages(message, id):
    sleep(0.5)
    for i in range(2, 50):  # Try up to 10 previous messages
        try:
            await bot.delete_message(chat_id=id, message_id=message - i)
        except TelegramBadRequest as e:
            pass  # Continue to the next try if there's an error


IMAGE_DOWNLOAD_PATH = "Certificate"
os.makedirs(IMAGE_DOWNLOAD_PATH, exist_ok=True)


async def download_image(bot: Bot, message: Message, name: str) -> str | None:
    try:
        # Ensure the save folder exists
        save_folder = "Certificate"
        os.makedirs(save_folder, exist_ok=True)

        # Create a valid file name (replace spaces with underscores)
        file_name = f"{name.replace(' ', '_')}.jpg"
        save_path = os.path.join(save_folder, file_name)

        # Get the file ID from the latest photo
        file_id = message.photo[-1].file_id

        # Download the file using file_id directly
        await bot.download(file_id, save_path)
        return save_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


async def send_certificate(bot: Bot, chat_id: int, callback_query):
    async with async_session() as session:
        try:
            # Fetch the most recent certificate
            result = await session.execute(select(Results_English).order_by(Results_English.id.desc())
                                           # Limit to the latest
                                           )
            certificates = result.scalars().all()

            if not certificates:
                await bot.send_message(chat_id, "No certificate found.")
                return
            for certificate in certificates:
                # Prepare the message text for each certificate
                text = (f"📋 Certificate Information:\n\n"
                        f"👤 Full Name: {certificate.fullname}\n"
                        f"🏅 Band Score: {certificate.Overall_Band}\n\n"
                        f"🗣 Speaking: {certificate.speaking}\n"
                        f"✍️ Writing: {certificate.writing}\n"
                        f"👂 Listening: {certificate.listening}\n"
                        f"📖 Reading: {certificate.reading}\n\n"
                        f"✨Smart English\n<a href='http://instagram.com/smart.english.official'>Instagram</a>|<a href='https://t.me/SMARTENGLISH2016'>Telegram</a>|<a href='https://www.youtube.com/channel/UCu8wC4sBtsVK6befrNuN7bw'>You Tube</a>|<a href='https://t.me/Smart_Food_official'>Smart Food</a>|<a href='https://t.me/xusanboyman200'>Programmer</a>"

                        )

                # Get the certificate image path
                image_path = certificate.image

                # Check if the image exists
                if os.path.exists(image_path):
                    photo = FSInputFile(image_path)
                    await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode='HTML')
                else:
                    await bot.send_message(chat_id, f"Certificate image not found for {certificate.fullname}.",
                                           parse_mode='HTML')
            await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)

            language = await get_user_language(tg_id=callback_query.from_user.id)
            user_id = callback_query.from_user.id

            language_map = {'ru': 'ru', 'en': 'en', 'uz': 'Bosh menu'}

            # Use the language map to determine the appropriate response text
            await bot.send_message(text=language_map.get(language, 'en'), chat_id=user_id,
                                   reply_markup=await home(language))


        except Exception as e:
            await bot.send_message(chat_id, f"An error occurred: {str(e)}")


# -----------------------------------------Messages---------------------------------------------------------------------#
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    existing_user = await get_user_by_tg_id(user_id)
    if not existing_user:
        await message.answer('🇺🇿: Assalomu alaykum botimizga xush kelibsiz\n🇷🇺: Privet \n🇺🇸: Hello Mr or Ms',
                             reply_markup=await languages())
        await delete_previous_messages(message.message_id, message.from_user.id)
        return
    else:
        language = await get_user_language(user_id)
        await bot.send_message(chat_id=user_id, text={"ru": "ru", "en": "en", "uz": "Bosh menu"}.get(language, "en"),
                               reply_markup=await home(language))
        await state.clear()
    try:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id - 1)
        await delete_previous_messages(message.message_id, message.from_user.id)
    except TelegramBadRequest as e:
        pass


@dp.callback_query(F.data.startswith('menu_'))
async def menu(callback_query: CallbackQuery):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    user_id = callback_query.from_user.id
    match language:
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='ru', chat_id=user_id,
                                        reply_markup=await home(language))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='en', chat_id=user_id,
                                        reply_markup=await home(language))
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=user_id, text="Bosh menu",
                                        reply_markup=await home(language))
        case _:
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='en', chat_id=user_id,
                                        reply_markup=await home(language))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('lan_'))
async def language(callback_query: CallbackQuery):
    if callback_query.from_user.username:
        await add_user(callback_query.from_user.id, callback_query.from_user.username,
                       callback_query.from_user.full_name)
    language = callback_query.data.split('_')[1]
    await set_user_language(tg_id=callback_query.from_user.id, language=language)
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text={"ru": "ru", "en": "en", "uz": "Bosh menu"}.get(language),
                                reply_markup=await home(language))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    return


@dp.callback_query(F.data.startswith('courses_'))
async def courses(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id,
                                        text='Smart English o\'vmarkazidagi kurslardan birini tanlang',
                                        reply_markup=await tuition(language))
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text='Smart English o\'vmarkazidagi kurslardan birini tanlang',
                                        reply_markup=await tuition(language))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text='Smart English o\'vmarkazidagi kurslardan birini tanlang',
                                        reply_markup=await tuition(language))


@dp.callback_query(F.data.startswith('register_'))
async def registers(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')[1]
    await state.update_data(course=str(data))
    language = await get_user_language(tg_id=callback_query.from_user.id)
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id,
                                        text='🖋️ Toliq ismingizni yozing\nMisol uchun: Abdulkhaev Xusanboy')
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id,
                                        text='🖋️ Toliq ismingizni yozing\nMisol uchun: Abdulkhaev Xusanboy')
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id,
                                        text='🖋️ Toliq ismingizni yozing\nMisol uchun: Abdulkhaev Xusanboy')
    await state.set_state(Register.fullname)


@dp.message(Register.fullname)
async def year_callback(message: Message, state: FSMContext):
    language = await get_user_language(tg_id=message.from_user.id)
    a = False
    for i in message.text:
        if i in str([1, 2, 3, 4, 5, 6, 7, 8, 9, 0]) or len(message.text)<7:
                a = True
                break
    c = message.text.split(' ')
    if len(c) != 2:
        a = True
    else:
        a = False
    if a:
        await state.set_state(Register.fullname)
        match language:
            case 'uz':
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Iltimos, toʻliq ismingizni kiriting va sonlardan foydalanmang')
            case 'ru':
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Пожалуйста, введите полное имя и не используйте цифры')
            case 'en':
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Please enter your full name without using numbers')
        return
    await state.update_data(fullname=message.text)
    match language:
        case 'uz':
            await bot.send_message(chat_id=message.from_user.id,
                                   text='📞 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing',
                                   reply_markup=await share_phone_number(language))
        case 'ru':
            await bot.send_message(chat_id=message.from_user.id,
                                   text='📞 Введите свой номер телефона или нажмите на кнопку ниже',
                                   reply_markup=await share_phone_number(language))
        case 'en':
            await bot.send_message(chat_id=message.from_user.id,
                                   text='📞 Please enter your phone number or click the button below',
                                   reply_markup=await share_phone_number(language))
    await state.set_state(Register.number)
    await delete_previous_messages(message.message_id, message.from_user.id)


@dp.message(Register.number)
async def number(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if message.text:
        if not message.text[1:].isdigit() or 9<=len(str(message.text))>=13 :
            await state.set_state(Register.number)
            match language:
                case 'uz':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='Iltimos telfon raqamingizni 998 90 123 45 67 korinishida yoki 901234567 korinishida yuboring  \nHarf va maxsus belgilardan foydalanmang',
                                           reply_markup=await share_phone_number(language))
                case 'ru':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='Iltimos telfon raqamingizni 998 90 123 45 67 korinishida yoki 901234567 korinishida yuboring  \nHarf va maxsus belgilardan foydalanmang',
                                           reply_markup=await share_phone_number(language))
                case 'en':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='Iltimos telfon raqamingizni 998 90 123 45 67 korinishida yoki 901234567 korinishida yuboring  \nHarf va maxsus belgilardan foydalanmang',
                                           reply_markup=await share_phone_number(language))
            return
        if message.text[0]=='+':
            await state.update_data(number=message.text)
        else:
            await state.update_data(number=f'+{message.text}')
    if message.contact:
        await state.update_data(number=message.contact.phone_number)
    match language:
        case 'uz':
            await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                   reply_markup=await gender(language, False))
        case 'ru':
            await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                   reply_markup=await gender(language, False))
        case 'en':
            await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                   reply_markup=await gender(language, False))
    await state.set_state(Register.start)
    await delete_previous_messages(message.message_id, message.from_user.id)


@dp.callback_query(F.data.startswith('gender_'))
async def genders(callback_query: CallbackQuery, state: FSMContext):
    inf = callback_query.data.split('.')[0]
    data = inf.split('_')[1]
    fake = callback_query.data.split('.')[1]
    await state.update_data(gender=data)
    await state.update_data(fake_gender=fake)
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='ru',
                                        chat_id=callback_query.from_user.id)
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='en',
                                        chat_id=callback_query.from_user.id)
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text='Iltmos tugilgan yilingizni kiriting\nMisol uchun: 2008',
                                        chat_id=callback_query.from_user.id)
    await state.set_state(Register.year)


@dp.message(Register.year)
async def year_callback(message: Message, state: FSMContext):
    language = await get_user_language(tg_id=message.from_user.id)
    if not message.text.isdigit():
        match language:
                case 'uz':
                    await bot.send_message(chat_id=message.from_user.id,
                                       text='Iltimos tugilgan yilingiz kiriting o\'yin qilman')
                case 'ru':
                    await bot.send_message(chat_id=message.from_user.id,
                                       text='Iltimos tugilgan yilingiz kiriting o\'yin qilman')
                case 'en':
                    await bot.send_message(chat_id=message.from_user.id,
                                       text='Iltimos tugilgan yilingiz kiriting o\'yin qilman')
        return
    if message.text.isdigit():
        if len(message.text) != 4 or not current_year-60+5<int(message.text)<current_year-5:
            await state.set_state(Register.year)
            match language:
                case 'uz':
                    await message.answer(
                        text='Iltimos ozingizning yoki kursga qatnashmoqchi bolgan insonning tugilgan yilini kiriting📅\nMisol uchun: 2008')
                case 'ru':
                    await message.answer(
                        text='Iltimos ozingizning yoki kursga qatnashmoqchi bolgan insonning tugilgan yilini kiriting📅\nMisol uchun: 2008')
                case 'ru':
                    await message.answer(
                        text='Iltimos ozingizning yoki kursga qatnashmoqchi bolgan insonning tugilgan yilini kiriting📅\nMisol uchun: 2008')
            await state.set_state(Register.year)
            return
    await state.update_data(year=message.text)
    match language:
        case 'ru':
            await bot.send_message(text='ru', chat_id=message.from_user.id, reply_markup=await month(language, gender))
        case 'en':
            await bot.send_message(text='en', chat_id=message.from_user.id, reply_markup=await month(language, gender))
        case 'uz':
            await bot.send_message(text='Tugilgan oyingizni tanlang', chat_id=message.from_user.id,
                                   reply_markup=await month(language, gender))
    await state.set_state(Register.start)
    await delete_previous_messages(id=message.from_user.id, message=message.message_id)


@dp.callback_query(F.data.startswith('year_'))
async def sssss(callback_query: CallbackQuery,state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    await state.update_data(year=callback_query.data.split('_')[1])
    data = await state.get_data()
    gender1 =data.get('gender')
    fake = data.get('fake_gender')
    gender = f'{gender1}_{fake}'
    match language:
        case 'uz':
            await bot.send_message(text='Tugilgan oyingizni tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await month(language, gender))
        case 'ru':
            await bot.send_message(text='Tugilgan oyingizni tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await month(language, gender))
        case 'en':
            await bot.send_message(text='Tugilgan oyingizni tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await month(language, gender))
    await bot.delete_message(message_id=callback_query.message.message_id,chat_id=callback_query.from_user.id)
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('month_'))
async def month_callback(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    month = callback_query.data.split('_')[1]
    month_name = callback_query.data.split('_')[2][2:]
    await state.update_data(month=month_name)
    years = await state.get_data()
    year = years.get('year')
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id, text=f'Choose the day for {month_name}:',
                                        reply_markup=await days(month, year))
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id, text=f'Choose the day for {month_name}:',
                                        reply_markup=await days(month, year))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id, text=f'Choose the day for {month_name}:',
                                        reply_markup=await days(month, year))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('day_'))
async def day_callback(callback_query: CallbackQuery, state: FSMContext):
    day = callback_query.data.split('_')[1]
    await state.update_data(day=day)
    years = await state.get_data()
    course = years.get('course')
    year = years.get('year')
    language = await get_user_language(tg_id=callback_query.from_user.id)
    if course == 'English':
        match language:
            case 'ru':
                await bot.edit_message_text(message_id=callback_query.message.message_id, text='ru',
                                            chat_id=callback_query.from_user.id, reply_markup=await tuition(language))
            case 'en':
                await bot.edit_message_text(message_id=callback_query.message.message_id, text='en',
                                            chat_id=callback_query.from_user.id, reply_markup=await tuition(language))
            case 'uz':
                await bot.edit_message_text(message_id=callback_query.message.message_id,
                                            text='Kurs darajasini tanlang', chat_id=callback_query.from_user.id,
                                            reply_markup=await tuition_en(language, year))
    else:
        data = course
        match language:
            case 'uz':
                await bot.edit_message_text(message_id=callback_query.message.message_id,
                                            text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await time_en(language, day))
            case 'ru':
                await bot.edit_message_text(message_id=callback_query.message.message_id,
                                            text=f'{data} uchun berilgan vaqtni tanlang',
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await time_en(language, day))
            case 'en':
                await bot.edit_message_text(message_id=callback_query.message.message_id,
                                            text=f'{data} uchun berilgan vaqtni tanlang',
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await time_en(language, day))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('level_'))
async def level(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')[1]
    await state.update_data(level=data)
    days = await state.get_data()
    course = days.get('course')
    day = days.get('day')
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await time_en(language, day))
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text=f'{data} uchun berilgan vaqtni tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await time_en(language, day))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text=f'{data} uchun berilgan vaqtni tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await time_en(language, day))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('more_level'))
async def level(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')[1]
    await state.update_data(level=data)
    days = await state.get_data()
    course = days.get('course')
    day = days.get('day')
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='Kurs darajasini tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await level_more(language))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='Kurs darajasini tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await level_more(language))
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='Kurs darajasini tanlang',
                                        chat_id=callback_query.from_user.id, reply_markup=await level_more(language))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message_id)


@dp.callback_query(F.data.startswith('time_'))
async def time(callback_query: CallbackQuery, state: FSMContext):
    years = await state.get_data()
    time = callback_query.data.split('_')[1]
    await state.update_data(time=time)
    course = years.get('course')
    day = years.get('day')
    year = years.get('year')
    month = years.get('month')
    number = years.get('number')
    gender = years.get('fake_gender')
    fullname = years.get('fullname')
    language = await get_user_language(tg_id=callback_query.from_user.id)
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id, text=(f'Sizning ma\'lumotlaringiz:\n'
                                                                                   f'To\'liq ismingiz: {fullname}\n'
                                                                                   f'Telefon raqamingiz: {number}\n'
                                                                                   f'Jinsingiz: {gender}\n'
                                                                                   f'Tug\'ilgan yilingiz: {year} yil\n'
                                                                                   f'Tug\'ilgan oyingiz: {month} oy\n'
                                                                                   f'Tug\'ilgan kuningiz: {day} kun\n'
                                                                                   f'Kurs nomi: {course}\n'
                                                                                   f'Kurs vaqti: {time}'

                                                                                   ),
                                        reply_markup=await confirmt(language, False))
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id, text=(f'Sizning ma\'lumotlaringiz:\n'
                                                                                   f'Tug\'ilgan yilingiz: {year}\n'
                                                                                   f'Tug\'ilgan oyingiz: {month}\n'
                                                                                   f'Tug\'ilgan kuningiz: {day}'),
                                        reply_markup=await confirmt(language, False))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id, text=(f'Sizning ma\'lumotlaringiz:\n'
                                                                                   f'Tug\'ilgan yilingiz: {year}\n'
                                                                                   f'Tug\'ilgan oyingiz: {month}\n'
                                                                                   f'Tug\'ilgan kuningiz: {day}'),
                                        reply_markup=await confirmt(language, False))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('confirm_'))
async def confirm(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    time1 = data.get('time')
    course = data.get('course')
    number = data.get('number')
    gender = data.get('fake_gender')
    fullname = data.get('fullname')
    level = data.get('level')
    day = data.get('day')
    year = data.get('year')
    month = data.get('month')
    born_year = f'{day:02}/{month}/{year}'
    if callback_query.from_user.username:
        await register(tg_id=callback_query.from_user.username, name=fullname, phone_number=number, course=course,
                       level=level,  # Pass the correct value here
                       course_time=time1,  # Pass the correct value here
                       user_gender=gender, born_year=born_year)
    else:
        # Register the user with the correct data
        await register(tg_id=callback_query.from_user.id, name=fullname, phone_number=number, course=course,
                       level=level,  # Pass the correct value here
                       course_time=time1,  # Pass the correct value here
                       user_gender=gender, born_year=born_year)
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.message.chat.id,
                                        text=f'Sizga 32 soat ichida {number if number[0] == "+" else "+" + str(number)} shu telefon raqamingizga masul shaxslar aloqaga chiqishadi.',
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')], [
                                                InlineKeyboardButton(text='📞 Telfon raqamni ozgartirish',
                                                                     callback_data='change_number_')]]))
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.message.chat.id,
                                        text=f'Sizga 32 soat ichida {number} shu telefon raqamingizga masul shaxslar aloqaga chiqishadi.',
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')], [
                                                InlineKeyboardButton(text='📞 Telfon raqamni ozgartirish',
                                                                     callback_data='change_number_')]]))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.message.chat.id,
                                        text=f'Sizga 32 soat ichida {number} shu telefon raqamingizga masul shaxslar aloqaga chiqishadi.',
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')], [
                                                InlineKeyboardButton(text='📞 Telfon raqamni ozgartirish',
                                                                     callback_data='change_number_')]]))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data == 'change_number_')
async def fake_number(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'uz':
            contact_keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📞 Share Contact", request_contact=True)]], resize_keyboard=True,
                one_time_keyboard=True  # The keyboard will hide after the user presses a button
            )

            await bot.send_message(chat_id=callback_query.message.chat.id,
                                   text='Iltimos, telefon raqamingizni ulashing:', reply_markup=contact_keyboard)
        case 'ru':
            contact_keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📞 Share Contact", request_contact=True)]], resize_keyboard=True,
                one_time_keyboard=True  # The keyboard will hide after the user presses a button
            )
            await bot.send_message(chat_id=callback_query.message.chat.id,
                                   text='Iltimos, telefon raqamingizni ulashing:', reply_markup=contact_keyboard)

        case 'en':
            contact_keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📞 Share Contact", request_contact=True)]], resize_keyboard=True,
                one_time_keyboard=True  # The keyboard will hide after the user presses a button
            )
    await bot.send_message(chat_id=callback_query.message.chat.id,
                           text='I📞 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing',
                           reply_markup=await share_phone_number(language))
    await state.set_state(Register.number2)
    await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)


@dp.message(Register.number2)
async def number2(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if message.text:
        if message.text[1:].isdigit() and message.text[0].isdigit() or message.text.isdigit():
            await state.set_state(Register.number2)
            match language:
                case 'uz':
                    await message.answer(
                        text='Iltimos telefon raqamingizni +998 90 123 45 67 yoki +90 123 45 67 formatida jonating',
                        reply_markup=await share_phone_number(language))
                case 'ru':
                    await message.answer(
                        text='Iltimos telefon raqamingizni +998 90 123 45 67 yoki +90 123 45 67 formatida jonating',
                        reply_markup=await share_phone_number(language))
                case 'en':
                    await message.answer(
                        text='Iltimos telefon raqamingizni +998 90 123 45 67 yoki +90 123 45 67 formatida jonating',
                        reply_markup=await share_phone_number(language))
            return
        await state.update_data(number=message.text)
    if message.contact:
        await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    number = data.get('number')
    match language:
        case 'uz':
            await message.answer(
                text=f'Sizga 32 soat ichida {number} shu telefon raqamingizga masul shaxslar aloqaga chiqishadi.',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')], [
                        InlineKeyboardButton(text='📞 Telfon raqamni ozgartirish', callback_data='change_number_')]
                                     # Make sure callback_data is set here
                                     ]))

        case 'ru':
            await message.answer(
                text=f'Sizga 32 soat ichida {number} shu telefon raqamingizga masul shaxslar aloqaga chiqishadi.',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')], [
                        InlineKeyboardButton(text='📞 Telfon raqamni ozgartirish', callback_data='change_number_')]
                                     # Make sure callback_data is set here
                                     ]))

        case 'en':
            await message.answer(
                text=f'Sizga 32 soat ichida {number} shu telefon raqamingizga masul shaxslar aloqaga chiqishadi.',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')], [
                        InlineKeyboardButton(text='📞 Telfon raqamni ozgartirish', callback_data='change_number_')]
                                     # Make sure callback_data is set here
                                     ]))
    await state.set_state(Register.start)
    await delete_previous_messages(message.message_id, id=message.from_user.id)


# --------------------------------  Add Information's ------------------------------------------------------------------#
@dp.message(Command('add_result'))
async def add_result(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    match language:
        case 'ru':
            text = "Напишите, на кого зарегистрирован сертификат (например: Akmaljon Khusanov)"
        case 'en':
            text = "Please write the full name of the certificate owner (e.g., Akmaljon Khusanov)"
        case _:
            text = "Certificat kimga tegishli ekanligini to'liq yozing \nMisol uchun: Akmaljon Khusanov"
    await message.answer(text=text)
    await state.set_state(Certificate.fullname)
    await delete_previous_messages(message.message_id, message.from_user.id)


@dp.callback_query(F.data.startswith('score_add_result_'))
async def add_result(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    await bot.delete_message(callback_query.chat.id - 1, callback_query.message.id)
    match language:
        case 'ru':
            text = "Напишите, на кого зарегистрирован сертификат (например: Akmaljon Khusanov)"
        case 'en':
            text = "Please write the full name of the certificate owner (e.g., Akmaljon Khusanov)"
        case _:
            text = "Certificat kimga tegishli ekanligini to'liq yozing \nMisol uchun: Akmaljon Khusanov"
    await bot.send_message(chat_id=callback_query.message.message_id, text=text)
    await state.set_state(Certificate.fullname)


@dp.message(Certificate.fullname)
async def fullname(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if message.text.isdigit():
        match language:
            case 'ru':
                text = 'Certificat kimga tegishli ekanligini to\'liq yozing va raqamlardan foydalanmang \nMisol uchun: Akmaljon Khusanov'
            case 'en':
                text = 'Certificat kimga tegishli ekanligini to\'liq yozing va raqamlardan foydalanmang \nMisol uchun: Akmaljon Khusanov'
            case _:
                text = 'Certificat kimga tegishli ekanligini to\'liq yozing va raqamlardan foydalanmang \nMisol uchun: Akmaljon Khusanov'
        await message.answer(text=text)
        await state.set_state(Certificate.fullname)
        return
    fullname = await state.update_data(fullname=message.text)
    match language:
        case 'ru':
            text = 'Speaknig dan nech baho olgansiz'
        case 'uz':
            text = 'Speaknig dan nech baho olgansiz'
        case _:
            text = 'Speaknig dan nech baho olgansiz'
    await state.set_state(Register.start)
    await bot.send_message(chat_id=message.from_user.id,text=text, reply_markup=await scores(language, 'speaking', 'add_result', f'{fullname}'))


@dp.callback_query(F.data.startswith('score_fullname_'))
async def fullname(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    await state.update_data(fullname=callback_query.data.split('_')[2])
    match language:
        case 'ru':
            text = 'Speaknig dan nech baho olgansiz'
        case 'uz':
            text = 'Speaknig dan nech baho olgansiz'
        case _:
            text = 'Speaknig dan nech baho olgansiz'
    await bot.send_message(chat_id=callback_query.from_user.id, text=text,
                           reply_markup=await scores(language, f'{speaking}', 'add_result', 'salom'))


@dp.callback_query(F.data.startswith('score_speaking_'))
async def speaking(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[2]
    get_data = await state.get_data()
    fullname = get_data.get('fullname')
    await state.update_data(speaking=data)
    match language:
        case 'ru':
            text = 'Writing dan nech baho olgan'
        case 'en':
            text = 'Writing dan nech baho olgan '
        case _:
            text = 'Writing dan nech baho olgan'
    await bot.edit_message_text(message_id=callback_query.message.message_id,chat_id=callback_query.from_user.id, text=text,
                           reply_markup=await scores(language, f'writing', 'fullname', f'{fullname}'))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('score_writing_'))
async def writing(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    speaking_score = data.get('speaking')
    await state.update_data(writing=callback_query.data.split('_')[2])
    match language:
        case 'ru':
            text = 'Listening dan nech ball olgan'
        case 'en':
            text = 'Listening dan nech ball olgan '
        case _:
            text = 'Listening dan nech ball olgan'
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text,
                                chat_id=callback_query.from_user.id,
                                reply_markup=await scores(language, f'listening', speaking, f'{speaking_score}'))


@dp.callback_query(F.data.startswith('score_listening_'))
async def listening(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    writing_score = data.get('writing')
    await state.update_data(listening=callback_query.data.split('_')[2])
    match language:
        case 'ru':
            text = 'Reading dan nech ball olgan'
        case 'en':
            text = 'Reading dan nech ball olgan '
        case _:
            text = 'Reading dan nech ball olgan'
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text,
                                chat_id=callback_query.from_user.id,
                                reply_markup=await scores(language, f"reading", f'{writing}', f'{writing_score}'))


@dp.callback_query(F.data.startswith('score_reading_'))
async def reading(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    listening_score = data.get('listening')
    await state.update_data(reading=callback_query.data.split('_')[2])
    match language:
        case 'ru':
            text = "Iltioms Certifikatning suratini yuboring"
        case 'uz':
            text = "Iltioms Certifikatning suratini yuboring"
        case _:
            text = "Iltioms Certifikatning suratini yuboring"
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text,
                                chat_id=callback_query.from_user.id,
                                reply_markup=await scores(language, f'photo', listening, f'{listening_score}'))
    await state.set_state(Certificate.image)


@dp.message(Certificate.image)
async def image(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if not message.photo:
        # If no photo is found, send an appropriate message based on the user's language
        match language:
            case 'uz':
                await message.answer(text='Iltimos faqat rasm tashlang 🖼')
            case 'en':
                await message.answer(text='Please send only an image 🖼')
            case 'ru':
                await message.answer(text='Пожалуйста, отправьте только изображение 🖼')

        # Set the state to capture the image again
        await state.set_state(Certificate.image)
        return
    data = await state.get_data()
    name = data.get('fullname')
    writing = data.get('writing')
    reading = data.get('reading')
    speaking = data.get('speaking')
    listening = data.get('listening')
    file_id = message.photo[-1].file_id
    await state.update_data(image=f'Certificate/{name.replace(' ', '_')}.jpg')
    band = (float(reading[:1]) + float(writing[:1]) + float(speaking[:1]) + float(listening[:1])) / 4
    decimal_part = str(band).split('.')[1]  # Extract the decimal part
    if int(decimal_part) >= 75:
        band = float(str(band).split('.')[0]) + 1  # Add 1 if the decimal is greater than 75
    elif int(decimal_part) >= 25:
        band = float(str(band).split('.')[0]) + 0.5
    else:
        band = float(band)
    await state.update_data(band=band)
    download_path = await download_image(bot, message, name)

    # If the image download failed, notify the user and stop
    if not download_path:
        await message.answer("❌ Failed to download the image.")
        return

    # Prepare the message text with the certificate details
    text = (f"📋 Certificate Information:\n\n"
            f"👤 Full Name: {name}\n"
            f"🏅 Band Score: {band}\n\n"
            f"🗣 Speaking: {speaking}\n"
            f"✍️ Writing: {writing}\n"
            f"👂 Listening: {listening}\n"
            f"📖 Reading: {reading}\n\n"
            f"<a href='https://t.me/xusanboyman'>Telegram number of programmer</a>")

    # Send the photo with the certificate information
    await bot.send_photo(chat_id=message.from_user.id, photo=file_id,  # Use the file_id stored in state
                         caption=text, reply_markup=await confirmt(language, True), parse_mode='HTML')
    await delete_previous_messages(message.message_id, message.from_user.id)


@dp.callback_query(F.data.startswith('state_confirm_'))
async def stagedconifer(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    fullname = str(data.get('fullname'))
    reading = str(data.get('reading'))
    writing = str(data.get('writing'))
    speaking = str(data.get('speaking'))
    image = str(data.get('image'))
    listening = str(data.get('listening'))
    band = str(data.get('band'))
    match language:
        case 'ru':
            text = 'Muaffaqiyatli saqalandi'
        case 'uz':
            text = 'Muaffaqiyatli saqalandi'
        case _:
            text = 'Muaffaqiyatli saqalandi'
    await register_result_en(fullname, writing, listening, reading, speaking, image, band)
    await bot.send_message(text=text, chat_id=callback_query.from_user.id, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_')]]))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


# ------------------------------------  Audio --------------------------------------------------------------------------#
@dp.callback_query(F.data.startswith('audio_'))
async def audiol(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    text = {
        'uz': 'Sizga kerakli audio qaysin bolimdan',
        'ru': 'Sizga kerakli audio qaysin bolimdan',
        'en': 'Sizga kerakli audio qaysin bolimdan',
    }
    current_text = text.get(language)
    current_markup = await audio_home(language)

    # Check if the content or markup has changed
    if callback_query.message.text != current_text or callback_query.message.reply_markup != current_markup:
        await bot.edit_message_text(
            message_id=callback_query.message.message_id,
            text=current_text,
            chat_id=callback_query.from_user.id,
            reply_markup=current_markup
        )

    # Delete previous message if necessary
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('/audio_home_'))
async def audio_monthl(callback_query: CallbackQuery):
    data = callback_query.data.split('_')[2]
    language = await get_user_language(callback_query.from_user.id)
    text = {
        'uz': f'{data.upper()} oyingizni tanlang',
        'ru': f'{data.upper()} oyingizni tanlang',
        'en': f'{data.upper()} oyingizni tanlang',
    }
    await bot.edit_message_text(message_id=callback_query.message.message_id,chat_id=callback_query.from_user.id, text=text.get(language),
                           reply_markup=await audio_month(language, data))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)

@dp.callback_query(F.data.startswith('.audio_month_'))
async def audio_month_level(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    month = callback_query.data.split('_')[2]
    data = callback_query.data.split('_')[3]
    folder_path = f'./audio/{data}/{month}'

    mp3_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
    text={
        'uz':'Bosh sahifa',
        'ru':'Bosh sahifa',
        'en':'Bosh sahifa',
    }
    # Sending each mp3 file to the user
    for file_path in mp3_files:
        audios = FSInputFile(file_path)
        await bot.send_chat_action(chat_id=callback_query.from_user.id,action='upload_audio')
        await bot.send_audio(chat_id=callback_query.from_user.id, audio=audios)
        await bot.send_message(chat_id=callback_query.from_user.id,text=text.get(language),reply_markup=await home(language))
        try:
            await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)
            await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
        except TelegramBadRequest:
            pass

# ------------------------------------  Certificates -------------------------------------------------------------------#

@dp.callback_query(F.data.startswith("results"))
async def results(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    if language == 'uz':
        await bot.edit_message_text(message_id=callback_query.message.message_id,
                                    text='Smart English o\'quv markazdagi kurslardan birini tanlang',
                                    chat_id=callback_query.from_user.id, reply_markup=await result_home(language))
    if language == 'ru':
        await bot.edit_message_text(message_id=callback_query.message.message_id,
                                    text='Smart English o\'quv markazdagi kurslardan birini tanlang',
                                    chat_id=callback_query.from_user.id, reply_markup=await result_home(language))
    if language == 'en':
        await bot.edit_message_text(message_id=callback_query.message.message_id,
                                    text='Smart English o\'quv markazdagi kurslardan birini tanlang',
                                    chat_id=callback_query.from_user.id, reply_markup=await result_home(language))
    try:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 2)
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 1)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest as e:
        pass


@dp.callback_query(F.data.startswith("result_"))
async def result(callback_query: CallbackQuery):
    data = callback_query.data.split('_')[1]
    if data == 'English':
        await send_certificate(bot, callback_query.from_user.id, callback_query)


# ------------------------------------Middleware------------------------------------------------------------------------#
class TestMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        if isinstance(event, Update) and event.message:
            message: Message = event.message
            user_id = message.from_user.id
            username = message.from_user.username or "No username"
            text = message.text
            print(f"User ID: {user_id}, Username: {username}, Message: {text}")
        result = await handler(event, data)
        return result


dp.update.middleware(TestMiddleware())


@dp.message(CommandStart)
async def deleter(message: Message):
    try:
        sleep(0.4)
        for _ in range(10):
            await message.delete()
        await delete_previous_messages(message.message_id, message.from_user.id)
    except TelegramBadRequest as error:
        print("Failed to delete message:", error)


# --------------------------------- Polling the bot ---------------------------------------------------------------------#
async def main():
    await init()
    print(f'Bot stareted at {formatted_time}')
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f'Bot stopped by Ctrl+C at {formatted_time}')
    except Exception as e:
        print(f'Unexpected error: {e}')

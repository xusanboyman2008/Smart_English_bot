import asyncio
import os
import traceback
from datetime import datetime
from time import localtime
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, TelegramObject, Update, \
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile, ReplyKeyboardRemove
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean, update, select
from sqlalchemy.exc import MultipleResultsFound
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


# -------------------------------------time-----------------------------------------------------------------------------#
current_time = localtime()
current_year = current_time.tm_year
start_time = datetime.now()
formatted_time = start_time.strftime("%d/%m/%Y %H:%M")


# ----------------------------------create table and its volumes--------------------------------------------------------#
class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    FIO = Column(String, nullable=True)
    tg_name = Column(String, nullable=False)
    tg_username = Column(String, nullable=True)
    tg_number = Column(Integer, unique=True, nullable=True)
    gender = Column(String, nullable=True)
    born_year = Column(String, nullable=True)
    language = Column(String, nullable=True)
    role = Column(String, nullable=False, default='User')
    registered = Column(Boolean, nullable=False, default=False)
    register_time = Column(String, nullable=True, default=formatted_time)


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
    tg_id = Column(String, unique=False, nullable=False)
    telegram_information = Column(String, ForeignKey(User.tg_id, ondelete='CASCADE'))
    is_connected = Column(String, nullable=False, default='no')
    comment_for_call = Column(String, nullable=False, default='')
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
    is_deleted = Column(String, default='False', nullable=True)  # Soft delete flag
    register_time = Column(DateTime, nullable=True)


class Hire_employee(Base):
    __tablename__ = 'Hire_employee'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False, unique=True)
    tg_username = Column(String, nullable=False, default='no')
    number = Column(String, nullable=False, default='not yet')
    name = Column(String, nullable=False)
    year = Column(String, nullable=False)
    certificate = Column(String, nullable=False, default=False)
    experience = Column(String, nullable=False, default=False)
    image = Column(String, nullable=False, default='./Hire/.💁‍♂️ Asistent ️/Abdulkhaev_Xusabvoy_Solijonivich.jpg')
    register_time = Column(DateTime, nullable=True)


class Complain_db(Base):
    __tablename__ = 'Complains'
    id = Column(Integer, primary_key=True)
    to_whom = Column(String, nullable=False)
    teacher_type = Column(String, nullable=False)
    text = Column(String, nullable=False)
    level = Column(String, nullable=False, default='Not chosen')
    time = Column(String, nullable=False, default=formatted_time)
    complainer_tg_id = Column(Integer, ForeignKey(User.tg_id, ondelete='CASCADE'))


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


async def back_home(language):
    text = {'uz': ['🏠 Bosh menu', f'🔙 Orqaga']}
    row = []
    for i in text.get(language):
        row.append(KeyboardButton(text=i))
    keyboard_button = ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)
    return keyboard_button


async def call_centre():
    async with async_session() as session:
        stmt = select(User.tg_id).where(User.role == 'Call centre')
        result1 = await session.execute(stmt)
        user_language = result1.scalars().all()
        return user_language


async def user_role(tg_id):
    async with async_session() as session:
        stmt = select(User.role).where(User.tg_id == tg_id)
        result1 = await session.execute(stmt)
        user_language = result1.scalar_one_or_none()
        return user_language


async def add_user(tg_id: int, username: str, name: str) -> None:
    async with async_session() as session:
        # Check if user already exists
        existing_user = await session.execute(select(User).where(User.tg_id == tg_id))
        if existing_user.scalar_one_or_none():
            return  # User already exists, so we do not add them again

        new_user = User(tg_id=tg_id, tg_username=username, tg_name=name, language="en")
        session.add(new_user)
        await session.commit()


async def add_complainer(tg_id: int, text: str, to_whom: str, type: str) -> None:
    async with async_session() as session:
        new_user = Complain_db(complainer_tg_id=tg_id, to_whom=to_whom, text=text, teacher_type=type)
        session.add(new_user)
        await session.commit()


async def add_user_full(tg_id: int, username: str, name: str, number: str, fullname: str, born_year: str,
                        gender: str) -> None:
    async with async_session() as session:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        update_stmt = (update(User).where(User.tg_id == tg_id).values(tg_username=username, tg_name=name, gender=gender,
                                                                      born_year=born_year, FIO=fullname,
                                                                      tg_number=number))
        await session.execute(update_stmt)
        await session.commit()


async def hire_employee(tg_id: int, username: str, name: str, year: str, certificate: str, experience: str,
                        image: str, ) -> None:
    async with async_session() as session:
        new_user = Hire_employee(tg_id=tg_id, tg_username=username, name=name, year=year, certificate=certificate,
                                 experience=experience, image=image)
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
            try:
                user = result.scalar_one_or_none()
            except MultipleResultsFound:
                user = result.scalars().first()
        else:
            # If user does not exist, create a new entry
            session.add(User(tg_id=tg_id, language=language))

        # Commit the changes
        await session.commit()


async def set_register_state_yes(tg_id, is_connected, comment):
    async with async_session() as session:
        # Select the user
        stmt = select(Registering).where(Registering.tg_id == tg_id)
        result = await session.execute(stmt)
        update_stmt = (update(Registering).where(Registering.tg_id == tg_id).values(is_connected=is_connected,
                                                                                    comment_for_call=comment))
        await session.execute(update_stmt)
        await session.commit()


async def changer_user_role(user_id, new_role):
    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        update_stmt = (update(User).where(User.id == user_id).values(role=new_role))
        await session.execute(update_stmt)
        await session.commit()
        return True


async def complain_user_level(tg_id, level):
    async with async_session() as session:
        update_stmt = update(Complain_db).where(Complain_db.complainer_tg_id == tg_id).values(level=level)
        await session.execute(update_stmt)
        await session.commit()
        return True


async def register_result_en(fullname: str, writing: str, listening, reading: str, speaking: str, image: str,
                             band: str):
    async with async_session() as session:
        new_user = Results_English(fullname=fullname, writing=writing, listening=listening, reading=reading,
                                   speaking=speaking, image=image, Overall_Band=band)
        session.add(new_user)
        await session.commit()


async def register(tg_id: str, name: str, phone_number: str, course: str, level: str, course_time: str,
                   user_gender: str, born_year: str, tg_id_real, ):
    async with async_session() as session:
        async with session.begin():
            await session.execute(select(Registering).where(Registering.tg_id == tg_id_real))
            new_user = Registering(user_name=name, number=phone_number, course=course, level=level, time=course_time,
                                   gender=user_gender, telegram_information=tg_id, born_year=born_year,
                                   tg_id=tg_id_real, )
            session.add(new_user)

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()


async def get_user_by_tg_id(tg_id):
    async with async_session() as session:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        return user


async def get_result_english(id):
    async with async_session() as session:
        stmt = select(Results_English).where(Results_English.id == id)  # Check for the specific tg_id
        result = await session.execute(stmt)
        user_role = result.all()  # Fetch the role or None if not found
        return user_role


async def delete_call(tg_id):
    async with async_session() as session:
        stmt = select(Registering).where(Registering.tg_id == tg_id)
        result = await session.execute(stmt)
        records = result.scalars().all()  # Fetch the single record

        if records:  # Check if record exists
            for record in records:
                await session.delete(record)  # Mark the record for deletion
                await session.commit()
        return None


async def manager():
    async with async_session() as session:
        stmt = select(User.tg_id).where(User.role == 'Admin')
        result1 = await session.execute(stmt)
        user_language = result1.scalars().all()
        return user_language


async def all_users(tg_id):
    async with async_session() as session:
        stmt = select(User).where(User.tg_id != tg_id)
        result = await session.execute(stmt)  # Executes the query
        user_ids = result.scalars().all()  # Fetches all tg_ids as a list
        return user_ids


async def all_users_to_register(tg_id):
    async with async_session() as session:
        stmt = select(Registering).where(Registering.tg_id == tg_id)
        result = await session.execute(stmt)  # Executes the query
        user_id = result.scalars().all()
        return user_id


async def get_single_role(tg_id):
    async with async_session() as session:
        stmt = select(User).where(User.id == tg_id)
        result = await session.execute(stmt)  # Executes the query
        user_ids = result.scalar()
        return user_ids


async def get_user_role(tg_id):
    async with async_session() as session:
        stmt = select(User.role).where(User.tg_id == tg_id)  # Check for the specific tg_id
        result = await session.execute(stmt)
        user_role = result.scalar_one_or_none()  # Fetch the role or None if not found
        return user_role


async def delete_results_en(tg_id):
    async with async_session() as session:
        # Fetch the entire object instead of just one column
        stmt = select(Results_English).where(Results_English.id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.is_deleted = True  # Set the attribute (use a boolean, not a string)
            await session.commit()  # Save changes to the database


async def change_user_language(tg_id, language):
    async with async_session() as session:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.language = language  # Set the attribute (use a boolean, not a string)
            await session.commit()  # Save changes to the database


async def take_admin(tg_id):
    async with async_session() as session:
        # Query the database for the role of the user with the given tg_id
        result = await session.execute(select(User.role).where(User.tg_id == tg_id))
        user_role = result.scalar()  # Extract the scalar value (User.role)

        # Return True if the user role is 'Admin', otherwise False
        return user_role == 'Admin'


async def all_complains():
    async with async_session() as session:
        stmt = select(Complain_db)
        result = await session.execute(stmt)  # Executes the query
        user_ids = result.scalars().all()  # Fetches all tg_ids as a list
        return user_ids


async def all_registred_students():
    async with async_session() as session:
        stmt = select(Registering)
        result = await session.execute(stmt)  # Executes the query
        user_ids = result.scalars().all()  # Fetches all tg_ids as a list
        return user_ids


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


class Hire(StatesGroup):
    start = State()
    name = State()
    year = State()
    stater = State()
    state_fake = State()
    experience = State()
    is_certificate = State()
    image_certificate = State()


class Call(StatesGroup):
    tg_id_user = State()
    comment = State()


class Complain(StatesGroup):
    start = State()
    teacher_type = State()
    teacher_name = State()
    message = State()


class Suggestions(StatesGroup):
    start = State()


class send_message_to_user(StatesGroup):
    tg_id = State()
    message = State()


class Register_full(StatesGroup):
    start = State()
    fullname = State()
    number = State()
    gender = State()
    year = State()
    month = State()
    day = State()
    fake_month = State()
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

    # Loop through the language list to create buttons
    for i in lan:
        # Add button text (exclude the flag) and callback data (first 2 chars of the language code)
        row.append(InlineKeyboardButton(text=f'{i[2:]}', callback_data=f"lan_{i[:2]}_"))
        if len(row) == 3:  # Add up to 3 buttons in one row
            inline_button.append(row)
            row = []

    # Add any remaining buttons
    if row:
        inline_button.append(row)

    # Create inline keyboard markup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def flanguages(language):
    lan = {'uz': ["uz🇺🇿 O'zbek tili", 'ru🇷🇺 Русский язык', "en🇺🇸 English"],
           'en': ["uz🇺🇿 O'zbek tili", 'ru🇷🇺 Русский язык', "en🇺🇸 English"],
           'ru': ["uz🇺🇿 O'zbek tili", 'ru🇷🇺 Русский язык', "en🇺🇸 English"], }

    inline_button = []
    row = []

    lang_text = lan.get(language, [])  # Default to empty list if not found

    # Loop through each language text and create a button
    for text in lang_text:
        # Split the string into parts (flag and language name)
        flag = text.split()[0]  # The first part is the flag
        language_name = " ".join(text.split()[1:])  # The rest is the language name

        # Add the button to the row
        row.append(InlineKeyboardButton(text=f'{flag} {language_name}', callback_data=f"lan_{text[:2]}_"))

        # If the row has 3 buttons, append it and reset the row
        if len(row) == 3:
            inline_button.append(row)
            row = []

    # If there's any remaining buttons in the row, append it
    if row:
        inline_button.append(row)

    # Create inline keyboard markup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def scores(language, category, before, band):
    inline_button = []
    row = []

    # Setting text based on the language
    if language == 'en':
        text1 = '🚫 Cancel'
        text2 = '🔙 Back'
    elif language == 'uz':
        text1 = '🚫 Bekor qilish'
        text2 = '🔙 Orqaga'
    else:  # Assuming Russian for other cases
        text1 = '🚫 Отмена'  # Russian translation for 'Cancel'
        text2 = '🔙 Назад'  # Russian translation for 'Back'

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
            menu = ['gender_man.🤵 Мужчина', 'gender_women.👩 Женщина']  # Russian translation for 'Man' and 'Woman'
        case 'en':
            menu = ['gender_man.🤵 Man', 'gender_women.👩 Woman']
        case _:
            menu = ['gender_man.🤵 Erkak kishi', 'gender_women.👩 Ayol kishi']

    inline_button = []
    row = []

    for i in menu:
        # Check if the state is True to modify callback data
        if is_state:
            row.append(InlineKeyboardButton(text=f"{i.split('_')[1].split('.')[1]}",
                                            callback_data=f"state.{i.split('_')[0]}_{i.split('_')[1]}"))
        else:
            row.append(InlineKeyboardButton(text=f"{i.split('_')[1].split('.')[1]}", callback_data=f"{i}"))

        # Add to inline buttons when there are 2 buttons in the row
        if len(row) == 2:
            inline_button.append(row)
            row = []

    # Add "Home" and "Back" buttons
    inline_button.append([InlineKeyboardButton(text='🏠 Bosh menu', callback_data="menu_"),
                          InlineKeyboardButton(text='🔙 Ortga', callback_data="Register_number_")])

    # Append remaining row if exists
    if row:
        inline_button.append(row)

    # Create InlineKeyboardMarkup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def kb_complain(language):
    inline_button = []
    row = []
    text = {'uz': ['s_complain_.✅ Tastiqlash va yuborish', 'complain_.🔄 Qaytadan', 'menu_.🏠 Bosh menu'],
            'ru': ['s_complain_.✅ Tastiqlash va yuborish', 'complain_.🔄 Qaytadan', 'menu_.🏠 Bosh menu'],
            'en': ['s_complain_.✅ Tastiqlash va yuborish', 'complain_.🔄 Qaytadan', 'menu_.🏠 Bosh menu'], }
    for i in text.get(language):
        row.append(InlineKeyboardButton(text=f"{i.split('.')[1]}", callback_data=f"{i.split('.')[0]}"))
        if len(row) == 2:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def month_audio():
    inline_button = []
    row = []
    text = ['?audio_Kids.🧸 Kids', '?audio_Intermediate.🕰️ Intermediate', '?audio_Adult.🧑‍🎓 Adult',
            '?audio_IELTS.🏆 IELTS', 'menu_.🏠 Bosh sahifa']
    for i in range(len(text)):
        row.append(InlineKeyboardButton(text=text[i].split('.')[1], callback_data=f"{text[i].split('.')[0]}"))
        if len(row) == 4:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def home(language, tg_id):
    inline_button = []
    row = []
    if await take_admin(tg_id):
        text = {'uz': ['courses_.✍️ Kursga yozilish', 'results.🏆 Natijalar', 'audio_.🔊 Audio materiallar',
                       'complain_.📌 Shikoyat qilish', 'hire_.👨‍💼 Xodimlar', 'admin_.🤴🏻 Admin kasbga qoyish',
                       'all_complains_.🎯 Barcha shikoyatlar', 'all_registration_.📜 Barcha registratsiyalar',
                       'settings.⚙️ Sozlamalar'],
                'ru': ['courses_.✍️ Записаться на курс', 'results.🏆 Результаты', 'audio_.🔊 Аудио материалы',
                       'complain_.📌 Подать жалобу', 'hire_.👨‍💼 Сотрудники', 'admin_.🤴🏻 Назначить на должность админа',
                       'all_complains_.🎯 Все жалобы', 'all_registration_.📜 Все регистрации', 'settings.⚙️ Настройки'],
                'en': ['courses_.✍️ Enroll in a course', 'results.🏆 Results', 'audio_.🔊 Audio materials',
                       'complain_.📌 File a complaint', 'hire_.👨‍💼 Employees', 'admin_.🤴🏻 Assign admin role',
                       'all_complains_.🎯 All complaints', 'all_registration_.📜 All registrations',
                       'settings.⚙️ Settings'], }
        for i in text.get(language):
            row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f"{i.split('.')[0]}"))
            if len(row) == 3:
                inline_button.append(row)
                row = []
        if row:
            inline_button.append(row)
    if not await take_admin(tg_id):
        text2 = {'uz': ['courses_.✍️ Kursga yozilish', 'results.🏆 Natijalar', 'audio_.🔊 Audio materiallar',
                        'complain_.📌 Shikoyat qilish', 'hire_.👨‍💼 Xodimlar', 'settings.⚙️ Sozlamalar'],
                 'ru': ['courses_.✍️ Записаться на курс', 'results.🏆 Результаты', 'audio_.🔊 Аудио материалы',
                        'complain_.📌 Подать жалобу', 'hire_.👨‍💼 Сотрудники', 'settings.⚙️ Настройки'],
                 'en': ['courses_.✍️ Enroll in a course', 'results.🏆 Results', 'audio_.🔊 Audio materials',
                        'complain_.📌 File a complaint', 'hire_.👨‍💼 Employees', 'settings.⚙️ Settings'], }
        for i in text2.get(language):
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
            menu = ['result_English.🇺🇸 Результаты по английскому', 'result_IT.💻 Результаты по IT',
                    'menu_.🏠 Вернуться на главную']
        case _:
            menu = ['result_English.🇺🇸 Results in English', 'result_IT.💻 IT Results', 'menu_.🏠 Return to home']

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
            menu = ['English_🇺🇸 Английский язык', 'IT_💻 ИТ', 'Matematika_✒️ Математика', 'Tarix_🔶 История',
                    'Arab tili_🔶 Арабский язык']
            inline_button = []
            row = []
            for i in menu:
                row.append(InlineKeyboardButton(text=f'{i.split("_")[1]}', callback_data=f"register_{i.split('_')[0]}"))
                if len(row) == 3:
                    inline_button.append(row)
                    row = []
            if row:
                inline_button.append(row)
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
            return inline_keyboard
        case 'en':
            menu = ['English_🇺🇸 English Language', 'IT_💻 IT', 'Matematika_✒️ Mathematics', 'Tarix_🔶 History',
                    'Arab tili_🔶 Arabic Language']
            inline_button = []
            row = []
            for i in menu:
                row.append(InlineKeyboardButton(text=f'{i.split("_")[1]}', callback_data=f"register_{i.split('_')[0]}"))
                if len(row) == 3:
                    inline_button.append(row)
                    row = []
            if row:
                inline_button.append(row)
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
            return inline_keyboard


async def month(language, gender):
    # Month dictionary with custom names for each language
    match language:
        case 'uz':
            months = {12: '12🎄 Dekabr',  # December
                      1: '01❄️ Yanvar',  # January
                      2: '02🌸 Fevral',  # February
                      3: '03🌷 Mart',  # March
                      4: '04🌱 Aprel',  # April
                      5: '05🌞 May',  # May
                      6: '06☀️ Iyun',  # June
                      7: '07🌞 Iyun',  # July
                      8: '08🌅 Avgust',  # August
                      9: '09🎒 Sentabr',  # September
                      10: '10🍂 Oktabr',  # October
                      11: '11🌧️ Noyabr'  # November
                      }
        case 'ru':
            months = {12: '12🎄 Декабрь',  # December
                      1: '01❄️ Январь',  # January
                      2: '02🌸 Февраль',  # February
                      3: '03🌷 Март',  # March
                      4: '04🌱 Апрель',  # April
                      5: '05🌞 Май',  # May
                      6: '06☀️ Июнь',  # June
                      7: '07🌞 Июль',  # July
                      8: '08🌅 Август',  # August
                      9: '09🎒 Сентябрь',  # September
                      10: '10🍂 Октябрь',  # October
                      11: '11🌧️ Ноябрь'  # November
                      }
        case 'en':
            months = {12: '12🎄 December',  # December
                      1: '01❄️ January',  # January
                      2: '02🌸 February',  # February
                      3: '03🌷 March',  # March
                      4: '04🌱 April',  # April
                      5: '05🌞 May',  # May
                      6: '06☀️ June',  # June
                      7: '07🌞 July',  # July
                      8: '08🌅 August',  # August
                      9: '09🎒 September',  # September
                      10: '10🍂 October',  # October
                      11: '11🌧️ November'  # November
                      }
        case _:
            # Default to Uzbek if language is unknown
            months = {12: '12🎄 Dekabr',  # December
                      1: '01❄️ Yanvar',  # January
                      2: '02🌸 Fevral',  # February
                      3: '03🌷 Mart',  # March
                      4: '04🌱 Aprel',  # April
                      5: '05🌞 May',  # May
                      6: '06☀️ Iyun',  # June
                      7: '07🌞 Iyun',  # July
                      8: '08🌅 Avgust',  # August
                      9: '09🎒 Sentabr',  # September
                      10: '10🍂 Oktabr',  # October
                      11: '11🌧️ Noyabr'  # November
                      }

    inline_buttons = []
    row = []

    # Button creation for each month
    for num, label in months.items():
        row.append(InlineKeyboardButton(text=label[2:],
                                        callback_data=f'month_{label[:2]}_{label}'))  # Removing the number part
        if len(row) == 3:  # Limit to 3 buttons per row
            inline_buttons.append(row)
            row = []
    if row:  # Add any remaining buttons to the last row
        inline_buttons.append(row)

    # Language-specific footer buttons
    if language == 'en':
        row.append(InlineKeyboardButton(text="🏠 Home", callback_data='menu_'))
        row.append(InlineKeyboardButton(text="🔙 Back", callback_data=f'gender_.{gender}'))
    elif language == 'ru':
        row.append(InlineKeyboardButton(text="🏠 Home", callback_data='menu'))
        row.append(InlineKeyboardButton(text="🔙 Back", callback_data=f'gender_.{gender}'))
    elif language == 'uz':
        row.append(InlineKeyboardButton(text="🏠 Bosh menu", callback_data='menu_'))
        row.append(InlineKeyboardButton(text="🔙 Ortga", callback_data=f'gender_.{gender}'))

    if row:  # Add any remaining footer buttons
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
                           InlineKeyboardButton(text='🔙 Orqaga', callback_data=f'year_{year}')])
    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_kb


async def share_phone_number(language):
    # Define the text for the button based on the language
    match language:
        case 'en':
            button_text = "📱 Share phone number"
            back_text = "🔙 Back"
        case 'uz':
            button_text = "📱 Telefon raqamni yuborish"
            back_text = "🔙 Ortga"
        case 'ru':
            button_text = "📱 Поделиться номером телефона"
            back_text = "🔙 Назад"
        case _:
            button_text = "📞 Share number"
            back_text = "🔙 Back"

    # Create the share phone number button
    share_phone_button = KeyboardButton(text=button_text, request_contact=True)

    # Create the back button
    back_button = KeyboardButton(text=back_text)

    # Define the keyboard layout with the share phone number button and back button
    keyboard = ReplyKeyboardMarkup(keyboard=[[share_phone_button], [back_button]],
                                   # Two rows: one with share phone button, one with back button
                                   resize_keyboard=True, one_time_keyboard=True, selective=True,
                                   input_field_placeholder="Enter your phone number")

    return keyboard


async def create_inline_keyboard(menu, max_buttons_per_row=2):
    inline_button = []
    row = []
    for item in menu:
        row.append(
            InlineKeyboardButton(text=item.split(".")[1], callback_data=f'{item.split(".")[0]}.'  # Changed to level_
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

    # Define the button texts based on the selected language
    match language:
        case 'uz':
            more_button = 'more.⚙️ Boshqa oyni tanlash'
            level_kids = 'level_kids.⭐️ Kids'
            level_intermittent = 'level_intermittent.⭐️ Intermittent'
            level_adult = 'level_adult.⭐️ Adult'
            level_ielt = 'level_ielt.⭐️ IELTS'
        case 'ru':
            more_button = 'more.⚙️ Больше месяцев'
            level_kids = 'level_kids.⭐️ Дети'
            level_intermittent = 'level_intermittent.⭐️ Промежуточный'
            level_adult = 'level_adult.⭐️ Взрослый'
            level_ielt = 'level_ielt.⭐️ IELTS'
        case 'en':
            more_button = 'more.⚙️ Choose another month'
            level_kids = 'level_kids.⭐️ Kids'
            level_intermittent = 'level_intermittent.⭐️ Intermittent'
            level_adult = 'level_adult.⭐️ Adult'
            level_ielt = 'level_ielt.⭐️ IELTS'
        case _:
            return None  # For unsupported languages, return None

    # Build the menu based on the age
    if age <= 12:
        menu = [level_kids, more_button]
        return await create_inline_keyboard(menu, max_buttons_per_row=2)
    elif age <= 14:
        menu = [level_kids, level_intermittent, more_button]
        return await create_inline_keyboard(menu, max_buttons_per_row=3)
    elif age >= 16:
        menu = [level_kids, level_intermittent, level_adult, level_ielt]
        return await create_inline_keyboard(menu, max_buttons_per_row=4)

    return None


async def level_more(language, day, month_name):
    text = {'uz': ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                   'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', f'month_{day}_{month_name}.🔙 Ortga'],
            'ru': ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                   'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', f'month_{day}.🔙 Ortga'],
            'en': ['level_kids.⭐️ Kids', 'level_intermittent.⭐️ Intermittent', 'level_adult.⭐️ Adult',
                   'level_ielt.⭐️ IELTS', 'menu_.🏠 Bosh menuga qaytish', f'month_{day}.🔙 Ortga'], }

    inline_button = []
    row = []

    # Build buttons for each text item based on the language
    for item in text.get(language):
        button_text = item.split('.')[1]  # Get text after the period (button label)
        callback_data = item.split('.')[0]  # Get text before the period (callback data)

        row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))

        # Add buttons to the row and limit the number of buttons per row
        if len(row) == 2:  # Adjust the number of buttons per row if needed
            inline_button.append(row)
            row = []

    # If there are leftover buttons in the row, add them to the inline_keyboard
    if row:
        inline_button.append(row)

    # Return the inline keyboard markup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def call(number, tg_id, langugae):
    inline_button = []
    inline_button.append([InlineKeyboardButton(text='🤙 Telefon raqamni olib qoyish ⚠️⚠️⚠️ maslahat beriladi',
                                               switch_inline_query=number)])
    row = []
    text = {'uz': [f'☎️ Telefon qildim. called_{tg_id}', f'🗑️ Bu telefon raqamni ochirish. broken_{tg_id}'],
            'ru': [f'☎️ Я позвонил. called_{tg_id}', f'🗑️ Удалить этот номер телефона. broken_{tg_id}'],
            'en': [f'☎️ I made a call. called_{tg_id}', f'🗑️ Delete this phone number. broken_{tg_id}']}
    for i in text.get(langugae):
        row.append(InlineKeyboardButton(text=f"{i.split('.')[0]}", callback_data=f"{i.split('.')[1]}"))
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def register_english(page):
    inline_keyboard = []
    row = []

    if int(page) == 1:
        for i in range(current_year - 11, current_year - 28, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'year_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 1
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'2year_{3}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'2year_{2}')])

    elif int(page) == 2:
        for i in range(current_year - 28, current_year - 45, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'year_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 2
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'2year_{1}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'2year_{3}')])

    elif int(page) == 3:
        for i in range(current_year - 45, current_year - 62, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'year_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 3
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'2year_{2}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'2year_{1}')])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return inline_keyboard


async def confirmt(language, is_state):
    # Define the menu text for all languages
    menu = {'uz': ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash', 'menu_.🚫 Bekore qilish'],
            'ru': ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash', 'menu_.🚫 Bekore qilish'],
            'en': ['confirm_.✅ Tastiqlash', 'register_.🔄 Qaytatan ishlash', 'menu_.🚫 Bekore qilish'], }

    # Default to 'en' language if no match
    menu = menu.get(language, menu['en'])

    inline_buttons = []
    row = []

    # Loop through the menu items and create buttons
    for i in menu:
        button_text = i.split(".")[1]  # Extract text after the period
        callback_data = f'state_{i.split(".")[0]}' if is_state else i.split('.')[0]  # Set callback data based on state

        row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))

        # Append row to buttons every 2 items
        if len(row) == 2:
            inline_buttons.append(row)
            row = []

    # Append any remaining buttons in the last row
    if row:
        inline_buttons.append(row)

    # Return the inline keyboard markup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_keyboard


async def call_confirm_yes(language):
    text = {'uz': ['ycall_yes_.✅ Ha', 'ycall_no_.❌ Yoʻq'], 'ru': ['ycall_yes_.✅ Да', 'ycall_no_.❌ Нет'],
            'en': ['ycall_yes_.✅ Yes', 'ycall_no_.❌ No'], }
    inline_button = []
    for i in text.get(language):
        inline_button.append([InlineKeyboardButton(text=i.split(".")[1], callback_data=f'{i.split(".")[0]}')])
    return InlineKeyboardMarkup(inline_keyboard=inline_button)


async def time_en(language, day, course):
    match language:
        case 'uz':
            menu = ['time_08:00 dan 09:30.', 'time_09:30 dan 11:00.', 'time_11:00 dan 12:30.', 'time_13:00 dan 14:30.',
                    'time_16:00 dan 5:30.']
        case 'ru':
            menu = ['time_08:00 до 09:30', 'time_09:30 до 11:00', 'time_11:00 до 12:30', 'time_13:00 до 14:30',
                    'time_16:00 до 5:30']
        case 'en':
            menu = ['time_08:00 to 09:30', 'time_09:30 to 11:00', 'time_11:00 to 12:30', 'time_13:00 to 14:30',
                    'time_16:00 to 5:30']
        case _:
            menu = ['time_08:00 to 09:30', 'time_09:30 to 11:00', 'time_11:00 to 12:30', 'time_13:00 to 14:30',
                    'time_16:00 to 5:30']

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
    if course == 'English':
        inline_button.append([InlineKeyboardButton(text='🏠 Home', callback_data='menu_'),
                              InlineKeyboardButton(text='🔙 Back', callback_data=f'day_{day}')])
    else:
        inline_button.append([InlineKeyboardButton(text='🏠 Home', callback_data='menu_'),
                              InlineKeyboardButton(text='🔙 Back', callback_data=f'month_{day}')])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def audio_home(language):
    text = {'uz': ['/audio_home_vt_.📹 (VT) materiallar', '/audio_home_mt_.👨‍🏫 (MT) materiallar', 'menu_.🏠 Bosh menu'],
            'ru': ['/audio_home_vt_.📹 (VT) материалы', '/audio_home_mt_.👨‍🏫 (MT) материалы', 'menu_.🏠 Главное меню'],
            'en': ['/audio_home_vt_.📹 (VT) materials', '/audio_home_mt_.👨‍🏫 (MT) materials', 'menu_.🏠 Main menu'], }

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

    for i in range(1, 17):
        row.append(InlineKeyboardButton(text=f'{i} Month', callback_data=f'.audio_month_{i}_{data}'))
        if len(row) == 3:  # Add up to 3 buttons in one row
            inline_button.append(row)
            row = []

    if row:  # Add any remaining buttons
        inline_button.append(row)

    # Texts for different languages
    text = {'uz': 'menu_.🏠 Bosh sahifa', 'ru': 'menu_.🏠 Бош меню', 'en': 'menu_.🏠 Home', }

    # Add home button
    inline_button.append([InlineKeyboardButton(text=text.get(language).split('.')[1],  # Get the button text
                                               callback_data=f"{text.get(language).split('.')[0]}")])

    # Create inline keyboard markup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def hire(language):
    text = {'uz': ['type_main_.🧑‍🏫 O‘qituvchi (MT)',  # Main Teacher - 🧑‍🏫 (Teacher)
                   'type_assistant_.🧑‍💼 Assistent',  # Assistant - 🧑‍💼 (Office worker)
                   'type_examiner_.📝 Imtihon oluvchi (Examiner)',  # Examiner - 📝 (Writing)
                   'type_video_.🖥️ O‘qituvchi (VT)',  # Video Teacher - 🖥️ (Computer)
                   'menu_.🏠 Bosh menu'  # Main Menu - 🏠 (House)
                   ], 'ru': ['type_main_.🧑‍🏫 Учитель (MT)',  # Main Teacher - 🧑‍🏫 (Teacher)
                             'type_assistant_.🧑‍💼 Ассистент',  # Assistant - 🧑‍💼 (Office worker)
                             'type_examiner_.📝 Экзаменатор',  # Examiner - 📝 (Writing)
                             'type_video_.🖥️ Учитель (VT)',  # Video Teacher - 🖥️ (Computer)
                             'menu_.🏠 Главное меню'  # Main Menu - 🏠 (House)
                             ], 'en': ['type_main_.🧑‍🏫 Teacher (MT)',  # Main Teacher - 🧑‍🏫 (Teacher)
                                       'type_assistant_.🧑‍💼 Assistant',  # Assistant - 🧑‍💼 (Office worker)
                                       'type_examiner_.📝 Examiner',  # Examiner - 📝 (Writing)
                                       'type_video_.🖥️ Teacher (VT)',  # Video Teacher - 🖥️ (Computer)
                                       'menu_.🏠 Main menu'  # Main Menu - 🏠 (House)
                                       ]}

    inline_button = []
    row = []
    for i in text.get(language):
        row.append(
            InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f'{i.split(".")[0]}.{i.split(".")[1]}'))
        if len(row) == 4:
            inline_button.append(row)
            row = []
    if row:
        inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def yhire(page):
    inline_keyboard = []
    row = []

    if int(page) == 1:
        for i in range(current_year - 11, current_year - 28, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'hyear_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 1
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'hyear2_{3}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'hyear2_{2}')])

    elif int(page) == 2:
        for i in range(current_year - 28, current_year - 45, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'hyear_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 2
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'hyear2_{1}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'hyear2_{3}')])

    elif int(page) == 3:
        for i in range(current_year - 45, current_year - 62, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'hyear_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 3
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'hyear2_{2}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'hyear2_{1}')])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return inline_keyboard


async def hexperience(language, data):
    if data == 'experience':
        text = {'uz': ['hexperience_yes_.✅ Ha', 'hexperience_no_.❌ Yo\'q', 'menu_.🏠 Bosh menu', 'type_.🔙 Orqaga'],
                'ru': ['hexperience_yes_.✅ Да', 'hexperience_no_.❌ Нет', 'menu_.🏠 Главное меню', 'type_.🔙 Назад'],
                'en': ['hexperience_yes_.✅ Yes', 'hexperience_no_.❌ No', 'menu_.🏠 Main menu', 'type_.🔙 Back']}
    else:
        text = {
            'uz': ['is/certificate_yes_.✅ Ha', 'is/hexperience_no_.❌ Yo\'q', 'menu_.🏠 Bosh menu', 'yhire_.🔙 Orqaga'],
            'ru': ['is/certificate_yes_.✅ Да', 'is/hexperience_no_.❌ Нет', 'menu_.🏠 Главное меню', 'yhire_.🔙 Назад'],
            'en': ['is/certificate_yes_.✅ Yes', 'is/hexperience_no_.❌ No', 'menu_.🏠 Main menu', 'yhire_.🔙 Back']}

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


async def conifim_hire(language):
    text = {'uz': ['cconifim_.✅ Hammasi tog\'ri', 'hire_.♻️ Boshqatan', 'menu_.🏠 Bosh menu'],
            'ru': ['cconifim_.✅ Все верно', 'hire_.♻️ Еще раз', 'menu_.🏠 Главное меню'],
            'en': ['cconifim_.✅ Everything is correct', 'hire_.♻️ Try again', 'menu_.🏠 Main menu']}

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


async def change_user_role(language, current_role, user_id):
    role_options = {
        'uz': [f'user_role_{user_id}_Call centre.📋 Registrator', f'user_role_{user_id}_User.👤 Foydalanuvchi',
               f'user_role_{user_id}_Manager.👨‍💼 Manager'],
        'ru': [f'user_role_{user_id}_Call centre.📋 Регистратор', f'user_role_{user_id}_User.👤 Пользователь',
               f'user_role_{user_id}_Manager.👨‍💼 Менеджер'],
        'en': [f'user_role_{user_id}_Call centre.📋 Registrar', f'user_role_{user_id}_User.👤 User',
               f'user_role_{user_id}_Manager.👨‍💼 Manager']}

    roles = role_options.get(language, [])
    inline_button = []
    row = []

    for role in roles:
        callback_data, display_text = role.split('.')
        role_name = callback_data.split('_')[3]
        if role_name == current_role:
            continue
        row.append(InlineKeyboardButton(text=display_text, callback_data=callback_data))
        if len(row) == 3:
            inline_button.append(row)
            row = []  # Reset the row
    if row:
        inline_button.append(row)
    text2 = {'uz': f'send_message_{user_id}.✉️ Xabar yuborish', 'ru': f'send_message_{user_id}.✉️ Отправить сообщение',
             'en': f'send_message_{user_id}.✉️ Send a message'}

    inline_button.append(
        [InlineKeyboardButton(text=text2.get(language).split('.')[1], callback_data=text2.get(language).split(".")[0])])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def compilationkb(language):
    inline_keyboard = []
    row = []
    text = {'uz': ['c_teacher_main.🧑‍🏫 (Main) O‘qituvchi',  # Main Teacher - 🧑‍🏫 (Teacher)
                   'c_teacher_assistant.🧑‍💼 Assistent',  # Assistant - 🧑‍💼 (Office worker)
                   'c_teacher_examiner.📝 Imtihon oluvchi',  # Examiner - 📝 (Writing)
                   'c_teacher_video.🎞 (Video) O‘qituvchi',  # Video Teacher - 🎞 (Movie)
                   'menu_.🏠 Bosh menu'  # Main Menu - 🏠 (House)
                   ], 'ru': ['c_teacher_main.🧑‍🏫 (Main) Учитель',  # Main Teacher - 🧑‍🏫 (Teacher)
                             'c_teacher_assistant.🧑‍💼 Ассистент',  # Assistant - 🧑‍💼 (Office worker)
                             'c_teacher_examiner.📝 Экзаменатор',  # Examiner - 📝 (Writing)
                             'c_teacher_video.🎞 (Video) Учитель',  # Video Teacher - 🎞 (Movie)
                             'menu_.🏠 Главное меню'  # Main Menu - 🏠 (House)
                             ], 'en': ['c_teacher_main.🧑‍🏫 (Main) Teacher',  # Main Teacher - 🧑‍🏫 (Teacher)
                                       'c_teacher_assistant.🧑‍💼 Assistant',  # Assistant - 🧑‍💼 (Office worker)
                                       'c_teacher_examiner.📝 Examiner',  # Examiner - 📝 (Writing)
                                       'c_teacher_video.🎞 (Video) Teacher',  # Video Teacher - 🎞 (Movie)
                                       'menu_.🏠 Main menu'  # Main Menu - 🏠 (House)
                                       ]}

    for i in text.get(language):
        row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f'{i.split(".")[0]}'))
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []
    if row:
        inline_keyboard.append(row)

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return inline_keyboard


async def delete_result_en(language: str, id, message_id):
    inline_button = []
    text = {'uz': [f'delete_result_{id}_{message_id}.🗑️ O‘chirish'],  # Uzbek: "O‘chirish" (Delete)
            'ru': [f'delete_result_{id}_{message_id}.🗑️ Удалить'],  # Russian: "Удалить" (Delete)
            'en': [f'delete_result_{id}_{message_id}.🗑️ Delete']  # English: "Delete"
            }

    for i in text.get(language):
        inline_button.append([InlineKeyboardButton(text=f"{i.split('.')[1]}", callback_data=i.split('.')[0])])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def keyboard(language, data):
    inline_button = []
    row = []
    text2 = {'uz': [f'yes_delete_{data}.✅ Ha, o‘chir', f'return_result_{data}.❌ Yo‘q'],
             # Uzbek: "Ha, o‘chir" (Yes, delete) / "Yo‘q" (No)
             'ru': [f'yes_delete_{data}.✅ Да, удалить', f'return_result_{data}.❌ Нет'],
             # Russian: "Да, удалить" (Yes, delete) / "Нет" (No)
             'en': [f'yes_delete_{data}.✅ Yes, delete', f'return_result_{data}.❌ No']  # English: "Yes, delete" / "No"
             }
    for i in text2.get(language):
        row.append(InlineKeyboardButton(text=f"{i.split('.')[1]}", callback_data=f"{i.split('.')[0]}"))
    inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def settings_kb(language):
    inline_buttons = []
    row = []
    text = {'uz': ['lan2_.🔄 Tilni o‘zgartirish', 'fregister_.📝 To‘liq ro‘yxatdan o‘tish', 'menu_.🏠 Bosh menu'],
            'ru': ['lan2_.🔄 Изменить язык', 'fregister_.📝 Полная регистрация',
                   # Full Registration - 📝 (Writing or filling forms)
                   'menu_.🏠 Главное меню'  # Main menu - 🏠 (House)
                   ], 'en': ['lan2_.🔄 Change language',  # Change language - 🔄 (Rotate arrows indicating change)
                             'fregister_.📝 Full Registration',  # Full Registration - 📝 (Writing or filling forms)
                             'menu_.🏠 Main menu'  # Main menu - 🏠 (House)
                             ]}

    for i in text.get(language):
        row.append(InlineKeyboardButton(text=i.split('.')[1], callback_data=i.split('.')[0]))
        if len(row) == 2:
            inline_buttons.append(row)
            row = []
    if row:
        inline_buttons.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_keyboard


async def fregister_year(page):
    inline_keyboard = []
    row = []

    if int(page) == 1:
        for i in range(current_year - 11, current_year - 28, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'yfregister_year_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'ypfregister_year2_{3}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'ypfregister_year2_{2}')])
        inline_keyboard.append([InlineKeyboardButton(text='🔙 Orqaga', callback_data=f'fregister_')])

    elif int(page) == 2:
        for i in range(current_year - 28, current_year - 45, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'yfregister_year_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 2
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'ypfregister_year2_{1}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'ypfregister_year2_{3}')])
        inline_keyboard.append([InlineKeyboardButton(text='🔙 Orqaga', callback_data=f'yfregister_')])

    elif int(page) == 3:
        for i in range(current_year - 45, current_year - 62, -1):
            row.append(InlineKeyboardButton(text=f'{i}', callback_data=f'yfregister_year_{i}_'))
            if len(row) == 4:
                inline_keyboard.append(row)
                row = []
        if row:
            inline_keyboard.append(row)

        # Navigation buttons for page 3
        inline_keyboard.append([InlineKeyboardButton(text='⏪', callback_data=f'ypfregister_year2_{2}'),
                                InlineKeyboardButton(text='🏠 Bosh menu', callback_data='menu_'),
                                InlineKeyboardButton(text='⏩', callback_data=f'ypfregister_year2_{1}')])
        inline_keyboard.append([InlineKeyboardButton(text='🔙 Orqaga', callback_data=f'fregister_')])

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return inline_keyboard


async def fmonth(language):
    # Month dictionary with custom names for each language
    match language:
        case 'uz':
            months = {12: '12🎄 Dekabr',  # December
                      1: '01❄️ Yanvar',  # January
                      2: '02🌸 Fevral',  # February
                      3: '03🌷 Mart',  # March
                      4: '04🌱 Aprel',  # April
                      5: '05🌞 May',  # May
                      6: '06☀️ Iyun',  # June
                      7: '07🌞 Iyun',  # July
                      8: '08🌅 Avgust',  # August
                      9: '09🎒 Sentabr',  # September
                      10: '10🍂 Oktabr',  # October
                      11: '11🌧️ Noyabr'  # November
                      }
        case 'ru':
            months = {12: '12🎄 Декабрь',  # December
                      1: '01❄️ Январь',  # January
                      2: '02🌸 Февраль',  # February
                      3: '03🌷 Март',  # March
                      4: '04🌱 Апрель',  # April
                      5: '05🌞 Май',  # May
                      6: '06☀️ Июнь',  # June
                      7: '07🌞 Июль',  # July
                      8: '08🌅 Август',  # August
                      9: '09🎒 Сентябрь',  # September
                      10: '10🍂 Октябрь',  # October
                      11: '11🌧️ Ноябрь'  # November
                      }
        case 'en':
            months = {12: '12🎄 December',  # December
                      1: '01❄️ January',  # January
                      2: '02🌸 February',  # February
                      3: '03🌷 March',  # March
                      4: '04🌱 April',  # April
                      5: '05🌞 May',  # May
                      6: '06☀️ June',  # June
                      7: '07🌞 July',  # July
                      8: '08🌅 August',  # August
                      9: '09🎒 September',  # September
                      10: '10🍂 October',  # October
                      11: '11🌧️ November'  # November
                      }
        case _:
            # Default to Uzbek if language is unknown
            months = {12: '12🎄 Dekabr',  # December
                      1: '01❄️ Yanvar',  # January
                      2: '02🌸 Fevral',  # February
                      3: '03🌷 Mart',  # March
                      4: '04🌱 Aprel',  # April
                      5: '05🌞 May',  # May
                      6: '06☀️ Iyun',  # June
                      7: '07🌞 Iyun',  # July
                      8: '08🌅 Avgust',  # August
                      9: '09🎒 Sentabr',  # September
                      10: '10🍂 Oktabr',  # October
                      11: '11🌧️ Noyabr'  # November
                      }

    inline_buttons = []
    row = []

    # Button creation for each month
    for num, label in months.items():
        row.append(InlineKeyboardButton(text=label[2:],
                                        callback_data=f'fmonth_{label[:2]}_{label}'))  # Removing the number part
        if len(row) == 3:  # Limit to 3 buttons per row
            inline_buttons.append(row)
            row = []
    if row:  # Add any remaining buttons to the last row
        inline_buttons.append(row)

    # Language-specific footer buttons
    if language == 'en':
        row.append(InlineKeyboardButton(text="🏠 Home", callback_data='menu_'))
        row.append(InlineKeyboardButton(text="🔙 Back", callback_data=f'fullname_f'))
    elif language == 'ru':
        row.append(InlineKeyboardButton(text="🏠 Home", callback_data='menu'))
        row.append(InlineKeyboardButton(text="🔙 Back", callback_data=f'fullname_f'))
    elif language == 'uz':
        row.append(InlineKeyboardButton(text="🏠 Bosh menu", callback_data='menu_'))
        row.append(InlineKeyboardButton(text="🔙 Ortga", callback_data=f'fullname_f'))

    if row:  # Add any remaining footer buttons
        inline_buttons.append(row)

    # Create an inline keyboard with the buttons
    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_kb


async def fdays(month, year):
    month_days = {'01': 31, '02': 29 if (int(year) % 4 == 0) else 28,  # Leap year logic
                  '03': 31, '04': 30, '05': 31, '06': 30, '07': 31, '08': 31, '09': 30, '10': 31, '11': 30, '12': 31}
    days_in_month = month_days[month]  # Get the number of days for the selected month
    inline_buttons = []
    row = []

    for num in range(1, days_in_month + 1):
        row.append(InlineKeyboardButton(text=f'{num}', callback_data=f'fday_{num}_'))
        if len(row) == 5:  # Limit to 3 buttons per row
            inline_buttons.append(row)
            row = []  # Reset the row for the next set of buttons
    if row:  # Add any remaining buttons to the last row
        inline_buttons.append(row)
    inline_buttons.append([InlineKeyboardButton(text='🏠 Bosh sahifa', callback_data='menu_'),
                           InlineKeyboardButton(text='🔙 Orqaga', callback_data=f'yfregister_year_')])
    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return inline_kb


async def fgender(language):
    menu = {'uz': ['fgender_man_.🤵 Erkak kishi', 'fgender_women_.👩 Ayol kishi', 'fday_.🔙 Orqaga', 'menu_.🏠 Bosh menu'],
            'ru': ['fgender_man_.🤵 Мужчина', 'fgender_women_.👩 Женщина', 'fday_.🔙 Назад', 'menu_.🏠 Главное меню'],
            'en': ['fgender_man_.🤵 Man', 'fgender_women_.👩 Woman', 'fday_.🔙 Back', 'menu_.🏠 Main menu']}

    inline_button = []
    row = []

    for i in menu.get(language):
        row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f'{i}'))
        if len(row) == 2:
            inline_button.append(row)
            row = []

    if row:
        inline_button.append(row)

    # Create InlineKeyboardMarkup
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def fconifim(language):
    text = {'uz': ['fconifim_.✅ Hammasi tog\'ri', 'fregister_.♻️ Boshqatan', 'menu_.🏠 Bosh menu'],
            'ru': ['fconifim_.✅ Все верно', 'fregister_.♻️ Еще раз', 'menu_.🏠 Главное меню'],
            'en': ['fconifim_.✅ Everything is correct', 'fregister_.♻️ Try again', 'menu_.🏠 Main menu']}

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


async def complain_level_manager(language, id):
    inline_button = []
    row = []
    text = {
        'uz': [f'mlevel_serious_{id}.😠 Jiddiy', f'mlevel_normal_{id}.🙂 Oddatiy', f'mlevel_delete_{id}.❌ Shikoyat emas'],
        'ru': [f'mlevel_serious_{id}.😠 Серьёзно', f'mlevel_normal_{id}.🙂 Обычный', f'mlevel_delete_{id}.❌ Не жалоба'],
        'en': [f'mlevel_serious_{id}.😠 Serious', f'mlevel_normal_{id}.🙂 Normal',
               f'mlevel_delete_{id}.❌ Not a complaint'], }
    for i in text.get(language):
        row.append(InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f"{i.split('.')[0]}"))
        if len(row) == 3:
            inline_button.append(row)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)
    return inline_keyboard


async def user_takes_call_or_not(language, data):
    text = {'uz': [f'ywarned_yes_{data}.✅ Telfon qilishdi', f'ywarned_no_{data}.❌ Hech kim qong\'iroq qilmadi'],
            'ru': [f'ywarned_yes_{data}.✅ Позвонили', f'ywarned_no_{data}.❌ Никто не звонил'],
            'en': [f'ywarned_yes_{data}.✅ They called', f'ywarned_no_{data}.❌ No one called']}

    inline_button = []
    for i in text.get(language):
        inline_button.append([InlineKeyboardButton(text=f'{i.split(".")[1]}', callback_data=f'{i}'), ])
    return InlineKeyboardMarkup(inline_keyboard=inline_button)


# ---------------------------------------functions ---------------------------------------------------------------------#


async def delete_previous_messages(message, id):
    for i in range(1, 50):
        try:
            await bot.delete_message(chat_id=id, message_id=message - i)
        except TelegramBadRequest:
            pass


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


async def download_image2(bot: Bot, message: Message, name: str, state: str) -> str | None:
    try:
        # Ensure the save folder exists
        save_folder = f"Hire/{state}"
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


async def image_send_edit_to_delete(id):
    async with async_session() as session:
        stmt = select(Results_English).where(Results_English.id == id)
        result = await session.execute(stmt)
        user_language = result.scalar()
        return user_language


async def send_certificate(bot: Bot, chat_id: int, callback_query, langauge):
    async with async_session() as session:
        try:
            result = await session.execute(select(Results_English).order_by(Results_English.id.desc()))
            certificates = result.scalars().all()
            if not certificates:
                await bot.send_message(chat_id, "No certificate found.")
                return
            for certificate in certificates:
                if certificate.is_deleted != '1':
                    text = (f"📋 Certificate Information:\n\n"
                            f"👤 Full Name: {certificate.fullname}\n"
                            f"🏅 Band Score: {certificate.Overall_Band}\n\n"
                            f"🗣 Speaking: {certificate.speaking}\n"
                            f"✍️ Writing: {certificate.writing}\n"
                            f"👂 Listening: {certificate.listening}\n"
                            f"📖 Reading: {certificate.reading}\n\n"
                            f"✨Smart English\n<a href='http://instagram.com/smart.english.official'>Instagram</a>|<a href='https://t.me/SMARTENGLISH2016'>Telegram</a>|<a href='https://www.youtube.com/channel/UCu8wC4sBtsVK6befrNuN7bw'>YouTube</a>|<a href='https://t.me/Smart_Food_official'>Smart Food</a>|<a href='https://t.me/xusanboyman200'>Programmer</a>")
                    image_path = certificate.image

                    if os.path.exists(image_path):
                        photo = FSInputFile(image_path)
                        user_role = await get_user_role(callback_query.from_user.id)
                        if user_role != 'User':
                            delete_button = await delete_result_en(langauge, certificate.id,
                                                                   callback_query.message.message_id)
                            await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode='HTML',
                                                 reply_markup=delete_button)
                        else:
                            await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode='HTML')

                    else:
                        await bot.send_message(chat_id, f"Certificate image not found for {certificate.fullname}.",
                                               parse_mode='HTML')

            language = await get_user_language(tg_id=callback_query.from_user.id)
            language_map = {'ru': 'ru', 'en': 'en', 'uz': 'Bosh menu'}
            user_id = callback_query.from_user.id
            await bot.send_message(text=language_map.get(language, 'en'), chat_id=user_id,
                                   reply_markup=await home(language, callback_query.message.message_id))

        except Exception as e:

            error_message = traceback.format_exc()  # Get the full traceback
            await bot.send_message(chat_id, f"An error occurred:\n{error_message}")


# -----------------------------------------Messages---------------------------------------------------------------------#
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    existing_user = await get_user_by_tg_id(user_id)
    if not existing_user:
        await message.answer('🇺🇿: Assalomu alaykum botimizga xush kelibsiz\n🇷🇺: Privet \n🇺🇸: Hello Mr or Ms',
                             reply_markup=await languages())
        await message.delete()
        await bot.delete_message(message.chat.id, message.message_id - 1)
        return
    else:
        language = await get_user_language(user_id)
        await bot.send_message(chat_id=user_id, text={"ru": "ru", "en": "en", "uz": "Bosh menu"}.get(language, "en"),
                               reply_markup=await home(language, message.from_user.id))
        await state.clear()
    try:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id - 1)
        await delete_previous_messages(message.message_id, message.from_user.id)
    except TelegramBadRequest as e:
        pass


@dp.callback_query(F.data.startswith('menu_'))
async def menu(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    user_id = callback_query.from_user.id
    text = {'ru': "Главное меню",  # Text in Russian
            'en': "Main Menu",  # Text in English
            'uz': "Bosh menu"  # Text in Uzbek
            }
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=user_id, text=text.get(language),
                                reply_markup=await home(language, callback_query.from_user.id))
    try:
        await state.clear()
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 1)
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 2)
    except TelegramBadRequest as e:
        pass


@dp.callback_query(F.data.startswith('lan_'))
async def language(callback_query: CallbackQuery):
    if callback_query.from_user.username:
        await add_user(callback_query.from_user.id, callback_query.from_user.username,
                       callback_query.from_user.full_name)
    else:
        await add_user(callback_query.from_user.id, 'no username', callback_query.from_user.full_name)
    language = callback_query.data.split('_')[1]
    await change_user_language(tg_id=callback_query.from_user.id, language=language)
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text={"ru": "ru", "en": "en", "uz": "Bosh menu"}.get(language),
                                reply_markup=await home(language, callback_query.from_user.id))
    try:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 1)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest as e:
        pass
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
                                        chat_id=callback_query.from_user.id,
                                        text='Smart English o\'vmarkazidagi kurslardan birini tanlang',
                                        reply_markup=await tuition(language))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        chat_id=callback_query.from_user.id,
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
        if i in str([1, 2, 3, 4, 5, 6, 7, 8, 9, 0]) or len(message.text) < 7:
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
    if message.text:
        if message.text[:1] == '🔙':
            match language:
                case 'uz':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='🖋️ Toliq ismingizni yozing\nMisol uchun: Abdulkhaev Xusanboy',
                                           reply_markup=ReplyKeyboardRemove())
                case 'ru':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='🖋️ Toliq ismingizni yozing\nMisol uchun: Abdulkhaev Xusanboy',
                                           reply_markup=ReplyKeyboardRemove())
                case 'en':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='🖋️ Toliq ismingizni yozing\nMisol uchun: Abdulkhaev Xusanboy',
                                           reply_markup=ReplyKeyboardRemove())
            await state.set_state(Register.fullname)
            await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)
            await bot.delete_message(message_id=message.message_id - 1, chat_id=message.from_user.id)
            await delete_previous_messages(message.message_id, message.from_user.id)
            return
        if not message.text[1:].isdigit() or 9 <= len(str(message.text)) >= 13:
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
        if message.text[0] == '+':
            await state.update_data(number=message.text)
        else:
            await state.update_data(number=f'+{message.text}')

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


@dp.callback_query(F.data.startswith('Register_number_'))
async def number(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'uz':
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text='📞 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing',
                                   reply_markup=await share_phone_number(language))
        case 'ru':
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text='📞 Введите свой номер телефона или нажмите на кнопку ниже',
                                   reply_markup=await share_phone_number(language))
        case 'en':
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text='📞 Please enter your phone number or click the button below',
                                   reply_markup=await share_phone_number(language))
    await state.set_state(Register.number)
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


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
                                        chat_id=callback_query.from_user.id, reply_markup=await register_english(1))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='en',
                                        chat_id=callback_query.from_user.id, reply_markup=await register_english(1))
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text='Iltmos tugilgan yilingizni kiriting', chat_id=callback_query.from_user.id,
                                        reply_markup=await register_english(1))


@dp.callback_query(F.data.startswith('year_'))
async def sssss(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    if len(callback_query.data.split('_')) == 3:
        await state.update_data(year=callback_query.data.split('_')[1])
    data = await state.get_data()
    gender1 = data.get('gender')
    fake = data.get('fake_gender')
    gender = f'{gender1}_{fake}'
    match language:
        case 'uz':
            await bot.send_message(text='Tugilgan oyingizni tanlang', chat_id=callback_query.from_user.id,
                                   reply_markup=await month(language, gender))
        case 'ru':
            await bot.send_message(text='Tugilgan oyingizni tanlang', chat_id=callback_query.from_user.id,
                                   reply_markup=await month(language, gender))
        case 'en':
            await bot.send_message(text='Tugilgan oyingizni tanlang', chat_id=callback_query.from_user.id,
                                   reply_markup=await month(language, gender))
    await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('2year_'))
async def sssss(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    data = await state.get_data()
    gender1 = data.get('gender')
    fake = data.get('fake_gender')
    data2 = callback_query.data.split('_')[1]
    match language:
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='ru',
                                        chat_id=callback_query.from_user.id, reply_markup=await register_english(data2))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='en',
                                        chat_id=callback_query.from_user.id, reply_markup=await register_english(data2))
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text='Iltmos tugilgan yilingizni kiriting', chat_id=callback_query.from_user.id,
                                        reply_markup=await register_english(data2))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('month_'))
async def month_callback(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    month = callback_query.data.split('_')[1]
    month_name = callback_query.data.split('_')[2][2:]
    await state.update_data(fake_month=month_name)
    await state.update_data(month=month)
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
    try:
        await bot.delete_message(message_id=callback_query.message.message_id - 1, chat_id=callback_query.from_user.id)
        await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)
    except TelegramBadRequest:
        pass


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
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await tuition_en(language, year))
            case 'en':
                await bot.edit_message_text(message_id=callback_query.message.message_id, text='en',
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await tuition_en(language, year))
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
                                            reply_markup=await time_en(language, day, 'other'))
            case 'ru':
                await bot.edit_message_text(message_id=callback_query.message.message_id,
                                            text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await time_en(language, day, 'other'))
            case 'en':
                await bot.edit_message_text(message_id=callback_query.message.message_id,
                                            text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                            chat_id=callback_query.from_user.id,
                                            reply_markup=await time_en(language, day, 'other'))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('level_'))
async def level(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')[1].replace('.', '')
    await state.update_data(level=data)
    days = await state.get_data()
    course = days.get('course')
    day = days.get('day')
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                        chat_id=callback_query.from_user.id,
                                        reply_markup=await time_en(language, day, course))
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                        chat_id=callback_query.from_user.id,
                                        reply_markup=await time_en(language, day, course))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id,
                                        text=f'{data.capitalize() if data != "ielt" else data.upper() + "S"} oyi uchun berilgan ozingizga mos vaqtni tanlang',
                                        chat_id=callback_query.from_user.id,
                                        reply_markup=await time_en(language, day, course))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('more.'))
async def level(callback_query: CallbackQuery, state: FSMContext):
    days = await state.get_data()
    day = days.get('month')
    month_name = days.get('fake_month')
    language = await get_user_language(callback_query.from_user.id)
    match language:
        case 'ru':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='Kurs darajasini tanlang',
                                        chat_id=callback_query.from_user.id,
                                        reply_markup=await level_more(language, day, month_name))
        case 'en':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='Kurs darajasini tanlang',
                                        chat_id=callback_query.from_user.id,
                                        reply_markup=await level_more(language, day, month_name))
        case 'uz':
            await bot.edit_message_text(message_id=callback_query.message.message_id, text='Kurs darajasini tanlang',
                                        chat_id=callback_query.from_user.id,
                                        reply_markup=await level_more(language, day, month_name))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)


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
    gender2 = data.get('gender')
    fullname = data.get('fullname')
    level = data.get('level')
    day = data.get('day')
    year = data.get('year')
    time = data.get('time')
    month = data.get('month')
    born_year = f'{int(day):02}/{month}/{year}'
    if callback_query.from_user.username:
        await register(tg_id=callback_query.from_user.username, name=fullname, phone_number=number, course=course,
                       level=level,  # Pass the correct value here
                       course_time=time1,  # Pass the correct value here
                       user_gender=gender, born_year=born_year, tg_id_real=callback_query.from_user.id)
        for call_centres1 in await call_centre():
            await bot.send_message(chat_id=call_centres1,
                                   text=(f'#student\n❗️❗️❗️❗️ Telefon qilish kerak Smart English ❗️❗️❗️❗️❗️\n\n'
                                         f'To\'liq ismi: {fullname}\n'
                                         f'Telegram foydalanuvchi nomi: @{callback_query.from_user.username}\n'
                                         f'Telefon raqami: {number}\n'
                                         f'Jinsi: {gender}\n'
                                         f'Tug\'ilgan yili: {year} yil\n'
                                         f'Tug\'ilgan oyi: {month} oy\n'
                                         f'Kurs darajasi: {level if level else "Kurs mavjud emas"}\n'
                                         f'Tug\'ilgan kuni: {day} kun\n'
                                         f'Kurs nomi: {course}\n'
                                         f'Kurs vaqti: {time}'),
                                   reply_markup=await call(number, callback_query.from_user.id, language))
    else:
        # Register the user with the correct data
        await register(tg_id=callback_query.from_user.username, name=fullname, phone_number=number, course=course,
                       level=level,  # Pass the correct value here
                       course_time=time1,  # Pass the correct value here
                       user_gender=gender2, born_year=born_year, tg_id_real=callback_query.from_user.id)
        for call_centres in await call_centre():
            await bot.send_message(chat_id=await call_centres(),
                                   text=(f'❗️❗️❗️❗️ Telefon qilish kerak Smart English ❗️❗️❗️❗️❗️\n\n'
                                         f'To\'liq ismi: {fullname}\n'
                                         f'Telefon raqami: {number}\n'
                                         f'Jinsi: {gender}\n'
                                         f'Tug\'ilgan yili: {year} yil\n'
                                         f'Tug\'ilgan oyi: {month} oy\n'
                                         f'Kurs darajasi: {level if level else "Kurs mavjud emas"}\n'
                                         f'Tug\'ilgan kuni: {day} kun\n'
                                         f'Kurs nomi: {course}\n'
                                         f'Kurs vaqti: {time}'),
                                   reply_markup=await call(number, callback_query.from_user.id, language))
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


@dp.callback_query(F.data.startswith('clled_'))
async def call_(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '📞 Siz telefon qilganingiz uchun rahmat\n📝 Qoʻngʻiroq uchun izoh qoldiring',
            'ru': '📞 Спасибо за ваш звонок\n📝 Оставьте комментарий к звонку',
            'en': '📞 Thank you for your call\n📝 Leave a comment about the call', }

    await callback_query.message.answer(text=text.get(language))
    await state.update_data(tg_id_user=callback_query.data.split('_')[1])
    print(callback_query.data)
    await state.set_state(Call.comment)


@dp.message(Call.comment)
async def call_comment(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if not message.text:
        text = {'uz': '✏️ Faqat text yozing', 'ru': '✏️ Пишите только текст', 'en': '✏️ Write text only', }
        await state.set_state(Call.comment)
        await message.answer(text=text.get(language))
        return
    else:
        data = await state.get_data()
        tg_id_user = data.get('tg_id_user')
        text = {'uz': f'❓ Sizning commentingiz tasdiqlaysizmi?\n\n📝 {message.text}',
                'ru': f'❓ Вы подтверждаете свой комментарий?\n\n📝 {message.text}',
                'en': f'❓ Do you confirm your comment?\n\n📝 {message.text}', }
        await state.update_data(comment=message.text)
        text2 = {'uz': '📞 Sizga Smart English tomonidan qong\'iroq qilindi, bundan habardormisiz?',
                 'ru': '📞 Вам позвонили из Smart English, вы в курсе?',
                 'en': '📞 You received a call from Smart English, are you aware?'}
        language2 = await get_user_language(tg_id_user)
        await bot.send_message(chat_id=tg_id_user, text=text2.get(language2),
                               reply_markup=await user_takes_call_or_not(language2, tg_id_user))
        await message.answer(text=text.get(language), reply_markup=await call_confirm_yes(language))
        await delete_previous_messages(message.message_id, id=message.from_user.id)


@dp.callback_query(F.data.startswith('ycall_'))
async def call4_confirm_yes(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get('tg_id_user')
    comment = data.get('comment')
    print(callback_query.data)
    language = await get_user_language(callback_query.from_user.id)
    if callback_query.data.split('_')[1] == 'yes':
        await set_register_state_yes(tg_id, 'yes', comment)
        await callback_query.answer(text='Commited sucsefully')
        await callback_query.message.delete()
        await delete_previous_messages(callback_query.message.message_id, id=callback_query.from_user.id)
        await state.clear()
        return
    else:
        text = {'uz': '📝 Qoʻngʻiroq uchun izoh qoldiring', 'ru': '📝 Оставьте комментарий к звонку',
                'en': '📝 Leave a comment for the call', }
        await callback_query.message.answer(text=text.get(language))
        await state.set_state(Call.comment)
        await delete_previous_messages(callback_query.message.message_id, id=callback_query.from_user.id)
        return


@dp.callback_query(F.data.startswith('broken_'))
async def broken2_(calllbac_Query: CallbackQuery):
    lanugage = await get_user_language(calllbac_Query.from_user.id)
    await delete_call(calllbac_Query.data.split('_')[1])
    text = {'uz': '✅ Bu telefon raqam muvaffaqiyatli o\'chirib yuborildi', 'ru': '✅ Этот номер телефона успешно удалён',
            'en': '✅ This phone number has been successfully deleted'}
    await calllbac_Query.answer(text=text.get(lanugage))
    await delete_previous_messages(calllbac_Query.message.message_id, calllbac_Query.from_user.id)
    return


@dp.callback_query(F.data.startswith('ywarned_'))
async def ywarned3_(callback_query: CallbackQuery):
    global number
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': 'Rahmat 🙂',  # Uzbek
            'ru': 'Спасибо 😊',  # Russian
            'en': 'Thank you 😄'  # English
            }
    if callback_query.data.split('_')[1] == 'yes':
        await callback_query.answer(text=text.get(language), show_alert=True)
        await callback_query.message.delete()
    else:
        call_center_ids = await call_centre()
        for call_center_id in call_center_ids:
            for i in await all_users_to_register(callback_query.from_user.id):
                number = i.number
                text = ("Siz bu studentga telefon qilishni unutgansiz yoki bu ishni atayin qilgansiz. "
                        "Bu haqida javob berasiz.\n\n"
                        "❗️❗️❗️❗️ Telefon qilish kerak - Smart English ❗️❗️❗️❗️❗️\n\n"
                        f"To'liq ismi: {i.user_name}\n"
                        f"Telegram foydalanuvchi nomi: @{i.telegram_information}\n"
                        f"Telefon raqami: {i.number}\n"
                        f"Jinsi: {i.gender}\n"
                        f"Tug'ilgan yili: {i.born_year} yil\n"
                        f"Kurs darajasi: {i.level}\n"
                        f"Kurs nomi: {i.course}\n"
                        f"Kurs vaqti: {i.time}")

            # Send the message to each call center
            await bot.send_message(chat_id=call_center_id, text=text,
                                   reply_markup=await call(number, callback_query.from_user.id, language))


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
    try:
        await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)
        await bot.delete_message(message_id=message.message_id - 1, chat_id=message.from_user.id)
        await delete_previous_messages(message.message_id, message.from_user.id)
    except TelegramBadRequest:
        pass


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
    await bot.send_message(chat_id=message.from_user.id, text=text,
                           reply_markup=await scores(language, 'speaking', 'add_result', f'{fullname}'))


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
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text, reply_markup=await scores(language, f'writing', 'fullname', f'{fullname}'))
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
    try:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id - 1)
        await delete_previous_messages(message.message_id, message.from_user.id)
    except TelegramBadRequest:
        pass


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
    try:
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest:
        pass


# ------------------------------------  Audio --------------------------------------------------------------------------#
@dp.callback_query(F.data.startswith('audio_'))
async def audiol(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '🎧 Sizga kerakli audio qaysi bo‘limdan? 📂', 'ru': '🎧 Какой раздел нужен для вашего аудио? 📂',
            'en': '🎧 Which section do you need the audio from? 📂'}
    current_text = text.get(language)
    current_markup = await audio_home(language)
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=current_text,
                                chat_id=callback_query.from_user.id, reply_markup=current_markup)
    try:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 1)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data.startswith('/audio_home_'))
async def audio_monthl(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')[2]
    await state.update_data(audio_home=data)
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': f'({data.upper()}) 📊 Darajangizni tanlang: 🔽', 'ru': f'({data.upper()}) 📊 Выберите ваш уровень: 🔽',
            'en': f'({data.upper()}) 📊 Please select your level: 🔽'}

    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(language), reply_markup=await month_audio())
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    try:
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data.startswith('?audio_'))
async def audio_level2(callback_query: CallbackQuery, state: FSMContext):
    audio_level = callback_query.data.split('_')[1]
    await state.update_data(audio_level=audio_level)
    data3 = await state.get_data()
    data = data3.get('audio_home')
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': f'{data.upper()} audioni olish uchun oyingizni tanlang 🎧',
            'ru': f'{data.upper()} для получения аудио выберите вашу игру 🎧',
            'en': f'{data.upper()} to get the audio, select your game 🎧'}
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(language), reply_markup=await audio_month(language, data))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('.audio_month_'))
async def audio_month_level(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    month = callback_query.data.split('_')[2]
    data = await state.get_data()
    home2 = data.get('audio_home')
    level = data.get('audio_level')
    folder_path = f'./audio/{home2}/{level}/{month}'
    print(folder_path)
    mp3_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
    text = {'uz': 'Bosh sahifa', 'ru': 'Bosh sahifa', 'en': 'Bosh sahifa', }
    for file_path in mp3_files:
        audios = FSInputFile(file_path)
        await bot.send_chat_action(chat_id=callback_query.from_user.id, action='upload_audio')
        await bot.send_audio(chat_id=callback_query.from_user.id, audio=audios)
    await bot.send_message(chat_id=callback_query.from_user.id, text=text.get(str(language)),
                           reply_markup=await home(language, callback_query.from_user.id))
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
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 1)
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 2)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest as e:
        pass


@dp.callback_query(F.data.startswith("result_"))
async def result(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[1]
    if data == 'English':
        await send_certificate(bot, callback_query.from_user.id, callback_query, language)
    try:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id - 1)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest as e:
        pass


@dp.callback_query(F.data.startswith('delete_result_'))
async def delete_resultantly(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[2]
    text = {'uz': '⚠️ Siz bu maʼlumotni o‘chirishni xohlaysizmi? 🗑️',
            'ru': '⚠️ Вы действительно хотите удалить эту информацию? 🗑️',
            'en': '⚠️ Are you sure you want to delete this information? 🗑️'}

    try:
        await bot.edit_message_caption(message_id=callback_query.message.message_id, caption=text[language],
                                       chat_id=callback_query.from_user.id, reply_markup=await keyboard(language, data))
    except TelegramBadRequest as e:
        print(f"Failed to edit message: {e}")


@dp.callback_query(F.data.startswith('return_result_'))
async def return_result(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    certificate = await image_send_edit_to_delete(callback_query.data.split('_')[2])
    text = (f"📋 Certificate Information:\n\n"
            f"👤 Full Name: {certificate.fullname}\n"
            f"🏅 Band Score: {certificate.Overall_Band}\n\n"
            f"🗣 Speaking: {certificate.speaking}\n"
            f"✍️ Writing: {certificate.writing}\n"
            f"👂 Listening: {certificate.listening}\n"
            f"📖 Reading: {certificate.reading}\n\n"
            f"✨Smart English\n<a href='http://instagram.com/smart.english.official'>Instagram</a>|<a href='https://t.me/SMARTENGLISH2016'>Telegram</a>|<a href='https://www.youtube.com/channel/UCu8wC4sBtsVK6befrNuN7bw'>YouTube</a>|<a href='https://t.me/Smart_Food_official'>Smart Food</a>|<a href='https://t.me/xusanboyman200'>Programmer</a>")

    await bot.edit_message_caption(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                   caption=text, reply_markup=await delete_result_en(language, certificate.id,
                                                                                     callback_query.message.message_id),
                                   parse_mode='HTML')


@dp.callback_query(F.data.startswith('yes_delete_'))
async def yes_delete3(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    await delete_results_en(callback_query.data.split('_')[2])
    text = {'uz': 'Natija muaffaqiyatli ochirildi :tick', 'ru': 'Natija muaffaqiyatli ochirildi :tick',
            'en': 'Natija muaffaqiyatli ochirildi :tick', }
    try:
        await callback_query.answer(text=text.get(language))
        await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)
    except TelegramBadRequest as e:
        pass


# ------------------------------------Hire worker-----------------------------------------------------------------------#
@dp.callback_query(F.data.startswith('hire_'))
async def hire2(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': 'Siz Smart English dagi qaysi soha boyicha ishlashni xoxlaysiz',
            'ru': 'Siz Smart English dagi qaysi soha boyicha ishlashni xoxlaysiz',
            'en': 'Siz Smart English dagi qaysi soha boyicha ishlashni xoxlaysiz', }
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                chat_id=callback_query.from_user.id, reply_markup=await hire(language))
    try:
        await bot.delete_message(message_id=callback_query.message.message_id - 1, chat_id=callback_query.from_user.id)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest:
        pass


@dp.message(Hire.name)
async def hire_name(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    message_text = message.text.strip()
    name_parts = message_text.split()
    if any(part.isdigit() for part in name_parts) or len(name_parts) < 2:
        text = {'uz': 'FIO ingizni kiriting:\nMisol uchun: Abdulkhaev Xusabvoy Solijonivich',
                'ru': 'FIO ingizni kiriting\nMisol uchun: Abdulkhaev Xusabvoy Solijonivich',
                'en': 'FIO ingizni kiriting\nMisol uchun: Abdulkhaev Xusabvoy Solijonivich'}
        await message.answer(text=text.get(language), reply_markup=ReplyKeyboardRemove())
        await delete_previous_messages(message.message_id, message.from_user.id)
        return

    # Capitalize each part and store the name
    name_parts = [part.capitalize() for part in name_parts]  # Capitalize each part
    full_name = " ".join(name_parts)  # Join the parts back into a full name

    # Store the name in the state
    await state.update_data(name=full_name)

    # Proceed to next step
    text = {'uz': 'Necha yoshdasiz nechada 👇 tugmalardan tanlang',
            'ru': 'Necha yoshdasiz nechada 👇 tugmalardan tanlang',
            'en': 'Necha yoshdasiz nechada 👇 tugmalardan tanlang'}
    await bot.send_message(chat_id=message.from_user.id, text=text.get(language), reply_markup=await yhire(1))

    # Set state for next input
    await state.set_state(Hire.start)

    # Delete previous messages
    try:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id - 1)
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await delete_previous_messages(message.message_id, message.from_user.id)
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data.startswith('type_'))
async def types(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    print(callback_query.data)
    if len(callback_query.data.split('_')) == 3:
        await state.update_data(stater=callback_query.data.split('_')[2])
        await state.update_data(state_fake=callback_query.data.split('.')[1])
    text = {'uz': 'FIO ingizni kiriting:\nMisol uchun: Abdulkhaev Xusabvoy Solijonivich',
            'ru': 'FIO ingizni kiriting\nMisol uchun: Abdulkhaev Xusabvoy Solijonivich',
            'en': 'FIO ingizni kiriting\nMisol uchun: Abdulkhaev Xusabvoy Solijonivich:', }
    await bot.edit_message_text(text=text.get(language), chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)
    await state.set_state(Hire.name)
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('hyear_'))
async def hyear_get(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    if len(callback_query.data.split('_')) == 3:
        await state.update_data(year=callback_query.data.split('_')[1])
    text = {'uz': 'Sizda ish staji bormi', 'ru': 'Sizda ish staji bormi', 'en': 'Sizda ish staji bormi', }
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                chat_id=callback_query.from_user.id,
                                reply_markup=await hexperience(language, 'experience'))


@dp.callback_query(F.data.startswith('hyear2_'))
async def usual(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[1]
    text = {'uz': 'Necha yoshdasiz 👇 tugmalardan tanlang', 'ru': 'Necha yoshdasiz  👇 tugmalardan tanlang',
            'en': 'Necha yoshdasiz  👇 tugmalardan tanlang', }
    await bot.edit_message_text(text=text.get(language), chat_id=callback_query.from_user.id,
                                reply_markup=await yhire(int(data)), message_id=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('hexperience_'))
async def hexperiensces(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    if len(callback_query.data.split('_')) == 3:
        await state.update_data(experience=callback_query.data.split('_')[1])
    text = {'uz': 'Sizning Certificatingiz bormi?', 'ru': 'Sizning Certificatingiz bormi?',
            'en': 'Sizning Certificatingiz bormi?', }
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                chat_id=callback_query.from_user.id,
                                reply_markup=await hexperience(language, 'is_certificate'))


@dp.callback_query(F.data.startswith('is/certificate_'))
async def is_certificate2(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    if len(callback_query.data.split('_')) == 3:
        await state.update_data(is_certificate=callback_query.data.split('_')[1])
    if callback_query.data.split('_')[1] == 'yes':
        text = {'uz': '🖼 Certifiact rasmini tashlang:', 'ru': '🖼 Certifiact rasmini tashlang:',
                'en': '🖼 Certifiact rasmini tashlang:', }
        await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                    chat_id=callback_query.from_user.id)
        await state.set_state(Hire.image_certificate)
    if callback_query.data.split('_')[1] == 'no':
        data = await state.get_data()
        name = data.get('name')
        text2 = {'uz': (f"👤 Ism sharifingiz: {name}\n🗓️ Tug'ilgan yilingiz: {data.get('year')}\n"
                        f"🗂️ Tanlagan kasbingiz: {data.get('state_fake')}\n🏅 Tajribangiz: {'Bor' if data.get('experience') == 'Yes' else 'Yo\'q'}"),
                 'ru': (f"👤 Ваше имя: {name}\n🗓️ Год вашего рождения: {data.get('year')}\n"
                        f"🗂️ Ваша выбранная профессия: {data.get('state_fake')}\n🏅 Ваш опыт: {'Bor' if data.get('experience') == 'Yes' else 'Yo\'q'}"),
                 'en': (f"👤 Your full name: {name}\n🗓️ Year of birth: {data.get('year')}\n"
                        f"🗂️ Chosen profession: {data.get('state_fake')}\n🏅 Experience: {'Bor' if data.get('experience') == 'Yes' else 'Yo\'q'}")}
        await bot.edit_message_text(message_id=callback_query.message.message_id, text=text2.get(language),
                                    chat_id=callback_query.from_user.id, reply_markup=await conifim_hire(language))


@dp.message(Hire.image_certificate)
async def hire_images3(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)

    # Check if a photo exists in the message
    if not message.photo:
        await message.answer("❌ Certifikat rasmini yuboring.")
        return

    # Get the user's data from state
    data = await state.get_data()
    stater = data.get('stater')  # Position the user is applying for
    name = data.get('name')  # User's full name

    # Ensure that all required data is present
    if not name or not stater:
        await message.answer("❌ Malumotlar to'liq emas. Qaytadan urining.")
        return

    # Create a safe file name for saving the certificate image
    inf = f"Hire/{stater}/{name.replace(' ', '_')}_certificate.jpg"

    # Update the state with the file path
    await state.update_data(image_certificate=inf)

    # Try to download the photo and handle potential errors
    try:
        # Download the image from Telegram (this function must be implemented)
        download_path = await download_image2(bot, message, name, stater)
        if not download_path:
            await message.answer("❌ Failed to download the image.")
            return
    except Exception as e:
        await message.answer(f"❌ An error occurred while downloading the image: {e}")
        return

    # Prepare the summary text to send to the user
    text = {'uz': (f"👤 Ism sharifingiz: {name}\n🗓️ Tug'ilgan yilingiz: {data.get('year')}\n"
                   f"🗂️ Tanlagan kasbingiz: {data.get('state_fake')}\n🏅 Tajribangiz: {'Bor' if data.get('experience') == 'Yes' else 'Yo\'q'}"),
            'ru': (f"👤 Ваше имя: {name}\n🗓️ Год вашего рождения: {data.get('year')}\n"
                   f"🗂️ Ваша выбранная профессия: {data.get('state_fake')}\n🏅 Ваш опыт: {'Bor' if data.get('experience') == 'Yes' else 'Yo\'q'}"),
            'en': (f"👤 Your full name: {name}\n🗓️ Year of birth: {data.get('year')}\n"
                   f"🗂️ Chosen profession: {data.get('state_fake')}\n🏅 Experience: {'Bor' if data.get('experience') == 'Yes' else 'Yo\'q'}")}

    # Send the photo and user details to the user
    try:
        await bot.send_photo(chat_id=message.from_user.id, caption=text.get(language), photo=message.photo[-1].file_id,
                             reply_markup=await conifim_hire(language))
        try:
            await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)
            await bot.delete_message(message_id=message.message_id - 1, chat_id=message.from_user.id)
            await delete_previous_messages(message.message_id, message.from_user.id)
        except TelegramBadRequest:
            pass
    except Exception as e:
        await message.answer(f"❌ An error occurred while sending the photo: {e}")
        return

    # Optionally clear state after processing is done  # await state.finish()  # If you want to end the state machine here


@dp.callback_query(F.data.startswith('cconifim_'))
async def confirm3(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': "📲 Agar siz bizga kerak bo'lsangiz, biz sizga 🤖 bot orqali aloqaga chiqamiz.",
            'ru': "📲 Если вы нам нужны, мы свяжемся с вами через 🤖 бота.",
            'en': "📲 If you need us, we will contact you via 🤖 the bot.", }
    text2 = {'uz': '🏠 Bosh menu', 'ru': '🏠 Bosh menu', 'en': '🏠 Bosh menu', }
    await bot.send_message(chat_id=callback_query.message.chat.id, text=text.get(language),
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                               [InlineKeyboardButton(text=text2.get(language), callback_data='menu_')]]))
    try:
        await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)
        await bot.delete_message(message_id=callback_query.message.message_id - 1, chat_id=callback_query.from_user.id)
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)
    except TelegramBadRequest:
        pass


# ------------------------------------ Complain ------------------------------------------------------------------------#

@dp.callback_query(F.data.startswith('complain_'))
async def complain(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': "🛑 Kimdan shikoyatingiz bor? 🕵️‍♂️ Ma'lumotlaringiz sir saqalanadi.",
            'ru': "🛑 На кого у вас жалоба? 🕵️‍♂️ Ваши данные останутся конфиденциальными.",
            'en': "🛑 Who are you complaining about? 🕵️‍♂️ Your information will remain confidential.", }

    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(language), reply_markup=await compilationkb(language))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('c_teacher_'))
async def complain_teacher(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[2]
    await state.update_data(teacher_type=data)
    text = {'uz': f"📋 {data} O‘qituvchingizning ismini kiriting", 'ru': f"📋 {data} Введите имя вашего учителя",
            'en': f"📋 {data} Please enter your teacher’s name", }

    await bot.send_message(text=text.get(language), chat_id=callback_query.from_user.id)
    await state.set_state(Complain.teacher_name)
    await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)


@dp.message(Complain.teacher_name)
async def complain_teacher(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    a = False
    for i in range(len(message.text.replace(' ', ''))):
        if message.text.replace(' ', '')[i].isdigit():
            a = True
            break
    if a:
        text2 = {'uz': '📛 Iltimos, o‘qituvchingiz ismini kiriting', 'ru': '📛 Пожалуйста, введите имя вашего учителя',
                 'en': '📛 Please enter your teacher’s name', }

        await message.answer(text=text2.get(language))
        await bot.delete_message(message_id=message.message_id - 1, chat_id=message.from_user.id)
        await state.set_state(Complain.message)
        return
    text = {'uz': '✍️ Shikoyatingizni yozing', 'ru': '✍️ Напишите свою жалобу', 'en': '✍️ Write your complaint', }

    await state.update_data(teacher_name=message.text)
    await message.answer(text=text.get(language))
    await delete_previous_messages(message.message_id, message.from_user.id)
    await state.set_state(Complain.message)


@dp.message(Complain.message)
async def Complains_messages(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    await state.update_data(message=message.text)
    if len(message.text) < 3:
        await state.set_state(Complain.message)
        text3 = {'uz': 'Shikoyatingiz kamida 4 ta sozdan iborat bolshi kerak',
                 'ru': 'Shikoyatingiz kamida 4 ta sozdan iborat bolshi kerak',
                 'en': 'Shikoyatingiz kamida 4 ta sozdan iborat bolshi kerak', }
        await message.answer(text=text3.get(language))
        await delete_previous_messages(message.message_id, message.from_user.id)
        try:
            await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id - 1)
        except TelegramBadRequest:
            pass
        return
    data = await state.get_data()
    teacher_name = data.get('teacher_name')
    teacher = data.get('teacher_type')
    text = {'uz': (f"⚠️ Siz {teacher_name} ({teacher.capitalize()})ga shikoyatgiz:\n"
                   f"💬 {message.text}"), 'ru': (f"⚠️ Вы отправили жалобу на {teacher_name} ({teacher.capitalize()}):\n"
                                                f"💬 {message.text}"),
            'en': (f"⚠️ You have sent a complaint to {teacher_name} ({teacher.capitalize()}):\n"
                   f"💬 {message.text}")}
    await message.answer(text=text.get(language), reply_markup=await kb_complain(language))
    await delete_previous_messages(message.message_id, message.from_user.id)


@dp.callback_query(F.data.startswith('s_complain_'))
async def complain32(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    teacher_name = data.get('teacher_name')
    teacher = data.get('teacher_type')
    managers = await manager()
    message = data.get('message')
    text = {'uz': ("✅ Sizning xabaringiz @SEOM2016 managerga yuborildi.\n"
                   "🔒 Sizning xabaringiz 💯 xavfsiz va 🕵️‍♂️ sizning kimligingiz sir saqlanadi."),
            'ru': ("✅ Ваше сообщение отправлено @SEOM2016 менеджеру.\n"
                   "🔒 Ваше сообщение 💯 безопасно, и 🕵️‍♂️ ваша личность будет сохранена в тайне."),
            'en': ("✅ Your message has been sent to the @SEOM2016 manager.\n"
                   "🔒 Your message is 💯 safe, and 🕵️‍♂️ your identity will remain confidential.")}
    menu = {'uz': '🏠 Bosh menu', 'ru': '🏠 Bosh menu', 'en': '🏠 Bosh menu', }
    await bot.send_message(chat_id=callback_query.from_user.id, text=text.get(language),
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                               [InlineKeyboardButton(text=menu.get(language), callback_data='menu_')]]))
    text3 = {
        'uz': (f"🛑 #shikoyat {'@' + callback_query.from_user.username if callback_query.from_user.username else ''}\n\n"
               f"👨‍🏫 {teacher.capitalize()} {teacher_name.capitalize()} ga\n"
               f"📋 Shikoyat:\n🗣️ {message}"),
        'ru': (f"🛑 #жалоба {'@' + callback_query.from_user.username if callback_query.from_user.username else ''}\n\n"
               f"👨‍🏫 {teacher.capitalize()} {teacher_name.capitalize()} - учителю\n"
               f"📋 Жалоба:\n🗣️ {message}"), 'en': (
            f"🛑 #complaint {'@' + callback_query.from_user.username if callback_query.from_user.username else ''}\n\n"
            f"👨‍🏫 Complaint against {teacher.capitalize()} {teacher_name.capitalize()}:\n"
            f"📋 Complaint:\n🗣️ {message}")}
    for manager_id in managers:
        await bot.send_message(chat_id=manager_id, text=text3.get(language),
                               reply_markup=await complain_level_manager(language, callback_query.from_user.id))
    await add_complainer(tg_id=callback_query.from_user.id, text=message, to_whom=teacher_name, type=teacher)
    await state.set_state(Complain.start)
    await state.clear()
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('mlevel_'))
async def mlevel_(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[1]
    tg_id = callback_query.data.split('_')[2]
    await complain_user_level(tg_id, level=data)
    await callback_query.message.delete()
    text = {'uz': f'🔔 Siz ushbu shikoyatni darajasini {data} ga belgiladingiz',
            'ru': f'🔔 Вы установили уровень этой жалобы как {data}',
            'en': f'🔔 You have set the level of this complaint to {data}', }
    await callback_query.answer(text=text.get(language), show_alert=True)


# ------------------------------------change users role-----------------------------------------------------------------#
@dp.message(Command('admin'))
async def admin(message: Message):
    language = await get_user_language(message.from_user.id)
    admins = await manager()
    for admin in admins:
        if admin == message.from_user.id:
            users = await all_users(message.from_user.id)
            for user in users:
                text = {'uz': f"Foydalanuvchining telegram ismi: {user.tg_name[:10]}\n"
                              f"Telegram usernamei: {'@' + user.tg_username if user.tg_username else 'mavjud emas'}\n"
                              f"FIO 📝: {user.FIO}\n"
                              f"Telefon raqami 📞: {user.tg_number}\n"
                              f"Tugilgan yili 🎂: {user.born_year}\n"
                              f"Jinsi 🚻: {user.gender}\n"
                              f"Darajasi: {user.role}\n"
                              f"Qachon qo\'shilgan: {user.register_time}",

                        'ru': f"Телеграм-имя пользователя: {user.tg_name[:10]}\n"
                              f"Телеграм-username: {'@' + user.tg_username if user.tg_username else 'не доступен'}\n"
                              f"ФИО 📝: {user.FIO}\n"
                              f"Номер телефона 📞: {user.tg_number}\n"
                              f"Год  🎂: {user.born_year}\n"
                              f"Пол 🚻: {user.gender}",

                        'en': f"User's Telegram name: {user.tg_name[:10]}\n"
                              f"Telegram username: {'@' + user.tg_username if user.tg_username else 'not available'}\n"
                              f"Full Name 📝: {user.FIO}\n"
                              f"Phone Number 📞: {user.tg_number}\n"
                              f"Year of Birth 🎂: {user.born_year}\n"
                              f"Gender 🚻: {user.gender}", }
                await message.answer(text=text.get(language),
                                     reply_markup=await change_user_role(language, user.role, user.tg_id))
            language = await get_user_language(message.from_user.id)
            await bot.send_message(chat_id=message.from_user.id,
                                   text={"ru": "ru", "en": "en", "uz": "Bosh menu"}.get(language, "en"),
                                   reply_markup=await home(language, message.from_user.id))
            await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)
            await delete_previous_messages(message.message_id, message.from_user.id)
        else:
            await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)


@dp.callback_query(F.data.startswith('admin_'))
async def admin(message: CallbackQuery):
    language = await get_user_language(message.from_user.id)
    admins = await manager()
    for admin in admins:
        if admin == message.from_user.id:
            users = await all_users(message.from_user.id)
            for user in users:
                text = {'uz': f"Foydalanuvchining telegram ismi: {user.tg_name[:10]}\n"
                              f"Telegram usernamei: {'@' + user.tg_username if user.tg_username else 'mavjud emas'}\n"
                              f"FIO 📝: {user.FIO}\n"
                              f"Telefon raqami 📞: {user.tg_number}\n"
                              f"Tugilgan yili 🎂: {user.born_year}\n"
                              f"Jinsi 🚻: {user.gender}\n"
                              f"Darajasi: {user.role}\n"
                              f"Qachon qo\'shilgan: {user.register_time}",

                        'ru': f"Телеграм-имя пользователя: {user.tg_name[:10]}\n"
                              f"Телеграм-username: {'@' + user.tg_username if user.tg_username else 'не доступен'}\n"
                              f"ФИО 📝: {user.FIO}\n"
                              f"Номер телефона 📞: {user.tg_number}\n"
                              f"Год  🎂: {user.born_year}\n"
                              f"Пол 🚻: {user.gender}",

                        'en': f"User's Telegram name: {user.tg_name[:10]}\n"
                              f"Telegram username: {'@' + user.tg_username if user.tg_username else 'not available'}\n"
                              f"Full Name 📝: {user.FIO}\n"
                              f"Phone Number 📞: {user.tg_number}\n"
                              f"Year of Birth 🎂: {user.born_year}\n"
                              f"Gender 🚻: {user.gender}", }
                await bot.send_message(chat_id=message.from_user.id, text=text.get(language),
                                       reply_markup=await change_user_role(language, user.role, user.tg_id))
            language = await get_user_language(message.from_user.id)
            await bot.send_message(chat_id=message.from_user.id,
                                   text={"ru": "ru", "en": "en", "uz": "Bosh menu"}.get(language, "en"),
                                   reply_markup=await home(language, message.from_user.id))
            await message.message.delete()
            await delete_previous_messages(message.message.message_id, message.from_user.id)


@dp.callback_query(F.data.startswith('user_role_'))
async def changer_role(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    user_id = callback_query.data.split('_')[2]
    role = callback_query.data.split('_')[3]
    await changer_user_role(user_id, role)
    user = await get_single_role(user_id)
    await callback_query.answer(
        text=f"Siz {user.tg_name[:20]} ni darajasini {role} ga muaffaqiyat bilan o'zgartirdingiz ✅", show_alert=True)
    text = {'uz': (f"Foydalanuvchining telegram ismi: {user.tg_name[:10]}\n"
                   f"Telegram usernamei: {'@' + user.tg_username if user.tg_username else 'mavjud emas'}\n"
                   f"FIO 📝: {user.FIO}\n"
                   f"Telefon raqami 📞: {user.tg_number}\n"
                   f"Tugilgan yili 🎂: {user.born_year}\n"
                   f"Jinsi 🚻: {user.gender}\n"
                   f"Darajasi:⚠️⚠️⚠️ {user.role} ⚠️⚠️⚠️\n"
                   f"Qachon qo'shilgan: {str(user.register_time)}"),
            'ru': (f"Телеграм-имя пользователя: {user.tg_name[:10]}\n"
                   f"Телеграм-username: {'@' + user.tg_username if user.tg_username else 'не доступен'}\n"
                   f"ФИО 📝: {user.FIO}\n"
                   f"Номер телефона 📞: {user.tg_number}\n"
                   f"Год 🎂: {user.born_year}\n"
                   f"Darajasi :⚠️⚠️⚠️ {user.role} ⚠️⚠️⚠️\n"
                   f"Пол 🚻: {user.gender}"), 'en': (f"User's Telegram name: {user.tg_name[:10]}\n"
                                                    f"Telegram username: {'@' + user.tg_username if user.tg_username else 'not available'}\n"
                                                    f"Full Name 📝: {user.FIO}\n"
                                                    f"Phone Number 📞: {user.tg_number}\n"
                                                    f"Year of Birth 🎂: {user.born_year}\n"
                                                    f"Darajasi :⚠️⚠️⚠️ {user.role} ⚠️⚠️⚠️\n"
                                                    f"Gender 🚻: {user.gender}")}
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text=text.get(language),
                                reply_markup=await change_user_role(language, user.role, user.tg_id))


@dp.callback_query(F.data.startswith('send_message_'))
async def send_message2_(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '💬 Xabaringizni yozing', 'ru': '💬 Напишите ваше сообщение', 'en': '💬 Write your message'}
    await callback_query.message.answer(text=text.get(language), reply_markup=await back_home(language))
    await state.update_data(tg_id=callback_query.data.split("_")[2])
    await state.set_state(send_message_to_user.message)


# ------------------------------------ All Complains -------------------------------------------------------------------#
@dp.callback_query(F.data.startswith('all_complains_'))
async def all_complains_(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    all1_complain = await all_complains()
    for all_complain in all1_complain:
        text = {
            'uz': (
                f'📄 ID: {all_complain.id}\n'
                f'👤 Shikoyatchi Telegram ID: {all_complain.complainer_tg_id}\n'
                f'🧑‍🏫 Ayblanuvchi: {all_complain.teacher_type} o\'qituvchi {all_complain.to_whom}ga\n'
                f'✍️ Shikoyat: "{all_complain.text.capitalize()}"\n'
                f'⚖️ Admin tomonidan shikoyat darajasi: '
                f'{"❓ Hali belgilanmagan" if all_complain.level == "Not chosen" else "📊 O\'rtacha" if all_complain.level == "normal" else "🔥 Jiddiy"}\n\n'
                f'🔧 Agar siz bu shikoyatni o\'zgartirmoqchi bo\'lsangiz, pastdagi tugmani bosing.'
            ),
            'ru': (
                f'📄 ID: {all_complain.id}\n'
                f'👤 ID Телеграмм жалобщика: {all_complain.complainer_tg_id}\n'
                f'🧑‍🏫 Обвиняемый: учитель {all_complain.teacher_type} {all_complain.to_whom}\n'
                f'✍️ Жалоба: "{all_complain.text.capitalize()}"\n'
                f'⚖️ Уровень жалобы, установленный администратором: '
                f'{"❓ Ещё не выбран" if all_complain.level == "Not chosen" else "📊 Средний" if all_complain.level == "normal" else "🔥 Серьёзный"}\n\n'
                f'🔧 Если вы хотите изменить эту жалобу, нажмите кнопку ниже.'
            ),
            'en': (
                f'📄 ID: {all_complain.id}\n'
                f'👤 Complainant\'s Telegram ID: {all_complain.complainer_tg_id}\n'
                f'🧑‍🏫 Accused: {all_complain.teacher_type} teacher {all_complain.to_whom}\n'
                f'✍️ Complaint: "{all_complain.text.capitalize()}"\n'
                f'⚖️ Complaint level set by admin: '
                f'{"❓ Not chosen yet" if all_complain.level == "Not chosen" else "📊 Average" if all_complain.level == "normal" else "🔥 Serious"}\n\n'
                f'🔧 If you want to edit this complaint, please click the button below.'
            )
        }

        await bot.send_message(text=text.get(language), chat_id=callback_query.message.chat_id,
                               reply_markup=await complain_level_manager(language, all_complain.complainer_tg_id))
        text2 = {'ru': "Главное меню",  # Text in Russian
                 'en': "Main Menu",  # Text in English
                 'uz': "Bosh menu"  # Text in Uzbek
                 }
        await bot.send_message(chat_id=callback_query.from_user.id, text=text2.get(language),
                               reply_markup=await home(language, callback_query.from_user.id))
        await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('all_registration_'))
async def all_registration_(callback_query: CallbackQuery):
    langauge = await get_user_language(callback_query.from_user.id)
    lists = await all_registred_students()
    for list in lists:
        text = {'uz': f'🆔 ID: {list.id}\n\n'
                      f'👤 Student ismi: {list.user_name}\n'
                      f'📱 Telegram foydalanuvchi nomi: {"Mavjud emas" if list.telegram_information == "None" else "@" + str(list.telegram_information)}\n'
                      f'🎂 Yoshi: {list.born_year}\n'
                      f'📞 Telefon raqami: {list.number}\n'
                      f'⚥ Jinsi: {list.gender}\n'
                      f'📚 Tanlagan kurs nomi: {list.course}\n'
                      f'📈 {list.course.capitalize()}ga tanlangan bosqichi: {list.level}\n'
                      f'⏰ {list.course.capitalize()}ga tanlangan vaqti: {list.time}\n'
                      f'📞 Studentga aloqga chiqishdimi: {"✅ Ha" if list.is_connected != "no" else "❌ Yo\'q"}\n'
                      f'📅 Registratsiyadan o‘tgan vaqti: {list.registered_time}',

                'ru': f'🆔 ID: {list.id}\n\n'
                      f'👤 Имя студента: {list.user_name}\n'
                      f'📱 Telegram имя пользователя: {"Отсутствует" if list.telegram_information == "None" else "@" + str(list.telegram_information)}\n'
                      f'🎂 Возраст: {list.born_year}\n'
                      f'📞 Номер телефона: {list.number}\n'
                      f'⚥ Пол: {list.gender}\n'
                      f'📚 Название выбранного курса: {list.course}\n'
                      f'📈 Уровень выбран для курса {list.course.capitalize()}: {list.level}\n'
                      f'⏰ Время, выбранное для курса {list.course.capitalize()}: {list.time}\n'
                      f'📞 Связались со студентом: {"✅ Да" if list.is_connected != "no" else "❌ Нет"}\n'
                      f'📅 Время регистрации: {list.registered_time}',

                'en': f'🆔 ID: {list.id}\n\n'
                      f'👤 Student Name: {list.user_name}\n'
                      f'📱 Telegram Username: {"Not available" if list.telegram_information == "None" else "@" + str(list.telegram_information)}\n'
                      f'🎂 Age: {list.born_year}\n'
                      f'📞 Phone Number: {list.number}\n'
                      f'⚥ Gender: {list.gender}\n'
                      f'📚 Selected Course Name: {list.course}\n'
                      f'📈 Selected Level for {list.course.capitalize()}: {list.level}\n'
                      f'⏰ Selected Time for {list.course.capitalize()}: {list.time}\n'
                      f'📞 Contacted the student: {"✅ Yes" if list.is_connected != "no" else "❌ No"}\n'
                      f'📅 Registration Time: {list.registered_time}', }

        await bot.send_message(text=text.get(langauge), chat_id=callback_query.from_user.id, parse_mode='HTML')
    text2 = {'ru': "Главное меню",  # Text in Russian
             'en': "Main Menu",  # Text in English
             'uz': "Bosh menu"  # Text in Uzbek
             }
    await bot.send_message(chat_id=callback_query.from_user.id, text=text2.get(langauge),
                           reply_markup=await home(langauge, callback_query.from_user.id))
    await callback_query.message.delete()
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


# ------------------------------------ Send message to all users--------------------------------------------------------#
@dp.message(Command('send_message'))
async def send_message(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    text = {
        'uz': '📸 Barcha foydalanuvchilarga yuboriladigan tayyor rasmni yo videoni tashlang. 📝 Suratning ostida matn bo\'lishi shart va uni oldindan tayyorlab oling.',
        'ru': '📸 Отправьте готовое изображение, которое будет отправлено всем пользователям. 📝 Под изображением должен быть текст, и его нужно подготовить заранее.',
        'en': '📸 Upload the prepared image or video to be sent to all users. 📝 The text should be below the image and should be prepared in advance.'}

    await bot.send_message(text=text.get(language), chat_id=message.from_user.id,
                           reply_markup=await back_home(language))
    await message.delete()
    await state.set_state(send_message_to_user.message)
    await delete_previous_messages(message.message_id, message.from_user.id)


@dp.message(send_message_to_user.message)
async def send_all_user_message223232(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if message.text:
        if message.text[0] == '🏠' or message.text[0] == '🔙':
            text4 = {'ru': "Главное меню",  # Text in Russian
                     'en': "Main Menu",  # Text in English
                     'uz': "Bosh menu"  # Text in Uzbek
                     }
            await bot.send_message(chat_id=message.from_user.id, text=text4.get(language),
                                   reply_markup=await home(language, message.from_user.id))
            await state.clear()
            await delete_previous_messages(message.message_id + 1, message.from_user.id)
            return
        else:
            text = {'uz': '📸 Iltimos, surat/video ostida 📝 matn bo\'lishi shart.',
                    'ru': '📸 Пожалуйста, под изображением/видео должен быть 📝 текст.',
                    'en': '📸 Please make sure there is 📝 text below the image/video.'}
            await message.answer(text=text.get(language), reply_markup=await back_home(language))
            await state.set_state(send_message_to_user.message)
            await delete_previous_messages(message.message_id, message.from_user.id)
            return
    if not message.caption:
        text = {'uz': '📸 Iltimos, surat/video ostida 📝 matn bo\'lishi shart.',
                'ru': '📸 Пожалуйста, под изображением/видео должен быть 📝 текст.',
                'en': '📸 Please make sure there is 📝 text below the image/video.'}
        await message.answer(text=text.get(language), reply_markup=await back_home(language))
        await state.set_state(send_message_to_user.message)
        await delete_previous_messages(message.message_id, message.from_user.id)
        return
    if message.photo or message.video:
        for user in await all_users(message.from_user.id):
            try:
                if message.video:
                    await bot.send_video(chat_id=user.tg_id, video=message.video.file_id, caption=message.caption)
                elif message.photo:
                    await bot.send_photo(chat_id=user.tg_id, photo=message.photo[-1].file_id, caption=message.caption)
            except:
                pass
        await delete_previous_messages(message.message_id, message.from_user.id)
        text4 = {'ru': "Главное меню",  # Text in Russian
                 'en': "Main Menu",  # Text in English
                 'uz': "Bosh menu"  # Text in Uzbek
                 }
        await bot.send_message(chat_id=message.from_user.id, text=text4.get(language),
                               reply_markup=await home(language, message.from_user.id))


# ------------------------------------ Settings ------------------------------------------------------------------------#
@dp.callback_query(F.data.startswith('settings'))
async def settings(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '🔧 Sozlamalar',  # Settings - 🔧 (Wrench)
            'ru': '🔧 Настройки',  # Settings - 🔧 (Wrench)
            'en': '🔧 Settings'  # Settings - 🔧 (Wrench)
            }
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                chat_id=callback_query.from_user.id, reply_markup=await settings_kb(language))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


# ------------------------------------Full_registration-----------------------------------------------------------------#
@dp.callback_query(F.data.startswith('fregister_'))
async def fregister(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '📝 FIO yingizni kiriting:\n📌 Misol uchun: Abdulkhaev Xusanboy Solijonovich',
            # Enter Full Name - 📝 (Writing)
            'ru': '📝 Введите ваше ФИО:\n📌 Например: Абдулхаев Хусанбой Солиджонович',  # Enter Full Name - 📝 (Writing)
            'en': '📝 Enter your Full Name:\n📌 For example: Abdulkhaev Xusanboy Solijonovich'
            # Enter Full Name - 📝 (Writing)
            }
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                chat_id=callback_query.from_user.id)
    await state.set_state(Register_full.fullname)
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.message(Register_full.fullname)
async def full_name_register_def(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    a = False
    for i in message.text:
        if i in str([1, 2, 3, 4, 5, 6, 7, 8, 9, 0]):
            a = True
            break
    c = message.text.split(' ')
    if len(c) != 3:
        a = True
    else:
        a = False
    if a:
        await state.set_state(Register_full.fullname)
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
    text = {'uz': '👇 Yoshni tanlang:', 'ru': '👇 Выберите ваш возраст:', 'en': '👇 Select your age:'}
    await state.update_data(fullname=message.text)
    await state.set_state(Register_full.start)
    await bot.send_message(text=text.get(language), chat_id=message.from_user.id, reply_markup=await fregister_year(1))
    await delete_previous_messages(message.message_id, message.from_user.id)
    await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)


@dp.callback_query(F.data.startswith('fullname_f'))
async def full_name_register_def(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '👇 Yoshni tanlang:', 'ru': '👇 Выберите ваш возраст:', 'en': '👇 Select your age:'}
    await bot.edit_message_text(text=text.get(language), chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id, reply_markup=await fregister_year(1))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('yfregister_year_'))
async def hyear3_get(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    text = {'uz': '📅 Tug‘ilgan oyingizni tanlang:',  # Choose your birth month - 📅 (Calendar)
            'ru': '📅 Выберите ваш месяц рождения:',  # Choose your birth month - 📅 (Calendar)
            'en': '📅 Select your birth month:'  # Choose your birth month - 📅 (Calendar)
            }
    await bot.edit_message_text(message_id=callback_query.message.message_id, text=text.get(language),
                                chat_id=callback_query.from_user.id, reply_markup=await fmonth(language))
    if len(callback_query.data.split('_')) == 4:
        await state.update_data(year=callback_query.data.split('_')[2])
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('ypfregister_year2_'))
async def usual2(callback_query: CallbackQuery):
    language = await get_user_language(callback_query.from_user.id)
    data = callback_query.data.split('_')[2]
    text = {'uz': '👇 Yoshni tanlang:', 'ru': '👇 Выберите ваш возраст:', 'en': '👇 Select your age:'}
    await bot.edit_message_text(text=text.get(language), chat_id=callback_query.from_user.id,
                                reply_markup=await fregister_year(int(data)),
                                message_id=callback_query.message.message_id)
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('fmonth_'))
async def month_callback(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(tg_id=callback_query.from_user.id)
    data = await state.get_data()
    if len(callback_query.data.split('_')) == 3:
        month_name = callback_query.data.split('_')[2][2:]
        month = callback_query.data.split('_')[1]
        await state.update_data(fake_month=month_name)
        await state.update_data(month=month)
    else:
        month_name = data.get('fake_month')
        month = data.get('month')
    years = await state.get_data()
    year = years.get('year')
    text = {'uz': f'{month_name} oyi uchun kunni tanlang:',  # For Uzbek
            'ru': f'Выберите день для месяца {month_name}:',  # For Russian
            'en': f'Choose the day for {month_name}:'  # For English
            }
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(language), reply_markup=await fdays(month, year))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('fday_'))
async def day_callback(callback_query: CallbackQuery, state: FSMContext):
    if len(callback_query.data.split('_')) == 3:
        day = callback_query.data.split('_')[1]
        await state.update_data(day=day)
    language = await get_user_language(tg_id=callback_query.from_user.id)
    text = {'uz': '📱 Telefon raqamingizni yozing yoki pasdagi tugmani bosing:',  # Uzbek
            'ru': '📱 Напишите ваш номер телефона или нажмите кнопку ниже:',  # Russian
            'en': '📱 Enter your phone number or press the button below:'  # English
            }
    await state.set_state(Register_full.number)
    await bot.send_message(text=text.get(language), chat_id=callback_query.from_user.id,
                           reply_markup=await share_phone_number(language))
    await delete_previous_messages(id=callback_query.from_user.id, message=callback_query.message.message_id)
    await bot.delete_message(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id)


@dp.message(Register_full.number)
async def Register_full_number(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    if message.contact:
        await state.update_data(number=message.contact.phone_number)
        match language:
            case 'uz':
                await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                       reply_markup=await fgender(language))
            case 'ru':
                await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                       reply_markup=await fgender(language))
            case 'en':
                await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                       reply_markup=await fgender(language))
        await state.set_state(Register.start)
        await delete_previous_messages(message.message_id, message.from_user.id)
        await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)
    if message.text:
        if message.text[:1] == '🔙':
            data = await state.get_data()
            month_name = data.get('fake_month')
            month = data.get('month')
            year = data.get('year')
            text = {'uz': f'{month_name} oyi uchun kunni tanlang:', 'ru': f'Выберите день для месяца {month_name}:',
                    'en': f'Choose the day for {month_name}:'}
            await bot.send_message(chat_id=message.from_user.id, text=text.get(language),
                                   reply_markup=await fdays(month, year))
            await bot.delete_message(message_id=message.message_id - 1, chat_id=message.from_user.id)
            return
        if not message.text[1:].isdigit() or 9 <= len(str(message.text)) >= 13:
            await state.set_state(Register.number)
            match language:
                case 'uz':
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='Iltimos telfon raqamingizda faqat sonlardan foydalaning',
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
        if message.text[0] == '+':
            await state.update_data(number=message.text)
        else:
            await state.update_data(number=f'+{message.text}')

        match language:
            case 'uz':
                await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                       reply_markup=await fgender(language))
            case 'ru':
                await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                       reply_markup=await fgender(language))
            case 'en':
                await bot.send_message(chat_id=message.from_user.id, text='Iltimos jinsingizni tanlang',
                                       reply_markup=await fgender(language))
        await state.set_state(Register.start)
        await delete_previous_messages(message.message_id, message.from_user.id)
        await bot.delete_message(message_id=message.message_id, chat_id=message.from_user.id)


@dp.callback_query(F.data.startswith('fgender_'))
async def register_gender(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    if len(callback_query.data.split('_')) == 3:
        await state.update_data(gender=callback_query.data.split('_')[1])
        await state.update_data(fake_gender=callback_query.data.split('.')[1])
    data = await state.get_data()
    full_name = data.get('fullname')
    year = data.get('year')
    month_name = data.get('fake_month')
    month = data.get('month')
    day = data.get('day')
    number = data.get('number')
    gender = data.get('gender')
    fake_gender = data.get('fake_gender')
    born_year = f'{day:02}/{month:02}/{year:04}'
    text = {'uz': f'👤 Ism-sharifingiz: {full_name}\n'
                  f'📅 Tugilgan yilingiz: {year}\n'
                  f'⭐ Tugilgan oyingiz: {month_name}\n'
                  f'🎉 Tugilgan kuningiz: {day}\n'
                  f'📞 Telefon raqamingiz: {number}\n'
                  f'🚻 Jinsingiz: {fake_gender}\n',

            'ru': f'👤 Ваше имя: {full_name}\n'
                  f'📅 Год рождения: {year}\n'
                  f'⭐ Месяц рождения: {month_name}\n'
                  f'🎉 День рождения: {day}\n'
                  f'📞 Ваш номер телефона: {number}\n'
                  f'🚻 Ваш пол: {fake_gender}\n',

            'en': f'👤 Your name: {full_name}\n'
                  f'📅 Year of birth: {year}\n'
                  f'⭐ Month of birth: {month_name}\n'
                  f'🎉 Day of birth: {day}\n'
                  f'📞 Your phone number: {number}\n'
                  f'🚻 Your gender: {fake_gender}\n'}
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(language), reply_markup=await fconifim(language))


@dp.callback_query(F.data.startswith('fconifim_'))
async def salom_dunyo(callback_query: CallbackQuery, state: FSMContext):
    language = await get_user_language(callback_query.from_user.id)
    data = await state.get_data()
    full_name = data.get('fullname')
    year = data.get('year')
    month = data.get('month')
    day = data.get('day')
    number = data.get('number')
    gender = data.get('gender')
    born_year = f'{day:02}/{month:02}/{year:04}'
    text = {'ru': "Главное меню",  # Text in Russian
            'en': "Main Menu",  # Text in English
            'uz': "Bosh menu"  # Text in Uzbek
            }
    await add_user_full(tg_id=callback_query.from_user.id,
                        username=callback_query.from_user.username if callback_query.from_user.username else 'no user name',
                        name=callback_query.from_user.first_name, number=number, fullname=full_name,
                        born_year=born_year, gender=gender)
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(language), reply_markup=await home(language, callback_query.from_user.id))
    await delete_previous_messages(callback_query.message.message_id, callback_query.from_user.id)


@dp.callback_query(F.data.startswith('lan2_'))
async def get_user_lanuage_nothing(callback_query: CallbackQuery):
    langauge = await get_user_language(callback_query.from_user.id)
    text = {'ru': "🇷🇺: Выберите ваш язык 🗣️", 'en': "🇬🇧: Select your preferred language 🗣️",
            'uz': "🇺🇿: Biladigan tilingizni tanlang 🗣️"}
    await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id,
                                text=text.get(langauge), reply_markup=await flanguages(langauge))


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
        await message.delete()
    except TelegramBadRequest as error:
        print("Failed to delete message:", error)


# --------------------------------- Polling the bot --------------------------------------------------------------------#
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

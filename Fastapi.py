import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select

from main import Complain_db

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///database.sqlite3"  # Async SQLite URL
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# External API setup
PHP_API_URL = "https://fairly-lasting-leech.ngrok-free.app"
user = '/users'
report='/reports'
CSRF_TOKEN = "oWYKV5bgVfEHQ7avAFbK1IO9xcXqdAM6WUv75y7D"

async def send_to_php_api(data,url):
    async with httpx.AsyncClient() as client:
        try:

            response = await client.post(PHP_API_URL+url, json=data,)
            if response.status_code == 201:
                print(f"Data sent successfully")
                return True
            else:

                return False
        except httpx.RequestError as e:
            return False

async def fetch_and_send_registering_data():
    from main import Registering  # Ensure this model is correctly defined

    while True:  # Continuous loop
        async with async_session() as session:
            try:
                # Fetch records with 'is_connected != "yes"'
                query = select(Registering)
                result = await session.execute(query)
                records = result.scalars().all()
                for record in records:
                    data = {
                        'id':int(record.id),
                        "gender": "male" if record.gender == '🤵 Erkak kishi' else "female",
                        "user_id": int(record.tg_id),
                        "full_name": record.user_name,
                        "status": 'uncalled' if record.is_connected=='no' else 'called',
                        "birthday": record.born_year,
                        "group": record.course,
                        "comment": record.comment_for_call,
                        "phone_number": str(record.number),
                        'created_at':str(record.registered_time),
                        'time':str(record.time),
                        'level':str(record.level)
                    }


                if await send_to_php_api(data, user):
                            record.is_connected = "yes"

                # Commit changes
                await session.commit()

            except Exception as e:
                pass

        await asyncio.sleep(10)  # Wait 10 seconds before rechecking

async def fetch_and_send_complain_data():

    while True:  # Continuous loop
        async with async_session() as session:
            try:
                # Fetch records with 'is_connected != "yes"'
                query = select(Complain_db)
                result = await session.execute(query)
                records = result.scalars().all()

                for record in records:
                    data = {
                        'id':int(record.id),
                        "user_id": int(record.complainer_tg_id),
                        "rating": str(record.level),
                        "message": record.text,
                        'created_at':str(record.time),
                        'title':str(record.to_whom),
                        'type':str(record.teacher_type)
                    }

                # Commit changes
                await session.commit()

            except Exception as e:
                pass
        await asyncio.sleep(10)  # Wait 10 seconds before rechecking

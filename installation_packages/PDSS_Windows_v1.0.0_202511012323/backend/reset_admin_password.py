import asyncio
from app.database import AsyncSessionLocal
from passlib.context import CryptContext
from sqlalchemy import update
from app.models import User

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def reset_password():
    password_hash = pwd_context.hash('admin123')
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.username == 'admin')
            .values(password_hash=password_hash)
        )
        await db.commit()
    print("Admin password reset to 'admin123'")

asyncio.run(reset_password())


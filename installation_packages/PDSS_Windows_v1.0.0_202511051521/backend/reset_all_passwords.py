import asyncio
from app.database import AsyncSessionLocal
from passlib.context import CryptContext
from sqlalchemy import update
from app.models import User

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def reset_passwords():
    passwords = {
        'admin': 'admin123',
        'pmo_user': 'pmo123',
        'pm1': 'pm123',
        'pm2': 'pm123',
        'procurement1': 'proc123',
        'finance1': 'finance123'
    }
    
    async with AsyncSessionLocal() as db:
        for username, password in passwords.items():
            password_hash = pwd_context.hash(password)
            result = await db.execute(
                update(User)
                .where(User.username == username)
                .values(password_hash=password_hash)
            )
            print(f"Updated {username}: {result.rowcount} row(s)")
        await db.commit()
    print("\nAll passwords reset!")

asyncio.run(reset_passwords())


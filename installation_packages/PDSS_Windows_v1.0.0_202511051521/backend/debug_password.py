import asyncio
from app.auth import verify_password, get_password_hash
from app.database import get_db
from app.models import User
from sqlalchemy import select

async def debug_password():
    async for db in get_db():
        result = await db.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()
        
        if not user:
            print('❌ Admin user not found!')
            return
            
        print(f'✅ Admin user found: {user.username}')
        print(f'📊 User ID: {user.id}')
        print(f'📊 Role: {user.role}')
        print(f'📊 Active: {user.is_active}')
        print(f'📊 Password hash: {user.password_hash[:50]}...')
        
        test_passwords = ['admin123', 'admin', 'password', '123456', '']
        
        print('\n🔍 Testing password verification:')
        for test_pwd in test_passwords:
            is_valid = verify_password(test_pwd, user.password_hash)
            status = '✅ VALID' if is_valid else '❌ INVALID'
            print(f'  Password "{test_pwd}": {status}')
        
        print('\n🔧 Testing hash creation:')
        new_password = 'Test123456'
        new_hash = get_password_hash(new_password)
        print(f'  New password: {new_password}')
        print(f'  New hash: {new_hash[:50]}...')
        
        is_new_valid = verify_password(new_password, new_hash)
        print(f'  New hash verification: {"✅ VALID" if is_new_valid else "❌ INVALID"}')
        
        is_old_with_new_hash = verify_password('admin123', new_hash)
        print(f'  Old password with new hash: {"✅ VALID" if is_old_with_new_hash else "❌ INVALID"}')
        
        break

if __name__ == "__main__":
    asyncio.run(debug_password())

import asyncio
from app.database import get_db
from app.models import User
from app.schemas import UserUpdate
from app.crud import update_user, get_user
from sqlalchemy import select

async def test_user_update():
    """Test user update process"""
    
    async for db in get_db():
        # Get the admin user
        result = await db.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()
        
        if not user:
            print('❌ Admin user not found!')
            return
            
        print(f'✅ Admin user found: {user.username} (ID: {user.id})')
        print(f'📊 Current password hash: {user.password_hash[:50]}...')
        
        # Test updating password
        print('\n🔧 Testing password update...')
        
        # Create update data
        user_update = UserUpdate(password="NewTestPassword123")
        print(f'📝 Update data: {user_update.dict()}')
        
        # Call update function
        try:
            updated_user = await update_user(db, user.id, user_update)
            if updated_user:
                print(f'✅ User update successful!')
                print(f'📊 New password hash: {updated_user.password_hash[:50]}...')
                
                # Get the user again to see the actual stored hash
                result_after = await db.execute(select(User).where(User.id == user.id))
                user_after = result_after.scalar_one_or_none()
                
                if user_after and user_after.password_hash != user.password_hash:
                    print('✅ Password hash was updated in database!')
                else:
                    print('❌ Password hash was NOT updated in database!')
                    
                # Test login with new password
                from app.auth import verify_password
                is_valid = verify_password("NewTestPassword123", updated_user.password_hash)
                print(f'🔍 New password verification: {"✅ VALID" if is_valid else "❌ INVALID"}')
                
                # Test login with old password
                is_old_valid = verify_password("admin123", updated_user.password_hash)
                print(f'🔍 Old password verification: {"✅ VALID" if is_old_valid else "❌ INVALID"}')
                
            else:
                print('❌ User update failed - no user returned')
                
        except Exception as e:
            print(f'❌ User update failed with error: {e}')
        
        break

if __name__ == "__main__":
    asyncio.run(test_user_update())

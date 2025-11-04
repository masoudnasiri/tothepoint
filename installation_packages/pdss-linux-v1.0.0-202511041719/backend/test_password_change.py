import asyncio
from app.database import get_db
from app.models import User
from app.schemas import UserUpdate
from app.crud import update_user, get_user
from app.auth import verify_password
from sqlalchemy import select

async def test_password_change():
    """Test password change functionality"""
    
    async for db in get_db():
        # Get the admin user
        result = await db.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()
        
        if not user:
            print('❌ Admin user not found!')
            return
            
        print(f'✅ Admin user found: {user.username} (ID: {user.id})')
        print(f'📊 Current password hash: {user.password_hash[:50]}...')
        
        # Test current password
        current_password_works = verify_password("admin123", user.password_hash)
        print(f'🔍 Current password "admin123" works: {"✅ YES" if current_password_works else "❌ NO"}')
        
        # Test changing password
        print('\n🔧 Testing password change...')
        new_password = "NewPassword123"
        user_update = UserUpdate(password=new_password)
        
        print(f'📝 Update data: {user_update.dict()}')
        
        try:
            # Call update function
            updated_user = await update_user(db, user.id, user_update)
            
            if updated_user:
                print('✅ User update function returned successfully')
                
                # Get the user again from database to verify the change
                result_after = await db.execute(select(User).where(User.id == user.id))
                user_after = result_after.scalar_one_or_none()
                
                if user_after:
                    print(f'📊 New password hash: {user_after.password_hash[:50]}...')
                    
                    # Test if hash changed
                    if user_after.password_hash != user.password_hash:
                        print('✅ Password hash was updated in database!')
                        
                        # Test new password
                        new_password_works = verify_password(new_password, user_after.password_hash)
                        print(f'🔍 New password "{new_password}" works: {"✅ YES" if new_password_works else "❌ NO"}')
                        
                        # Test old password (should fail)
                        old_password_works = verify_password("admin123", user_after.password_hash)
                        print(f'🔍 Old password "admin123" works: {"✅ YES" if old_password_works else "❌ NO"}')
                        
                        if new_password_works and not old_password_works:
                            print('🎉 Password change successful!')
                        else:
                            print('❌ Password change failed - verification issues')
                    else:
                        print('❌ Password hash was NOT updated in database!')
                else:
                    print('❌ Could not retrieve user after update')
            else:
                print('❌ User update function returned None')
                
        except Exception as e:
            print(f'❌ Password change failed with error: {e}')
            import traceback
            traceback.print_exc()
        
        break

if __name__ == "__main__":
    asyncio.run(test_password_change())

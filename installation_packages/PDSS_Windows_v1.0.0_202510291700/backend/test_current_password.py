from app.auth import verify_password

# Current hash from database
hash_from_db = "$2b$12$VMiigG4un.xlZ7CuhAIot.MAi1EYsyeCZ.w9UrGi3nSmcarYuh7r."

test_passwords = [
    'admin123', 
    'admin', 
    'password', 
    '123456', 
    'Test123456', 
    'NewTestPassword123',
    'password123',
    'admin123456'
]

print('🔍 Testing passwords against current hash:')
for pwd in test_passwords:
    is_valid = verify_password(pwd, hash_from_db)
    status = '✅ VALID' if is_valid else '❌ INVALID'
    print(f'  Password "{pwd}": {status}')

from app.auth import verify_password

# Current hash from database
hash_from_db = "$2b$12$Jzh53hgSwi7biljEy.YjWe29kV4U0gbZsr81riXysFnUQwR0pRnYi"

test_passwords = [
    'admin123', 
    'admin', 
    'password', 
    '123456',
    'Test123456',
    'NewPassword123'
]

print('Testing passwords against current admin hash:')
for pwd in test_passwords:
    is_valid = verify_password(pwd, hash_from_db)
    status = 'VALID' if is_valid else 'INVALID'
    print(f'  Password "{pwd}": {status}')

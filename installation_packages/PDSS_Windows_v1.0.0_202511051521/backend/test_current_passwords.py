from app.auth import verify_password

# Current hash from database
hash_from_db = "$2b$12$ylRAM2hBBThQewEAv5.t/OvKkO63ywIA2mwoTtmPbt6NH4OfNy2GW"

test_passwords = [
    'admin123', 
    'NewPassword123', 
    'admin', 
    'password'
]

print('Testing passwords against current hash:')
for pwd in test_passwords:
    is_valid = verify_password(pwd, hash_from_db)
    status = 'VALID' if is_valid else 'INVALID'
    print(f'  Password "{pwd}": {status}')

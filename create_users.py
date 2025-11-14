from werkzeug.security import generate_password_hash

# Пароль для всех тестовых пользователей
password = "password123"
hash = generate_password_hash(password)

print(f"Хеш пароля: {hash}")

# Вставьте этот хеш в init_database.sql для всех пользователей
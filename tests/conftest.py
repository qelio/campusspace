import pytest
import os
import tempfile
from flask import Flask, session
import pytest
import sys
import os

# Добавляем корень проекта в sys.path, чтобы pytest видел app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from app import get_db_connection
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

# Настройка тестовой базы данных
TEST_DB_CONFIG = {
    'host': os.environ.get('TEST_DB_HOST', 'localhost'),
    'user': os.environ.get('TEST_DB_USER', 'root'),
    'password': os.environ.get('TEST_DB_PASSWORD', 'slava2012'),
    'database': os.environ.get('TEST_DB_NAME', 'university_rooms1')
}

@pytest.fixture
def app():
    """Фикстура для тестового приложения"""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False  # Отключаем CSRF для тестов
    })
    
    with flask_app.app_context():
        setup_test_database()
    
    yield flask_app
    
    # Очистка после тестов
    with flask_app.app_context():
        cleanup_test_database()

@pytest.fixture
def client(app):
    """Фикстура для тестового клиента"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Фикстура для CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """Авторизованный клиент"""
    # Создаем тестового пользователя
    create_test_user()
    
    # Логинимся
    client.post('/login', data={
        'email': 'test@university.ru',
        'password': 'testpassword123'
    })
    
    return client

def create_test_user():
    """Создание тестового пользователя"""
    try:
        conn = mysql.connector.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, is_active)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            password_hash = VALUES(password_hash),
            is_active = VALUES(is_active)
        """, (
            'test@university.ru',
            generate_password_hash('testpassword123'),
            'Тестовый Пользователь',
            True
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Ошибка создания тестового пользователя: {e}")

def setup_test_database():
    """Создание тестовых таблиц и данных"""
    try:
        # Подключаемся без указания базы данных для ее создания
        temp_config = TEST_DB_CONFIG.copy()
        temp_config['database'] = None
        
        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        
        # Создаем тестовую базу данных если не существует
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DB_CONFIG['database']}")
        cursor.execute(f"USE {TEST_DB_CONFIG['database']}")
        
        # Создаем таблицы (упрощенная версия)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buildings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type ENUM('faculty', 'department', 'laboratory') NOT NULL,
                parent_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                building_id INT NOT NULL,
                room_number VARCHAR(20) NOT NULL,
                location_description TEXT,
                width DECIMAL(8,2) NOT NULL,
                length DECIMAL(8,2) NOT NULL,
                ceiling_height DECIMAL(4,2) NOT NULL,
                purpose VARCHAR(255),
                room_type ENUM('lecture', 'laboratory', 'office', 'storage', 'other') NOT NULL,
                department_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Ошибка настройки тестовой БД: {e}")
        raise

def cleanup_test_database():
    """Очистка тестовой базы данных"""
    try:
        conn = mysql.connector.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        
        # Очищаем таблицы
        cursor.execute("DELETE FROM rooms")
        cursor.execute("DELETE FROM departments")
        cursor.execute("DELETE FROM buildings")
        cursor.execute("DELETE FROM users")
        
        # Сбрасываем автоинкремент
        cursor.execute("ALTER TABLE rooms AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE departments AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE buildings AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Ошибка очистки тестовой БД: {e}")
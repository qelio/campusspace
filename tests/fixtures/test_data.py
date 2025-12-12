"""Тестовые данные для тестов"""

TEST_BUILDINGS = [
    {'name': 'Главный корпус'},
    {'name': 'Корпус А'},
    {'name': 'Лабораторный корпус'},
]

TEST_ROOMS = [
    {
        'building_id': 1,
        'room_number': '101',
        'width': 5.0,
        'length': 10.0,
        'ceiling_height': 3.0,
        'room_type': 'lecture',
        'purpose': 'Лекционная аудитория'
    },
    {
        'building_id': 1,
        'room_number': '201',
        'width': 8.0,
        'length': 12.0,
        'ceiling_height': 3.5,
        'room_type': 'laboratory',
        'purpose': 'Химическая лаборатория'
    },
    {
        'building_id': 2,
        'room_number': '105',
        'width': 4.0,
        'length': 6.0,
        'ceiling_height': 2.8,
        'room_type': 'office',
        'purpose': 'Кабинет преподавателя'
    },
]

TEST_USERS = [
    {
        'email': 'admin@university.ru',
        'password': 'admin123',
        'full_name': 'Администратор Системы',
        'is_active': True
    },
    {
        'email': 'viewer@university.ru',
        'password': 'viewer123',
        'full_name': 'Наблюдатель',
        'is_active': True
    },
]
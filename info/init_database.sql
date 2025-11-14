CREATE DATABASE IF NOT EXISTS university_rooms;
USE university_rooms;

-- Таблица для иерархической структуры подразделений
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT NULL,
    type ENUM('faculty', 'department', 'laboratory') NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Таблица корпусов
CREATE TABLE buildings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Таблица помещений
CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id INT NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    location_description TEXT,
    width DECIMAL(8,2) NOT NULL,
    length DECIMAL(8,2) NOT NULL,
    ceiling_height DECIMAL(5,2) NOT NULL DEFAULT 3.0,
    purpose VARCHAR(255),
    room_type ENUM('lecture', 'laboratory', 'office', 'storage', 'other') NOT NULL,
    department_id INT NULL,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Вставка тестовых данных
INSERT INTO buildings (name) VALUES
('Главный корпус'),
('Корпус А'),
('Корпус Б');

INSERT INTO departments (name, parent_id, type) VALUES
('Факультет информатики', NULL, 'faculty'),
('Кафедра программирования', 1, 'department'),
('Кафедра сетевых технологий', 1, 'department'),
('Лаборатория искусственного интеллекта', 2, 'laboratory'),
('Факультет экономики', NULL, 'faculty'),
('Кафедра финансов', 5, 'department');

INSERT INTO rooms (building_id, room_number, location_description, width, length, ceiling_height, purpose, room_type, department_id) VALUES
(1, '101', 'Первый этаж, левое крыло', 8.0, 12.0, 3.2, 'Лекционная аудитория', 'lecture', 1),
(1, '102', 'Первый этаж, левое крыло', 6.0, 8.0, 3.0, 'Лаборатория программирования', 'laboratory', 2),
(1, '201', 'Второй этаж, правое крыло', 5.0, 7.0, 3.0, 'Кабинет профессора', 'office', 3),
(2, '301', 'Третий этаж, центр', 10.0, 15.0, 3.5, 'Большая лекционная', 'lecture', 5);
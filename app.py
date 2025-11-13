from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='slava2012',
            database='classroom-fund',
        )
        return connection
    except Error as e:
        print(f"Ошибка подключения к БД: {e}")
        return None


@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return render_template('index.html')

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                COUNT(DISTINCT b.id) as total_buildings,
                COUNT(r.id) as total_rooms,
                SUM(r.width * r.length) as total_area,
                SUM(r.width * r.length * r.ceiling_height) as total_volume
            FROM buildings b
            LEFT JOIN rooms r ON b.id = r.building_id
        """)
        stats = cursor.fetchone()

        cursor.execute("SELECT * FROM buildings ORDER BY name")
        buildings = cursor.fetchall()

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return render_template('index.html')
    finally:
        cursor.close()
        conn.close()

    return render_template('index.html', stats=stats, buildings=buildings)


@app.route('/rooms')
def rooms_list():
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT r.*, b.name as building_name, 
                   d.name as department_name,
                   (r.width * r.length) as area,
                   (r.width * r.length * r.ceiling_height) as volume
            FROM rooms r
            JOIN buildings b ON r.building_id = b.id
            LEFT JOIN departments d ON r.department_id = d.id
            ORDER BY b.name, r.room_number
        """)
        rooms = cursor.fetchall()

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()

    return render_template('rooms.html', rooms=rooms)


@app.route('/building/<int:building_id>')
def building_structure(building_id):
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM buildings WHERE id = %s", (building_id,))
        building = cursor.fetchone()

        if not building:
            flash('Корпус не найден', 'error')
            return redirect(url_for('index'))

        cursor.execute("""
            SELECT DISTINCT d.*, 
                   (SELECT COUNT(*) FROM rooms r2 WHERE r2.department_id = d.id AND r2.building_id = %s) as room_count
            FROM departments d
            JOIN rooms r ON r.department_id = d.id OR r.department_id IN (
                SELECT id FROM departments WHERE parent_id = d.id
            )
            WHERE r.building_id = %s AND d.type = 'faculty'
        """, (building_id, building_id))

        faculties = cursor.fetchall()

        faculty_structure = []
        for faculty in faculties:
            cursor.execute("""
                WITH RECURSIVE dept_tree AS (
                    SELECT id, name, parent_id, type, 0 as level
                    FROM departments 
                    WHERE id = %s
                    UNION ALL
                    SELECT d.id, d.name, d.parent_id, d.type, dt.level + 1
                    FROM departments d
                    JOIN dept_tree dt ON d.parent_id = dt.id
                )
                SELECT dt.*, 
                       (SELECT COUNT(*) FROM rooms r WHERE r.department_id = dt.id AND r.building_id = %s) as room_count
                FROM dept_tree dt
                ORDER BY level, name
            """, (faculty['id'], building_id))

            structure = cursor.fetchall()
            faculty_structure.append({
                'faculty': faculty,
                'structure': structure
            })

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()

    return render_template('building_structure.html',
                           building=building,
                           faculty_structure=faculty_structure)


@app.route('/buildings')
def buildings_management():
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM buildings ORDER BY name")
        buildings = cursor.fetchall()

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()

    return render_template('buildings.html', buildings=buildings)


@app.route('/building/add', methods=['GET', 'POST'])
def add_building():
    if request.method == 'POST':
        name = request.form['name']

        conn = get_db_connection()
        if conn is None:
            flash('Ошибка подключения к базе данных', 'error')
            return redirect(url_for('buildings_management'))

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO buildings (name) VALUES (%s)", (name,))
            conn.commit()
            flash('Корпус успешно добавлен', 'success')

        except Error as e:
            conn.rollback()
            flash(f'Ошибка добавления корпуса: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('buildings_management'))

    return render_template('add_building.html')


@app.route('/building/edit/<int:building_id>', methods=['GET', 'POST'])
def edit_building(building_id):
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('buildings_management'))

    if request.method == 'POST':
        name = request.form['name']

        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE buildings SET name = %s WHERE id = %s", (name, building_id))
            conn.commit()
            flash('Корпус успешно обновлен', 'success')

        except Error as e:
            conn.rollback()
            flash(f'Ошибка обновления корпуса: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('buildings_management'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM buildings WHERE id = %s", (building_id,))
        building = cursor.fetchone()

        if not building:
            flash('Корпус не найден', 'error')
            return redirect(url_for('buildings_management'))

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('buildings_management'))
    finally:
        cursor.close()
        conn.close()

    return render_template('edit_building.html', building=building)


@app.route('/building/delete/<int:building_id>')
def delete_building(building_id):
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('buildings_management'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM buildings WHERE id = %s", (building_id,))
        conn.commit()
        flash('Корпус успешно удален', 'success')

    except Error as e:
        conn.rollback()
        flash(f'Ошибка удаления корпуса: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('buildings_management'))


@app.route('/rooms/manage')
def rooms_management():
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT r.*, b.name as building_name, d.name as department_name
            FROM rooms r
            JOIN buildings b ON r.building_id = b.id
            LEFT JOIN departments d ON r.department_id = d.id
            ORDER BY b.name, r.room_number
        """)
        rooms = cursor.fetchall()

        cursor.execute("SELECT * FROM buildings ORDER BY name")
        buildings = cursor.fetchall()

        cursor.execute("SELECT * FROM departments ORDER BY name")
        departments = cursor.fetchall()

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()

    return render_template('rooms_management.html',
                           rooms=rooms,
                           buildings=buildings,
                           departments=departments)


@app.route('/room/add', methods=['GET', 'POST'])
def add_room():
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('rooms_management'))

    if request.method == 'POST':
        try:
            building_id = request.form['building_id']
            room_number = request.form['room_number']
            location_description = request.form['location_description']
            width = float(request.form['width'])
            length = float(request.form['length'])
            ceiling_height = float(request.form['ceiling_height'])
            purpose = request.form['purpose']
            room_type = request.form['room_type']
            department_id = request.form['department_id'] if request.form['department_id'] else None

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rooms 
                (building_id, room_number, location_description, width, length, 
                 ceiling_height, purpose, room_type, department_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (building_id, room_number, location_description, width, length,
                  ceiling_height, purpose, room_type, department_id))

            conn.commit()
            flash('Помещение успешно добавлено', 'success')

        except Error as e:
            conn.rollback()
            flash(f'Ошибка добавления помещения: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('rooms_management'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM buildings ORDER BY name")
        buildings = cursor.fetchall()

        cursor.execute("SELECT * FROM departments ORDER BY name")
        departments = cursor.fetchall()

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('rooms_management'))
    finally:
        cursor.close()
        conn.close()

    return render_template('add_room.html',
                           buildings=buildings,
                           departments=departments,
                           room_types=['lecture', 'laboratory', 'office', 'storage', 'other'])


@app.route('/room/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('rooms_management'))

    if request.method == 'POST':
        try:
            building_id = request.form['building_id']
            room_number = request.form['room_number']
            location_description = request.form['location_description']
            width = float(request.form['width'])
            length = float(request.form['length'])
            ceiling_height = float(request.form['ceiling_height'])
            purpose = request.form['purpose']
            room_type = request.form['room_type']
            department_id = request.form['department_id'] if request.form['department_id'] else None

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE rooms 
                SET building_id = %s, room_number = %s, location_description = %s, 
                    width = %s, length = %s, ceiling_height = %s, purpose = %s, 
                    room_type = %s, department_id = %s
                WHERE id = %s
            """, (building_id, room_number, location_description, width, length,
                  ceiling_height, purpose, room_type, department_id, room_id))

            conn.commit()
            flash('Помещение успешно обновлено', 'success')

        except Error as e:
            conn.rollback()
            flash(f'Ошибка обновления помещения: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('rooms_management'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()

        if not room:
            flash('Помещение не найдено', 'error')
            return redirect(url_for('rooms_management'))

        cursor.execute("SELECT * FROM buildings ORDER BY name")
        buildings = cursor.fetchall()

        cursor.execute("SELECT * FROM departments ORDER BY name")
        departments = cursor.fetchall()

    except Error as e:
        flash(f'Ошибка получения данных: {e}', 'error')
        return redirect(url_for('rooms_management'))
    finally:
        cursor.close()
        conn.close()

    return render_template('edit_room.html',
                           room=room,
                           buildings=buildings,
                           departments=departments,
                           room_types=['lecture', 'laboratory', 'office', 'storage', 'other'])


@app.route('/room/delete/<int:room_id>')
def delete_room(room_id):
    conn = get_db_connection()
    if conn is None:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('rooms_management'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
        conn.commit()
        flash('Помещение успешно удалено', 'success')

    except Error as e:
        conn.rollback()
        flash(f'Ошибка удаления помещения: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('rooms_management'))


if __name__ == '__main__':
    app.run(debug=True)
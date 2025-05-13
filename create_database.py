import sqlite3
import os
import json
from datetime import datetime

# Путь к базе данных
DB_PATH = "email_database.db"

def create_database():
    """Создает базу данных и необходимые таблицы"""

    print("Создание базы данных...")

    # Проверяем, существует ли уже база данных
    if os.path.exists(DB_PATH):
        user_input = input(f"База данных {DB_PATH} уже существует. Пересоздать? (y/n): ")
        if user_input.lower() != 'y':
            print("Операция отменена.")
            return False

    # Создаем соединение с базой данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

   # exit("Первый шаг создания базы данных")
    # Создаем таблицу для хранения писем
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT,
        subject TEXT,
        sender TEXT,
        date TEXT,
        date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        body TEXT,
        is_processed INTEGER DEFAULT 0
    )
    ''')

    # Создаем таблицу для хранения вложений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER,
        filename TEXT,
        content_type TEXT,
        data BLOB,
        FOREIGN KEY (email_id) REFERENCES emails (id)
    )
    ''')

    # Создаем таблицу для хранения категорий писем
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT
    )
    ''')

    # Создаем таблицу для связи писем и категорий (многие ко многим)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_categories (
        email_id INTEGER,
        category_id INTEGER,
        PRIMARY KEY (email_id, category_id),
        FOREIGN KEY (email_id) REFERENCES emails (id),
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')

    # Создаем индексы для ускорения поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_date ON emails (date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails (subject)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails (sender)')

    # Добавляем несколько стандартных категорий
    categories = [
        ('Важное', 'Важные письма, требующие внимания'),
        ('Работа', 'Рабочая корреспонденция'),
        ('Личное', 'Личные письма'),
        ('Спам', 'Нежелательная почта'),
        ('Новости', 'Новостные рассылки')
    ]

    cursor.executemany('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', categories)

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

    print(f"База данных {DB_PATH} успешно создана.")
    return True


def import_from_json(json_file):
    """Импортирует данные из JSON файла в базу данных"""

    if not os.path.exists(json_file):
        print(f"Файл {json_file} не найден.")
        return False

    if not os.path.exists(DB_PATH):
        print(f"База данных {DB_PATH} не найдена. Сначала создайте базу данных.")
        return False

    print(f"Импорт данных из {json_file}...")

    try:
        # Загружаем данные из JSON файла
        with open(json_file, 'r', encoding='utf-8') as f:
            emails_data = json.load(f)

        # Подключаемся к базе данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Счетчики для статистики
        added = 0
        skipped = 0

        # Обрабатываем каждое письмо
        for email_info in emails_data:
            # Проверяем, существует ли уже письмо с таким email_id
            cursor.execute('SELECT id FROM emails WHERE email_id = ?', (email_info['id'],))
            existing = cursor.fetchone()

            if existing:
                skipped += 1
                continue

            # Добавляем новое письмо
            cursor.execute('''
            INSERT INTO emails (email_id, subject, sender, date, body)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                email_info['id'],
                email_info['subject'],
                email_info['from'],
                email_info['date'],
                email_info['body']
            ))

            added += 1

        # Сохраняем изменения
        conn.commit()
        conn.close()

        print(f"Импорт завершен. Добавлено: {added}, пропущено: {skipped}")
        return True

    except Exception as e:
        print(f"Ошибка при импорте данных: {str(e)}")
        return False

def show_database_stats():
    """Показывает статистику базы данных"""

    if not os.path.exists(DB_PATH):
        print(f"База данных {DB_PATH} не найдена.")
        return

    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Получаем общее количество писем
        cursor.execute('SELECT COUNT(*) FROM emails')
        total_emails = cursor.fetchone()[0]

        # Получаем количество писем по отправителям
        cursor.execute('''
        SELECT sender, COUNT(*) as count
        FROM emails
        GROUP BY sender
        ORDER BY count DESC
        LIMIT 5
        ''')
        top_senders = cursor.fetchall()

        # Получаем количество писем по датам
        cursor.execute('''
        SELECT substr(date, 1, 10) as day, COUNT(*) as count
        FROM emails
        GROUP BY day
        ORDER BY day DESC
        LIMIT 5
        ''')
        emails_by_date = cursor.fetchall()

        # Получаем количество категорий
        cursor.execute('SELECT COUNT(*) FROM categories')
        total_categories = cursor.fetchone()[0]

        # Закрываем соединение
        conn.close()

        # Выводим статистику
        print("\n=== Статистика базы данных ===")
        print(f"Всего писем: {total_emails}")
        print(f"Всего категорий: {total_categories}")

        print("\nТоп отправителей:")
        for sender, count in top_senders:
            print(f"  - {sender}: {count} писем")

        print("\nПисьма по датам:")
        for date, count in emails_by_date:
            print(f"  - {date}: {count} писем")

    except Exception as e:
        print(f"Ошибка при получении статистики: {str(e)}")

if __name__ == "__main__":
    print("=== Создание базы данных для проекта обработки электронной почты ===\n")

    # Создаем базу данных
    if create_database():
        # Спрашиваем пользователя, хочет ли он импортировать данные из JSON
        import_choice = input("\nХотите импортировать данные из JSON файла? (y/n): ")
        if import_choice.lower() == 'y':
            json_file = input("Введите путь к JSON файлу (по умолчанию emails_data.json): ") or "emails_data.json"
            import_from_json(json_file)

        # Показываем статистику базы данных
        show_database_stats()
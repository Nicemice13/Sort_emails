import sqlite3
import os
import json
from datetime import datetime

class EmailManager:
    """Класс для управления электронными письмами в базе данных SQLite"""
    
    def __init__(self, db_path="email_database.db"):
        """Инициализация менеджера писем"""
        self.db_path = db_path
        
        # Проверяем существование базы данных
        if not os.path.exists(db_path):
            print(f"База данных {db_path} не найдена. Используйте create_database.py для создания базы данных.")
    
    def connect(self):
        """Создает и возвращает соединение с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def search_emails(self, query=None, sender=None, date_from=None, date_to=None, category=None, limit=10):
        """
        Поиск писем по различным критериям
        
        Args:
            query (str): Поисковый запрос для поиска в теме и теле письма
            sender (str): Фильтр по отправителю
            date_from (str): Начальная дата в формате YYYY-MM-DD
            date_to (str): Конечная дата в формате YYYY-MM-DD
            category (str): Название категории
            limit (int): Максимальное количество результатов
            
        Returns:
            list: Список писем, соответствующих критериям поиска
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Строим SQL запрос
        sql = "SELECT e.id, e.email_id, e.subject, e.sender, e.date, e.body FROM emails e"
        params = []
        conditions = []
        
        # Добавляем условия поиска
        if query:
            conditions.append("(e.subject LIKE ? OR e.body LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        if sender:
            conditions.append("e.sender LIKE ?")
            params.append(f"%{sender}%")
        
        if date_from:
            conditions.append("e.date >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("e.date <= ?")
            params.append(date_to)
        
        if category:
            sql += " JOIN email_categories ec ON e.id = ec.email_id JOIN categories c ON ec.category_id = c.id"
            conditions.append("c.name = ?")
            params.append(category)
        
        # Собираем условия в WHERE клаузу
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        # Добавляем сортировку и лимит
        sql += " ORDER BY e.date DESC LIMIT ?"
        params.append(limit)
        
        # Выполняем запрос
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # Преобразуем результаты в список словарей
        emails = []
        for row in results:
            emails.append({
                "id": row[0],
                "email_id": row[1],
                "subject": row[2],
                "sender": row[3],
                "date": row[4],
                "body": row[5][:200] + "..." if len(row[5]) > 200 else row[5]  # Ограничиваем длину тела
            })
        
        conn.close()
        return emails
    
    def get_email_by_id(self, email_id):
        """
        Получает полную информацию о письме по его ID
        
        Args:
            email_id (int): ID письма в базе данных
            
        Returns:
            dict: Информация о письме или None, если письмо не найдено
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Получаем информацию о письме
        cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
        email_data = cursor.fetchone()
        
        if not email_data:
            conn.close()
            return None
        
        # Получаем категории письма
        cursor.execute("""
            SELECT c.name FROM categories c
            JOIN email_categories ec ON c.id = ec.category_id
            WHERE ec.email_id = ?
        """, (email_id,))
        categories = [row[0] for row in cursor.fetchall()]
        
        # Получаем вложения письма
        cursor.execute("SELECT id, filename, content_type FROM attachments WHERE email_id = ?", (email_id,))
        attachments = [{"id": row[0], "filename": row[1], "content_type": row[2]} for row in cursor.fetchall()]
        
        # Формируем результат
        result = {
            "id": email_data[0],
            "email_id": email_data[1],
            "subject": email_data[2],
            "sender": email_data[3],
            "date": email_data[4],
            "date_received": email_data[5],
            "body": email_data[6],
            "is_processed": bool(email_data[7]),
            "categories": categories,
            "attachments": attachments
        }
        
        conn.close()
        return result
    
    def add_email_to_category(self, email_id, category_name):
        """
        Добавляет письмо в указанную категорию
        
        Args:
            email_id (int): ID письма
            category_name (str): Название категории
            
        Returns:
            bool: True если операция выполнена успешно, иначе False
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Проверяем существование категории
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            category = cursor.fetchone()
            
            if not category:
                # Создаем новую категорию
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                category_id = cursor.lastrowid
            else:
                category_id = category[0]
            
            # Добавляем связь между письмом и категорией
            cursor.execute("""
                INSERT OR IGNORE INTO email_categories (email_id, category_id)
                VALUES (?, ?)
            """, (email_id, category_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка при добавлении письма в категорию: {str(e)}")
            conn.rollback()
            conn.close()
            return False
    
    def remove_email_from_category(self, email_id, category_name):
        """
        Удаляет письмо из указанной категории
        
        Args:
            email_id (int): ID письма
            category_name (str): Название категории
            
        Returns:
            bool: True если операция выполнена успешно, иначе False
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Получаем ID категории
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            category = cursor.fetchone()
            
            if not category:
                conn.close()
                return False
            
            # Удаляем связь между письмом и категорией
            cursor.execute("""
                DELETE FROM email_categories 
                WHERE email_id = ? AND category_id = ?
            """, (email_id, category[0]))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка при удалении письма из категории: {str(e)}")
            conn.rollback()
            conn.close()
            return False
    
    def mark_as_processed(self, email_id, processed=True):
        """
        Отмечает письмо как обработанное или необработанное
        
        Args:
            email_id (int): ID письма
            processed (bool): Статус обработки
            
        Returns:
            bool: True если операция выполнена успешно, иначе False
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE emails SET is_processed = ?
                WHERE id = ?
            """, (1 if processed else 0, email_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка при изменении статуса письма: {str(e)}")
            conn.rollback()
            conn.close()
            return False
    
    def get_categories(self):
        """
        Получает список всех категорий
        
        Returns:
            list: Список категорий
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, description FROM categories ORDER BY name")
        categories = [{"id": row[0], "name": row[1], "description": row[2]} for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def get_statistics(self):
        """
        Получает статистику по письмам
        
        Returns:
            dict: Статистика по письмам
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Общее количество писем
        cursor.execute("SELECT COUNT(*) FROM emails")
        total_emails = cursor.fetchone()[0]
        
        # Количество обработанных писем
        cursor.execute("SELECT COUNT(*) FROM emails WHERE is_processed = 1")
        processed_emails = cursor.fetchone()[0]
        
        # Количество писем по категориям
        cursor.execute("""
            SELECT c.name, COUNT(ec.email_id) as count
            FROM categories c
            LEFT JOIN email_categories ec ON c.id = ec.category_id
            GROUP BY c.id
            ORDER BY count DESC
        """)
        categories_stats = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Количество писем по отправителям
        cursor.execute("""
            SELECT sender, COUNT(*) as count
            FROM emails
            GROUP BY sender
            ORDER BY count DESC
            LIMIT 5
        """)
        senders_stats = [{"sender": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_emails": total_emails,
            "processed_emails": processed_emails,
            "unprocessed_emails": total_emails - processed_emails,
            "categories": categories_stats,
            "top_senders": senders_stats
        }

# Пример использования
if __name__ == "__main__":
    manager = EmailManager()
    
    print("=== Менеджер электронной почты ===\n")
    
    # Проверяем существование базы данных
    if not os.path.exists(manager.db_path):
        print(f"База данных {manager.db_path} не найдена.")
        print("Запустите create_database.py для создания базы данных.")
        exit()
    
    # Выводим статистику
    stats = manager.get_statistics()
    print(f"Всего писем: {stats['total_emails']}")
    print(f"Обработано: {stats['processed_emails']}")
    print(f"Не обработано: {stats['unprocessed_emails']}")
    
    print("\nКатегории:")
    for category in stats['categories']:
        print(f"  - {category['name']}: {category['count']} писем")
    
    print("\nТоп отправителей:")
    for sender in stats['top_senders']:
        print(f"  - {sender['sender']}: {sender['count']} писем")
    
    # Пример поиска писем
    print("\nПоследние 5 писем:")
    emails = manager.search_emails(limit=5)
    for email in emails:
        print(f"  - {email['date']} | {email['sender']} | {email['subject']}")
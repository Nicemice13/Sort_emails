import imaplib
import email
import base64
import os
import json
from email.header import decode_header
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

mail_server = "imap.mail.ru"
mail_port = 993

email_address = os.getenv("EMAIL_RU")
app_password = os.getenv("PASSWORD_RU")

def decode_str(s):
    """Декодирует строку email-заголовка"""
    if s is None:
        return ""
    decoded_parts = decode_header(s)
    result = ""
    for data, charset in decoded_parts:
        if isinstance(data, bytes):
            if charset:
                result += data.decode(charset, errors='replace')
            else:
                result += data.decode('utf-8', errors='replace')
        else:
            result += data
    return result

def get_email_body(msg):
    """Извлекает тело письма"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Пропускаем вложения
            if "attachment" in content_disposition:
                continue
                
            # Ищем текстовые части
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break  # Берем первую текстовую часть
                except Exception as e:
                    print(f"Ошибка при декодировании тела: {e}")
                    try:
                        # Пробуем декодировать base64 если обычное декодирование не сработало
                        body = base64.b64decode(part.get_payload()).decode('utf-8', errors='replace')
                    except:
                        continue
    else:
        # Если письмо не мультичастное
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
        except Exception as e:
            print(f"Ошибка при декодировании тела: {e}")
            try:
                # Пробуем декодировать base64
                body = base64.b64decode(msg.get_payload()).decode('utf-8', errors='replace')
            except:
                pass
    
    return body

def format_date(date_tuple):
    """Форматирует дату из формата parsedate_tz в читаемый формат"""
    if not date_tuple:
        return "Неизвестная дата"
    
    try:
        # Преобразуем tuple в datetime
        year, month, day, hour, minute, second = date_tuple[:6]
        return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    except:
        return str(date_tuple)

def save_emails_to_json(max_emails=10, output_file="emails_data.json"):
    """
    Получает письма из почтового ящика и сохраняет их в JSON файл
    
    Args:
        max_emails (int): Максимальное количество писем для обработки
        output_file (str): Имя файла для сохранения результатов
    """
    try:
        print("Подключение к почтовому серверу...")
        mail = imaplib.IMAP4_SSL(mail_server, mail_port)
        
        print(f"Вход в аккаунт {email_address}...")
        mail.login(email_address, app_password)
        print("Вход выполнен успешно")
        
        print("Выбор папки 'Входящие'...")
        mail.select("INBOX")
        
        print("Поиск писем...")
        result, data = mail.search(None, "ALL")
        
        if result != "OK":
            print("Ошибка при поиске писем")
            return False
        
        email_ids = data[0].split()
        total_emails = len(email_ids)
        print(f"Найдено {total_emails} писем")
        
        # Создаем список для хранения информации о письмах
        all_emails = []
        
        # Обрабатываем письма (в обратном порядке - от новых к старым)
        for i, email_id in enumerate(email_ids[::-1]):
            if i >= max_emails:  # Ограничиваем количество обрабатываемых писем
                break
                
            print(f"Обработка письма {i+1} из {min(max_emails, total_emails)}...")
            
            # Получаем письмо по ID
            result, data = mail.fetch(email_id, "(RFC822)")
            
            if result != "OK":
                print(f"Ошибка при получении письма {email_id}")
                continue
                
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Извлекаем информацию о письме
            try:
                subject = decode_str(email_message["Subject"])
            except:
                subject = "Без темы"
                
            try:
                from_addr = decode_str(email_message["From"])
            except:
                from_addr = "Неизвестный отправитель"
                
            # Обработка даты
            date_tuple = email.utils.parsedate_tz(email_message["Date"])
            date_formatted = format_date(date_tuple)
            
            # Получаем тело письма
            body = get_email_body(email_message)
            
            # Создаем словарь с информацией о письме
            email_info = {
                "id": email_id.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date_formatted,
                "body": body
            }
            
            # Добавляем информацию о письме в общий список
            all_emails.append(email_info)
            
            print(f"Письмо обработано: {subject}")
        
        # Сохраняем результаты в JSON файл
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_emails, f, ensure_ascii=False, indent=2)
        
        print(f"\nДанные {len(all_emails)} писем сохранены в файл {output_file}")
        return True

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return False

    finally:
        # Закрытие соединения
        try:
            mail.close()
            mail.logout()
            print("Соединение с почтовым сервером закрыто")
        except:
            pass

if __name__ == "__main__":
    # Запрашиваем у пользователя количество писем для обработки
    try:
        max_emails = int(input("Введите количество писем для обработки (по умолчанию 10): ") or "10")
    except:
        max_emails = 10
        print("Некорректный ввод, будет использовано значение по умолчанию: 10")
    
    # Запрашиваем имя файла для сохранения
    output_file = input("Введите имя файла для сохранения (по умолчанию emails_data.json): ") or "emails_data.json"
    
    # Получаем и сохраняем письма
    success = save_emails_to_json(max_emails, output_file)
    
    if success:
        print("Программа успешно завершена")
    else:
        print("Программа завершена с ошибками")
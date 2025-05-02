import imaplib
import email
import base64
import os
import json
from email.header import decode_header
from datetime import datetime

from dotenv import load_dotenv, dotenv_values

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
    if msg.is_multipart():
        # Если письмо состоит из нескольких частей, ищем текстовую часть
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Пропускаем вложения
            if "attachment" in content_disposition:
                continue

            # Ищем текстовые части
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                    return body, content_type
                except:
                    return "[Не удалось декодировать тело письма]", content_type
    else:
        # Если письмо не мультичастное
        try:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
            return body, msg.get_content_type()
        except:
            return "[Не удалось декодировать тело письма]", msg.get_content_type()

    return "[Тело письма не найдено]", "text/plain"

def get_all_emails():
    """Получает все письма из почтового ящика"""
    try:
        # Подключаемся к почтовому серверу
        mail = imaplib.IMAP4_SSL(mail_server, mail_port)
        mail.login(email_address, app_password)

        # Выбираем папку "Входящие"
        mail.select("INBOX")

        # Ищем все письма
        status, messages = mail.search(None, "ALL")

        if status != "OK":
            print("Ошибка при поиске писем")
            return []

        email_ids = messages[0].split()
        print(f"Найдено {len(email_ids)} писем")

        all_emails = []

        # Обрабатываем каждое письмо
        for e_id in email_ids:
            # Получаем письмо по ID
            status, msg_data = mail.fetch(e_id, "(RFC822)")

            if status != "OK":
                print(f"Ошибка при получении письма {e_id}")
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Извлекаем информацию о письме
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            date_str = msg["Date"]

            # Преобразуем дату в более читаемый формат
            try:
                date_obj = email.utils.parsedate_to_datetime(date_str)
                date_formatted = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_formatted = date_str

            # Получаем тело письма
            body, content_type = get_email_body(msg)

            # Создаем структуру для хранения информации о письме
            email_info = {
                "id": e_id.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date_formatted,
                "content_type": content_type,
                "body": body[:500] + "..." if len(body) > 500 else body  # Ограничиваем длину для вывода
            }

            all_emails.append(email_info)
            print(f"Обработано письмо: {subject}")

        # Закрываем соединение
        mail.close()
        mail.logout()

        return all_emails

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return []

# Получаем все письма
emails = get_all_emails()

# Выводим информацию о письмах
for i, email_info in enumerate(emails):
    print(f"\n--- Письмо {i+1} ---")
    print(f"От: {email_info['from']}")
    print(f"Тема: {email_info['subject']}")
    print(f"Дата: {email_info['date']}")
    print(f"Тип содержимого: {email_info['content_type']}")
    print(f"Начало текста: {email_info['body'][:100]}...")

# Сохраняем результаты в JSON файл для дальнейшего анализа
with open("emails_data.json", "w", encoding="utf-8") as f:
    json.dump(emails, f, ensure_ascii=False, indent=2)

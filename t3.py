import imaplib, email, base64, os, json

from dotenv import load_dotenv, dotenv_values

load_dotenv()


mail_server = "imap.mail.ru"
mail_port = 993


email_address = os.getenv("EMAIL_RU")
app_password = os.getenv("PASSWORD_RU")


mail = imaplib.IMAP4_SSL(mail_server, mail_port)

try:
    mail.login(email_address, app_password)
    mail.select("INBOX")

    result, data = mail.search(None, "ALL")

    email_ids = data[0].split()


    for email_id in email_ids[::-1]:
        result, data = mail.fetch(email_id, "(RFC822)")

        # Парсинг письма

        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        msg_info = {
            "Subject":email.header.decode_header(email_message['Subject'])[0][0].decode(),
            "From": email_message["From"],
            "Date": email.utils.parsedate_tz(email_message["Date"]),
            "Body": [],
        }

        print(1, msg_info)
        # Вывод основной информации
        # print(
        #     f"Тема: {email.header.decode_header(email_message['Subject'])[0][0].decode()}"
        # )
        # print(f"От: {email_message['From']}")
        # print(f"Дата: {email.utils.parsedate_tz(email_message['Date'])}")

        # Извлечение текста письма
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                print("\nТекст письма:")
                print(base64.b64decode(part.get_payload()).decode())
            # break
        print("\n---\n")
        break

except Exception as e:
    print(f"Ошибка: {e}")

"""
finally:
    # Закрытие соединения
    mail.close()
    mail.logout()
"""
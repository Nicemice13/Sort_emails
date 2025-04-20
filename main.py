import imaplib, email, base64, os, json

from dotenv import load_dotenv, dotenv_values

load_dotenv()


mail_server = "imap.mail.ru"
mail_port = 993


email_address = os.getenv("EMAIL_RU")
app_password = os.getenv("PASSWORD_RU")


mail = imaplib.IMAP4_SSL(mail_server, mail_port)
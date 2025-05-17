from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, String
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

# Создай подключение к базе данных
from sqlalchemy import create_engine
engine = create_engine('sqlite:///email_database.db')

class Base(DeclarativeBase): pass

# Создай модель для моей базы данных
class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String)
    subject = Column(String)
    sender = Column(String)
    date = Column(String)
    body = Column(String)


# Создаем экземпляр приложения
app = FastAPI()

# создай подключение к БД
Base.metadata.create_all(bind=engine)

# создай сессию
session = Session(bind=engine)

all_emails = session.query(Email).all()
print(all_emails)

for email in all_emails:
    print(email.subject)

templates = Jinja2Templates(directory="templates")
# Создаем маршрут для корневого пути
@app.get("/")
async def read_root(request: Request):
    # получить все письма из базы данных
    #all_emails = EmailManager().get_all_emails()

    # выведи все письма в файл index.html
    return templates.TemplateResponse(
        "index1.html", {"request": request, "title": "Главная страница", "emails": all_emails}
    )

@app.get("/email/{email_id}")
async def read_email(request: Request, email_id: int):
    # Создаем сессию
    session = Session(bind=engine)

    try:
        # Получаем письмо по ID
        email = session.query(Email).filter(Email.id == email_id).first()

        if not email:
            # Если письмо не найдено, перенаправляем на главную страницу
            return RedirectResponse(url="/")

        # Отображаем страницу с деталями письма
        return templates.TemplateResponse(
            "detail.html", {"request": request, "email": email}
        )
    finally:
        # Закрываем сессию
        session.close()

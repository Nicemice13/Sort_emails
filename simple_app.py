from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
import uvicorn
import os

# Создаем FastAPI приложение
app = FastAPI(title="Simple FastAPI App")

# Создаем директорию для шаблонов, если её нет
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

# Создаем директорию для статических файлов, если её нет
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Создаем файл стилей
css_dir = os.path.join(static_dir, "css")
os.makedirs(css_dir, exist_ok=True)
with open(os.path.join(css_dir, "style.css"), "w") as f:
    f.write("""
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}
.header {
    background-color: #4285f4;
    color: white;
    padding: 10px 20px;
    margin-bottom: 20px;
    text-align: center;
}
.card {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
}
.form-group {
    margin-bottom: 15px;
}
.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}
.form-group input, .form-group textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
}
.btn {
    padding: 10px 15px;
    background-color: #4285f4;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
.btn:hover {
    background-color: #3367d6;
}
.item {
    border-bottom: 1px solid #eee;
    padding: 10px 0;
}
.item-title {
    font-weight: bold;
    font-size: 18px;
}
.item-description {
    color: #666;
    margin-top: 5px;
}
.nav {
    background-color: #333;
    overflow: hidden;
}
.nav a {
    float: left;
    display: block;
    color: white;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
}
.nav a:hover {
    background-color: #ddd;
    color: black;
}
.nav a.active {
    background-color: #4285f4;
}
    """)

# Создаем базовый шаблон
with open(os.path.join(templates_dir, "base.html"), "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Simple FastAPI App{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="nav">
        <a href="/" class="{{ 'active' if request.url.path == '/' else '' }}">Главная</a>
        <a href="/items" class="{{ 'active' if request.url.path == '/items' else '' }}">Элементы</a>
        <a href="/about" class="{{ 'active' if request.url.path == '/about' else '' }}">О приложении</a>
    </div>
    
    <div class="container">
        <div class="header">
            <h1>{% block header %}Simple FastAPI App{% endblock %}</h1>
        </div>
        
        <div class="content">
            {% block content %}{% endblock %}
        </div>
    </div>
</body>
</html>
    """)

# Создаем шаблон для главной страницы
with open(os.path.join(templates_dir, "index.html"), "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Simple FastAPI App - Главная{% endblock %}

{% block header %}Добро пожаловать в Simple FastAPI App{% endblock %}

{% block content %}
<div class="card">
    <h2>О приложении</h2>
    <p>Это простое приложение на FastAPI с базовыми функциями.</p>
    <p>Используйте навигационное меню для доступа к различным функциям:</p>
    <ul>
        <li><strong>Главная</strong> - эта страница</li>
        <li><strong>Элементы</strong> - список элементов и форма для добавления новых</li>
        <li><strong>О приложении</strong> - информация о приложении</li>
    </ul>
</div>

<div class="card">
    <h2>Статистика</h2>
    <p>Всего элементов: <strong>{{ item_count }}</strong></p>
</div>
{% endblock %}
    """)

# Создаем шаблон для страницы элементов
with open(os.path.join(templates_dir, "items.html"), "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Simple FastAPI App - Элементы{% endblock %}

{% block header %}Элементы{% endblock %}

{% block content %}
<div class="card">
    <h2>Добавить новый элемент</h2>
    <form action="/items" method="post">
        <div class="form-group">
            <label for="title">Название:</label>
            <input type="text" id="title" name="title" required>
        </div>
        <div class="form-group">
            <label for="description">Описание:</label>
            <textarea id="description" name="description" rows="3"></textarea>
        </div>
        <button type="submit" class="btn">Добавить</button>
    </form>
</div>

<div class="card">
    <h2>Список элементов</h2>
    {% for item in items %}
    <div class="item">
        <div class="item-title">{{ item.title }}</div>
        <div class="item-description">{{ item.description }}</div>
    </div>
    {% else %}
    <p>Элементов пока нет.</p>
    {% endfor %}
</div>
{% endblock %}
    """)

# Создаем шаблон для страницы "О приложении"
with open(os.path.join(templates_dir, "about.html"), "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Simple FastAPI App - О приложении{% endblock %}

{% block header %}О приложении{% endblock %}

{% block content %}
<div class="card">
    <h2>Simple FastAPI App</h2>
    <p>Это простое приложение, созданное с использованием FastAPI.</p>
    <p>Технологии:</p>
    <ul>
        <li>FastAPI - современный веб-фреймворк для Python</li>
        <li>Jinja2 - шаблонизатор для HTML</li>
        <li>Pydantic - библиотека для валидации данных</li>
        <li>Uvicorn - ASGI сервер</li>
    </ul>
    <p>Версия: 1.0.0</p>
</div>
{% endblock %}
    """)

# Настраиваем шаблоны и статические файлы
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Модель данных для элемента
class Item(BaseModel):
    title: str
    description: Optional[str] = None

# Хранилище элементов (в памяти)
items = []

# Маршрут для главной страницы
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "item_count": len(items)}
    )

# Маршрут для страницы элементов (GET)
@app.get("/items", response_class=HTMLResponse)
async def read_items(request: Request):
    return templates.TemplateResponse(
        "items.html", 
        {"request": request, "items": items}
    )

# Маршрут для страницы элементов (POST)
@app.post("/items", response_class=HTMLResponse)
async def create_item(request: Request, title: str = Form(...), description: str = Form("")):
    item = Item(title=title, description=description)
    items.append(item)
    return templates.TemplateResponse(
        "items.html", 
        {"request": request, "items": items}
    )

# Маршрут для страницы "О приложении"
@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse(
        "about.html", 
        {"request": request}
    )

# API маршрут для получения элементов в формате JSON
@app.get("/api/items", response_model=List[Item])
async def api_items():
    return items

# API маршрут для добавления элемента
@app.post("/api/items", response_model=Item)
async def api_create_item(item: Item):
    items.append(item)
    return item

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
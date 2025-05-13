from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sqlite3
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

# Создаем FastAPI приложение
app = FastAPI(title="Email Manager")

# Путь к базе данных
DB_PATH = "email_database.db"

# Проверяем существование базы данных
if not os.path.exists(DB_PATH):
    raise Exception(f"База данных {DB_PATH} не найдена. Запустите create_database.py для создания базы данных.")

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
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}
.header {
    background-color: #4285f4;
    color: white;
    padding: 10px 20px;
    margin-bottom: 20px;
}
.card {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
}
.email-list {
    list-style-type: none;
    padding: 0;
}
.email-item {
    border-bottom: 1px solid #eee;
    padding: 10px 0;
}
.email-subject {
    font-weight: bold;
}
.email-sender {
    color: #666;
}
.email-date {
    color: #999;
    font-size: 0.9em;
}
.email-body {
    margin-top: 10px;
    white-space: pre-wrap;
}
.badge {
    display: inline-block;
    background-color: #e0e0e0;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 0.8em;
    margin-right: 5px;
}
.pagination {
    display: flex;
    justify-content: center;
    margin-top: 20px;
}
.pagination a {
    color: #4285f4;
    padding: 8px 16px;
    text-decoration: none;
}
.pagination a.active {
    background-color: #4285f4;
    color: white;
    border-radius: 5px;
}
.search-form {
    margin-bottom: 20px;
}
.search-input {
    padding: 8px;
    width: 300px;
    border: 1px solid #ddd;
    border-radius: 4px;
}
.search-button {
    padding: 8px 16px;
    background-color: #4285f4;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
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
    <title>{% block title %}Email Manager{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="nav">
        <a href="/" class="{{ 'active' if request.url.path == '/' else '' }}">Главная</a>
        <a href="/emails" class="{{ 'active' if request.url.path == '/emails' else '' }}">Письма</a>
        <a href="/categories" class="{{ 'active' if request.url.path == '/categories' else '' }}">Категории</a>
        <a href="/stats" class="{{ 'active' if request.url.path == '/stats' else '' }}">Статистика</a>
    </div>
    
    <div class="container">
        <div class="header">
            <h1>{% block header %}Email Manager{% endblock %}</h1>
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

{% block title %}Email Manager - Главная{% endblock %}

{% block header %}Добро пожаловать в Email Manager{% endblock %}

{% block content %}
<div class="card">
    <h2>О проекте</h2>
    <p>Этот проект предназначен для управления электронными письмами из почтового ящика mail.ru.</p>
    <p>Используйте навигационное меню для доступа к различным функциям:</p>
    <ul>
        <li><strong>Письма</strong> - просмотр и поиск писем</li>
        <li><strong>Категории</strong> - управление категориями писем</li>
        <li><strong>Статистика</strong> - статистика по письмам</li>
    </ul>
</div>

<div class="card">
    <h2>Статистика</h2>
    <p>Всего писем: <strong>{{ stats.total_emails }}</strong></p>
    <p>Обработано: <strong>{{ stats.processed_emails }}</strong></p>
    <p>Не обработано: <strong>{{ stats.unprocessed_emails }}</strong></p>
    
    <h3>Топ отправителей:</h3>
    <ul>
        {% for sender in stats.top_senders %}
        <li>{{ sender.sender }} ({{ sender.count }} писем)</li>
        {% endfor %}
    </ul>
</div>
{% endblock %}
    """)

# Создаем шаблон для страницы писем
with open(os.path.join(templates_dir, "emails.html"), "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Email Manager - Письма{% endblock %}

{% block header %}Письма{% endblock %}

{% block content %}
<div class="card">
    <form class="search-form" action="/emails" method="get">
        <input type="text" name="query" placeholder="Поиск по теме или отправителю" class="search-input" value="{{ query }}">
        <button type="submit" class="search-button">Поиск</button>
    </form>
    
    <div class="email-list">
        {% for email in emails %}
        <div class="email-item">
            <div class="email-subject">{{ email.subject }}</div>
            <div class="email-sender">От: {{ email.sender }}</div>
            <div class="email-date">Дата: {{ email.date }}</div>
            <div class="email-body">{{ email.body[:200] }}{% if email.body|length > 200 %}...{% endif %}</div>
            {% if email.categories %}
            <div class="email-categories">
                {% for category in email.categories %}
                <span class="badge">{{ category }}</span>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% else %}
        <p>Писем не найдено.</p>
        {% endfor %}
    </div>
    
    <div class="pagination">
        {% if page > 1 %}
        <a href="/emails?page={{ page - 1 }}&query={{ query }}">&laquo; Предыдущая</a>
        {% endif %}
        
        {% for p in range(1, total_pages + 1) %}
        <a href="/emails?page={{ p }}&query={{ query }}" class="{{ 'active' if p == page else '' }}">{{ p }}</a>
        {% endfor %}
        
        {% if page < total_pages %}
        <a href="/emails?page={{ page + 1 }}&query={{ query }}">Следующая &raquo;</a>
        {% endif %}
    </div>
</div>
{% endblock %}
    """)

# Создаем шаблон для страницы категорий
with open(os.path.join(templates_dir, "categories.html"), "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Email Manager - Категории{% endblock %}

{% block header %}Категории{% endblock %}

{% block content %}
<div class="card">
    <ul>
        {% for category in categories %}
        <li>
            <strong>{{ category.name }}</strong>
            {% if category.description %}
            <p>{{ category.description }}</p>
            {% endif %}
            <p>Писем в категории: {{ category.count }}</p>
        </li>
        {% else %}
        <p>Категорий не найдено.</p>
        {% endfor %}
    </ul>
</div>
{% endblock %}
    """)

# Создаем шаблон для страницы статистики
with open(os.path.join(templates_dir, "stats.html"), "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Email Manager - Статистика{% endblock %}

{% block header %}Статистика{% endblock %}

{% block content %}
<div class="card">
    <h2>Общая статистика</h2>
    <p>Всего писем: <strong>{{ stats.total_emails }}</strong></p>
    <p>Обработано: <strong>{{ stats.processed_emails }}</strong></p>
    <p>Не обработано: <strong>{{ stats.unprocessed_emails }}</strong></p>
    
    <h2>Статистика по категориям</h2>
    <ul>
        {% for category in stats.categories %}
        <li>{{ category.name }}: {{ category.count }} писем</li>
        {% endfor %}
    </ul>
    
    <h2>Топ отправителей</h2>
    <ul>
        {% for sender in stats.top_senders %}
        <li>{{ sender.sender }}: {{ sender.count }} писем</li>
        {% endfor %}
    </ul>
</div>
{% endblock %}
    """)

# Настраиваем шаблоны и статические файлы
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Функция для получения статистики
def get_statistics():
    conn = get_db_connection()
    
    # Общее количество писем
    total_emails = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
    
    # Количество обработанных писем
    processed_emails = conn.execute("SELECT COUNT(*) FROM emails WHERE is_processed = 1").fetchone()[0]
    
    # Количество писем по категориям
    categories_stats = conn.execute("""
        SELECT c.name, COUNT(ec.email_id) as count
        FROM categories c
        LEFT JOIN email_categories ec ON c.id = ec.category_id
        GROUP BY c.id
        ORDER BY count DESC
    """).fetchall()
    
    # Количество писем по отправителям
    senders_stats = conn.execute("""
        SELECT sender, COUNT(*) as count
        FROM emails
        GROUP BY sender
        ORDER BY count DESC
        LIMIT 5
    """).fetchall()
    
    conn.close()
    
    return {
        "total_emails": total_emails,
        "processed_emails": processed_emails,
        "unprocessed_emails": total_emails - processed_emails,
        "categories": [{"name": row["name"], "count": row["count"]} for row in categories_stats],
        "top_senders": [{"sender": row["sender"], "count": row["count"]} for row in senders_stats]
    }

# Маршрут для главной страницы
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    stats = get_statistics()
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})

# Маршрут для страницы писем
@app.get("/emails", response_class=HTMLResponse)
async def read_emails(request: Request, page: int = 1, query: str = ""):
    conn = get_db_connection()
    
    # Количество писем на странице
    per_page = 10
    
    # Строим SQL запрос
    sql = "SELECT e.id, e.subject, e.sender, e.date, e.body FROM emails e"
    params = []
    
    # Добавляем условие поиска, если есть запрос
    if query:
        sql += " WHERE e.subject LIKE ? OR e.sender LIKE ?"
        params.extend([f"%{query}%", f"%{query}%"])
    
    # Добавляем сортировку и пагинацию
    sql += " ORDER BY e.date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    # Выполняем запрос
    emails_data = conn.execute(sql, params).fetchall()
    
    # Получаем категории для каждого письма
    emails = []
    for email in emails_data:
        # Получаем категории письма
        categories = conn.execute("""
            SELECT c.name FROM categories c
            JOIN email_categories ec ON c.id = ec.category_id
            WHERE ec.email_id = ?
        """, (email["id"],)).fetchall()
        
        # Формируем данные о письме
        emails.append({
            "id": email["id"],
            "subject": email["subject"],
            "sender": email["sender"],
            "date": email["date"],
            "body": email["body"],
            "categories": [category["name"] for category in categories]
        })
    
    # Получаем общее количество писем для пагинации
    count_sql = "SELECT COUNT(*) FROM emails"
    count_params = []
    
    if query:
        count_sql += " WHERE subject LIKE ? OR sender LIKE ?"
        count_params.extend([f"%{query}%", f"%{query}%"])
    
    total_emails = conn.execute(count_sql, count_params).fetchone()[0]
    total_pages = (total_emails + per_page - 1) // per_page
    
    conn.close()
    
    return templates.TemplateResponse(
        "emails.html", 
        {
            "request": request, 
            "emails": emails, 
            "page": page, 
            "total_pages": total_pages,
            "query": query
        }
    )

# Маршрут для страницы категорий
@app.get("/categories", response_class=HTMLResponse)
async def read_categories(request: Request):
    conn = get_db_connection()
    
    # Получаем категории с количеством писем
    categories = conn.execute("""
        SELECT c.id, c.name, c.description, COUNT(ec.email_id) as count
        FROM categories c
        LEFT JOIN email_categories ec ON c.id = ec.category_id
        GROUP BY c.id
        ORDER BY c.name
    """).fetchall()
    
    conn.close()
    
    return templates.TemplateResponse(
        "categories.html", 
        {
            "request": request, 
            "categories": [
                {
                    "id": category["id"],
                    "name": category["name"],
                    "description": category["description"],
                    "count": category["count"]
                } 
                for category in categories
            ]
        }
    )

# Маршрут для страницы статистики
@app.get("/stats", response_class=HTMLResponse)
async def read_stats(request: Request):
    stats = get_statistics()
    return templates.TemplateResponse("stats.html", {"request": request, "stats": stats})

# API маршрут для получения писем в формате JSON
@app.get("/api/emails")
async def api_emails(page: int = 1, limit: int = 10, query: str = ""):
    conn = get_db_connection()
    
    # Строим SQL запрос
    sql = "SELECT e.id, e.subject, e.sender, e.date, e.body FROM emails e"
    params = []
    
    # Добавляем условие поиска, если есть запрос
    if query:
        sql += " WHERE e.subject LIKE ? OR e.sender LIKE ?"
        params.extend([f"%{query}%", f"%{query}%"])
    
    # Добавляем сортировку и пагинацию
    sql += " ORDER BY e.date DESC LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])
    
    # Выполняем запрос
    emails_data = conn.execute(sql, params).fetchall()
    
    # Получаем категории для каждого письма
    emails = []
    for email in emails_data:
        # Получаем категории письма
        categories = conn.execute("""
            SELECT c.name FROM categories c
            JOIN email_categories ec ON c.id = ec.category_id
            WHERE ec.email_id = ?
        """, (email["id"],)).fetchall()
        
        # Формируем данные о письме
        emails.append({
            "id": email["id"],
            "subject": email["subject"],
            "sender": email["sender"],
            "date": email["date"],
            "body": email["body"],
            "categories": [category["name"] for category in categories]
        })
    
    conn.close()
    
    return emails

# API маршрут для получения статистики в формате JSON
@app.get("/api/stats")
async def api_stats():
    return get_statistics()

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
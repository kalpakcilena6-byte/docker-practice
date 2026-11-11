import os

import psycopg
from fastapi import FastAPI

app = FastAPI()

# строка подключения к базе приходит из переменной окружения (флаг -e при docker run)
database_url = os.getenv("DATABASE_URL")

@app.get("/ping")
def ping():
    return { "message": "lala" }

@app.get("/hello/{name}")
def hello(name: str):
    return {"hello": name}


@app.get("/books")
def get_books():
    # подключаемся к Postgres, берём все книги и превращаем строки таблицы в список словарей
    with psycopg.connect(database_url) as conn:
        rows = conn.execute("select id, title, author from books order by id").fetchall()
    return [{"id": r[0], "title": r[1], "author": r[2]} for r in rows]

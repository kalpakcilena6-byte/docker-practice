import os
from datetime import datetime

import psycopg
from fastapi import FastAPI, HTTPException, Query
from psycopg.rows import dict_row
from pydantic import BaseModel

app = FastAPI(title="Library API")
DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class Book(BaseModel):
    id: int
    title: str
    author: str
    cover_path: str | None
    created_at: datetime


class BookPage(BaseModel):
    total: int
    items: list[Book]


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/db-check")
def db_check():
    with get_conn() as conn:
        version = conn.execute("select version() as v").fetchone()["v"]
        books = conn.execute("select count(*) as cnt from books").fetchone()["cnt"]
    return {"database": version, "books_in_db": books}


@app.get("/api/v1/books", response_model=BookPage)
def list_books(
    q: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    pattern = f"%{q}%" if q else "%"
    with get_conn() as conn:
        total = conn.execute(
            "select count(*) as total from books where title ilike %s or author ilike %s",
            (pattern, pattern),
        ).fetchone()["total"]
        items = conn.execute(
            """
            select id, title, author, cover_path, created_at
            from books
            where title ilike %s or author ilike %s
            order by id
            limit %s offset %s
            """,
            (pattern, pattern, limit, offset),
        ).fetchall()
    return {"total": total, "items": items}


@app.get("/api/v1/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    with get_conn() as conn:
        book = conn.execute(
            "select id, title, author, cover_path, created_at from books where id = %s",
            (book_id,),
        ).fetchone()
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book
import os
from datetime import datetime

import psycopg
from fastapi import FastAPI, HTTPException, Query, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

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


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)


class EditionCreate(BaseModel):
    publisher: str = Field(min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=1400, le=2100)


class Edition(BaseModel):
    book_id: int
    number: int
    publisher: str
    year: int | None
    created_at: datetime


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/db-check")
def db_check():
    with get_conn() as conn:
        version = conn.execute("select version() as v").fetchone()["v"]
        books = conn.execute("select count(*) as cnt from books").fetchone()["cnt"]
    return {"database": version, "books_in_db": books}


# книги

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


@app.post("/api/v1/books", response_model=Book, status_code=201)
def create_book(data: BookCreate, response: Response):
    try:
        with get_conn() as conn:
            book = conn.execute(
                """
                insert into books (title, author)
                values (%s, %s)
                returning id, title, author, cover_path, created_at
                """,
                (data.title, data.author),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Такая книга уже есть")
    response.headers["Location"] = f"/api/v1/books/{book['id']}"
    return book


@app.put("/api/v1/books/{book_id}", response_model=Book)
def replace_book(book_id: int, data: BookCreate):
    try:
        with get_conn() as conn:
            book = conn.execute(
                """
                update books
                set title = %s, author = %s
                where id = %s
                returning id, title, author, cover_path, created_at
                """,
                (data.title, data.author, book_id),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Такая книга уже есть")
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


@app.patch("/api/v1/books/{book_id}", response_model=Book)
def update_book(book_id: int, data: BookUpdate):
    if data.title is None and data.author is None:
        raise HTTPException(status_code=400, detail="Нечего менять: передай title или author")
    try:
        with get_conn() as conn:
            book = conn.execute(
                """
                update books
                set title = coalesce(%s, title),
                    author = coalesce(%s, author)
                where id = %s
                returning id, title, author, cover_path, created_at
                """,
                (data.title, data.author, book_id),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Такая книга уже есть")
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


@app.delete("/api/v1/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    with get_conn() as conn:
        deleted = conn.execute("delete from books where id = %s returning id", (book_id,)).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return Response(status_code=204)


# издания

@app.get("/api/v1/books/{book_id}/editions", response_model=list[Edition])
def list_editions(book_id: int):
    with get_conn() as conn:
        book = conn.execute("select id from books where id = %s", (book_id,)).fetchone()
        if book is None:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        editions = conn.execute(
            """
            select book_id, number, publisher, year, created_at
            from editions
            where book_id = %s
            order by number desc
            """,
            (book_id,),
        ).fetchall()
    return editions


@app.post("/api/v1/books/{book_id}/editions", response_model=Edition, status_code=201)
def create_edition(book_id: int, data: EditionCreate, response: Response):
    try:
        with get_conn() as conn:
            edition = conn.execute(
                """
                insert into editions (book_id, number, publisher, year)
                values (
                    %s,
                    (select coalesce(max(number), 0) + 1 from editions where book_id = %s),
                    %s,
                    %s
                )
                returning book_id, number, publisher, year, created_at
                """,
                (book_id, book_id, data.publisher, data.year),
            ).fetchone()
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Издание с этим номером только что создали, повтори запрос")
    response.headers["Location"] = f"/api/v1/books/{book_id}/editions/{edition['number']}"
    return edition


@app.get("/api/v1/books/{book_id}/editions/{number}", response_model=Edition)
def get_edition(book_id: int, number: int):
    with get_conn() as conn:
        edition = conn.execute(
            """
            select book_id, number, publisher, year, created_at
            from editions
            where book_id = %s and number = %s
            """,
            (book_id, number),
        ).fetchone()
    if edition is None:
        raise HTTPException(status_code=404, detail="Издание не найдено")
    return edition
import os
import psycopg
from fastapi import FastAPI

app = FastAPI()
database_url = os.getenv("DATABASE_URL")

@app.get("/quotes")
def get_quotes():
    with psycopg.connect(database_url) as conn:
        rows = conn.execute("select id, text, author from quotes").fetchall()
    return [{"id": r[0], "text": r[1], "author": r[2]} for r in rows]
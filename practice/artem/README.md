# Docker, Docker Compose и REST API: моя практика

Здесь всё, что я сделал по плану:

1. Изучить Docker и docker-compose и установить их на свою машину.
2. Разобраться, что такое REST API, как проектировать методы API, чем они отличаются и как выбрать нужный. Понять, зачем нужны коды ответов от 1xx до 5xx.

Ещё руководители предложили написать REST API на FastAPI с Pydantic и подробной документацией на вымышленном примере. Это проект `library-rest`.


## Что в репозитории

| Папка | Что это | Что я на нём отработал |
|---|---|---|
| `warmup` | страница на nginx | сборка своего образа из Dockerfile, запуск контейнера, проброс портов, сеть между контейнерами |
| `quotes-api` | первое API на FastAPI в контейнере | Dockerfile для Python, кэш слоёв и порядок команд, `.dockerignore`, запуск не от root, подключение к Postgres в соседнем контейнере |
| `library-api` | второе API по тем же шагам, с книгами в Postgres | закрепление: сборка, теги образов, переменная `DATABASE_URL`, общая сеть с базой |
| `library-rest` | основной проект: REST API библиотеки | Docker Compose, затем REST API по этапам |

## Пункт 1. Docker и Docker Compose

Что освоил:

- работу с образами и контейнерами: `docker pull`, `docker run` с флагами `-d`, `--name`, `-p`, `-e`, `-v`, `--network`, команды `ps`, `logs`, `exec`, `stop`, `start`, `rm`, `rmi`;
- готовые образы PostgreSQL 16 и Redis: подключение через `psql` и `redis-cli` внутри контейнера, хранение данных в именованном томе;
- свой образ через Dockerfile: базовый образ, `WORKDIR`, порядок `COPY` ради кэша слоёв, `pip install`, отдельный пользователь вместо root, `EXPOSE`, `CMD`;
- сети: контейнеры в одной сети находят друг друга по имени;
- Docker Compose в `library-rest`: три сервиса (PostgreSQL, API, Adminer), переменные из `.env`, `healthcheck` и `depends_on`, чтобы API запускалось только после готовности базы, `init.sql` для создания таблиц, bind mount и `--reload`, чтобы изменения кода подхватывались без пересборки;
- когда что перезапускать: изменения кода при bind mount ничего не требуют, после `requirements.txt` и `Dockerfile` нужен `--build`, а `init.sql` выполняется только при создании тома, поэтому для него нужен `down -v`.

## Пункт 2. REST API

Делаю по этапам на проекте `library-rest`. Этапы 1–3 касались Docker и Compose, с 4-го начинается REST.

- [x] этапы 1–3: свой образ, Compose из трёх сервисов, bind mount и автоперезагрузка;
- [x] этап 4: `GET /api/v1/books` с поиском `q` и пагинацией `limit` и `offset`, в ответе `total` и `items`; `GET /api/v1/books/{book_id}`; коды 200, 404, 422; модели Pydantic для ответов;
- [ ] этап 5: создание через POST, коды 201 и 409, заголовок `Location`;
- [ ] этап 6: PUT, PATCH, DELETE, код 204, безопасные и идемпотентные методы;
- [ ] этап 7: вложенный ресурс, издания книги;
- [ ] этап 8: подробная документация в `/docs` и README проекта;
- [ ] этап 9: проектирование API без кода, читатели и выдачи книг;
- [ ] этап 10: загрузка и скачивание обложки, коды 400, 413, 415;
- [ ] этап 11: все коды от 1xx до 5xx на своём API;
- [ ] этап 12: свой проект с нуля и `design.md`.

## Как запустить library-rest

```bash
cd library-rest
cp .env.example .env
# заполнить значения в .env
docker compose up -d --build
```

- API: http://localhost:8000, документация: http://localhost:8000/docs
- Adminer: http://localhost:8080 (система PostgreSQL, сервер `db`)
- PostgreSQL с Mac: `localhost:5434`

Примеры запросов:

```bash
curl localhost:8000/db-check
curl "localhost:8000/api/v1/books?limit=2&offset=2"
curl -G --data-urlencode "q=булгаков" localhost:8000/api/v1/books
curl -i localhost:8000/api/v1/books/999
```


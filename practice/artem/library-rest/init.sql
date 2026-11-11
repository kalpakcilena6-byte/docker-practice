create table if not exists books (
id serial primary key,
    title text not null,
    author text not null,
    cover_path text,
    created_at timestamptz not null default now(),
    unique (title, author)
);

create table if not exists editions (
    book_id integer not null references books (id) on delete cascade,
    number integer not null check (number >= 1),
    publisher text not null,
    year integer check (year between 1400 and 2100),
    created_at timestamptz not null default now(),
    primary key (book_id, number)
);

insert into books (title, author) values
    ('Преступление и наказание', 'Фёдор Достоевский'),
    ('Война и мир', 'Лев Толстой'),
    ('Мастер и Маргарита', 'Михаил Булгаков'),
    ('Евгений Онегин', 'Александр Пушкин');

insert into editions (book_id, number, publisher, year) values
    (1, 1, 'Русский вестник', 1866),
    (1, 2, 'АСТ', 2015),
    (2, 1, 'Русский вестник', 1869),
    (4, 1, 'Типография Департамента народного просвещения', 1833),
    (4, 2, 'Эксмо', 2020);
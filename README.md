# Telegram-бот Московского зоопарка: "Тотемное животное"

Бот-викторина для популяризации программы опеки животных Московского зоопарка. Пользователь отвечает на 10 вопросов и узнаёт, какое из 10 животных зоопарка ближе всего к его характеру.

## 🎯 Возможности

- ✅ Викторина из 10 вопросов с персонализированными результатами;
- ✅ 10 животных-героев с описаниями, фактами и фотографиями;
- ✅ Информация о программе опеки с переходом на сайт зоопарка;
- ✅ Система отзывов и оценок;
- ✅ Сохранение всех результатов в PostgreSQL для аналитики;
- ✅ Полностью готов к развертыванию через Docker.

## 🏗 Архитектура

### Технологический стек
- **Python 3.11** + **python-telegram-bot v20+** (асинхронный);
- **PostgreSQL 15** — хранение пользователей, результатов и отзывов;
- **SQLAlchemy 2.0 (async)** — ORM для работы с БД;
- **Docker + Docker Compose** — контейнеризация;
- **JSON** — хранение вопросов и данных о животных.

### Структура проекта
```
zoo_bot/
├── app/                      # Исходный код (ООП)
│   ├── init.py
│   ├── bot.py                # Точка входа, инициализация бота
│   ├── config.py             # Загрузка конфигурации из .env
│   ├── database.py           # Менеджер PostgreSQL (SQLAlchemy async)
│   ├── handlers.py           # Обработчики команд и кнопок Telegram
│   ├── models.py             # SQLAlchemy модели (User, QuizResult, Feedback)
│   └── quiz_engine.py        # Логика викторины и подсчёт баллов
├── data/                     # Данные викторины (JSON)
│   ├── animals.json          # 10 животных-героев
│   └── questions.json        # 10 вопросов с вариантами ответов
├── images/                   # Фотографии животных (10 файлов)
│   ├── lion.jpg
│   ├── elephant.jpg
│   └── ...
├── .env                      # Секреты
├── .env.example              # Шаблон .env
├── .gitignore
├── docker-compose.yml        # Оркестрация контейнеров
├── Dockerfile
├── requirements.txt
└── README.md
```
### Схема базы данных
```
users
├── id (PK)
├── telegram_id (UNIQUE)
├── username
├── first_name, last_name
└── created_at
quiz_results
├── id (PK)
├── user_id (FK -> users)
├── animal_key (lion, tiger, elephant...)
├── answers_json (JSON с историей ответов)
├── scores_json (JSON с баллами по животным)
└── completed_at
feedback
├── id (PK)
├── user_id (FK -> users)
├── rating (1-5)
├── comment
└── created_at
```

## 🚀 Быстрый старт (Docker)

### 1. Клонируйте репозиторий
```bash
git clone git@github.com:3axap4yk/zoo_bot.git
cd zoo_bot
```

### 2. Получите токен бота
Откройте `@BotFather` в Telegram, отправьте команду `/newbot` и следуйте инструкциям для получения токена

### 3. Настройте переменные окружения
```bash
cp .env.example .env
```
Заполните `.env` своими данными

### 4. Запустите бота
```bash
docker compose up -d --build
```

### 5. Просмотр логов
```bash
docker compose logs -f bot
```

## 📊 Работа с базой данных
### Подключиться к PostgreSQL
```bash
docker exec -it zoo_bot_db psql -U zoo_bot_user -d zoo_bot_db
```

### Полезные команды
```sql
-- Показать все таблицы
\dt

-- Посмотреть всех пользователей
SELECT * FROM users;

-- Посмотреть результаты викторин
SELECT * FROM quiz_results;

-- Какие животные самые популярные?
SELECT animal_key, COUNT(*) as count 
FROM quiz_results 
GROUP BY animal_key 
ORDER BY count DESC;

-- Средняя оценка бота
SELECT AVG(rating) FROM feedback;

-- Выйти
\q
```

### Одной командой
```bash
# Количество пользователей
docker exec -it zoo_bot_db psql -U zoo_bot_user -d zoo_bot_db \
  -c "SELECT COUNT(*) FROM users;"

# Популярность животных
docker exec -it zoo_bot_db psql -U zoo_bot_user -d zoo_bot_db \
  -c "SELECT animal_key, COUNT(*) FROM quiz_results GROUP BY animal_key ORDER BY count DESC;"
```

## ✏️ Редактирование контента
### Изменить вопросы
Откройте `data/questions.json` и отредактируйте тексты или варианты ответов. Перезапустите контейнер:
```bash
docker compose restart bot
```

### Изменить описания животных
Откройте `data/animals.json` — там описания, факты и стоимость опеки для каждого животного

### Добавить новое животное
- Добавьте запись в `data/animals.json`;
- Добавьте его в поле `scores` нужных вариантов ответов в `data/questions.json`;
- Положите фотографию в `images/`;
- Перезапустите: `docker compose restart bot`.

## 🛠 Локальная разработка (без Docker)

1. Установите PostgreSQL и создайте базу данных:
```
sudo apt install postgresql
sudo -u postgres psql
CREATE DATABASE zoo_bot_db;
CREATE USER zoo_bot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE zoo_bot_db TO zoo_bot_user;
```

2. Установите Python зависимости:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. В `.env` измените:
```
POSTGRES_HOST=localhost
```

4. Запустите:
```bash
python -m app.bot
```

## 📈 Алгоритм подсчёта баллов

- Каждый вариант ответа начисляет 1-2 балла одному или нескольким животным;
- В конце побеждает животное с наибольшей суммой баллов;
- При ничьей приоритет у того животного, которое встречалось в ответах пользователя раньше (по порядку вопросов).

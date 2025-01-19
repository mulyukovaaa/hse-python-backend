# Указываем базовый образ Python 3.12
FROM python:3.12-slim

# Устанавливаем зависимости для Poetry
RUN pip install poetry

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы poetry для установки зависимостей
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости с помощью Poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Копируем все файлы проекта в контейнер
COPY . /app

# Экспонируем порт 8000 для приложения
EXPOSE 8000

# Запускаем Uvicorn сервер для FastAPI приложения
CMD ["poetry", "run", "uvicorn", "lecture_2.hw.shop_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

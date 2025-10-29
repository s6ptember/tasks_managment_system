FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    libc6-dev \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Создание пользователя для запуска приложения
RUN addgroup --system django && \
    adduser --system --group django

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY --chown=django:django . .

# Создание необходимых директорий и установка прав
RUN mkdir -p /app/src/static /app/src/staticfiles && \
    chown -R django:django /app/src/static /app/src/staticfiles && \
    chmod -R 775 /app/src/static /app/src/staticfiles

# Переключение на непривилегированного пользователя
USER django

# Открытие порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "src", "config.wsgi:application"]

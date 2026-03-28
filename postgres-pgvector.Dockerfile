# firefeed-api/postgres-pgvector.Dockerfile
FROM postgres:17-alpine

# Установка зависимостей для компиляции pgvector
# Устанавливаем clang19 и llvm19 - версии, которые ожидает PostgreSQL 17
RUN apk add --no-cache \
    gcc \
    musl-dev \
    clang19 \
    llvm19 \
    git \
    make

# Скачивание и компиляция pgvector с правильными путями
# pg_config находится в /usr/local/bin/pg_config в postgres:17-alpine
RUN git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make USE_PGXS=1 PG_CONFIG=/usr/local/bin/pg_config \
    && make USE_PGXS=1 PG_CONFIG=/usr/local/bin/pg_config install \
    && cd / \
    && rm -rf /tmp/pgvector

# Копируем скрипты инициализации
COPY database/init/ /docker-entrypoint-initdb.d/

# Делаем скрипты исполняемыми
RUN chmod +x /docker-entrypoint-initdb.d/*.sh

# Экспорт порта
EXPOSE 5432

# Команда по умолчанию
CMD ["postgres"]
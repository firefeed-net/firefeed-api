#!/bin/bash
set -euo pipefail

# Use POSTGRES_* vars from docker-compose (set from root .env)
: "${POSTGRES_DB:=firefeed}"
: "${POSTGRES_USER:=firefeed_api}"
: "${POSTGRES_PASSWORD:=firefeed_password}"

# Check that variables are not empty
if [[ -z "$POSTGRES_USER" || -z "$POSTGRES_PASSWORD" ]]; then
  echo "❌ Ошибка: POSTGRES_USER и POSTGRES_PASSWORD не могут быть пустыми"
  exit 1
fi

# Prepare SQL using resolved variables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 <<EOSQL
-- Включаем необходимые расширения
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Создаём или обновляем пользователя
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$POSTGRES_USER') THEN
        CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
    ELSE
        ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
    END IF;
END
\$\$;

-- Даём права на подключение к базе
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO $POSTGRES_USER;

-- Даём права на схему public
GRANT USAGE ON SCHEMA public TO $POSTGRES_USER;

-- Даём права на существующие таблицы и последовательности
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $POSTGRES_USER;

-- Устанавливаем права по умолчанию для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $POSTGRES_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO $POSTGRES_USER;

-- Дополнительно: разрешаем создавать временные таблицы (полезно для приложений)
ALTER USER $POSTGRES_USER SET statement_timeout = '30s';
EOSQL

echo "✅ Пользователь '$POSTGRES_USER' создан или обновлён"
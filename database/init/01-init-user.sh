#!/bin/bash
set -euo pipefail

# Получаем переменные окружения или используем значения по умолчанию
: "${FIREFEED_DB:=firefeed}"
: "${FIREFEED_DB_USER:=firefeed_api}"
: "${FIREFEED_DB_PASSWORD:=api_password}"

# Проверяем, что переменные не пустые
if [[ -z "$FIREFEED_DB_USER" || -z "$FIREFEED_DB_PASSWORD" ]]; then
  echo "❌ Ошибка: FIREFEED_DB_USER и FIREFEED_DB_PASSWORD не могут быть пустыми"
  exit 1
fi

# Подготовка SQL с подстановкой переменных
psql -v ON_ERROR_STOP=1 --username "$FIREFEED_DB_USER" --dbname "$FIREFEED_DB" --set=ON_ERROR_STOP=1 <<EOSQL
-- Включаем необходимые расширения
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Создаём или обновляем пользователя
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$FIREFEED_DB_USER') THEN
        CREATE USER $FIREFEED_DB_USER WITH PASSWORD '$FIREFEED_DB_PASSWORD';
    ELSE
        ALTER USER $FIREFEED_DB_USER WITH PASSWORD '$FIREFEED_DB_PASSWORD';
    END IF;
END
\$\$;

-- Даём права на подключение к базе
GRANT CONNECT ON DATABASE "$FIREFEED_DB" TO $FIREFEED_DB_USER;

-- Даём права на схему public
GRANT USAGE ON SCHEMA public TO $FIREFEED_DB_USER;

-- Даём права на существующие таблицы и последовательности
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $FIREFEED_DB_USER;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $FIREFEED_DB_USER;

-- Устанавливаем права по умолчанию для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $FIREFEED_DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO $FIREFEED_DB_USER;

-- Дополнительно: разрешаем создавать временные таблицы (полезно для приложений)
ALTER USER $FIREFEED_DB_USER SET statement_timeout = '30s';
EOSQL

echo "✅ Пользователь '$FIREFEED_DB_USER' создан или обновлён"
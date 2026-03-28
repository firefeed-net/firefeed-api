#!/bin/bash
set -euo pipefail

# Получаем переменные окружения или используем значения по умолчанию
: "${POSTGRES_DB:=firefeed}"
: "${FIREFEED_DB_USER:=firefeed_api}"
: "${FIREFEED_DB_PASSWORD:=api_password}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v firefeed_db_user="$FIREFEED_DB_USER" \
     -v firefeed_db_password="$FIREFEED_DB_PASSWORD" <<'EOSQL'
    -- Включаем необходимые расширения
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Создаём пользователя, если не существует, или обновляем пароль
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_setting('firefeed_db_user')) THEN
            EXECUTE 'CREATE USER ' || quote_ident(current_setting('firefeed_db_user')) ||
                    ' WITH PASSWORD ' || quote_literal(current_setting('firefeed_db_password'));
        ELSE
            EXECUTE 'ALTER USER ' || quote_ident(current_setting('firefeed_db_user')) ||
                    ' WITH PASSWORD ' || quote_literal(current_setting('firefeed_db_password'));
        END IF;
    END
    $$;

    -- Даём права на подключение к базе
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO "$FIREFEED_DB_USER";

    -- Даём права на схему public
    GRANT USAGE ON SCHEMA public TO "$FIREFEED_DB_USER";

    -- Даём права на существующие таблицы и последовательности
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "$FIREFEED_DB_USER";
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "$FIREFEED_DB_USER";

    -- Устанавливаем права по умолчанию для будущих объектов
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "$FIREFEED_DB_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO "$FIREFEED_DB_USER";
EOSQL

echo "✅ Пользователь '$FIREFEED_DB_USER' создан/обновлён"
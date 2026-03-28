# Тестирование firefeed-api

Этот документ описывает структуру и запуск тестов для микросервиса firefeed-api.

## Структура тестов

Тесты разделены на две основные категории:

### Unit-тесты (`tests/unit/`)
- **`test_external_api_compatibility.py`** - Тесты внешнего API для проверки совместимости с клиентами
- **`test_internal_api.py`** - Тесты внутреннего API для проверки внутренних операций
- **`api/`** - Тесты для внешних API-эндпоинтов
- **`config/`** - Тесты конфигурационных модулей
- **`core/`** - Тесты ядренных компонентов
- **`database/`** - Тесты базы данных
- **`exceptions/`** - Тесты обработки исключений
- **`models/`** - Тесты моделей данных
- **`repositories/`** - Тесты репозиториев
- **`services/`** - Тесты сервисов
- **`utils/`** - Тесты утилит

### Integration-тесты (`tests/integration/`)
- Тесты интеграции между компонентами
- Тесты взаимодействия с внешними сервисами

## Запуск тестов

### Запуск всех тестов
```bash
cd firefeed-api
python -m pytest tests/
```

### Запуск unit-тестов
```bash
cd firefeed-api
python -m pytest tests/unit/
```

### Запуск integration-тестов
```bash
cd firefeed-api
python -m pytest tests/integration/
```

### Запуск конкретного теста
```bash
cd firefeed-api
python -m pytest tests/unit/test_external_api_compatibility.py::TestExternalAPICompatibility::test_health_check
```

### Запуск тестов с подробным выводом
```bash
cd firefeed-api
python -m pytest tests/ -v
```

### Запуск тестов в Docker контейнере
```bash
cd firefeed-api
docker-compose exec api python -m pytest tests/
```

## Покрытие кода

### Генерация отчета о покрытии
```bash
cd firefeed-api
python -m pytest tests/ --cov=firefeed_api --cov-report=html
```

Отчет будет доступен в `htmlcov/index.html`.

### Проверка покрытия в Docker
```bash
cd firefeed-api
docker-compose exec api python -m pytest tests/ --cov=firefeed_api --cov-report=term
```

## Тестовые данные

Тесты используют фикстуры для создания тестовых данных. Основные фикстуры определены в `conftest.py`.

## Mock-объекты

Для изоляции unit-тестов используются mock-объекты:
- `unittest.mock` для мокирования внешних зависимостей
- `patch` для временного замещения модулей и функций

## CI/CD

Тесты автоматически запускаются в CI/CD pipeline:
- Unit-тесты запускаются при каждом коммите
- Integration-тесты запускаются при создании pull request
- Покрытие кода проверяется и сравнивается с базовой веткой

## Best Practices

1. **Изолированные тесты**: Каждый тест должен быть независимым
2. **Чистые фикстуры**: Используйте фикстуры для подготовки тестовых данных
3. **Mock внешних зависимостей**: Мокируйте базу данных, внешние API и файловую систему
4. **Тестирование исключений**: Проверяйте обработку ошибок и исключительных ситуаций
5. **Именование тестов**: Используйте понятные имена для тестов
6. **Документирование**: Добавляйте комментарии к сложным тестам

## Запуск тестов в development

Для удобства разработки можно использовать следующие команды:

```bash
# Запуск тестов с авто-перезапуском при изменениях
python -m pytest tests/ --watch

# Запуск только упавших тестов
python -m pytest tests/ --lf

# Запуск тестов по ключевым словам
python -m pytest tests/ -k "health"

# Сервис Групповых Денежных Сборов
## Описание

Веб-сервис на базе Django, предоставляющий REST API для организации групповых денежных сборов. Пользователи могут создавать сборы, делать пожертвования и отслеживать статус сборов.

## Технический стек

- **Backend**: Django, Django REST Framework
- **База данных**: MySQL
- **Кэширование**: Redis
- **Асинхронные задачи**: Celery
- **Документация API**: Swagger/drf-yasg
- **Контейнеризация**: Docker, Docker Compose
- **Аутентификация**: JWT (djangorestframework-simplejwt)
- **Email**: MailHog (для разработки)

## Основные сущности

- **User** — пользователь системы
- **Collect** — групповой денежный сбор (название, описание, цель сбора и т.д.)
- **Payment** — платеж в рамках сбора

## Установка и запуск

### Предварительные требования

- Docker и Docker Compose

### Шаги по установке

1. Клонируйте репозиторий:
```
git clone <url-репозитория>
   cd fund_raising
```


2. Создайте файл `.env` со следующими переменными:
```
DJANGO_ENV=development
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
   
   # MySQL
   MYSQL_ROOT_PASSWORD=password
   MYSQL_DATABASE=fund_raising
   MYSQL_USER=root
   MYSQL_PASSWORD=password
   MYSQL_HOST=mysql
   
   # Redis и Celery
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   REDIS_CACHE_URL=redis://redis:6379/1
   
   # Email для разработки (MailHog)
   DEV_EMAIL_HOST=mailhog
   DEV_EMAIL_PORT=1025
   DEV_EMAIL_USE_TLS=False
   
   # Email для production
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@example.com
   EMAIL_HOST_PASSWORD=your_email_password
   EMAIL_USE_TLS=True
   DEFAULT_FROM_EMAIL=Fund Raising <noreply@example.com>
```


3. Запустите проект с помощью Docker Compose:
```
docker compose up --build
4. Доступные адреса:
   - Основной API: `http://localhost:8000/api/v1/`
   - Swagger UI: `http://localhost:8000/docs/`
   - MailHog (для перехвата email): `http://localhost:8025/`

## API Endpoints

- `/api/v1/collects/` — операции с групповыми сборами
- `/api/v1/payments/` — операции с платежами
- `/api/auth/token/` — получение JWT токена
- `/api/auth/token/refresh/` — обновление JWT токена
- `/docs/` — интерактивная документация Swagger

## Команды

### Создание суперпользователя

```
docker-compose exec web python manage.py createsuperuser
```


### Генерация тестовых данных

```
docker-compose exec web python manage.py generate_test_data --users 50 --collects 100 --payments 5000
```


Данная команда создаст:
- 50 пользователей
- 100 групповых сборов с различными типами
- 5000 платежей с реалистичными суммами и датами

## Функциональность

- Создание и управление групповыми сборами
- Система платежей с уведомлениями
- Кэширование данных для повышения производительности
- Отправка email-уведомлений через Celery
- Документация API с помощью Swagger

## Примеры API-запросов

### Получение токена

```shell script
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```


### Получение списка сборов

```shell script
curl -X GET http://localhost:8000/api/v1/collects/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```


### Создание нового сбора

```shell script
curl -X POST http://localhost:8000/api/v1/collects/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"title": "День рождения", "description": "Сбор на подарок", "occasion": "birthday", "goal_amount": "5000.00"}'
```


## Производительность

- Реализовано кэширование GET-запросов через Redis
- Bulk операции для эффективной работы с большими объемами данных
- Асинхронные задачи для отправки email-уведомлений через Celery
# Group Fundraising Service

## Overview

A Django-based web service providing a REST API for organizing group fundraising. Users can create collections, make donations, and track the progress of fundraising goals.

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Database**: MySQL
- **Caching**: Redis
- **Asynchronous Tasks**: Celery
- **API Documentation**: Swagger/drf-yasg
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Email Testing**: MailHog (for development)

## Core Entities

- **User**: System user
- **Collect**: A group fundraising event (title, description, goal amount, etc.)
- **Payment**: A donation made towards a specific collection

## Installation and Setup

### Prerequisites

- Docker and Docker Compose

### Step-by-Step Guide

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fund_raising
   ```

2. **Configure environment variables:**
   Create a `.env` file in the root directory and add the following:
   ```env
   DJANGO_ENV=development
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
   
   # MySQL Configuration
   MYSQL_ROOT_PASSWORD=password
   MYSQL_DATABASE=fund_raising
   MYSQL_USER=root
   MYSQL_PASSWORD=password
   MYSQL_HOST=mysql
   
   # Redis and Celery
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   REDIS_CACHE_URL=redis://redis:6379/1
   
   # Email Configuration for Development (MailHog)
   DEV_EMAIL_HOST=mailhog
   DEV_EMAIL_PORT=1025
   DEV_EMAIL_USE_TLS=False
   
   # Email Configuration for Production
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@example.com
   EMAIL_HOST_PASSWORD=your_email_password
   EMAIL_USE_TLS=True
   DEFAULT_FROM_EMAIL=Fund Raising <noreply@example.com>
   ```

3. **Start the project using Docker Compose:**
   ```bash
   docker compose up --build
   ```

4. **Access points:**
   - **Main API:** `http://localhost:8000/api/v1/`
   - **Swagger UI:** `http://localhost:8000/docs/`
   - **MailHog (Email Interceptor):** `http://localhost:8025/`

## API Endpoints

- `/api/v1/collects/` — Group fundraising operations
- `/api/v1/payments/` — Payment operations
- `/api/auth/token/` — Obtain JWT token
- `/api/auth/token/refresh/` — Refresh JWT token
- `/docs/` — Interactive Swagger documentation

## Management Commands

### Create Superuser
```bash
docker compose exec web python manage.py createsuperuser
```

### Generate Sample Data
```bash
docker compose exec web python manage.py generate_test_data --users 50 --collects 100 --payments 5000
```
This command generates:
- 50 users
- 100 fundraising collections of various types
- 5,000 payments with realistic amounts and dates

## Key Features

- Creation and management of group fundraising collections
- Payment system with automated notifications
- Redis-based caching for optimized performance
- Asynchronous email delivery via Celery
- Automated API documentation with Swagger

## API Examples

### Obtain Token
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### List Fundraising Collections
```bash
curl -X GET http://localhost:8000/api/v1/collects/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Create a New Collection
```bash
curl -X POST http://localhost:8000/api/v1/collects/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"title": "Birthday Gift", "description": "Raising money for a gift", "occasion": "birthday", "goal_amount": "5000.00"}'
```

## Performance Optimization

- **Caching**: Implemented Redis caching for GET requests.
- **Efficiency**: Utilizes bulk operations for handling large datasets.
- **Scalability**: Offloads email notifications to background tasks via Celery.
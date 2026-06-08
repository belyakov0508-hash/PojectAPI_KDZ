# Courier API

Система управления курьерской доставкой. Диспетчер загружает курьеров и заказы, назначает заказы курьерам. Курьеры видят свои заказы, рейтинг и заработок.

---

## Стек технологий

**Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, JWT  
**Frontend:** React, Vite  
**Тесты:** pytest, pytest-asyncio, httpx

---

## Установка и запуск

### Backend

1. Установить зависимости:
```bash
pip install -r backend/requirements.txt
```

2. Создать файл `backend/.env`: DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/courier_db
SECRET_KEY=your_secret_key
3. Запустить сервер:
```bash
uvicorn backend.main:app --reload
```

### Frontend

1. Установить зависимости:
```bash
cd frontend
npm install
```

2. Создать файл `frontend/.env`: VITE_API_URL=http://localhost:8000
3. Запустить:
```bash
npm run dev
```

---

## Роли

| Роль | role_id | Возможности |
|------|---------|-------------|
| Курьер | 1 | Видит свои заказы, завершает заказы, видит рейтинг и заработок |
| Диспетчер | 2 | Загружает курьеров и заказы, назначает курьеров, мониторинг |

---

## Создание диспетчера

```sql
INSERT INTO users (email, hashed_password, role_id, created_at)
VALUES ('Admin@mail.ru', '12', 2, NOW());
```

---

## Формат JSON файлов

### couriers.json
```json
[
  {
    "courier_id": 1,
    "courier_type_id": 1,
    "working_hours": ["09:00-18:00"],
    "regions": [1, 2],
    "email": "courier1@mail.com",
    "password": "pass123"
  }
]
```

| Поле | Тип | Описание |
|------|-----|----------|
| courier_id | int | ID курьера (уникальный, > 0) |
| courier_type_id | int | 1 = пеший, 2 = велокурьер, 3 = авто |
| working_hours | string[] | Часы работы, формат "HH:MM-HH:MM" |
| regions | int[] | Список регионов |
| email | string | Почта для входа |
| password | string | Пароль для входа |

### orders.json
```json
[
  {
    "order_id": 1,
    "weight": 1.50,
    "region": 1,
    "delivery_hours": ["09:00-12:00"]
  }
]
```

| Поле | Тип | Описание |
|------|-----|----------|
| order_id | int | ID заказа (уникальный, > 0) |
| weight | float | Вес от 0.01 до 50.00 кг |
| region | int | Регион доставки (> 0) |
| delivery_hours | string[] | Часы доставки, формат "HH:MM-HH:MM" |

---

## Ограничения по весу

| Тип курьера | Максимальный вес |
|-------------|-----------------|
| Пеший | 10 кг |
| Велокурьер | 15 кг |
| Автокурьер | 50 кг |

---

## Расчёт рейтинга и заработка

**Рейтинг:** rating = (3600 - min(t, 3600)) / 3600 * 5,
где `t` — минимальное из средних времён доставки по районам (в секундах).  
Рассчитывается только если курьер завершил хотя бы один заказ.

**Заработок:** earnings = количество_заказов × 500 × C, где `C` — коэффициент типа курьера: пеший = 2, велокурьер = 5, авто = 9.

---

## API эндпоинты

### Авторизация
| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| POST | /api/auth/login | Все | Вход в систему |

### Заказы
| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | /api/orders/ | Диспетчер | Все заказы |
| GET | /api/orders/my | Курьер | Свои заказы |
| GET | /api/orders/my/stats | Курьер | Рейтинг и заработок |
| PATCH | /api/orders/{id}/assign | Диспетчер | Назначить курьера |
| POST | /api/orders/{id}/complete | Курьер | Завершить заказ |

### Курьеры и мониторинг
| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | /api/monitoring/couriers | Диспетчер | Список курьеров |
| POST | /api/monitoring/upload-couriers | Диспетчер | Загрузить JSON курьеров |
| POST | /api/dispatcher/upload-orders | Диспетчер | Загрузить JSON заказов |

---

## Запуск тестов

```bash
pytest -v
```

---

## Структура проекта
├ backend/

│   ├── api/          # Роутеры FastAPI

│   ├── core/         # БД, конфиг, безопасность

│   ├── crud/         # Работа с БД

│   ├── models/       # SQLAlchemy модели

│   ├── schemas/      # Pydantic схемы

│   ├── tests/        # Тесты

│   └── main.py

├ frontend/

│   └── src/

│       ├── pages/    # Auth, Courier, Dispatcher, Monitoring, CourierOrders

│       ├── components/  # Navbar

│       └── api.js    # HTTP клиент

└── README.md
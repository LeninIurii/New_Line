# New_Line

Telegram Mini App для мониторинга лимитных ордеров по фьючерсам на бирже Hyperliquid.

## Описание

Модуль состоит из двух частей:
- **Backend** — сбор данных с Hyperliquid, фильтрация, хранение, логирование
- **Mini App** — отображение активных лимитных ордеров в реальном времени через Telegram

## Структура проекта

```
New_Line/
├── backend/
│   ├── main.py                 # Точка входа
│   ├── config.py               # Конфиг токенов и порогов
│   ├── models.py               # Dataclass-модели
│   ├── filters.py              # Фильтрация ордеров
│   ├── order_manager.py        # Менеджер активных лимиток
│   ├── hyperliquid_client.py   # Клиент Hyperliquid WS/REST
│   ├── ws_server.py            # WebSocket сервер для Mini App
│   ├── stats_reporter.py       # Логи статистики каждые 5 сек
│   └── logger.py               # Централизованный логгер
├── miniapp/
│   ├── index.html              # Главный экран Mini App
│   ├── app.js                  # Логика и WebSocket клиент
│   └── styles.css              # Стили
├── requirements.txt
└── README.md
```

## Требования

- Python 3.11+
- websockets
- aiohttp

## Установка и запуск

```bash
pip install -r requirements.txt
cd backend
python main.py
```

## Конфиг токенов

Отредактируй `backend/config.py`:
- Добавь нужные токены в `TOKENS_CONFIG`
- Укажи минимальный объём `min_usdc` для каждого токена
- При необходимости смени `WS_PORT`

## Как работает

1. Backend подключается к Hyperliquid WebSocket
2. Входящие ордера фильтруются по 3 критериям:
   - Токен есть в конфиге
   - Объём `px * sz >= min_usdc`
   - Отклонение цены от mid-price >= 5%
3. Прошедшие фильтр лимитки добавляются в активный список
4. Каждые 5 секунд проверяются открытые ордера на бирже
5. Неактуальные лимитки удаляются с причиной: `filled` / `canceled` / `unknown`
6. Mini App получает обновления через WebSocket и рендерит карточки

## Логирование

Каждые 5 секунд в логах:
- Количество поступивших / прошедших / не прошедших фильтр
- Текущее количество активных лимиток
- Статистика удалённых (filled / canceled / unknown)
- Какие лимитки появились и исчезли (с txHash)

## Code Style

- Python: PEP 8, black (88 символов), ruff, mypy
- JS: ESLint + Prettier, ES2020+
- Максимум 300 строк на файл, 50 строк на функцию

## Лицензия

MIT

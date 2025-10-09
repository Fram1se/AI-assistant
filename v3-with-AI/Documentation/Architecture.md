# Архитектура проекта Telegram бота с Yandex GPT

## Общая структура проекта

```
telegram-yandex-gpt-bot/
├── main.py                    # Главный файл приложения
├── requirements.txt           # Зависимости проекта(На сервере)
└── Technical task.md                  # Документация проекта
```

## Компоненты архитектуры

### 1. **Слой конфигурации (Configuration Layer)**
```python
# Текущая реализация - переменные в коде
API_TOKEN = "your_telegram_bot_token"
YANDEX_API_KEY = "your_yandex_api_key"
YANDEX_FOLDER_ID = "your_folder_id"
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/..."
```

**Рекомендуемое улучшение:**
```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    API_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY")
    YANDEX_FOLDER_ID: str = os.getenv("YANDEX_FOLDER_ID")
    YANDEX_GPT_URL: str = "https://llm.api.cloud.yandex.net/..."
```

### 2. **Слой инициализации (Initialization Layer)**
```python
# Инициализация основных компонентов
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
```

### 3. **Слой представления (Presentation Layer)**
#### 3.1 Клавиатуры и интерфейс
```python
def get_main_menu() -> ReplyKeyboardMarkup
def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup
```

#### 3.2 Обработчики сообщений (Handlers)
```python
# Команды
@dp.message(Command("start"))
@dp.message(Command("menu")) 
@dp.message(Command("help"))
@dp.message(Command("status"))

# Кнопки меню
@dp.message(lambda message: message.text == "ℹ️ Информация для проекта")
@dp.message(lambda message: message.text == "🔍 Поиск")
@dp.message(lambda message: message.text == "🏠 Главное меню")

# Общий обработчик текста
@dp.message()
```

### 4. **Слой бизнес-логики (Business Logic Layer)**
#### 4.1 Сервис Yandex GPT
```python
async def ask_yandex_gpt(question: str) -> str:
    """
    Основной сервис для взаимодействия с Yandex GPT API
    """
    # Заголовки авторизации
    # Подготовка данных запроса
    # Обработка HTTP запроса
    # Парсинг ответа
    # Обработка ошибок
```

### 5. **Слой данных (Data Layer)**
```python
# Структура данных для Yandex GPT запроса
data = {
    "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.3,
        "maxTokens": 1500
    },
    "messages": [
        {
            "role": "system",
            "text": "Ты - полезный ИИ-ассистент..."
        },
        {
            "role": "user",
            "text": question
        }
    ]
}
```

## Поток данных (Data Flow)

```
Пользователь Telegram
        ↓
Telegram Bot API
        ↓
Aiogram Dispatcher
        ↓
Соответствующий обработчик
        ↓
Сервис Yandex GPT (ask_yandex_gpt)
        ↓
Yandex Cloud LLM API
        ↓
Обработка ответа
        ↓
Форматирование сообщения
        ↓
Отправка пользователю
```

## Модульная архитектура (Рекомендуемое улучшение)

```
telegram-yandex-gpt-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── handlers/            # Обработчики
│   │   ├── __init__.py
│   │   ├── commands.py      # Команды (/start, /help, etc.)
│   │   ├── menu.py          # Обработчики меню
│   │   └── messages.py      # Обработка сообщений
│   ├── keyboards/           # Клавиатуры
│   │   ├── __init__.py
│   │   ├── main_menu.py
│   │   └── builder.py
│   ├── services/            # Сервисы
│   │   ├── __init__.py
│   │   └── yandex_gpt.py    # Сервис Yandex GPT
│   └── utils/               # Утилиты
│       ├── __init__.py
│       └── logger.py        # Настройка логирования
├── requirements.txt
└── README.md
```

## Компонентная диаграмма

```
+----------------+     +-----------------+     +-----------------+
|   Пользователь |     |  Telegram Bot   |     |   Yandex GPT    |
|    Telegram    |---->|     (Aiogram)   |---->|      API        |
+----------------+     +-----------------+     +-----------------+
         ↑                      |                      |
         |                      |                      |
         +----------------------+----------------------+
         |             Обработка ответа               |
         +--------------------------------------------+
```

## Описание ключевых компонентов

### 1. **Ядро бота (Bot Core)**
- **Aiogram Dispatcher** - маршрутизатор сообщений
- **Bot instance** - экземпляр бота для API вызовов
- **Middleware** (опционально) - для обработки контекста

### 2. **Менеджер состояний (State Management)**
```python
# Текущая реализация - stateless
# Рекомендуемое улучшение - FSM (Finite State Machine)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class UserStates(StatesGroup):
    WAITING_FOR_QUESTION = State()
    IN_SEARCH_MODE = State()
```

### 3. **Сервисный слой (Service Layer)**
- **Yandex GPT Service** - инкапсуляция логики API вызовов
- **Error Handling** - обработка ошибок сети и API
- **Rate Limiting** - ограничение частоты запросов

### 4. **Слой представления (View Layer)**
- **Keyboard Builders** - создание интерфейсов
- **Message Formatters** - форматирование ответов
- **Template System** - шаблоны сообщений

## Преимущества текущей архитектуры

1. **Простота** - один файл для быстрого старта
2. **Понятность** - линейный поток выполнения
3. **Минимальные зависимости** - только необходимые библиотеки

## Возможные улучшения архитектуры

1. **Разделение на модули** для лучшей поддерживаемости
2. **Добавление FSM** для управления состояниями диалога
3. **Кэширование** часто запрашиваемых ответов
4. **Логирование** операций и ошибок
5. **Конфигурация через environment variables**
6. **Docker контейнеризация** для упрощения деплоя
7. **База данных** для хранения истории диалогов
8. **Система плагинов** для расширения функциональности
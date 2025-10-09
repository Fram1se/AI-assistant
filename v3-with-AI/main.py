import logging
import aiohttp
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройки
API_TOKEN = "8171207811:AAGPMC93yKCM_KOmzJ5cr0WxgLJs3ycO5MQ"
YANDEX_API_KEY = "AQVN0-erzW4-kr4F7HrG9gqgVRm7__JJBsCceTCX"  # Замените на ваш API ключ
YANDEX_FOLDER_ID = "b1gv72v9ib7kguo2h06h"     # Замените на ваш folder_id
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем главное меню
def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="ℹ️ Информация для проекта"),
        KeyboardButton(text="🔍 Поиск")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Создаем клавиатуру с кнопкой "Главное меню"
def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)

async def ask_yandex_gpt(question: str) -> str:
    """
    Функция для обращения к Yandex GPT
    """
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
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
                "text": "Ты - полезный ИИ-ассистент. Отвечай кратко и информативно."
            },
            {
                "role": "user",
                "text": question
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(YANDEX_GPT_URL, headers=headers, json=data, timeout=30) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result["result"]["alternatives"][0]["message"]["text"]
                
                elif response.status == 401:
                    return "❌ Ошибка: Неверный API-ключ Yandex GPT"
                
                elif response.status == 403:
                    return "❌ Ошибка: Нет прав доступа. Проверьте права сервисного аккаунта"
                
                else:
                    error_text = await response.text()
                    return f"❌ Ошибка {response.status}: {error_text}"
                    
    except asyncio.TimeoutError:
        return "⏰ Таймаут: Превышено время ожидания ответа"
    except Exception as e:
        return f"❌ Непредвиденная ошибка: {str(e)}"

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Обработчик команды /start
    """
    welcome_text = (
        "👋 Привет! Я бот с интеграцией Yandex GPT.\n\n"
        "Используйте кнопки меню ниже для навигации:\n\n"
        "• ℹ️ Информация для проекта - покажу информацию о проекте\n"
        "• 🔍 Поиск - перейду в режим поиска и ответов\n\n"
        "Также вы можете просто написать любой вопрос!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

@dp.message(Command("menu"))
async def menu_handler(message: types.Message):
    """
    Обработчик команды /menu - показывает главное меню
    """
    welcome_back_text = (
        "🏠 Добро пожаловать в главное меню!\n\n"
        "Выберите нужный раздел:"
    )
    await message.answer(welcome_back_text, reply_markup=get_main_menu())

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    """
    Обработчик команды /help
    """
    help_text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "Этот бот использует Yandex GPT для ответов на ваши вопросы.\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - начать работу\n"
        "/menu - показать главное меню\n"
        "/help - показать эту справку\n"
        "/status - проверить статус подключения\n\n"
        "<b>Кнопки меню:</b>\n"
        "• ℹ️ Информация для проекта - информация о проекте\n"
        "• 🔍 Поиск - режим поиска\n"
        "• 🏠 Главное меню - вернуться в главное меню\n\n"
        "Также просто напишите любой текст, и бот ответит!"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_menu())

@dp.message(Command("status"))
async def status_handler(message: types.Message):
    """
    Проверка статуса подключения к Yandex GPT
    """
    status_msg = await message.answer("🔍 Проверяю подключение к Yandex GPT...")
    
    # Проверяем формат ключей
    if YANDEX_API_KEY.startswith("your_") or YANDEX_FOLDER_ID.startswith("your_"):
        await status_msg.edit_text("❌ Ключи не настроены. Замените YANDEX_API_KEY и YANDEX_FOLDER_ID в коде.")
        return
    
    # Тестовый запрос
    test_result = await ask_yandex_gpt("Ответь одним словом: 'работает'")
    
    if "работает" in test_result.lower() or "work" in test_result.lower():
        await status_msg.edit_text("✅ Yandex GPT подключен и работает отлично!")
    else:
        await status_msg.edit_text(f"❌ Проблема с подключением:\n{test_result}")

@dp.message(lambda message: message.text == "ℹ️ Информация для проекта")
async def project_info_handler(message: types.Message):
    """
    Обработчик кнопки "Информация для проекта"
    """
    project_info = (
        "📋 <b>Информация о проекте</b>\n\n"
        "🤖 <b>Название:</b> Yandex GPT AI Ассистент\n"
        "📝 <b>Описание:</b> Умный бот-ассистент с интеграцией Yandex GPT\n"
        "🔧 <b>Технологии:</b>\n"
        "   • Python 3.8+\n"
        "   • Aiogram 3.x (асинхронный фреймворк для Telegram)\n"
        "   • Yandex GPT API\n"
        "   • aiohttp для асинхронных HTTP запросов\n\n"
        "⚡ <b>Возможности:</b>\n"
        "   • Интеллектуальные ответы на вопросы\n"
        "   • Поиск информации\n"
        "   • Поддержка диалога\n"
        "   • Умное контекстное понимание\n\n"
        "👨‍💻 <b>Разработчик:</b> Fram1se\n\n"
        "Для поиска информации нажмите кнопку <b>🔍 Поиск</b> или просто напишите свой вопрос!"
    )
    await message.answer(project_info, parse_mode="HTML", reply_markup=get_back_to_menu_keyboard())

@dp.message(lambda message: message.text == "🔍 Поиск")
async def search_handler(message: types.Message):
    """
    Обработчик кнопки "Поиск"
    """
    search_info = (
        "🔍 <b>Режим поиска активирован!</b>\n\n"
        "Теперь вы можете задавать любые вопросы:\n\n"
        "• Научные вопросы\n"
        "• Технические консультации\n"
        "• Помощь с кодом\n"
        "• Образовательные темы\n"
        "• И многое другое!\n\n"
        "Просто напишите ваш вопрос ниже 👇\n\n"
        "Чтобы вернуться в меню, используйте кнопку <b>🏠 Главное меню</b>"
    )
    await message.answer(search_info, parse_mode="HTML", reply_markup=get_back_to_menu_keyboard())

@dp.message(lambda message: message.text == "🏠 Главное меню")
async def back_to_menu_handler(message: types.Message):
    """
    Обработчик кнопки "Главное меню"
    """
    welcome_back_text = (
        "🏠 Добро пожаловать в главное меню!\n\n"
        "Рад снова вас видеть! 😊\n\n"
        "Выберите нужный раздел:"
    )
    await message.answer(welcome_back_text, reply_markup=get_main_menu())

@dp.message()
async def message_handler(message: types.Message):
    """
    Обработчик всех текстовых сообщений
    """
    user_text = message.text.strip()
    
    # Игнорируем пустые сообщения
    if not user_text:
        return
    
    # Если сообщение не является командой меню, обрабатываем как запрос к GPT
    if user_text not in ["ℹ️ Информация для проекта", "🔍 Поиск", "🏠 Главное меню"]:
        # Отправляем статус "печатает"
        await bot.send_chat_action(message.chat.id, "typing")
        
        # Отправляем сообщение о обработке
        status_msg = await message.answer("🤔 Думаю...")
        
        # Получаем ответ от Yandex GPT
        response = await ask_yandex_gpt(user_text)
        
        # Отправляем ответ
        await status_msg.edit_text(response)

async def main():
    """
    Главная функция
    """
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import logging
import aiohttp
import asyncio
import re
from urllib.parse import quote

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- Импорт базы данных ---
from database import db

API_TOKEN = "8171207811:AAGPMC93yKCM_KOmzJ5cr0WxgLJs3ycO5MQ"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Обновленное главное меню (пункт 6) ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Поиск")],
        [KeyboardButton(text="📜 История поиска"), KeyboardButton(text="📊 Моя статистика")],
        [KeyboardButton(text="ℹ️ Информация о проекте")]
    ],
    resize_keyboard=True
)

# --- Кнопка "Главное меню" ---
back_to_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)

# --- Функции для анализа сложных запросов ---
def analyze_complex_query(text: str) -> dict:
    """
    Анализирует сложные запросы и определяет тип поиска
    """
    text_lower = text.lower()
    
    # Определяем тип запроса
    query_type = "general"
    search_terms = []
    
    # Поиск различий между двумя понятиями
    difference_patterns = [
        r'разница между (.+) и (.+)',
        r'чем отличается (.+) от (.+)',
        r'отличие (.+) от (.+)',
        r'сравнение (.+) и (.+)',
        r'(.+) vs (.+)',
        r'(.+) или (.+)'
    ]
    
    for pattern in difference_patterns:
        match = re.search(pattern, text_lower)
        if match:
            query_type = "difference"
            search_terms = [match.group(1).strip(), match.group(2).strip()]
            break
    
    # Поиск истории
    history_patterns = [
        r'история (.+)',
        r'когда появил(ся|ась|ось) (.+)',
        r'основани(е|я) (.+)',
        r'создани(е|я) (.+)'
    ]
    
    if not search_terms:
        for pattern in history_patterns:
            match = re.search(pattern, text_lower)
            if match:
                query_type = "history"
                search_terms = [match.group(1).strip()]
                break
    
    # Поиск фактов/информации
    if not search_terms:
        query_type = "general"
        search_terms = [text.strip()]
    
    return {
        "type": query_type,
        "terms": search_terms,
        "original": text
    }

async def fetch_difference_info(term1: str, term2: str) -> str:
    """
    Ищет различия между двумя понятиями
    """
    headers = {
        "User-Agent": "BrandHelperBot/1.0",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Ищем информацию по обоим терминам
        info1 = await fetch_single_term_info(term1, session)
        info2 = await fetch_single_term_info(term2, session)
        
        if not info1 and not info2:
            return f"❌ Не удалось найти информацию ни о '{term1}', ни о '{term2}'"
        
        result = f"<b>Сравнение: {term1} vs {term2}</b>\n\n"
        
        if info1:
            result += f"<b>{term1}:</b>\n{info1}\n\n"
        else:
            result += f"<b>{term1}:</b>\nИнформация не найдена\n\n"
            
        if info2:
            result += f"<b>{term2}:</b>\n{info2}\n\n"
        else:
            result += f"<b>{term2}:</b>\nИнформация не найдена\n\n"
        
        # Добавляем ключевые различия если есть информация по обоим
        if info1 and info2:
            result += "🔍 <b>Ключевые различия:</b>\n"
            # Здесь можно добавить логику для выделения конкретных различий
            result += "• Это разные понятия/объекты/явления\n"
            result += "• Имеют различное происхождение и применение\n"
            result += "• Отличаются по характеристикам и свойствам\n"
        
        return result

async def fetch_single_term_info(term: str, session: aiohttp.ClientSession) -> str:
    """
    Ищет информацию об одном термине
    """
    try:
        # Пробуем русскую Википедию
        search_url = "https://ru.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": term, "format": "json"}
        async with session.get(search_url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                search_results = data.get("query", {}).get("search", [])
                if search_results:
                    page_title = search_results[0]["title"]
                    qtitle = quote(page_title, safe='')
                    summary_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{qtitle}"
                    async with session.get(summary_url) as sresp:
                        if sresp.status == 200:
                            sdata = await sresp.json()
                            extract = sdata.get("extract")
                            if extract:
                                clean_text = re.sub(r"\s*\(.*?\)", "", extract)
                                clean_text = re.sub(r"\[\d+\]", "", clean_text)
                                sentences = clean_text.split(". ")
                                short_text = ". ".join(sentences[:3]) + "."
                                return short_text
    except Exception:
        logger.exception(f"Ошибка при поиске информации о {term}")
    
    return ""

async def fetch_history_info(term: str) -> str:
    """
    Ищет историческую информацию о термине
    """
    headers = {
        "User-Agent": "BrandHelperBot/1.0",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Специальный поиск с акцентом на историю
            search_query = f"история {term}"
            search_url = "https://ru.wikipedia.org/w/api.php"
            params = {"action": "query", "list": "search", "srsearch": search_query, "format": "json"}
            async with session.get(search_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    if search_results:
                        page_title = search_results[0]["title"]
                        qtitle = quote(page_title, safe='')
                        summary_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{qtitle}"
                        async with session.get(summary_url) as sresp:
                            if sresp.status == 200:
                                sdata = await sresp.json()
                                extract = sdata.get("extract")
                                url = sdata.get("content_urls", {}).get("desktop", {}).get("page", "")
                                if extract:
                                    # Ищем исторические факты в тексте
                                    history_keywords = ['основан', 'создан', 'появился', 'история', 'год', 'век']
                                    sentences = extract.split(". ")
                                    history_sentences = []
                                    
                                    for sentence in sentences:
                                        if any(keyword in sentence.lower() for keyword in history_keywords):
                                            history_sentences.append(sentence)
                                    
                                    if history_sentences:
                                        result = ". ".join(history_sentences[:5]) + "."
                                        clean_result = re.sub(r"\s*\(.*?\)", "", result)
                                        clean_result = re.sub(r"\[\d+\]", "", clean_result)
                                        return f"<b>История: {term}</b>\n\n{clean_result}\n\n🔗 <a href='{url}'>Подробнее</a>"
        except Exception:
            logger.exception(f"Ошибка при поиске истории {term}")
    
    return f"❌ Не удалось найти историческую информацию о '{term}'"

# --- Обновленный обработчик start (пункт 5) ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user = message.from_user
    # Сохраняем пользователя в БД
    db.add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    await message.answer("👋 Привет! Я твой главный помощник в поиске информации 0w0. Выбери действие:", reply_markup=main_menu)

@dp.message(F.text == "🔎 Поиск")
async def search_start(message: types.Message):
    await message.answer("Напишите что хотите узнать, и я найду самую важную информацию!\n\nНапример:\n• Разница между iPhone и Android\n• История Microsoft\n• Сравнение Python и Java\n• Что такое искусственный интеллект\n• Или просто вписываете слова",
                         reply_markup=back_to_menu)

@dp.message(F.text == "ℹ️ Информация о проекте")
async def project_info(message: types.Message):
    text = (
        "✨ <b>Brend AI</b> ✨\n\n"
        "ИИ-ассистент который поможет вам узнать всю важную и нужную информацию.\n"
        "📖 Вы узнаете историю, важные факты и отличия между вещами.\n"
        "🧠 Если хотите узнать что-то новое и полезное — вам сюда!\n"
        "(ИИ-ассистент разработан Fram1se)"
    )
    await message.answer(text, reply_markup=back_to_menu)

# --- Новые обработчики для статистики и истории (пункт 5) ---
@dp.message(F.text == "📊 Моя статистика")
async def user_stats(message: types.Message):
    """Показывает статистику пользователя"""
    stats = db.get_user_stats(message.from_user.id)
    
    text = f"📊 <b>Ваша статистика</b>\n\n"
    text += f"🔍 Всего поисков: <b>{stats['total_searches']}</b>\n"
    
    if stats['query_types']:
        text += "\n<b>По типам запросов:</b>\n"
        for query_type, count in stats['query_types'].items():
            type_name = {
                'general': 'Обычный поиск',
                'difference': 'Сравнение',
                'history': 'История'
            }.get(query_type, query_type)
            text += f"• {type_name}: {count}\n"
    
    if stats['first_search']:
        text += f"\n📅 Первый поиск: {stats['first_search'][:10]}"
    
    await message.answer(text, reply_markup=back_to_menu)

@dp.message(F.text == "📜 История поиска")
async def search_history(message: types.Message):
    """Показывает историю поиска пользователя"""
    history = db.get_user_search_history(message.from_user.id, limit=10)
    
    if not history:
        await message.answer("📜 Вы еще не совершали поисковых запросов.", reply_markup=back_to_menu)
        return
    
    text = "📜 <b>Ваша история поиска</b>\n\n"
    for i, item in enumerate(history, 1):
        type_icon = {
            'general': '🔍',
            'difference': '⚖️', 
            'history': '📚'
        }.get(item['query_type'], '🔍')
        
        text += f"{i}. {type_icon} <code>{item['query_text']}</code>\n"
        text += f"   📅 {item['created_at'][:16]} | 📊 {item['result_count']} рез.\n\n"
    
    await message.answer(text, reply_markup=back_to_menu)

@dp.message(F.text == "🏠 Главное меню")
async def return_to_menu(message: types.Message):
    await message.answer("👋 Вы снова в главном меню!", reply_markup=main_menu)

# --- Обновленный обработчик brand_handler (пункт 5) ---
@dp.message(F.text)
async def brand_handler(message: types.Message):
    user_text = message.text.strip()
    user = message.from_user

    # Если это служебная кнопка
    if user_text in ["🏠 Главное меню", "📊 Моя статистика", "📜 История поиска"]:
        # Эти обработчики уже есть выше
        return

    status_msg = await message.answer(f"🔎 Анализирую запрос...")

    try:
        # Анализируем сложный запрос
        analyzed = analyze_complex_query(user_text)
        
        # Сохраняем запрос в БД
        query_id = db.add_search_query(user.id, user_text, analyzed["type"])
        db.increment_user_search_count(user.id)
        
        if analyzed["type"] == "difference" and len(analyzed["terms"]) == 2:
            await status_msg.edit_text(f"🔍 Сравниваю '{analyzed['terms'][0]}' и '{analyzed['terms'][1]}'...")
            result = await fetch_difference_info(analyzed['terms'][0], analyzed['terms'][1])
            # Сохраняем результат в БД
            if query_id != -1:
                db.add_search_result(query_id, "comparison", f"{analyzed['terms'][0]} vs {analyzed['terms'][1]}", result, "")
        
        elif analyzed["type"] == "history":
            await status_msg.edit_text(f"📚 Ищу историю '{analyzed['terms'][0]}'...")
            result = await fetch_history_info(analyzed['terms'][0])
            if query_id != -1:
                db.add_search_result(query_id, "wikipedia", analyzed['terms'][0], result, "")
        
        else:
            await status_msg.edit_text(f"🔎 Ищу информацию о '{user_text}'...")
            result = await fetch_brand_info(user_text)
            if query_id != -1 and result:
                # Сохраняем результат общего поиска
                db.add_search_result(query_id, "wikipedia", user_text, result, "")

        if result:
            await status_msg.edit_text(result)
            await message.answer("Хотите узнать что-то ещё?", reply_markup=back_to_menu)
        else:
            await status_msg.edit_text("😔 К сожалению, я не нашёл достаточно информации.")
            await message.answer("Хотите попробовать другой запрос?", reply_markup=back_to_menu)

    except Exception as e:
        logger.exception("Ошибка при обработке запроса:")
        await status_msg.edit_text("❌ Произошла ошибка при поиске информации.")
        await message.answer("Попробуйте другой запрос.", reply_markup=back_to_menu)

# --- Оригинальная функция поиска (оставь без изменений) ---
async def fetch_brand_info(brand: str) -> str:
    headers = {
        "User-Agent": "BrandHelperBot/1.0 (https://t.me/YourBotUsername)",
        "Accept": "application/json"
    }
    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        # --- Русская Википедия ---
        try:
            search_url = "https://ru.wikipedia.org/w/api.php"
            params = {"action": "query", "list": "search", "srsearch": brand, "format": "json"}
            async with session.get(search_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    if search_results:
                        page_title = search_results[0]["title"]
                        qtitle = quote(page_title, safe='')
                        summary_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{qtitle}"
                        async with session.get(summary_url) as sresp:
                            if sresp.status == 200:
                                sdata = await sresp.json()
                                extract = sdata.get("extract")
                                url = sdata.get("content_urls", {}).get("desktop", {}).get("page", "")
                                if extract:
                                    return clean_summary(page_title, extract, url)
        except Exception:
            logger.exception("Ошибка при запросе к русской Википедии:")

        # --- Английская Википедия ---
        try:
            search_url_en = "https://en.wikipedia.org/w/api.php"
            params = {"action": "query", "list": "search", "srsearch": brand, "format": "json"}
            async with session.get(search_url_en, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    if search_results:
                        page_title = search_results[0]["title"]
                        qtitle = quote(page_title, safe='')
                        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{qtitle}"
                        async with session.get(summary_url) as sresp:
                            if sresp.status == 200:
                                sdata = await sresp.json()
                                extract = sdata.get("extract")
                                url = sdata.get("content_urls", {}).get("desktop", {}).get("page", "")
                                if extract:
                                    return clean_summary(page_title, extract, url)
        except Exception:
            logger.exception("Ошибка при запросе к английской Википедии:")

        # --- DuckDuckGo ---
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={quote(brand)}&format=json&lang=ru"
            async with session.get(ddg_url) as resp:
                if resp.status == 200:
                    dd = await resp.json()
                    text = dd.get("AbstractText") or (dd.get("RelatedTopics") and dd["RelatedTopics"][0].get("Text"))
                    if text:
                        short = re.sub(r"\s*\(.*?\)", "", text)
                        short = re.sub(r"\[\d+\]", "", short)
                        short_sent = ". ".join(short.split(". ")[:6]) + "."
                        if len(short_sent) > 900:
                            short_sent = short_sent[:900].rsplit(".", 1)[0] + "."
                        return f"<b>{brand}</b>\n\n{short_sent}\n\n🔗 DuckDuckGo"
        except Exception:
            logger.exception("Ошибка при запросе к DuckDuckGo")

    return ""

def clean_summary(title: str, text: str, url: str) -> str:
    clean_text = re.sub(r"\s*\(.*?\)", "", text)
    clean_text = re.sub(r"\[\d+\]", "", clean_text)
    sentences = clean_text.split(". ")
    short_text = ". ".join(sentences[:6]) + "."
    if len(short_text) > 900:
        short_text = short_text[:900].rsplit(".", 1)[0] + "."
    return f"<b>{title}</b>\n\n{short_text}\n\n🔗 <a href='{url}'>Подробнее</a>"

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import logging
import aiohttp
import asyncio
import re
from urllib.parse import quote

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "8171207811:AAGPMC93yKCM_KOmzJ5cr0WxgLJs3ycO5MQ"  # <-- вставь свой токен

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Привет! Напиши название бренда, и я найду самую важную информацию.")


@dp.message(F.text)
async def brand_handler(message: types.Message):
    brand = message.text.strip()
    status_msg = await message.answer(f"🔎 Ищу информацию о бренде <b>{brand}</b>...")

    try:
        result = await asyncio.wait_for(fetch_brand_info(brand), timeout=13)
        if result:
            await status_msg.edit_text(result)
            return
    except asyncio.TimeoutError:
        result = None
    except Exception as e:
        logger.exception("Ошибка при быстром поиске:")
        result = None

    steps = [
        ("⏳ Ищу... [25%]", 3),
        ("⏳ Ищу... [50%]", 3),
        ("⏳ Ищу... [75%]", 3),
        ("⏳ Почти готово... [100%]", 4)
    ]

    for text, delay in steps:
        await asyncio.sleep(delay)
        try:
            await status_msg.edit_text(f"{text}\n\n<b>{brand}</b>")
        except Exception:
            pass

    if result:
        await status_msg.edit_text(result)
    else:
        final = await fetch_brand_info(brand)
        if final:
            await status_msg.edit_text(final)
        else:
            await status_msg.edit_text("😔 К сожалению, я не нашёл достаточно информации.")


async def fetch_brand_info(brand: str) -> str:
    headers = {
        "User-Agent": "BrandHelperBot/1.0 (https://t.me/YourBotUsername) Python aiohttp",
        "Accept": "application/json"
    }
    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        # --- 1) Русская Википедия ---
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

        # --- 2) Английская Википедия ---
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

        # --- 3) DuckDuckGo ---
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

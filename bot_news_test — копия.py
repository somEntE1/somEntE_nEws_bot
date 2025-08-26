import asyncio
import feedparser
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

# Загружаем .env
load_dotenv()

# Токен телеграмм бота
API_TOKEN = os.getenv("API_TOKEN")

# Лог API KEY
if API_TOKEN is None:
    raise ValueError("❌ Не найден API_TOKEN в .env файле")

# Ссылки для парсинга с известных новостных порталов
RSS_URLS = [
    "https://lenta.ru/rss",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://tass.ru/rss/v2.xml",
    "https://meduza.io/rss/all",
]

# Ключевые слова для фильтра
KEYWORDS = [
    # Общие IT и технологии
    "it", "айти", "технолог", "цифров", "программ", "софт", "гаджет",
    "компьютер", "сервер", "облако", "cloud", "дата-центр", "сеть", "интернет",

    # Интернет и связь
    "wi-fi", "вайфай", "5g", "4g", "lte", "сетев", "браузер", "vpn", "tor", 
    "ip-адрес", "dns", "провайдер", "трафик", "доступ в интернет",

    # Искусственный интеллект и роботы
    "искусственный интеллект", "нейросеть", "нейросети", "machine learning", 
    "ml", "deep learning", "ai", "chatgpt", "робот", "автоматизация",

    # Кибербезопасность и политика интернета
    "кибер", "кибербезопасность", "кибератака", "хакер", "взлом", "ddos", 
    "шифрование", "vpn", "firewall", "антивирус", "блокировка сайтов", 
    "цензура", "роскомнадзор", "регулирование интернета", "закон о рунете",

    # Соцсети и платформы
    "facebook", "meta", "instagram", "youtube", "telegram", "whatsapp", 
    "vk", "вконтакте", "социальные сети", "соцсеть", "twitter", "x.com",

    # Финтех и цифровая экономика
    "финтех", "финтеха", "криптовалюта", "биткоин", "bitcoin", "ethereum", 
    "блокчейн", "майнинг", "цифровой рубль", "электронные деньги", 
    "онлайн-банкинг", "безналичная оплата",

    # Гос. регулирование и законы
    "цифровая трансформация", "цифровая экономика", "законопроект", 
    "регулирование", "цифровые сервисы", "импортозамещение", 
    "российское по", "реестр отечественного по", "закон о персональных данных",

    # Персональные данные и приватность
    "big data", "большие данные", "персональные данные", "биометрия", 
    "биометрические данные", "утечка данных", "конфиденциальность", 
    "privacy", "cookies", "data protection", "gdpr",

    # Инновации
    "стартап", "venture", "венчур", "инновации", "научные разработки", 
    "технопарк", "сколково", "iot", "интернет вещей", "умный дом", 
    "wearable", "дрон", "беспилотник"

    # Общая политика
    "политика", "власть", "правительство", "госдума", "совет федерации",
    "закон", "законопроект", "реформа", "выборы", "депутат", "министр",
    "парламент", "политик", "сенатор", "президент", "премьер",
    "оппозиция", "коалиция", "референдум", "инициатива",
    
    # Россия
    "кремль", "мид", "силовики", "песков", "шойгу", "лавров", "медведев",
    "санкции", "россия", "мосгордума", "спч", "фсб", "росгвардия",

    # Международка
    "нато", "оон", "ес", "евросоюз", "госдеп", "белый дом", "конгресс", 
    "байден", "трамп", "макрон", "шольц", "зеленский", "пентагон",
    "международные отношения", "санкции", "эмбарго", "геополитика",

    # Безопасность и конфликты
    "армия", "военные", "операция", "конфликт", "мирные переговоры",
    "международный суд", "терроризм", "оборонка", "мобилизация",
    "спецслужбы", "киберугрозы",

    # Английские (часто встречаются в новостях)
    "politics", "government", "law", "parliament", "senate", "minister", 
    "president", "prime minister", "elections", "reform", "sanctions",
    "nato", "eu", "un", "white house", "congress"
]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище отправленных новостей, чтобы не слать повторно
sent_links = set()
USERS = set()

def get_full_text(url):
    """Парсим полный текст новости с сайта"""
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # Заголовок
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Без заголовка"
        # Абзацы текста
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        full_text = f"{title}\n\n" + "\n\n".join(paragraphs[:10])

        return title, full_text
    except Exception as e:
        return "Ошибка", f"Ошибка парсинга: {e}"
def contains_keywords(text):
    """Проверяем наличие ключевых слов"""
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in KEYWORDS)

async def fetch_news():
    while True:
        for url in RSS_URLS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link not in sent_links:
                    # Берём полный текст
                    title, full_text = get_full_text(entry.link)

                    if contains_keywords(title) or contains_keywords(full_text):
                        # Отправка всем пользователям
                        for user_id in USERS:
                            try:
                                await bot.send_message(user_id, f"{full_text}\n\n{entry.link}")
                            except Exception as e:
                                print(f"Ошибка при отправке: {e}")
                                
                    sent_links.add(entry.link)
        await asyncio.sleep(120)  # проверка каждые 2 минут

@dp.message(Command("start"))
async def start(message: types.Message):
    USERS.add(message.from_user.id)
    await message.answer("Привет! Я буду присылать тебе новости автоматически.")

async def main():
    asyncio.create_task(fetch_news())
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
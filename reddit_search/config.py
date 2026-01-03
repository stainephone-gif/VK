"""
Конфигурация для поиска постов в Reddit API
"""

# Релевантные сабреддиты для поиска
TARGET_SUBREDDITS = [
    'Midjourney',
    'StableDiffusion',
    'Genealogy',
    'PhotoRestoration',
    'Colorization',
    'estoration',  # r/estoration - photo restoration
    'AncestryDNA',
    'OldSchoolCool',
    'dalle2',
    'ChatGPT',
    'ArtificialIntelligence',
    'GAN',
    'deepdream',
    'weirddalle',
    'MachineLearning',
    'ComputerVision',
    'ImageRestoration',
]

# Ключевые слова для поиска (английский)
SEARCH_KEYWORDS_EN = [
    'AI restored family photo',
    'neural network grandparents photo',
    'Midjourney family portrait',
    'restored old family picture',
    'AI generated ancestor',
    'stable diffusion family',
    'colorized family photo AI',
    'brought back family member',
    'AI recreated relative',
    'neural network lost family photo',
]

# Ключевые слова (русский - для мультиязычных сабреддитов)
SEARCH_KEYWORDS_RU = [
    'нейросеть восстановила фото',
    'AI семейные фотографии',
    'Midjourney предки',
    'восстановление старых фото',
]

# Объединенный список
SEARCH_KEYWORDS = SEARCH_KEYWORDS_EN + SEARCH_KEYWORDS_RU

# Параметры поиска
SEARCH_CONFIG = {
    'posts_per_subreddit': 100,   # Постов из каждого сабреддита
    'posts_per_keyword': 50,      # Постов на каждое ключевое слово
    'comments_per_post': 20,      # Комментариев для анализа
    'min_upvotes': 5,             # Минимум upvotes
    'min_comments': 1,            # Минимум комментариев
    'time_filter': 'all',         # all, year, month, week, day
    'sort_by': 'relevance',       # relevance, hot, top, new, comments
}

# Критерии для остановки сбора
STOP_CRITERIA = {
    'min_cases': 7,               # Минимум найденных кейсов
    'min_en_cases': 5,            # Минимум англоязычных кейсов
}

# Шаблон карточки для результатов
CARD_TEMPLATE = """## КЕЙС {number}

**Источник:** {url}
**Автор:** {author}
**Дата:** {date}
**Платформа:** Reddit
**Сабреддит:** {subreddit}

**Контекст:**
{context}

**Мотивация:**
{motivation}

**Процесс:**
{process}

**Результат:**
{result}

**Рефлексия автора:**
{reflection}

**Социальный контекст:**
{social_context}

**Медиа-логика:** {media_logic}

**Цитаты (ключевые):**
{quotes}

**Топ комментарии:**
{top_comments}

**Скриншот:** {screenshot_status}

---

"""

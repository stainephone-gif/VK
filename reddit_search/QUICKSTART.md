# 🚀 Быстрый старт - Reddit Search

## За 5 минут до первого запуска

### Шаг 1: Установите зависимости
```bash
pip install -r requirements.txt
```

### Шаг 2: Создайте Reddit приложение

1. Откройте: https://www.reddit.com/prefs/apps
2. Нажмите **"create another app..."** (внизу страницы)
3. Заполните:
   - **name**: `AI Photo Research` (или любое другое)
   - **type**: ⚪ выберите **"script"**
   - **redirect uri**: `http://localhost:8080`
4. Нажмите **"create app"**

### Шаг 3: Скопируйте credentials

После создания приложения вы увидите:

```
AI Photo Research
[personal use script]

dkj39fkDK3kd          ← это ваш CLIENT_ID
secret: 3kdK_dkf93kDKF...   ← это ваш CLIENT_SECRET
```

**Скопируйте:**
- Строку под названием → **CLIENT_ID**
- Строку после "secret:" → **CLIENT_SECRET**

### Шаг 4: Настройте .env файл

```bash
cp .env.example .env
```

Откройте `.env` (блокнотом или любым редактором):

```
REDDIT_CLIENT_ID=dkj39fkDK3kd
REDDIT_CLIENT_SECRET=3kdK_dkf93kDKF...
REDDIT_USER_AGENT=AI_Family_Photo_Research/1.0 (by /u/ваш_username)
```

Замените:
- `dkj39fkDK3kd` → ваш CLIENT_ID
- `3kdK_dkf93kDKF...` → ваш CLIENT_SECRET
- `ваш_username` → ваше имя пользователя Reddit

### Шаг 5: Проверьте настройки

```bash
python setup_check.py
```

Если все ✅ - можно запускать!

### Шаг 6: Запустите поиск

```bash
python reddit_search.py
```

## 📊 Результаты

После завершения смотрите:
- `results/results.md` - карточки кейсов
- `results/results.json` - данные в JSON

## ⚙️ Настройка поиска

Отредактируйте `config.py`:

```python
# Добавьте свои сабреддиты
TARGET_SUBREDDITS.append('YourSubreddit')

# Измените параметры
SEARCH_CONFIG = {
    'posts_per_subreddit': 200,  # больше постов
    'min_upvotes': 10,           # только популярные
    'time_filter': 'year',       # только за год
}
```

## 🆘 Проблемы?

**Ошибка: "credentials не настроены"**
- Проверьте что скопировали CLIENT_ID и SECRET полностью
- Убедитесь что нет лишних пробелов в .env

**Ошибка: "401 Unauthorized"**
- Проверьте что выбрали тип приложения **"script"**
- Пересоздайте приложение если нужно

**Ничего не найдено:**
- Попробуйте изменить `time_filter` на 'year' или 'all'
- Уменьшите `min_upvotes` до 1
- Проверьте список сабреддитов в config.py

**Медленно работает:**
- Уменьшите `posts_per_subreddit` до 50
- Ограничьте количество сабреддитов

## 📖 Полная документация

См. [README.md](README.md)

## 🔗 Используете VK и Reddit?

Запустите оба скрипта для полного охвата:
- **VK** → русскоязычный контент
- **Reddit** → англоязычный контент

Объединяйте results.json для комплексного анализа!

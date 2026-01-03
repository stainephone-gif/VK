#!/usr/bin/env python3
"""
Скрипт для проверки настроек и готовности к работе с Reddit API
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Проверка наличия .env файла"""
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("\n📝 Создайте файл .env на основе .env.example:")
        print("   cp .env.example .env")
        print("\n🔑 Затем добавьте ваши Reddit API credentials в файл .env")
        return False
    print("✅ Файл .env найден")
    return True

def check_credentials():
    """Проверка наличия credentials"""
    load_dotenv()
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')

    if not client_id or client_id == 'your_client_id_here':
        print("❌ REDDIT_CLIENT_ID не настроен!")
        print("\n🔑 Получите credentials:")
        print("   1. Перейдите на https://www.reddit.com/prefs/apps")
        print("   2. Нажмите 'create another app...'")
        print("   3. Выберите тип 'script'")
        print("   4. Заполните название и redirect uri: http://localhost:8080")
        print("   5. Скопируйте client_id (под названием приложения)")
        print("   6. Скопируйте client_secret")
        print("   7. Добавьте их в файл .env")
        return False

    if not client_secret or client_secret == 'your_client_secret_here':
        print("❌ REDDIT_CLIENT_SECRET не настроен!")
        return False

    if not user_agent or 'your_username' in user_agent:
        print("⚠️  REDDIT_USER_AGENT не настроен должным образом")
        print("   Рекомендуется формат: 'AppName/Version (by /u/YourUsername)'")

    print("✅ Reddit credentials найдены")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   User Agent: {user_agent}")
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    try:
        import praw
        print("✅ praw установлен")
        print(f"   Версия: {praw.__version__}")
    except ImportError:
        print("❌ praw не установлен")
        print("\n📦 Установите зависимости:")
        print("   pip install -r requirements.txt")
        return False

    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv установлен")
    except ImportError:
        print("❌ python-dotenv не установлен")
        print("\n📦 Установите зависимости:")
        print("   pip install -r requirements.txt")
        return False

    return True

def test_api_connection():
    """Тестовое подключение к Reddit API"""
    try:
        import praw
        from dotenv import load_dotenv

        load_dotenv()
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')

        if not client_id or client_id == 'your_client_id_here':
            return False

        # Создаем экземпляр Reddit (read-only режим)
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        # Тестовый запрос
        subreddit = reddit.subreddit('test')
        test_post = next(subreddit.hot(limit=1))

        print("✅ Подключение к Reddit API успешно")
        print(f"   Тестовый запрос выполнен: получен пост из r/test")
        print(f"   Режим: {'Авторизованный' if reddit.read_only == False else 'Read-only'}")
        return True

    except Exception as e:
        print(f"❌ Ошибка подключения к Reddit API: {e}")
        print("\n💡 Возможные причины:")
        print("   - Неверный client_id или client_secret")
        print("   - Проблемы с интернет-соединением")
        print("   - Некорректный user_agent")
        return False

def main():
    """Основная функция проверки"""
    print("=" * 60)
    print("ПРОВЕРКА НАСТРОЕК REDDIT API")
    print("=" * 60)
    print()

    checks = [
        ("Проверка файла .env", check_env_file),
        ("Проверка зависимостей", check_dependencies),
        ("Проверка Reddit credentials", check_credentials),
        ("Тестовое подключение к API", test_api_connection),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 60)
        result = check_func()
        results.append(result)

    print()
    print("=" * 60)

    if all(results):
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print()
        print("🚀 Вы готовы к запуску:")
        print("   python reddit_search.py")
        return 0
    else:
        print("❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print()
        print("📖 Смотрите инструкции выше для исправления проблем")
        print("📚 Подробная документация: README.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())

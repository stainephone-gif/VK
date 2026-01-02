#!/usr/bin/env python3
"""
Скрипт для проверки настроек и готовности к работе с VK API
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
        print("\n🔑 Затем добавьте ваш VK токен в файл .env")
        return False
    print("✅ Файл .env найден")
    return True

def check_token():
    """Проверка наличия токена"""
    load_dotenv()
    token = os.getenv('VK_ACCESS_TOKEN')

    if not token or token == 'your_access_token_here':
        print("❌ VK токен не настроен!")
        print("\n🔑 Получите токен:")
        print("   1. Перейдите на https://vkhost.github.io/")
        print("   2. Выберите 'VK Admin' или создайте приложение")
        print("   3. Получите токен с правами: groups, wall, offline")
        print("   4. Добавьте токен в файл .env")
        return False

    print("✅ VK токен найден")
    print(f"   Токен начинается с: {token[:20]}...")
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    try:
        import vk_api
        print("✅ vk-api установлен")
    except ImportError:
        print("❌ vk-api не установлен")
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
    """Тестовое подключение к VK API"""
    try:
        import vk_api
        from dotenv import load_dotenv

        load_dotenv()
        token = os.getenv('VK_ACCESS_TOKEN')

        if not token or token == 'your_access_token_here':
            return False

        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()

        # Простой тестовый запрос
        result = vk.users.get(user_ids=[1])

        print("✅ Подключение к VK API успешно")
        print(f"   Тестовый запрос выполнен: получен пользователь {result[0]['first_name']} {result[0]['last_name']}")
        return True

    except vk_api.exceptions.ApiError as e:
        print(f"❌ Ошибка VK API: {e}")
        print("\n💡 Возможные причины:")
        print("   - Неверный токен")
        print("   - Истек срок действия токена")
        print("   - Недостаточные права доступа")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("=" * 60)
    print("ПРОВЕРКА НАСТРОЕК VK API")
    print("=" * 60)
    print()

    checks = [
        ("Проверка файла .env", check_env_file),
        ("Проверка зависимостей", check_dependencies),
        ("Проверка VK токена", check_token),
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
        print("   python vk_search.py")
        return 0
    else:
        print("❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print()
        print("📖 Смотрите инструкции выше для исправления проблем")
        print("📚 Подробная документация: README.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())

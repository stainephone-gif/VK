#!/usr/bin/env python3
"""
Скрипт для автоматического сбора постов из ВКонтакте
по ключевым словам, связанным с AI-восстановлением семейных фото
"""

import vk_api
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
import config

# Загрузка переменных окружения
load_dotenv()


class VKSearcher:
    """Класс для поиска и сбора постов из ВКонтакте"""

    def __init__(self):
        """Инициализация VK API"""
        self.access_token = os.getenv('VK_ACCESS_TOKEN')
        self.api_version = os.getenv('VK_API_VERSION', '5.131')

        if not self.access_token:
            raise ValueError("VK_ACCESS_TOKEN не найден. Создайте файл .env на основе .env.example")

        # Создание сессии VK API
        self.vk_session = vk_api.VkApi(token=self.access_token, api_version=self.api_version)
        self.vk = self.vk_session.get_api()

        # Счетчики для контроля лимитов API
        self.request_count = 0
        self.last_request_time = time.time()

        # Результаты поиска
        self.found_cases = []

    def _rate_limit(self):
        """Контроль частоты запросов к API (максимум 3 запроса в секунду)"""
        self.request_count += 1
        if self.request_count >= 3:
            elapsed = time.time() - self.last_request_time
            if elapsed < 1:
                time.sleep(1 - elapsed)
            self.request_count = 0
            self.last_request_time = time.time()

    def search_groups(self, query: str, count: int = 20) -> List[Dict[str, Any]]:
        """
        Поиск групп по запросу

        Args:
            query: Поисковый запрос
            count: Количество групп для получения

        Returns:
            Список найденных групп
        """
        print(f"Поиск групп по запросу: '{query}'")
        self._rate_limit()

        try:
            response = self.vk.groups.search(
                q=query,
                count=min(count, 1000),
                sort=0  # По популярности
            )
            groups = response.get('items', [])
            print(f"  Найдено {len(groups)} групп")
            return groups
        except Exception as e:
            print(f"  Ошибка при поиске групп: {e}")
            return []

    def get_wall_posts(self, owner_id: int, count: int = 100, keyword: str = None) -> List[Dict[str, Any]]:
        """
        Получение постов со стены группы или пользователя

        Args:
            owner_id: ID владельца стены (отрицательный для групп)
            count: Количество постов
            keyword: Ключевое слово для фильтрации

        Returns:
            Список постов
        """
        self._rate_limit()

        try:
            response = self.vk.wall.get(
                owner_id=owner_id,
                count=min(count, 100),
                filter='owner'
            )
            posts = response.get('items', [])

            # Фильтрация по ключевому слову
            if keyword:
                filtered_posts = []
                for post in posts:
                    text = post.get('text', '').lower()
                    if any(word.lower() in text for word in keyword.split()):
                        filtered_posts.append(post)
                return filtered_posts

            return posts
        except Exception as e:
            print(f"  Ошибка при получении постов: {e}")
            return []

    def search_posts(self, query: str, count: int = 50) -> List[Dict[str, Any]]:
        """
        Поиск постов по ключевым словам

        Args:
            query: Поисковый запрос
            count: Количество постов

        Returns:
            Список найденных постов
        """
        print(f"Поиск постов по запросу: '{query}'")
        self._rate_limit()

        try:
            response = self.vk.newsfeed.search(
                q=query,
                count=min(count, 200)
            )
            posts = response.get('items', [])
            print(f"  Найдено {len(posts)} постов")
            return posts
        except Exception as e:
            print(f"  Ошибка при поиске постов: {e}")
            return []

    def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """
        Получение информации о пользователе

        Args:
            user_id: ID пользователя

        Returns:
            Информация о пользователе
        """
        self._rate_limit()

        try:
            users = self.vk.users.get(
                user_ids=[user_id],
                fields='city,country,occupation'
            )
            return users[0] if users else {}
        except Exception as e:
            print(f"  Ошибка при получении информации о пользователе: {e}")
            return {}

    def get_group_info(self, group_id: int) -> Dict[str, Any]:
        """
        Получение информации о группе

        Args:
            group_id: ID группы (положительное число)

        Returns:
            Информация о группе
        """
        self._rate_limit()

        try:
            groups = self.vk.groups.getById(
                group_ids=[group_id],
                fields='description,members_count'
            )
            return groups[0] if groups else {}
        except Exception as e:
            print(f"  Ошибка при получении информации о группе: {e}")
            return {}

    def get_comments(self, owner_id: int, post_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """
        Получение комментариев к посту

        Args:
            owner_id: ID владельца поста
            post_id: ID поста
            count: Количество комментариев

        Returns:
            Список комментариев
        """
        self._rate_limit()

        try:
            response = self.vk.wall.getComments(
                owner_id=owner_id,
                post_id=post_id,
                count=min(count, 100),
                sort='desc'
            )
            return response.get('items', [])
        except Exception as e:
            print(f"  Ошибка при получении комментариев: {e}")
            return []

    def analyze_post(self, post: Dict[str, Any], case_number: int) -> Dict[str, Any]:
        """
        Анализ поста и извлечение релевантной информации

        Args:
            post: Данные поста
            case_number: Номер кейса

        Returns:
            Структурированная информация о кейсе
        """
        # Извлечение базовых данных
        owner_id = post.get('owner_id', post.get('from_id', 0))
        post_id = post.get('id', 0)
        text = post.get('text', '')
        date = datetime.fromtimestamp(post.get('date', 0)).strftime('%Y-%m-%d %H:%M:%S')

        # URL поста
        if owner_id < 0:
            url = f"https://vk.com/wall{owner_id}_{post_id}"
        else:
            url = f"https://vk.com/wall{owner_id}_{post_id}"

        # Информация об авторе
        author_name = "Неизвестно"
        author_info = ""

        if owner_id < 0:
            # Это группа
            group_info = self.get_group_info(abs(owner_id))
            author_name = group_info.get('name', f'club{abs(owner_id)}')
            author_info = f"Группа: {author_name}"
        else:
            # Это пользователь
            user_info = self.get_user_info(owner_id)
            first_name = user_info.get('first_name', '')
            last_name = user_info.get('last_name', '')
            author_name = f"{first_name} {last_name}".strip() or f"id{owner_id}"

            city = user_info.get('city', {}).get('title', '')
            occupation = user_info.get('occupation', {}).get('name', '')
            author_info = f"Пользователь: {author_name}"
            if city:
                author_info += f", {city}"
            if occupation:
                author_info += f", {occupation}"

        # Получение комментариев
        comments = self.get_comments(owner_id, post_id, count=10)
        comments_text = "\n".join([f"- {c.get('text', '')[:100]}" for c in comments[:5]])

        # Статистика
        likes = post.get('likes', {}).get('count', 0)
        reposts = post.get('reposts', {}).get('count', 0)
        comments_count = post.get('comments', {}).get('count', 0)

        # Извлечение цитат (первые 3 предложения или 500 символов)
        quotes = text[:500] if text else "Нет текста"

        # Формирование структурированных данных
        case_data = {
            'number': case_number,
            'url': url,
            'author': author_name,
            'date': date,
            'context': author_info,
            'motivation': self._extract_motivation(text),
            'process': self._extract_process(text),
            'result': self._extract_result(text),
            'reflection': self._extract_reflection(text),
            'social_context': f"Лайки: {likes}, Репосты: {reposts}, Комментарии: {comments_count}\n\nПримеры комментариев:\n{comments_text}" if comments_text else f"Лайки: {likes}, Репосты: {reposts}, Комментарии: {comments_count}",
            'media_logic': self._determine_media_logic(text),
            'quotes': f"> {quotes}",
            'screenshot_status': 'не сохранён',
            'raw_text': text,
            'stats': {
                'likes': likes,
                'reposts': reposts,
                'comments': comments_count
            }
        }

        return case_data

    def _extract_motivation(self, text: str) -> str:
        """Извлечение мотивации из текста"""
        keywords = ['хотел', 'решил', 'попробовал', 'мечтал', 'восстановить', 'создать', 'увидеть']
        for keyword in keywords:
            if keyword in text.lower():
                # Найти предложение с этим ключевым словом
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        return "Не указано"

    def _extract_process(self, text: str) -> str:
        """Извлечение описания процесса"""
        tech_keywords = ['midjourney', 'dall-e', 'stable diffusion', 'нейросеть', 'ai', 'промпт']
        found_tech = []
        for keyword in tech_keywords:
            if keyword in text.lower():
                found_tech.append(keyword.upper())

        if found_tech:
            return f"Использованные технологии: {', '.join(found_tech)}"
        return "Технология не указана"

    def _extract_result(self, text: str) -> str:
        """Извлечение описания результата"""
        result_keywords = ['получилось', 'результат', 'вышло', 'создал', 'восстановил']
        for keyword in result_keywords:
            if keyword in text.lower():
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        return "Результат описан в тексте поста"

    def _extract_reflection(self, text: str) -> str:
        """Извлечение рефлексии автора"""
        reflection_keywords = ['чувствую', 'думаю', 'понял', 'осознал', 'удивительно', 'невероятно', 'эмоции']
        for keyword in reflection_keywords:
            if keyword in text.lower():
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        return "Эмоциональная рефлексия не выражена явно"

    def _determine_media_logic(self, text: str) -> str:
        """Определение медиа-логики"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['восстановил', 'дополнил', 'улучшил']):
            return 'Дополнение'
        elif any(word in text_lower for word in ['преобразовал', 'изменил', 'трансформировал']):
            return 'Трансформация'
        elif any(word in text_lower for word in ['объединил', 'совместил', 'смешал']):
            return 'Рекомбинация'
        return 'Не определено'

    def run_search(self):
        """Запуск основного процесса поиска"""
        print("=" * 80)
        print("ЗАПУСК ПОИСКА ПОСТОВ В ВКОНТАКТЕ")
        print("=" * 80)
        print()

        all_posts = []

        # 1. Поиск по ключевым словам
        print("Этап 1: Поиск постов по ключевым словам")
        print("-" * 80)
        for keyword in config.SEARCH_KEYWORDS:
            posts = self.search_posts(keyword, config.SEARCH_CONFIG['posts_per_keyword'])
            all_posts.extend(posts)
            time.sleep(0.5)

        print(f"\nВсего найдено постов по ключевым словам: {len(all_posts)}")
        print()

        # 2. Поиск в группах
        print("Этап 2: Поиск постов в тематических группах")
        print("-" * 80)
        for query in config.GROUP_SEARCH_QUERIES:
            groups = self.search_groups(query, config.SEARCH_CONFIG['groups_per_query'])

            for group in groups[:10]:  # Берем топ-10 групп
                group_id = -group['id']  # Для групп ID отрицательный
                group_name = group.get('name', 'Unknown')
                print(f"  Сбор постов из группы: {group_name}")

                for keyword in config.SEARCH_KEYWORDS:
                    posts = self.get_wall_posts(group_id, config.SEARCH_CONFIG['posts_per_group'], keyword)
                    all_posts.extend(posts)
                    time.sleep(0.5)

        print(f"\nОбщее количество найденных постов: {len(all_posts)}")
        print()

        # 3. Фильтрация и анализ постов
        print("Этап 3: Анализ и фильтрация постов")
        print("-" * 80)

        # Удаление дубликатов
        unique_posts = {}
        for post in all_posts:
            post_id = f"{post.get('owner_id', post.get('from_id', 0))}_{post.get('id', 0)}"
            if post_id not in unique_posts:
                unique_posts[post_id] = post

        print(f"Уникальных постов: {len(unique_posts)}")

        # Фильтрация по минимальной активности
        filtered_posts = []
        for post in unique_posts.values():
            likes = post.get('likes', {}).get('count', 0)
            comments = post.get('comments', {}).get('count', 0)

            if (likes >= config.SEARCH_CONFIG['min_likes'] and
                comments >= config.SEARCH_CONFIG['min_comments']):
                filtered_posts.append(post)

        print(f"Постов после фильтрации: {len(filtered_posts)}")
        print()

        # 4. Создание карточек для релевантных постов
        print("Этап 4: Создание структурированных карточек")
        print("-" * 80)

        for idx, post in enumerate(filtered_posts[:20], 1):  # Обрабатываем первые 20
            print(f"Обработка кейса {idx}/20...")
            case_data = self.analyze_post(post, idx)
            self.found_cases.append(case_data)

        print(f"\nСоздано карточек: {len(self.found_cases)}")
        print()

        return self.found_cases

    def save_results(self, output_file: str = 'results.md'):
        """
        Сохранение результатов в файл

        Args:
            output_file: Имя выходного файла
        """
        os.makedirs('results', exist_ok=True)
        output_path = os.path.join('results', output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# РЕЗУЛЬТАТЫ ПОИСКА: AI-ВОССТАНОВЛЕНИЕ СЕМЕЙНЫХ ФОТО\n\n")
            f.write(f"Дата поиска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Найдено кейсов: {len(self.found_cases)}\n\n")
            f.write("=" * 80 + "\n\n")

            for case in self.found_cases:
                card = config.CARD_TEMPLATE.format(**case)
                f.write(card)

        print(f"Результаты сохранены в: {output_path}")

        # Также сохраняем в JSON для дальнейшей обработки
        json_path = os.path.join('results', 'results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.found_cases, f, ensure_ascii=False, indent=2)

        print(f"JSON данные сохранены в: {json_path}")


def main():
    """Основная функция"""
    try:
        searcher = VKSearcher()
        cases = searcher.run_search()
        searcher.save_results()

        print()
        print("=" * 80)
        print("ПОИСК ЗАВЕРШЕН")
        print("=" * 80)
        print(f"Найдено релевантных кейсов: {len(cases)}")
        print("Проверьте папку 'results/' для просмотра результатов")

    except Exception as e:
        print(f"Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

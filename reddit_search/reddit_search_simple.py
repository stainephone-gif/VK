#!/usr/bin/env python3
"""
Упрощенная версия скрипта для сбора постов из Reddit
БЕЗ регистрации разработчика - использует публичный JSON API
"""

import requests
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import config

class SimpleRedditSearcher:
    """Упрощенный класс для поиска постов в Reddit без OAuth"""

    def __init__(self):
        """Инициализация"""
        self.session = requests.Session()
        # User agent для соблюдения правил Reddit
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.found_cases = []
        self.request_count = 0
        self.last_request_time = time.time()

    def _rate_limit(self):
        """Контроль частоты запросов (2 запроса в секунду для публичного API)"""
        self.request_count += 1
        if self.request_count >= 2:
            elapsed = time.time() - self.last_request_time
            if elapsed < 1:
                time.sleep(1 - elapsed)
            self.request_count = 0
            self.last_request_time = time.time()

    def search_subreddit(self, subreddit_name: str, query: str = None, limit: int = 100) -> List[Dict]:
        """
        Поиск постов в сабреддите через публичный JSON API

        Args:
            subreddit_name: Название сабреддита
            query: Поисковый запрос
            limit: Количество постов

        Returns:
            Список постов
        """
        try:
            if query:
                # Поиск по запросу
                url = f"https://www.reddit.com/r/{subreddit_name}/search.json"
                params = {
                    'q': query,
                    'restrict_sr': 'on',
                    'sort': 'relevance',
                    'limit': min(limit, 100)
                }
                print(f"  Поиск в r/{subreddit_name} по запросу: '{query}'")
            else:
                # Топ посты
                url = f"https://www.reddit.com/r/{subreddit_name}/hot.json"
                params = {'limit': min(limit, 100)}
                print(f"  Получение постов из r/{subreddit_name}")

            self._rate_limit()
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                print(f"    Найдено {len(posts)} постов")
                return [post['data'] for post in posts]
            else:
                print(f"    Ошибка {response.status_code}")
                return []

        except Exception as e:
            print(f"  Ошибка при поиске в r/{subreddit_name}: {e}")
            return []

    def get_post_comments(self, subreddit: str, post_id: str, limit: int = 20) -> List[Dict]:
        """
        Получение комментариев к посту

        Args:
            subreddit: Название сабреддита
            post_id: ID поста
            limit: Количество комментариев

        Returns:
            Список комментариев
        """
        try:
            url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
            params = {'limit': limit}

            self._rate_limit()
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    comments_data = data[1].get('data', {}).get('children', [])
                    comments = []

                    for comment in comments_data[:limit]:
                        comment_data = comment.get('data', {})
                        if comment_data.get('body'):
                            comments.append({
                                'author': comment_data.get('author', '[deleted]'),
                                'body': comment_data.get('body', ''),
                                'score': comment_data.get('score', 0),
                                'created': datetime.fromtimestamp(
                                    comment_data.get('created_utc', 0)
                                ).strftime('%Y-%m-%d %H:%M:%S')
                            })

                    return comments
            return []

        except Exception as e:
            print(f"  Ошибка при получении комментариев: {e}")
            return []

    def analyze_post(self, post: Dict, case_number: int) -> Dict[str, Any]:
        """
        Анализ поста и извлечение информации

        Args:
            post: Данные поста
            case_number: Номер кейса

        Returns:
            Структурированная информация
        """
        # Базовая информация
        title = post.get('title', '')
        selftext = post.get('selftext', '')
        author_name = post.get('author', '[deleted]')
        subreddit_name = post.get('subreddit', '')
        post_id = post.get('id', '')
        created = datetime.fromtimestamp(post.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S')
        permalink = post.get('permalink', '')
        url = f"https://reddit.com{permalink}"

        # Статистика
        upvotes = post.get('score', 0)
        num_comments = post.get('num_comments', 0)
        upvote_ratio = post.get('upvote_ratio', 0)

        # Контекст
        context = f"Автор: u/{author_name}\n"
        context += f"Сабреддит: r/{subreddit_name}"

        # Получение комментариев
        comments = self.get_post_comments(subreddit_name, post_id, 10)

        # Топ комментарии
        top_comments = sorted(comments, key=lambda x: x['score'], reverse=True)[:5]
        top_comments_text = ""
        for i, comment in enumerate(top_comments, 1):
            top_comments_text += f"\n{i}. u/{comment['author']} (↑{comment['score']}):\n"
            comment_preview = comment['body'][:200] + "..." if len(comment['body']) > 200 else comment['body']
            top_comments_text += f"   {comment_preview}\n"

        # Полный текст
        full_text = f"{title}\n\n{selftext}"

        # Цитаты
        quotes = f"> **{title}**\n\n"
        if selftext:
            quotes += f"> {selftext[:500]}..." if len(selftext) > 500 else f"> {selftext}"

        # Социальный контекст
        social_context = f"Upvotes: {upvotes} (ratio: {upvote_ratio:.0%})\n"
        social_context += f"Комментарии: {num_comments}\n"
        social_context += f"Engagement: {upvotes + num_comments} interactions"

        # Формирование данных кейса
        case_data = {
            'number': case_number,
            'url': url,
            'author': f"u/{author_name}",
            'date': created,
            'subreddit': f"r/{subreddit_name}",
            'context': context,
            'motivation': self._extract_motivation(full_text),
            'process': self._extract_process(full_text),
            'result': self._extract_result(full_text),
            'reflection': self._extract_reflection(full_text),
            'social_context': social_context,
            'media_logic': self._determine_media_logic(full_text),
            'quotes': quotes,
            'top_comments': top_comments_text if top_comments_text else "Нет комментариев",
            'screenshot_status': 'не сохранён',
            'raw_title': title,
            'raw_text': selftext,
            'stats': {
                'upvotes': upvotes,
                'comments': num_comments,
                'upvote_ratio': upvote_ratio
            }
        }

        return case_data

    def _extract_motivation(self, text: str) -> str:
        """Извлечение мотивации"""
        keywords = ['wanted', 'decided', 'tried', 'dreamed', 'restore', 'create', 'see']
        sentences = text.replace('\n', '. ').split('.')
        for keyword in keywords:
            for sentence in sentences:
                if keyword in sentence.lower() and len(sentence.strip()) > 20:
                    return sentence.strip()
        return "Не указано явно"

    def _extract_process(self, text: str) -> str:
        """Извлечение описания процесса"""
        tech_keywords = {
            'midjourney': 'Midjourney',
            'dall-e': 'DALL-E',
            'dalle': 'DALL-E',
            'stable diffusion': 'Stable Diffusion',
            'neural network': 'Neural Network',
            'ai': 'AI',
            'chatgpt': 'ChatGPT',
        }

        found_tech = []
        text_lower = text.lower()

        for keyword, tech_name in tech_keywords.items():
            if keyword in text_lower and tech_name not in found_tech:
                found_tech.append(tech_name)

        if found_tech:
            return f"Использованные технологии: {', '.join(found_tech)}"
        return "Технология не указана"

    def _extract_result(self, text: str) -> str:
        """Извлечение результата"""
        result_keywords = ['result', 'outcome', 'turned out', 'created', 'restored']
        sentences = text.replace('\n', '. ').split('.')
        for keyword in result_keywords:
            for sentence in sentences:
                if keyword in sentence.lower() and len(sentence.strip()) > 20:
                    return sentence.strip()
        return "Результат описан в тексте поста"

    def _extract_reflection(self, text: str) -> str:
        """Извлечение рефлексии"""
        reflection_keywords = ['feel', 'think', 'realize', 'amazing', 'incredible', 'emotional']
        sentences = text.replace('\n', '. ').split('.')
        for keyword in reflection_keywords:
            for sentence in sentences:
                if keyword in sentence.lower() and len(sentence.strip()) > 20:
                    return sentence.strip()
        return "Эмоциональная рефлексия не выражена явно"

    def _determine_media_logic(self, text: str) -> str:
        """Определение медиа-логики"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['restor', 'fix', 'repair', 'enhance']):
            return 'Дополнение'
        elif any(word in text_lower for word in ['transform', 'change', 'convert']):
            return 'Трансформация'
        elif any(word in text_lower for word in ['combin', 'merge', 'mix']):
            return 'Рекомбинация'
        elif any(word in text_lower for word in ['generat', 'creat', 'imagine']):
            return 'Генерация'
        return 'Не определено'

    def run_search(self):
        """Запуск поиска"""
        print("=" * 80)
        print("ЗАПУСК УПРОЩЕННОГО ПОИСКА В REDDIT (БЕЗ РЕГИСТРАЦИИ)")
        print("=" * 80)
        print()

        all_posts = []
        seen_ids = set()

        # 1. Поиск в сабреддитах
        print("Этап 1: Поиск в тематических сабреддитах")
        print("-" * 80)

        for subreddit_name in config.TARGET_SUBREDDITS[:10]:  # Ограничиваем для упрощенной версии
            posts = self.search_subreddit(subreddit_name, limit=50)

            for post in posts:
                post_id = post.get('id')
                if post_id and post_id not in seen_ids:
                    all_posts.append(post)
                    seen_ids.add(post_id)

            time.sleep(1)  # Задержка между сабреддитами

        print(f"\nВсего найдено постов: {len(all_posts)}")
        print()

        # 2. Фильтрация
        print("Этап 2: Фильтрация постов")
        print("-" * 80)

        filtered_posts = []
        for post in all_posts:
            upvotes = post.get('score', 0)
            num_comments = post.get('num_comments', 0)

            if (upvotes >= config.SEARCH_CONFIG['min_upvotes'] and
                num_comments >= config.SEARCH_CONFIG['min_comments']):
                filtered_posts.append(post)

        # Сортировка по популярности
        filtered_posts.sort(key=lambda p: p.get('score', 0) + p.get('num_comments', 0), reverse=True)

        print(f"Постов после фильтрации: {len(filtered_posts)}")
        print()

        # 3. Создание карточек
        print("Этап 3: Создание карточек")
        print("-" * 80)

        for idx, post in enumerate(filtered_posts[:15], 1):
            print(f"Обработка кейса {idx}/15...")
            try:
                case_data = self.analyze_post(post, idx)
                self.found_cases.append(case_data)
            except Exception as e:
                print(f"  Ошибка: {e}")
                continue

        print(f"\nСоздано карточек: {len(self.found_cases)}")
        print()

        return self.found_cases

    def save_results(self, output_file: str = 'results.md'):
        """Сохранение результатов"""
        os.makedirs('results', exist_ok=True)
        output_path = os.path.join('results', output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# РЕЗУЛЬТАТЫ ПОИСКА REDDIT: AI-ВОССТАНОВЛЕНИЕ СЕМЕЙНЫХ ФОТО\n\n")
            f.write(f"Дата поиска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Найдено кейсов: {len(self.found_cases)}\n")
            f.write("Метод: Упрощенный поиск (публичный JSON API)\n\n")
            f.write("=" * 80 + "\n\n")

            for case in self.found_cases:
                card = config.CARD_TEMPLATE.format(**case)
                f.write(card)

        print(f"Результаты сохранены в: {output_path}")

        # JSON
        json_path = os.path.join('results', 'results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.found_cases, f, ensure_ascii=False, indent=2)

        print(f"JSON данные сохранены в: {json_path}")


def main():
    """Основная функция"""
    try:
        print("УПРОЩЕННАЯ ВЕРСИЯ - не требует регистрации разработчика!")
        print("Ограничения: меньше запросов в минуту, только публичные данные\n")

        searcher = SimpleRedditSearcher()
        cases = searcher.run_search()
        searcher.save_results()

        print()
        print("=" * 80)
        print("ПОИСК ЗАВЕРШЕН")
        print("=" * 80)
        print(f"Найдено релевантных кейсов: {len(cases)}")
        print("Проверьте папку 'results/' для просмотра результатов")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

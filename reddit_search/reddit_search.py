#!/usr/bin/env python3
"""
Скрипт для автоматического сбора постов из Reddit
по ключевым словам, связанным с AI-восстановлением семейных фото
"""

import praw
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
import config

# Загрузка переменных окружения
load_dotenv()


class RedditSearcher:
    """Класс для поиска и сбора постов из Reddit"""

    def __init__(self):
        """Инициализация Reddit API"""
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT')

        # Опциональные параметры для авторизации
        self.username = os.getenv('REDDIT_USERNAME')
        self.password = os.getenv('REDDIT_PASSWORD')

        if not self.client_id or not self.client_secret:
            raise ValueError("REDDIT_CLIENT_ID и REDDIT_CLIENT_SECRET не найдены. Создайте файл .env на основе .env.example")

        # Создание экземпляра Reddit
        if self.username and self.password:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                username=self.username,
                password=self.password
            )
        else:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )

        # Результаты поиска
        self.found_cases = []

    def search_subreddit(self, subreddit_name: str, query: str = None, limit: int = 100) -> List[Any]:
        """
        Поиск постов в конкретном сабреддите

        Args:
            subreddit_name: Название сабреддита
            query: Поисковый запрос (если None, берет топ посты)
            limit: Количество постов

        Returns:
            Список постов
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            if query:
                print(f"  Поиск в r/{subreddit_name} по запросу: '{query}'")
                posts = list(subreddit.search(
                    query,
                    sort=config.SEARCH_CONFIG['sort_by'],
                    time_filter=config.SEARCH_CONFIG['time_filter'],
                    limit=limit
                ))
            else:
                print(f"  Получение топ-постов из r/{subreddit_name}")
                posts = list(subreddit.hot(limit=limit))

            print(f"    Найдено {len(posts)} постов")
            return posts

        except Exception as e:
            print(f"  Ошибка при поиске в r/{subreddit_name}: {e}")
            return []

    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Any]:
        """
        Глобальный поиск по Reddit по ключевому слову

        Args:
            keyword: Ключевое слово
            limit: Количество результатов

        Returns:
            Список постов
        """
        print(f"Глобальный поиск по запросу: '{keyword}'")
        try:
            posts = list(self.reddit.subreddit('all').search(
                keyword,
                sort=config.SEARCH_CONFIG['sort_by'],
                time_filter=config.SEARCH_CONFIG['time_filter'],
                limit=limit
            ))
            print(f"  Найдено {len(posts)} постов")
            return posts
        except Exception as e:
            print(f"  Ошибка при глобальном поиске: {e}")
            return []

    def get_post_comments(self, post, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Получение комментариев к посту

        Args:
            post: Объект поста
            limit: Количество комментариев

        Returns:
            Список комментариев
        """
        try:
            post.comments.replace_more(limit=0)  # Разворачиваем "load more comments"
            comments = []

            for comment in post.comments.list()[:limit]:
                if hasattr(comment, 'body'):
                    comments.append({
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created': datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                    })

            return comments
        except Exception as e:
            print(f"  Ошибка при получении комментариев: {e}")
            return []

    def get_author_info(self, author_name: str) -> Dict[str, Any]:
        """
        Получение информации об авторе

        Args:
            author_name: Имя пользователя

        Returns:
            Информация об авторе
        """
        try:
            if author_name == '[deleted]':
                return {'username': '[deleted]', 'karma': 0}

            author = self.reddit.redditor(author_name)
            return {
                'username': author.name,
                'karma': author.link_karma + author.comment_karma,
                'created': datetime.fromtimestamp(author.created_utc).strftime('%Y-%m-%d'),
                'is_verified': author.verified if hasattr(author, 'verified') else False
            }
        except Exception as e:
            print(f"  Ошибка при получении информации об авторе: {e}")
            return {'username': author_name, 'karma': 0}

    def analyze_post(self, post, case_number: int) -> Dict[str, Any]:
        """
        Анализ поста и извлечение релевантной информации

        Args:
            post: Объект поста Reddit
            case_number: Номер кейса

        Returns:
            Структурированная информация о кейсе
        """
        # Базовая информация
        title = post.title
        selftext = post.selftext if hasattr(post, 'selftext') else ''
        author_name = str(post.author) if post.author else '[deleted]'
        subreddit_name = str(post.subreddit)
        created = datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S')
        url = f"https://reddit.com{post.permalink}"

        # Статистика
        upvotes = post.score
        num_comments = post.num_comments
        upvote_ratio = post.upvote_ratio if hasattr(post, 'upvote_ratio') else 0

        # Информация об авторе
        author_info = self.get_author_info(author_name)
        author_karma = author_info.get('karma', 0)

        context = f"Автор: u/{author_name}\n"
        context += f"Karma: {author_karma}\n"
        if 'created' in author_info:
            context += f"Аккаунт создан: {author_info['created']}\n"
        context += f"Сабреддит: r/{subreddit_name}"

        # Получение комментариев
        comments = self.get_post_comments(post, config.SEARCH_CONFIG['comments_per_post'])

        # Топ комментарии (по score)
        top_comments = sorted(comments, key=lambda x: x['score'], reverse=True)[:5]
        top_comments_text = ""
        for i, comment in enumerate(top_comments, 1):
            top_comments_text += f"\n{i}. u/{comment['author']} (↑{comment['score']}):\n"
            top_comments_text += f"   {comment['body'][:200]}...\n" if len(comment['body']) > 200 else f"   {comment['body']}\n"

        # Объединенный текст для анализа
        full_text = f"{title}\n\n{selftext}"

        # Извлечение цитат
        quotes = f"> **{title}**\n\n"
        if selftext:
            quotes += f"> {selftext[:500]}..." if len(selftext) > 500 else f"> {selftext}"

        # Социальный контекст
        social_context = f"Upvotes: {upvotes} (ratio: {upvote_ratio:.0%})\n"
        social_context += f"Комментарии: {num_comments}\n"
        social_context += f"Engagement: {upvotes + num_comments} interactions"

        # Формирование структурированных данных
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
                'upvote_ratio': upvote_ratio,
                'author_karma': author_karma
            }
        }

        return case_data

    def _extract_motivation(self, text: str) -> str:
        """Извлечение мотивации из текста"""
        keywords = ['wanted', 'decided', 'tried', 'dreamed', 'restore', 'create', 'see',
                   'хотел', 'решил', 'попробовал', 'мечтал']
        text_lower = text.lower()

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
            'prompt': 'Промпт-инжиниринг',
            'chatgpt': 'ChatGPT',
            'gpt-4': 'GPT-4',
            'нейросеть': 'Нейросеть',
        }

        found_tech = []
        text_lower = text.lower()

        for keyword, tech_name in tech_keywords.items():
            if keyword in text_lower:
                if tech_name not in found_tech:
                    found_tech.append(tech_name)

        if found_tech:
            return f"Использованные технологии: {', '.join(found_tech)}"
        return "Технология не указана"

    def _extract_result(self, text: str) -> str:
        """Извлечение описания результата"""
        result_keywords = ['result', 'outcome', 'turned out', 'created', 'restored',
                          'получилось', 'результат', 'вышло']

        sentences = text.replace('\n', '. ').split('.')
        for keyword in result_keywords:
            for sentence in sentences:
                if keyword in sentence.lower() and len(sentence.strip()) > 20:
                    return sentence.strip()
        return "Результат описан в тексте поста"

    def _extract_reflection(self, text: str) -> str:
        """Извлечение рефлексии автора"""
        reflection_keywords = ['feel', 'think', 'realize', 'understand', 'amazing', 'incredible',
                              'emotional', 'чувствую', 'думаю', 'понял', 'удивительно']

        sentences = text.replace('\n', '. ').split('.')
        for keyword in reflection_keywords:
            for sentence in sentences:
                if keyword in sentence.lower() and len(sentence.strip()) > 20:
                    return sentence.strip()
        return "Эмоциональная рефлексия не выражена явно"

    def _determine_media_logic(self, text: str) -> str:
        """Определение медиа-логики"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['restor', 'fix', 'repair', 'enhance', 'восстановил', 'улучшил']):
            return 'Дополнение'
        elif any(word in text_lower for word in ['transform', 'change', 'convert', 'преобразовал', 'изменил']):
            return 'Трансформация'
        elif any(word in text_lower for word in ['combin', 'merge', 'mix', 'объединил', 'смешал']):
            return 'Рекомбинация'
        elif any(word in text_lower for word in ['generat', 'creat', 'imagine', 'создал', 'сгенерировал']):
            return 'Генерация'
        return 'Не определено'

    def run_search(self):
        """Запуск основного процесса поиска"""
        print("=" * 80)
        print("ЗАПУСК ПОИСКА ПОСТОВ В REDDIT")
        print("=" * 80)
        print()

        all_posts = []
        seen_ids = set()

        # 1. Поиск в целевых сабреддитах
        print("Этап 1: Поиск в тематических сабреддитах")
        print("-" * 80)

        for subreddit_name in config.TARGET_SUBREDDITS:
            print(f"\nОбработка r/{subreddit_name}:")

            # Получаем топ посты из сабреддита
            posts = self.search_subreddit(
                subreddit_name,
                limit=config.SEARCH_CONFIG['posts_per_subreddit']
            )

            for post in posts:
                if post.id not in seen_ids:
                    all_posts.append(post)
                    seen_ids.add(post.id)

            time.sleep(0.5)  # Небольшая задержка

        print(f"\nВсего найдено постов в сабреддитах: {len(all_posts)}")
        print()

        # 2. Поиск по ключевым словам
        print("Этап 2: Поиск по ключевым словам")
        print("-" * 80)

        for keyword in config.SEARCH_KEYWORDS[:10]:  # Ограничиваем для скорости
            posts = self.search_by_keyword(keyword, config.SEARCH_CONFIG['posts_per_keyword'])

            for post in posts:
                if post.id not in seen_ids:
                    all_posts.append(post)
                    seen_ids.add(post.id)

            time.sleep(0.5)

        print(f"\nОбщее количество найденных постов: {len(all_posts)}")
        print()

        # 3. Фильтрация постов
        print("Этап 3: Фильтрация постов")
        print("-" * 80)

        filtered_posts = []
        for post in all_posts:
            upvotes = post.score
            num_comments = post.num_comments

            if (upvotes >= config.SEARCH_CONFIG['min_upvotes'] and
                num_comments >= config.SEARCH_CONFIG['min_comments']):
                filtered_posts.append(post)

        # Сортируем по популярности
        filtered_posts.sort(key=lambda p: p.score + p.num_comments, reverse=True)

        print(f"Постов после фильтрации: {len(filtered_posts)}")
        print()

        # 4. Создание карточек
        print("Этап 4: Создание структурированных карточек")
        print("-" * 80)

        for idx, post in enumerate(filtered_posts[:20], 1):  # Обрабатываем первые 20
            print(f"Обработка кейса {idx}/20... (r/{post.subreddit})")
            try:
                case_data = self.analyze_post(post, idx)
                self.found_cases.append(case_data)
            except Exception as e:
                print(f"  Ошибка при обработке: {e}")
                continue

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
            f.write("# РЕЗУЛЬТАТЫ ПОИСКА REDDIT: AI-ВОССТАНОВЛЕНИЕ СЕМЕЙНЫХ ФОТО\n\n")
            f.write(f"Дата поиска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Найдено кейсов: {len(self.found_cases)}\n\n")
            f.write("=" * 80 + "\n\n")

            for case in self.found_cases:
                card = config.CARD_TEMPLATE.format(**case)
                f.write(card)

        print(f"Результаты сохранены в: {output_path}")

        # Также сохраняем в JSON
        json_path = os.path.join('results', 'results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.found_cases, f, ensure_ascii=False, indent=2)

        print(f"JSON данные сохранены в: {json_path}")


def main():
    """Основная функция"""
    try:
        searcher = RedditSearcher()

        # Проверка подключения
        print(f"Подключено к Reddit API")
        print(f"Режим: {'Авторизованный' if searcher.username else 'Только чтение'}")
        print()

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

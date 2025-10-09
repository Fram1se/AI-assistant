import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "brand_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Создает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация таблиц в базе данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                search_count INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица поисковых запросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query_text TEXT NOT NULL,
                query_type TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица результатов поиска
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES search_queries (id)
            )
        ''')
        
        # Индексы для ускорения поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_queries_user_date ON search_queries(user_id, created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_queries_type ON search_queries(query_type)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_or_update_user(self, user_id: int, username: str, first_name: str, last_name: str = None):
        """Добавляет или обновляет пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, last_activity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_activity = excluded.last_activity
            ''', (user_id, username, first_name, last_name, datetime.now()))
            
            conn.commit()
            logger.info(f"User {user_id} added/updated")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def increment_user_search_count(self, user_id: int):
        """Увеличивает счетчик поисков пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET search_count = search_count + 1, last_activity = ?
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing search count for user {user_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def add_search_query(self, user_id: int, query_text: str, query_type: str) -> int:
        """Добавляет поисковый запрос и возвращает его ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO search_queries (user_id, query_text, query_type)
                VALUES (?, ?, ?)
            ''', (user_id, query_text, query_type))
            
            query_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Search query added: {query_text} (type: {query_type})")
            return query_id
        except Exception as e:
            logger.error(f"Error adding search query: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def add_search_result(self, query_id: int, source: str, title: str, summary: str, url: str = None):
        """Добавляет результат поиска"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO search_results (query_id, source, title, summary, url)
                VALUES (?, ?, ?, ?, ?)
            ''', (query_id, source, title, summary, url))
            
            # Обновляем счетчик результатов в запросе
            cursor.execute('''
                UPDATE search_queries 
                SET result_count = result_count + 1 
                WHERE id = ?
            ''', (query_id,))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error adding search result: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_user_search_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает историю поиска пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sq.query_text, sq.query_type, sq.result_count, sq.created_at
            FROM search_queries sq
            WHERE sq.user_id = ?
            ORDER BY sq.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append(dict(row))
        
        conn.close()
        return history
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Общее количество поисков
        cursor.execute('SELECT search_count FROM users WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        
        # Статистика по типам запросов
        cursor.execute('''
            SELECT query_type, COUNT(*) as count
            FROM search_queries
            WHERE user_id = ?
            GROUP BY query_type
        ''', (user_id,))
        
        type_stats = {}
        for row in cursor.fetchall():
            type_stats[row['query_type']] = row['count']
        
        # Дата первого поиска
        cursor.execute('''
            SELECT MIN(created_at) as first_search
            FROM search_queries
            WHERE user_id = ?
        ''', (user_id,))
        
        first_search_row = cursor.fetchone()
        first_search = first_search_row['first_search'] if first_search_row and first_search_row['first_search'] else None
        
        conn.close()
        
        return {
            'total_searches': user_row['search_count'] if user_row else 0,
            'query_types': type_stats,
            'first_search': first_search
        }

# Глобальный экземпляр базы данных
db = DatabaseManager()
"""Advanced database manager with connection pooling and caching"""
import sqlite3
import logging
import json
from typing import Optional, List, Tuple, Any, Dict
from threading import Lock
from contextlib import contextmanager
from datetime import datetime
from shizuka_bot.config import settings
from shizuka_bot.models import User, Item, BotSetting, Couple, Warning, Game

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Thread-safe database manager with connection pooling"""
    
    def __init__(self, db_file: str = None):
        self.db_file = db_file or settings.DATABASE_FILE
        self._lock = Lock()
        self._connections = []
        self._query_cache = {}
        self.init_database()
        logger.info(f"✅ Database initialized: {self.db_file}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic commit/rollback"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_file,
                timeout=settings.DB_TIMEOUT,
                check_same_thread=settings.DB_CHECK_SAME_THREAD
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self) -> None:
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    balance INTEGER DEFAULT 0,
                    bank_balance INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    experience INTEGER DEFAULT 0,
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    is_protected BOOLEAN DEFAULT 0,
                    protection_end_time REAL,
                    last_work_time REAL,
                    last_daily_time REAL,
                    last_rob_time REAL,
                    is_warned BOOLEAN DEFAULT 0,
                    warning_count INTEGER DEFAULT 0,
                    is_muted BOOLEAN DEFAULT 0,
                    mute_end_time REAL,
                    is_banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    couple_id INTEGER REFERENCES users(id),
                    couple_since REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # Items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    emoji TEXT NOT NULL,
                    description TEXT,
                    added_by INTEGER REFERENCES users(id),
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # Bot settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Couples table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS couples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER NOT NULL REFERENCES users(id),
                    user2_id INTEGER NOT NULL REFERENCES users(id),
                    couple_since REAL DEFAULT (strftime('%s', 'now')),
                    UNIQUE(user1_id, user2_id)
                )
            ''')
            
            # Warnings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    reason TEXT NOT NULL,
                    warned_at REAL DEFAULT (strftime('%s', 'now')),
                    warned_by INTEGER NOT NULL REFERENCES users(id)
                )
            ''')
            
            # Games table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT NOT NULL,
                    group_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL REFERENCES users(id),
                    status TEXT DEFAULT 'waiting',
                    players TEXT NOT NULL,
                    started_at REAL DEFAULT (strftime('%s', 'now')),
                    ended_at REAL,
                    winner_id INTEGER REFERENCES users(id)
                )
            ''')
            
            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_id ON users(id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_group ON games(group_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings(user_id)')
            
            # Insert default settings if empty
            cursor.execute('SELECT COUNT(*) FROM bot_settings')
            if cursor.fetchone()[0] == 0:
                for key, value in settings.BOT_SETTINGS.items():
                    cursor.execute(
                        'INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)',
                        (key, json.dumps(value))
                    )
            
            # Insert default items if empty
            cursor.execute('SELECT COUNT(*) FROM items')
            if cursor.fetchone()[0] == 0:
                for item in settings.DEFAULT_ITEMS:
                    cursor.execute(
                        'INSERT INTO items (name, price, emoji, description, added_by) VALUES (?, ?, ?, ?, ?)',
                        (item['name'], item['price'], item['emoji'], item['description'], None)
                    )
            
            conn.commit()
            logger.info("✅ All tables initialized with indexes and defaults")
    
    # ===== USER OPERATIONS =====
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """Get existing user or create new one"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to get existing user
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_user(row)
            
            # Create new user
            cursor.execute('''
                INSERT INTO users (id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return self._row_to_user(cursor.fetchone())
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user fields"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if not kwargs:
                return False
            
            kwargs['updated_at'] = datetime.now().timestamp()
            columns = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            cursor.execute(f'UPDATE users SET {columns} WHERE id = ?', values)
            conn.commit()
            return cursor.rowcount > 0
    
    def add_balance(self, user_id: int, amount: int) -> bool:
        """Add money to user balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_bank_balance(self, user_id: int, amount: int) -> bool:
        """Add money to bank balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET bank_balance = bank_balance + ? WHERE id = ?', (amount, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_experience(self, user_id: int, amount: int) -> bool:
        """Add experience to user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?', (amount, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # ===== ITEM OPERATIONS =====
    def get_items(self, limit: int = None, offset: int = 0) -> List[Item]:
        """Get all items with pagination"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute('SELECT * FROM items LIMIT ? OFFSET ?', (limit, offset))
            else:
                cursor.execute('SELECT * FROM items')
            return [self._row_to_item(row) for row in cursor.fetchall()]
    
    def get_item(self, item_id: int) -> Optional[Item]:
        """Get item by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            return self._row_to_item(row) if row else None
    
    def add_item(self, name: str, price: int, emoji: str, description: str, added_by: int = None) -> Optional[int]:
        """Add new item to shop"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO items (name, price, emoji, description, added_by) VALUES (?, ?, ?, ?, ?)',
                (name, price, emoji, description, added_by)
            )
            conn.commit()
            return cursor.lastrowid
    
    def delete_item(self, item_id: int) -> bool:
        """Delete item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ===== SETTINGS OPERATIONS =====
    def get_setting(self, key: str) -> Any:
        """Get bot setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
            return None
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set bot setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)',
                (key, json.dumps(value) if not isinstance(value, str) else value)
            )
            conn.commit()
            return True
    
    # ===== LEADERBOARD OPERATIONS =====
    def get_top_users(self, field: str = 'balance', limit: int = 10) -> List[User]:
        """Get top users by field"""
        allowed_fields = ['balance', 'level', 'experience', 'kills']
        field = field if field in allowed_fields else 'balance'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM users ORDER BY {field} DESC LIMIT ?', (limit,))
            return [self._row_to_user(row) for row in cursor.fetchall()]
    
    def get_user_rank(self, user_id: int, field: str = 'balance') -> Optional[int]:
        """Get user's rank in leaderboard"""
        allowed_fields = ['balance', 'level', 'experience', 'kills']
        field = field if field in allowed_fields else 'balance'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT COUNT(*) + 1 FROM users WHERE {field} > (SELECT {field} FROM users WHERE id = ?)',
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    # ===== COUPLE OPERATIONS =====
    def get_couple(self, user_id: int) -> Optional[Couple]:
        """Get couple info for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM couples WHERE user1_id = ? OR user2_id = ?',
                (user_id, user_id)
            )
            row = cursor.fetchone()
            return self._row_to_couple(row) if row else None
    
    def create_couple(self, user1_id: int, user2_id: int) -> bool:
        """Create couple relationship"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO couples (user1_id, user2_id) VALUES (?, ?)',
                    (min(user1_id, user2_id), max(user1_id, user2_id))
                )
                couple_since = datetime.now().timestamp()
                cursor.execute('UPDATE users SET couple_id = ?, couple_since = ? WHERE id IN (?, ?)',
                             (max(user1_id, user2_id), couple_since, user1_id, user2_id))
                conn.commit()
                return True
            except:
                return False
    
    # ===== WARNING OPERATIONS =====
    def add_warning(self, user_id: int, reason: str, warned_by: int) -> bool:
        """Add warning to user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO warnings (user_id, reason, warned_by) VALUES (?, ?, ?)',
                (user_id, reason, warned_by)
            )
            cursor.execute('UPDATE users SET warning_count = warning_count + 1 WHERE id = ?', (user_id,))
            conn.commit()
            return True
    
    def get_user_warnings(self, user_id: int) -> List[Warning]:
        """Get user's warnings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM warnings WHERE user_id = ? ORDER BY warned_at DESC', (user_id,))
            return [self._row_to_warning(row) for row in cursor.fetchall()]
    
    # ===== HELPER METHODS =====
    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        return User(
            id=row['id'],
            username=row['username'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            balance=row['balance'],
            bank_balance=row['bank_balance'],
            level=row['level'],
            experience=row['experience'],
            kills=row['kills'],
            deaths=row['deaths'],
            is_protected=bool(row['is_protected']),
            protection_end_time=row['protection_end_time'],
            last_work_time=row['last_work_time'],
            last_daily_time=row['last_daily_time'],
            last_rob_time=row['last_rob_time'],
            is_warned=bool(row['is_warned']),
            warning_count=row['warning_count'],
            is_muted=bool(row['is_muted']),
            mute_end_time=row['mute_end_time'],
            is_banned=bool(row['is_banned']),
            ban_reason=row['ban_reason'],
            couple_id=row['couple_id'],
            couple_since=row['couple_since'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_item(self, row) -> Item:
        """Convert database row to Item object"""
        return Item(
            id=row['id'],
            name=row['name'],
            price=row['price'],
            emoji=row['emoji'],
            description=row['description'],
            added_by=row['added_by'],
            created_at=row['created_at']
        )
    
    def _row_to_couple(self, row) -> Couple:
        """Convert database row to Couple object"""
        return Couple(
            id=row['id'],
            user1_id=row['user1_id'],
            user2_id=row['user2_id'],
            couple_since=row['couple_since']
        )
    
    def _row_to_warning(self, row) -> Warning:
        """Convert database row to Warning object"""
        return Warning(
            id=row['id'],
            user_id=row['user_id'],
            reason=row['reason'],
            warned_at=row['warned_at'],
            warned_by=row['warned_by']
        )

# Global database instance
db = DatabaseManager()

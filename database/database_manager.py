#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器
负责SQLite数据库的连接、查询和管理
"""

import os
import sqlite3
import hashlib
import secrets
from typing import Any, List, Dict, Optional, Tuple
from contextlib import contextmanager


class DatabaseManager:
    """
    数据库管理器类
    提供SQLite数据库的连接、查询和管理功能
    """
    
    _instance = None
    
    def __new__(cls, db_path: str = None):
        """
        单例模式，确保整个应用只有一个数据库连接
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        """
        if self._initialized:
            return
        
        if db_path is None:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(app_dir, 'data', 'app.db')
        
        self.db_path = db_path
        self._connection = None
        self._ensure_data_directory()
        self._connect()
        self._initialize_database()
        self._initialized = True
    
    def _ensure_data_directory(self):
        """
        确保数据目录存在
        """
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def _connect(self):
        """
        连接到SQLite数据库
        """
        try:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._connection.row_factory = sqlite3.Row
            print(f"成功连接到数据库: {self.db_path}")
        except sqlite3.Error as e:
            print(f"连接数据库失败: {e}")
            raise
    
    def _initialize_database(self):
        """
        初始化数据库表结构
        """
        self._create_settings_table()
        self._create_users_table()
        self._create_passwords_table()
    
    def _create_settings_table(self):
        """
        创建设置表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            module TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)"
        self.execute(create_index_sql)
    
    def _create_users_table(self):
        """
        创建用户表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        self.execute(create_index_sql)
        
        self._create_default_user()
    
    def _create_default_user(self):
        """
        创建默认用户
        用户名: user, 密码: 123456
        """
        existing = self.query_one("SELECT id FROM users WHERE username = ?", ("user",))
        
        if not existing:
            password = "123456"
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            self.insert('users', {
                'username': 'user',
                'password_hash': password_hash,
                'salt': salt,
                'is_active': 1
            })
            print("默认用户已创建: user / 123456")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        使用SHA-256哈希密码
        """
        combined = password + salt
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        验证用户密码
        """
        user = self.query_one(
            "SELECT password_hash, salt, is_active FROM users WHERE username = ?",
            (username,)
        )
        
        if not user:
            return False
        
        if user['is_active'] != 1:
            return False
        
        password_hash = self._hash_password(password, user['salt'])
        return password_hash == user['password_hash']
    
    def update_last_login(self, username: str) -> bool:
        """
        更新用户最后登录时间
        """
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return self.update(
            'users',
            {'last_login': now, 'updated_at': 'CURRENT_TIMESTAMP'},
            'username = ?',
            (username,)
        ) > 0
    
    def _create_passwords_table(self):
        """
        创建密码管理表
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            username TEXT,
            password TEXT NOT NULL,
            website TEXT,
            category TEXT DEFAULT '其他',
            notes TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.execute(create_table_sql)
        
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_passwords_title ON passwords(title)"
        self.execute(create_index_sql)
        
        create_category_index_sql = "CREATE INDEX IF NOT EXISTS idx_passwords_category ON passwords(category)"
        self.execute(create_category_index_sql)
    
    @contextmanager
    def get_cursor(self):
        """
        获取数据库游标
        使用上下文管理器确保资源正确释放
        """
        if self._connection is None:
            raise RuntimeError("数据库连接未初始化")
        
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute(self, sql: str, parameters: Tuple = ()) -> int:
        """
        执行SQL语句（INSERT、UPDATE、DELETE等）
        返回受影响的行数
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.rowcount
    
    def execute_many(self, sql: str, parameters: List[Tuple]) -> int:
        """
        批量执行SQL语句
        """
        with self.get_cursor() as cursor:
            cursor.executemany(sql, parameters)
            return cursor.rowcount
    
    def query_one(self, sql: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        查询单行数据
        返回字典形式的结果
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, parameters)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def query_all(self, sql: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        """
        查询多行数据
        返回字典列表
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, parameters)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def query_scalar(self, sql: str, parameters: Tuple = ()) -> Any:
        """
        查询单个值
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, parameters)
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入数据
        返回新插入的行ID
        """
        keys = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in keys])
        columns = ', '.join(keys)
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: Tuple = ()) -> int:
        """
        更新数据
        返回受影响的行数
        """
        keys = list(data.keys())
        values = list(data.values())
        set_clause = ', '.join([f"{key} = ?" for key in keys])
        
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        all_params = values + list(where_params)
        return self.execute(sql, tuple(all_params))
    
    def delete(self, table: str, where: str, where_params: Tuple = ()) -> int:
        """
        删除数据
        返回受影响的行数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        return self.execute(sql, where_params)
    
    def get_setting(self, key: str, default: Any = None, module: str = None) -> Any:
        """
        获取设置值
        """
        if module:
            sql = "SELECT value FROM settings WHERE key = ? AND module = ?"
            result = self.query_one(sql, (key, module))
        else:
            sql = "SELECT value FROM settings WHERE key = ? AND module IS NULL"
            result = self.query_one(sql, (key,))
        
        if result:
            return result['value']
        return default
    
    def set_setting(self, key: str, value: Any, module: str = None) -> bool:
        """
        设置配置值
        """
        existing = self.query_one(
            "SELECT id FROM settings WHERE key = ? AND module IS ?",
            (key, module)
        )
        
        if existing:
            return self.update(
                'settings',
                {'value': str(value), 'updated_at': 'CURRENT_TIMESTAMP'},
                'key = ? AND module IS ?',
                (key, module)
            ) > 0
        else:
            return self.insert(
                'settings',
                {'key': key, 'value': str(value), 'module': module}
            ) > 0
    
    def delete_setting(self, key: str, module: str = None) -> bool:
        """
        删除设置
        """
        if module:
            return self.delete('settings', 'key = ? AND module = ?', (key, module)) > 0
        else:
            return self.delete('settings', 'key = ? AND module IS NULL', (key,)) > 0
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        """
        sql = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = self.query_one(sql, (table_name,))
        return result is not None
    
    def close(self):
        """
        关闭数据库连接
        """
        if self._connection:
            self._connection.close()
            self._connection = None
            print("数据库连接已关闭")
    
    def __del__(self):
        """
        析构函数，确保数据库连接被关闭
        """
        self.close()

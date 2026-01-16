"""
数据库模块

功能:
1. SQLite 数据库连接管理
2. 表结构定义与初始化
3. JSON 到 SQLite 数据迁移
"""
from app.db.connection import get_db, init_db, close_db
from app.db.migration import migrate_from_json

__all__ = ["get_db", "init_db", "close_db", "migrate_from_json"]

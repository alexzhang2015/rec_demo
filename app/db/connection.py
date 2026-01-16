"""
数据库连接管理

功能:
1. SQLite 连接池管理
2. 异步上下文管理器
"""
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.db.schema import SCHEMA_SQL

# 数据库文件路径
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "recommendation.db"

# 全局连接实例（单例模式用于简单场景）
_db_connection: aiosqlite.Connection | None = None


async def init_db() -> None:
    """初始化数据库，创建表结构"""
    global _db_connection

    _db_connection = await aiosqlite.connect(DB_PATH)
    _db_connection.row_factory = aiosqlite.Row

    # 启用外键约束
    await _db_connection.execute("PRAGMA foreign_keys = ON")

    # 执行建表语句
    await _db_connection.executescript(SCHEMA_SQL)
    await _db_connection.commit()

    print(f"[DB] 数据库初始化完成: {DB_PATH}")


async def close_db() -> None:
    """关闭数据库连接"""
    global _db_connection

    if _db_connection:
        await _db_connection.close()
        _db_connection = None
        print("[DB] 数据库连接已关闭")


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接"""
    global _db_connection

    if _db_connection is None:
        await init_db()

    return _db_connection


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[aiosqlite.Connection, None]:
    """数据库连接上下文管理器"""
    db = await get_db()
    try:
        yield db
    finally:
        # 单例模式下不关闭连接，由 close_db 统一管理
        pass

import os
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        dsn = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
            f"{os.getenv('POSTGRES_HOST', 'postgres')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'n8n')}"
        )
        self.pool = await asyncpg.create_pool(
            dsn,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as conn:
            yield conn

    async def init_migrations(self) -> None:
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "migrations", "001_news_tables.sql"
        )
        if os.path.exists(migration_path):
            with open(migration_path) as f:
                sql = f.read()
            async with self.pool.acquire() as conn:
                await conn.execute(sql)


db = Database()

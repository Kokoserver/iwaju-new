import asyncio
from sqlalchemy import select, text
from alembic.config import Config
from alembic import command
import pytest
from db.config import engine
from core import settings


@pytest.mark.asyncio
async def test_alembic_migration():
    async with engine.connect() as conn:
        stmt = text("SELECT COUNT(*) FROM alembic_version")
        result = await conn.execute(stmt)
        result = result.scalar()
        assert result != 0

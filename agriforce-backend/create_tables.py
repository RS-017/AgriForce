"""
create_tables.py — One-shot script to create all DB tables from SQLAlchemy models.
Run: python create_tables.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# Import ALL models so their metadata is registered
import models.users       # noqa: F401
import models.jobs        # noqa: F401
import models.equipment   # noqa: F401
import models.subsidies   # noqa: F401
import models.notifications  # noqa: F401
import models.forecast    # noqa: F401
import models.crops       # noqa: F401
import models.locations   # noqa: F401

from database import Base
from core.config import settings


async def create_all():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("\n✅ All tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_all())

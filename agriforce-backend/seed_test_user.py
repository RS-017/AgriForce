"""seed_test_user.py — Insert a test farmer user directly into the DB."""
import asyncio
import uuid
import bcrypt

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:Martinnanobot@localhost:5432/agriforce"

# ── Test credentials ──────────────────────────────────────────────────────────
TEST_PHONE    = "9000000001"
TEST_EMAIL    = "testfarmer@agriforce.com"
TEST_PASSWORD = "AgriTest@123"
TEST_ROLE     = "FARMER"

async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    hashed = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()
    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    async with async_session() as session:
        # Delete existing test user if already exists (idempotent)
        await session.execute(text("DELETE FROM users WHERE phone = :p OR email = :e"),
                              {"p": TEST_PHONE, "e": TEST_EMAIL})
        await session.commit()

        # Insert user
        await session.execute(text("""
            INSERT INTO users (id, phone, email, hashed_password, role, is_verified, is_active)
            VALUES (:id, :phone, :email, :hashed_password, :role, true, true)
        """), {
            "id": str(user_id),
            "phone": TEST_PHONE,
            "email": TEST_EMAIL,
            "hashed_password": hashed,
            "role": TEST_ROLE,
        })

        # Insert farmer profile
        await session.execute(text("""
            INSERT INTO farmer_profiles (id, user_id, farm_size, primary_crop, district, taluk, land_type)
            VALUES (:id, :user_id, :farm_size, :primary_crop, :district, :taluk, :land_type)
        """), {
            "id": str(profile_id),
            "user_id": str(user_id),
            "farm_size": 5.0,
            "primary_crop": "Rice",
            "district": "Chennai",
            "taluk": "Ambattur",
            "land_type": "IRRIGATED",
        })

        await session.commit()

    await engine.dispose()
    print("\n[OK] Test user created successfully!")
    print("-" * 40)
    print(f"  Phone    : {TEST_PHONE}")
    print(f"  Email    : {TEST_EMAIL}")
    print(f"  Password : {TEST_PASSWORD}")
    print(f"  Role     : {TEST_ROLE}")
    print(f"  User ID  : {user_id}")
    print("-" * 40)

if __name__ == "__main__":
    asyncio.run(seed())

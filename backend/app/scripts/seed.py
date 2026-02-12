"""Seed script for local development database.

Usage:
    python -m app.scripts.seed

Idempotent — safe to run multiple times.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.db.session import AsyncSessionLocal

SEED_USERS = [
    {
        "email": "admin@trendedge.dev",
        "role": "admin",
        "subscription_tier": "team",
        "onboarding_completed": True,
        "onboarding_step": 0,
        "settings": {},
    },
    {
        "email": "free@trendedge.dev",
        "role": "user",
        "subscription_tier": "free",
        "onboarding_completed": True,
        "onboarding_step": 0,
        "settings": {},
    },
    {
        "email": "trader@trendedge.dev",
        "role": "user",
        "subscription_tier": "trader",
        "onboarding_completed": True,
        "onboarding_step": 0,
        "settings": {},
    },
    {
        "email": "pro@trendedge.dev",
        "role": "user",
        "subscription_tier": "pro",
        "onboarding_completed": True,
        "onboarding_step": 0,
        "settings": {},
    },
]


async def seed() -> None:
    """Seed the development database with test data."""
    print("Seeding database...")

    users_created = 0
    users_skipped = 0
    audit_logs_created = 0

    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)

        for user_data in SEED_USERS:
            # Check if user already exists by email (idempotent)
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user is not None:
                users_skipped += 1
                print(f"  User {user_data['email']} already exists, skipping.")
                continue

            # Create user with a generated UUID
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                email=user_data["email"],
                role=user_data["role"],
                subscription_tier=user_data["subscription_tier"],
                onboarding_completed=user_data["onboarding_completed"],
                onboarding_step=user_data["onboarding_step"],
                settings=user_data["settings"],
                last_login_at=now,
            )
            session.add(user)
            users_created += 1

            # Create audit log: user_registered
            registration_log = AuditLog(
                id=uuid.uuid4(),
                user_id=user_id,
                event_type="user_registered",
                event_data={
                    "email": user_data["email"],
                    "registered_at": now.isoformat(),
                },
                ip_address="127.0.0.1",
                user_agent="seed-script",
            )
            session.add(registration_log)
            audit_logs_created += 1

            # Create audit log: login_success
            login_log = AuditLog(
                id=uuid.uuid4(),
                user_id=user_id,
                event_type="login_success",
                event_data={
                    "login_at": now.isoformat(),
                },
                ip_address="127.0.0.1",
                user_agent="seed-script",
            )
            session.add(login_log)
            audit_logs_created += 1

        await session.commit()

    print("Seed complete.")
    print(f"  Users:      {users_created} created, {users_skipped} skipped")
    print(f"  Audit logs: {audit_logs_created} created")


def main() -> None:
    try:
        asyncio.run(seed())
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

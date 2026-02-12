"""Seed script for local development database.

Usage:
    python -m app.scripts.seed

Idempotent — safe to run multiple times.
"""

from __future__ import annotations

import asyncio
import sys


async def seed() -> None:
    """Seed the development database with test data."""
    print("Seeding database...")

    # TODO: Import engine/session once app factory is wired up
    # from app.db.session import async_session
    #
    # async with async_session() as session:
    #     # Check existing data before inserting
    #     result = await session.execute(select(func.count()).select_from(User))
    #     user_count = result.scalar_one()
    #     if user_count > 0:
    #         print(f"  Users already seeded ({user_count} found), skipping.")
    #     else:
    #         # Insert test users, instruments, playbooks, etc.
    #         pass
    #
    #     await session.commit()

    print("Seed complete.")
    print("  Users:       0 (skeleton — not yet implemented)")
    print("  Instruments: 0")
    print("  Playbooks:   0")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()

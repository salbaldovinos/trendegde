"""Seed execution pipeline reference data.

Usage: python -m app.db.seed_execution

Idempotent — safe to run multiple times (uses INSERT ... ON CONFLICT DO NOTHING).
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select, text

from app.db.session import AsyncSessionLocal


# ---------------------------------------------------------------------------
# Contract Specifications (9 contracts)
# ---------------------------------------------------------------------------
CONTRACT_SPECS = [
    {
        "symbol": "MNQ",
        "name": "Micro E-mini Nasdaq 100",
        "exchange": "CME",
        "tick_size": "0.25",
        "tick_value": "0.50",
        "point_value": "2.00",
        "margin_day": "1000.00",
        "margin_overnight": "2000.00",
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "NQ",
    },
    {
        "symbol": "MES",
        "name": "Micro E-mini S&P 500",
        "exchange": "CME",
        "tick_size": "0.25",
        "tick_value": "1.25",
        "point_value": "5.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "ES",
    },
    {
        "symbol": "MYM",
        "name": "Micro E-mini Dow",
        "exchange": "CBOT",
        "tick_size": "1.00",
        "tick_value": "0.50",
        "point_value": "0.50",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "YM",
    },
    {
        "symbol": "M2K",
        "name": "Micro E-mini Russell 2000",
        "exchange": "CME",
        "tick_size": "0.10",
        "tick_value": "0.50",
        "point_value": "5.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "RTY",
    },
    {
        "symbol": "MGC",
        "name": "Micro Gold",
        "exchange": "COMEX",
        "tick_size": "0.10",
        "tick_value": "1.00",
        "point_value": "10.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0820-1330 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "GC",
    },
    {
        "symbol": "MCL",
        "name": "Micro Crude Oil",
        "exchange": "NYMEX",
        "tick_size": "0.01",
        "tick_value": "1.00",
        "point_value": "100.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0900-1430 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "CL",
    },
    {
        "symbol": "SIL",
        "name": "Micro Silver",
        "exchange": "COMEX",
        "tick_size": "0.005",
        "tick_value": "2.50",
        "point_value": "500.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0820-1330 ETH:1800-1700",
        "is_micro": True,
        "full_size_symbol": "SI",
    },
    {
        "symbol": "NQ",
        "name": "E-mini Nasdaq 100",
        "exchange": "CME",
        "tick_size": "0.25",
        "tick_value": "5.00",
        "point_value": "20.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
    {
        "symbol": "ES",
        "name": "E-mini S&P 500",
        "exchange": "CME",
        "tick_size": "0.25",
        "tick_value": "12.50",
        "point_value": "50.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
    {
        "symbol": "YM",
        "name": "Dow E-mini",
        "exchange": "CBOT",
        "tick_size": "1.00",
        "tick_value": "5.00",
        "point_value": "5.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
    {
        "symbol": "GC",
        "name": "Gold",
        "exchange": "COMEX",
        "tick_size": "0.10",
        "tick_value": "10.00",
        "point_value": "100.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0820-1330 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
    {
        "symbol": "CL",
        "name": "Crude Oil",
        "exchange": "NYMEX",
        "tick_size": "0.01",
        "tick_value": "10.00",
        "point_value": "1000.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0900-1430 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
    {
        "symbol": "RTY",
        "name": "Russell 2000",
        "exchange": "CME",
        "tick_size": "0.10",
        "tick_value": "5.00",
        "point_value": "50.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0830-1515 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
    {
        "symbol": "SI",
        "name": "Silver",
        "exchange": "COMEX",
        "tick_size": "0.005",
        "tick_value": "25.00",
        "point_value": "5000.00",
        "margin_day": None,
        "margin_overnight": None,
        "trading_hours": "RTH:0820-1330 ETH:1800-1700",
        "is_micro": False,
        "full_size_symbol": None,
    },
]

# ---------------------------------------------------------------------------
# Contract Calendar (4 quarters x 3 families = 12 rows)
# ---------------------------------------------------------------------------
CALENDAR_FAMILIES = ["NQ", "ES", "YM"]
QUARTERS = [
    {"month_code": "H", "year": 2026, "suffix": "H26"},
    {"month_code": "M", "year": 2026, "suffix": "M26"},
    {"month_code": "U", "year": 2026, "suffix": "U26"},
    {"month_code": "Z", "year": 2026, "suffix": "Z26"},
]

# ---------------------------------------------------------------------------
# Instrument Correlations (21 pairs, instrument_a < instrument_b)
# ---------------------------------------------------------------------------
CORRELATIONS = [
    ("CL", "ES", "0.4500"),
    ("CL", "GC", "0.2500"),
    ("CL", "NQ", "0.4000"),
    ("CL", "RTY", "0.3500"),
    ("CL", "SI", "0.2000"),
    ("CL", "YM", "0.4200"),
    ("ES", "GC", "-0.1500"),
    ("ES", "NQ", "0.9200"),
    ("ES", "RTY", "0.8800"),
    ("ES", "SI", "0.1000"),
    ("ES", "YM", "0.9500"),
    ("GC", "NQ", "-0.1200"),
    ("GC", "RTY", "-0.1000"),
    ("GC", "SI", "0.8500"),
    ("GC", "YM", "-0.1300"),
    ("NQ", "RTY", "0.8200"),
    ("NQ", "SI", "0.0800"),
    ("NQ", "YM", "0.8700"),
    ("RTY", "SI", "0.0500"),
    ("RTY", "YM", "0.8400"),
    ("SI", "YM", "0.0600"),
]


async def seed() -> None:
    """Seed execution pipeline reference data."""
    print("Seeding execution pipeline data...")

    async with AsyncSessionLocal() as session:
        # ---------------------------------------------------------------
        # 1. Contract Specifications
        # ---------------------------------------------------------------
        specs_inserted = 0
        for spec in CONTRACT_SPECS:
            margin_day_clause = f"'{spec['margin_day']}'" if spec["margin_day"] else "NULL"
            margin_overnight_clause = f"'{spec['margin_overnight']}'" if spec["margin_overnight"] else "NULL"
            full_size_clause = f"'{spec['full_size_symbol']}'" if spec["full_size_symbol"] else "NULL"

            await session.execute(text("""
                INSERT INTO contract_specifications
                    (symbol, name, exchange, tick_size, tick_value, point_value,
                     margin_day, margin_overnight, trading_hours, is_micro, full_size_symbol)
                VALUES
                    (:symbol, :name, :exchange, :tick_size, :tick_value, :point_value,
                     :margin_day, :margin_overnight, :trading_hours, :is_micro, :full_size_symbol)
                ON CONFLICT (symbol) DO NOTHING
            """), {
                "symbol": spec["symbol"],
                "name": spec["name"],
                "exchange": spec["exchange"],
                "tick_size": spec["tick_size"],
                "tick_value": spec["tick_value"],
                "point_value": spec["point_value"],
                "margin_day": spec["margin_day"],
                "margin_overnight": spec["margin_overnight"],
                "trading_hours": spec["trading_hours"],
                "is_micro": spec["is_micro"],
                "full_size_symbol": spec["full_size_symbol"],
            })
            specs_inserted += 1

        # ---------------------------------------------------------------
        # 2. Contract Calendar
        # ---------------------------------------------------------------
        cal_inserted = 0
        for family in CALENDAR_FAMILIES:
            for q in QUARTERS:
                contract_symbol = f"{family}{q['suffix']}"
                await session.execute(text("""
                    INSERT INTO contract_calendar
                        (instrument_family, contract_symbol, month_code, year, is_front_month)
                    VALUES
                        (:family, :contract_symbol, :month_code, :year, false)
                    ON CONFLICT (instrument_family, month_code, year) DO NOTHING
                """), {
                    "family": family,
                    "contract_symbol": contract_symbol,
                    "month_code": q["month_code"],
                    "year": q["year"],
                })
                cal_inserted += 1

        # ---------------------------------------------------------------
        # 3. Instrument Correlations
        # ---------------------------------------------------------------
        corr_inserted = 0
        for inst_a, inst_b, corr_val in CORRELATIONS:
            await session.execute(text("""
                INSERT INTO instrument_correlations
                    (instrument_a, instrument_b, correlation)
                VALUES
                    (:a, :b, :corr)
                ON CONFLICT (instrument_a, instrument_b) DO NOTHING
            """), {
                "a": inst_a,
                "b": inst_b,
                "corr": corr_val,
            })
            corr_inserted += 1

        # ---------------------------------------------------------------
        # 4. Default risk settings for existing seed users
        # ---------------------------------------------------------------
        result = await session.execute(text("SELECT id FROM users"))
        user_rows = result.fetchall()
        risk_inserted = 0
        for row in user_rows:
            user_id = row[0]
            await session.execute(text("""
                INSERT INTO user_risk_settings (user_id)
                VALUES (:uid)
                ON CONFLICT (user_id) DO NOTHING
            """), {"uid": user_id})
            risk_inserted += 1

        await session.commit()

    print("Seed complete.")
    print(f"  Contract specs:    {specs_inserted} attempted (ON CONFLICT DO NOTHING)")
    print(f"  Calendar entries:  {cal_inserted} attempted")
    print(f"  Correlations:      {corr_inserted} attempted")
    print(f"  Risk settings:     {risk_inserted} attempted (for existing users)")


def main() -> None:
    try:
        asyncio.run(seed())
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

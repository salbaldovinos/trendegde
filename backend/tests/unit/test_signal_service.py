"""Unit tests for the signal service (creation, validation, enrichment, dedup, webhook)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.contract_specification import ContractSpecification
from app.db.models.signal import Signal
from app.db.models.webhook_url import WebhookUrl
from app.services.signal_service import SignalService


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def make_contract_spec(**overrides):
    defaults = {
        "symbol": "MNQ",
        "tick_size": Decimal("0.25"),
        "tick_value": Decimal("0.50"),
        "point_value": Decimal("2.00"),
        "is_micro": True,
        "full_size_symbol": "NQ",
    }
    defaults.update(overrides)
    spec = MagicMock(spec=ContractSpecification)
    for k, v in defaults.items():
        setattr(spec, k, v)
    return spec


def make_signal(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "source": "MANUAL",
        "status": "RECEIVED",
        "instrument_symbol": "MNQ",
        "direction": "LONG",
        "entry_type": "MARKET",
        "entry_price": Decimal("18500.00"),
        "stop_loss_price": Decimal("18480.00"),
        "take_profit_price": Decimal("18540.00"),
        "quantity": 1,
        "enrichment_data": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    signal = MagicMock(spec=Signal)
    for k, v in defaults.items():
        setattr(signal, k, v)
    return signal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest_asyncio.fixture
async def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    return redis


@pytest_asyncio.fixture
async def svc(mock_db, mock_redis):
    return SignalService(mock_db, mock_redis)


# ═══════════════════════════════════════════════════════════════════
# Manual Signal Creation Tests
# ═══════════════════════════════════════════════════════════════════


class TestManualSignalCreation:
    """Test manual signal creation flow."""

    @pytest.mark.asyncio
    async def test_create_manual_signal(self, svc, mock_db, mock_redis):
        """Creates signal with correct fields and transitions to ENRICHED."""
        spec = make_contract_spec()
        user_id = uuid.uuid4()

        # Mock validate_instrument
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result1

        # Patch Celery task
        with patch("app.services.signal_service.SignalService.deduplicate_signal", new_callable=AsyncMock):
            with patch("app.tasks.execution_tasks.process_signal") as mock_task:
                mock_task.delay = MagicMock()

                signal = await svc.create_manual_signal(
                    user_id,
                    {
                        "instrument_symbol": "MNQ",
                        "direction": "LONG",
                        "entry_type": "MARKET",
                        "entry_price": 18500.00,
                        "stop_loss_price": 18480.00,
                        "take_profit_price": 18540.00,
                    },
                )

        # Signal was added to DB
        mock_db.add.assert_called()
        added = mock_db.add.call_args_list[0].args[0]
        assert isinstance(added, Signal)
        assert added.source == "MANUAL"
        assert added.instrument_symbol == "MNQ"
        assert added.direction == "LONG"

    @pytest.mark.asyncio
    async def test_create_manual_dispatches_task(self, svc, mock_db, mock_redis):
        """Dispatches process_signal Celery task after creation."""
        spec = make_contract_spec()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_db.execute.return_value = mock_result

        with patch("app.services.signal_service.SignalService.deduplicate_signal", new_callable=AsyncMock):
            with patch("app.tasks.execution_tasks.process_signal") as mock_task:
                mock_task.delay = MagicMock()

                signal = await svc.create_manual_signal(
                    uuid.uuid4(),
                    {
                        "instrument_symbol": "MNQ",
                        "direction": "LONG",
                        "entry_price": 18500.00,
                    },
                )

                mock_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_signal_dedup(self, svc, mock_redis):
        """Duplicate signal within window is rejected."""
        mock_redis.get.return_value = "1"  # Key exists

        with pytest.raises(ConflictError, match="Duplicate signal"):
            await svc.deduplicate_signal(
                uuid.uuid4(), "MNQ", "LONG"
            )

    @pytest.mark.asyncio
    async def test_signal_dedup_expired(self, svc, mock_redis):
        """Signal after dedup window passes through."""
        mock_redis.get.return_value = None  # No key

        # Should not raise
        await svc.deduplicate_signal(uuid.uuid4(), "MNQ", "LONG")
        mock_redis.set.assert_awaited_once()


# ═══════════════════════════════════════════════════════════════════
# Validation Tests
# ═══════════════════════════════════════════════════════════════════


class TestSignalValidation:
    """Test signal price validation."""

    def test_validate_prices_long(self):
        """entry > SL, TP > entry for LONG passes."""
        SignalService.validate_prices(
            direction="LONG",
            entry_price=18500.0,
            stop_loss_price=18480.0,
            take_profit_price=18540.0,
            tick_size=0.25,
        )

    def test_validate_prices_short(self):
        """entry < SL, TP < entry for SHORT passes."""
        SignalService.validate_prices(
            direction="SHORT",
            entry_price=18500.0,
            stop_loss_price=18520.0,
            take_profit_price=18460.0,
            tick_size=0.25,
        )

    @pytest.mark.asyncio
    async def test_validate_invalid_instrument(self, svc, mock_db):
        """Unknown symbol raises NotFoundError."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundError, match="Instrument"):
            await svc.validate_instrument("INVALID")

    def test_validate_prices_invalid_long_sl_above(self):
        """LONG with SL >= entry raises ValueError."""
        with pytest.raises(ValueError, match="Stop loss must be below"):
            SignalService.validate_prices(
                direction="LONG",
                entry_price=18500.0,
                stop_loss_price=18500.0,
                take_profit_price=18540.0,
                tick_size=0.25,
            )

    def test_validate_prices_invalid_short_sl_below(self):
        """SHORT with SL <= entry raises ValueError."""
        with pytest.raises(ValueError, match="Stop loss must be above"):
            SignalService.validate_prices(
                direction="SHORT",
                entry_price=18500.0,
                stop_loss_price=18500.0,
                take_profit_price=18460.0,
                tick_size=0.25,
            )

    def test_validate_prices_invalid_long_tp_below(self):
        """LONG with TP <= entry raises ValueError."""
        with pytest.raises(ValueError, match="Take profit must be above"):
            SignalService.validate_prices(
                direction="LONG",
                entry_price=18500.0,
                stop_loss_price=18480.0,
                take_profit_price=18499.0,
                tick_size=0.25,
            )

    def test_validate_prices_too_close(self):
        """SL closer than 1 tick raises ValueError."""
        with pytest.raises(ValueError, match="at least 1 tick"):
            SignalService.validate_prices(
                direction="LONG",
                entry_price=18500.0,
                stop_loss_price=18499.90,
                take_profit_price=18540.0,
                tick_size=0.25,
            )


# ═══════════════════════════════════════════════════════════════════
# Enrichment Tests
# ═══════════════════════════════════════════════════════════════════


class TestSignalEnrichment:
    """Test signal enrichment with risk/reward calculations."""

    def test_enrich_calculates_risk(self):
        """risk_per_contract calculation from entry and SL."""
        signal = make_signal(
            entry_price=Decimal("18500.00"),
            stop_loss_price=Decimal("18480.00"),
            take_profit_price=None,
        )
        spec = make_contract_spec(
            tick_size=Decimal("0.25"),
            tick_value=Decimal("0.50"),
            point_value=Decimal("2.00"),
        )

        enrichment = SignalService.enrich_signal(signal, spec)

        # risk_distance = |18500 - 18480| = 20.0
        # risk_ticks = 20.0 / 0.25 = 80
        # risk_per_contract = 80 * 0.50 = 40.0
        assert enrichment["risk_distance"] == 20.0
        assert enrichment["risk_ticks"] == 80.0
        assert enrichment["risk_per_contract"] == 40.0

    def test_enrich_calculates_rr(self):
        """risk/reward ratio from entry, SL, and TP."""
        signal = make_signal(
            entry_price=Decimal("18500.00"),
            stop_loss_price=Decimal("18480.00"),
            take_profit_price=Decimal("18540.00"),
        )
        spec = make_contract_spec(
            tick_size=Decimal("0.25"),
            tick_value=Decimal("0.50"),
        )

        enrichment = SignalService.enrich_signal(signal, spec)

        # reward_distance = |18540 - 18500| = 40.0
        # reward_ticks = 40 / 0.25 = 160
        # reward_per_contract = 160 * 0.50 = 80.0
        # risk_per_contract = 40.0 (from above)
        # rr = 80.0 / 40.0 = 2.0
        assert enrichment["risk_reward_ratio"] == 2.0

    def test_enrich_no_sl(self):
        """Enrichment skipped without stop loss."""
        signal = make_signal(
            entry_price=Decimal("18500.00"),
            stop_loss_price=None,
            take_profit_price=Decimal("18540.00"),
        )
        spec = make_contract_spec()

        enrichment = SignalService.enrich_signal(signal, spec)

        assert "risk_per_contract" not in enrichment
        assert "risk_reward_ratio" not in enrichment
        assert enrichment["tick_size"] == 0.25


# ═══════════════════════════════════════════════════════════════════
# Webhook Processing Tests
# ═══════════════════════════════════════════════════════════════════


class TestWebhookProcessing:
    """Test webhook signal normalization and creation."""

    def test_normalize_webhook_signal(self):
        """TradingView webhook payload normalized to canonical format."""
        raw = {
            "ticker": "MNQ",
            "action": "buy",
            "price": 18500.0,
            "stop": 18480.0,
            "target": 18540.0,
            "quantity": 1,
        }
        result = SignalService.normalize_signal("WEBHOOK", raw)

        assert result["instrument_symbol"] == "MNQ"
        assert result["direction"] == "LONG"
        assert result["entry_price"] == 18500.0
        assert result["stop_loss_price"] == 18480.0
        assert result["take_profit_price"] == 18540.0

    def test_normalize_webhook_sell(self):
        """Sell action maps to SHORT direction."""
        raw = {"ticker": "ES", "action": "sell", "price": 5000.0}
        result = SignalService.normalize_signal("WEBHOOK", raw)

        assert result["direction"] == "SHORT"

    def test_normalize_non_webhook_passthrough(self):
        """Non-webhook payload passes through unchanged."""
        raw = {"instrument_symbol": "MNQ", "direction": "LONG", "entry_price": 18500.0}
        result = SignalService.normalize_signal("MANUAL", raw)

        assert result == raw

# PRD-003: Trade Execution Pipeline & Broker Integration

**TrendEdge -- AI-Powered Futures Trading Platform**

| Field | Value |
|---|---|
| PRD Number | PRD-003 of 11 |
| Feature Area | Trade Execution Pipeline & Broker Integration |
| Status | Draft |
| Version | 1.0 |
| Author | TrendEdge Engineering |
| Date | February 2026 |
| Classification | CONFIDENTIAL |

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Risk Management Requirements](#5-risk-management-requirements)
6. [Dependencies on Other PRDs](#6-dependencies-on-other-prds)
7. [Testing Requirements](#7-testing-requirements)
8. [Security Considerations](#8-security-considerations)
9. [Phase Mapping](#9-phase-mapping)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Overview & Purpose

### 1.1 Summary

The Trade Execution Pipeline is the mission-critical system that transforms trading signals into broker orders, manages their lifecycle from submission to fill, and captures every detail for downstream journaling and analytics. It is the connective tissue between TrendEdge's signal generation capabilities (trendline engine, TradingView webhooks, manual entry) and the user's brokerage account.

### 1.2 Problem Statement

Retail futures traders today rely on fragmented middleware tools (TradersPost at $49-299/mo, PickMyTrade at $50/mo, SignalStack at $0.59-1.49/signal) to route signals to brokers. These tools lack integrated journaling, have no awareness of trendline metadata, offer limited risk management, and lose critical context between signal and fill. Traders cannot answer questions like "what was the trendline grade on the trade that just filled?" because the execution layer is disconnected from the analysis layer.

### 1.3 Solution

TrendEdge unifies signal ingestion, validation, risk management, order construction, broker routing, and post-fill processing into a single pipeline. Every trade carries its full genealogy -- from the trendline that spawned the signal, through the risk checks it passed, to the bracket order structure, fill details, and slippage measurement. This context flows directly into the journal and analytics systems without manual intervention.

### 1.4 Scope

This PRD covers:
- Signal ingestion from three sources (internal engine, TradingView webhook, manual dashboard entry)
- Signal validation and enrichment pipeline
- Risk management engine
- Order construction (bracket orders, OCO groups)
- Broker adapter interface and concrete implementations (IBKR, Tradovate, Webull)
- Paper trading simulator
- Position and order lifecycle management
- Continuous contract symbol mapping
- Circuit breaker and failover mechanisms
- Fill reconciliation

This PRD does NOT cover:
- Trendline detection engine internals (see PRD-002)
- Journal entry content and UI (see PRD-004)
- Analytics and playbook computation (see PRD-005)
- Notification delivery mechanisms (see PRD-008)
- User authentication and authorization (see PRD-009)

---

## 2. User Stories

### 2.1 Signal Ingestion

| ID | Story | Priority |
|---|---|---|
| US-EX-001 | As a trendline trader, I want signals from TrendEdge's trendline detection engine to automatically enter the execution pipeline so that qualifying breaks are traded without my manual intervention. | P0 |
| US-EX-002 | As a TradingView user, I want to configure my TradingView alerts to POST to a unique TrendEdge webhook URL so that my Pine Script strategies can trigger trades through TrendEdge. | P0 |
| US-EX-003 | As a discretionary trader, I want to manually enter a trade signal through the dashboard (instrument, direction, entry price, stop, target) so that I can use TrendEdge's risk management and execution for ad-hoc setups. | P0 |
| US-EX-004 | As a trader, I want every signal to pass through risk checks before an order is placed so that I never violate my own risk rules even when I am tempted to. | P0 |

### 2.2 Broker Integration

| ID | Story | Priority |
|---|---|---|
| US-EX-005 | As an IBKR user, I want to connect my Interactive Brokers account to TrendEdge and route orders through the TWS API so that I benefit from IBKR's low commissions ($0.25-0.85 per micro contract). | P0 |
| US-EX-006 | As a Tradovate user, I want to connect my Tradovate account and have TrendEdge handle OAuth token refresh automatically so that I never have stale credentials causing missed trades. | P0 |
| US-EX-007 | As a Webull user, I want to connect my Webull futures account once TrendEdge adds support so that I can use Webull's competitive micro commissions (~$0.25 + exchange fees). | P1 |
| US-EX-008 | As a trader, I want to switch between brokers without changing my signal or risk configuration so that the execution layer is cleanly separated from my strategy. | P0 |

### 2.3 Paper Trading

| ID | Story | Priority |
|---|---|---|
| US-EX-009 | As a new user, I want to paper trade for a configurable period (default 60 days) with simulated fills that include realistic slippage so that I validate my strategy before risking real capital. | P0 |
| US-EX-010 | As a paper trader, I want my paper P&L tracked completely separately from live P&L, with a clear visual indicator on the dashboard, so that I never confuse simulated with real results. | P0 |
| US-EX-011 | As a user completing my paper period, I want the system to prompt me to enable live trading (not auto-enable) so that the transition to real money is a deliberate, conscious decision. | P0 |

### 2.4 Order Management

| ID | Story | Priority |
|---|---|---|
| US-EX-012 | As a trader, I want every entry order to include an attached stop loss and take profit (bracket order) so that my risk is defined from the moment I enter a position. | P0 |
| US-EX-013 | As a trader, I want to see real-time order status (pending, submitted, partial fill, filled, cancelled, rejected) on the dashboard so that I always know the state of my orders. | P0 |
| US-EX-014 | As a trader, I want the ability to manually cancel or modify an open order from the dashboard so that I retain override control at all times. | P0 |
| US-EX-015 | As a trader, I want to see fill price, slippage from signal price, and timestamp for every execution so that I can evaluate execution quality. | P0 |

### 2.5 Resilience

| ID | Story | Priority |
|---|---|---|
| US-EX-016 | As a trader, I want the system to automatically halt order submission after N consecutive broker failures (circuit breaker) so that a broker outage does not result in erratic behavior. | P0 |
| US-EX-017 | As a trader, I want to receive an immediate notification if an order is rejected or a broker connection is lost so that I can take manual action. | P0 |
| US-EX-018 | As a trader, I want duplicate signal detection so that a webhook that fires twice does not result in double the intended position. | P0 |

---

## 3. Functional Requirements

### 3.1 Signal Ingestion

#### EX-FR-001: Internal Signal Source

The system SHALL accept signals from the trendline detection engine (PRD-002) via an internal message bus (Redis pub/sub or direct function call). Internal signals SHALL include: instrument, direction (LONG/SHORT), entry price, stop loss price, take profit price, trendline ID, trendline grade, touch count, signal timestamp, and confidence score.

#### EX-FR-002: TradingView Webhook Signal Source

The system SHALL accept TradingView alert webhooks via an HTTP POST endpoint. The endpoint URL SHALL be unique per user, following the pattern: `POST /api/v1/webhooks/tradingview/{user_webhook_id}`. The system SHALL parse the JSON payload and extract: ticker, action (buy/sell/close), price, stop loss, take profit, and any user-defined custom fields.

#### EX-FR-003: Manual Signal Source

The system SHALL provide a dashboard form for manual signal entry. Required fields: instrument (searchable dropdown), direction, entry type (market/limit), entry price (pre-filled with last price for market orders). Optional fields: stop loss price, take profit price, quantity override, free-text notes. The form SHALL validate all inputs client-side and server-side before submission.

#### EX-FR-004: Signal Normalization

All signals, regardless of source, SHALL be normalized into a canonical `Signal` data structure before entering the pipeline:

```python
class Signal:
    id: UUID
    user_id: UUID
    source: SignalSource  # INTERNAL | WEBHOOK | MANUAL
    source_metadata: dict  # Source-specific raw payload
    instrument: str        # Normalized symbol (e.g., "MNQZ5")
    direction: Direction   # LONG | SHORT
    entry_type: OrderType  # MARKET | LIMIT
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
    quantity: int
    trendline_id: Optional[UUID]
    trendline_grade: Optional[str]
    risk_reward_ratio: Decimal  # Computed
    created_at: datetime
    status: SignalStatus   # RECEIVED | VALIDATED | RISK_PASSED | EXECUTING | FILLED | REJECTED
```

### 3.2 TradingView Webhook Receiver

#### EX-FR-005: Unique Webhook URL Generation

Upon user registration or first broker connection, the system SHALL generate a unique webhook URL containing a cryptographically random identifier (minimum 32 characters, URL-safe base64). The webhook ID SHALL NOT be the user's UUID. Users SHALL be able to regenerate their webhook URL at any time, which invalidates the previous URL immediately.

#### EX-FR-006: Webhook Authentication

Each webhook request SHALL be authenticated using one of the following methods:
1. **API Key in payload**: A user-specific API key included in the JSON body under a `key` or `api_key` field.
2. **HMAC Signature**: An `X-Signature` header containing HMAC-SHA256(request_body, user_secret). The system SHALL compute the expected signature and reject requests where the signature does not match within a constant-time comparison.
3. **Webhook ID validation**: The webhook URL path itself serves as a shared secret (minimum security level).

The system SHALL reject unauthenticated requests with HTTP 401 and log the attempt.

#### EX-FR-007: Webhook Payload Parsing

The system SHALL accept the following TradingView JSON payload format:

```json
{
  "key": "user_api_key",
  "ticker": "NQ1!",
  "action": "buy",
  "price": 18450.25,
  "stop": 18420.00,
  "target": 18510.50,
  "quantity": 1,
  "timeframe": "240",
  "message": "A+ trendline break - 4 touches"
}
```

The system SHALL also accept alternative field names commonly used in TradingView alerts: `symbol` for `ticker`, `side`/`order` for `action`, `sl` for `stop`, `tp` for `target`, `qty`/`contracts` for `quantity`. Unrecognized fields SHALL be preserved in `source_metadata` for journaling.

#### EX-FR-008: Webhook Response

The system SHALL respond to valid webhook requests with HTTP 200 and a JSON body containing: `{ "signal_id": "uuid", "status": "received", "message": "Signal accepted for processing" }`. The response SHALL be returned within 2 seconds regardless of downstream processing time. Processing SHALL continue asynchronously after the response is sent.

#### EX-FR-009: Webhook Rate Limiting

The system SHALL enforce rate limiting per webhook URL: maximum 10 requests per minute, 100 requests per hour. Requests exceeding the rate limit SHALL receive HTTP 429 with a `Retry-After` header. Rate limiting SHALL use a sliding window algorithm via Redis.

### 3.3 Signal Validation and Enrichment

#### EX-FR-010: Signal Authentication Validation

For webhook signals, the system SHALL verify the API key or HMAC signature matches the user associated with the webhook URL. For internal signals, the system SHALL verify the signal originates from an authenticated trendline engine process. For manual signals, the system SHALL verify the user's session token.

#### EX-FR-011: Instrument Validation

The system SHALL validate that the instrument symbol maps to a supported futures contract. The system SHALL reject signals for unsupported instruments with a descriptive error message. The system SHALL maintain a reference table of all supported CME/CBOT/NYMEX/COMEX micro and full-size futures contracts.

#### EX-FR-012: Continuous Contract Symbol Mapping

The system SHALL map TradingView continuous contract symbols to specific contract months:

| TradingView Symbol | Mapped Instrument | Logic |
|---|---|---|
| NQ1! | MNQ{current_month} | Map to Micro E-mini Nasdaq front month |
| ES1! | MES{current_month} | Map to Micro E-mini S&P front month |
| YM1! | MYM{current_month} | Map to Micro E-mini Dow front month |
| RTY1! | M2K{current_month} | Map to Micro E-mini Russell front month |
| GC1! | MGC{current_month} | Map to Micro Gold front month |
| CL1! | MCL{current_month} | Map to Micro Crude Oil front month |
| SI1! | SIL{current_month} | Map to Micro Silver front month |
| NQ1! | NQ{current_month} | Full-size if user preference is full-size |

The mapping SHALL account for rollover dates. The system SHALL use a configurable rollover schedule (default: roll 3 business days before contract expiration). Users SHALL be able to configure whether signals map to micro or full-size contracts.

#### EX-FR-013: Price Validation

The system SHALL validate that:
- Entry price is within 5% of the current market price for the instrument (configurable tolerance).
- Stop loss is on the correct side of the entry price (below for LONG, above for SHORT).
- Take profit is on the correct side of the entry price (above for LONG, below for SHORT).
- Stop distance is at least 1 tick.
- The computed risk-reward ratio meets the user's minimum threshold (default: 2.0).

#### EX-FR-014: Signal Enrichment

The system SHALL enrich validated signals with:
- Contract specification: tick size, tick value, notional value per contract, margin requirements.
- Computed fields: stop distance in ticks, target distance in ticks, risk per contract in dollars, reward per contract in dollars, R:R ratio.
- Market context: current session (RTH/ETH), day of week, time to next session boundary.
- Trendline metadata (if from internal engine): trendline ID, grade, touch count, slope, duration, candle spacing.
- Account context: current position in the same instrument, current daily P&L, current open position count.

#### EX-FR-015: Signal Deduplication

The system SHALL detect and reject duplicate signals using a deduplication window (default: 5 minutes). Two signals are considered duplicates if they share the same user, instrument, direction, and entry price within a configurable tolerance (default: 2 ticks). The first signal SHALL be processed; subsequent duplicates SHALL be logged and rejected with reason "DUPLICATE_SIGNAL".

### 3.4 Risk Management Engine

#### EX-FR-016: Maximum Position Size Check

The system SHALL enforce a per-instrument maximum position size (default: 2 contracts for micro, 1 contract for full-size). The check SHALL consider the sum of the proposed order quantity plus any existing open position in the same instrument. Orders that would exceed the limit SHALL be rejected.

#### EX-FR-017: Daily Loss Limit Check

The system SHALL enforce a daily loss limit (configurable, default: $500 for paper, user-defined for live). The daily loss is computed as the sum of realized P&L for closed trades today plus unrealized P&L for open positions. If placing a new trade could theoretically hit the daily loss limit (assuming the stop is hit on all open positions plus the new trade), the order SHALL be rejected. When the daily loss limit is reached, no further trades SHALL be allowed for the remainder of the trading day. The daily loss counter SHALL reset at 5:00 PM CT (futures day boundary).

#### EX-FR-018: Maximum Concurrent Positions Check

The system SHALL enforce a maximum number of simultaneously open positions across all instruments (default: 3). The check SHALL count all positions with a status of OPEN. Orders that would exceed this limit SHALL be rejected.

#### EX-FR-019: Minimum Risk-Reward Ratio Check

The system SHALL enforce a minimum risk-reward ratio (default: 2.0). The R:R ratio is calculated as `(take_profit_price - entry_price) / (entry_price - stop_loss_price)` for LONG positions (inverted for SHORT). Signals with R:R below the minimum SHALL be rejected.

#### EX-FR-020: Correlation Limit Check

The system SHALL enforce correlation limits across open positions. The system SHALL maintain a correlation matrix for supported instruments (e.g., MNQ and MES are highly correlated index futures). If a new signal would result in multiple open positions in correlated instruments (correlation coefficient > 0.7), the system SHALL warn the user and optionally block the order (configurable: warn-only or block, default: warn-only).

#### EX-FR-021: Risk Check Audit Trail

Every risk check evaluation SHALL be logged to the database with: signal ID, check name, check result (PASS/FAIL/WARN), actual value, threshold value, timestamp. The audit trail SHALL be viewable from the trade journal entry.

#### EX-FR-022: Risk Parameter Configuration

Users SHALL be able to configure all risk parameters through the dashboard settings:
- Maximum position size per instrument
- Daily loss limit (absolute dollar amount)
- Maximum concurrent positions
- Minimum R:R ratio
- Correlation limit action (warn vs. block)
- Correlation coefficient threshold

Changes to risk parameters SHALL take effect immediately for new signals. Changes SHALL NOT affect orders already submitted to the broker. All parameter changes SHALL be logged with previous and new values.

### 3.5 Order Construction

#### EX-FR-023: Bracket Order Construction

For each validated and risk-approved signal, the system SHALL construct a bracket order consisting of:

1. **Entry Order**: MARKET or LIMIT order based on signal entry_type.
   - MARKET: Submitted immediately at best available price.
   - LIMIT: Submitted at signal entry_price with a configurable time-in-force (default: GTC, options: DAY, GTC, GTD).
2. **Stop Loss Order**: STOP order at signal stop_loss_price. Attached as a child order to the entry (OCO group). Stop loss SHALL be a stop-market order by default, with an option for stop-limit (user-configurable).
3. **Take Profit Order**: LIMIT order at signal take_profit_price. Attached as a child order to the entry (OCO group with the stop loss).

The stop loss and take profit SHALL be linked as an OCO (One-Cancels-Other) group: when either is filled, the other SHALL be automatically cancelled.

#### EX-FR-024: Safety Line Stop Loss Calculation

For signals originating from the internal trendline engine, the stop loss SHALL be calculated using the "safety line" methodology: the opposing trendline projected forward by 4 candles from the entry candle. The system SHALL receive the safety line price from the trendline engine as part of the signal payload. If no safety line is available, the system SHALL fall back to a configurable default stop distance (default: 20 ticks for micro index futures, 10 ticks for micro metals).

#### EX-FR-025: Take Profit at Support/Resistance

For signals originating from the internal trendline engine, the take profit SHALL be placed at the first identified support/resistance level that provides at least 2R reward. The system SHALL receive candidate S/R levels from the trendline engine. If no qualifying S/R level is available, the system SHALL use a default multiple of the stop distance (default: 2.5x stop distance).

#### EX-FR-026: Order Quantity Calculation

If the signal does not specify a quantity, the system SHALL calculate the order quantity based on:
1. Fixed risk per trade (user-configurable, default: $100 per trade).
2. Stop distance in ticks multiplied by tick value = risk per contract.
3. Quantity = floor(fixed_risk / risk_per_contract).
4. Quantity SHALL be clamped to the maximum position size (EX-FR-016).
5. Minimum quantity SHALL be 1.

#### EX-FR-027: Order Metadata Attachment

Each order submitted to the broker SHALL carry metadata in a local database record: signal ID, user ID, broker adapter name, order type, intended entry/stop/target prices, constructed quantity, risk calculations, risk check audit trail reference, and submission timestamp.

### 3.6 Broker Adapter Interface

#### EX-FR-028: Abstract Broker Interface

The system SHALL define an abstract base class (ABC) `BrokerAdapter` that all broker implementations MUST conform to:

```python
from abc import ABC, abstractmethod

class BrokerAdapter(ABC):
    @abstractmethod
    async def connect(self) -> ConnectionStatus:
        """Establish connection to the broker."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close the broker connection."""
        ...

    @abstractmethod
    async def place_order(self, order: Order) -> OrderResult:
        """Submit an order to the broker. Returns broker order ID."""
        ...

    @abstractmethod
    async def place_bracket_order(
        self, entry: Order, stop_loss: Order, take_profit: Order
    ) -> BracketOrderResult:
        """Submit a bracket order (entry + SL + TP as OCO)."""
        ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> CancelResult:
        """Cancel a pending order by broker order ID."""
        ...

    @abstractmethod
    async def modify_order(
        self, broker_order_id: str, modifications: OrderModification
    ) -> ModifyResult:
        """Modify a pending order (price, quantity)."""
        ...

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Retrieve all open positions."""
        ...

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        """Get current status of an order."""
        ...

    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Retrieve account balance, margin, buying power."""
        ...

    @abstractmethod
    async def subscribe_order_updates(
        self, callback: Callable[[OrderUpdate], None]
    ) -> None:
        """Subscribe to real-time order status updates."""
        ...

    @abstractmethod
    async def subscribe_position_updates(
        self, callback: Callable[[PositionUpdate], None]
    ) -> None:
        """Subscribe to real-time position updates."""
        ...

    @abstractmethod
    async def get_contract_details(self, symbol: str) -> ContractDetails:
        """Retrieve contract specifications for a symbol."""
        ...
```

All methods SHALL raise typed exceptions (`BrokerConnectionError`, `OrderRejectedError`, `InsufficientMarginError`, `InvalidSymbolError`) rather than returning error codes.

#### EX-FR-029: Broker Adapter Registry

The system SHALL maintain a registry of available broker adapters. Users SHALL be able to configure one or more broker connections. Each broker connection SHALL store: broker type, connection parameters (encrypted), default account ID, and active/inactive status. The routing layer SHALL select the appropriate adapter based on the user's active broker configuration.

### 3.7 Interactive Brokers (IBKR) Adapter

#### EX-FR-030: IBKR Connection Management

The IBKR adapter SHALL connect via the `ib_async` library to IB Gateway running on the application VPS. The adapter SHALL:
- Maintain a persistent connection to IB Gateway (TWS API socket, default port 4001 for live, 4002 for paper).
- Detect connection drops and auto-reconnect with exponential backoff (initial: 1s, max: 60s, jitter: +/- 500ms).
- Support both live and paper trading accounts (IB Gateway mode determines this).
- Handle IB's pacing violations (max 50 messages/second) via internal rate limiting.

#### EX-FR-031: IBKR Order Submission

The IBKR adapter SHALL translate TrendEdge's `Order` model into IB API `Order` objects:
- Map TrendEdge instrument symbols to IB `Contract` objects (e.g., "MNQH6" to Contract(symbol="MNQ", exchange="CME", secType="FUT", lastTradeDateOrContractMonth="202603")).
- Support order types: MKT, LMT, STP, STP LMT.
- Implement bracket orders using IB's native bracket order support (parent + child OCA group).
- Set `transmit=False` on parent, `transmit=True` on last child to submit atomically.
- Capture and return: IB orderId, permId, status, and fill details.

#### EX-FR-032: IBKR Event Handling

The IBKR adapter SHALL subscribe to and process the following IB events:
- `orderStatus`: Map to TrendEdge order states (Submitted, Filled, Cancelled, Error).
- `execDetails`: Capture fill price, fill quantity, commission, execution time, exchange.
- `error`: Log error codes and messages. Handle common codes: 110 (price out of range), 201 (order rejected), 502 (couldn't connect), 1100 (connectivity lost), 2104/2106 (data farm connection).
- `position`: Reconcile IB-reported positions with TrendEdge's internal position tracking.

#### EX-FR-033: IBKR Account Data

The IBKR adapter SHALL retrieve and cache (refresh every 30 seconds):
- Account balance (NetLiquidation, TotalCashValue).
- Margin usage (InitMarginReq, MaintMarginReq, AvailableFunds).
- Daily P&L (RealizedPnL, UnrealizedPnL).
- Open positions with average cost and current market value.

### 3.8 Tradovate Adapter

#### EX-FR-034: Tradovate Authentication

The Tradovate adapter SHALL authenticate using OAuth 2.0:
- Obtain access token via `POST /auth/accessTokenRequest` with user credentials or device ID.
- Store access token and refresh token securely (encrypted at rest).
- Tokens expire every 60 minutes. The adapter SHALL refresh tokens proactively at 50 minutes (10-minute buffer).
- On token refresh failure, the adapter SHALL retry 3 times with 5-second intervals before marking the connection as failed and notifying the user.

#### EX-FR-035: Tradovate Order Submission

The Tradovate adapter SHALL submit orders via the REST API:
- Use `POST /order/placeOrder` for individual orders.
- Use `POST /order/placeOSO` (Order-Sends-Order) for bracket orders, which chains the entry order with SL and TP as child orders.
- Map TrendEdge order types to Tradovate: Market, Limit, Stop, StopLimit.
- Set `isAutomated=true` for all programmatic orders.
- Capture and return: Tradovate orderId, order status, and fill details.

#### EX-FR-036: Tradovate WebSocket Streaming

The Tradovate adapter SHALL maintain a WebSocket connection for real-time updates:
- Connect to `wss://live.tradovateapi.com/v1/websocket` (live) or `wss://demo.tradovateapi.com/v1/websocket` (paper).
- Subscribe to `order/item` for order status changes.
- Subscribe to `fill/item` for fill notifications.
- Subscribe to `position/item` for position updates.
- Handle WebSocket heartbeat (send ping every 2.5 seconds per Tradovate spec).
- Reconnect on disconnect with exponential backoff.

#### EX-FR-037: Tradovate Account Data

The Tradovate adapter SHALL retrieve:
- Account balance and margin via `GET /account/item` and `GET /cashBalance/getCashBalanceSnapshot`.
- Open positions via `GET /position/list`.
- Open orders via `GET /order/list`.
- Daily P&L from cash balance snapshots.

### 3.9 Paper Trading Simulator

#### EX-FR-038: Paper Trading Mode

The system SHALL provide a paper trading mode that simulates the complete execution pipeline without submitting orders to any live broker. Paper mode SHALL be enabled per user and SHALL be the default mode for all new users. Paper mode SHALL use the exact same code paths as live mode up to (and including) order construction, differing only at the broker routing step.

#### EX-FR-039: Paper Fill Simulation

The paper trading simulator SHALL simulate order fills as follows:
- **Market orders**: Filled immediately at signal price + simulated slippage.
- **Limit orders**: Filled when the simulated market price reaches the limit price. The simulator SHALL use real-time or delayed market data (if available) or mark limit orders as filled after a configurable delay (default: immediate fill at limit price for simplicity in MVP).
- **Stop orders**: Triggered when the simulated market price reaches the stop price; filled at stop price + slippage.

Slippage model:
- Micro contracts: 1 tick slippage (default).
- Full-size contracts: 2 ticks slippage (default).
- Slippage direction: adverse to the trader (buy = price higher, sell = price lower).
- Configurable: users can set slippage from 0 to 10 ticks.

#### EX-FR-040: Paper Position Tracking

The paper trading simulator SHALL maintain a complete position ledger:
- Track open positions with entry price (including simulated slippage), current unrealized P&L, and time in position.
- Simulate stop loss and take profit triggers based on market data feed or periodic price checks.
- Calculate and store MAE (Maximum Adverse Excursion) and MFE (Maximum Favorable Excursion) for each paper position.
- Paper P&L SHALL be stored in a separate table or with a clear `is_paper` flag. Paper trades SHALL NEVER be commingled with live trades in analytics.

#### EX-FR-041: Paper-to-Live Transition

The system SHALL enforce a configurable minimum paper trading period (default: 60 days). After the minimum period is met, the system SHALL:
1. Display a notification that the user is eligible for live trading.
2. Require the user to explicitly opt in to live trading via a confirmation flow (checkbox + typed confirmation, e.g., "I understand I am trading with real money").
3. Allow the user to continue paper trading indefinitely if they choose not to transition.
4. Maintain all paper trading history and analytics after transitioning to live.
5. Allow the user to run paper and live modes simultaneously on different broker connections.

The minimum paper period SHALL be configurable by the user (minimum: 0 days for experienced traders who accept the risk, maximum: 365 days). Setting the period to 0 SHALL require an additional acknowledgment.

### 3.10 Position Management

#### EX-FR-042: Open Position Tracking

The system SHALL maintain a real-time view of all open positions:
- Source: broker adapter position updates (live mode) or internal ledger (paper mode).
- Fields: instrument, direction, quantity, entry price, current price, unrealized P&L ($ and R-multiple), stop loss price, take profit price, time in position, MAE, MFE.
- Positions SHALL be reconciled with the broker at a configurable interval (default: every 60 seconds) and on every broker reconnection.
- Discrepancies between TrendEdge's position record and the broker's position SHALL be flagged and logged as alerts.

#### EX-FR-043: P&L Tracking

The system SHALL track P&L at multiple granularities:
- **Per-trade**: Entry price, exit price, gross P&L, commission, net P&L, R-multiple.
- **Daily**: Sum of closed trade P&L + change in unrealized P&L for open positions.
- **Weekly/Monthly/Yearly**: Aggregated from daily P&L.
- **Paper vs. Live**: Separate P&L tracking with distinct database columns or tables.

P&L SHALL be calculated using:
- Gross P&L = (exit_price - entry_price) x tick_value / tick_size x quantity (for LONG; inverted for SHORT).
- Net P&L = Gross P&L - commission.
- R-multiple = Net P&L / planned_risk_per_trade.

### 3.11 Order Lifecycle Management

#### EX-FR-044: Order State Machine

Each order SHALL follow a defined state machine:

```
CONSTRUCTED --> SUBMITTED --> [PENDING] --> PARTIAL_FILL --> FILLED
                    |              |              |
                    v              v              v
                REJECTED       CANCELLED      CANCELLED
                    |              |              |
                    v              v              v
                 [terminal]    [terminal]     [terminal]

                                               FILLED --> CLOSED (when position exit completes)
```

States:
- `CONSTRUCTED`: Order object created, not yet sent to broker.
- `SUBMITTED`: Sent to broker adapter, awaiting acknowledgment.
- `PENDING`: Broker acknowledged, order is working (limit/stop orders waiting for trigger).
- `PARTIAL_FILL`: Part of the order quantity has been filled.
- `FILLED`: Entire quantity filled.
- `REJECTED`: Broker rejected the order (insufficient margin, invalid symbol, etc.).
- `CANCELLED`: Order cancelled by user or system (OCO cancellation, circuit breaker, etc.).
- `CLOSED`: The associated position has been fully exited.

State transitions SHALL be persisted to the database with timestamps and metadata (fill price, fill quantity, rejection reason, etc.).

#### EX-FR-045: Order Event Log

Every order state transition SHALL be recorded in an `order_events` table:
- `id`, `order_id`, `previous_state`, `new_state`, `timestamp`, `broker_order_id`, `fill_price`, `fill_quantity`, `commission`, `rejection_reason`, `raw_broker_response`.
- This log is append-only and serves as the audit trail for all order activity.

#### EX-FR-046: OCO Group Management

When a bracket order's stop loss is filled:
1. The system SHALL immediately cancel the associated take profit order.
2. The system SHALL update the position to CLOSED.
3. The system SHALL create the journal entry with exit reason "STOP_LOSS".

When a bracket order's take profit is filled:
1. The system SHALL immediately cancel the associated stop loss order.
2. The system SHALL update the position to CLOSED.
3. The system SHALL create the journal entry with exit reason "TAKE_PROFIT".

If either cancellation fails (e.g., already filled due to race condition), the system SHALL detect the double fill and alert the user immediately.

### 3.12 Continuous Contract Symbol Mapping

#### EX-FR-047: Symbol Mapping Engine

The system SHALL maintain a mapping table for continuous contract symbols to specific contract months. The table SHALL be updated automatically based on CME rollover schedules. The mapping SHALL support:

- TradingView continuous symbols: NQ1!, ES1!, YM1!, RTY1!, GC1!, CL1!, SI1!, HG1!, PL1!.
- Generic TrendEdge symbols: MNQ, MES, MYM, M2K, MGC, MCL, SIL.
- Broker-specific symbols: IB uses "MNQ" + "202603", Tradovate uses "MNQH5" format.

#### EX-FR-048: Rollover Management

The system SHALL handle contract rollover:
- Track front-month and next-month contract expiration dates.
- Auto-roll symbol mappings 3 business days before first notice day (configurable).
- Notify users when a rollover occurs.
- Reject orders for expired contracts with a clear error message.
- Never auto-roll open positions. Users SHALL be alerted to manually manage positions during rollover.

#### EX-FR-049: Broker-Specific Symbol Translation

Each broker adapter SHALL implement a `translate_symbol(trendedge_symbol: str) -> str` method that converts the canonical TrendEdge symbol to the broker's expected format:
- IBKR: `Contract(symbol="MNQ", secType="FUT", exchange="CME", lastTradeDateOrContractMonth="202603")`.
- Tradovate: `"MNQH6"` (symbol + month code + year digit).
- Webull: As specified by Webull API documentation.

### 3.13 Circuit Breaker

#### EX-FR-050: Consecutive Failure Circuit Breaker

The system SHALL implement a circuit breaker that halts order submission after N consecutive broker failures (default: 3). Failure conditions include:
- Broker connection timeout (>10 seconds).
- Order rejection by broker.
- Broker API error response (5xx).
- WebSocket disconnection during order submission.

When the circuit breaker trips:
1. All pending signal processing SHALL be paused.
2. The user SHALL receive an immediate notification (Telegram, email, and dashboard alert).
3. The circuit breaker state SHALL be displayed prominently on the dashboard.
4. No new orders SHALL be submitted until the circuit breaker is manually reset by the user OR auto-resets after a configurable cooldown period (default: 15 minutes).

#### EX-FR-051: Health Check Monitoring

The system SHALL perform periodic health checks on all active broker connections:
- Ping/heartbeat every 30 seconds.
- Verify account data retrieval every 5 minutes.
- Log connection latency.
- If a health check fails 3 times consecutively, mark the broker connection as unhealthy and notify the user.

### 3.14 Manual Override

#### EX-FR-052: Manual Order Cancellation

Users SHALL be able to cancel any pending or working order from the dashboard. Cancellation SHALL:
1. Send the cancel request to the broker adapter.
2. Wait for broker confirmation (timeout: 10 seconds).
3. Update order state to CANCELLED.
4. If the order is part of a bracket group, cancel all related orders.
5. Log the manual cancellation with user ID and timestamp.

#### EX-FR-053: Manual Order Modification

Users SHALL be able to modify pending orders:
- Change limit price (for LIMIT entries).
- Move stop loss price (up/down).
- Move take profit price (up/down).
- Reduce quantity (cannot increase beyond max position size).

Modifications SHALL be validated against risk rules before submission. The system SHALL log the original and modified values.

#### EX-FR-054: Manual Position Close

Users SHALL be able to close any open position from the dashboard with a single action ("Close Position" button). This SHALL:
1. Submit a market order in the opposite direction for the full position quantity.
2. Cancel all pending stop loss and take profit orders for the position.
3. Update position status to CLOSED.
4. Create the journal entry with exit reason "MANUAL_CLOSE".

#### EX-FR-055: Emergency Flatten All

The system SHALL provide an "Emergency Flatten All" button that:
1. Submits market orders to close ALL open positions across all instruments.
2. Cancels ALL pending orders.
3. Disables signal processing until manually re-enabled.
4. Logs the emergency action with timestamp.
5. Requires confirmation before execution (but with a fast path, not multi-step).

### 3.15 Fill Reconciliation

#### EX-FR-056: Fill Reconciliation Engine

The system SHALL reconcile order fills between TrendEdge's internal records and the broker's reported fills:
- On every broker reconnection, query the broker for all fills since the last known fill timestamp.
- Compare broker fill records against TrendEdge's `order_events` table.
- Flag discrepancies: missing fills (TrendEdge has no record), extra fills (broker reports fills TrendEdge did not expect), price discrepancies (fill price differs by more than 1 tick).
- Discrepancies SHALL be logged and the user SHALL be notified.

#### EX-FR-057: Slippage Tracking

For every filled order, the system SHALL calculate and store slippage:
- Slippage = fill_price - intended_price (positive = adverse, negative = favorable).
- Slippage SHALL be stored in both tick units and dollar value.
- Aggregate slippage statistics SHALL be available in the analytics dashboard (average slippage per instrument, per broker, per time of day).

#### EX-FR-058: Commission Tracking

The system SHALL record commissions for every fill:
- Source: broker-reported commission (preferred) or calculated from the commission schedule.
- Commission schedules per broker:
  - IBKR: $0.25-$0.85 per micro contract (varies by volume tier).
  - Tradovate: $0.79 per side per micro contract (with funded account, may be $0 commissions).
  - Webull: ~$0.25 per micro contract + exchange fees.
- Commission SHALL be included in net P&L calculations.

---

## 4. Non-Functional Requirements

### 4.1 Latency

#### EX-NFR-001: End-to-End Signal Latency

The end-to-end latency from webhook receipt to broker order submission SHALL be less than 5 seconds at p50 and less than 10 seconds at p95. This target applies to the TrendEdge processing pipeline only and excludes TradingView's webhook delivery latency (which ranges from 2-60 seconds and is outside TrendEdge's control).

#### EX-NFR-002: Internal Signal Latency

Signals from the internal trendline engine SHALL reach broker order submission within 3 seconds at p95.

#### EX-NFR-003: Broker Response Latency

The system SHALL log and track broker API response times. Expected baselines:
- IBKR order submission: <500ms (TWS socket, local IB Gateway).
- Tradovate order submission: <1s (REST API).
- Acceptable degradation threshold: 5x baseline. Beyond this threshold, log a warning.

#### EX-NFR-004: Dashboard Update Latency

Order status changes SHALL be reflected on the dashboard within 2 seconds of the broker event, delivered via WebSocket push.

### 4.2 Reliability

#### EX-NFR-005: Zero Missed Signals

The system SHALL achieve zero missed signals over 30 consecutive trading days. A signal is considered "missed" if it is received by the webhook endpoint, passes validation, passes risk checks, but fails to result in an order submission attempt. Broker rejections and risk check failures are NOT missed signals (they are intentional non-executions).

#### EX-NFR-006: Signal Processing Guarantee

Every signal received SHALL be processed to a terminal state (FILLED, REJECTED, or CANCELLED) within 5 minutes. Signals that remain in a non-terminal state for more than 5 minutes SHALL trigger an alert.

#### EX-NFR-007: At-Least-Once Processing

The signal processing pipeline SHALL guarantee at-least-once processing. Combined with the deduplication logic (EX-FR-015), this provides effectively-once semantics.

### 4.3 Broker Connection Resilience

#### EX-NFR-008: Auto-Reconnection

Broker adapter connections SHALL automatically reconnect on failure with exponential backoff: initial delay 1 second, maximum delay 60 seconds, jitter +/- 500ms. The adapter SHALL attempt reconnection indefinitely until either the connection is restored or the user explicitly disables the broker connection.

#### EX-NFR-009: Connection State Visibility

The dashboard SHALL display real-time broker connection status: Connected (green), Reconnecting (yellow), Disconnected (red). Connection uptime percentage SHALL be tracked and displayed in account settings.

#### EX-NFR-010: Graceful Degradation

If the broker connection is lost while orders are pending:
- The system SHALL NOT assume orders were cancelled. It SHALL query the broker for order status upon reconnection.
- The system SHALL queue incoming signals during the disconnection and process them upon reconnection (if still within the deduplication window and the signal's entry price is still valid).
- The user SHALL be notified of the disconnection within 30 seconds.

### 4.4 Order Idempotency

#### EX-NFR-011: Idempotent Order Submission

Each order SHALL carry a unique client-side order ID (UUID) that is sent to the broker. If the same order ID is submitted twice (e.g., due to retry after a timeout), the broker SHALL reject the duplicate (IBKR and Tradovate both support client order IDs). The system SHALL treat a duplicate rejection as a success (the original order was placed).

#### EX-NFR-012: Idempotent Signal Processing

The signal processing pipeline SHALL be idempotent. Processing the same signal twice SHALL NOT result in two orders. This is enforced by the deduplication logic (EX-FR-015) and the order state machine (EX-FR-044), which prevents CONSTRUCTED orders from being submitted twice.

---

## 5. Risk Management Requirements

### 5.1 Pre-Trade Risk Controls

| Requirement ID | Control | Default | Configurable |
|---|---|---|---|
| EX-RM-001 | Maximum position size per instrument | 2 micro / 1 full-size | Yes |
| EX-RM-002 | Daily loss limit | $500 (paper), user-defined (live) | Yes |
| EX-RM-003 | Maximum concurrent open positions | 3 | Yes |
| EX-RM-004 | Minimum risk-reward ratio | 2.0 | Yes |
| EX-RM-005 | Correlation limit between positions | Warn at r > 0.7 | Yes (warn/block + threshold) |
| EX-RM-006 | Maximum single-trade risk | $200 | Yes |
| EX-RM-007 | Trading hours restriction | RTH only (default) | Yes (RTH/ETH/24h) |
| EX-RM-008 | Signal staleness rejection | Reject if signal > 5 min old | Yes (1-30 minutes) |

### 5.2 In-Trade Risk Controls

| Requirement ID | Control | Description |
|---|---|---|
| EX-RM-009 | Bracket order enforcement | Every position MUST have an active stop loss. Positions without stops SHALL trigger an alert. |
| EX-RM-010 | Stop loss modification guard | Moving a stop loss further from entry (increasing risk) SHALL require confirmation and SHALL be logged as a "stop widened" event. |
| EX-RM-011 | Break-even stop | When position reaches 1R profit, the system SHALL offer to move stop to break-even (configurable auto vs. manual). |

### 5.3 Post-Trade Risk Controls

| Requirement ID | Control | Description |
|---|---|---|
| EX-RM-012 | Daily loss limit lockout | When daily loss limit is hit, the system SHALL block all new orders until the next trading day. |
| EX-RM-013 | Consecutive loss cooldown | After N consecutive losses (default: 3), the system SHALL require manual confirmation for the next trade. Configurable: off, 2-5 losses. |
| EX-RM-014 | Weekly drawdown warning | If cumulative weekly P&L exceeds a configurable warning threshold (default: -$1,000), the system SHALL display a prominent warning. |

---

## 6. Dependencies on Other PRDs

| PRD | Dependency | Type | Description |
|---|---|---|---|
| PRD-001: Foundation & Infrastructure | Hard | Database schema, authentication, API framework, Redis for pub/sub and rate limiting. Execution pipeline cannot function without the foundation. |
| PRD-002: Trendline Detection Engine | Soft | Internal signal source. The execution pipeline accepts signals from the trendline engine but also works independently with webhooks and manual entry. |
| PRD-004: Trade Journaling | Soft (downstream) | Post-fill processing creates journal entries. The execution pipeline emits events; journaling consumes them. Execution functions without journaling during development. |
| PRD-005: Analytics & Playbook System | Soft (downstream) | Closed trades feed analytics. Execution pipeline emits trade close events; analytics consumes them. |
| PRD-006: Dashboard & Frontend | Soft | Dashboard provides the UI for manual signal entry, order management, position monitoring, and circuit breaker controls. Backend API works without frontend (API-first). |
| PRD-007: AI Features | None | No direct dependency. AI features consume trade data but do not participate in execution. |
| PRD-008: Notifications | Soft (downstream) | Post-fill and error notifications are routed through the notification system. Execution pipeline can function without notifications (logs serve as fallback). |
| PRD-009: Auth & Multi-Tenancy | Hard | User authentication, broker credential storage, and user-scoped data isolation are required for the execution pipeline to function in multi-user mode. |
| PRD-010: Market Data | Soft | Real-time market data feeds into price validation, paper trading simulation, and P&L tracking. Without market data, the system can still route orders to brokers (brokers have their own data). |
| PRD-011: DevOps & Infrastructure | Soft | IB Gateway hosting, deployment pipeline, monitoring, and alerting. |

---

## 7. Testing Requirements

### 7.1 Paper Trading Validation

#### EX-TEST-001: Paper Trade End-to-End

Verify that a signal submitted via webhook results in a paper trade with correct entry price (including slippage), stop loss, take profit, and that the trade appears in the position list and P&L calculations.

#### EX-TEST-002: Paper Fill Accuracy

Compare paper trading results against historical market data over a 60-day period. Paper fills (with simulated slippage) SHALL be within 2 ticks of what a live execution would have achieved for market orders during regular trading hours.

#### EX-TEST-003: Paper Stop Loss Trigger

Verify that paper stop loss orders trigger correctly when price reaches the stop level, and that the resulting P&L matches the expected loss (entry to stop, adjusted for slippage and commissions).

#### EX-TEST-004: Paper Take Profit Trigger

Verify that paper take profit orders trigger correctly when price reaches the target level, and that the resulting P&L matches the expected profit.

#### EX-TEST-005: Paper OCO Behavior

Verify that when a paper stop loss triggers, the corresponding take profit is cancelled (and vice versa), and only one exit fill is recorded.

### 7.2 Broker Adapter Mock Testing

#### EX-TEST-006: IBKR Adapter Unit Tests

Unit tests for the IBKR adapter using a mock `ib_async.IB` client. Tests SHALL cover:
- Connection establishment and reconnection.
- Order submission (market, limit, stop).
- Bracket order construction with OCA groups.
- Fill event processing (full fill, partial fill).
- Order cancellation.
- Account data retrieval.
- Error handling for all common IB error codes (110, 201, 502, 1100).

#### EX-TEST-007: Tradovate Adapter Unit Tests

Unit tests for the Tradovate adapter using `httpx` mock responses and mock WebSocket messages. Tests SHALL cover:
- OAuth token acquisition and refresh.
- Order submission via REST.
- OSO bracket order submission.
- WebSocket order/fill/position event processing.
- Token expiration handling (verify proactive refresh at 50 minutes).
- Error handling for HTTP 4xx and 5xx responses.

#### EX-TEST-008: Adapter Interface Compliance

A parameterized test suite that runs against every broker adapter implementation to verify it conforms to the `BrokerAdapter` ABC. Tests verify that all abstract methods are implemented, return the correct types, and raise the correct exceptions.

### 7.3 End-to-End Signal Flow Testing

#### EX-TEST-009: Webhook-to-Order Flow

End-to-end test: POST a TradingView-formatted webhook to the endpoint, verify the signal is received, validated, enriched, risk-checked, and results in a paper order. Assert correct state transitions in the `order_events` table.

#### EX-TEST-010: Internal Signal-to-Order Flow

End-to-end test: Publish a trendline break signal to the internal message bus, verify it flows through the pipeline identically to webhook signals.

#### EX-TEST-011: Manual Signal-to-Order Flow

End-to-end test: Submit a manual signal via the API (simulating the dashboard form), verify the complete pipeline processes it.

#### EX-TEST-012: Risk Check Rejection Flow

End-to-end test: Submit signals that violate each risk check (position size, daily loss, concurrent positions, R:R ratio) and verify each is rejected with the correct reason and audit trail.

#### EX-TEST-013: Duplicate Signal Rejection

Submit the same signal twice within the deduplication window. Verify only one order is created and the second signal is rejected with reason "DUPLICATE_SIGNAL".

### 7.4 Failover Testing

#### EX-TEST-014: Broker Disconnection During Order

Simulate a broker connection drop during order submission. Verify:
- The system detects the failure.
- The circuit breaker counter increments.
- The user is notified.
- Upon reconnection, the system reconciles order status with the broker.

#### EX-TEST-015: Circuit Breaker Trip

Simulate 3 consecutive broker failures. Verify:
- The circuit breaker trips after the 3rd failure.
- No further orders are submitted.
- The user is notified.
- The circuit breaker auto-resets after the cooldown period (or manual reset).

#### EX-TEST-016: Token Expiration During Order (Tradovate)

Simulate a Tradovate OAuth token expiring mid-session. Verify:
- The adapter detects the 401 response.
- The adapter refreshes the token.
- The original request is retried with the new token.
- No orders are lost.

#### EX-TEST-017: IB Gateway Restart

Simulate an IB Gateway restart (connection drop + reconnect). Verify:
- The adapter detects the disconnection.
- Auto-reconnection succeeds.
- Open positions and pending orders are reconciled.
- No phantom orders are created.

### 7.5 Latency Benchmarking

#### EX-TEST-018: Pipeline Latency Benchmark

Measure end-to-end pipeline latency (webhook receipt to broker submission) under the following conditions:
- Baseline: single signal, no open positions, no concurrent signals.
- Load: 10 concurrent signals from different users.
- Stress: 50 concurrent signals from different users.

Results SHALL be compared against targets (EX-NFR-001): <5s p50, <10s p95.

#### EX-TEST-019: Broker API Latency Tracking

Run a daily latency benchmark against each broker API (paper mode):
- IBKR: Submit and cancel a limit order, measure round-trip time.
- Tradovate: Submit and cancel a limit order via REST, measure round-trip time.
- Log results to a time-series for trend analysis.

---

## 8. Security Considerations

### 8.1 Broker Credentials

#### EX-SEC-001: Credential Encryption at Rest

Broker API credentials (API keys, secrets, OAuth tokens, IB Gateway passwords) SHALL be encrypted at rest using AES-256-GCM. Encryption keys SHALL be stored separately from the encrypted data (e.g., environment variables or a dedicated secrets manager such as Railway's built-in secrets or AWS Secrets Manager). Credentials SHALL NEVER appear in application logs, error messages, or API responses.

#### EX-SEC-002: Credential Transmission

Broker credentials SHALL only be transmitted over TLS 1.2+. Internal service-to-service communication involving credentials SHALL also use encrypted channels. Credentials SHALL NEVER be included in URL query parameters.

#### EX-SEC-003: Credential Rotation

The system SHALL support credential rotation without downtime. Users SHALL be able to update their broker API keys from the dashboard. The previous credential SHALL be invalidated immediately upon successful validation of the new credential.

### 8.2 Webhook Security

#### EX-SEC-004: HMAC Signature Validation

Webhook endpoints SHALL validate the HMAC-SHA256 signature of the request body using the user's secret key. Signature comparison SHALL use constant-time comparison (`hmac.compare_digest` in Python) to prevent timing attacks.

#### EX-SEC-005: Webhook URL Security

Webhook URLs SHALL contain a minimum 32-character cryptographically random identifier generated using `secrets.token_urlsafe(32)`. Webhook IDs SHALL NOT be sequential or predictable. The system SHALL support webhook URL regeneration, immediately invalidating the previous URL.

#### EX-SEC-006: Replay Attack Prevention

Webhook requests SHALL include a timestamp. Requests older than 5 minutes SHALL be rejected to prevent replay attacks. The system SHALL also maintain a short-lived cache (5 minutes) of processed request IDs to reject exact duplicates.

### 8.3 API Key Management

#### EX-SEC-007: User API Key Generation

Each user SHALL be issued a unique API key for webhook authentication. API keys SHALL be:
- Generated using `secrets.token_urlsafe(32)` (minimum 256 bits of entropy).
- Stored as a SHA-256 hash in the database (the plaintext is shown to the user exactly once upon generation).
- Revocable by the user at any time from the dashboard.
- Rotatable: users can generate a new key, which invalidates the old key.

#### EX-SEC-008: API Key Scoping

API keys SHALL be scoped to specific permissions:
- `signal:write` -- can submit signals via webhook.
- `order:read` -- can query order status.
- `position:read` -- can query positions.

The default API key SHALL have `signal:write` permission only. Additional scopes require explicit user opt-in.

### 8.4 Audit and Compliance

#### EX-SEC-009: Execution Audit Log

All order-related actions SHALL be logged to an immutable audit log:
- Signal receipt (source, payload, timestamp).
- Risk check results (all checks, pass/fail, values).
- Order submission (broker, order details, client order ID).
- Fill events (price, quantity, commission, timestamp).
- Manual overrides (cancellations, modifications, position closes, flatten-all).
- Authentication events (webhook auth success/failure, broker connection changes).

The audit log SHALL be append-only and SHALL NOT be deletable by users or application code. Retention: minimum 7 years (to satisfy potential regulatory inquiries).

#### EX-SEC-010: IP Allowlisting for Webhooks

The system SHALL support optional IP allowlisting for webhook endpoints. If configured, only requests from allowed IP addresses SHALL be accepted. TradingView's webhook source IPs SHALL be documented and pre-configurable.

---

## 9. Phase Mapping

### 9.1 Phase 1: Paper Trading Foundation (Weeks 5-6)

**Goal**: Complete execution pipeline working end-to-end in paper mode with IBKR and Tradovate adapters.

| Deliverable | Requirements Covered | Priority |
|---|---|---|
| Signal ingestion (webhook + manual) | EX-FR-001 through EX-FR-009 | P0 |
| Signal validation & enrichment | EX-FR-010 through EX-FR-015 | P0 |
| Risk management engine (all pre-trade checks) | EX-FR-016 through EX-FR-022 | P0 |
| Bracket order construction | EX-FR-023 through EX-FR-027 | P0 |
| Broker adapter interface | EX-FR-028, EX-FR-029 | P0 |
| IBKR adapter (paper mode) | EX-FR-030 through EX-FR-033 | P0 |
| Tradovate adapter (paper mode) | EX-FR-034 through EX-FR-037 | P0 |
| Paper trading simulator | EX-FR-038 through EX-FR-041 | P0 |
| Order lifecycle management | EX-FR-044 through EX-FR-046 | P0 |
| Symbol mapping (core instruments) | EX-FR-047 through EX-FR-049 | P0 |
| Circuit breaker | EX-FR-050, EX-FR-051 | P0 |

**Exit Criteria**:
- TradingView webhook triggers a paper trade in <10 seconds (p95).
- All risk checks enforced and logged.
- Paper P&L tracking accurate to within 2 ticks of expected.
- IBKR and Tradovate adapters pass interface compliance tests.
- Circuit breaker trips after 3 consecutive failures.

### 9.2 Phase 2: Live Trading (Weeks 7-8 of development, after 60-day paper period)

**Goal**: Enable live order routing to IBKR and Tradovate with full risk controls.

| Deliverable | Requirements Covered | Priority |
|---|---|---|
| Live order routing (IBKR) | EX-FR-030 through EX-FR-033 (live mode) | P0 |
| Live order routing (Tradovate) | EX-FR-034 through EX-FR-037 (live mode) | P0 |
| Paper-to-live transition flow | EX-FR-041 | P0 |
| Fill reconciliation engine | EX-FR-056 through EX-FR-058 | P0 |
| Position management (live) | EX-FR-042, EX-FR-043 | P0 |
| Manual override capabilities | EX-FR-052 through EX-FR-055 | P0 |
| Slippage & commission tracking | EX-FR-057, EX-FR-058 | P0 |
| In-trade risk controls | EX-RM-009 through EX-RM-011 | P0 |
| Post-trade risk controls | EX-RM-012 through EX-RM-014 | P0 |
| All security requirements | EX-SEC-001 through EX-SEC-010 | P0 |

**Exit Criteria**:
- Live order placed and filled on IBKR paper account (IB's own paper environment).
- Live order placed and filled on Tradovate demo account.
- Fill reconciliation detects and flags intentionally introduced discrepancies.
- Emergency flatten-all closes all positions within 5 seconds.
- Zero data leakage between paper and live P&L.

### 9.3 Phase 3: Webull + Multi-Account (Weeks 19-20)

**Goal**: Add Webull broker support and enable multi-account execution from a single signal.

| Deliverable | Requirements Covered | Priority |
|---|---|---|
| Webull adapter implementation | New (modeled on EX-FR-034 through EX-FR-037) | P1 |
| Multi-account order routing | Extension of EX-FR-029 | P1 |
| Account-level risk isolation | Extension of EX-FR-016 through EX-FR-022 | P1 |
| Prop firm support (multi-account) | New | P1 |
| Rithmic adapter (research/prototype) | New | P2 |

**Exit Criteria**:
- Webull adapter passes interface compliance tests.
- Single signal routes to 3+ accounts simultaneously.
- Per-account risk limits enforced independently.
- Cross-account position correlation tracked.

---

## 10. Acceptance Criteria

### 10.1 Signal Pipeline Acceptance

| ID | Criterion | Measurement |
|---|---|---|
| AC-EX-001 | TradingView webhook signal received and acknowledged within 2 seconds. | Automated test: POST webhook, measure response time. Target: p95 < 2s. |
| AC-EX-002 | End-to-end webhook-to-paper-trade latency under 10 seconds. | Automated test: POST webhook, measure time until paper fill recorded. Target: p95 < 10s. |
| AC-EX-003 | Internal engine signal-to-paper-trade latency under 5 seconds. | Automated test: publish internal signal, measure time until paper fill. Target: p95 < 5s. |
| AC-EX-004 | Manual signal-to-paper-trade latency under 3 seconds. | Automated test: submit manual signal via API, measure time until paper fill. Target: p95 < 3s. |
| AC-EX-005 | Zero missed signals over 30 consecutive trading days. | Production monitoring: count signals received vs. signals processed to terminal state. Target: 0 missed. |
| AC-EX-006 | Duplicate signals rejected without creating duplicate orders. | Automated test: submit identical signal twice within 5 minutes. Assert exactly 1 order created. |

### 10.2 Risk Management Acceptance

| ID | Criterion | Measurement |
|---|---|---|
| AC-EX-007 | Position size limit enforced correctly. | Automated test: submit signal that would exceed max position size. Assert rejection with reason. |
| AC-EX-008 | Daily loss limit blocks orders when reached. | Automated test: simulate losses reaching daily limit, then submit new signal. Assert rejection. |
| AC-EX-009 | Concurrent position limit enforced. | Automated test: open max positions, submit one more signal. Assert rejection. |
| AC-EX-010 | R:R ratio check rejects sub-threshold signals. | Automated test: submit signal with 1.5R when minimum is 2.0R. Assert rejection. |
| AC-EX-011 | All risk checks produce audit trail entries. | Automated test: submit signal, query audit trail. Assert all checks logged with values. |

### 10.3 Broker Integration Acceptance

| ID | Criterion | Measurement |
|---|---|---|
| AC-EX-012 | IBKR adapter connects, submits, and receives fill confirmation. | Integration test: connect to IB Gateway (paper), submit market order, assert fill received. |
| AC-EX-013 | IBKR adapter reconnects automatically after disconnection. | Integration test: kill IB Gateway connection, verify reconnection within 60 seconds. |
| AC-EX-014 | Tradovate adapter authenticates, submits order, receives fill. | Integration test: authenticate with Tradovate demo, submit order, assert fill. |
| AC-EX-015 | Tradovate adapter refreshes expired OAuth token without order loss. | Integration test: expire token, submit order, verify token refreshed and order placed. |
| AC-EX-016 | Bracket orders create correct OCO groups on both brokers. | Integration test: submit bracket order, fill entry, trigger SL, verify TP cancelled (and vice versa). |
| AC-EX-017 | Symbol mapping resolves NQ1! to correct MNQ contract month. | Unit test: mock current date near rollover, verify correct month resolution. |

### 10.4 Paper Trading Acceptance

| ID | Criterion | Measurement |
|---|---|---|
| AC-EX-018 | Paper trades execute identically to live pipeline (minus broker routing). | Code review: verify paper mode shares all code paths except broker adapter call. |
| AC-EX-019 | Paper P&L completely separated from live P&L. | Automated test: create paper and live trades, query P&L. Assert separate results. |
| AC-EX-020 | Paper slippage simulation applies correct tick values. | Unit test: submit paper market order for MNQ. Assert fill price = signal price + 1 tick (0.25 points). |
| AC-EX-021 | Paper trading period enforcement prevents early live trading. | Automated test: attempt to enable live trading before 60-day period. Assert rejection. |

### 10.5 Resilience Acceptance

| ID | Criterion | Measurement |
|---|---|---|
| AC-EX-022 | Circuit breaker trips after 3 consecutive failures. | Automated test: simulate 3 broker failures, verify circuit breaker state, verify no further orders submitted. |
| AC-EX-023 | Circuit breaker auto-resets after cooldown period. | Automated test: trip circuit breaker, wait cooldown, verify orders resume. |
| AC-EX-024 | Fill reconciliation detects missing fills. | Integration test: inject a fill on broker side without TrendEdge knowing. Run reconciliation. Assert discrepancy flagged. |
| AC-EX-025 | Emergency flatten-all closes all positions and cancels all orders. | Integration test: open 3 paper positions with pending orders. Execute flatten-all. Assert all closed/cancelled within 5 seconds. |

### 10.6 Security Acceptance

| ID | Criterion | Measurement |
|---|---|---|
| AC-EX-026 | Invalid webhook API key returns HTTP 401. | Automated test: POST webhook with invalid key. Assert 401 response. |
| AC-EX-027 | HMAC signature validation rejects tampered payloads. | Automated test: POST webhook with valid HMAC, then modify body. Assert rejection. |
| AC-EX-028 | Broker credentials never appear in logs. | Log audit: search all log output for known test credentials. Assert zero matches. |
| AC-EX-029 | Webhook rate limiting enforced at 10 req/min. | Load test: POST 20 webhooks in 1 minute. Assert first 10 accepted, remaining receive HTTP 429. |
| AC-EX-030 | Replay attack prevention rejects stale webhooks. | Automated test: POST webhook with timestamp 10 minutes in the past. Assert rejection. |

---

## Appendix A: Data Models

### A.1 Signal Table

```sql
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    source VARCHAR(20) NOT NULL CHECK (source IN ('INTERNAL', 'WEBHOOK', 'MANUAL')),
    source_metadata JSONB,
    instrument VARCHAR(20) NOT NULL,
    direction VARCHAR(5) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    entry_type VARCHAR(10) NOT NULL CHECK (entry_type IN ('MARKET', 'LIMIT')),
    entry_price DECIMAL(12,4) NOT NULL,
    stop_loss_price DECIMAL(12,4) NOT NULL,
    take_profit_price DECIMAL(12,4) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    risk_reward_ratio DECIMAL(4,2),
    trendline_id UUID REFERENCES trendlines(id),
    trendline_grade VARCHAR(5),
    status VARCHAR(20) NOT NULL DEFAULT 'RECEIVED',
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    is_paper BOOLEAN NOT NULL DEFAULT TRUE
);
```

### A.2 Orders Table

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID NOT NULL REFERENCES signals(id),
    user_id UUID NOT NULL REFERENCES users(id),
    broker VARCHAR(20) NOT NULL,
    broker_order_id VARCHAR(100),
    client_order_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    order_type VARCHAR(15) NOT NULL,
    side VARCHAR(5) NOT NULL,
    instrument VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(12,4),
    stop_price DECIMAL(12,4),
    status VARCHAR(20) NOT NULL DEFAULT 'CONSTRUCTED',
    bracket_group_id UUID,
    bracket_role VARCHAR(15) CHECK (bracket_role IN ('ENTRY', 'STOP_LOSS', 'TAKE_PROFIT')),
    fill_price DECIMAL(12,4),
    fill_quantity INTEGER,
    commission DECIMAL(8,4),
    slippage_ticks DECIMAL(6,2),
    slippage_dollars DECIMAL(8,4),
    is_paper BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    filled_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);
```

### A.3 Order Events Table

```sql
CREATE TABLE order_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    previous_state VARCHAR(20),
    new_state VARCHAR(20) NOT NULL,
    broker_order_id VARCHAR(100),
    fill_price DECIMAL(12,4),
    fill_quantity INTEGER,
    commission DECIMAL(8,4),
    rejection_reason TEXT,
    raw_broker_response JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### A.4 Positions Table

```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    signal_id UUID REFERENCES signals(id),
    entry_order_id UUID REFERENCES orders(id),
    instrument VARCHAR(20) NOT NULL,
    direction VARCHAR(5) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(12,4) NOT NULL,
    current_price DECIMAL(12,4),
    stop_loss_price DECIMAL(12,4),
    take_profit_price DECIMAL(12,4),
    unrealized_pnl DECIMAL(12,4),
    realized_pnl DECIMAL(12,4),
    commission_total DECIMAL(8,4),
    r_multiple DECIMAL(6,2),
    mae_ticks DECIMAL(8,2),
    mfe_ticks DECIMAL(8,2),
    mae_dollars DECIMAL(12,4),
    mfe_dollars DECIMAL(12,4),
    status VARCHAR(10) NOT NULL DEFAULT 'OPEN',
    exit_reason VARCHAR(20),
    is_paper BOOLEAN NOT NULL DEFAULT TRUE,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);
```

### A.5 Risk Check Audit Table

```sql
CREATE TABLE risk_check_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID NOT NULL REFERENCES signals(id),
    check_name VARCHAR(50) NOT NULL,
    result VARCHAR(10) NOT NULL CHECK (result IN ('PASS', 'FAIL', 'WARN')),
    actual_value DECIMAL(12,4),
    threshold_value DECIMAL(12,4),
    details JSONB,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Appendix B: Contract Specifications Reference

| Symbol | Instrument | Tick Size | Tick Value | Exchange | Margin (Day) |
|---|---|---|---|---|---|
| MNQ | Micro E-mini Nasdaq | 0.25 | $0.50 | CME | ~$920 |
| MES | Micro E-mini S&P 500 | 0.25 | $1.25 | CME | ~$660 |
| MYM | Micro E-mini Dow | 1.00 | $0.50 | CBOT | ~$440 |
| M2K | Micro E-mini Russell | 0.10 | $0.50 | CME | ~$360 |
| MGC | Micro Gold | 0.10 | $1.00 | COMEX | ~$780 |
| MCL | Micro Crude Oil | 0.01 | $1.00 | NYMEX | ~$590 |
| SIL | Micro Silver | 0.005 | $2.50 | COMEX | ~$930 |
| NQ | E-mini Nasdaq | 0.25 | $5.00 | CME | ~$9,200 |
| ES | E-mini S&P 500 | 0.25 | $12.50 | CME | ~$6,600 |

Note: Margin values are approximate and vary by broker and market conditions.

---

## Appendix C: Futures Month Codes

| Code | Month |
|---|---|
| F | January |
| G | February |
| H | March |
| J | April |
| K | May |
| M | June |
| N | July |
| Q | August |
| U | September |
| V | October |
| X | November |
| Z | December |

Example: `MNQH6` = Micro E-mini Nasdaq, March 2026.

---

*PRD-003 v1.0 -- Trade Execution Pipeline & Broker Integration*
*TrendEdge -- February 2026*

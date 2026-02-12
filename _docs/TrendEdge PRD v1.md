# TrendEdge — Product Requirements Document

**AI-Powered Futures Trading Platform**
Trendline Detection · Automated Execution · Trade Journaling · Performance Analytics

Version 1.0 · February 2026 · CONFIDENTIAL

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Positioning](#2-product-vision--positioning)
3. [Target Users & Personas](#3-target-users--personas)
4. [Competitive Landscape](#4-competitive-landscape)
5. [Core Feature Set](#5-core-feature-set)
6. [Technical Architecture](#6-technical-architecture)
7. [Integrations](#7-integrations)
8. [Pricing & Monetization](#8-pricing--monetization)
9. [MVP Scope & Development Phases](#9-mvp-scope--development-phases)
10. [Success Metrics](#10-success-metrics)
11. [Risks & Mitigations](#11-risks--mitigations)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

**TrendEdge** is a unified SaaS platform that combines automated trendline detection, webhook-based futures trade execution, intelligent journaling, and performance analytics into a single system. No competitor today offers all four capabilities together—retail futures traders currently spend $100–300/month cobbling together 3–4 separate tools (TradingView + TradeZella + TradersPost/PickMyTrade) to achieve what TrendEdge delivers in one integrated experience.

The platform is purpose-built for swing traders operating on 1-hour to daily timeframes, with first-class support for the trendline-based methodology popularized by Tori Trades (Victoria Duke). Her A+ trendline criteria—3+ touchpoints, <45° slope, 6+ candle spacing, 3+ weeks of price history—are fully codifiable and serve as the foundation for TrendEdge's automated detection engine.

### Market Opportunity

The retail futures trading tools market is estimated at $5.1 billion (2024), projected to reach $10.2 billion by 2033 at 8.5% CAGR. CME Micro E-mini contracts surpassed 3 billion cumulative contracts traded by November 2024. An estimated 1–2 million active US retail futures traders are spending on fragmented tooling. Even capturing 0.5% market share at $79/month average revenue yields $4.7–9.5 million ARR.

### The Gap We Fill

| Capability | TradeZella | TradersPost | PickMyTrade | TrendEdge |
|---|---|---|---|---|
| Trendline Detection | ✘ | ✘ | ✘ | ✔ |
| Trade Execution | ✘ | ✔ | ✔ | ✔ |
| Trade Journaling | ✔ | ✘ | ✘ | ✔ |
| Playbook Analytics | ✔ | ✘ | ✘ | ✔ |
| Performance Metrics | ✔ | ✘ | ✘ | ✔ |
| AI Insights | Basic | ✘ | ✘ | ✔ |
| Paper Trading Mode | ✘ | ✔ | ✔ | ✔ |
| Prop Firm Support | ✘ | ✘ | ✔ | ✔ |
| Monthly Cost | $29–49 | $49–299 | $50 | $49–99 |

---

## 2. Product Vision & Positioning

### Vision Statement

> **TrendEdge is the first platform where trendline detection, trade execution, and performance analytics live in one system** — enabling futures swing traders to detect setups algorithmically, execute automatically, journal every trade with full context, and continuously improve through data-driven insights.

### Core Principles

- **Build for one, then for many.** The platform is built as a personal trading system first. Every feature must work flawlessly for a single power user before being generalized for multi-tenant SaaS.

- **Automate the mechanical, preserve the discretionary.** Roughly 70% of a trendline strategy is codifiable. The remaining 30% — context reading, false breakout filtering — is supported through AI assistance rather than replaced by it.

- **Execution discipline over algorithmic sophistication.** Risk management, position sizing, and psychological discipline determine outcomes more than signal complexity. The platform enforces discipline by design.

- **Futures-first, not futures-also.** Contract specifications, margin types, session times, rollover management, and Section 1256 tax treatment are first-class concepts, not afterthoughts.

### Build-Then-Productize Strategy

1. **Phase 1 — Personal Trading System.** Build the complete platform for internal use. Paper trade, then live trade with micro futures. Validate the integrated system outperforms the fragmented tool stack.

2. **Phase 2 — Multi-Tenant SaaS.** Add authentication, billing, onboarding, and multi-broker support. Launch to waitlist from r/algotrading, Futures.io, and YouTube trading communities.

---

## 3. Target Users & Personas

### Primary: The Trendline Swing Trader

| Attribute | Description |
|---|---|
| Archetype | Victoria Duke (Tori Trades) and her 330K+ YouTube subscriber community |
| Strategy | Pure price-action trendlines, no indicators. 4H primary timeframe, daily/weekly for direction |
| Instruments | Platinum (PL), Crude Oil (CL), Gold (GC), Dow (YM) futures |
| Trade Frequency | ~1 trade/month (low frequency, high conviction) |
| Current Stack | TradingView ($15–60/mo) + TradeZella ($29–49/mo) + manual execution |
| Pain Points | Manual trendline monitoring, no automated alerts for multi-touch setups, fragmented tools |
| Willingness to Pay | $49–99/month for a unified solution |

### Secondary: The Algo-Curious Retail Trader

| Attribute | Description |
|---|---|
| Archetype | Developer or technical professional learning systematic trading |
| Strategy | MA crossovers, Donchian breakouts, mean reversion — simple systematic strategies |
| Instruments | MES, MNQ micro futures (lower capital requirements) |
| Trade Frequency | Daily to weekly signals |
| Current Stack | TradingView + TradersPost/PickMyTrade + spreadsheet journaling |
| Pain Points | No unified analytics on automated trades, can't A/B test strategy variants |

### Tertiary: Prop Firm Trader

Prop firm traders managing 5–20+ funded accounts need multi-account execution from a single signal, consistency metrics matching prop firm evaluation criteria (daily loss limits, trailing drawdown), and centralized performance tracking. They represent the highest LTV segment ($199+/month) and the fastest-growing market segment.

---

## 4. Competitive Landscape

### Trade Journaling Competitors

| Tool | Price | Strengths | Weaknesses |
|---|---|---|---|
| TradeZella | $29–49/mo | Playbook system, trade replay, Zella AI, Tori Trades partnership | No automation, no free tier, broker sync failures, no mobile app |
| Tradervue | $0–49.95/mo | 80+ broker integrations, 13 years mature, community sharing | Dated UI, futures requires $29.95+ plan, no replay/backtesting |
| Edgewonk | $169/year | Best value, Tiltmeter psychology tracking, AI Edge Finder | No real-time features, file-import only, no trade replay |
| Journalytix | $47/mo | Futures-native, real-time news squawk, prop firm metrics | Expensive, locked to Jigsaw/NinjaTrader ecosystem |
| TradesViz | $0–29.99/mo | Generous free tier, 100+ chart types, fast imports | Less polished UI, no AI features, smaller community |

### Trade Automation Competitors

| Tool | Price | Futures Brokers | Key Limitation |
|---|---|---|---|
| TradersPost | $49–299/mo | Tradovate, NinjaTrader, tastytrade (17 total) | No analytics, IBKR beta (stocks only), continuous symbol issues |
| PickMyTrade | $50/mo flat | Tradovate, Rithmic, IBKR, TradeStation, 8+ prop firms | No analytics/journaling, trailing stops Tradovate-only |
| SignalStack | $0.59–1.49/signal | 33+ brokers (widest support) | Per-signal pricing expensive for active traders |

### The Critical Gap

> **No competitor unifies detection + execution + journaling + analytics.** Traders today pay $94–409/month across 3–4 fragmented tools. Trade context is lost between systems — the webhook middleware doesn't know which playbook a trade belongs to, the journal doesn't know the original signal parameters, and neither tracks trendline quality metrics. TrendEdge closes this loop.

---

## 5. Core Feature Set

### F1: Automated Trendline Detection & Alerts

The signature differentiator. TrendEdge algorithmically identifies trendlines meeting configurable quality criteria, scores them, and fires alerts when price interacts with qualifying lines.

#### Detection Algorithm

The detection pipeline runs server-side in Python on 4H candle data:

1. **Swing Point Detection.** Identify pivot highs/lows using N-bar confirmation (default N=5). Williams Fractals (N=2) available as higher-sensitivity alternative.

2. **Candidate Line Generation.** Connect all valid pivot pairs. Evaluate N×(N-1)/2 candidate lines using exhaustive search with RANSAC for outlier-robust fitting.

3. **Touch Scoring.** Count additional pivots within ATR-scaled tolerance (0.5×ATR default). A "touch" requires the wick (not body) to intersect the line.

4. **A+ Quality Filtering.** Apply filters: ≥3 touches, ≥6 candles between touches, slope <45°, ≥3 weeks from first touch, ≥1 week from first touch to entry zone.

5. **Ranking.** Score by touch count × spacing quality × duration × inverse slope. Surface top 3–5 lines per instrument.

#### Alert Types

| Alert | Trigger | Payload Data |
|---|---|---|
| Trendline Break | 4H candle closes past qualifying trendline | Direction, touch count, slope, duration, safety line, 2R target |
| Trendline Touch | Price tests qualifying trendline (within 0.5×ATR) | Touch number, trendline age, slope, bounce/break probability |
| New A+ Trendline | New line qualifies as A+ grade | Instrument, direction, touch points, projected interaction price |
| Trendline Invalidated | Previously qualifying line broken without entry | Removal reason, replacement candidates |

#### Configurable Parameters

- Minimum touch count (default: 3, range: 2–5)
- Minimum candle spacing between touches (default: 6, range: 3–20)
- Maximum slope angle (default: 45°, range: 15°–75°)
- Minimum trendline duration (default: 3 weeks, range: 1 week–6 months)
- Touch tolerance (default: 0.5×ATR, range: 0.2–1.5×ATR)
- Pivot sensitivity (N-bar lookback: 2–10)

---

### F2: Trade Execution Pipeline

TrendEdge receives signals from its own trendline engine or TradingView webhooks, applies risk management rules, and routes orders to the user's broker.

#### Signal Flow

1. **Signal Ingestion.** Accept signals via: (a) internal trendline engine alerts, (b) TradingView webhook POST, or (c) manual entry through dashboard.

2. **Validation & Enrichment.** Verify signal authenticity (API key + HMAC signature), map continuous symbols (NQ1! → MNQ current month), attach trendline metadata.

3. **Risk Check.** Enforce: max position size, daily loss limit, max concurrent positions, minimum R:R ratio, correlation limits across open positions.

4. **Order Construction.** Build bracket order: market/limit entry + stop loss (safety line @ 4th candle) + take profit (first S/R at ≥2R).

5. **Broker Routing.** Send via broker adapter (IBKR, Tradovate, or Webull). Log order ID, fill price, timestamp, slippage.

6. **Post-Fill.** Auto-create journal entry with full context. Send Telegram/Discord notification. Update dashboard via WebSocket.

#### Supported Brokers

| Broker | API Type | Micro Commission | Priority | Notes |
|---|---|---|---|---|
| Interactive Brokers | TWS Socket + REST | $0.25–0.85 | P0 (MVP) | Most mature API via ib_async, requires IB Gateway on VPS |
| Tradovate | REST + WebSocket | $0.79/side | P0 (MVP) | Clean API, free with funded account, OAuth tokens expire hourly |
| Webull | REST/gRPC/MQTT | ~$0.25 + exchange | P1 | New API (Dec 2025), Python SDK, app secret expires 24h–7d |
| Rithmic | Protocol Buffers | Varies | P2 | Prop firm standard, complex integration |

#### Paper Trading Mode

All execution features work identically in paper trading mode. The system simulates fills using signal price + configurable slippage (default: 1 tick for micro, 2 ticks for full-size). Paper P&L and analytics are tracked separately with a clear visual indicator. Users must complete a configurable minimum paper period (default: 60 days) before live order routing is enabled.

---

### F3: Trade Journaling

Every trade is automatically logged with full context from the execution pipeline. Users enrich entries with discretionary notes, emotional state, and chart screenshots.

#### Automatic Capture (Zero-Input Journaling)

- Entry/exit timestamps, prices, and fills (with slippage calculation)
- Contract specification (instrument, tick size, tick value, notional exposure)
- Signal source (internal trendline engine, TradingView webhook, or manual)
- Trendline metadata: touch count, slope, duration, candle spacing, grade (A+/A/B)
- Setup classification: break vs. bounce, long vs. short
- Risk parameters: stop distance, target distance, planned R:R, actual R-multiple
- MAE/MFE (Maximum Adverse/Favorable Excursion) tracked tick-by-tick
- Session context: RTH vs. overnight, day of week, time of day
- Margin type used: day-trade vs. overnight

#### Manual Enrichment

- Pre-trade conviction level (1–5 scale)
- Emotional state tags: confident, anxious, FOMO, revenge, patient, disciplined
- Chart screenshot upload with annotation tools
- Free-text trade notes (pre-trade thesis + post-trade review)
- Rule compliance checklist (did you follow your playbook?)
- Mistake tags: moved stop, entered early, oversized, held too long, exited too early

---

### F4: Playbook System

Every trade is tagged to a named playbook for independent performance tracking. Inspired by TradeZella's model but enhanced with automated classification from trendline engine metadata.

#### Default Playbooks

| Playbook | Criteria | Auto-Classification |
|---|---|---|
| A+ Trendline Break | ≥3 touches, <45°, ≥6-candle spacing, 4H close past line | Yes — from trendline engine |
| Standard Trendline Break | 2 touches, break criteria met | Yes |
| Trendline Bounce | Price tests existing trendline with ≥2 confirmed touches | Yes |
| Custom / Manual | User-defined criteria | Manual tagging |

Each playbook tracks independent metrics: win rate, average R-multiple, profit factor, expectancy, Sharpe ratio, average hold time, and equity curve. The system answers "should I stop trading 2-touch breaks?" with data.

---

### F5: Performance Analytics

#### Core Metrics Dashboard

| Category | Metrics |
|---|---|
| Trade Performance | Win rate, avg winner/loser, profit factor, expectancy, largest win/loss |
| Risk-Adjusted | Sharpe ratio, Sortino ratio, Calmar ratio, max drawdown ($ and %), recovery time |
| R-Multiple Analysis | Average R, R-multiple distribution histogram, cumulative R curve |
| Time Analysis | P&L by hour, day of week, month. Session analysis (RTH vs. overnight) |
| Execution Quality | Avg slippage, MAE/MFE analysis, fill quality scoring |
| Behavioral | Rule compliance rate, cost of mistakes ($), Tiltmeter score |
| Trendline-Specific | Win rate by touch count, edge by slope angle, performance by trendline duration |

#### Advanced Analytics (Pro Tier)

- Monte Carlo simulation: projected equity curves with confidence intervals
- Strategy correlation matrix: identify which playbooks diversify vs. correlate
- Walk-forward analysis: rolling performance windows to detect strategy decay
- Drawdown analysis: time-to-recovery, clustering, underwater equity curve
- AI-powered insights: natural language queries ("Best setup on Tuesdays in crude oil?")
- P&L calendar heatmap with drill-down to individual trades
- Equity curve comparison: paper vs. live, strategy A vs. B, month-over-month

---

### F6: AI-Powered Features

- **Trendline Quality Scoring.** ML model predicting probability of successful trade given trendline characteristics. Features: touch count, slope, spacing regularity, volume at touches, ATR context.

- **False Breakout Filter.** Gradient boosting classifier (XGBoost/LightGBM) on confirmed vs. false breakouts. Features: break candle volume, momentum, time of day, VIX regime, distance from key S/R.

- **Conversational Analytics.** Claude API for querying trade data: "Show all losing trades in platinum where I moved my stop" or "Compare bounce vs. break setups over 6 months."

- **Trade Review Assistant.** After each trade closes, AI generates a review comparing the trade to similar historical setups, highlighting strengths and areas for improvement.

---

## 6. Technical Architecture

### Recommended Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 14+ (App Router) + TypeScript + Tailwind + shadcn/ui | SSR for dashboard performance, API routes, excellent DX with Claude Code |
| Charting | TradingView Lightweight Charts + D3.js | Professional financial charts with trendline overlay. Same engine traders know |
| Backend API | FastAPI (Python 3.12+) | Native async/await for broker calls, 15–20K rps, auto OpenAPI docs, WebSocket support |
| Trendline Engine | Python: scipy.signal + pytrendline + NumPy + pandas | find_peaks() for swing detection, RANSAC fitting, vectorized scoring |
| Broker Adapters | ib_async (IBKR), httpx (Tradovate), webull SDK | Common BrokerInterface ABC: place_order(), cancel_order(), get_positions() |
| Task Queue | Celery + Redis (or Dramatiq) | Async: trendline scans, alert evaluation, trade logging, notifications, AI analysis |
| Database | PostgreSQL 16 (Supabase or Railway) | JSONB for trade metadata, RLS for multi-tenant, time-series for tick data |
| Cache / Pub-Sub | Redis (Upstash serverless) | Signal dedup, rate limiting, WebSocket pub/sub, session management |
| Auth | Clerk or Supabase Auth | OAuth 2.0 + magic links, team/org support for prop firms |
| File Storage | S3-compatible (Cloudflare R2) | Chart screenshots, trade replay data, CSV exports |
| Hosting | Railway (backend + workers) + Vercel (frontend) | Managed PostgreSQL + Redis + persistent processes for IB Gateway |
| Monitoring | Sentry + Axiom + Uptime Robot | Trade execution alerting via PagerDuty/Telegram on failures |
| CI/CD | GitHub Actions | Automated testing, linting, deployment on push |

### Data Flow Architecture

1. **Detection Flow:** Market data (broker API) → Trendline Engine (Celery worker) → Qualified trendlines in PostgreSQL → Alert evaluation on each new 4H candle → Signal to execution pipeline + WebSocket push to dashboard.

2. **Execution Flow:** Signal (internal/webhook/manual) → FastAPI endpoint → Validation + risk check → Broker adapter → Order placed → Fill confirmation → Journal entry created → Analytics updated → Notification sent.

3. **Analytics Flow:** Trade closed → MAE/MFE calculated from tick data → R-multiple computed → Playbook stats updated → Dashboard refreshed via WebSocket → AI review queued.

### Key Data Models

| Entity | Key Fields | Relationships |
|---|---|---|
| User | id, email, broker_connections[], settings, subscription_tier | Has many Trades, Playbooks, Trendlines |
| Trendline | id, instrument, direction, slope, touch_count, touch_points[], grade, status | Has many Alerts; referenced by Trades |
| Signal | id, source, trendline_id, instrument, direction, entry/stop/target prices, risk_amount | Belongs to Trendline; has one Trade |
| Trade | id, signal_id, playbook_id, broker_order_ids[], fills, pnl, r_multiple, mae, mfe | Belongs to Signal, Playbook; has JournalEntry |
| Playbook | id, name, criteria_description, auto_classify_rules{} | Has many Trades |
| JournalEntry | id, trade_id, conviction, emotional_state[], notes, screenshots[], mistakes[] | Belongs to Trade |

---

## 7. Integrations

### TradingView Integration

- **Webhook Receiver.** Unique webhook URL per user. TradingView alerts POST JSON with ticker, action, price, custom fields. Receiver validates (API key), maps symbols, routes to execution. Latency: 2–60s (acceptable for 1H+ strategies).

- **Pine Script Companion Indicator.** Published indicator implementing trendline detection client-side for visual verification. Free — serves as marketing/acquisition tool.

### Notification Channels

| Channel | Use Case | Priority |
|---|---|---|
| Telegram Bot | Real-time trade alerts, fill confirmations, daily P&L | P0 (MVP) |
| Discord Webhook | Community trade signals, leaderboard updates | P1 |
| Email (SendGrid) | Daily/weekly performance digests | P1 |
| Push Notifications | Mobile app alerts (native app) | P2 |

### Data Sources

- **Real-time:** IBKR provides Level 1+2 CME data (~$10–25/mo) through execution API. Tradovate includes real-time data with funded accounts.

- **Historical:** yfinance for free daily OHLCV (ES=F tickers). Nasdaq Data Link for continuous contract data. Databento $125 free credit for tick-level research.

- **Sentiment (Pro):** Batch-process headlines via Claude API or free FinBERT for daily sentiment scores as supplementary trendline quality features.

---

## 8. Pricing & Monetization

### Tier Structure

| | Free | Trader ($49/mo) | Pro ($99/mo) | Team ($199/mo) |
|---|---|---|---|---|
| Trendline Detection | 3 instruments, delayed | 10 instruments, real-time | Unlimited, real-time | Unlimited + custom |
| Trade Execution | Paper only | 1 broker, 1 account | 3 brokers, 5 accounts | Unlimited accounts |
| Journaling | 10 trades/month | Unlimited | Unlimited + AI review | Unlimited + sharing |
| Playbooks | 1 default | 5 custom | Unlimited | Unlimited + templates |
| Analytics | 5 basic metrics | 25+ full dashboard | Advanced + Monte Carlo | Everything + team |
| Notifications | Email only | Telegram + Email | All channels | All + custom hooks |
| Support | Community | Email (48h) | Priority (24h) | Dedicated (4h) |
| Annual Price | — | $399/yr (32% off) | $799/yr (33% off) | $1,899/yr (21% off) |

### Unit Economics

| Metric | Target |
|---|---|
| Average Revenue Per User | $79/month |
| Customer Acquisition Cost | <$50 (content + community) |
| Monthly Churn | <5% (industry avg: 5–10%) |
| Average Customer Lifetime | 14–18 months |
| Lifetime Value | $1,100–1,400 |
| LTV:CAC Ratio | >20:1 |

---

## 9. MVP Scope & Development Phases

> **Development Approach:** All development uses Claude Code as the primary development tool with the best tech stack for each layer. Timelines assume AI-assisted development at 3–5x acceleration. No artificial constraints on language or framework choices.

### Phase 1: Personal Trading System (Weeks 1–8)

**Goal:** Working system that detects trendlines on platinum and crude oil, fires alerts, executes paper trades via IBKR/Tradovate, journals every trade, and displays basic analytics.

| Week | Deliverables | Stack |
|---|---|---|
| 1–2 | FastAPI scaffold, PostgreSQL schema, webhook receiver, Telegram bot, basic auth | FastAPI, PostgreSQL, Redis, python-telegram-bot |
| 3–4 | Trendline detection engine: swing detection, line fitting, A+ scoring, alert generation | scipy, pytrendline, NumPy, pandas, Celery |
| 5–6 | IBKR + Tradovate broker adapters, paper trading mode, bracket order construction | ib_async, httpx, asyncio |
| 7–8 | Next.js dashboard: trade log, active trendlines, P&L summary, equity curve, chart overlays | Next.js, TypeScript, Tailwind, shadcn/ui, Lightweight Charts |

### Phase 2: Analytics & Journaling (Weeks 9–14)

| Week | Deliverables | Stack |
|---|---|---|
| 9–10 | Playbook system, auto-classification, journal enrichment UI, screenshot uploads | React forms, S3, PostgreSQL JSONB |
| 11–12 | Full analytics: 25+ metrics, P&L calendar, heatmaps, R-multiple distributions, MAE/MFE | Recharts/D3.js, SQL aggregations |
| 13–14 | AI features: conversational analytics (Claude API), false breakout classifier, trade reviews | Claude API, scikit-learn, XGBoost |

### Phase 3: Multi-Tenant SaaS Launch (Weeks 15–22)

| Week | Deliverables | Stack |
|---|---|---|
| 15–16 | Multi-tenant: user isolation (RLS), subscription tiers, Stripe billing | Clerk Auth, Stripe, PostgreSQL RLS |
| 17–18 | Onboarding flow, broker connection wizard, docs site, landing page | Next.js, MDX |
| 19–20 | Webull adapter, prop firm multi-account support, consistency metrics | Webull SDK |
| 21–22 | Beta launch to 50–100 users, monitoring, performance optimization, iterate on feedback | Sentry, Axiom, load testing |

### Phase 4: Growth & Advanced Features (Months 6–12)

- Mobile app (React Native / Expo) with push notifications
- Pine Script companion indicator (free, for acquisition)
- Monte Carlo simulation engine
- Strategy marketplace: users publish and sell playbooks/indicators
- Advanced ML: regime detection (HMM), sentiment-augmented trendline scoring
- Automated contract rollover handling (genuine differentiator)
- Trade replay with tick-by-tick playback and annotation
- Community features: anonymized leaderboard, strategy sharing

---

## 10. Success Metrics

### Phase 1 Criteria (Personal System)

- Trendline engine identifies ≥80% of setups a skilled manual trader would find (validated by review)
- End-to-end webhook-to-paper-trade latency <10 seconds (p95)
- Zero missed signals over 30 consecutive trading days
- Paper trading results within 20% of backtest expectations over 60+ days
- System runs unattended 2+ weeks without manual intervention

### Phase 3 Criteria (SaaS Launch)

| KPI | 3-Month | 6-Month | 12-Month |
|---|---|---|---|
| Registered Users | 200 | 1,000 | 5,000 |
| Paying Subscribers | 25 | 150 | 750 |
| MRR | $1,500 | $10,000 | $55,000 |
| Monthly Churn | <8% | <6% | <5% |
| NPS | >30 | >40 | >50 |

---

## 11. Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Trendline detection doesn't match human judgment | High | Configurable parameters. Visual overlay for manual confirmation. Start alert-only (no auto-execution). |
| Broker API downtime during execution | Critical | Multi-broker failover. Retry logic. Circuit breaker: halt after 3+ consecutive failures. Manual override via Telegram. |
| TradingView webhook latency spikes (up to 60s) | Medium | Target 1H+ strategies only. Server-side engine provides independent signals not dependent on TradingView. |
| Regulatory: CFTC/NFA registration required? | High | No registration for individuals trading own accounts. SaaS providing tools (not managing money) is exempt. Consult fintech attorney pre-launch. |
| Strategy edge decays | High | Platform value is tooling (journaling + analytics), not strategy. Users bring own strategies. Detection is one feature, not sole value. |
| Low free-to-paid conversion | Medium | Gate execution behind paid tier. Content marketing via Pine Script indicator. Generous free tier builds habit. |
| Competitive response | Medium | 6–12 month head start. Neither TradeZella nor TradersPost has incentive to build the other's core product. |

---

## 12. Appendix

### A. Tori Trades Strategy Reference

| Parameter | A+ Setup | Standard Setup | Implementation |
|---|---|---|---|
| Touchpoints | ≥3 (wick-to-line) | 2 | Touch = wick within 0.5×ATR of line |
| Candle Spacing | ≥6 between each touch | ≥3 | Count 4H candles between pivots |
| Slope | <45° at 3-month zoom | <60° | atan(price_change / time) normalized |
| Duration | ≥3 weeks from 1st touch | ≥1 week | Calendar days from 1st touchpoint |
| Entry Trigger | 4H candle close past line | Same | Close (not wick) exceeds line level |
| Stop Loss | Safety Line @ 4th candle | Same | Opposing trendline projected 4 candles |
| Take Profit | First S/R at ≥2R | Same | Scan for nearest S/R at 2:1 R:R min |
| Max Attempts | 1 per trendline | 1 | Flag trendline as "traded" after entry |

### B. Monthly Operating Costs

| Item | MVP (0–100 users) | Growth (100–1K) | Scale (1K+) |
|---|---|---|---|
| Hosting (Railway/Render) | $25/mo | $100/mo | $300–500/mo |
| Database (PostgreSQL) | $0–20/mo | $25–50/mo | $100–200/mo |
| Redis | $0–10/mo | $20–40/mo | $50–100/mo |
| Frontend (Vercel) | $0–20/mo | $20/mo | $20–150/mo |
| CME Data (via broker) | $10–25/mo | $10–25/mo | $10–25/mo |
| Claude API | $5–20/mo | $50–100/mo | $200–500/mo |
| Monitoring | $0 | $26/mo | $80/mo |
| Stripe Fees | ~$50/mo | ~$500/mo | ~$2,500/mo |
| **Total** | **$50–120/mo** | **$250–500/mo** | **$1K–2.5K/mo** |

### C. Key Resources

- Tori Trades Playbook: [tradezella.com/playbooks/trendline-strategy](https://tradezella.com/playbooks/trendline-strategy)
- FX Replay Strategy Breakdown: [fxreplay.com/strategies/tori-trades-trendlines-strategy](https://fxreplay.com/strategies/tori-trades-trendlines-strategy)
- pytrendline Library: [github.com/ednunezg/pytrendline](https://github.com/ednunezg/pytrendline)
- trendln Library: [github.com/GregoryMorse/trendln](https://github.com/GregoryMorse/trendln)
- ib_async (IBKR Python): [pypi.org/project/ib_async/](https://pypi.org/project/ib_async/)
- pysystemtrade: [github.com/robcarver17/pysystemtrade](https://github.com/robcarver17/pysystemtrade)
- TradingView Webhook Docs: [tradingview.com/support/solutions/43000529348](https://tradingview.com/support/solutions/43000529348)
- TradersPost Futures Docs: [docs.traderspost.io/docs/assets/futures-trading](https://docs.traderspost.io/docs/assets/futures-trading)
- Ernest Chan, "Quantitative Trading" (Wiley)
- Rob Carver, "Systematic Trading" (Harriman House)

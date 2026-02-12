# PRD-011: Frontend Dashboard & UI/UX

**Product:** TrendEdge — AI-Powered Futures Trading Platform
**Component:** Frontend Dashboard, Design System & User Interface
**Version:** 1.0
**Date:** February 2026
**Status:** Draft
**Dependencies:** PRD-001 through PRD-010 (this is the presentation layer for all platform features)

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [UI/UX Design System](#5-uiux-design-system)
6. [Dependencies](#6-dependencies)
7. [Testing Requirements](#7-testing-requirements)
8. [Security](#8-security)
9. [Phase Mapping](#9-phase-mapping)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Overview & Purpose

### 1.1 Purpose

This PRD defines all frontend requirements for the TrendEdge trading platform. The frontend is the sole user-facing layer: every backend service (trendline detection, trade execution, journaling, analytics, AI insights) is surfaced through this dashboard. The frontend must deliver a professional, performant, futures-first trading experience that consolidates functionality traders currently spread across 3-4 separate tools.

### 1.2 Scope

The frontend application encompasses:

- **Application shell**: Navigation, layout, authentication flow, global state
- **Dashboard home**: Real-time overview of trading activity, positions, and alerts
- **Trendline detection**: Interactive charting with algorithmic trendline overlays
- **Trade execution**: Position management, signal queue, order entry, broker connection
- **Trade journal**: Searchable trade log with manual enrichment and screenshot uploads
- **Playbook management**: Strategy CRUD, comparison, and per-playbook analytics
- **Analytics dashboard**: 25+ metrics with professional financial visualizations
- **Settings**: Profile, preferences, broker connections, notifications, risk rules
- **Onboarding**: Multi-step wizard for new user setup (Phase 3)
- **Landing page**: Marketing site and conversion funnel (Phase 3)
- **AI chat interface**: Conversational analytics powered by Claude API
- **Design system**: Component library, tokens, conventions

### 1.3 Tech Stack

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Framework | Next.js (App Router) | 14+ | SSR for dashboard performance, RSC for reduced client JS, API routes for BFF pattern |
| Language | TypeScript | 5.3+ | Type safety across component props, API responses, and state |
| Styling | Tailwind CSS | 3.4+ | Utility-first, design token integration, dark mode built-in |
| Component Library | shadcn/ui | Latest | Accessible, composable primitives; copy-paste ownership model |
| Charting (Financial) | TradingView Lightweight Charts | 4.x | Industry-standard candlestick rendering, trendline overlay API |
| Charting (Analytics) | D3.js | 7.x | Custom visualizations: heatmaps, scatter plots, histograms |
| State Management | Zustand | 4.x | Lightweight, TypeScript-native, devtools support |
| Data Fetching | TanStack Query (React Query) | 5.x | Cache, retry, optimistic updates, WebSocket integration |
| Forms | React Hook Form + Zod | Latest | Performant forms with schema validation |
| Real-time | WebSocket (native) + Supabase Realtime | N/A | Live dashboard updates, position changes, alert notifications |
| File Upload | react-dropzone | Latest | Drag-and-drop screenshot uploads |
| Date Handling | date-fns | Latest | Lightweight date formatting, timezone support |
| Icons | Lucide React | Latest | Consistent with shadcn/ui |
| Hosting | Vercel | N/A | Edge network, preview deployments, analytics |

### 1.4 Architecture Principles

1. **Server Components by default.** Use React Server Components for data fetching and static UI. Client Components only where interactivity is required (charts, forms, real-time widgets).

2. **BFF pattern via API routes.** Next.js API routes proxy requests to the FastAPI backend, handling auth token injection and response shaping. The frontend never calls the FastAPI backend directly from the browser.

3. **Optimistic updates.** Trade actions (journal edits, playbook changes, settings updates) update the UI immediately and reconcile with the server response.

4. **Progressive loading.** Dashboard sections load independently via Suspense boundaries. Critical data (positions, P&L) loads first; secondary data (analytics charts) streams in.

5. **Futures-first vocabulary.** All UI copy, labels, and tooltips use futures trading terminology: "contracts" not "shares", "margin" not "buying power", "session" not "market hours".

---

## 2. User Stories

### 2.1 Dashboard & Navigation

| ID | Story | Priority |
|---|---|---|
| US-FE-001 | As a trader, I want to see my current P&L, open positions, and active alerts immediately upon login so I can assess my trading status at a glance. | P0 |
| US-FE-002 | As a trader, I want a collapsible sidebar navigation so I can maximize chart viewing area on smaller screens. | P0 |
| US-FE-003 | As a trader, I want a command palette (Cmd+K) so I can navigate to any page, instrument, or trade instantly without clicking through menus. | P1 |
| US-FE-004 | As a trader, I want breadcrumbs on nested views (e.g., Playbook > "A+ Break" > Trade #47) so I can orient myself and navigate back efficiently. | P1 |
| US-FE-005 | As a trader, I want to see a clear visual indicator of whether I am in Paper or Live mode at all times so I never accidentally confuse simulated and real trading. | P0 |

### 2.2 Trendline Detection

| ID | Story | Priority |
|---|---|---|
| US-FE-006 | As a trader, I want to see auto-detected trendlines overlaid on a professional candlestick chart so I can visually verify A+ setups without drawing lines manually. | P0 |
| US-FE-007 | As a trader, I want to click on any trendline to see its detail panel (touch points, slope, grade, alert status) so I can evaluate the quality of the setup. | P0 |
| US-FE-008 | As a trader, I want to switch instruments quickly and see trendlines re-render for the new symbol so I can scan across my watchlist. | P0 |
| US-FE-009 | As a trader, I want to adjust detection parameters (min touches, slope threshold, spacing) via a configuration panel so I can tune the engine to my criteria. | P1 |
| US-FE-010 | As a trader, I want to see trendlines ranked by quality score so I can focus on the highest-probability setups first. | P1 |

### 2.3 Trade Execution

| ID | Story | Priority |
|---|---|---|
| US-FE-011 | As a trader, I want to see all my active positions in a table with real-time P&L updates so I can monitor open risk. | P0 |
| US-FE-012 | As a trader, I want to toggle between Paper and Live mode with a confirmation dialog so I have a deliberate gate before live trading. | P0 |
| US-FE-013 | As a trader, I want to see pending trendline signals in a queue and approve/reject them before execution so I maintain discretionary control. | P1 |
| US-FE-014 | As a trader, I want a manual trade entry form so I can log trades taken outside of automated execution. | P1 |
| US-FE-015 | As a trader, I want to see broker connection status (connected, disconnected, error) at all times so I know if order routing is available. | P0 |

### 2.4 Trade Journal

| ID | Story | Priority |
|---|---|---|
| US-FE-016 | As a trader, I want a trade table with sortable columns (date, instrument, P&L, R-multiple, playbook) and pagination so I can browse my history efficiently. | P0 |
| US-FE-017 | As a trader, I want to click any trade row to open a detail view showing all auto-captured data plus my journal notes so I can review the complete trade context. | P0 |
| US-FE-018 | As a trader, I want to enrich trades with conviction level, emotional state tags, notes, and screenshots so I can build a comprehensive trading journal. | P0 |
| US-FE-019 | As a trader, I want to drag-and-drop chart screenshots onto a trade entry and have them upload and display inline so journaling is frictionless. | P1 |
| US-FE-020 | As a trader, I want to search trades by full-text query (e.g., "moved stop on crude oil") and filter by date range, instrument, playbook, and outcome so I can find specific trades quickly. | P1 |

### 2.5 Playbook Management

| ID | Story | Priority |
|---|---|---|
| US-FE-021 | As a trader, I want to see all my playbooks in a list with summary metrics (win rate, expectancy, trade count) so I can identify which strategies are working. | P0 |
| US-FE-022 | As a trader, I want to view a playbook detail page showing its dedicated equity curve, metrics, and trade list so I can analyze a single strategy in isolation. | P0 |
| US-FE-023 | As a trader, I want to create, edit, and delete playbooks with names, descriptions, and auto-classification rules so I can organize my strategies. | P1 |
| US-FE-024 | As a trader, I want to compare two playbooks side-by-side (metrics, equity curves) so I can objectively decide which to continue trading. | P2 |

### 2.6 Analytics

| ID | Story | Priority |
|---|---|---|
| US-FE-025 | As a trader, I want a dashboard of 25+ performance metrics presented as cards and charts so I can understand my trading edge quantitatively. | P0 |
| US-FE-026 | As a trader, I want a P&L calendar heatmap so I can visualize profitable and losing days at a glance and identify patterns. | P0 |
| US-FE-027 | As a trader, I want to filter all analytics by date range, instrument, and playbook so I can isolate specific segments of my performance. | P0 |
| US-FE-028 | As a trader, I want an R-multiple distribution histogram so I can see how my trade outcomes cluster relative to planned risk. | P1 |
| US-FE-029 | As a trader, I want MAE/MFE scatter plots so I can analyze whether I am leaving money on the table or placing stops too tight. | P1 |
| US-FE-030 | As a trader, I want an equity curve chart with drawdown overlay so I can track account growth and drawdown recovery. | P0 |

### 2.7 Settings & Configuration

| ID | Story | Priority |
|---|---|---|
| US-FE-031 | As a trader, I want to manage broker connections (add, remove, test connection) through a settings page so I can configure order routing. | P0 |
| US-FE-032 | As a trader, I want to set notification preferences (Telegram, Discord, email) for different alert types so I get notified on my preferred channels. | P1 |
| US-FE-033 | As a trader, I want to configure default risk management rules (max position size, daily loss limit, max concurrent positions) so the system enforces my discipline. | P1 |
| US-FE-034 | As a trader, I want to toggle between dark mode (default) and light mode so I can use the interface in different lighting conditions. | P1 |

### 2.8 AI & Conversational Analytics

| ID | Story | Priority |
|---|---|---|
| US-FE-035 | As a trader, I want to ask natural language questions about my trading data (e.g., "What is my win rate on Tuesdays in crude oil?") and receive answers with supporting charts so I can discover insights without building queries manually. | P2 |
| US-FE-036 | As a trader, I want to receive AI-generated post-trade reviews comparing my trade to similar historical setups so I can learn from patterns. | P2 |

### 2.9 Onboarding (Phase 3)

| ID | Story | Priority |
|---|---|---|
| US-FE-037 | As a new user, I want a guided setup wizard that walks me through broker connection, first playbook creation, and paper trading activation so I can start using the platform without reading documentation. | P2 |
| US-FE-038 | As a new user, I want contextual tooltips and empty-state guidance on each page so I understand what data will appear once I start trading. | P2 |

---

## 3. Functional Requirements

### 3.1 Application Shell & Navigation

#### FE-FR-001: Sidebar Navigation (Collapsible)

The application shell uses a persistent left sidebar navigation with the following behavior:

- **Collapsed state**: Shows icon-only navigation; sidebar width = 64px.
- **Expanded state**: Shows icon + label; sidebar width = 240px.
- **Toggle**: Clickable chevron button at the bottom of the sidebar. State persists in `localStorage`.
- **Mobile (<768px)**: Sidebar is an overlay drawer, triggered by hamburger icon in the header. Closes on navigation or backdrop click.

**Navigation items (in order):**

| Icon | Label | Route | Badge |
|---|---|---|---|
| LayoutDashboard | Dashboard | `/dashboard` | -- |
| TrendingUp | Trendlines | `/trendlines` | Active trendline count |
| ArrowRightLeft | Execution | `/execution` | Pending signal count |
| BookOpen | Journal | `/journal` | -- |
| Target | Playbooks | `/playbooks` | -- |
| BarChart3 | Analytics | `/analytics` | -- |
| MessageSquare | AI Chat | `/chat` | -- |
| Settings | Settings | `/settings` | -- |

- **Bottom section**: User avatar + name (truncated), plan badge (Free/Trader/Pro), and logout button.
- **Active state**: Left border accent (4px, primary color) + background highlight on the active route.
- **Hover state**: Subtle background change (opacity 0.08 of foreground color).

#### FE-FR-002: Header Bar

A fixed top header bar spanning the width above the main content area:

- **Left**: Breadcrumb trail (see FE-FR-003).
- **Center**: Paper/Live mode indicator (see FE-FR-004).
- **Right (in order)**:
  - Command palette trigger button (magnifying glass icon + "Cmd+K" shortcut hint).
  - Notification bell icon with unread count badge (red dot if >0). Clicking opens a dropdown panel showing the 10 most recent notifications with "View all" link to `/settings/notifications`.
  - User avatar dropdown: Profile link, Settings link, Theme toggle, Logout.

Header height: 56px. Background: `bg-background` with bottom border `border-border`.

#### FE-FR-003: Breadcrumb Navigation

Breadcrumbs appear in the header for all routes deeper than top-level:

- **Format**: `Home / [Section] / [Subsection] / [Item]`
- **Behavior**: Each segment except the last is a clickable link. The last segment is plain text (current page).
- **Dynamic segments**: Trade IDs display as `Trade #[id]`, Playbook names display their user-given name, truncated at 24 characters with ellipsis.
- **Examples**:
  - `/journal/trade/47` renders as: `Journal / Trade #47`
  - `/playbooks/a-plus-break/analytics` renders as: `Playbooks / A+ Trendline Break / Analytics`
  - `/settings/brokers` renders as: `Settings / Broker Connections`

#### FE-FR-004: Paper/Live Mode Indicator

A persistent, always-visible mode indicator positioned in the center of the header:

- **Paper mode**: Blue badge with `TestTube` icon, text "PAPER TRADING". Background: `bg-blue-500/10`, text: `text-blue-500`, border: `border-blue-500/20`.
- **Live mode**: Green badge with `Zap` icon, text "LIVE TRADING". Background: `bg-green-500/10`, text: `text-green-500`, border: `border-green-500/20`.
- **Additional**: In paper mode, a subtle blue top-border (2px) spans the full width of the application as an ambient visual cue.
- **Click behavior**: Clicking the badge opens the Paper/Live toggle dialog (see FE-FR-058).

#### FE-FR-005: Command Palette (Cmd+K)

A modal command palette triggered by `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux):

- **Search input**: Auto-focused, placeholder "Search pages, instruments, trades..."
- **Result categories** (displayed as grouped sections):
  - **Pages**: All navigation items (Dashboard, Trendlines, Execution, etc.)
  - **Instruments**: Searchable list of tracked instruments (ES, NQ, CL, GC, PL, YM, etc.)
  - **Recent trades**: Last 10 trades by date, showing instrument + P&L
  - **Playbooks**: All user playbooks by name
  - **Actions**: "New Trade Entry", "New Playbook", "Toggle Theme", "Open Settings"
- **Navigation**: Arrow keys to move, Enter to select, Escape to close.
- **Fuzzy matching**: Results filter as user types. Match highlights displayed in bold.
- **Performance**: Results render within 100ms of keystroke. Debounce search API calls to 200ms.

#### FE-FR-006: Global Loading States

Every page and widget follows a consistent loading pattern:

- **Page-level**: Full-page skeleton with layout-matching placeholder shapes. No spinner. Duration: visible for minimum 200ms to avoid flash.
- **Widget-level**: Individual skeleton placeholders matching the widget's content shape (card skeletons, table row skeletons, chart area skeletons).
- **Data refetch**: Subtle loading indicator (thin progress bar at top of content area) during background data refreshes. Content remains visible and interactive.
- **Error state**: Error boundary with "Something went wrong" message, error detail in collapsible section, and "Retry" button. Logged to Sentry automatically.
- **Empty state**: Purpose-specific illustration or icon, descriptive heading, and action CTA. Examples:
  - Trade journal empty: "No trades yet. Connect a broker or add your first trade manually." + "Add Trade" button.
  - Analytics empty: "Start trading to see your analytics. Paper trading results count!" + "Go to Execution" button.

#### FE-FR-007: Toast Notifications

Global toast notification system for transient feedback:

- **Position**: Bottom-right corner, stacked vertically with 8px gap.
- **Types**: `success` (green accent), `error` (red accent), `warning` (yellow accent), `info` (blue accent).
- **Behavior**: Auto-dismiss after 5 seconds (errors: 8 seconds). Hovering pauses the dismiss timer. Swipe-right or click X to dismiss manually.
- **Content**: Icon + title (bold) + optional description (regular weight). Max 2 lines.
- **Queue**: Maximum 3 visible toasts. Additional toasts queue and display as earlier ones dismiss.

---

### 3.2 Dashboard / Home Page

Route: `/dashboard`

#### FE-FR-008: Today's P&L Summary Card

A prominent card at the top of the dashboard:

- **Layout**: Full-width card with centered content.
- **Content**:
  - "Today's P&L" label.
  - Dollar amount in large typography (32px). Green if positive, red if negative, muted foreground if zero.
  - Percentage change relative to starting equity, displayed below in smaller text.
  - Comparison to previous day: arrow icon (up/down) with "vs. yesterday" label.
- **Data source**: Real-time via WebSocket. Updates on every trade fill and position mark-to-market.
- **Paper mode**: Amount prefixed with "(Paper)" in the label.

#### FE-FR-009: Active Positions Widget

A card displaying all currently open positions:

- **Table columns**: Instrument | Direction (Long/Short with color) | Contracts | Entry Price | Current Price | Unrealized P&L | % of Account
- **Real-time**: Current price and unrealized P&L update via WebSocket every 1 second during market hours.
- **Row actions**: Click row to navigate to the position in the Execution page.
- **Empty state**: "No open positions" with muted text.
- **Visual**: Direction uses green chip for Long, red chip for Short. P&L column uses green/red text.
- **Maximum rows**: Show all positions (expected max ~5-10 concurrent). No pagination needed.

#### FE-FR-010: Active Trendline Alerts Widget

A card showing trendlines currently being monitored for alerts:

- **List items**: Each trendline shows: Instrument | Direction (Support/Resistance) | Grade (A+/A/B badge) | Touch Count | Alert Status (Watching/Near Alert/Triggered)
- **Sorting**: Default sort by grade descending (A+ first), then by proximity to alert trigger.
- **Alert status colors**: Watching = muted, Near Alert = yellow pulse animation, Triggered = green flash.
- **Click behavior**: Clicking a trendline navigates to `/trendlines?instrument=[symbol]&trendline=[id]` and highlights it on the chart.
- **Maximum items**: Show top 10. "View all [n] trendlines" link at bottom if more exist.
- **Empty state**: "No active trendlines. Visit the Trendlines page to scan for setups." + "Scan Trendlines" button.

#### FE-FR-011: Recent Trades Widget

A compact list of the 5 most recent closed trades:

- **Each row**: Date (relative, e.g., "2h ago") | Instrument | Direction | P&L (dollar, colored) | R-Multiple
- **Click behavior**: Navigate to trade detail view in journal.
- **Footer**: "View all trades" link to `/journal`.
- **Empty state**: "No trades recorded yet."

#### FE-FR-012: Quick Stats Bar

A horizontal row of 4-5 stat cards below the P&L summary:

| Stat | Format | Source |
|---|---|---|
| Win Rate | Percentage with fraction (e.g., "68.2% (15/22)") | Calculated from closed trades in selected period |
| Account Equity | Dollar amount | Latest broker account balance |
| Open Risk | Dollar amount + percentage of equity | Sum of stop distances on open positions |
| Total Trades (period) | Count | Closed trades in selected period |
| Avg R-Multiple | Number with 2 decimals | Mean R-multiple of closed trades |

- **Period selector**: Dropdown at the top of the stats bar: Today, This Week, This Month, All Time. Default: This Month. Persisted in `localStorage`.
- **Each card**: Label (muted, small), value (bold, medium), and a sparkline (tiny inline chart showing 30-day trend) below the value.

---

### 3.3 Trendline Detection Page

Route: `/trendlines`

#### FE-FR-013: Interactive Candlestick Chart

The primary chart area occupying approximately 65% of the page width (left side):

- **Engine**: TradingView Lightweight Charts library.
- **Chart type**: Candlestick (OHLC). Green (close > open) and red (close < open) candles.
- **Default timeframe**: 4H (the primary analysis timeframe per the Tori Trades methodology).
- **Timeframe selector**: Horizontal button group: 1H | 4H | D | W. 4H is highlighted by default.
- **Interactions**: Scroll to zoom, click-drag to pan, double-click to reset zoom. Pinch-to-zoom on touch devices.
- **Crosshair**: Vertical + horizontal dashed lines following cursor, with price label on Y-axis and date label on X-axis.
- **Price axis**: Right side. Auto-scaling with 10% headroom above/below visible range.
- **Time axis**: Bottom. Formatted: "Jan 15" for daily, "Jan 15 09:00" for intraday.
- **Data**: Fetched from backend API (`/api/market-data/{instrument}/{timeframe}`). Paginated: initial load = 300 candles, load more on scroll-left.

#### FE-FR-014: Trendline Overlays

Detected trendlines rendered as line series on the chart:

- **Line rendering**: Each trendline drawn as a straight line between its first and last touch points, extended to the right edge of the visible chart area.
- **Color coding by grade**:
  - A+ grade: Gold/amber (`#F59E0B`) with 2px solid line.
  - A grade: Blue (`#3B82F6`) with 1.5px solid line.
  - B grade: Gray (`#6B7280`) with 1px dashed line.
- **Touch point markers**: Small circles (6px diameter) at each confirmed touch point on the trendline. Color matches the trendline. Tooltip on hover showing touch date and price.
- **Interactive**: Clicking a trendline highlights it (increases line width to 3px, adds glow effect) and populates the detail panel (FE-FR-016).
- **Alert zone**: When price is within 1x ATR of a trendline, the area between the trendline and price is shaded with a semi-transparent fill (10% opacity of line color).
- **Toggling**: Each trendline can be toggled visible/hidden via its checkbox in the trendline list panel.

#### FE-FR-015: Trendline List Panel

A scrollable list panel on the right side (approximately 35% width):

- **Tab bar**: "Active" | "Triggered" | "Expired" tabs.
- **Each list item displays**:
  - Direction icon: TrendingUp (support) or TrendingDown (resistance).
  - Grade badge: A+ (gold), A (blue), B (gray).
  - Touch count: "3 touches", "4 touches", etc.
  - Slope angle: Displayed as degrees (e.g., "28 deg").
  - Duration: Time since first touch (e.g., "5 weeks").
  - Alert status: Watching | Near (within 1 ATR) | Triggered.
  - Quality score: Numeric score (0-100) with small bar indicator.
- **Sorting**: Dropdown to sort by: Score (default), Touch Count, Duration, Proximity to Price.
- **Selection**: Clicking an item highlights the corresponding trendline on the chart and opens the detail panel.
- **Bulk actions**: "Dismiss" button (removes from active list, marks as dismissed in backend).

#### FE-FR-016: Trendline Detail Panel

A slide-over panel or expanded section when a trendline is selected:

- **Header**: Instrument + Direction + Grade badge.
- **Metrics grid** (2 columns):
  - Touch Points: Count + list of dates/prices.
  - Slope: Angle in degrees + visual gauge.
  - Spacing: Average candle count between touches.
  - Duration: Total timespan from first to last touch.
  - Quality Score: 0-100 with color gradient bar.
  - Current Distance: ATR-normalized distance from current price to the trendline.
- **Alert configuration**:
  - Enable/disable alert toggle.
  - Alert type dropdown: Break, Touch, Both.
  - Notification channels: Checkboxes for Telegram, Discord, Email, Dashboard.
- **Actions**:
  - "Set Alert" button (primary).
  - "Dismiss" button (secondary, with confirmation).
  - "View Trades" link (if trades were taken from this trendline).
- **History**: List of past alert triggers for this trendline, if any.

#### FE-FR-017: Instrument Selector

Instrument switching control positioned above the chart:

- **Format**: Dropdown with search, showing instrument name + current price + daily change.
- **Grouped sections**: "Favorites" (user-pinned, stored in settings) at top, then "All Instruments" alphabetically.
- **Supported instruments (MVP)**: ES (E-mini S&P), NQ (E-mini Nasdaq), CL (Crude Oil), GC (Gold), PL (Platinum), YM (E-mini Dow), MES (Micro E-mini S&P), MNQ (Micro E-mini Nasdaq).
- **Behavior on change**: Chart re-renders with new instrument data. Trendline list refreshes for the selected instrument. URL updates to `/trendlines?instrument=[symbol]`.
- **Keyboard**: Typing while the selector is focused filters the list.

#### FE-FR-018: Detection Configuration Panel

A collapsible panel (accordion or drawer) for tuning detection parameters:

- **Parameters** (each with label, input, range, and tooltip explaining the parameter):

| Parameter | Input Type | Default | Range | Tooltip |
|---|---|---|---|---|
| Min Touch Count | Slider + number input | 3 | 2-5 | "Minimum pivot points that must intersect the trendline" |
| Min Candle Spacing | Slider + number input | 6 | 3-20 | "Minimum 4H candles between consecutive touches" |
| Max Slope Angle | Slider + number input | 45 | 15-75 | "Maximum angle relative to horizontal (lower = flatter)" |
| Min Duration | Dropdown | 3 weeks | 1w, 2w, 3w, 1m, 2m, 3m, 6m | "Minimum time from first touch to current" |
| Touch Tolerance | Slider + number input | 0.5 | 0.2-1.5 | "ATR multiplier for touch proximity (lower = stricter)" |
| Pivot Sensitivity | Slider + number input | 5 | 2-10 | "N-bar lookback for swing point detection" |

- **Preset buttons**: "Tori Trades A+" (loads default A+ criteria), "Relaxed" (min 2 touches, wider tolerance), "Strict" (4+ touches, narrow tolerance).
- **Actions**: "Apply" button triggers a re-scan. "Reset to Default" button restores factory defaults.
- **Persistence**: Custom settings saved per-user via API. Last-used settings loaded on page visit.

---

### 3.4 Trade Execution Page

Route: `/execution`

#### FE-FR-019: Active Positions Table

A data table of all currently open positions:

- **Columns**:

| Column | Description | Sortable |
|---|---|---|
| Instrument | Contract symbol (e.g., "MES Mar 26") | Yes |
| Direction | Long (green) / Short (red) | Yes |
| Contracts | Position size | Yes |
| Entry Price | Fill price | Yes |
| Current Price | Live price (WebSocket) | No |
| Stop Loss | Current stop price | No |
| Take Profit | Current target price | No |
| Unrealized P&L | Dollar amount (green/red) | Yes |
| R-Multiple | Current R (based on stop distance) | Yes |
| Duration | Time since entry (e.g., "2h 15m") | Yes |
| MAE/MFE | Max adverse/favorable excursion ticks | No |

- **Row actions**: Click row to expand inline detail view showing: entry signal source, trendline reference (if any), bracket order details, slippage.
- **Row context menu** (right-click or three-dot button): "Close Position", "Modify Stop", "Modify Target", "Flatten All".
- **Real-time**: Current price, P&L, R-multiple, MAE/MFE update via WebSocket every 1 second.
- **Visual**: Rows alternate background. P&L column text color: green for profit, red for loss.
- **Footer**: Summary row showing total unrealized P&L, total contracts, total open risk.

#### FE-FR-020: Pending Signals Queue

A separate section below positions showing signals awaiting execution:

- **Each signal card shows**:
  - Source: Trendline Engine / TradingView Webhook / Manual.
  - Instrument + Direction.
  - Entry price, Stop price, Target price.
  - Planned R:R ratio.
  - Signal strength / trendline grade (if applicable).
  - Time since signal was generated.
- **Actions per signal**:
  - "Execute" (primary button): Sends order to broker. Confirmation dialog showing order details before submission.
  - "Reject" (secondary button): Marks signal as rejected with optional reason dropdown (Not my setup, Risk too high, Already positioned, Market conditions changed).
  - "Modify" (icon button): Opens form to adjust entry/stop/target before execution.
- **Auto-execution indicator**: If auto-execution is enabled for this signal type, a badge shows "Auto" and a countdown timer shows time until auto-execution (configurable delay, default 60 seconds, to allow manual override).
- **Empty state**: "No pending signals. Signals from trendline detection and TradingView webhooks will appear here."

#### FE-FR-021: Manual Trade Entry Form

A form accessible via "Add Trade" button or from the pending signals section:

- **Fields**:

| Field | Type | Required | Validation |
|---|---|---|---|
| Instrument | Searchable dropdown | Yes | Must be a supported instrument |
| Direction | Toggle: Long / Short | Yes | -- |
| Entry Price | Number input | Yes | Positive number, tick-size validated |
| Contracts | Number input | Yes | Integer, 1-100 |
| Stop Loss | Number input | Yes | Positive number, must be below entry (long) or above (short) |
| Take Profit | Number input | No | Positive number, must be above entry (long) or below (short) |
| Order Type | Dropdown: Market / Limit | Yes | Default: Market |
| Signal Source | Dropdown: Manual / TradingView / Other | Yes | Default: Manual |
| Playbook | Dropdown (user's playbooks) | No | -- |
| Notes | Textarea | No | Max 500 characters |

- **Calculated fields** (display-only, auto-computed):
  - Risk per contract: `|entry - stop| x tick_value`.
  - Total risk: `risk_per_contract x contracts`.
  - R:R ratio: `|entry - target| / |entry - stop|` (if target provided).
  - % of equity at risk.
- **Submit**: "Place Order" button. Disabled until all required fields pass validation. On submit:
  - If live mode: Confirmation dialog with full order summary + "This will execute a LIVE order" warning.
  - If paper mode: Direct submission with toast confirmation.
- **Post-submit**: Toast notification with fill status. Position appears in active positions table.

#### FE-FR-022: Broker Connection Status

A persistent status indicator in the Execution page header:

- **States**:
  - Connected: Green dot + "Connected to [Broker Name]" + last heartbeat time.
  - Disconnected: Red dot + "Disconnected from [Broker Name]" + "Reconnect" button.
  - Connecting: Yellow dot with pulse animation + "Connecting..."
  - Error: Red dot + error message (e.g., "Authentication expired") + "Fix" button linking to Settings.
  - No broker: Gray dot + "No broker connected" + "Connect Broker" button linking to Settings.
- **Multiple brokers**: If multiple brokers are configured, show a dropdown listing each with its status.
- **Auto-reconnect**: System attempts reconnection automatically every 30 seconds when disconnected. UI shows countdown to next attempt.

#### FE-FR-058: Paper/Live Mode Toggle

Accessible via the header mode indicator click or from the Execution page:

- **Toggle UI**: A prominent switch control with "Paper" and "Live" labels.
- **Paper to Live transition**:
  1. Confirmation dialog appears: "Switch to Live Trading?"
  2. Warning text: "Orders will be routed to your broker and executed with real funds."
  3. Checkbox: "I understand that live orders involve real financial risk."
  4. "Switch to Live" button (red/danger variant). Disabled until checkbox is checked.
  5. If paper minimum period (60 days) has not been met, display warning: "You have [X] days of paper trading. We recommend at least 60 days before going live."
- **Live to Paper transition**: Single-click with brief confirmation toast: "Switched to Paper Trading."
- **Visual impact**: Upon switching, the entire application's mode indicator updates, and a full-width toast confirms the change.

---

### 3.5 Trade Journal Page

Route: `/journal`

#### FE-FR-023: Trade Table

The primary view of the journal page, a full-featured data table:

- **Columns**:

| Column | Description | Sortable | Filterable |
|---|---|---|---|
| Date | Entry date/time | Yes | Date range picker |
| Instrument | Contract symbol | Yes | Multi-select dropdown |
| Direction | Long/Short | Yes | Toggle filter |
| Entry Price | Fill price | Yes | -- |
| Exit Price | Fill price | Yes | -- |
| P&L ($) | Realized dollar P&L | Yes | Range slider |
| P&L (%) | Percentage return | Yes | -- |
| R-Multiple | Actual R achieved | Yes | Range slider |
| Playbook | Playbook name | Yes | Multi-select dropdown |
| Duration | Hold time | Yes | -- |
| Grade | Trendline grade (if applicable) | Yes | Multi-select |
| Conviction | User-rated 1-5 | Yes | Star filter |
| Tags | Emotional state tags | No | Tag multi-select |

- **Default sort**: Date descending (newest first).
- **Pagination**: 25 rows per page. Page size selector: 10, 25, 50, 100. Total count displayed: "Showing 1-25 of 147 trades."
- **Row styling**:
  - Winning trades: Subtle green left-border (2px).
  - Losing trades: Subtle red left-border (2px).
  - Breakeven (within 0.1R): Gray left-border.
- **Row click**: Opens trade detail view (FE-FR-024).
- **Bulk actions**: Multi-select via checkboxes. Actions: "Add to Playbook", "Export Selected (CSV)", "Delete" (with confirmation).
- **Column visibility**: Column selector dropdown to show/hide columns. User preference persisted.

#### FE-FR-024: Trade Detail View

A full-width detail view (replaces table) or a slide-over panel when a trade is clicked:

- **Navigation**: Back button/link to return to the trade table. Previous/Next trade navigation arrows.
- **Layout**: Two-column on desktop (chart left, details right). Single column stacked on mobile.

**Left column (55%)**:
- **Mini chart**: TradingView Lightweight Charts showing the instrument around the trade period. Entry and exit points marked with vertical dashed lines (green for entry, red for exit). Trendline(s) overlaid if the trade was trendline-sourced. Stop loss and take profit levels shown as horizontal dashed lines.
- **Screenshot gallery**: If screenshots are attached, display as a carousel below the chart. Click to expand to full-screen lightbox.

**Right column (45%)**:
- **Auto-captured data section** (read-only, styled as a detail grid):
  - Entry: Date, time, price, order type, slippage.
  - Exit: Date, time, price, order type, slippage.
  - P&L: Dollar, percentage, R-multiple.
  - Risk: Stop distance (ticks), risk amount ($), planned R:R.
  - Execution: MAE (ticks + $), MFE (ticks + $), fill quality score.
  - Context: Session (RTH/Overnight), day of week, margin type.
  - Signal: Source, trendline grade (if applicable), touch count, slope.
  - Playbook: Name (clickable link to playbook detail).
- **Journal enrichment section** (editable, see FE-FR-025).

#### FE-FR-025: Journal Enrichment Form

An inline editable form within the trade detail view:

- **Fields**:

| Field | Type | Options/Validation |
|---|---|---|
| Conviction (Pre-Trade) | Star rating (1-5) | 1=Low, 5=High. Clickable stars with hover preview. |
| Emotional State | Multi-select tag picker | Options: Confident, Anxious, FOMO, Revenge, Patient, Disciplined, Frustrated, Excited, Fearful, Neutral. Max 3 selections. |
| Pre-Trade Notes | Rich textarea | Markdown support. Placeholder: "What was your thesis before entering?" Max 2000 chars. |
| Post-Trade Review | Rich textarea | Markdown support. Placeholder: "What did you learn from this trade?" Max 2000 chars. |
| Mistakes | Multi-select tag picker | Options: Moved Stop, Entered Early, Oversized, Held Too Long, Exited Too Early, Ignored Setup Criteria, FOMO Entry, Revenge Trade, No Stop Loss. |
| Rule Compliance | Checklist | Dynamic based on user's playbook rules. Each rule is a checkbox. |
| Screenshots | File upload area | See FE-FR-026. |

- **Auto-save**: Changes save automatically 1 second after the user stops typing (debounced). A subtle "Saving..." / "Saved" indicator appears near the form header.
- **Validation**: Emotional state tags limited to 3. Notes fields show character count. All fields optional.

#### FE-FR-026: Screenshot Upload

A drag-and-drop file upload component within the journal enrichment form:

- **Drop zone**: Dashed border area with "Drag screenshots here or click to upload" text and an Upload icon.
- **File types**: PNG, JPG, JPEG, WebP. Max file size: 5MB each. Max files per trade: 10.
- **Upload behavior**:
  - On drop/select: Immediate upload with progress bar per file.
  - Preview: Thumbnail grid (120x80px) showing uploaded images.
  - Each thumbnail has a delete button (X icon, top-right corner) with "Are you sure?" tooltip confirmation.
- **Clipboard paste**: Support `Cmd+V` / `Ctrl+V` to paste screenshot from clipboard directly into the upload area.
- **Storage**: Files upload to S3-compatible storage (Cloudflare R2) via presigned URL. The frontend requests a presigned URL from the API, uploads directly to R2, then registers the file URL with the trade entry.
- **Error handling**: File too large: "File exceeds 5MB limit. Please reduce the image size." Wrong format: "Unsupported format. Please use PNG, JPG, or WebP."

#### FE-FR-027: Trade Search

A search bar at the top of the trade journal page:

- **Full-text search**: Searches across trade notes, post-trade reviews, instrument names, playbook names, and tags. Backend handles the full-text search via PostgreSQL `tsvector`.
- **Search input**: Text input with search icon. Debounced at 300ms. Minimum 2 characters to trigger search.
- **Filter bar** (horizontal, below search):
  - Date range: Calendar date range picker with presets (Today, This Week, This Month, Last 30 Days, Last 90 Days, Year to Date, All Time, Custom).
  - Instrument: Multi-select dropdown.
  - Playbook: Multi-select dropdown.
  - Outcome: Toggle buttons: All | Winners | Losers | Breakeven.
  - Direction: Toggle buttons: All | Long | Short.
  - Conviction: Star rating filter (minimum conviction level).
- **Active filters**: Displayed as removable chips/badges below the filter bar. "Clear all filters" link when any filter is active.
- **Results**: Trade table updates to show matching results. Result count displayed: "Found 12 trades matching your search."
- **URL sync**: Filters are reflected in URL query parameters for shareable/bookmarkable views.

---

### 3.6 Playbook Management Page

Route: `/playbooks`

#### FE-FR-028: Playbook List View

A card grid layout showing all user playbooks:

- **Card layout**: 2 columns on desktop, 1 column on mobile. Each card contains:
  - **Header**: Playbook name + auto-classify badge (if auto-classification rules are configured).
  - **Metrics row**: Win Rate | Expectancy | Trade Count | Profit Factor.
  - **Mini equity curve**: A sparkline showing the playbook's cumulative P&L over time (64px height).
  - **Last trade**: "Last trade: [date]" in muted text.
  - **Actions**: "View Details" link, three-dot menu with "Edit", "Delete" options.
- **Empty state**: "No playbooks configured. Create your first playbook to start tracking strategy-specific performance." + "Create Playbook" button.
- **Create button**: Prominent "+ New Playbook" button at the top of the page. Opens the playbook form (FE-FR-030).
- **Sort**: Dropdown to sort by: Name, Win Rate, Expectancy, Trade Count, Last Trade Date.
- **Default playbooks**: The system-provided playbooks ("A+ Trendline Break", "Standard Trendline Break", "Trendline Bounce") are marked with a "System" badge and cannot be deleted (only edited for name/description).

#### FE-FR-029: Playbook Detail View

Route: `/playbooks/[id]`

A dedicated page for a single playbook:

- **Header**: Playbook name (editable inline), description, auto-classification rules summary, "Edit" and "Delete" buttons.
- **Metrics section**: Full metric cards matching the analytics dashboard format (see FE-FR-034), but scoped to this playbook only. Minimum metrics:
  - Win Rate, Loss Rate, Breakeven Rate.
  - Average Winner ($), Average Loser ($), Largest Win, Largest Loss.
  - Profit Factor, Expectancy, Average R-Multiple.
  - Total Trades, Total P&L, Average Duration.
- **Equity curve**: Full-width line chart showing cumulative P&L over time for this playbook's trades.
- **Trade list**: Filtered trade table (same component as FE-FR-023) pre-filtered to this playbook. All sorting and filtering available.
- **Time analysis**: Bar chart showing P&L by month for this playbook.

#### FE-FR-030: Playbook CRUD Forms

A modal or slide-over form for creating/editing playbooks:

- **Fields**:

| Field | Type | Required | Validation |
|---|---|---|---|
| Name | Text input | Yes | 2-50 characters, unique per user |
| Description | Textarea | No | Max 500 characters |
| Auto-Classify Rules | Rule builder | No | See below |
| Target R:R | Number input | No | Range 1.0-10.0 |
| Max Risk Per Trade | Number input (% of equity) | No | Range 0.1-10.0 |

- **Auto-classification rule builder**: A simple rule constructor:
  - Condition fields: Trendline Grade (A+, A, B), Direction (Long, Short, Both), Min Touch Count (number), Setup Type (Break, Bounce).
  - Logic: All conditions must match (AND logic).
  - Preview: "Trades will be auto-assigned to this playbook when: Grade is A+ AND Direction is Long AND Touch Count >= 3."
- **Delete**: Confirmation dialog: "Delete playbook [name]? This will not delete the trades, but they will be unassigned from this playbook." Trades' `playbook_id` is set to null.

#### FE-FR-031: Playbook Comparison View

Route: `/playbooks/compare?ids=[id1],[id2]`

A side-by-side comparison of 2 playbooks:

- **Selection**: From the playbook list, checkboxes allow selecting exactly 2 playbooks. "Compare" button appears when 2 are selected.
- **Layout**: Two columns, each showing the same metrics for one playbook. Metrics that are "better" in one column are highlighted with a subtle green background.
- **Sections compared**:
  - Key metrics (table: metric name, playbook A value, playbook B value).
  - Equity curves overlaid on the same chart (different colors, with legend).
  - Win rate over time (rolling 10-trade window) as overlaid line charts.
  - R-multiple distributions as overlapping histograms.
- **Conclusion helper**: A summary text at the top: "Playbook A has a higher win rate (72% vs 58%) but Playbook B has a better expectancy ($145 vs $98 per trade)."

---

### 3.7 Analytics Dashboard Page

Route: `/analytics`

#### FE-FR-032: Analytics Filter Bar

A sticky filter bar at the top of the analytics page:

- **Filters**:
  - **Date range**: Calendar date range picker with presets (This Month, Last 30 Days, Last 90 Days, YTD, All Time, Custom). Default: Last 90 Days.
  - **Instrument**: Multi-select dropdown, "All Instruments" default.
  - **Playbook**: Multi-select dropdown, "All Playbooks" default.
  - **Mode**: Toggle: Paper | Live | Both. Default: Both.
- **Behavior**: Changing any filter triggers a re-fetch of all analytics data. All charts and metrics update simultaneously. URL query parameters sync with filter state.
- **Applied filters**: Displayed as chips below the filter bar with individual remove buttons.

#### FE-FR-033: Metric Cards Grid

A responsive grid of metric cards:

- **Layout**: 4 columns on desktop (>1280px), 3 columns on tablet (768-1280px), 2 columns on mobile (<768px).
- **Card design**: Each card contains:
  - Metric label (small, muted text).
  - Metric value (large, bold text).
  - Trend indicator: Small arrow (up/down) with percentage change vs. prior period. Green for improvement, red for deterioration. "Improvement" semantics vary: higher win rate = improvement, higher max drawdown = deterioration.
  - Sparkline (optional): Tiny inline chart showing the metric over the last 30 data points.

- **Metrics displayed** (grouped visually with section headers):

**Trade Performance:**

| ID | Metric | Format | Calculation |
|---|---|---|---|
| M01 | Win Rate | % (e.g., "68.2%") | Winners / Total Closed Trades |
| M02 | Loss Rate | % (e.g., "31.8%") | Losers / Total Closed Trades |
| M03 | Average Winner | $ (e.g., "$342") | Mean P&L of winning trades |
| M04 | Average Loser | $ (e.g., "-$198") | Mean P&L of losing trades |
| M05 | Largest Win | $ | Max single-trade P&L |
| M06 | Largest Loss | $ | Min single-trade P&L |
| M07 | Profit Factor | Ratio (e.g., "2.14") | Gross Profit / Gross Loss |
| M08 | Expectancy | $ (e.g., "$87/trade") | (Win% x Avg Win) - (Loss% x Avg Loss) |
| M09 | Total Net P&L | $ | Sum of all closed trade P&L |
| M10 | Total Trades | Count | Number of closed trades in period |

**Risk-Adjusted:**

| ID | Metric | Format | Calculation |
|---|---|---|---|
| M11 | Sharpe Ratio | Ratio (e.g., "1.82") | Mean return / Std dev of returns (annualized) |
| M12 | Sortino Ratio | Ratio | Mean return / Downside deviation |
| M13 | Calmar Ratio | Ratio | Annual return / Max drawdown |
| M14 | Max Drawdown ($) | $ | Largest peak-to-trough equity decline |
| M15 | Max Drawdown (%) | % | Max drawdown as % of peak equity |
| M16 | Recovery Time | Duration (e.g., "12 days") | Time from max drawdown trough to new equity high |

**R-Multiple Analysis:**

| ID | Metric | Format | Calculation |
|---|---|---|---|
| M17 | Average R | Number (e.g., "0.72R") | Mean R-multiple across all trades |
| M18 | Best R | Number (e.g., "4.2R") | Maximum R-multiple achieved |
| M19 | Worst R | Number (e.g., "-1.0R") | Minimum R-multiple |
| M20 | R Expectancy | Number (e.g., "0.35R") | (Win% x Avg Win R) - (Loss% x Avg Loss R) |

**Execution Quality:**

| ID | Metric | Format | Calculation |
|---|---|---|---|
| M21 | Avg Slippage | Ticks (e.g., "0.8 ticks") | Mean |fill_price - signal_price| |
| M22 | Avg MAE | Ticks | Mean maximum adverse excursion |
| M23 | Avg MFE | Ticks | Mean maximum favorable excursion |
| M24 | Fill Quality | % (e.g., "92%") | Percentage of fills within 1 tick of signal price |

**Behavioral:**

| ID | Metric | Format | Calculation |
|---|---|---|---|
| M25 | Rule Compliance | % (e.g., "85%") | Trades following all playbook rules / Total trades |
| M26 | Cost of Mistakes | $ | Sum P&L of trades tagged with mistakes |
| M27 | Avg Conviction | Stars (e.g., "3.8/5") | Mean conviction rating across trades |

#### FE-FR-034: Equity Curve Chart

A full-width line chart below the metric cards:

- **X-axis**: Time (dates). Auto-scaled to the selected date range.
- **Y-axis**: Cumulative P&L in dollars. Starting from $0 at the first trade.
- **Line**: Smooth (curved interpolation) with area fill below the line. Green area above $0, red area below $0.
- **Drawdown overlay**: Optional toggle to show drawdown periods as shaded red areas between the equity curve and its running maximum.
- **Benchmark line**: Optional toggle to show a flat $0 line (break-even reference).
- **Tooltips**: Hover shows date, cumulative P&L, trade count, and drawdown % at that point.
- **Paper vs. Live**: If both modes are selected in filters, two separate lines with different colors and a legend.
- **Interactions**: Click a point on the curve to navigate to the trade that occurred on that date in the journal.

#### FE-FR-035: P&L Calendar Heatmap

A calendar heatmap visualization (similar to GitHub contribution graph):

- **Layout**: Monthly grid, one cell per trading day. Weekends and market holidays are grayed out or omitted.
- **Color scale**: Continuous gradient from deep red (worst losing day) through white/neutral ($0) to deep green (best winning day). Color intensity proportional to P&L magnitude.
- **Cell content**: Dollar P&L displayed inside the cell (if cell size permits) or on hover tooltip.
- **Tooltip**: Date, Day P&L ($), Trade Count, Win/Loss breakdown.
- **Navigation**: Month/year navigation arrows. Default view: current month with 2 prior months visible.
- **Click behavior**: Clicking a cell filters the trade journal to that specific date.
- **Legend**: Color scale bar showing the P&L range (min to max) for the visible period.

#### FE-FR-036: R-Multiple Distribution Histogram

A bar chart showing the distribution of R-multiples:

- **X-axis**: R-multiple buckets (e.g., -2R to -1.5R, -1.5R to -1R, ..., 0R to 0.5R, ..., 3R to 3.5R, 3.5R+).
- **Y-axis**: Trade count.
- **Bar colors**: Red for negative R buckets, green for positive R buckets.
- **Reference lines**: Vertical dashed line at 0R (breakeven). Vertical dashed line at the mean R value (labeled).
- **Annotations**: Text showing "Average R: 0.72" and "Median R: 0.45" in the chart margin.
- **Tooltip**: Hover on a bar shows the R-range and exact trade count.

#### FE-FR-037: Time-Based Analysis Charts

A section with multiple small charts analyzing performance by time dimensions:

- **P&L by Day of Week**: Horizontal bar chart. Each bar = a weekday (Mon-Fri). Color: green if positive, red if negative.
- **P&L by Hour of Day**: Vertical bar chart. Each bar = an hour (7am-4pm CT for RTH). Color: green/red.
- **P&L by Month**: Vertical bar chart. Each bar = a calendar month. Color: green/red.
- **Win Rate by Session**: Donut chart comparing RTH vs. Overnight win rates.
- **Each chart**: Title, data, and a one-line insight text below (e.g., "Tuesdays are your most profitable day (+$1,240 avg)").

#### FE-FR-038: MAE/MFE Scatter Plots

Two scatter plot charts:

- **MAE Scatter (left)**:
  - X-axis: MAE (maximum adverse excursion, in ticks or dollars).
  - Y-axis: Trade P&L.
  - Each dot = one trade. Green dot for winners, red for losers.
  - Insight: Cluster of losing trades with high MAE suggests stops may be too wide. Large winners with low MAE suggests entry timing is good.
  - Reference line: Horizontal at $0 P&L. Vertical at average MAE.
- **MFE Scatter (right)**:
  - X-axis: MFE (maximum favorable excursion).
  - Y-axis: Trade P&L.
  - Each dot = one trade.
  - Insight: Winners with high MFE but low captured P&L suggests exiting too early.
  - Reference line: 45-degree diagonal line representing "captured all favorable excursion."
- **Both plots**: Tooltip on hover shows trade details (instrument, date, P&L, R). Click dot navigates to trade detail.

#### FE-FR-039: Drawdown Chart

A standalone area chart:

- **X-axis**: Time.
- **Y-axis**: Drawdown percentage (0% at top, negative percentages going down).
- **Area fill**: Red, with darker shading for deeper drawdowns.
- **Annotations**: The maximum drawdown point is labeled with its percentage and date.
- **Recovery periods**: Time between drawdown start and recovery (return to 0%) shown with subtle vertical span markers.
- **Tooltip**: Hover shows date, drawdown %, drawdown $ amount, and days in drawdown.

---

### 3.8 Settings Page

Route: `/settings`

#### FE-FR-040: Settings Navigation

A tabbed or sidebar-within-page layout with sections:

- Profile
- Trading Preferences
- Broker Connections
- Notifications
- Detection Defaults
- Risk Management
- Appearance
- Data & Privacy

Each section is its own sub-route: `/settings/profile`, `/settings/brokers`, etc.

#### FE-FR-041: Profile Management

- **Fields**: Display name, email (read-only if using OAuth), avatar upload, timezone (dropdown with auto-detect).
- **Account info**: Subscription tier badge, member since date, usage stats (trades this month, API calls).
- **Actions**: "Change Password" (if email auth), "Delete Account" (with double-confirmation and data export prompt).

#### FE-FR-042: Trading Preferences

| Preference | Type | Default | Description |
|---|---|---|---|
| Default Instrument | Dropdown | MES | Pre-selected instrument on Trendlines page |
| Default Timeframe | Dropdown | 4H | Pre-selected chart timeframe |
| Default Order Type | Dropdown | Market | For manual trade entry |
| Slippage Assumption (Paper) | Number (ticks) | 1 | Simulated slippage for paper trades |
| Auto-Execute Signals | Toggle | Off | Whether trendline signals auto-execute without approval |
| Auto-Execute Delay | Number (seconds) | 60 | Delay before auto-execution (allows manual override) |
| Currency Display | Dropdown | USD | Display currency for P&L |

- **Save behavior**: Auto-save on change with toast confirmation.

#### FE-FR-043: Broker Connection Management

A card-based list of broker connections:

- **Each connection card**:
  - Broker logo + name.
  - Connection status: Connected (green) / Disconnected (red) / Error (yellow).
  - Account ID (masked, last 4 digits visible).
  - Last sync timestamp.
  - Actions: "Test Connection" (sends a ping, shows result), "Reconnect", "Remove" (with confirmation).
- **Add broker flow**:
  1. "Add Broker" button opens a modal.
  2. Step 1: Select broker (IBKR, Tradovate, Webull). Each option shows a card with broker logo, supported features, and commission info.
  3. Step 2: Credential input specific to the selected broker:
     - IBKR: Host, Port, Client ID, Account ID. Help link to IB Gateway setup docs.
     - Tradovate: Username, Password, App ID, App Version. Help link to Tradovate API docs.
     - Webull: App Key, App Secret. Help link to Webull API docs.
  4. Step 3: Test connection. Show success/failure with specific error message.
  5. Step 4: Confirm and save. Connection appears in the list.
- **Credential storage note**: Displayed text: "Credentials are encrypted at rest and never stored in plain text."

#### FE-FR-044: Notification Preferences

A table/grid of notification types and channels:

| Notification Type | Dashboard | Telegram | Discord | Email |
|---|---|---|---|---|
| Trendline Break Alert | Toggle | Toggle | Toggle | Toggle |
| Trendline Touch Alert | Toggle | Toggle | Toggle | Toggle |
| New A+ Trendline | Toggle | Toggle | Toggle | Toggle |
| Trade Filled | Toggle | Toggle | Toggle | Toggle |
| Trade Closed | Toggle | Toggle | Toggle | Toggle |
| Daily P&L Summary | Toggle | -- | -- | Toggle |
| Weekly Performance Report | -- | -- | -- | Toggle |
| System Alerts (errors, downtime) | Toggle | Toggle | -- | Toggle |

- **Channel setup**: Each channel (Telegram, Discord) has a "Configure" button. Telegram: shows bot link + chat ID input. Discord: webhook URL input.
- **Quiet hours**: Toggle with time range picker (e.g., "10pm - 7am"). No notifications during quiet hours except system alerts.
- **Defaults**: Dashboard toggles all ON. External channels all OFF until configured.

#### FE-FR-045: Detection Parameter Defaults

Same parameter form as FE-FR-018 (Detection Configuration Panel), but changes here set the user's global defaults. These defaults are used when visiting the Trendlines page without explicit overrides.

#### FE-FR-046: Risk Management Rules

Configuration for system-enforced risk limits:

| Rule | Type | Default | Description |
|---|---|---|---|
| Max Position Size | Number (contracts) | 5 | Maximum contracts per order |
| Max Daily Loss | Number ($) | $500 | Trading halts when daily loss exceeds this |
| Max Concurrent Positions | Number | 3 | Maximum open positions at once |
| Min R:R Ratio | Number | 2.0 | Orders below this R:R are rejected |
| Max % Equity at Risk | Number (%) | 2% | Max risk per trade as % of account equity |
| Correlation Limit | Number | 2 | Max positions in correlated instruments |

- **Enforcement**: When a rule would be violated, the system blocks the trade and shows the specific rule violation in the pending signals queue.
- **Override**: Each rule has an "Override for this trade" option in the execution flow (with a warning log entry).

---

### 3.9 Onboarding Flow (Phase 3)

Route: `/onboarding`

#### FE-FR-047: Welcome Wizard

A multi-step onboarding flow for new users:

- **Step indicator**: Horizontal progress bar showing current step and total steps.
- **Steps**:

1. **Welcome** (splash screen):
   - TrendEdge logo, tagline: "AI-powered futures trading, from detection to journal."
   - "Get Started" button.
   - "Skip Setup" link (goes to dashboard with empty state guidance).

2. **Trading Profile**:
   - Experience level: Beginner / Intermediate / Advanced (radio buttons). Affects default settings.
   - Primary instruments: Multi-select checkboxes of supported instruments.
   - Trading style: Trendline Swing (default), Systematic/Algo, Manual Discretionary (radio buttons).
   - Timezone: Auto-detected, editable dropdown.

3. **Broker Connection** (optional):
   - Same flow as FE-FR-043 but embedded in the wizard.
   - "Skip for now" option with note: "You can connect a broker anytime from Settings."

4. **First Playbook**:
   - Pre-populate with "A+ Trendline Break" playbook if Trendline Swing was selected.
   - Brief explanation of what playbooks are and how they track strategy performance.
   - "Create" button or "Use Default Playbooks" button.

5. **Paper Trading Activation**:
   - Explanation of paper trading mode and the 60-day recommended period.
   - "Start Paper Trading" button (activates paper mode).
   - Note: "Paper trading lets you test the full system risk-free before going live."

6. **Complete**:
   - Confirmation screen: "You're all set!"
   - Summary of configured settings.
   - "Go to Dashboard" button.

- **State**: Onboarding completion is tracked. Users who haven't completed it see a banner on the dashboard: "Finish your setup" with a link to resume.
- **Skip behavior**: Skipping any step sets sensible defaults. All steps can be configured later from Settings.

---

### 3.10 Landing Page (Phase 3)

Route: `/` (unauthenticated)

#### FE-FR-048: Marketing Landing Page

A single-page marketing site for user acquisition:

- **Hero section**: Headline, subheadline, CTA button ("Start Free"), hero screenshot/demo of the dashboard.
- **Problem statement**: "Tired of switching between 3-4 tools?" with icon grid showing the fragmentation.
- **Feature sections**: Detection, Execution, Journaling, Analytics — each with screenshot, description, and key benefit.
- **Comparison table**: TrendEdge vs. competitors (derived from master PRD section 4).
- **Pricing section**: Tier cards (Free, Trader, Pro, Team) with feature comparison.
- **Social proof**: Testimonials/early user quotes (when available), "Built for the Tori Trades community" callout.
- **Footer**: Links to docs, support, privacy policy, terms of service.
- **Performance**: Must achieve Lighthouse performance score >95. Static content, no client-side data fetching. ISR for pricing data if dynamic.
- **SEO**: Meta tags, Open Graph tags, structured data (SoftwareApplication schema). Target keywords: "futures trading journal", "trendline detection", "automated futures trading".

---

### 3.11 AI Chat Interface

Route: `/chat`

#### FE-FR-049: Conversational Analytics Chat

A chat interface for natural language queries against trading data:

- **Layout**: Chat messages in a scrollable container (full page height minus header). Input area fixed at the bottom.
- **Message types**:
  - **User messages**: Right-aligned, blue background, plain text.
  - **Assistant messages**: Left-aligned, card-style with subtle background. Can contain:
    - Text (formatted with markdown).
    - Inline metric cards.
    - Embedded charts (rendered using the same chart components as the analytics dashboard).
    - Trade lists (clickable links to trade details).
    - Tables.
- **Input area**:
  - Textarea (auto-growing, max 4 lines visible).
  - Send button (arrow icon). Disabled while awaiting response.
  - Keyboard: Enter to send, Shift+Enter for new line.
- **Suggested prompts**: On empty chat, show a grid of suggested questions:
  - "What is my win rate by day of week?"
  - "Show my best and worst trades this month."
  - "Compare my trendline break vs. bounce performance."
  - "How much have my mistakes cost me?"
  - "What is my average R-multiple on A+ setups?"
- **Streaming**: Assistant responses stream token-by-token for perceived responsiveness.
- **Context awareness**: The AI has access to the user's trade data, playbooks, and analytics. It does not have access to other users' data.
- **Conversation history**: Chat history persists within a session. "New Chat" button clears the conversation.
- **Error handling**: If the AI cannot answer a query: "I couldn't find enough data to answer that question. Try being more specific or adjusting the date range."

---

### 3.12 Real-Time Updates

#### FE-FR-050: WebSocket Integration

The frontend maintains a persistent WebSocket connection for live updates:

- **Connection**: Established on app mount. Reconnects automatically with exponential backoff (1s, 2s, 4s, 8s, max 30s).
- **Authentication**: WebSocket connection includes the auth token as a query parameter. Server validates before accepting.
- **Connection status**: A small dot indicator in the header (green = connected, yellow = reconnecting, red = disconnected). Visible only on hover or when not connected.

**Subscribed channels and their UI effects:**

| Channel | Event | UI Update |
|---|---|---|
| `positions` | Position opened/closed/updated | Active positions table, dashboard widget |
| `fills` | Order filled | Toast notification, position update, journal entry created |
| `trendlines` | New trendline detected, alert triggered | Trendline list, dashboard widget, chart overlay |
| `signals` | New signal generated | Pending signals queue, notification badge |
| `account` | Balance/margin update | Dashboard equity stat |
| `alerts` | Notification dispatched | Notification bell badge, toast |

- **Optimistic reconciliation**: When a WebSocket message conflicts with a pending optimistic update, the server data takes precedence and the UI reconciles.
- **Stale data detection**: If the WebSocket disconnects for >60 seconds, on reconnection the client performs a full data refresh for all visible widgets.

---

### 3.13 Responsive Design

#### FE-FR-051: Responsive Breakpoints

| Breakpoint | Width | Name | Layout |
|---|---|---|---|
| Mobile | <768px | `sm` | Single column, drawer navigation, stacked cards |
| Tablet | 768-1279px | `md` | Two columns, collapsible sidebar, responsive charts |
| Desktop | 1280-1535px | `lg` | Three columns where applicable, expanded sidebar |
| Wide | 1536px+ | `xl` | Full layout, maximum chart area |

- **Desktop-primary**: All features are designed for desktop first. Mobile receives a functional but simplified experience.
- **Charts on mobile**: TradingView Lightweight Charts supports touch interactions (pinch-zoom, pan). Chart containers take full width. Detail panels stack below charts.
- **Tables on mobile**: Horizontal scroll with fixed first column (instrument name). Alternatively, card-based layout replacing table rows.
- **Navigation on mobile**: Bottom tab bar replacing sidebar on screens <768px. Tabs: Dashboard, Trendlines, Journal, More (dropdown with remaining items).

---

### 3.14 Theme System

#### FE-FR-052: Dark Mode (Default) / Light Mode

- **Default**: Dark mode. Set via `class="dark"` on `<html>` element (Tailwind dark mode strategy: `class`).
- **Toggle**: Available in header user dropdown and Settings > Appearance. Toggle switch with sun/moon icons.
- **Persistence**: Theme preference stored in `localStorage` under `theme` key. On initial load, check localStorage first, then respect `prefers-color-scheme` media query, then default to dark.
- **Transition**: Theme switch applies a 200ms CSS transition on background and text colors to avoid jarring flash.
- **System option**: Three-state toggle: Light | Dark | System (follows OS preference).
- **SSR flash prevention**: Theme is read from a cookie (set on toggle) so the server can render the correct theme on first load, preventing a white flash on dark-mode-preferred clients.

---

### 3.15 Keyboard Shortcuts

#### FE-FR-053: Global Keyboard Shortcuts

| Shortcut | Action | Context |
|---|---|---|
| `Cmd+K` / `Ctrl+K` | Open command palette | Global |
| `Cmd+/` / `Ctrl+/` | Show keyboard shortcuts help dialog | Global |
| `G then D` | Navigate to Dashboard | Global (vim-style sequence) |
| `G then T` | Navigate to Trendlines | Global |
| `G then E` | Navigate to Execution | Global |
| `G then J` | Navigate to Journal | Global |
| `G then P` | Navigate to Playbooks | Global |
| `G then A` | Navigate to Analytics | Global |
| `G then C` | Navigate to AI Chat | Global |
| `G then S` | Navigate to Settings | Global |
| `N` | New trade entry (opens form) | Journal, Execution pages |
| `Escape` | Close modal/panel/palette | Global |
| `[` / `]` | Previous / Next item | Trade detail view (navigate trades) |
| `F` | Toggle favorite instrument | Trendlines page |
| `?` | Show contextual help | Global |

- **Implementation**: Key bindings registered via a global keyboard event listener. Suppressed when focus is in a text input, textarea, or contenteditable element.
- **Help dialog**: `Cmd+/` opens a modal listing all shortcuts, grouped by context.

---

### 3.16 Accessibility

#### FE-FR-054: WCAG 2.1 AA Compliance

- **Color contrast**: All text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text) in both dark and light themes. Green/red chart colors are supplemented with patterns or labels for color-blind users.
- **Keyboard navigation**: All interactive elements are reachable via Tab key. Focus order matches visual order. Focus indicators are visible (2px ring, primary color).
- **Screen reader support**: All images have `alt` text. Charts have `aria-label` describing the data trend. Data tables use proper `<th>` elements with `scope` attributes. Dynamic content changes announced via `aria-live` regions.
- **Reduced motion**: Users with `prefers-reduced-motion` OS setting see no animations (transitions, chart drawing animations, loading skeletons use instant render).
- **Form accessibility**: All inputs have associated `<label>` elements. Error messages are linked via `aria-describedby`. Required fields marked with `aria-required="true"`.
- **Skip navigation**: "Skip to main content" link as the first focusable element on every page.
- **Semantic HTML**: Proper use of `<nav>`, `<main>`, `<aside>`, `<section>`, `<article>`, headings hierarchy (`<h1>` through `<h6>`).

---

### 3.17 Loading, Error, and Empty States

#### FE-FR-055: State Definitions for All Views

Every page and widget has three defined states beyond the normal data-populated state:

| Page/Widget | Loading State | Error State | Empty State |
|---|---|---|---|
| Dashboard P&L | Skeleton card with shimmer | "Unable to load P&L data. Retry." | "$0.00 — No trades today" |
| Active Positions | 3-row skeleton table | "Unable to fetch positions. Check broker connection." | "No open positions" |
| Trendline Chart | Chart area skeleton with axis placeholders | "Unable to load chart data. Retry." | "Select an instrument to view trendlines" |
| Trendline List | 5-item skeleton list | "Unable to fetch trendlines. Retry." | "No trendlines detected for [instrument]. Adjust parameters or try another instrument." |
| Pending Signals | Card skeleton | "Unable to load signals. Retry." | "No pending signals. Signals will appear when the trendline engine or webhooks generate them." |
| Trade Table | 5-row skeleton table | "Unable to load trades. Retry." | "No trades recorded yet. Add your first trade or connect a broker to start auto-journaling." with "Add Trade" CTA |
| Playbook List | 3-card skeleton grid | "Unable to load playbooks. Retry." | "No playbooks yet. Create your first playbook to track strategy performance." with "Create Playbook" CTA |
| Analytics Dashboard | Skeleton cards + chart placeholders | "Unable to calculate analytics. Retry." | "Start trading to see your analytics. Paper trades count! Need at least 5 closed trades for meaningful metrics." |
| P&L Calendar | Calendar grid skeleton | "Unable to render calendar. Retry." | Calendar renders with all cells at $0 / neutral color |
| AI Chat | Typing indicator (3 bouncing dots) | "AI service unavailable. Please try again in a few minutes." | Suggested prompts grid |
| Settings | Form skeleton | "Unable to load settings. Retry." | N/A (always has defaults) |

- **Retry mechanism**: All error states include a "Retry" button that re-triggers the failed data fetch.
- **Partial errors**: If one widget fails but others load successfully, only the failed widget shows its error state. The rest of the page remains functional.

---

## 4. Non-Functional Requirements

### Performance

#### FE-NFR-001: First Contentful Paint (FCP)

FCP must be less than 1.5 seconds on a 4G connection for all pages. Measured via Vercel Analytics and Lighthouse CI.

**Implementation approach**: Server-side rendering for initial HTML, critical CSS inlined, font preloading, image optimization via Next.js `<Image>` component.

#### FE-NFR-002: Time to Interactive (TTI)

TTI must be less than 3 seconds on a 4G connection for all pages.

**Implementation approach**: Code splitting per route via Next.js dynamic imports, tree shaking, deferred loading of non-critical scripts (analytics, third-party widgets).

#### FE-NFR-003: Largest Contentful Paint (LCP)

LCP must be less than 2.5 seconds. The largest content element on most pages is the primary chart or the trade table.

**Implementation approach**: Charts render with skeleton first, data streams in. Tables render headers immediately, rows stream via React Suspense.

#### FE-NFR-004: Cumulative Layout Shift (CLS)

CLS must be less than 0.1.

**Implementation approach**: All images and charts have explicit width/height or aspect-ratio. Skeleton loaders match the exact dimensions of loaded content. No dynamically injected content that shifts layout.

#### FE-NFR-005: First Input Delay (FID)

FID must be less than 100ms.

**Implementation approach**: Minimize main-thread blocking. Offload expensive computations (chart data processing, metric calculations) to Web Workers where applicable.

#### FE-NFR-006: Lighthouse Score

All pages must achieve a Lighthouse score of 90+ for Performance, Accessibility, Best Practices, and SEO categories.

**Enforcement**: Lighthouse CI runs on every PR. Scores below 90 in any category block merge.

#### FE-NFR-007: Bundle Size Targets

| Bundle | Target | Measured By |
|---|---|---|
| Initial JS (first load) | <150 KB gzipped | `next build` output |
| Per-route JS chunk | <50 KB gzipped | `next build` output |
| TradingView Lightweight Charts | <45 KB gzipped | Loaded dynamically, only on chart pages |
| D3.js (analytics charts) | <30 KB gzipped (tree-shaken) | Loaded dynamically, only on analytics page |
| Total CSS | <30 KB gzipped | Tailwind purge output |

**Enforcement**: Bundle analyzer (`@next/bundle-analyzer`) run on CI. Alerts if any chunk exceeds target by >10%.

#### FE-NFR-008: Real-Time Data Latency

WebSocket messages must be reflected in the UI within 200ms of receipt. Position P&L updates must render at 1 Hz (1 update per second) without dropped frames.

#### FE-NFR-009: API Response Handling

- All API calls include a 10-second timeout.
- Failed requests retry up to 3 times with exponential backoff (1s, 2s, 4s).
- Stale data is served from TanStack Query cache while revalidation occurs in the background (stale-while-revalidate pattern).
- Cache TTL: 30 seconds for position data, 5 minutes for analytics data, 1 hour for settings data.

### Reliability

#### FE-NFR-010: Error Boundary Coverage

Every page-level component and every widget-level component is wrapped in a React Error Boundary. Uncaught errors render the error state (FE-FR-055) for that component without crashing the entire application.

#### FE-NFR-011: Offline Resilience

When network connectivity is lost:
- A banner appears at the top of the page: "You are offline. Some features may be unavailable."
- Cached data remains visible and readable.
- Write operations (journal edits, settings changes) are queued locally and synced when connectivity returns.
- Real-time data (positions, prices) shows a "stale" indicator with the last update timestamp.

### Scalability

#### FE-NFR-012: Data Volume Handling

- Trade table must perform smoothly with up to 10,000 rows (virtualized rendering via `@tanstack/react-virtual`).
- Analytics must compute and render within 3 seconds for up to 5,000 trades.
- Chart must render up to 2,000 candles without frame drops.
- Trendline list must handle up to 100 trendlines per instrument.

---

## 5. UI/UX Design System

### 5.1 Component Library

Built on shadcn/ui. All components are copied into the project (not imported from a package), allowing full customization.

**Core components used:**

| Category | Components |
|---|---|
| Layout | Card, Separator, ScrollArea, Sheet (slide-over), Dialog (modal), Tabs |
| Navigation | NavigationMenu, Breadcrumb, Command (palette), DropdownMenu |
| Data Display | Table, Badge, Avatar, Tooltip, HoverCard |
| Data Input | Input, Textarea, Select, Checkbox, RadioGroup, Switch, Slider, DatePicker, Combobox |
| Feedback | Toast, Alert, AlertDialog, Progress, Skeleton |
| Overlay | Dialog, Sheet, Popover, ContextMenu |
| Chart | Custom components wrapping TradingView Lightweight Charts and D3.js |

### 5.2 Color Palette

#### Dark Theme (Default)

```
Background:
  --background:        hsl(222, 47%, 6%)      /* #0B0F19 - deepest background */
  --card:              hsl(222, 41%, 9%)      /* #0E1424 - card surfaces */
  --popover:           hsl(222, 41%, 9%)      /* same as card */
  --muted:             hsl(222, 30%, 15%)     /* #1A2035 - muted backgrounds */

Foreground:
  --foreground:        hsl(210, 40%, 96%)     /* #F1F5F9 - primary text */
  --card-foreground:   hsl(210, 40%, 96%)     /* same as foreground */
  --muted-foreground:  hsl(215, 20%, 55%)     /* #7B8BA5 - secondary text */

Border:
  --border:            hsl(222, 25%, 18%)     /* #232D42 - borders */
  --input:             hsl(222, 25%, 22%)     /* #2A3550 - input borders */
  --ring:              hsl(217, 91%, 60%)     /* #3B82F6 - focus ring */

Accent:
  --primary:           hsl(217, 91%, 60%)     /* #3B82F6 - primary actions */
  --primary-foreground: hsl(0, 0%, 100%)      /* white - text on primary */
  --secondary:         hsl(222, 30%, 15%)     /* #1A2035 - secondary actions */
  --accent:            hsl(222, 30%, 15%)     /* same as secondary */
  --destructive:       hsl(0, 84%, 60%)       /* #EF4444 - destructive actions */
```

#### Trading-Specific Colors

```
Profit/Loss:
  --profit:            hsl(142, 71%, 45%)     /* #22C55E - profit green */
  --loss:              hsl(0, 84%, 60%)       /* #EF4444 - loss red */
  --breakeven:         hsl(215, 20%, 55%)     /* #7B8BA5 - breakeven gray */

Trendline Grades:
  --grade-aplus:       hsl(38, 92%, 50%)      /* #F59E0B - A+ gold */
  --grade-a:           hsl(217, 91%, 60%)     /* #3B82F6 - A blue */
  --grade-b:           hsl(215, 14%, 45%)     /* #6B7280 - B gray */

Mode Indicators:
  --mode-paper:        hsl(217, 91%, 60%)     /* #3B82F6 - paper blue */
  --mode-live:         hsl(142, 71%, 45%)     /* #22C55E - live green */

Direction:
  --direction-long:    hsl(142, 71%, 45%)     /* green */
  --direction-short:   hsl(0, 84%, 60%)       /* red */

Alert Status:
  --alert-watching:    hsl(215, 20%, 55%)     /* gray */
  --alert-near:        hsl(45, 93%, 47%)      /* #EAB308 - yellow */
  --alert-triggered:   hsl(142, 71%, 45%)     /* green */
```

#### Light Theme

Light theme inverts the background/foreground relationships while maintaining the same semantic colors for trading data (green = profit, red = loss).

```
Background:
  --background:        hsl(0, 0%, 100%)       /* white */
  --card:              hsl(0, 0%, 98%)        /* #FAFAFA */
  --muted:             hsl(210, 40%, 96%)     /* #F1F5F9 */

Foreground:
  --foreground:        hsl(222, 47%, 11%)     /* #0F172A */
  --muted-foreground:  hsl(215, 16%, 47%)     /* #64748B */

Border:
  --border:            hsl(214, 32%, 91%)     /* #E2E8F0 */
```

### 5.3 Typography Scale

Using the system font stack with Inter as the primary web font:

```
Font Family:
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;  /* for prices, code */

Scale:
  text-xs:    12px / 16px (0.75rem)     — labels, captions, timestamps
  text-sm:    14px / 20px (0.875rem)    — body text, table cells, form labels
  text-base:  16px / 24px (1rem)        — default body, descriptions
  text-lg:    18px / 28px (1.125rem)    — section headings, card titles
  text-xl:    20px / 28px (1.25rem)     — page subtitles
  text-2xl:   24px / 32px (1.5rem)      — page titles
  text-3xl:   30px / 36px (1.875rem)    — hero numbers (P&L amount)
  text-4xl:   36px / 40px (2.25rem)     — landing page headings

Font Weights:
  font-normal:   400  — body text
  font-medium:   500  — labels, table headers
  font-semibold: 600  — headings, metric values
  font-bold:     700  — emphasis, P&L amounts

Monospace Usage:
  All prices, dollar amounts, percentages, R-multiples, and numeric metrics use
  --font-mono for proper digit alignment (tabular numbers).
```

### 5.4 Spacing System

Follows Tailwind's default spacing scale (base 4px):

```
p-1:   4px     — tight padding (badge internal)
p-2:   8px     — compact padding (table cells)
p-3:   12px    — default padding (input padding)
p-4:   16px    — card padding (standard)
p-5:   20px    — card padding (comfortable)
p-6:   24px    — section spacing
p-8:   32px    — large section spacing
p-10:  40px    — page padding
p-12:  48px    — major section breaks

Gap:
  gap-2:  8px   — between related items (stat cards, filter chips)
  gap-4:  16px  — between cards in a grid
  gap-6:  24px  — between page sections
  gap-8:  32px  — between major page areas
```

### 5.5 Chart Color Conventions

| Data Type | Color | Hex |
|---|---|---|
| Profit / Gain / Positive | Green | `#22C55E` |
| Loss / Decline / Negative | Red | `#EF4444` |
| Breakeven / Neutral | Gray | `#7B8BA5` |
| Equity Curve (primary) | Blue | `#3B82F6` |
| Equity Curve (secondary/comparison) | Purple | `#8B5CF6` |
| Drawdown Area | Red (30% opacity) | `#EF4444` at 0.3 alpha |
| Volume Bars | Muted foreground (40% opacity) | `#7B8BA5` at 0.4 alpha |
| Stop Loss Level | Red dashed line | `#EF4444` |
| Take Profit Level | Green dashed line | `#22C55E` |
| Entry Marker | Blue vertical dashed line | `#3B82F6` |
| Exit Marker | Purple vertical dashed line | `#8B5CF6` |

**Accessibility note**: Charts that use green/red also include shape or pattern differentiation (e.g., filled vs. hollow circles, solid vs. dashed lines) for color-blind accessibility.

### 5.6 Status Indicators

| Status | Badge Variant | Icon | Color |
|---|---|---|---|
| Paper Mode | Outline badge | TestTube | Blue (`#3B82F6`) |
| Live Mode | Filled badge | Zap | Green (`#22C55E`) |
| Connected | Filled dot | -- | Green (`#22C55E`) |
| Disconnected | Filled dot | -- | Red (`#EF4444`) |
| Error | Filled dot | AlertTriangle | Yellow (`#EAB308`) |
| Grade A+ | Filled badge | -- | Gold (`#F59E0B`) |
| Grade A | Filled badge | -- | Blue (`#3B82F6`) |
| Grade B | Outline badge | -- | Gray (`#6B7280`) |
| Long Direction | Filled chip | ArrowUp | Green (`#22C55E`) |
| Short Direction | Filled chip | ArrowDown | Red (`#EF4444`) |
| Winner | Left border | -- | Green (`#22C55E`) |
| Loser | Left border | -- | Red (`#EF4444`) |
| Auto-classified | Small badge | Bot | Muted (`#7B8BA5`) |
| System Playbook | Small badge | Lock | Muted (`#7B8BA5`) |

### 5.7 Iconography

All icons sourced from Lucide React (consistent with shadcn/ui). Size defaults:

| Context | Size | Usage |
|---|---|---|
| Navigation icons | 20px | Sidebar items |
| Inline icons | 16px | Button icons, table action icons |
| Status dots | 8px | Connection status indicators |
| Hero icons | 24px | Card header icons, empty state illustrations |
| Feature icons | 32px | Landing page feature sections |

### 5.8 Motion & Animation

| Animation | Duration | Easing | Usage |
|---|---|---|---|
| Theme transition | 200ms | ease-in-out | Background/text color on theme toggle |
| Sidebar collapse | 200ms | ease-in-out | Sidebar width change |
| Modal enter | 200ms | ease-out | Dialog/Sheet opening |
| Modal exit | 150ms | ease-in | Dialog/Sheet closing |
| Toast enter | 300ms | spring | Toast sliding in from right |
| Toast exit | 200ms | ease-in | Toast sliding out |
| Skeleton shimmer | 1.5s | linear (infinite) | Loading skeleton pulse |
| Alert pulse | 2s | ease-in-out (infinite) | Near-alert trendline indicator |
| Chart draw | 500ms | ease-out | Initial chart rendering |
| Data transition | 300ms | ease-in-out | Metric value changes |
| Hover state | 150ms | ease | Button/card hover effects |

All animations respect `prefers-reduced-motion` and are disabled when the user's OS requests it.

---

## 6. Dependencies

This PRD (PRD-011) is the presentation layer and depends on all other TrendEdge PRDs:

| Dependency PRD | Dependency Type | What This PRD Consumes |
|---|---|---|
| PRD-001: Infrastructure & DevOps | Platform | Vercel hosting, CI/CD pipeline, environment configuration |
| PRD-002: Database Schema & Data Models | Data | All entity shapes for TypeScript types, API response interfaces |
| PRD-003: Authentication & Authorization | Auth | Login/signup flows, session management, protected routes, role-based UI |
| PRD-004: Trendline Detection Engine | Feature | Trendline data for chart overlays, trendline list, detection configuration UI |
| PRD-005: Trade Execution Pipeline | Feature | Position data, signal queue, order forms, broker connection status |
| PRD-006: Trade Journaling | Feature | Trade table data, trade detail data, enrichment form schema, screenshot storage |
| PRD-007: Playbook System | Feature | Playbook CRUD APIs, playbook metrics, auto-classification rules |
| PRD-008: Performance Analytics | Feature | All 25+ metrics calculations, chart data (equity curve, heatmap, histograms) |
| PRD-009: Notification System | Feature | Notification preferences, notification list, real-time alert delivery |
| PRD-010: AI Features | Feature | Conversational analytics chat API, trade review content, trendline scoring display |

### API Contract Requirements

The frontend depends on the following API contracts from the FastAPI backend:

- **REST endpoints**: Standard RESTful JSON APIs for CRUD operations. OpenAPI spec auto-generated by FastAPI.
- **WebSocket channels**: Documented message types and payload schemas for each real-time channel.
- **Response envelope**: Standardized response format: `{ data: T, meta: { page, total, ... }, error: { code, message, details } }`.
- **Pagination**: Cursor-based pagination for trade lists (large datasets). Offset-based for smaller collections.
- **Error codes**: Standardized error codes mapped to user-facing messages in the frontend.
- **TypeScript types**: Generated from OpenAPI spec using `openapi-typescript` for type-safe API consumption.

---

## 7. Testing Requirements

### 7.1 Component Unit Testing

**Framework**: Jest + React Testing Library

| Metric | Target |
|---|---|
| Component coverage | >80% of exported components |
| Branch coverage | >70% |
| Test execution time | <60 seconds for full suite |

**What to test:**
- All form components: validation, submission, error display.
- Data display components: correct rendering of all data variants (positive P&L, negative P&L, zero).
- State management: Zustand store actions and derived state.
- Loading/error/empty states for all widgets.
- Keyboard shortcut handlers.
- Theme toggle behavior.

**What NOT to test:**
- Third-party library internals (TradingView Lightweight Charts rendering).
- CSS styling (covered by visual regression testing).
- Full page integration (covered by E2E).

### 7.2 End-to-End Testing

**Framework**: Playwright

| Metric | Target |
|---|---|
| Critical path coverage | 100% of user journeys below |
| Test execution time | <5 minutes for full suite |
| Browsers | Chromium, Firefox, WebKit |

**Critical user journeys (E2E tests required):**

1. **Authentication flow**: Sign up, log in, log out, protected route redirect.
2. **Dashboard load**: Navigate to dashboard, verify all widgets render with data.
3. **Trendline interaction**: Select instrument, view chart, click trendline, view detail panel, adjust parameters, apply.
4. **Trade entry**: Open manual trade form, fill fields, verify calculated fields, submit, verify trade appears in journal.
5. **Journal workflow**: View trade table, sort by P&L, filter by instrument, click trade, add conviction rating, add notes, upload screenshot, verify save.
6. **Playbook CRUD**: Create playbook, verify it appears in list, edit name, view detail page, delete.
7. **Analytics filtering**: Navigate to analytics, change date range, change instrument filter, verify charts update.
8. **Paper/Live toggle**: Toggle to live (verify confirmation dialog), toggle back to paper.
9. **Settings**: Update notification preferences, test broker connection, change theme.
10. **Command palette**: Open with Cmd+K, search for a trade, navigate to it.
11. **Responsive**: Run critical journeys at mobile viewport (375px width).

### 7.3 Visual Regression Testing

**Framework**: Playwright screenshot comparison or Chromatic (Storybook)

- Capture screenshots of all major pages and components in both dark and light themes.
- Compare against baseline on every PR.
- Threshold: 0.1% pixel difference tolerance (accounts for anti-aliasing).
- Critical components requiring visual regression: Trade table, equity curve chart, P&L calendar heatmap, trendline chart with overlays, metric cards.

### 7.4 Accessibility Testing

**Framework**: axe-core (via `@axe-core/playwright` for E2E, `jest-axe` for unit)

- Every page must pass axe-core with zero violations at the "critical" and "serious" levels.
- "Moderate" and "minor" violations are logged as warnings and addressed in subsequent sprints.
- Manual testing: Keyboard-only navigation through all critical user journeys. Screen reader testing with VoiceOver (macOS) for the dashboard and trade journal.

### 7.5 Cross-Browser Testing

| Browser | Version | Priority | Testing Level |
|---|---|---|---|
| Chrome | Latest 2 versions | P0 | Full E2E + visual regression |
| Firefox | Latest 2 versions | P0 | Full E2E |
| Safari | Latest 2 versions | P0 | Full E2E |
| Edge | Latest 2 versions | P1 | Smoke test (critical journeys) |
| Mobile Safari (iOS) | Latest | P1 | Responsive smoke test |
| Chrome (Android) | Latest | P1 | Responsive smoke test |

### 7.6 Mobile Responsiveness Testing

- Tested at breakpoints: 375px (iPhone SE), 390px (iPhone 14), 768px (iPad), 1024px (iPad Pro landscape).
- Verified: No horizontal overflow, all interactive elements have minimum 44px touch target, charts are usable with touch gestures.

### 7.7 Performance Testing

**Framework**: Lighthouse CI (via `@lhci/cli`)

- Runs on every PR against a deployed preview environment (Vercel preview).
- Assertions:

```
Performance >= 90
Accessibility >= 90
Best Practices >= 90
SEO >= 90
FCP <= 1500ms
LCP <= 2500ms
TTI <= 3000ms
CLS <= 0.1
```

- Performance budget file (`budget.json`) enforces bundle size limits.
- Alerts on regression: If any metric drops >5 points from the baseline, the PR is flagged.

---

## 8. Security

### 8.1 XSS Prevention

#### FE-SEC-001: Output Encoding

- React's JSX automatically escapes interpolated values, preventing reflected XSS. Never use `dangerouslySetInnerHTML` except for rendering markdown content processed through a sanitizer.
- Markdown rendering (trade notes, AI chat responses) uses `react-markdown` with `rehype-sanitize` to strip dangerous HTML (scripts, iframes, event handlers).
- URL parameters used in API calls are validated against allowlists (instruments, sort fields) rather than passed through directly.

#### FE-SEC-002: Content Security Policy (CSP)

Next.js middleware sets the following CSP headers:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline' https://vercel.live;
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data: https://*.r2.cloudflarestorage.com;
  font-src 'self';
  connect-src 'self' wss://*.trendedge.com https://*.trendedge.com https://*.supabase.co;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
```

Note: `unsafe-eval` is required by some charting libraries in development mode and should be removed in production if possible. `unsafe-inline` for styles is required by Tailwind's runtime.

### 8.2 Input Sanitization

#### FE-SEC-003: Client-Side Input Validation

- All form inputs are validated using Zod schemas before submission.
- Numeric fields (prices, quantities) reject non-numeric input at the input level.
- Text fields (notes, descriptions) are sanitized with DOMPurify before rendering user-generated content.
- File uploads (screenshots) validate MIME type on the client side and again on the server.
- Search queries are parameterized; no raw SQL construction occurs on the frontend.

### 8.3 Authentication Token Handling

#### FE-SEC-004: Token Storage & Transmission

- Auth tokens (JWT) are stored in `httpOnly`, `Secure`, `SameSite=Strict` cookies. Never stored in `localStorage` or `sessionStorage`.
- API routes (Next.js BFF) read the cookie server-side and inject the token into backend API calls. The token is never exposed to client-side JavaScript.
- Token refresh: When a 401 response is received, the BFF attempts a token refresh using the refresh token cookie. If refresh fails, the user is redirected to `/login` with a "Session expired" message.
- Logout: Clears all auth cookies and invalidates the session on the backend.

#### FE-SEC-005: Sensitive Data Handling

- Broker credentials are never stored in the frontend. The broker connection form submits credentials directly to the backend, which encrypts and stores them.
- API keys and secrets are never included in client-side bundles. All secrets are server-side only (environment variables accessed in API routes or server components).
- Source maps are disabled in production builds (`productionBrowserSourceMaps: false` in `next.config.js`).

### 8.4 Additional Security Headers

Set via Next.js middleware or `next.config.js` headers:

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

---

## 9. Phase Mapping

### Phase 1: Core Dashboard (Weeks 7-8)

**Goal**: A functional dashboard showing trendline detection results, trade log, and basic P&L.

| Requirement | ID | Description |
|---|---|---|
| Application Shell | FE-FR-001, FE-FR-002, FE-FR-004, FE-FR-006, FE-FR-007 | Sidebar, header, Paper/Live indicator, loading states, toasts |
| Dashboard Home | FE-FR-008, FE-FR-009, FE-FR-010, FE-FR-011, FE-FR-012 | P&L card, positions widget, trendlines widget, recent trades, quick stats |
| Trendline Chart | FE-FR-013, FE-FR-014, FE-FR-015, FE-FR-017 | Candlestick chart, trendline overlays, trendline list, instrument selector |
| Trade Log | FE-FR-023, FE-FR-024 | Trade table with sorting/pagination, trade detail view (auto-captured data only) |
| Equity Curve | FE-FR-034 | Basic equity curve chart |
| WebSocket | FE-FR-050 | Real-time position and P&L updates |
| Dark Theme | FE-FR-052 | Dark mode implementation (default) |
| Design System | Section 5 (partial) | Color tokens, typography, core shadcn/ui components |

**Excluded from Phase 1**: Journal enrichment, playbooks, full analytics, AI chat, settings, onboarding, landing page, light mode, command palette, keyboard shortcuts, accessibility audit.

**Exit criteria**:
- Dashboard renders with real data from the backend API.
- Trendline chart displays candlesticks and detected trendlines for at least 2 instruments.
- Trade table displays all trades with correct P&L calculations.
- Equity curve chart renders from trade data.
- WebSocket connection delivers real-time position updates.
- Dark mode is the default and only theme.
- FCP < 1.5s on Vercel deployment.

### Phase 2: Analytics & Journaling (Weeks 9-14)

**Goal**: Full analytics dashboard, journal enrichment, playbook management, and screenshot uploads.

| Week | Requirement IDs | Description |
|---|---|---|
| 9-10 | FE-FR-025, FE-FR-026, FE-FR-027, FE-FR-028, FE-FR-029, FE-FR-030 | Journal enrichment form, screenshot upload, trade search, playbook list, playbook detail, playbook CRUD |
| 11-12 | FE-FR-032, FE-FR-033, FE-FR-035, FE-FR-036, FE-FR-037, FE-FR-038, FE-FR-039 | Analytics filter bar, metric cards (all 27 metrics), P&L calendar heatmap, R-multiple histogram, time-based charts, MAE/MFE scatter plots, drawdown chart |
| 13-14 | FE-FR-016, FE-FR-018, FE-FR-019, FE-FR-020, FE-FR-021, FE-FR-022, FE-FR-031, FE-FR-049, FE-FR-058 | Trendline detail panel, detection config, active positions table (full), pending signals queue, manual trade entry, broker status, playbook comparison, AI chat interface, Paper/Live toggle |

**Exit criteria**:
- All 27 metrics display correctly with real trade data.
- P&L calendar heatmap renders with correct green/red color mapping.
- Journal enrichment form saves conviction, emotions, notes, and screenshots.
- Screenshots upload to R2 and display in trade detail view.
- Playbook CRUD fully functional; auto-classification assigns trades.
- AI chat returns meaningful responses with inline charts.
- All analytics charts render within 3 seconds for 1,000+ trades.

### Phase 3: Polish, Onboarding & Marketing (Weeks 17-18)

**Goal**: Onboarding flow, landing page, design polish, accessibility, and remaining features.

| Requirement IDs | Description |
|---|---|
| FE-FR-003, FE-FR-005, FE-FR-053, FE-FR-054 | Breadcrumbs, command palette, keyboard shortcuts, WCAG 2.1 AA compliance |
| FE-FR-040 through FE-FR-046 | Full settings page (profile, preferences, brokers, notifications, detection defaults, risk rules) |
| FE-FR-047 | Onboarding wizard (multi-step) |
| FE-FR-048 | Landing page |
| FE-FR-051 | Full responsive design audit and mobile optimization |
| FE-FR-052 (light mode) | Light mode implementation |
| FE-FR-055 | Complete empty/error/loading state audit for all views |
| FE-NFR-006 | Lighthouse score >90 enforcement |
| Section 7 (testing) | Full test suite: E2E, visual regression, accessibility, cross-browser |
| Section 8 (security) | CSP headers, security audit |

**Exit criteria**:
- New user can complete onboarding wizard end-to-end and begin paper trading.
- Landing page achieves Lighthouse performance >95.
- All pages pass WCAG 2.1 AA audit (axe-core, zero critical/serious violations).
- All keyboard shortcuts functional.
- Command palette searches across pages, instruments, and trades.
- Light mode fully functional and visually polished.
- Cross-browser tests pass on Chrome, Firefox, Safari.
- All E2E critical journeys pass.
- Mobile responsive at 375px, 768px, 1024px breakpoints.

---

## 10. Acceptance Criteria

### 10.1 Global Acceptance Criteria (All Phases)

| ID | Criterion | Verification |
|---|---|---|
| AC-FE-001 | All pages render without JavaScript errors in the browser console | Playwright E2E + manual check |
| AC-FE-002 | All API errors display user-friendly error messages, not raw error responses | Manual review + E2E tests |
| AC-FE-003 | Paper mode is visually distinguishable from Live mode at all times | Visual inspection: blue badge + top border in paper, green in live |
| AC-FE-004 | All monetary values display with correct formatting ($1,234.56) and monospace font | Unit tests + visual inspection |
| AC-FE-005 | All timestamps display in the user's configured timezone | Unit tests with timezone mocking |
| AC-FE-006 | Navigation between all pages completes in <500ms (client-side transition) | Playwright performance measurement |
| AC-FE-007 | No layout shift occurs during page load (CLS < 0.1) | Lighthouse CI |
| AC-FE-008 | The application functions correctly with WebSocket disconnected (graceful degradation) | E2E test: disconnect WebSocket, verify UI shows stale indicators, retries |

### 10.2 Phase 1 Acceptance Criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-FE-P1-001 | Dashboard loads and displays P&L summary, positions, trendlines, recent trades within 3 seconds of authentication | E2E timing measurement |
| AC-FE-P1-002 | Trendline chart renders 300 candles with 5+ trendline overlays without frame drops (<16ms render time) | Browser DevTools performance profiling |
| AC-FE-P1-003 | Clicking a trendline on the chart highlights it and shows correct touch count, slope, and grade | E2E interaction test |
| AC-FE-P1-004 | Instrument selector changes the chart and trendline list within 1 second | E2E test |
| AC-FE-P1-005 | Trade table sorts correctly by all sortable columns (ascending and descending) | Unit tests for sort logic, E2E for UI |
| AC-FE-P1-006 | Trade table pagination works: first page, last page, next, previous, page size change | E2E test |
| AC-FE-P1-007 | Equity curve chart renders correctly with both positive and negative P&L data points | Visual regression test |
| AC-FE-P1-008 | WebSocket position updates appear in the Active Positions widget within 200ms of message receipt | E2E test with WebSocket mock |
| AC-FE-P1-009 | Dark mode renders with correct color tokens throughout all Phase 1 pages | Visual regression test |
| AC-FE-P1-010 | Sidebar collapses and expands, and state persists across page reloads | E2E test |

### 10.3 Phase 2 Acceptance Criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-FE-P2-001 | Journal enrichment form saves conviction (1-5), emotional state tags (max 3), pre/post notes, and screenshots | E2E test: fill form, save, reload, verify data persists |
| AC-FE-P2-002 | Screenshot drag-and-drop uploads file to R2, displays thumbnail, and persists on page reload | E2E test with file fixture |
| AC-FE-P2-003 | Clipboard paste (Cmd+V) of a screenshot creates an upload in the journal enrichment form | Manual test (Playwright cannot simulate clipboard image paste) |
| AC-FE-P2-004 | Trade search returns correct results for full-text queries across notes, instruments, and tags within 500ms | E2E test with seeded data |
| AC-FE-P2-005 | All 27 analytics metrics display correct values matching backend API responses | Unit tests comparing rendered values to mock API data |
| AC-FE-P2-006 | P&L calendar heatmap shows correct green/red coloring: green for profitable days, red for losing days, white/neutral for $0 | Visual regression test with known data |
| AC-FE-P2-007 | Analytics filters (date range, instrument, playbook) update all charts and metrics simultaneously | E2E test: apply filter, verify all components reflect filtered data |
| AC-FE-P2-008 | Playbook CRUD: create a playbook, verify it appears in the list with correct metrics, edit the name, delete it | E2E test |
| AC-FE-P2-009 | Playbook comparison view displays two playbooks side-by-side with overlaid equity curves | E2E test |
| AC-FE-P2-010 | Manual trade entry form calculates risk, R:R, and % of equity correctly in real-time as fields are filled | Unit tests for calculation logic + E2E for UI |
| AC-FE-P2-011 | Paper/Live toggle shows confirmation dialog with checkbox requirement before switching to Live | E2E test |
| AC-FE-P2-012 | AI chat interface sends a query, streams a response, and displays inline charts when the response includes chart data | E2E test with API mock |
| AC-FE-P2-013 | Analytics dashboard renders all charts within 3 seconds for a dataset of 1,000 trades | Performance test with seeded data |

### 10.4 Phase 3 Acceptance Criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-FE-P3-001 | Onboarding wizard: new user completes all steps (profile, broker, playbook, paper mode) and arrives at a populated dashboard | E2E test |
| AC-FE-P3-002 | Onboarding wizard: skipping all optional steps still results in a functional dashboard with default settings | E2E test |
| AC-FE-P3-003 | Landing page achieves Lighthouse Performance score >95 | Lighthouse CI |
| AC-FE-P3-004 | Command palette (Cmd+K) opens within 100ms, searches across pages/instruments/trades, and navigates correctly | E2E test |
| AC-FE-P3-005 | All keyboard shortcuts listed in FE-FR-053 function correctly and are suppressed when focus is in a text input | E2E test for each shortcut |
| AC-FE-P3-006 | All pages pass axe-core accessibility audit with zero "critical" or "serious" violations | Automated axe-core test per page |
| AC-FE-P3-007 | Light mode renders correctly with all color tokens inverted appropriately | Visual regression test (light theme screenshots) |
| AC-FE-P3-008 | All pages render correctly at 375px, 768px, 1024px, and 1536px viewports | Visual regression tests at each breakpoint |
| AC-FE-P3-009 | Settings page: broker connection add/test/remove flow works end-to-end | E2E test |
| AC-FE-P3-010 | Settings page: notification preference changes are saved and reflected in actual notification delivery | E2E test + integration test |
| AC-FE-P3-011 | Full E2E test suite (all 11 critical user journeys) passes on Chrome, Firefox, and Safari | Playwright cross-browser CI |
| AC-FE-P3-012 | No page in the application has a Lighthouse score below 90 in any category | Lighthouse CI sweep of all routes |

### 10.5 Definition of Done (Per Feature)

A feature is considered "Done" when all of the following are satisfied:

1. Code compiles without TypeScript errors (`next build` succeeds).
2. All unit tests pass (`jest --coverage` meets >80% component coverage).
3. Relevant E2E tests pass for the feature's user journey.
4. Visual regression baseline is updated and approved.
5. Accessibility: axe-core returns zero critical/serious violations for the feature's pages.
6. Loading, error, and empty states are implemented and tested.
7. Dark mode renders correctly (visual inspection + screenshot baseline).
8. Responsive at desktop (1280px+) and tablet (768px) breakpoints minimum.
9. Code reviewed and approved by at least one other developer.
10. Deployed to preview environment on Vercel and manually verified.

---

*End of PRD-011: Frontend Dashboard & UI/UX*

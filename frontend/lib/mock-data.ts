import type { Instrument, Trendline, CandleData, DetectionParams, TrendlineAlert } from "@/types/trendline";
import type { PnlSummary, Position, TradeSummary, DashboardStats } from "@/types/dashboard";
import type { Signal, Order, ExecutionPosition, RiskSettings, CircuitBreakerStatus, BrokerStatus } from "@/types/execution";
import type { Trade, TradeStats } from "@/types/journal";

// --- Instruments ---
export const mockInstruments: Instrument[] = [
  { id: "inst-es", symbol: "ES", name: "E-mini S&P 500", exchange: "CME", assetClass: "equity_index", tickSize: 0.25, tickValue: 12.5, contractMonths: "HMUZ", currentContract: "ESH26", isActive: true },
  { id: "inst-nq", symbol: "NQ", name: "E-mini Nasdaq 100", exchange: "CME", assetClass: "equity_index", tickSize: 0.25, tickValue: 5.0, contractMonths: "HMUZ", currentContract: "NQH26", isActive: true },
  { id: "inst-cl", symbol: "CL", name: "Crude Oil", exchange: "NYMEX", assetClass: "energy", tickSize: 0.01, tickValue: 10.0, contractMonths: "FGHJKMNQUVXZ", currentContract: "CLH26", isActive: true },
  { id: "inst-gc", symbol: "GC", name: "Gold", exchange: "COMEX", assetClass: "metals", tickSize: 0.1, tickValue: 10.0, contractMonths: "GJMQVZ", currentContract: "GCJ26", isActive: true },
  { id: "inst-si", symbol: "SI", name: "Silver", exchange: "COMEX", assetClass: "metals", tickSize: 0.005, tickValue: 25.0, contractMonths: "HKNUZ", currentContract: "SIH26", isActive: true },
  { id: "inst-zb", symbol: "ZB", name: "30-Year Treasury Bond", exchange: "CBOT", assetClass: "bonds", tickSize: 0.03125, tickValue: 31.25, contractMonths: "HMUZ", currentContract: "ZBH26", isActive: true },
  { id: "inst-zn", symbol: "ZN", name: "10-Year Treasury Note", exchange: "CBOT", assetClass: "bonds", tickSize: 0.015625, tickValue: 15.625, contractMonths: "HMUZ", currentContract: "ZNH26", isActive: true },
  { id: "inst-6e", symbol: "6E", name: "Euro FX", exchange: "CME", assetClass: "currencies", tickSize: 0.00005, tickValue: 6.25, contractMonths: "HMUZ", currentContract: "6EH26", isActive: true },
];

// --- Sample Trendlines for ES ---
export const mockTrendlines: Trendline[] = [
  {
    id: "tl-1",
    grade: "A+",
    touchCount: 4,
    slopeDegrees: 12.3,
    durationDays: 35,
    spacingQuality: 0.88,
    compositeScore: 8.7,
    status: "active",
    direction: "SUPPORT",
    projectedPrice: 5890.25,
    safetyLinePrice: 5940.0,
    targetPrice: 5980.0,
    anchorPoints: [
      { timestamp: "2026-01-05T00:00:00Z", price: 5820.0 },
      { timestamp: "2026-02-09T00:00:00Z", price: 5890.25 },
    ],
    touchPoints: [
      { timestamp: "2026-01-05T00:00:00Z", price: 5820.0, candle_index: 0 },
      { timestamp: "2026-01-14T00:00:00Z", price: 5838.5, candle_index: 7 },
      { timestamp: "2026-01-24T00:00:00Z", price: 5858.75, candle_index: 15 },
      { timestamp: "2026-02-05T00:00:00Z", price: 5882.0, candle_index: 23 },
    ],
    lastTouchAt: "2026-02-05T00:00:00Z",
    createdAt: "2026-01-06T00:00:00Z",
  },
  {
    id: "tl-2",
    grade: "A",
    touchCount: 3,
    slopeDegrees: -8.5,
    durationDays: 28,
    spacingQuality: 0.76,
    compositeScore: 6.4,
    status: "active",
    direction: "RESISTANCE",
    projectedPrice: 5960.0,
    safetyLinePrice: 5910.0,
    targetPrice: 5860.0,
    anchorPoints: [
      { timestamp: "2026-01-10T00:00:00Z", price: 5985.0 },
      { timestamp: "2026-02-07T00:00:00Z", price: 5960.0 },
    ],
    touchPoints: [
      { timestamp: "2026-01-10T00:00:00Z", price: 5985.0, candle_index: 3 },
      { timestamp: "2026-01-22T00:00:00Z", price: 5975.5, candle_index: 13 },
      { timestamp: "2026-02-04T00:00:00Z", price: 5963.25, candle_index: 22 },
    ],
    lastTouchAt: "2026-02-04T00:00:00Z",
    createdAt: "2026-01-11T00:00:00Z",
  },
  {
    id: "tl-3",
    grade: "B",
    touchCount: 3,
    slopeDegrees: 22.1,
    durationDays: 18,
    spacingQuality: 0.62,
    compositeScore: 4.2,
    status: "qualifying",
    direction: "SUPPORT",
    projectedPrice: 5870.0,
    safetyLinePrice: null,
    targetPrice: null,
    anchorPoints: [
      { timestamp: "2026-01-20T00:00:00Z", price: 5840.0 },
      { timestamp: "2026-02-07T00:00:00Z", price: 5870.0 },
    ],
    touchPoints: [
      { timestamp: "2026-01-20T00:00:00Z", price: 5840.0, candle_index: 11 },
      { timestamp: "2026-01-28T00:00:00Z", price: 5852.5, candle_index: 17 },
      { timestamp: "2026-02-06T00:00:00Z", price: 5868.25, candle_index: 24 },
    ],
    lastTouchAt: "2026-02-06T00:00:00Z",
    createdAt: "2026-01-21T00:00:00Z",
  },
  {
    id: "tl-4",
    grade: "A+",
    touchCount: 5,
    slopeDegrees: -5.2,
    durationDays: 42,
    spacingQuality: 0.91,
    compositeScore: 9.3,
    status: "active",
    direction: "RESISTANCE",
    projectedPrice: 5950.0,
    safetyLinePrice: 5900.0,
    targetPrice: 5840.0,
    anchorPoints: [
      { timestamp: "2025-12-28T00:00:00Z", price: 5990.0 },
      { timestamp: "2026-02-08T00:00:00Z", price: 5950.0 },
    ],
    touchPoints: [
      { timestamp: "2025-12-28T00:00:00Z", price: 5990.0, candle_index: 0 },
      { timestamp: "2026-01-06T00:00:00Z", price: 5982.5, candle_index: 5 },
      { timestamp: "2026-01-16T00:00:00Z", price: 5973.0, candle_index: 13 },
      { timestamp: "2026-01-27T00:00:00Z", price: 5962.75, candle_index: 20 },
      { timestamp: "2026-02-06T00:00:00Z", price: 5952.25, candle_index: 28 },
    ],
    lastTouchAt: "2026-02-06T00:00:00Z",
    createdAt: "2025-12-29T00:00:00Z",
  },
  {
    id: "tl-5",
    grade: null,
    touchCount: 2,
    slopeDegrees: 15.8,
    durationDays: 10,
    spacingQuality: null,
    compositeScore: null,
    status: "detected",
    direction: "SUPPORT",
    projectedPrice: 5855.0,
    safetyLinePrice: null,
    targetPrice: null,
    anchorPoints: [
      { timestamp: "2026-01-30T00:00:00Z", price: 5845.0 },
      { timestamp: "2026-02-09T00:00:00Z", price: 5855.0 },
    ],
    touchPoints: [
      { timestamp: "2026-01-30T00:00:00Z", price: 5845.0, candle_index: 19 },
      { timestamp: "2026-02-09T00:00:00Z", price: 5855.0, candle_index: 27 },
    ],
    lastTouchAt: "2026-02-09T00:00:00Z",
    createdAt: "2026-02-10T00:00:00Z",
  },
];

// --- 300 candles of ES mock OHLC data ---
function generateCandles(count: number): CandleData[] {
  const candles: CandleData[] = [];
  let price = 5800;
  const baseTime = new Date("2025-11-01T00:00:00Z").getTime() / 1000;
  const daySeconds = 86400;

  for (let i = 0; i < count; i++) {
    const change = (Math.random() - 0.48) * 20;
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * 15;
    const low = Math.min(open, close) - Math.random() * 15;
    price = close;

    candles.push({
      time: baseTime + i * daySeconds,
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume: Math.floor(500000 + Math.random() * 1500000),
    });
  }
  return candles;
}

export const mockCandles: CandleData[] = generateCandles(300);

// --- Dashboard Data ---
export const mockPnlSummary: PnlSummary = {
  todayPnl: 1250.0,
  weekPnl: 3480.75,
  monthPnl: 8920.5,
  todayR: 1.8,
  weekR: 4.2,
  monthR: 12.6,
  isPaper: true,
};

export const mockDashboardStats: DashboardStats = {
  winRate: 0.62,
  avgR: 1.85,
  totalTrades: 47,
  openPositions: 2,
  activeTrendlines: 8,
  winRateHistory: [0.55, 0.58, 0.60, 0.57, 0.63, 0.61, 0.62],
  avgRHistory: [1.5, 1.6, 1.7, 1.9, 1.8, 2.0, 1.85],
};

export const mockPositions: Position[] = [
  {
    id: "pos-1",
    instrumentId: "inst-es",
    symbol: "ES",
    direction: "long",
    entryPrice: 5882.25,
    currentPrice: 5910.5,
    unrealizedPnl: 1412.5,
    rMultiple: 1.4,
    quantity: 2,
    enteredAt: "2026-02-10T14:30:00Z",
  },
  {
    id: "pos-2",
    instrumentId: "inst-cl",
    symbol: "CL",
    direction: "short",
    entryPrice: 78.45,
    currentPrice: 77.82,
    unrealizedPnl: 630.0,
    rMultiple: 0.9,
    quantity: 1,
    enteredAt: "2026-02-11T09:15:00Z",
  },
];

export const mockRecentTrades: TradeSummary[] = [
  { id: "trade-1", instrumentId: "inst-nq", symbol: "NQ", direction: "long", pnl: 2150.0, rMultiple: 2.3, closedAt: "2026-02-09T15:45:00Z" },
  { id: "trade-2", instrumentId: "inst-es", symbol: "ES", direction: "short", pnl: -625.0, rMultiple: -0.8, closedAt: "2026-02-08T14:20:00Z" },
  { id: "trade-3", instrumentId: "inst-gc", symbol: "GC", direction: "long", pnl: 890.0, rMultiple: 1.2, closedAt: "2026-02-07T16:00:00Z" },
  { id: "trade-4", instrumentId: "inst-es", symbol: "ES", direction: "long", pnl: 1875.0, rMultiple: 2.1, closedAt: "2026-02-06T15:30:00Z" },
  { id: "trade-5", instrumentId: "inst-cl", symbol: "CL", direction: "short", pnl: -340.0, rMultiple: -0.5, closedAt: "2026-02-05T14:10:00Z" },
];

// --- Trendline Alerts ---
export const mockAlerts: TrendlineAlert[] = [
  {
    id: "alert-1",
    trendlineId: "tl-1",
    alertType: "touch",
    direction: "SUPPORT",
    payload: { price: 5890.25, distance_pct: 0.3 },
    channelsSent: ["email"],
    acknowledged: false,
    createdAt: "2026-02-11T10:30:00Z",
  },
  {
    id: "alert-2",
    trendlineId: "tl-4",
    alertType: "break",
    direction: "RESISTANCE",
    payload: { price: 5952.0, breakType: "close_above" },
    channelsSent: ["email", "telegram"],
    acknowledged: true,
    createdAt: "2026-02-10T15:20:00Z",
  },
];

// --- Default Detection Params ---
export const mockDetectionParams: DetectionParams = {
  minTouchCount: 3,
  minCandleSpacing: 6,
  maxSlopeDegrees: 45,
  minDurationDays: 21,
  touchToleranceAtr: 0.5,
  pivotNBarLookback: 5,
  maxLinesPerInstrument: 10,
  presetName: "default",
};

// --- Execution Mock Data ---
export const mockExecutionPositions: ExecutionPosition[] = [
  { id: "pos-1", signalId: "sig-1", instrumentSymbol: "MNQ", direction: "LONG", entryPrice: 21450.25, currentPrice: 21520.50, stopLossPrice: 21380.00, takeProfitPrice: 21590.00, quantity: 2, unrealizedPnl: 70.25, realizedPnl: null, netPnl: null, rMultiple: 1.0, mae: -35.50, mfe: 82.75, status: "OPEN", exitReason: null, enteredAt: "2026-02-12T09:35:00Z", closedAt: null, createdAt: "2026-02-12T09:35:00Z" },
  { id: "pos-2", signalId: "sig-3", instrumentSymbol: "MES", direction: "SHORT", entryPrice: 6050.75, currentPrice: 6035.25, stopLossPrice: 6075.00, takeProfitPrice: 6000.00, quantity: 1, unrealizedPnl: 77.50, realizedPnl: null, netPnl: null, rMultiple: 0.64, mae: -12.25, mfe: 95.50, status: "OPEN", exitReason: null, enteredAt: "2026-02-11T14:20:00Z", closedAt: null, createdAt: "2026-02-11T14:20:00Z" },
  { id: "pos-3", signalId: "sig-5", instrumentSymbol: "MCL", direction: "LONG", entryPrice: 72.45, currentPrice: 73.10, stopLossPrice: 71.80, takeProfitPrice: 74.00, quantity: 1, unrealizedPnl: 65.00, realizedPnl: null, netPnl: null, rMultiple: 1.0, mae: -15.00, mfe: 78.00, status: "OPEN", exitReason: null, enteredAt: "2026-02-10T10:00:00Z", closedAt: null, createdAt: "2026-02-10T10:00:00Z" },
  { id: "pos-4", signalId: null, instrumentSymbol: "MGC", direction: "SHORT", entryPrice: 2920.00, currentPrice: 2905.50, stopLossPrice: 2945.00, takeProfitPrice: 2870.00, quantity: 2, unrealizedPnl: 29.00, realizedPnl: null, netPnl: null, rMultiple: 0.58, mae: -8.00, mfe: 35.00, status: "OPEN", exitReason: null, enteredAt: "2026-02-12T08:15:00Z", closedAt: null, createdAt: "2026-02-12T08:15:00Z" },
  { id: "pos-5", signalId: "sig-7", instrumentSymbol: "MYM", direction: "LONG", entryPrice: 44150.00, currentPrice: 44280.00, stopLossPrice: 44050.00, takeProfitPrice: 44400.00, quantity: 1, unrealizedPnl: 65.00, realizedPnl: null, netPnl: null, rMultiple: 1.3, mae: -22.00, mfe: 72.00, status: "OPEN", exitReason: null, enteredAt: "2026-02-11T09:45:00Z", closedAt: null, createdAt: "2026-02-11T09:45:00Z" },
];

export const mockSignals: Signal[] = [
  { id: "sig-pending-1", source: "INTERNAL", status: "RISK_PASSED", instrumentSymbol: "MNQ", direction: "LONG", entryType: "MARKET", entryPrice: 21550.00, stopLossPrice: 21480.00, takeProfitPrice: 21690.00, quantity: 2, trendlineId: "tl-1", trendlineGrade: "A+", enrichmentData: { riskRewardRatio: 2.0, riskPerContract: 35.00 }, rejectionReason: null, riskChecks: [{ checkName: "MAX_POSITION_SIZE", result: "PASS", actualValue: 2, thresholdValue: 5, details: null }], createdAt: "2026-02-12T10:15:00Z", updatedAt: "2026-02-12T10:15:00Z" },
  { id: "sig-pending-2", source: "WEBHOOK", status: "VALIDATED", instrumentSymbol: "MES", direction: "SHORT", entryType: "LIMIT", entryPrice: 6080.00, stopLossPrice: 6105.00, takeProfitPrice: 6030.00, quantity: null, trendlineId: null, trendlineGrade: null, enrichmentData: null, rejectionReason: null, riskChecks: null, createdAt: "2026-02-12T10:20:00Z", updatedAt: "2026-02-12T10:20:00Z" },
  { id: "sig-pending-3", source: "MANUAL", status: "RECEIVED", instrumentSymbol: "MCL", direction: "LONG", entryType: "MARKET", entryPrice: 73.50, stopLossPrice: 72.80, takeProfitPrice: 75.00, quantity: 1, trendlineId: null, trendlineGrade: null, enrichmentData: null, rejectionReason: null, riskChecks: null, createdAt: "2026-02-12T10:25:00Z", updatedAt: "2026-02-12T10:25:00Z" },
];

export const mockOrders: Order[] = [
  { id: "ord-1", signalId: "sig-1", bracketGroupId: "bg-1", instrumentSymbol: "MNQ", side: "BUY", orderType: "MARKET", bracketRole: "ENTRY", price: null, quantity: 2, timeInForce: "GTC", status: "FILLED", brokerOrderId: "PAPER-ABC123", fillPrice: 21450.25, filledQuantity: 2, commission: 1.24, slippageTicks: 1, submittedAt: "2026-02-12T09:35:00Z", filledAt: "2026-02-12T09:35:00Z", createdAt: "2026-02-12T09:35:00Z" },
  { id: "ord-2", signalId: "sig-1", bracketGroupId: "bg-1", instrumentSymbol: "MNQ", side: "SELL", orderType: "STOP", bracketRole: "STOP_LOSS", price: 21380.00, quantity: 2, timeInForce: "GTC", status: "SUBMITTED", brokerOrderId: "PAPER-ABC124", fillPrice: null, filledQuantity: null, commission: null, slippageTicks: null, submittedAt: "2026-02-12T09:35:00Z", filledAt: null, createdAt: "2026-02-12T09:35:00Z" },
  { id: "ord-3", signalId: "sig-1", bracketGroupId: "bg-1", instrumentSymbol: "MNQ", side: "SELL", orderType: "LIMIT", bracketRole: "TAKE_PROFIT", price: 21590.00, quantity: 2, timeInForce: "GTC", status: "SUBMITTED", brokerOrderId: "PAPER-ABC125", fillPrice: null, filledQuantity: null, commission: null, slippageTicks: null, submittedAt: "2026-02-12T09:35:00Z", filledAt: null, createdAt: "2026-02-12T09:35:00Z" },
  { id: "ord-4", signalId: "sig-3", bracketGroupId: "bg-2", instrumentSymbol: "MES", side: "SELL", orderType: "MARKET", bracketRole: "ENTRY", price: null, quantity: 1, timeInForce: "GTC", status: "FILLED", brokerOrderId: "PAPER-DEF123", fillPrice: 6050.75, filledQuantity: 1, commission: 0.62, slippageTicks: 1, submittedAt: "2026-02-11T14:20:00Z", filledAt: "2026-02-11T14:20:00Z", createdAt: "2026-02-11T14:20:00Z" },
  { id: "ord-5", signalId: "sig-3", bracketGroupId: "bg-2", instrumentSymbol: "MES", side: "BUY", orderType: "STOP", bracketRole: "STOP_LOSS", price: 6075.00, quantity: 1, timeInForce: "GTC", status: "SUBMITTED", brokerOrderId: "PAPER-DEF124", fillPrice: null, filledQuantity: null, commission: null, slippageTicks: null, submittedAt: "2026-02-11T14:20:00Z", filledAt: null, createdAt: "2026-02-11T14:20:00Z" },
  { id: "ord-6", signalId: "sig-3", bracketGroupId: "bg-2", instrumentSymbol: "MES", side: "BUY", orderType: "LIMIT", bracketRole: "TAKE_PROFIT", price: 6000.00, quantity: 1, timeInForce: "GTC", status: "SUBMITTED", brokerOrderId: "PAPER-DEF125", fillPrice: null, filledQuantity: null, commission: null, slippageTicks: null, submittedAt: "2026-02-11T14:20:00Z", filledAt: null, createdAt: "2026-02-11T14:20:00Z" },
];

export const mockRiskSettings: RiskSettings = {
  maxPositionSizeMicro: 2,
  maxPositionSizeFull: 1,
  dailyLossLimit: 500,
  maxConcurrentPositions: 3,
  minRiskReward: 2.0,
  correlationLimit: 0.70,
  maxSingleTradeRisk: 200,
  tradingHoursMode: "RTH",
  stalenessMinutes: 5,
  paperSlippageTicks: 1,
  circuitBreakerThreshold: 3,
  autoFlattenLossLimit: null,
  isPaperMode: true,
  updatedAt: "2026-02-10T00:00:00Z",
};

export const mockCircuitBreaker: CircuitBreakerStatus = {
  state: "CLOSED",
  consecutiveLosses: 1,
  threshold: 3,
  lastTrippedAt: null,
  queuedSignals: 0,
};

export const mockBrokerStatus: BrokerStatus = {
  connected: true,
  brokerType: "paper",
  accountId: "PAPER-demo",
  isPaper: true,
  lastConnected: "2026-02-12T08:00:00Z",
};

// --- Journal Mock Data ---
function generateMockTrades(count: number): Trade[] {
  const instruments = ["MNQ", "MES", "MCL", "MGC", "MYM"];
  const directions: Array<"LONG" | "SHORT"> = ["LONG", "SHORT"];
  const exitReasons = ["STOP_LOSS", "TAKE_PROFIT", "MANUAL"];
  const emotions = ["calm", "confident", "anxious", "fomo", null];
  const qualities = ["textbook", "acceptable", "forced", null];
  const trades: Trade[] = [];

  for (let i = 0; i < count; i++) {
    const dir = directions[i % 2];
    const instrument = instruments[i % instruments.length];
    const isWin = i % 3 !== 0;
    const pnl = isWin ? (50 + (i * 37) % 400) : -(30 + (i * 23) % 250);
    const r = isWin ? (0.5 + (i * 17) % 300 / 100) : -(0.3 + (i * 13) % 150 / 100);
    const baseDate = new Date("2026-02-12T00:00:00Z");
    baseDate.setDate(baseDate.getDate() - i);

    trades.push({
      id: `trade-${i + 1}`,
      signalId: i % 3 === 0 ? null : `sig-closed-${i}`,
      instrumentSymbol: instrument,
      direction: dir,
      entryPrice: 20000 + (i * 127) % 2000,
      exitPrice: 20000 + (i * 139) % 2000,
      quantity: 1 + (i % 3),
      realizedPnl: Math.round(pnl * 100) / 100,
      netPnl: Math.round((pnl - 1.24) * 100) / 100,
      rMultiple: Math.round(r * 100) / 100,
      mae: -(5 + (i * 11) % 50),
      mfe: 10 + (i * 7) % 80,
      exitReason: exitReasons[i % 3],
      enteredAt: new Date(baseDate.getTime() - 3600000).toISOString(),
      closedAt: baseDate.toISOString(),
      rating: i % 4 !== 0 ? 1 + (i % 5) : null,
      emotionalState: emotions[i % emotions.length],
      setupQuality: qualities[i % qualities.length],
      notes: i % 4 === 0 ? "Clean setup, followed the plan." : null,
      screenshots: [],
      tags: i % 3 === 0 ? ["trendline-break", "A+"] : [],
      playbook: i % 2 === 0 ? "Trendline Break" : null,
    });
  }
  return trades;
}

export const mockTrades: Trade[] = generateMockTrades(50);

export const mockTradeStats: TradeStats = {
  totalTrades: 50,
  winRate: 0.62,
  avgR: 1.45,
  totalPnl: 4250.75,
  bestTrade: 850.00,
  worstTrade: -380.00,
  avgWin: 225.50,
  avgLoss: -145.30,
  profitFactor: 2.15,
};

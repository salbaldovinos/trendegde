export type SignalSource = "INTERNAL" | "WEBHOOK" | "MANUAL";
export type SignalStatus =
  | "RECEIVED"
  | "VALIDATED"
  | "ENRICHED"
  | "RISK_PASSED"
  | "EXECUTING"
  | "FILLED"
  | "REJECTED"
  | "CANCELLED"
  | "EXPIRED";

export interface Signal {
  id: string;
  source: SignalSource;
  status: SignalStatus;
  instrumentSymbol: string;
  direction: "LONG" | "SHORT";
  entryType: "MARKET" | "LIMIT";
  entryPrice: number;
  stopLossPrice: number | null;
  takeProfitPrice: number | null;
  quantity: number | null;
  trendlineId: string | null;
  trendlineGrade: string | null;
  enrichmentData: Record<string, unknown> | null;
  rejectionReason: string | null;
  riskChecks: RiskCheck[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface RiskCheck {
  checkName: string;
  result: "PASS" | "FAIL" | "WARN" | "SKIP";
  actualValue: number | null;
  thresholdValue: number | null;
  details: Record<string, unknown> | null;
}

export type OrderStatus =
  | "CONSTRUCTED"
  | "SUBMITTED"
  | "PARTIAL_FILL"
  | "FILLED"
  | "CANCELLED"
  | "REJECTED";
export type BracketRole = "ENTRY" | "STOP_LOSS" | "TAKE_PROFIT";

export interface Order {
  id: string;
  signalId: string | null;
  bracketGroupId: string;
  instrumentSymbol: string;
  side: "BUY" | "SELL";
  orderType: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
  bracketRole: BracketRole;
  price: number | null;
  quantity: number;
  timeInForce: string;
  status: OrderStatus;
  brokerOrderId: string | null;
  fillPrice: number | null;
  filledQuantity: number | null;
  commission: number | null;
  slippageTicks: number | null;
  submittedAt: string | null;
  filledAt: string | null;
  createdAt: string;
}

export interface ExecutionPosition {
  id: string;
  signalId: string | null;
  instrumentSymbol: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  currentPrice: number | null;
  stopLossPrice: number | null;
  takeProfitPrice: number | null;
  quantity: number;
  unrealizedPnl: number;
  realizedPnl: number | null;
  netPnl: number | null;
  rMultiple: number | null;
  mae: number | null;
  mfe: number | null;
  status: "OPEN" | "CLOSED";
  exitReason: string | null;
  enteredAt: string;
  closedAt: string | null;
  createdAt: string;
}

export interface RiskSettings {
  maxPositionSizeMicro: number;
  maxPositionSizeFull: number;
  dailyLossLimit: number;
  maxConcurrentPositions: number;
  minRiskReward: number;
  correlationLimit: number;
  maxSingleTradeRisk: number;
  tradingHoursMode: "RTH" | "ETH" | "24H";
  stalenessMinutes: number;
  paperSlippageTicks: number;
  circuitBreakerThreshold: number;
  autoFlattenLossLimit: number | null;
  isPaperMode: boolean;
  updatedAt: string;
}

export interface CircuitBreakerStatus {
  state: "CLOSED" | "TRIPPED";
  consecutiveLosses: number;
  threshold: number;
  lastTrippedAt: string | null;
  queuedSignals: number;
}

export interface BrokerStatus {
  connected: boolean;
  brokerType: string;
  accountId: string | null;
  isPaper: boolean;
  lastConnected: string | null;
}

export interface ManualTradeFormData {
  instrumentSymbol: string;
  direction: "LONG" | "SHORT";
  entryType: "MARKET" | "LIMIT";
  entryPrice: number;
  stopLossPrice: number | null;
  takeProfitPrice: number | null;
  quantity: number | null;
  notes: string;
}

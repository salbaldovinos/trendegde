export interface PnlSummary {
  todayPnl: number;
  weekPnl: number;
  monthPnl: number;
  todayR: number;
  weekR: number;
  monthR: number;
  isPaper: boolean;
}

export interface Position {
  id: string;
  instrumentId: string;
  symbol: string;
  direction: "long" | "short";
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  rMultiple: number;
  quantity: number;
  enteredAt: string;
}

export interface TradeSummary {
  id: string;
  instrumentId: string;
  symbol: string;
  direction: "long" | "short";
  pnl: number;
  rMultiple: number;
  closedAt: string;
}

export interface DashboardStats {
  winRate: number;
  avgR: number;
  totalTrades: number;
  openPositions: number;
  activeTrendlines: number;
  winRateHistory: number[];
  avgRHistory: number[];
}

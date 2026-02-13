export interface Trade {
  id: string;
  signalId: string | null;
  instrumentSymbol: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  realizedPnl: number;
  netPnl: number;
  rMultiple: number;
  mae: number | null;
  mfe: number | null;
  exitReason: string;
  enteredAt: string;
  closedAt: string;
  rating: number | null;
  emotionalState: string | null;
  setupQuality: string | null;
  notes: string | null;
  screenshots: string[];
  tags: string[];
  playbook: string | null;
}

export interface TradeFilter {
  search: string;
  dateFrom: string | null;
  dateTo: string | null;
  instruments: string[];
  direction: "LONG" | "SHORT" | null;
  minR: number | null;
  maxR: number | null;
  exitReasons: string[];
  playbook: string | null;
}

export interface TradeStats {
  totalTrades: number;
  winRate: number;
  avgR: number;
  totalPnl: number;
  bestTrade: number;
  worstTrade: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
}

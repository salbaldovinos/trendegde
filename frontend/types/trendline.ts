export type Timeframe = "1H" | "4H" | "1D" | "1W";

export type TrendlineGrade = "A+" | "A" | "B";

export type TrendlineStatus =
  | "detected"
  | "qualifying"
  | "active"
  | "traded"
  | "invalidated"
  | "expired";

export type TrendlineDirection = "SUPPORT" | "RESISTANCE";

export type AlertType = "break" | "touch" | "promotion" | "invalidation";

export interface AnchorPoint {
  timestamp: string;
  price: number;
}

export interface TouchPoint {
  timestamp: string;
  price: number;
  candle_index?: number;
}

export interface Trendline {
  id: string;
  grade: TrendlineGrade | null;
  touchCount: number;
  slopeDegrees: number;
  durationDays: number | null;
  spacingQuality: number | null;
  compositeScore: number | null;
  status: TrendlineStatus;
  direction: TrendlineDirection;
  projectedPrice: number | null;
  safetyLinePrice: number | null;
  targetPrice: number | null;
  anchorPoints: AnchorPoint[];
  touchPoints: TouchPoint[];
  lastTouchAt: string | null;
  createdAt: string;
}

export interface Instrument {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  assetClass: string;
  tickSize: number;
  tickValue: number;
  contractMonths: string;
  currentContract: string | null;
  isActive: boolean;
}

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface DetectionParams {
  minTouchCount: number;
  minCandleSpacing: number;
  maxSlopeDegrees: number;
  minDurationDays: number;
  touchToleranceAtr: number;
  pivotNBarLookback: number;
  maxLinesPerInstrument: number;
  presetName: string | null;
}

export interface TrendlineAlert {
  id: string;
  trendlineId: string;
  alertType: AlertType;
  direction: TrendlineDirection;
  payload: Record<string, unknown>;
  channelsSent: string[];
  acknowledged: boolean;
  createdAt: string;
}

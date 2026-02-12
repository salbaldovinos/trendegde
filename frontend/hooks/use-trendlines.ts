import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api-client";
import {
  mockInstruments,
  mockTrendlines,
  mockCandles,
  mockAlerts,
  mockDetectionParams,
} from "@/lib/mock-data";
import type {
  Instrument,
  Trendline,
  CandleData,
  TrendlineAlert,
  DetectionParams,
  Timeframe,
} from "@/types/trendline";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export function useInstruments() {
  return useQuery({
    queryKey: ["instruments"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockInstruments)
        : apiGet<Instrument[]>("/instruments"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTrendlines(instrumentId: string | null, timeframe: Timeframe) {
  return useQuery({
    queryKey: ["trendlines", instrumentId, timeframe],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockTrendlines)
        : apiGet<Trendline[]>(`/trendlines?instrument_id=${instrumentId}&timeframe=${timeframe}`),
    enabled: !!instrumentId,
    staleTime: 30 * 1000,
  });
}

export function useCandles(instrumentId: string | null, timeframe: Timeframe) {
  return useQuery({
    queryKey: ["candles", instrumentId, timeframe],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockCandles)
        : apiGet<CandleData[]>(`/instruments/${instrumentId}/candles?timeframe=${timeframe}`),
    enabled: !!instrumentId,
    staleTime: 30 * 1000,
  });
}

export function useTrendlineAlerts() {
  return useQuery({
    queryKey: ["trendline-alerts"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockAlerts)
        : apiGet<TrendlineAlert[]>("/alerts"),
    staleTime: 30 * 1000,
  });
}

export function useDetectionParams() {
  return useQuery({
    queryKey: ["detection-params"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockDetectionParams)
        : apiGet<DetectionParams>("/detection/config"),
    staleTime: 5 * 60 * 1000,
  });
}

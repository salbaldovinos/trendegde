import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api-client";
import { mockTrades, mockTradeStats } from "@/lib/mock-data";
import type { Trade, TradeFilter, TradeStats } from "@/types/journal";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export function useTrades(filters?: TradeFilter) {
  return useQuery({
    queryKey: ["trades", filters],
    queryFn: () => {
      if (useMocks) {
        let trades = [...mockTrades];
        if (filters) {
          if (filters.search) {
            const q = filters.search.toLowerCase();
            trades = trades.filter(
              (t) =>
                t.instrumentSymbol.toLowerCase().includes(q) ||
                t.notes?.toLowerCase().includes(q) ||
                t.tags.some((tag) => tag.toLowerCase().includes(q))
            );
          }
          if (filters.direction) {
            trades = trades.filter((t) => t.direction === filters.direction);
          }
          if (filters.instruments.length > 0) {
            trades = trades.filter((t) =>
              filters.instruments.includes(t.instrumentSymbol)
            );
          }
          if (filters.dateFrom) {
            trades = trades.filter((t) => t.closedAt >= filters.dateFrom!);
          }
          if (filters.dateTo) {
            trades = trades.filter((t) => t.closedAt <= filters.dateTo!);
          }
          if (filters.minR !== null) {
            trades = trades.filter((t) => t.rMultiple >= filters.minR!);
          }
          if (filters.maxR !== null) {
            trades = trades.filter((t) => t.rMultiple <= filters.maxR!);
          }
        }
        return Promise.resolve(trades);
      }
      const params = new URLSearchParams();
      if (filters?.search) params.set("search", filters.search);
      if (filters?.direction) params.set("direction", filters.direction);
      if (filters?.dateFrom) params.set("date_from", filters.dateFrom);
      if (filters?.dateTo) params.set("date_to", filters.dateTo);
      if (filters?.instruments.length)
        params.set("instruments", filters.instruments.join(","));
      const qs = params.toString();
      return apiGet<Trade[]>(`/trades${qs ? `?${qs}` : ""}`);
    },
    staleTime: 30 * 1000,
  });
}

export function useTrade(tradeId: string) {
  return useQuery({
    queryKey: ["trade", tradeId],
    queryFn: () => {
      if (useMocks) {
        const trade = mockTrades.find((t) => t.id === tradeId);
        return Promise.resolve(trade ?? null);
      }
      return apiGet<Trade>(`/trades/${tradeId}`);
    },
    enabled: !!tradeId,
  });
}

export function useTradeStats(filters?: TradeFilter) {
  return useQuery({
    queryKey: ["trade-stats", filters],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockTradeStats)
        : apiGet<TradeStats>("/trades/stats"),
    staleTime: 60 * 1000,
  });
}

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api-client";
import {
  mockPnlSummary,
  mockDashboardStats,
  mockPositions,
  mockRecentTrades,
} from "@/lib/mock-data";
import type { PnlSummary, Position, TradeSummary, DashboardStats } from "@/types/dashboard";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export function usePnlSummary() {
  return useQuery({
    queryKey: ["pnl-summary"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockPnlSummary)
        : apiGet<PnlSummary>("/dashboard/pnl"),
    staleTime: 30 * 1000,
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockDashboardStats)
        : apiGet<DashboardStats>("/dashboard/stats"),
    staleTime: 60 * 1000,
  });
}

export function usePositions() {
  return useQuery({
    queryKey: ["positions"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockPositions)
        : apiGet<Position[]>("/positions"),
    staleTime: 15 * 1000,
  });
}

export function useRecentTrades() {
  return useQuery({
    queryKey: ["recent-trades"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockRecentTrades)
        : apiGet<TradeSummary[]>("/trades/recent"),
    staleTime: 60 * 1000,
  });
}

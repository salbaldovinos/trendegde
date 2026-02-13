"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TradeSearchFilters } from "./trade-search-filters";
import { TradeTable } from "./trade-table";
import { useTrades, useTradeStats } from "@/hooks/use-journal";
import { formatCurrency, formatPercent, formatR, formatPnl } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { TradeFilter } from "@/types/journal";

const defaultFilters: TradeFilter = {
  search: "",
  dateFrom: null,
  dateTo: null,
  instruments: [],
  direction: null,
  minR: null,
  maxR: null,
  exitReasons: [],
  playbook: null,
};

function StatsBar() {
  const { data: stats, isLoading } = useTradeStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-4 sm:grid-cols-5 lg:grid-cols-9">
        {Array.from({ length: 9 }).map((_, i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const items = [
    { label: "Total Trades", value: stats.totalTrades.toString() },
    {
      label: "Win Rate",
      value: formatPercent(stats.winRate),
      color: stats.winRate >= 0.5 ? "text-profit" : "text-loss",
    },
    {
      label: "Avg R",
      value: formatR(stats.avgR),
      color: stats.avgR >= 0 ? "text-profit" : "text-loss",
    },
    {
      label: "Total P&L",
      value: formatPnl(stats.totalPnl),
      color: stats.totalPnl >= 0 ? "text-profit" : "text-loss",
    },
    {
      label: "Best Trade",
      value: formatCurrency(stats.bestTrade),
      color: "text-profit",
    },
    {
      label: "Worst Trade",
      value: formatCurrency(stats.worstTrade),
      color: "text-loss",
    },
    {
      label: "Avg Win",
      value: formatCurrency(stats.avgWin),
      color: "text-profit",
    },
    {
      label: "Avg Loss",
      value: formatCurrency(stats.avgLoss),
      color: "text-loss",
    },
    {
      label: "Profit Factor",
      value: stats.profitFactor.toFixed(2),
      color: stats.profitFactor >= 1 ? "text-profit" : "text-loss",
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-4 sm:grid-cols-5 lg:grid-cols-9">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="px-3 py-2.5">
            <p className="text-xs text-muted-foreground">{item.label}</p>
            <p
              className={cn(
                "text-sm font-semibold tabular-nums",
                item.color
              )}
            >
              {item.value}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function JournalPageClient() {
  const [filters, setFilters] = useState<TradeFilter>(defaultFilters);
  const { data: trades, isLoading } = useTrades(filters);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Trade Journal</h1>

      <StatsBar />

      <TradeSearchFilters filters={filters} onFiltersChange={setFilters} />

      <Card>
        <CardContent className="p-0">
          <TradeTable trades={trades} isLoading={isLoading} />
        </CardContent>
      </Card>
    </div>
  );
}

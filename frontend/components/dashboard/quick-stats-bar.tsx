"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useDashboardStats } from "@/hooks/use-dashboard";
import { useDashboardStore } from "@/stores/dashboard-store";
import { formatPercent, formatR, formatNumber } from "@/lib/format";
import { Sparkline } from "./sparkline";

interface StatCardProps {
  label: string;
  value: string;
  sparklineData?: number[];
  sparklineColor?: string;
}

function StatCard({ label, value, sparklineData, sparklineColor }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-xl font-bold tabular-nums">{value}</p>
        {sparklineData && sparklineData.length > 0 && (
          <div className="mt-2">
            <Sparkline data={sparklineData} color={sparklineColor} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function QuickStatsBar() {
  const { data, isLoading } = useDashboardStats();
  const { statsPeriod, setStatsPeriod } = useDashboardStore();

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="flex justify-end">
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="grid grid-cols-5 gap-4">
          {[0, 1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="mt-2 h-6 w-20" />
                <Skeleton className="mt-3 h-8 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <ToggleGroup
          type="single"
          value={statsPeriod}
          onValueChange={(v) => {
            if (v) setStatsPeriod(v as "1W" | "1M" | "3M" | "ALL");
          }}
          size="sm"
        >
          <ToggleGroupItem value="1W">1W</ToggleGroupItem>
          <ToggleGroupItem value="1M">1M</ToggleGroupItem>
          <ToggleGroupItem value="3M">3M</ToggleGroupItem>
          <ToggleGroupItem value="ALL">All</ToggleGroupItem>
        </ToggleGroup>
      </div>
      <div className="grid grid-cols-5 gap-4">
        <StatCard
          label="Win Rate"
          value={formatPercent(data.winRate)}
          sparklineData={data.winRateHistory}
          sparklineColor="hsl(var(--profit))"
        />
        <StatCard
          label="Avg R"
          value={formatR(data.avgR)}
          sparklineData={data.avgRHistory}
          sparklineColor="hsl(var(--primary))"
        />
        <StatCard label="Total Trades" value={formatNumber(data.totalTrades)} />
        <StatCard label="Open Positions" value={formatNumber(data.openPositions)} />
        <StatCard label="Active Trendlines" value={formatNumber(data.activeTrendlines)} />
      </div>
    </div>
  );
}

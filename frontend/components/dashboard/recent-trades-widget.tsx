"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useRecentTrades } from "@/hooks/use-dashboard";
import { formatCurrency, formatR, formatTimeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

export function RecentTradesWidget() {
  const { data: trades, isLoading } = useRecentTrades();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">Recent Trades</CardTitle>
      </CardHeader>
      <CardContent>
        {!trades || trades.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No recent trades
          </p>
        ) : (
          <div className="space-y-0">
            <div className="grid grid-cols-5 gap-2 border-b pb-2 text-xs font-medium text-muted-foreground">
              <span>Symbol</span>
              <span>Direction</span>
              <span className="text-right">P&L</span>
              <span className="text-right">R</span>
              <span className="text-right">Closed</span>
            </div>
            {trades.map((trade) => {
              const isPositive = trade.pnl >= 0;
              return (
                <div
                  key={trade.id}
                  className="grid grid-cols-5 gap-2 border-b py-2.5 text-sm last:border-0"
                >
                  <span className="font-medium">{trade.symbol}</span>
                  <span>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        trade.direction === "long"
                          ? "border-profit text-profit"
                          : "border-loss text-loss"
                      )}
                    >
                      {trade.direction}
                    </Badge>
                  </span>
                  <span
                    className={cn(
                      "text-right tabular-nums font-medium",
                      isPositive ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatCurrency(trade.pnl)}
                  </span>
                  <span
                    className={cn(
                      "text-right tabular-nums",
                      isPositive ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatR(trade.rMultiple)}
                  </span>
                  <span className="text-right text-xs text-muted-foreground">
                    {formatTimeAgo(trade.closedAt)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

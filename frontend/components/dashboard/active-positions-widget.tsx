"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { usePositions } from "@/hooks/use-dashboard";
import { formatCurrency, formatR, formatPrice, formatTimeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

export function ActivePositionsWidget() {
  const { data: positions, isLoading } = usePositions();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-36" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[0, 1].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">Open Positions</CardTitle>
      </CardHeader>
      <CardContent>
        {!positions || positions.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No open positions
          </p>
        ) : (
          <div className="space-y-0">
            <div className="grid grid-cols-6 gap-2 border-b pb-2 text-xs font-medium text-muted-foreground">
              <span>Symbol</span>
              <span>Direction</span>
              <span className="text-right">Entry</span>
              <span className="text-right">Current</span>
              <span className="text-right">P&L</span>
              <span className="text-right">R</span>
            </div>
            {positions.map((pos) => {
              const isPositive = pos.unrealizedPnl >= 0;
              return (
                <div
                  key={pos.id}
                  className="grid grid-cols-6 gap-2 border-b py-2.5 text-sm last:border-0"
                >
                  <span className="font-medium">{pos.symbol}</span>
                  <span>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        pos.direction === "long"
                          ? "border-profit text-profit"
                          : "border-loss text-loss"
                      )}
                    >
                      {pos.direction}
                    </Badge>
                  </span>
                  <span className="text-right tabular-nums">
                    {formatPrice(pos.entryPrice)}
                  </span>
                  <span className="text-right tabular-nums">
                    {formatPrice(pos.currentPrice)}
                  </span>
                  <span
                    className={cn(
                      "text-right tabular-nums font-medium",
                      isPositive ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatCurrency(pos.unrealizedPnl)}
                  </span>
                  <span
                    className={cn(
                      "text-right tabular-nums",
                      isPositive ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatR(pos.rMultiple)}
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

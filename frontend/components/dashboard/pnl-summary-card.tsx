"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { usePnlSummary } from "@/hooks/use-dashboard";
import { formatPnl, formatR } from "@/lib/format";
import { cn } from "@/lib/utils";

function PnlItem({ label, pnl, r }: { label: string; pnl: number; r: number }) {
  const isPositive = pnl >= 0;
  return (
    <div className="space-y-1">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p
        className={cn(
          "text-2xl font-bold tabular-nums",
          isPositive ? "text-profit" : "text-loss"
        )}
      >
        {formatPnl(pnl)}
      </p>
      <p
        className={cn(
          "text-sm font-medium tabular-nums",
          isPositive ? "text-profit" : "text-loss"
        )}
      >
        {formatR(r)}
      </p>
    </div>
  );
}

export function PnlSummaryCard() {
  const { data, isLoading } = usePnlSummary();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-8 w-28" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-medium">P&L Summary</CardTitle>
        {data.isPaper && (
          <Badge variant="outline" className="border-alert-near text-alert-near">
            Paper
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-6">
          <PnlItem label="Today" pnl={data.todayPnl} r={data.todayR} />
          <PnlItem label="This Week" pnl={data.weekPnl} r={data.weekR} />
          <PnlItem label="This Month" pnl={data.monthPnl} r={data.monthR} />
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useTrendlines } from "@/hooks/use-trendlines";
import { formatPrice, formatTimeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Trendline, TrendlineGrade } from "@/types/trendline";

function GradeBadge({ grade }: { grade: TrendlineGrade | null }) {
  if (!grade) return <Badge variant="outline" className="text-xs">--</Badge>;

  const colorMap: Record<TrendlineGrade, string> = {
    "A+": "bg-grade-a-plus/15 text-grade-a-plus border-grade-a-plus/30",
    A: "bg-grade-a/15 text-grade-a border-grade-a/30",
    B: "bg-grade-b/15 text-grade-b border-grade-b/30",
  };

  return (
    <Badge variant="outline" className={cn("text-xs", colorMap[grade])}>
      {grade}
    </Badge>
  );
}

export function TrendlineAlertsWidget() {
  // Show top trendlines by composite score as "near-price" items
  // Using ES as default instrument for dashboard overview
  const { data: trendlines, isLoading } = useTrendlines("inst-es", "1D");

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const sorted = (trendlines || [])
    .filter((t) => t.status === "active" || t.status === "qualifying")
    .sort((a, b) => (b.compositeScore || 0) - (a.compositeScore || 0))
    .slice(0, 10);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">Top Trendlines</CardTitle>
      </CardHeader>
      <CardContent>
        {sorted.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No active trendlines
          </p>
        ) : (
          <div className="space-y-0">
            <div className="grid grid-cols-5 gap-2 border-b pb-2 text-xs font-medium text-muted-foreground">
              <span>Grade</span>
              <span>Direction</span>
              <span className="text-right">Projected</span>
              <span className="text-right">Touches</span>
              <span className="text-right">Score</span>
            </div>
            {sorted.map((tl) => (
              <div
                key={tl.id}
                className="grid grid-cols-5 gap-2 border-b py-2.5 text-sm last:border-0"
              >
                <GradeBadge grade={tl.grade} />
                <span
                  className={cn(
                    "text-xs font-medium",
                    tl.direction === "SUPPORT" ? "text-profit" : "text-loss"
                  )}
                >
                  {tl.direction}
                </span>
                <span className="text-right tabular-nums">
                  {tl.projectedPrice ? formatPrice(tl.projectedPrice) : "--"}
                </span>
                <span className="text-right tabular-nums">{tl.touchCount}</span>
                <span className="text-right tabular-nums font-medium">
                  {tl.compositeScore?.toFixed(1) || "--"}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

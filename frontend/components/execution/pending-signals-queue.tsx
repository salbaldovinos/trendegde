"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Check, X } from "lucide-react";
import { useSignals, useSubmitSignal, useRejectSignal } from "@/hooks/use-execution";
import { formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Signal, RiskCheck } from "@/types/execution";

const PENDING_STATUSES = new Set(["RECEIVED", "VALIDATED", "ENRICHED", "RISK_PASSED"]);

function sourceBadgeColor(source: Signal["source"]) {
  switch (source) {
    case "INTERNAL":
      return "bg-blue-500/10 text-blue-500 border-blue-500/30";
    case "WEBHOOK":
      return "bg-purple-500/10 text-purple-500 border-purple-500/30";
    case "MANUAL":
      return "bg-orange-500/10 text-orange-500 border-orange-500/30";
  }
}

const riskDotColor: Record<string, string> = {
  PASS: "bg-green-500",
  FAIL: "bg-red-500",
  WARN: "bg-yellow-500",
  SKIP: "bg-gray-400",
};

function RiskCheckDots({ checks }: { checks: RiskCheck[] }) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex items-center gap-1">
        {checks.map((check, i) => (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <span
                className={cn(
                  "inline-block h-2 w-2 rounded-full",
                  riskDotColor[check.result] ?? "bg-gray-400"
                )}
              />
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">
              <p className="font-medium">{check.checkName}</p>
              <p className="text-muted-foreground">{check.result}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}

export function PendingSignalsQueue() {
  const { data: signals, isLoading } = useSignals();
  const submitSignal = useSubmitSignal();
  const rejectSignal = useRejectSignal();

  const pending = signals?.filter((s) => PENDING_STATUSES.has(s.status));

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-36" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[0, 1].map((i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">
          Signal Queue
          {pending && pending.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({pending.length})
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!pending || pending.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No pending signals
          </p>
        ) : (
          <div className="space-y-3">
            {pending.map((signal) => (
              <div
                key={signal.id}
                className="rounded-lg border p-3 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {signal.instrumentSymbol}
                    </span>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        signal.direction === "LONG"
                          ? "border-profit text-profit"
                          : "border-loss text-loss"
                      )}
                    >
                      {signal.direction}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={cn("text-xs", sourceBadgeColor(signal.source))}
                    >
                      {signal.source}
                    </Badge>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {signal.status.replace("_", " ")}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                  <div>
                    <span className="block text-foreground tabular-nums">
                      {formatPrice(signal.entryPrice)}
                    </span>
                    Entry ({signal.entryType})
                  </div>
                  <div>
                    <span className="block text-foreground tabular-nums">
                      {signal.stopLossPrice !== null
                        ? formatPrice(signal.stopLossPrice)
                        : "-"}
                    </span>
                    Stop Loss
                  </div>
                  <div>
                    <span className="block text-foreground tabular-nums">
                      {signal.takeProfitPrice !== null
                        ? formatPrice(signal.takeProfitPrice)
                        : "-"}
                    </span>
                    Take Profit
                  </div>
                </div>

                {signal.trendlineGrade && (
                  <p className="text-xs text-muted-foreground">
                    Trendline: Grade {signal.trendlineGrade}
                  </p>
                )}

                {signal.riskChecks && signal.riskChecks.length > 0 && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Risk:</span>
                    <RiskCheckDots checks={signal.riskChecks} />
                  </div>
                )}

                <div className="flex gap-2 pt-1">
                  <Button
                    size="sm"
                    className="h-7 flex-1 bg-profit text-white hover:bg-profit/90"
                    disabled={submitSignal.isPending}
                    onClick={() =>
                      submitSignal.mutate({
                        instrumentSymbol: signal.instrumentSymbol,
                        direction: signal.direction,
                        entryType: signal.entryType,
                        entryPrice: signal.entryPrice,
                        stopLossPrice: signal.stopLossPrice,
                        takeProfitPrice: signal.takeProfitPrice,
                        quantity: signal.quantity,
                        notes: "",
                      })
                    }
                  >
                    <Check className="mr-1 h-3 w-3" />
                    Execute
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 flex-1 text-destructive hover:text-destructive"
                    disabled={rejectSignal.isPending}
                    onClick={() => rejectSignal.mutate(signal.id)}
                  >
                    <X className="mr-1 h-3 w-3" />
                    Reject
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCircuitBreaker, useResetCircuitBreaker } from "@/hooks/use-execution";

export function CircuitBreakerBanner() {
  const { data: cb } = useCircuitBreaker();
  const resetMutation = useResetCircuitBreaker();

  if (!cb || cb.state !== "TRIPPED") return null;

  return (
    <div className="flex items-center justify-between rounded-lg border border-destructive bg-destructive/10 px-4 py-3">
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-5 w-5 text-destructive" />
        <div>
          <p className="text-sm font-semibold text-destructive">
            Circuit Breaker Tripped
          </p>
          <p className="text-xs text-muted-foreground">
            {cb.consecutiveLosses} consecutive losses (threshold: {cb.threshold}).
            {cb.queuedSignals > 0 &&
              ` ${cb.queuedSignals} signal(s) queued.`}
          </p>
        </div>
      </div>
      <Button
        variant="destructive"
        size="sm"
        onClick={() => resetMutation.mutate()}
        disabled={resetMutation.isPending}
      >
        {resetMutation.isPending ? "Resetting..." : "Reset"}
      </Button>
    </div>
  );
}

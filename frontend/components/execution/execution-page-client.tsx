"use client";

import { CircuitBreakerBanner } from "./circuit-breaker-banner";
import { ActivePositionsTable } from "./active-positions-table";
import { PendingSignalsQueue } from "./pending-signals-queue";
import { ManualTradeForm } from "./manual-trade-form";
import { BrokerConnectionStatus } from "./broker-connection-status";
import { PaperLiveToggle } from "./paper-live-toggle";
import { useOrders, useCancelOrder } from "@/hooks/use-execution";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatPrice, formatTimeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

function OrdersTable() {
  const { data: orders, isLoading } = useOrders();
  const cancelOrder = useCancelOrder();

  const working = orders?.filter(
    (o) => o.status === "SUBMITTED" || o.status === "PARTIAL_FILL"
  );

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">
          Working Orders
          {working && working.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({working.length})
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!working || working.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No working orders
          </p>
        ) : (
          <div className="space-y-2">
            {working.map((order) => (
              <div
                key={order.id}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium">{order.instrumentSymbol}</span>
                  <Badge variant="outline" className="text-xs">
                    {order.bracketRole.replace("_", " ")}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      order.side === "BUY"
                        ? "border-profit text-profit"
                        : "border-loss text-loss"
                    )}
                  >
                    {order.side}
                  </Badge>
                </div>
                <div className="flex items-center gap-3">
                  <span className="tabular-nums text-xs text-muted-foreground">
                    {order.orderType} @ {order.price !== null ? formatPrice(order.price) : "MKT"}
                  </span>
                  <span className="tabular-nums text-xs">
                    x{order.quantity}
                  </span>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-6 w-6 text-muted-foreground hover:text-destructive"
                    disabled={cancelOrder.isPending}
                    onClick={() => cancelOrder.mutate(order.id)}
                  >
                    <X className="h-3.5 w-3.5" />
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

export function ExecutionPageClient() {
  return (
    <div className="space-y-6">
      {/* Header with mode toggle */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Execution</h1>
        <PaperLiveToggle />
      </div>

      {/* Circuit breaker alert */}
      <CircuitBreakerBanner />

      {/* Main 3-column layout */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left: Positions + Orders */}
        <div className="space-y-6 lg:col-span-5">
          <ActivePositionsTable />
          <OrdersTable />
        </div>

        {/* Center: Manual trade form */}
        <div className="lg:col-span-3">
          <ManualTradeForm />
        </div>

        {/* Right: Signals + Broker */}
        <div className="space-y-6 lg:col-span-4">
          <PendingSignalsQueue />
          <BrokerConnectionStatus />
        </div>
      </div>
    </div>
  );
}

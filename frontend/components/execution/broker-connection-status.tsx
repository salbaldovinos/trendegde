"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useBrokerStatus } from "@/hooks/use-execution";
import { formatTimeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

export function BrokerConnectionStatus() {
  const { data: broker, isLoading } = useBrokerStatus();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!broker) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">Broker</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-block h-2.5 w-2.5 rounded-full",
              broker.connected ? "bg-profit" : "bg-loss"
            )}
          />
          <span className="text-sm">
            {broker.connected ? "Connected" : "Disconnected"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={broker.isPaper ? "secondary" : "default"}>
            {broker.isPaper ? "Paper" : "Live"}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {broker.brokerType.toUpperCase()}
          </span>
        </div>
        {broker.accountId && (
          <p className="text-xs text-muted-foreground">
            Account: {broker.accountId}
          </p>
        )}
        {broker.lastConnected && (
          <p className="text-xs text-muted-foreground">
            Last connected {formatTimeAgo(broker.lastConnected)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

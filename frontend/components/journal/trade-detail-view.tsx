"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft } from "lucide-react";
import { useTrade } from "@/hooks/use-journal";
import { JournalEnrichmentForm } from "./journal-enrichment-form";
import { ScreenshotUploadZone } from "./screenshot-upload-zone";
import { formatCurrency, formatR, formatPrice, formatPnl, formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

interface TradeDetailViewProps {
  tradeId: string;
}

export function TradeDetailView({ tradeId }: TradeDetailViewProps) {
  const { data: trade, isLoading } = useTrade(tradeId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[400px]" />
          <Skeleton className="h-[400px]" />
        </div>
      </div>
    );
  }

  if (!trade) {
    return (
      <div className="space-y-4">
        <Link href="/journal">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Journal
          </Button>
        </Link>
        <p className="py-12 text-center text-sm text-muted-foreground">
          Trade not found
        </p>
      </div>
    );
  }

  const isWin = trade.realizedPnl >= 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/journal">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </Link>
        <h1 className="text-xl font-semibold">
          {trade.instrumentSymbol} Trade
        </h1>
        <Badge
          variant="outline"
          className={cn(
            trade.direction === "LONG"
              ? "border-profit text-profit"
              : "border-loss text-loss"
          )}
        >
          {trade.direction}
        </Badge>
        <span
          className={cn(
            "text-lg font-semibold tabular-nums",
            isWin ? "text-profit" : "text-loss"
          )}
        >
          {formatPnl(trade.realizedPnl)}
        </span>
      </div>

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Chart placeholder + trade data */}
        <div className="space-y-6">
          {/* Chart placeholder */}
          <Card>
            <CardContent className="flex h-48 items-center justify-center">
              <p className="text-sm text-muted-foreground">
                Chart view coming soon
              </p>
            </CardContent>
          </Card>

          {/* Trade details */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium">
                Trade Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Entry Price</p>
                  <p className="font-medium tabular-nums">
                    {formatPrice(trade.entryPrice)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Exit Price</p>
                  <p className="font-medium tabular-nums">
                    {formatPrice(trade.exitPrice)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Quantity</p>
                  <p className="font-medium tabular-nums">{trade.quantity}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Exit Reason</p>
                  <Badge variant="secondary" className="text-xs">
                    {trade.exitReason.replace("_", " ")}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Realized P&L</p>
                  <p
                    className={cn(
                      "font-medium tabular-nums",
                      isWin ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatPnl(trade.realizedPnl)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Net P&L</p>
                  <p
                    className={cn(
                      "font-medium tabular-nums",
                      trade.netPnl >= 0 ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatPnl(trade.netPnl)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">R-Multiple</p>
                  <p
                    className={cn(
                      "font-medium tabular-nums",
                      isWin ? "text-profit" : "text-loss"
                    )}
                  >
                    {formatR(trade.rMultiple)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">MAE / MFE</p>
                  <p className="font-medium tabular-nums text-xs">
                    <span className="text-loss">
                      {trade.mae !== null ? formatPrice(trade.mae) : "-"}
                    </span>
                    {" / "}
                    <span className="text-profit">
                      {trade.mfe !== null ? formatPrice(trade.mfe) : "-"}
                    </span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Entered</p>
                  <p className="text-xs">{formatDateTime(trade.enteredAt)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Closed</p>
                  <p className="text-xs">{formatDateTime(trade.closedAt)}</p>
                </div>
              </div>

              {trade.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1">
                  {trade.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {trade.playbook && (
                <div className="mt-3">
                  <p className="text-xs text-muted-foreground">Playbook</p>
                  <Badge variant="secondary" className="text-xs mt-1">
                    {trade.playbook}
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Journal enrichment */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium">
                Journal Entry
              </CardTitle>
            </CardHeader>
            <CardContent>
              <JournalEnrichmentForm trade={trade} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium">
                Screenshots
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScreenshotUploadZone screenshots={trade.screenshots} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

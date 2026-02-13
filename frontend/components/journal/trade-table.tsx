"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronLeft, ChevronRight, Star, ArrowUpDown } from "lucide-react";
import { formatCurrency, formatR, formatPrice, formatDate, formatPnl } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Trade } from "@/types/journal";

interface TradeTableProps {
  trades: Trade[] | undefined;
  isLoading: boolean;
}

type SortField = "closedAt" | "instrumentSymbol" | "realizedPnl" | "rMultiple";
type SortDir = "asc" | "desc";

const PAGE_SIZE = 15;

export function TradeTable({ trades, isLoading }: TradeTableProps) {
  const router = useRouter();
  const [sortField, setSortField] = useState<SortField>("closedAt");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(0);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!trades || trades.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-muted-foreground">
        No trades found
      </p>
    );
  }

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
    setPage(0);
  }

  const sorted = [...trades].sort((a, b) => {
    let cmp = 0;
    switch (sortField) {
      case "closedAt":
        cmp = a.closedAt.localeCompare(b.closedAt);
        break;
      case "instrumentSymbol":
        cmp = a.instrumentSymbol.localeCompare(b.instrumentSymbol);
        break;
      case "realizedPnl":
        cmp = a.realizedPnl - b.realizedPnl;
        break;
      case "rMultiple":
        cmp = a.rMultiple - b.rMultiple;
        break;
    }
    return sortDir === "asc" ? cmp : -cmp;
  });

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function SortHeader({ field, children }: { field: SortField; children: React.ReactNode }) {
    return (
      <button
        className="inline-flex items-center gap-1 hover:text-foreground"
        onClick={() => toggleSort(field)}
      >
        {children}
        <ArrowUpDown className="h-3 w-3" />
      </button>
    );
  }

  return (
    <div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <SortHeader field="closedAt">Date</SortHeader>
            </TableHead>
            <TableHead>
              <SortHeader field="instrumentSymbol">Symbol</SortHeader>
            </TableHead>
            <TableHead>Dir</TableHead>
            <TableHead className="text-right">Entry</TableHead>
            <TableHead className="text-right">Exit</TableHead>
            <TableHead className="text-right">
              <SortHeader field="realizedPnl">P&L</SortHeader>
            </TableHead>
            <TableHead className="text-right">
              <SortHeader field="rMultiple">R</SortHeader>
            </TableHead>
            <TableHead>Exit</TableHead>
            <TableHead>Rating</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {paged.map((trade) => {
            const isWin = trade.realizedPnl >= 0;
            return (
              <TableRow
                key={trade.id}
                className={cn(
                  "cursor-pointer",
                  isWin
                    ? "border-l-2 border-l-profit"
                    : "border-l-2 border-l-loss"
                )}
                onClick={() => router.push(`/journal/trade/${trade.id}`)}
              >
                <TableCell className="text-xs text-muted-foreground">
                  {formatDate(trade.closedAt)}
                </TableCell>
                <TableCell className="font-medium">
                  {trade.instrumentSymbol}
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      trade.direction === "LONG"
                        ? "border-profit text-profit"
                        : "border-loss text-loss"
                    )}
                  >
                    {trade.direction}
                  </Badge>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatPrice(trade.entryPrice)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatPrice(trade.exitPrice)}
                </TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums font-medium",
                    isWin ? "text-profit" : "text-loss"
                  )}
                >
                  {formatPnl(trade.realizedPnl)}
                </TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums",
                    isWin ? "text-profit" : "text-loss"
                  )}
                >
                  {formatR(trade.rMultiple)}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="text-xs">
                    {trade.exitReason.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell>
                  {trade.rating ? (
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star
                          key={i}
                          className={cn(
                            "h-3 w-3",
                            i < trade.rating!
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-muted-foreground/30"
                          )}
                        />
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground">-</span>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t px-2 py-3">
          <p className="text-xs text-muted-foreground">
            {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, sorted.length)} of{" "}
            {sorted.length} trades
          </p>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              className="h-7 w-7 p-0"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 w-7 p-0"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

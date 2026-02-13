"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { MoreHorizontal, X } from "lucide-react";
import {
  useExecutionPositions,
  useClosePosition,
  useFlattenAll,
  useOrders,
  useModifyOrder,
} from "@/hooks/use-execution";
import { formatCurrency, formatR, formatPrice, formatPnl } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ExecutionPosition } from "@/types/execution";

function ModifyPriceDialog({
  open,
  onOpenChange,
  position,
  field,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  position: ExecutionPosition;
  field: "STOP_LOSS" | "TAKE_PROFIT";
}) {
  const { data: orders } = useOrders();
  const modifyOrder = useModifyOrder();
  const currentPrice =
    field === "STOP_LOSS" ? position.stopLossPrice : position.takeProfitPrice;
  const [price, setPrice] = useState(currentPrice?.toString() ?? "");

  const bracketOrder = orders?.find(
    (o) =>
      o.signalId === position.signalId &&
      o.bracketRole === field &&
      (o.status === "SUBMITTED" || o.status === "CONSTRUCTED")
  );

  function handleSubmit() {
    if (!bracketOrder || !price) return;
    modifyOrder.mutate(
      { orderId: bracketOrder.id, data: { newPrice: parseFloat(price) } as never },
      { onSuccess: () => onOpenChange(false) }
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>
            Modify {field === "STOP_LOSS" ? "Stop Loss" : "Take Profit"}
          </DialogTitle>
          <DialogDescription>
            {position.instrumentSymbol} {position.direction} — Current:{" "}
            {currentPrice !== null ? formatPrice(currentPrice) : "None"}
          </DialogDescription>
        </DialogHeader>
        <Input
          type="number"
          step="0.25"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          placeholder="New price"
        />
        {!bracketOrder && (
          <p className="text-xs text-destructive">
            No pending {field === "STOP_LOSS" ? "SL" : "TP"} order found for
            this position.
          </p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!bracketOrder || !price || modifyOrder.isPending}
          >
            Update
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ActivePositionsTable() {
  const { data: positions, isLoading } = useExecutionPositions("OPEN");
  const closeMutation = useClosePosition();
  const flattenMutation = useFlattenAll();
  const [modifyTarget, setModifyTarget] = useState<{
    position: ExecutionPosition;
    field: "STOP_LOSS" | "TAKE_PROFIT";
  } | null>(null);

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-36" />
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

  const totalPnl = positions?.reduce((sum, p) => sum + p.unrealizedPnl, 0) ?? 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-medium">
          Active Positions
          {positions && positions.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({positions.length})
            </span>
          )}
        </CardTitle>
        {positions && positions.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs text-destructive hover:text-destructive"
            onClick={() => flattenMutation.mutate()}
            disabled={flattenMutation.isPending}
          >
            <X className="mr-1 h-3 w-3" />
            Flatten All
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {!positions || positions.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No open positions
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Dir</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Entry</TableHead>
                <TableHead className="text-right">Current</TableHead>
                <TableHead className="text-right">SL</TableHead>
                <TableHead className="text-right">TP</TableHead>
                <TableHead className="text-right">P&L</TableHead>
                <TableHead className="text-right">R</TableHead>
                <TableHead className="text-right">MAE</TableHead>
                <TableHead className="text-right">MFE</TableHead>
                <TableHead className="w-8" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {positions.map((pos) => {
                const isPositive = pos.unrealizedPnl >= 0;
                return (
                  <TableRow key={pos.id}>
                    <TableCell className="font-medium">
                      {pos.instrumentSymbol}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs",
                          pos.direction === "LONG"
                            ? "border-profit text-profit"
                            : "border-loss text-loss"
                        )}
                      >
                        {pos.direction}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {pos.quantity}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatPrice(pos.entryPrice)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {pos.currentPrice !== null
                        ? formatPrice(pos.currentPrice)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-xs text-muted-foreground">
                      {pos.stopLossPrice !== null
                        ? formatPrice(pos.stopLossPrice)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-xs text-muted-foreground">
                      {pos.takeProfitPrice !== null
                        ? formatPrice(pos.takeProfitPrice)
                        : "-"}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right tabular-nums font-medium",
                        isPositive ? "text-profit" : "text-loss"
                      )}
                    >
                      {formatPnl(pos.unrealizedPnl)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right tabular-nums",
                        (pos.rMultiple ?? 0) >= 0 ? "text-profit" : "text-loss"
                      )}
                    >
                      {pos.rMultiple !== null ? formatR(pos.rMultiple) : "-"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-xs text-loss">
                      {pos.mae !== null ? formatPrice(pos.mae) : "-"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-xs text-profit">
                      {pos.mfe !== null ? formatPrice(pos.mfe) : "-"}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => closeMutation.mutate(pos.id)}
                          >
                            Close Position
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() =>
                              setModifyTarget({ position: pos, field: "STOP_LOSS" })
                            }
                          >
                            Modify SL
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() =>
                              setModifyTarget({ position: pos, field: "TAKE_PROFIT" })
                            }
                          >
                            Modify TP
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
            <TableFooter>
              <TableRow>
                <TableCell colSpan={7} className="text-right font-medium">
                  Total
                </TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums font-semibold",
                    totalPnl >= 0 ? "text-profit" : "text-loss"
                  )}
                >
                  {formatPnl(totalPnl)}
                </TableCell>
                <TableCell colSpan={4} />
              </TableRow>
            </TableFooter>
          </Table>
        )}
      </CardContent>

      {modifyTarget && (
        <ModifyPriceDialog
          open={!!modifyTarget}
          onOpenChange={(open) => !open && setModifyTarget(null)}
          position={modifyTarget.position}
          field={modifyTarget.field}
        />
      )}
    </Card>
  );
}

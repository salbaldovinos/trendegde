"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { mockInstruments } from "@/lib/mock-data";
import { useSubmitSignal } from "@/hooks/use-execution";
import { useExecutionStore } from "@/stores/execution-store";
import { formatCurrency } from "@/lib/format";

export function ManualTradeForm() {
  const submitMutation = useSubmitSignal();
  const { tradingMode } = useExecutionStore();

  const [instrument, setInstrument] = useState("");
  const [direction, setDirection] = useState<"LONG" | "SHORT">("LONG");
  const [entryType, setEntryType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [entryPrice, setEntryPrice] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [takeProfit, setTakeProfit] = useState("");
  const [quantity, setQuantity] = useState("");

  const entry = parseFloat(entryPrice) || 0;
  const sl = parseFloat(stopLoss) || 0;
  const tp = parseFloat(takeProfit) || 0;
  const qty = parseInt(quantity) || 0;

  const riskPerContract = entry && sl ? Math.abs(entry - sl) : 0;
  const totalRisk = riskPerContract * (qty || 1);
  const reward = entry && tp ? Math.abs(tp - entry) : 0;
  const rr = riskPerContract > 0 ? reward / riskPerContract : 0;

  function handleSubmit() {
    if (!instrument || !entry) return;
    submitMutation.mutate({
      instrumentSymbol: instrument,
      direction,
      entryType,
      entryPrice: entry,
      stopLossPrice: sl || null,
      takeProfitPrice: tp || null,
      quantity: qty || null,
      notes: "",
    });
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">Manual Trade</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Instrument</Label>
          <Select value={instrument} onValueChange={setInstrument}>
            <SelectTrigger>
              <SelectValue placeholder="Select instrument" />
            </SelectTrigger>
            <SelectContent>
              {mockInstruments.map((inst) => (
                <SelectItem key={inst.id} value={inst.symbol}>
                  {inst.symbol} - {inst.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Direction</Label>
          <ToggleGroup
            type="single"
            value={direction}
            onValueChange={(v) => {
              if (v) setDirection(v as "LONG" | "SHORT");
            }}
            className="justify-start"
          >
            <ToggleGroupItem value="LONG" className="flex-1 data-[state=on]:bg-profit/20 data-[state=on]:text-profit">
              Long
            </ToggleGroupItem>
            <ToggleGroupItem value="SHORT" className="flex-1 data-[state=on]:bg-loss/20 data-[state=on]:text-loss">
              Short
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <div className="space-y-2">
          <Label>Entry Type</Label>
          <ToggleGroup
            type="single"
            value={entryType}
            onValueChange={(v) => {
              if (v) setEntryType(v as "MARKET" | "LIMIT");
            }}
            className="justify-start"
          >
            <ToggleGroupItem value="MARKET" className="flex-1">
              Market
            </ToggleGroupItem>
            <ToggleGroupItem value="LIMIT" className="flex-1">
              Limit
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Entry Price</Label>
            <Input
              type="number"
              step="any"
              placeholder="0.00"
              value={entryPrice}
              onChange={(e) => setEntryPrice(e.target.value)}
              className="tabular-nums"
            />
          </div>
          <div className="space-y-2">
            <Label>Quantity</Label>
            <Input
              type="number"
              min="1"
              placeholder="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="tabular-nums"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Stop Loss</Label>
            <Input
              type="number"
              step="any"
              placeholder="0.00"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              className="tabular-nums"
            />
          </div>
          <div className="space-y-2">
            <Label>Take Profit</Label>
            <Input
              type="number"
              step="any"
              placeholder="0.00"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              className="tabular-nums"
            />
          </div>
        </div>

        {(riskPerContract > 0 || rr > 0) && (
          <div className="rounded-md bg-muted/50 p-3 text-xs space-y-1">
            {riskPerContract > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Risk/contract</span>
                <span className="tabular-nums font-medium">
                  {formatCurrency(riskPerContract)}
                </span>
              </div>
            )}
            {totalRisk > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total risk</span>
                <span className="tabular-nums font-medium">
                  {formatCurrency(totalRisk)}
                </span>
              </div>
            )}
            {rr > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">R:R ratio</span>
                <span className="tabular-nums font-medium">
                  1:{rr.toFixed(1)}
                </span>
              </div>
            )}
          </div>
        )}

        <Button
          className="w-full"
          onClick={handleSubmit}
          disabled={!instrument || !entry || submitMutation.isPending}
        >
          {submitMutation.isPending
            ? "Submitting..."
            : tradingMode === "live"
              ? "Submit Live Order"
              : "Submit Paper Order"}
        </Button>
      </CardContent>
    </Card>
  );
}

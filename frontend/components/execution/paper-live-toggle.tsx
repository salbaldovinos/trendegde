"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useExecutionStore } from "@/stores/execution-store";
import { useUpdateRiskSettings } from "@/hooks/use-execution";
import { cn } from "@/lib/utils";

export function PaperLiveToggle() {
  const { tradingMode, setTradingMode } = useExecutionStore();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const updateRiskSettings = useUpdateRiskSettings();

  function handleToggle() {
    if (tradingMode === "paper") {
      setConfirmOpen(true);
    } else {
      updateRiskSettings.mutate(
        { isPaperMode: true },
        { onSuccess: () => setTradingMode("paper") }
      );
    }
  }

  function confirmLive() {
    updateRiskSettings.mutate(
      { isPaperMode: false },
      {
        onSuccess: () => {
          setTradingMode("live");
          setConfirmOpen(false);
        },
      }
    );
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant={tradingMode === "paper" ? "default" : "outline"}
          className={cn(
            "h-7 text-xs",
            tradingMode === "paper" && "bg-blue-600 hover:bg-blue-700"
          )}
          onClick={() => tradingMode !== "paper" && handleToggle()}
        >
          Paper
        </Button>
        <Button
          size="sm"
          variant={tradingMode === "live" ? "default" : "outline"}
          className={cn(
            "h-7 text-xs",
            tradingMode === "live" && "bg-profit hover:bg-profit/90"
          )}
          onClick={() => tradingMode !== "live" && handleToggle()}
        >
          Live
        </Button>
      </div>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Switch to Live Trading?</DialogTitle>
            <DialogDescription>
              Are you sure? Live mode will execute real trades with real money.
              Make sure your broker connection is active and risk settings are
              configured.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmLive}>
              Switch to Live
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

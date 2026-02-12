"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useTrendlineStore } from "@/stores/trendline-store";
import type { Timeframe } from "@/types/trendline";

const timeframes: Timeframe[] = ["1H", "4H", "1D", "1W"];

export function TimeframeSelector() {
  const { selectedTimeframe, setSelectedTimeframe } = useTrendlineStore();

  return (
    <ToggleGroup
      type="single"
      value={selectedTimeframe}
      onValueChange={(val) => {
        if (val) setSelectedTimeframe(val as Timeframe);
      }}
      size="sm"
    >
      {timeframes.map((tf) => (
        <ToggleGroupItem key={tf} value={tf} className="px-3 text-xs">
          {tf}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

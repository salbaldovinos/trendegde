"use client";

import { useRef, useState, useCallback } from "react";
import { useChart } from "@/hooks/use-chart";
import { useTrendlineStore } from "@/stores/trendline-store";
import { useCandles, useTrendlines } from "@/hooks/use-trendlines";
import { Skeleton } from "@/components/ui/skeleton";
import { formatPrice } from "@/lib/format";

interface OhlcTooltip {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export function CandlestickChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ohlc, setOhlc] = useState<OhlcTooltip | null>(null);
  const { selectedInstrumentId, selectedTimeframe, selectedTrendlineId } =
    useTrendlineStore();

  const { data: candles, isLoading: candlesLoading } = useCandles(
    selectedInstrumentId,
    selectedTimeframe
  );
  const { data: trendlines } = useTrendlines(
    selectedInstrumentId,
    selectedTimeframe
  );

  const handleCrosshairMove = useCallback(
    (data: OhlcTooltip | null) => setOhlc(data),
    []
  );

  useChart(containerRef, {
    candles: candles ?? [],
    trendlines: trendlines ?? [],
    selectedTrendlineId,
    onCrosshairMove: handleCrosshairMove,
  });

  if (!selectedInstrumentId) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Select an instrument to view chart
      </div>
    );
  }

  if (candlesLoading) {
    return <Skeleton className="h-full w-full" />;
  }

  return (
    <div className="relative h-full w-full">
      {/* OHLC Tooltip */}
      {ohlc && (
        <div className="absolute top-2 left-2 z-10 flex gap-3 rounded bg-card/90 px-3 py-1.5 text-xs backdrop-blur-sm border shadow-sm">
          <span>
            O{" "}
            <span className="font-medium">{formatPrice(ohlc.open)}</span>
          </span>
          <span>
            H{" "}
            <span className="font-medium">{formatPrice(ohlc.high)}</span>
          </span>
          <span>
            L{" "}
            <span className="font-medium">{formatPrice(ohlc.low)}</span>
          </span>
          <span>
            C{" "}
            <span
              className={
                ohlc.close >= ohlc.open
                  ? "font-medium text-green-500"
                  : "font-medium text-red-500"
              }
            >
              {formatPrice(ohlc.close)}
            </span>
          </span>
        </div>
      )}
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}

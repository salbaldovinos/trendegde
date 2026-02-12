"use client";

import { useRef, useEffect, useCallback } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  ColorType,
  CrosshairMode,
  type UTCTimestamp,
  type MouseEventParams,
  type Time,
} from "lightweight-charts";
import type { CandleData, Trendline } from "@/types/trendline";

const GRADE_COLORS: Record<string, string> = {
  "A+": "#F59E0B",
  A: "#3B82F6",
  B: "#6B7280",
};

const SELECTED_LINE_WIDTH = 3;
const DEFAULT_LINE_WIDTH = 1;

interface UseChartOptions {
  candles: CandleData[];
  trendlines: Trendline[];
  selectedTrendlineId: string | null;
  onCrosshairMove?: (data: {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
  } | null) => void;
}

export function useChart(
  containerRef: React.RefObject<HTMLDivElement | null>,
  options: UseChartOptions
) {
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const lineSeriesMapRef = useRef<Map<string, ISeriesApi<"Line">>>(new Map());
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Create chart
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9CA3AF",
      },
      grid: {
        vertLines: { color: "rgba(156, 163, 175, 0.1)" },
        horzLines: { color: "rgba(156, 163, 175, 0.1)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "rgba(156, 163, 175, 0.2)",
      },
      timeScale: {
        borderColor: "rgba(156, 163, 175, 0.2)",
        timeVisible: true,
        secondsVisible: false,
      },
      width: container.clientWidth,
      height: container.clientHeight,
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22C55E",
      downColor: "#EF4444",
      wickUpColor: "#22C55E",
      wickDownColor: "#EF4444",
      borderVisible: false,
    });
    candleSeriesRef.current = candleSeries;

    // ResizeObserver for responsive chart
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chart.applyOptions({ width, height });
      }
    });
    observer.observe(container);
    resizeObserverRef.current = observer;

    // Double-click to reset zoom
    container.addEventListener("dblclick", () => {
      chart.timeScale().fitContent();
    });

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      lineSeriesMapRef.current.clear();
    };
  }, [containerRef]);

  // Update candle data
  useEffect(() => {
    if (!candleSeriesRef.current || options.candles.length === 0) return;
    candleSeriesRef.current.setData(
      options.candles.map((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );
    chartRef.current?.timeScale().fitContent();
  }, [options.candles]);

  // Update trendline overlays
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    // Remove old line series that are no longer in the trendlines list
    const currentIds = new Set(options.trendlines.map((t) => t.id));
    for (const [id, series] of lineSeriesMapRef.current) {
      if (!currentIds.has(id)) {
        chart.removeSeries(series);
        lineSeriesMapRef.current.delete(id);
      }
    }

    // Add/update line series for each trendline
    for (const tl of options.trendlines) {
      if (tl.anchorPoints.length < 2) continue;

      const isSelected = tl.id === options.selectedTrendlineId;
      const color = GRADE_COLORS[tl.grade ?? ""] ?? "#6B7280";
      const lineWidth = isSelected ? SELECTED_LINE_WIDTH : DEFAULT_LINE_WIDTH;

      let series = lineSeriesMapRef.current.get(tl.id);
      if (!series) {
        series = chart.addLineSeries({
          color,
          lineWidth,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        lineSeriesMapRef.current.set(tl.id, series);
      } else {
        series.applyOptions({ color, lineWidth });
      }

      // Build line data from anchor points
      const lineData = tl.anchorPoints.map((ap) => ({
        time: (new Date(ap.timestamp).getTime() / 1000) as UTCTimestamp,
        value: ap.price,
      }));

      series.setData(lineData);
    }
  }, [options.trendlines, options.selectedTrendlineId]);

  // Crosshair subscription
  useEffect(() => {
    const chart = chartRef.current;
    const candleSeries = candleSeriesRef.current;
    if (!chart || !candleSeries || !options.onCrosshairMove) return;

    const handler = (param: MouseEventParams<Time>) => {
      if (!param.time || !param.seriesData) {
        options.onCrosshairMove?.(null);
        return;
      }
      const data = param.seriesData.get(candleSeries) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      if (data) {
        options.onCrosshairMove?.({
          time: param.time as number,
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
        });
      }
    };

    chart.subscribeCrosshairMove(handler);
    return () => {
      chart.unsubscribeCrosshairMove(handler);
    };
  }, [options.onCrosshairMove]);

  const fitContent = useCallback(() => {
    chartRef.current?.timeScale().fitContent();
  }, []);

  return { fitContent };
}

"use client";

import { useMemo } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { toast } from "sonner";
import { GradeBadge } from "@/components/trendlines/grade-badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useTrendlineStore } from "@/stores/trendline-store";
import { useTrendlines } from "@/hooks/use-trendlines";
import { apiPatch } from "@/lib/api-client";
import { formatPrice, formatDate, formatNumber } from "@/lib/format";
import type { Trendline } from "@/types/trendline";

function MetricRow({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value ?? "--"}</span>
    </div>
  );
}

export function TrendlineDetailPanel() {
  const queryClient = useQueryClient();
  const {
    selectedInstrumentId,
    selectedTimeframe,
    selectedTrendlineId,
    setSelectedTrendline,
  } = useTrendlineStore();

  const { data: trendlines } = useTrendlines(selectedInstrumentId, selectedTimeframe);

  const trendline: Trendline | undefined = useMemo(
    () => trendlines?.find((t) => t.id === selectedTrendlineId),
    [trendlines, selectedTrendlineId]
  );

  const dismissMutation = useMutation({
    mutationFn: (id: string) =>
      apiPatch<{ status: string }>(`/trendlines/${id}/dismiss`, {}),
    onSuccess: () => {
      toast.success("Trendline dismissed");
      queryClient.invalidateQueries({ queryKey: ["trendlines"] });
      setSelectedTrendline(null);
    },
    onError: () => {
      toast.error("Failed to dismiss trendline");
    },
  });

  if (!trendline) {
    return (
      <div className="flex items-center justify-center h-full p-6 text-sm text-muted-foreground">
        Select a trendline to view details
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <GradeBadge grade={trendline.grade} />
          <span className="text-sm font-medium capitalize">
            {trendline.direction.toLowerCase()}
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setSelectedTrendline(null)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Metrics */}
      <div className="px-4 py-3 space-y-0.5">
        <MetricRow label="Grade" value={trendline.grade ?? "--"} />
        <MetricRow
          label="Composite Score"
          value={trendline.compositeScore?.toFixed(1) ?? "--"}
        />
        <MetricRow label="Touch Count" value={trendline.touchCount} />
        <MetricRow
          label="Slope"
          value={`${trendline.slopeDegrees.toFixed(1)}\u00B0`}
        />
        <MetricRow
          label="Duration"
          value={trendline.durationDays ? `${trendline.durationDays}d` : "--"}
        />
        <MetricRow
          label="Spacing Quality"
          value={
            trendline.spacingQuality
              ? formatNumber(trendline.spacingQuality, 2)
              : "--"
          }
        />
      </div>

      <Separator />

      {/* Projections */}
      <div className="px-4 py-3 space-y-0.5">
        <MetricRow
          label="Projected Price"
          value={
            trendline.projectedPrice
              ? formatPrice(trendline.projectedPrice)
              : "--"
          }
        />
        <MetricRow
          label="Safety Line"
          value={
            trendline.safetyLinePrice
              ? formatPrice(trendline.safetyLinePrice)
              : "--"
          }
        />
        <MetricRow
          label="Target"
          value={
            trendline.targetPrice ? formatPrice(trendline.targetPrice) : "--"
          }
        />
      </div>

      <Separator />

      {/* Touch points */}
      <div className="px-4 py-3">
        <h4 className="text-xs font-medium text-muted-foreground mb-2">
          Touch Points
        </h4>
        <div className="space-y-1">
          {trendline.touchPoints.map((tp, i) => (
            <div
              key={i}
              className="flex items-center justify-between text-xs"
            >
              <span className="text-muted-foreground">
                {formatDate(tp.timestamp)}
              </span>
              <span className="font-medium">{formatPrice(tp.price)}</span>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Actions */}
      <div className="px-4 py-3 mt-auto">
        <Button
          variant="destructive"
          size="sm"
          className="w-full"
          onClick={() => dismissMutation.mutate(trendline.id)}
          disabled={
            dismissMutation.isPending ||
            trendline.status === "invalidated" ||
            trendline.status === "expired"
          }
        >
          {dismissMutation.isPending ? "Dismissing..." : "Dismiss Trendline"}
        </Button>
      </div>
    </div>
  );
}

"use client";

import { ArrowUp, ArrowDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { GradeBadge } from "@/components/trendlines/grade-badge";
import type { Trendline } from "@/types/trendline";

interface TrendlineListItemProps {
  trendline: Trendline;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

const statusColors: Record<string, string> = {
  detected: "bg-gray-100 text-gray-600",
  qualifying: "bg-blue-100 text-blue-600",
  active: "bg-green-100 text-green-600",
  traded: "bg-purple-100 text-purple-600",
  invalidated: "bg-red-100 text-red-600",
  expired: "bg-gray-100 text-gray-400",
};

export function TrendlineListItem({
  trendline,
  isSelected,
  onSelect,
}: TrendlineListItemProps) {
  const DirectionIcon =
    trendline.direction === "RESISTANCE" ? ArrowUp : ArrowDown;
  const directionColor =
    trendline.direction === "RESISTANCE" ? "text-red-500" : "text-green-500";

  return (
    <button
      onClick={() => onSelect(trendline.id)}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors",
        isSelected
          ? "bg-primary/10 ring-1 ring-primary/20"
          : "hover:bg-accent"
      )}
    >
      <DirectionIcon className={cn("h-4 w-4 shrink-0", directionColor)} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <GradeBadge grade={trendline.grade} />
          <span className="text-xs text-muted-foreground">
            {trendline.touchCount}T
          </span>
          <span className="text-xs text-muted-foreground">
            {Math.abs(trendline.slopeDegrees).toFixed(1)}&deg;
          </span>
        </div>
      </div>
      <span
        className={cn(
          "shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium capitalize",
          statusColors[trendline.status] ?? "bg-gray-100 text-gray-600"
        )}
      >
        {trendline.status}
      </span>
    </button>
  );
}

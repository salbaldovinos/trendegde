"use client";

import { useMemo, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendlineListItem } from "@/components/trendlines/trendline-list-item";
import { useTrendlineStore } from "@/stores/trendline-store";
import { useTrendlines } from "@/hooks/use-trendlines";
import type { Trendline, TrendlineStatus } from "@/types/trendline";

type SortKey = "score" | "grade" | "touches";

const gradeOrder: Record<string, number> = { "A+": 3, A: 2, B: 1 };

function sortTrendlines(lines: Trendline[], sortKey: SortKey): Trendline[] {
  return [...lines].sort((a, b) => {
    if (sortKey === "grade") {
      return (gradeOrder[b.grade ?? ""] ?? 0) - (gradeOrder[a.grade ?? ""] ?? 0);
    }
    if (sortKey === "touches") {
      return b.touchCount - a.touchCount;
    }
    return (b.compositeScore ?? 0) - (a.compositeScore ?? 0);
  });
}

const activeStatuses: TrendlineStatus[] = ["detected", "qualifying", "active"];
const triggeredStatuses: TrendlineStatus[] = ["traded"];
const expiredStatuses: TrendlineStatus[] = ["invalidated", "expired"];

export function TrendlineListPanel() {
  const { selectedInstrumentId, selectedTimeframe, selectedTrendlineId, setSelectedTrendline } =
    useTrendlineStore();
  const { data: trendlines, isLoading } = useTrendlines(
    selectedInstrumentId,
    selectedTimeframe
  );
  const [sortKey] = useState<SortKey>("score");

  const grouped = useMemo(() => {
    if (!trendlines) return { active: [], triggered: [], expired: [] };
    return {
      active: sortTrendlines(
        trendlines.filter((t) => activeStatuses.includes(t.status)),
        sortKey
      ),
      triggered: sortTrendlines(
        trendlines.filter((t) => triggeredStatuses.includes(t.status)),
        sortKey
      ),
      expired: sortTrendlines(
        trendlines.filter((t) => expiredStatuses.includes(t.status)),
        sortKey
      ),
    };
  }, [trendlines, sortKey]);

  if (!selectedInstrumentId) {
    return (
      <div className="flex items-center justify-center p-6 text-sm text-muted-foreground">
        Select an instrument
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-2 p-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  return (
    <Tabs defaultValue="active" className="flex flex-col h-full">
      <TabsList className="w-full shrink-0">
        <TabsTrigger value="active" className="flex-1 text-xs">
          Active ({grouped.active.length})
        </TabsTrigger>
        <TabsTrigger value="triggered" className="flex-1 text-xs">
          Triggered ({grouped.triggered.length})
        </TabsTrigger>
        <TabsTrigger value="expired" className="flex-1 text-xs">
          Expired ({grouped.expired.length})
        </TabsTrigger>
      </TabsList>

      {(["active", "triggered", "expired"] as const).map((tab) => (
        <TabsContent key={tab} value={tab} className="flex-1 overflow-auto mt-0 pt-2">
          <div className="space-y-1">
            {grouped[tab].length === 0 ? (
              <p className="px-3 py-4 text-center text-xs text-muted-foreground">
                No {tab} trendlines
              </p>
            ) : (
              grouped[tab].map((tl) => (
                <TrendlineListItem
                  key={tl.id}
                  trendline={tl}
                  isSelected={selectedTrendlineId === tl.id}
                  onSelect={setSelectedTrendline}
                />
              ))
            )}
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}

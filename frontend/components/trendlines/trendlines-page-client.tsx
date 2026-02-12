"use client";

import { useState } from "react";
import { Menu, Settings2 } from "lucide-react";
import { InstrumentSelector } from "@/components/trendlines/instrument-selector";
import { TimeframeSelector } from "@/components/trendlines/timeframe-selector";
import { CandlestickChart } from "@/components/trendlines/candlestick-chart";
import { TrendlineListPanel } from "@/components/trendlines/trendline-list-panel";
import { TrendlineDetailPanel } from "@/components/trendlines/trendline-detail-panel";
import { DetectionConfigPanel } from "@/components/trendlines/detection-config-panel";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useTrendlineStore } from "@/stores/trendline-store";
import type { Timeframe } from "@/types/trendline";

interface TrendlinesPageClientProps {
  initialInstrument?: string;
  initialTimeframe?: Timeframe;
}

export function TrendlinesPageClient({
  initialInstrument,
  initialTimeframe,
}: TrendlinesPageClientProps) {
  const { setSelectedInstrument, setSelectedTimeframe, selectedTrendlineId } =
    useTrendlineStore();
  const [rightTab, setRightTab] = useState<"detail" | "config">("detail");
  const [listSheetOpen, setListSheetOpen] = useState(false);

  // Apply URL params on mount
  useState(() => {
    if (initialInstrument) setSelectedInstrument(initialInstrument);
    if (initialTimeframe) setSelectedTimeframe(initialTimeframe);
  });

  return (
    <div className="flex h-full gap-0">
      {/* Left Panel - Desktop (>=1280px) */}
      <aside className="hidden xl:flex w-[250px] shrink-0 flex-col border-r bg-card">
        <div className="p-3 border-b">
          <InstrumentSelector />
        </div>
        <div className="flex-1 overflow-hidden">
          <TrendlineListPanel />
        </div>
      </aside>

      {/* Center - Chart */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-2 border-b px-3 py-2">
          {/* Mobile: Sheet trigger for list panel */}
          <Sheet open={listSheetOpen} onOpenChange={setListSheetOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="xl:hidden h-8 w-8">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-[300px] p-0">
              <SheetHeader className="p-4 border-b">
                <SheetTitle>Trendlines</SheetTitle>
              </SheetHeader>
              <div className="p-3 border-b">
                <InstrumentSelector />
              </div>
              <div className="flex-1 overflow-auto">
                <TrendlineListPanel />
              </div>
            </SheetContent>
          </Sheet>

          {/* Mobile: instrument selector inline */}
          <div className="xl:hidden flex-1 max-w-[200px]">
            <InstrumentSelector />
          </div>

          <TimeframeSelector />

          <div className="ml-auto" />

          {/* Toggle right panel tab on mobile */}
          <Button
            variant={rightTab === "config" ? "secondary" : "ghost"}
            size="icon"
            className="h-8 w-8 lg:hidden"
            onClick={() =>
              setRightTab((t) => (t === "config" ? "detail" : "config"))
            }
          >
            <Settings2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Chart area - Desktop */}
        <div className="hidden md:flex flex-1 min-h-0">
          <div className="flex-1">
            <CandlestickChart />
          </div>
        </div>

        {/* Mobile layout: chart on top, panels below in tabs */}
        <div className="flex flex-col md:hidden flex-1 min-h-0">
          <div className="h-[300px] shrink-0">
            <CandlestickChart />
          </div>
          <Tabs defaultValue="detail" className="flex-1 overflow-hidden">
            <TabsList className="w-full rounded-none border-y">
              <TabsTrigger value="detail" className="flex-1 text-xs">
                Detail
              </TabsTrigger>
              <TabsTrigger value="config" className="flex-1 text-xs">
                Config
              </TabsTrigger>
              <TabsTrigger value="list" className="flex-1 text-xs">
                List
              </TabsTrigger>
            </TabsList>
            <TabsContent value="detail" className="flex-1 overflow-auto mt-0">
              <TrendlineDetailPanel />
            </TabsContent>
            <TabsContent value="config" className="flex-1 overflow-auto mt-0">
              <DetectionConfigPanel />
            </TabsContent>
            <TabsContent value="list" className="flex-1 overflow-auto mt-0">
              <TrendlineListPanel />
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Right Panel - Desktop */}
      <aside className="hidden lg:flex w-[300px] shrink-0 flex-col border-l bg-card">
        <Tabs
          value={rightTab}
          onValueChange={(v) => setRightTab(v as "detail" | "config")}
          className="flex flex-col h-full"
        >
          <TabsList className="w-full shrink-0 rounded-none border-b">
            <TabsTrigger value="detail" className="flex-1 text-xs">
              Detail
            </TabsTrigger>
            <TabsTrigger value="config" className="flex-1 text-xs">
              Config
            </TabsTrigger>
          </TabsList>
          <TabsContent value="detail" className="flex-1 overflow-hidden mt-0">
            <TrendlineDetailPanel />
          </TabsContent>
          <TabsContent value="config" className="flex-1 overflow-hidden mt-0">
            <DetectionConfigPanel />
          </TabsContent>
        </Tabs>
      </aside>
    </div>
  );
}

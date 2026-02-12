import { create } from "zustand";
import type { Timeframe } from "@/types/trendline";

interface TrendlineState {
  selectedInstrumentId: string | null;
  selectedTimeframe: Timeframe;
  selectedTrendlineId: string | null;
  setSelectedInstrument: (id: string | null) => void;
  setSelectedTimeframe: (tf: Timeframe) => void;
  setSelectedTrendline: (id: string | null) => void;
}

export const useTrendlineStore = create<TrendlineState>()((set) => ({
  selectedInstrumentId: null,
  selectedTimeframe: "1D",
  selectedTrendlineId: null,
  setSelectedInstrument: (id) => set({ selectedInstrumentId: id, selectedTrendlineId: null }),
  setSelectedTimeframe: (tf) => set({ selectedTimeframe: tf }),
  setSelectedTrendline: (id) => set({ selectedTrendlineId: id }),
}));

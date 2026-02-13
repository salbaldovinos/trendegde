import { create } from "zustand";

interface ExecutionState {
  selectedPositionId: string | null;
  selectedOrderId: string | null;
  signalQueueOpen: boolean;
  tradingMode: "paper" | "live";
  manualTradeOpen: boolean;
  setSelectedPosition: (id: string | null) => void;
  setSelectedOrder: (id: string | null) => void;
  toggleSignalQueue: () => void;
  setTradingMode: (mode: "paper" | "live") => void;
  setManualTradeOpen: (open: boolean) => void;
}

export const useExecutionStore = create<ExecutionState>()((set) => ({
  selectedPositionId: null,
  selectedOrderId: null,
  signalQueueOpen: true,
  tradingMode: "paper",
  manualTradeOpen: false,
  setSelectedPosition: (id) => set({ selectedPositionId: id }),
  setSelectedOrder: (id) => set({ selectedOrderId: id }),
  toggleSignalQueue: () =>
    set((state) => ({ signalQueueOpen: !state.signalQueueOpen })),
  setTradingMode: (mode) => set({ tradingMode: mode }),
  setManualTradeOpen: (open) => set({ manualTradeOpen: open }),
}));

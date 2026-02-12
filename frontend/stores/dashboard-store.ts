import { create } from "zustand";

type StatsPeriod = "1W" | "1M" | "3M" | "ALL";

interface DashboardState {
  statsPeriod: StatsPeriod;
  setStatsPeriod: (period: StatsPeriod) => void;
}

export const useDashboardStore = create<DashboardState>()((set) => ({
  statsPeriod: "1M",
  setStatsPeriod: (period) => set({ statsPeriod: period }),
}));

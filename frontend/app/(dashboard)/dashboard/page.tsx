import { PnlSummaryCard } from "@/components/dashboard/pnl-summary-card";
import { QuickStatsBar } from "@/components/dashboard/quick-stats-bar";
import { ActivePositionsWidget } from "@/components/dashboard/active-positions-widget";
import { TrendlineAlertsWidget } from "@/components/dashboard/trendline-alerts-widget";
import { RecentTradesWidget } from "@/components/dashboard/recent-trades-widget";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Full-width P&L summary */}
      <PnlSummaryCard />

      {/* 5-column stats bar with period selector */}
      <QuickStatsBar />

      {/* 60/40 split: positions + trendline alerts */}
      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3">
          <ActivePositionsWidget />
        </div>
        <div className="col-span-2">
          <TrendlineAlertsWidget />
        </div>
      </div>

      {/* Recent trades (60% width) */}
      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3">
          <RecentTradesWidget />
        </div>
      </div>
    </div>
  );
}

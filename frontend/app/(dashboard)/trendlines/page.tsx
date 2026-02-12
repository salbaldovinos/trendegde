import { TrendlinesPageClient } from "@/components/trendlines/trendlines-page-client";
import type { Timeframe } from "@/types/trendline";

const validTimeframes = new Set<string>(["1H", "4H", "1D", "1W"]);

interface TrendlinesPageProps {
  searchParams: Promise<{ instrument?: string; timeframe?: string }>;
}

export default async function TrendlinesPage({ searchParams }: TrendlinesPageProps) {
  const params = await searchParams;
  const instrument = params.instrument;
  const timeframe = validTimeframes.has(params.timeframe ?? "")
    ? (params.timeframe as Timeframe)
    : undefined;

  return (
    <div className="h-[calc(100vh-theme(spacing.14)-theme(spacing.14)-theme(spacing.12))]">
      <TrendlinesPageClient
        initialInstrument={instrument}
        initialTimeframe={timeframe}
      />
    </div>
  );
}

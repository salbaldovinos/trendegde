import { TradeDetailView } from "@/components/journal/trade-detail-view";

export const metadata = { title: "Trade Detail | TrendEdge" };

export default function TradeDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return <TradeDetailView tradeId={params.id} />;
}

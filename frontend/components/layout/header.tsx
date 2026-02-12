"use client";

import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/trendlines": "Trendlines",
  "/trades": "Trades",
  "/journal": "Journal",
  "/analytics": "Analytics",
  "/settings": "Settings",
};

export function Header() {
  const pathname = usePathname();

  const title =
    pageTitles[pathname] ||
    Object.entries(pageTitles).find(([path]) =>
      pathname.startsWith(path + "/")
    )?.[1] ||
    "TrendEdge";

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="flex items-center gap-3">
        <Badge variant="outline" className="border-alert-near text-alert-near">
          Paper
        </Badge>
      </div>
    </header>
  );
}

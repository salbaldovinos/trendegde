"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useInstruments } from "@/hooks/use-trendlines";
import { useTrendlineStore } from "@/stores/trendline-store";
import { Skeleton } from "@/components/ui/skeleton";

export function InstrumentSelector() {
  const { data: instruments, isLoading } = useInstruments();
  const { selectedInstrumentId, setSelectedInstrument } = useTrendlineStore();

  if (isLoading) {
    return <Skeleton className="h-10 w-full" />;
  }

  return (
    <Select
      value={selectedInstrumentId ?? undefined}
      onValueChange={setSelectedInstrument}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select instrument" />
      </SelectTrigger>
      <SelectContent>
        {instruments?.map((inst) => (
          <SelectItem key={inst.id} value={inst.id}>
            <span className="font-medium">{inst.symbol}</span>
            <span className="ml-2 text-muted-foreground">{inst.name}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

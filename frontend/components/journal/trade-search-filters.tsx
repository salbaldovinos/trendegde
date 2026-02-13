"use client";

import { useCallback, useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Download, Search } from "lucide-react";
import type { TradeFilter } from "@/types/journal";

interface TradeSearchFiltersProps {
  filters: TradeFilter;
  onFiltersChange: (filters: TradeFilter) => void;
}

export function TradeSearchFilters({
  filters,
  onFiltersChange,
}: TradeSearchFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== filters.search) {
        onFiltersChange({ ...filters, search: searchInput });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput, filters, onFiltersChange]);

  const updateFilter = useCallback(
    (patch: Partial<TradeFilter>) => {
      onFiltersChange({ ...filters, ...patch });
    },
    [filters, onFiltersChange]
  );

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="flex-1 min-w-[200px]">
        <Label className="sr-only">Search</Label>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search symbol, notes, tags..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <div className="w-32">
        <Label className="text-xs text-muted-foreground">From</Label>
        <Input
          type="date"
          value={filters.dateFrom ?? ""}
          onChange={(e) =>
            updateFilter({ dateFrom: e.target.value || null })
          }
          className="text-xs"
        />
      </div>

      <div className="w-32">
        <Label className="text-xs text-muted-foreground">To</Label>
        <Input
          type="date"
          value={filters.dateTo ?? ""}
          onChange={(e) =>
            updateFilter({ dateTo: e.target.value || null })
          }
          className="text-xs"
        />
      </div>

      <div className="w-28">
        <Label className="text-xs text-muted-foreground">Direction</Label>
        <Select
          value={filters.direction ?? "all"}
          onValueChange={(v) =>
            updateFilter({
              direction: v === "all" ? null : (v as "LONG" | "SHORT"),
            })
          }
        >
          <SelectTrigger className="h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="LONG">Long</SelectItem>
            <SelectItem value="SHORT">Short</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button variant="outline" size="sm" className="h-9" disabled>
        <Download className="mr-1.5 h-3.5 w-3.5" />
        Export
      </Button>
    </div>
  );
}

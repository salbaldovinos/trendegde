"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDetectionParams } from "@/hooks/use-trendlines";
import { apiPut, apiPost } from "@/lib/api-client";
import type { DetectionParams } from "@/types/trendline";

interface ParamConfig {
  key: keyof Omit<DetectionParams, "maxLinesPerInstrument" | "presetName">;
  label: string;
  min: number;
  max: number;
  step: number;
}

const params: ParamConfig[] = [
  { key: "minTouchCount", label: "Min Touch Count", min: 2, max: 5, step: 1 },
  { key: "minCandleSpacing", label: "Min Candle Spacing", min: 3, max: 20, step: 1 },
  { key: "maxSlopeDegrees", label: "Max Slope Degrees", min: 15, max: 75, step: 1 },
  { key: "minDurationDays", label: "Min Duration Days", min: 7, max: 180, step: 1 },
  { key: "touchToleranceAtr", label: "Touch Tolerance ATR", min: 0.2, max: 1.5, step: 0.1 },
  { key: "pivotNBarLookback", label: "Pivot N-Bar Lookback", min: 2, max: 10, step: 1 },
];

const presets: Record<string, Partial<DetectionParams>> = {
  conservative: {
    minTouchCount: 4,
    minCandleSpacing: 10,
    maxSlopeDegrees: 30,
    minDurationDays: 30,
    touchToleranceAtr: 0.3,
    pivotNBarLookback: 5,
  },
  default: {
    minTouchCount: 3,
    minCandleSpacing: 6,
    maxSlopeDegrees: 45,
    minDurationDays: 21,
    touchToleranceAtr: 0.5,
    pivotNBarLookback: 5,
  },
  aggressive: {
    minTouchCount: 2,
    minCandleSpacing: 3,
    maxSlopeDegrees: 60,
    minDurationDays: 7,
    touchToleranceAtr: 1.0,
    pivotNBarLookback: 3,
  },
};

export function DetectionConfigPanel() {
  const queryClient = useQueryClient();
  const { data: config, isLoading } = useDetectionParams();
  const [values, setValues] = useState<DetectionParams | null>(null);

  useEffect(() => {
    if (config && !values) {
      setValues(config);
    }
  }, [config, values]);

  const saveMutation = useMutation({
    mutationFn: (data: Partial<DetectionParams>) =>
      apiPut<DetectionParams>("/config", {
        min_touch_count: data.minTouchCount,
        min_candle_spacing: data.minCandleSpacing,
        max_slope_degrees: data.maxSlopeDegrees,
        min_duration_days: data.minDurationDays,
        touch_tolerance_atr: data.touchToleranceAtr,
        pivot_n_bar_lookback: data.pivotNBarLookback,
      }),
    onSuccess: () => {
      toast.success("Detection config saved");
      queryClient.invalidateQueries({ queryKey: ["detection-params"] });
      queryClient.invalidateQueries({ queryKey: ["trendlines"] });
    },
    onError: () => {
      toast.error("Failed to save config");
    },
  });

  const resetMutation = useMutation({
    mutationFn: () => apiPost<{ message: string }>("/config/reset", {}),
    onSuccess: () => {
      toast.success("Config reset to defaults");
      setValues(null);
      queryClient.invalidateQueries({ queryKey: ["detection-params"] });
      queryClient.invalidateQueries({ queryKey: ["trendlines"] });
    },
    onError: () => {
      toast.error("Failed to reset config");
    },
  });

  if (isLoading || !values) {
    return (
      <div className="space-y-3 p-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  function updateValue(key: keyof DetectionParams, val: number) {
    setValues((prev) => (prev ? { ...prev, [key]: val } : prev));
  }

  function applyPreset(name: string) {
    const preset = presets[name];
    if (preset) {
      setValues((prev) => (prev ? { ...prev, ...preset, presetName: name } : prev));
    }
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="px-4 py-3 border-b">
        <h3 className="text-sm font-medium">Detection Config</h3>
      </div>

      {/* Presets */}
      <div className="flex gap-2 px-4 py-3">
        {Object.keys(presets).map((name) => (
          <Button
            key={name}
            variant={values.presetName === name ? "default" : "outline"}
            size="sm"
            className="flex-1 capitalize text-xs"
            onClick={() => applyPreset(name)}
          >
            {name}
          </Button>
        ))}
      </div>

      {/* Parameters */}
      <Accordion type="multiple" defaultValue={params.map((p) => p.key)} className="px-4">
        {params.map((param) => (
          <AccordionItem key={param.key} value={param.key}>
            <AccordionTrigger className="text-xs py-3">
              <span className="flex-1 text-left">{param.label}</span>
              <span className="mr-2 text-xs font-mono text-muted-foreground">
                {param.step < 1
                  ? (values[param.key] as number).toFixed(1)
                  : values[param.key]}
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <div className="flex items-center gap-3">
                <Slider
                  value={[values[param.key] as number]}
                  min={param.min}
                  max={param.max}
                  step={param.step}
                  onValueChange={([val]) => updateValue(param.key, val)}
                  className="flex-1"
                />
                <Input
                  type="number"
                  value={values[param.key] as number}
                  min={param.min}
                  max={param.max}
                  step={param.step}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    if (!isNaN(val) && val >= param.min && val <= param.max) {
                      updateValue(param.key, val);
                    }
                  }}
                  className="w-16 h-8 text-xs text-center"
                />
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      {/* Actions */}
      <div className="px-4 py-3 mt-auto space-y-2 border-t">
        <Button
          className="w-full"
          size="sm"
          onClick={() => saveMutation.mutate(values)}
          disabled={saveMutation.isPending}
        >
          {saveMutation.isPending ? "Saving..." : "Apply"}
        </Button>
        <Button
          variant="outline"
          className="w-full"
          size="sm"
          onClick={() => resetMutation.mutate()}
          disabled={resetMutation.isPending}
        >
          {resetMutation.isPending ? "Resetting..." : "Reset to Defaults"}
        </Button>
      </div>
    </div>
  );
}

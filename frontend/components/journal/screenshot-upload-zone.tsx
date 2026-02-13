"use client";

import { useState } from "react";
import { Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

interface ScreenshotUploadZoneProps {
  screenshots: string[];
}

export function ScreenshotUploadZone({ screenshots: initial }: ScreenshotUploadZoneProps) {
  const [screenshots, setScreenshots] = useState<string[]>(initial);

  function handleRemove(index: number) {
    setScreenshots((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-3">
      <Label>Screenshots</Label>
      <div className="flex min-h-[80px] items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 px-4 py-6 transition-colors hover:border-muted-foreground/50">
        <div className="text-center">
          <Upload className="mx-auto h-6 w-6 text-muted-foreground/50" />
          <p className="mt-1 text-sm text-muted-foreground">
            Click to upload or drag files here
          </p>
          <p className="text-xs text-muted-foreground/60">
            PNG, JPG up to 5MB
          </p>
        </div>
      </div>
      {screenshots.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {screenshots.map((url, i) => (
            <div
              key={i}
              className="group relative h-16 w-16 overflow-hidden rounded-md border bg-muted"
            >
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                IMG
              </div>
              <Button
                variant="destructive"
                size="sm"
                className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 opacity-0 group-hover:opacity-100"
                onClick={() => handleRemove(i)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

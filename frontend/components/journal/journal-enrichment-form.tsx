"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Trade } from "@/types/journal";

interface JournalEnrichmentFormProps {
  trade: Trade;
}

const EMOTIONS = [
  { value: "calm", label: "Calm" },
  { value: "confident", label: "Confident" },
  { value: "anxious", label: "Anxious" },
  { value: "fomo", label: "FOMO" },
  { value: "revenge", label: "Revenge" },
  { value: "neutral", label: "Neutral" },
];

const QUALITIES = [
  { value: "textbook", label: "Textbook" },
  { value: "acceptable", label: "Acceptable" },
  { value: "forced", label: "Forced" },
];

export function JournalEnrichmentForm({ trade }: JournalEnrichmentFormProps) {
  const [rating, setRating] = useState(trade.rating ?? 0);
  const [emotion, setEmotion] = useState(trade.emotionalState ?? "");
  const [quality, setQuality] = useState(trade.setupQuality ?? "");
  const [notes, setNotes] = useState(trade.notes ?? "");
  const [tags, setTags] = useState(trade.tags.join(", "));

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Rating</Label>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star === rating ? 0 : star)}
              className="p-0.5"
            >
              <Star
                className={cn(
                  "h-5 w-5 transition-colors",
                  star <= rating
                    ? "fill-yellow-400 text-yellow-400"
                    : "text-muted-foreground/30 hover:text-yellow-400/50"
                )}
              />
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Emotional State</Label>
        <Select value={emotion} onValueChange={setEmotion}>
          <SelectTrigger>
            <SelectValue placeholder="Select emotion" />
          </SelectTrigger>
          <SelectContent>
            {EMOTIONS.map((e) => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Setup Quality</Label>
        <Select value={quality} onValueChange={setQuality}>
          <SelectTrigger>
            <SelectValue placeholder="Select quality" />
          </SelectTrigger>
          <SelectContent>
            {QUALITIES.map((q) => (
              <SelectItem key={q.value} value={q.value}>
                {q.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Notes</Label>
        <Textarea
          placeholder="Add trade notes (supports markdown)..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
        />
        <p className="text-xs text-muted-foreground">Supports markdown</p>
      </div>

      <div className="space-y-2">
        <Label>Tags</Label>
        <Input
          placeholder="Enter tags, comma-separated"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
        />
      </div>

      <p className="text-xs text-muted-foreground italic">
        Auto-save enabled
      </p>
    </div>
  );
}

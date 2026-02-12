import { cn } from "@/lib/utils";

type AlertStatus = "watching" | "near" | "triggered";

const statusStyles: Record<AlertStatus, string> = {
  watching: "text-muted-foreground border-border",
  near: "text-amber-500 border-amber-300 animate-pulse-alert",
  triggered: "text-red-500 bg-red-50 border-red-200",
};

interface AlertStatusBadgeProps {
  status: AlertStatus;
  className?: string;
}

export function AlertStatusBadge({ status, className }: AlertStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize",
        statusStyles[status],
        className
      )}
    >
      {status}
    </span>
  );
}

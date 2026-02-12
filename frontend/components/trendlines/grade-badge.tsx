import { cn } from "@/lib/utils";
import type { TrendlineGrade } from "@/types/trendline";

const gradeStyles: Record<string, string> = {
  "A+": "bg-amber-100 text-amber-600",
  A: "bg-blue-100 text-blue-500",
  B: "bg-gray-100 text-gray-500",
};

interface GradeBadgeProps {
  grade: TrendlineGrade | null;
  className?: string;
}

export function GradeBadge({ grade, className }: GradeBadgeProps) {
  if (!grade) {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold bg-gray-100 text-gray-400",
          className
        )}
      >
        --
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        gradeStyles[grade],
        className
      )}
    >
      {grade}
    </span>
  );
}

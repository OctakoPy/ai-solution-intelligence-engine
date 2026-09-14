import { cn } from "@/lib/utils";
import { LANGUAGE_LABELS, type Language } from "@/lib/types";

export interface LanguageBadgeProps {
  language?: Language;
  className?: string;
}

const COLORS: Record<Language, string> = {
  en: "bg-gray-100 text-gray-600",
  bm: "bg-amber-100 text-amber-700",
  zh: "bg-red-100 text-red-700",
};

export function LanguageBadge({ language, className }: LanguageBadgeProps) {
  if (!language || language === "en" || !LANGUAGE_LABELS[language]) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        COLORS[language],
        className,
      )}
      title={language === "bm" ? "Bahasa Malaysia" : "Chinese"}
    >
      {LANGUAGE_LABELS[language]}
    </span>
  );
}

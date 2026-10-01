import { cn } from "@/lib/utils";
import { LANGUAGE_LABELS, type Language } from "@/lib/types";

export interface LanguageBadgeProps {
  language?: Language;
  className?: string;
}

const LANGUAGE_TITLES: Record<Exclude<Language, "en">, string> = {
  bm: "Bahasa Malaysia",
  zh: "Chinese",
  ja: "Japanese",
};

/**
 * Every language gets the same neutral chip.
 *
 * These were semantic hues once: amber for Bahasa Malaysia and red for
 * Chinese, so a Chinese result carried the same hue as a rejected record. In
 * a product whose pitch is that one search crosses languages, the Chinese
 * badge reading as an error worked against the claim. Distinct hues per
 * language also imply an order that does not exist.
 *
 * The label does the identifying, so colour carries no meaning here and stays
 * out of the way.
 */
const CHIP = "bg-gray-100 text-gray-700";

export function LanguageBadge({ language, className }: LanguageBadgeProps) {
  if (!language || language === "en" || !LANGUAGE_LABELS[language]) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        CHIP,
        className,
      )}
      title={LANGUAGE_TITLES[language]}
    >
      {LANGUAGE_LABELS[language]}
    </span>
  );
}

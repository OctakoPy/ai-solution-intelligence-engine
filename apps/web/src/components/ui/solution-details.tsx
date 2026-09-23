import { useState } from "react";
import { Languages } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RetrievedSolution } from "@/lib/types";
import { LanguageBadge } from "./language-badge";
import { WhyPanel } from "./why-panel";

export interface SolutionDetailsProps {
  solution: RetrievedSolution;
  className?: string;
}

export function hasEnglishTranslation(s: RetrievedSolution): boolean {
  return !!(
    s.language &&
    s.language !== "en" &&
    (s.english_title || s.english_description || s.english_resolution)
  );
}

export function SolutionDetails({ solution, className }: SolutionDetailsProps) {
  const [translated, setTranslated] = useState(false);
  const showTranslate = hasEnglishTranslation(solution);

  const title = translated && solution.english_title ? solution.english_title : solution.title;
  const description =
    translated && solution.english_description
      ? solution.english_description
      : solution.description;
  const resolution =
    translated && solution.english_resolution
      ? solution.english_resolution
      : solution.resolution;

  return (
    <div className={cn("mt-3 space-y-2 border-t border-gray-100 pt-3 animate-expand", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-900">
          {showTranslate && translated ? "English Translation" : "Details"}
        </p>
        <div className="flex items-center gap-2">
          {showTranslate && (
            <button
              onClick={() => setTranslated((t) => !t)}
              className="inline-flex items-center gap-1 rounded-md border border-blue-600 px-2 py-0.5 text-sm font-semibold text-blue-600 hover:bg-blue-50"
            >
              <Languages className="h-3.5 w-3.5" />
              {translated ? "Show Original" : "Translate to English"}
            </button>
          )}
        </div>
      </div>

      <div className="mb-1 flex items-center gap-1.5">
        <LanguageBadge language={solution.language} />
        <p className="text-sm font-medium text-gray-500">Title</p>
      </div>
      <p className="text-base font-semibold text-gray-900">{title}</p>

      <p className="text-sm font-medium text-gray-500">Description</p>
      <p className="text-base text-gray-700 whitespace-pre-wrap">{description}</p>

      <p className="pt-1 text-sm font-medium text-gray-500">Resolution</p>
      <p className="text-base text-gray-700 whitespace-pre-wrap">{resolution}</p>

      <WhyPanel solution={solution} className="mt-2" />
    </div>
  );
}

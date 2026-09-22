export type SourceType = "ticket" | "sap_note" | "sharepoint_doc" | "kb_article";

export type CheckResult = "pass" | "flag" | "reject";

export type CheckStage = "source" | "stage1" | "judge" | "duplicate";

export type Outcome = "added" | "rejected" | "flagged";

export type Language = "en" | "bm" | "zh";

export const LANGUAGE_LABELS: Record<Language, string> = {
  en: "EN",
  bm: "BM",
  zh: "中文",
};

export interface Check {
  stage: "stage1" | "judge" | "duplicate";
  label: string;
  result: CheckResult;
  score: number | null;
  detail: string;
}

export interface View {
  id: string;
  source_type: SourceType;
  source_icon: string;
  source_label: string;
  title: string;
  category: string;
  date: string;
  description: string;
  resolution: string;
  outcome: Outcome;
  reason: string;
  checks: Check[];
  language?: Language;
}

export type Signal = "error_code" | "module" | "environment";

export interface SearchContext {
  error_code?: string;
  module?: string;
  environment?: string;
}

export interface RetrievedSolution {
  id: string;
  title: string;
  source: string;
  category: string;
  score: number;
  confidence: number;
  description: string;
  resolution: string;
  date: string;
  language?: Language;
  english_title?: string;
  english_description?: string;
  english_resolution?: string;
  signals?: Signal[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  timestamp: string | null;
}

export interface OverviewCategoryRow {
  name: string;
  count: number;
}

export interface OverviewImpactRow {
  label: string;
  before: string;
  after: string;
  delta: string;
}

export interface OverviewRecentRow {
  source: string;
  title: string;
  category: string;
  status: string;
  time_label: string;
}

export interface OverviewFlaggedRow {
  id: string;
  title: string;
  category: string;
  source: string;
  reason: string;
}

export interface OverviewCategoryTimeRow {
  name: string;
  avg_time: string;
}

export interface OverviewResponse {
  processed: number;
  added: number;
  rejected: number;
  flagged_count: number;
  avg_time: string;
  top_categories: OverviewCategoryRow[];
  before_after: OverviewImpactRow[];
  recent: OverviewRecentRow[];
  flagged: OverviewFlaggedRow[];
  resolution_by_category: OverviewCategoryTimeRow[];
}

export interface IngestResponse {
  ingested: number;
  rejected: number;
  total: number;
}

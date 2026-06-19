const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type HealthResponse = {
  status: string;
  database: string;
  kis: { status: string; configured: boolean; smoke?: { status: string } };
  news_configured: boolean;
  llm?: { provider: string; configured: boolean; model: string };
  llm_configured: boolean;
};

export type StockEvent = {
  id?: string;
  trade_date: string;
  stock: { code: string; name?: string; market?: string };
  event_types: string[];
  price?: number;
  change_rate?: number;
  volume?: number;
  source: string;
};

export type Article = {
  id?: string;
  title: string;
  url: string;
  publisher?: string;
  published_at?: string;
  summary?: string;
};

export type AnalysisReport = {
  id?: string;
  stock: { code: string; name?: string };
  base_date: string;
  report_type: string;
  summary: string;
  key_points: string[];
  possible_reasons: string[];
  risks: string[];
  confidence: string;
  sources: string[];
  article_urls: string[];
};

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchApi("/api/health");
}

export async function getScreenerEvents(params: {
  start_date: string;
  end_date: string;
  min_volume: number;
  include_upper_limit: boolean;
}): Promise<{ events: StockEvent[]; total: number }> {
  const q = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
    min_volume: String(params.min_volume),
    include_upper_limit: String(params.include_upper_limit),
  });
  return fetchApi(`/api/screener/events?${q}`);
}

export function screenerCsvUrl(params: {
  start_date: string;
  end_date: string;
  min_volume: number;
  include_upper_limit: boolean;
}): string {
  const q = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
    min_volume: String(params.min_volume),
    include_upper_limit: String(params.include_upper_limit),
  });
  return `${API_URL}/api/screener/events/export.csv?${q}`;
}

export async function searchNews(params: {
  stock_code: string;
  stock_name?: string;
  base_date: string;
}): Promise<{ articles: Article[]; total: number; cached: boolean }> {
  const q = new URLSearchParams({
    stock_code: params.stock_code,
    base_date: params.base_date,
  });
  if (params.stock_name) q.set("stock_name", params.stock_name);
  return fetchApi(`/api/news/search?${q}`);
}

export async function refreshNews(body: {
  stock_code: string;
  stock_name?: string;
  base_date: string;
}): Promise<{ articles: Article[]; total: number }> {
  return fetchApi("/api/news/refresh", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function createNewsPriceReport(body: {
  stock_code: string;
  stock_name?: string;
  base_date: string;
  article_ids: string[];
  screener_event?: StockEvent;
}): Promise<{ report: AnalysisReport }> {
  return fetchApi("/api/reports/news-price", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getReport(reportId: string): Promise<AnalysisReport> {
  return fetchApi(`/api/reports/${reportId}`);
}

// --- Agent endpoints (Phase 2~5) ---

export type MarketBriefing = {
  base_date: string;
  timeline: "PRE_MARKET" | "INTRADAY" | "CLOSE";
  label: string;
  content: {
    headline: string;
    market_summary: string;
    key_narratives: string[];
    sector_highlights: string[];
    watch_items: string[];
    risks: string[];
    confidence: string;
  };
  sources: string[];
};

// 시장 판단 에이전트: 타임라인별 종합 시황 브리핑
export async function createBriefing(body: {
  base_date: string;
  timeline?: "PRE_MARKET" | "INTRADAY" | "CLOSE";
  articles?: Article[];
}): Promise<{ briefing: MarketBriefing }> {
  return fetchApi("/api/briefing", {
    method: "POST",
    body: JSON.stringify({ timeline: "CLOSE", articles: [], ...body }),
  });
}

// 전략 에이전트: 상한가/거래량 종목 인과관계 분석
export async function analyzeCausality(body: {
  event: StockEvent;
  articles?: Article[];
  candles?: { date: string; close: number; volume?: number }[];
}): Promise<{ report: AnalysisReport; canslim: unknown }> {
  return fetchApi("/api/strategy/causality", {
    method: "POST",
    body: JSON.stringify({ articles: [], candles: [], ...body }),
  });
}

// 모니터링 에이전트: 장마감 일일 리포트 트리거
export async function runDailyReport(body: {
  base_date: string;
  session?: "KR_DAY" | "US_NIGHT" | "GLOBAL";
  events?: StockEvent[];
}): Promise<{ digest: unknown; telegram: unknown; persisted: boolean }> {
  return fetchApi("/api/monitor/daily-report", {
    method: "POST",
    body: JSON.stringify({ session: "KR_DAY", events: [], ...body }),
  });
}

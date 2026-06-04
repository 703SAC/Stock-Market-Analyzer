"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  searchNews,
  refreshNews,
  createNewsPriceReport,
  type Article,
  type StockEvent,
} from "@/lib/api";

function addDays(dateStr: string, delta: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  dt.setDate(dt.getDate() + delta);
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  const dd = String(dt.getDate()).padStart(2, "0");
  return `${dt.getFullYear()}-${mm}-${dd}`;
}

function NewsContent() {
  const params = useSearchParams();
  const router = useRouter();
  const [stockCode, setStockCode] = useState(params.get("stock_code") || "");
  const [stockName, setStockName] = useState(params.get("stock_name") || "");
  const [baseDate, setBaseDate] = useState(
    params.get("base_date") || new Date().toISOString().slice(0, 10)
  );
  const [tab, setTab] = useState<"base" | "prev">("base");
  const [articles, setArticles] = useState<Article[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [cached, setCached] = useState(false);

  const displayDate = tab === "base" ? baseDate : addDays(baseDate, -1);

  const loadNews = useCallback(async () => {
    if (!stockCode) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchNews({
        stock_code: stockCode,
        stock_name: stockName || undefined,
        base_date: displayDate,
      });
      setArticles(res.articles);
      setCached(res.cached);
      setSearched(true);
      setSelected(new Set(res.articles.slice(0, 3).map((a) => a.id || a.url)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "검색 실패");
    } finally {
      setLoading(false);
    }
  }, [stockCode, stockName, displayDate]);

  useEffect(() => {
    if (stockCode) loadNews();
  }, [stockCode, displayDate, loadNews]);

  function toggleArticle(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  }

  async function handleRefresh() {
    setLoading(true);
    try {
      const res = await refreshNews({
        stock_code: stockCode,
        stock_name: stockName || undefined,
        base_date: displayDate,
      });
      setArticles(res.articles);
      setCached(false);
      setSearched(true);
      setSelected(new Set(res.articles.slice(0, 3).map((a) => a.id || a.url)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "새로고침 실패");
    } finally {
      setLoading(false);
    }
  }

  async function handleReport() {
    setReportLoading(true);
    setError(null);
    try {
      const screenerEvent: StockEvent | undefined =
        params.get("from_screener") === "1"
          ? {
              trade_date: baseDate,
              stock: { code: stockCode, name: stockName },
              event_types: ["HIGH_VOLUME"],
              source: "screener",
            }
          : undefined;

      const res = await createNewsPriceReport({
        stock_code: stockCode,
        stock_name: stockName || undefined,
        base_date: baseDate,
        article_ids: Array.from(selected),
        screener_event: screenerEvent,
      });
      router.push(`/reports?id=${res.report.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "보고서 생성 실패");
    } finally {
      setReportLoading(false);
    }
  }

  return (
    <div>
      <h1>종목 기사 검색</h1>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>종목코드</label>
            <input
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              placeholder="005930"
            />
          </div>
          <div className="form-group">
            <label>종목명</label>
            <input
              value={stockName}
              onChange={(e) => setStockName(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>기준일</label>
            <input
              type="date"
              value={baseDate}
              onChange={(e) => setBaseDate(e.target.value)}
            />
          </div>
          <button type="button" onClick={loadNews} disabled={loading}>
            검색
          </button>
          <button type="button" onClick={handleRefresh} disabled={loading}>
            캐시 무시
          </button>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={() => setTab("base")}
            style={{
              background: tab === "base" ? "var(--accent)" : "var(--border)",
            }}
          >
            기준일 ({baseDate})
          </button>
          <button
            type="button"
            onClick={() => setTab("prev")}
            style={{
              background: tab === "prev" ? "var(--accent)" : "var(--border)",
            }}
          >
            전일 ({displayDate})
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">로딩...</p>}

      {searched && !loading && articles.length === 0 && (
        <div className="card">
          <p style={{ margin: 0, color: "var(--muted)" }}>
            {displayDate} 기준 최근 7일 안에 해당하는 기사가 없습니다.
            {cached ? " (캐시)" : ""} 다른 날짜를 선택하거나 「캐시 무시」로 다시
            검색해 보세요.
          </p>
        </div>
      )}

      {articles.length > 0 && (
        <div className="card">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: "1rem",
            }}
          >
            <span>
              {articles.length}건 · {displayDate} ±7일
              {cached ? " (캐시)" : ""}
            </span>
            <button
              type="button"
              onClick={handleReport}
              disabled={reportLoading || selected.size === 0}
            >
              {reportLoading ? "생성 중..." : "LLM 보고서 생성"}
            </button>
          </div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {articles.map((a) => {
              const aid = a.id || a.url;
              return (
                <li
                  key={aid}
                  style={{
                    borderBottom: "1px solid var(--border)",
                    padding: "0.75rem 0",
                  }}
                >
                  <label style={{ display: "flex", gap: "0.5rem" }}>
                    <input
                      type="checkbox"
                      checked={selected.has(aid)}
                      onChange={() => toggleArticle(aid)}
                    />
                    <div>
                      <a href={a.url} target="_blank" rel="noreferrer">
                        {a.title}
                      </a>
                      <div
                        style={{
                          fontSize: "0.8rem",
                          color: "var(--muted)",
                        }}
                      >
                        {a.publisher} · {a.published_at?.slice(0, 16) || ""}
                      </div>
                      {a.summary && (
                        <p style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
                          {a.summary.slice(0, 120)}...
                        </p>
                      )}
                    </div>
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function NewsPage() {
  return (
    <Suspense fallback={<p className="loading">로딩...</p>}>
      <NewsContent />
    </Suspense>
  );
}

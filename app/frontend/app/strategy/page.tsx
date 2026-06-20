"use client";

import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  analyzeCausality,
  type AnalysisReport,
  type Article,
  type CanSlimResult,
  type StockEvent,
} from "@/lib/api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function addDays(dateStr: string, delta: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  dt.setDate(dt.getDate() + delta);
  return dt.toISOString().slice(0, 10);
}

function sampleCandles(baseDate: string) {
  return Array.from({ length: 90 }, (_, i) => {
    const drift = i * 120;
    const pulse = i > 72 ? (i - 72) * 240 : 0;
    return {
      date: addDays(baseDate, i - 89),
      close: 62000 + drift + pulse,
      volume: i > 78 ? 18_000_000 + i * 50_000 : 6_000_000 + i * 25_000,
    };
  });
}

function parseArticles(text: string, stockName: string): Article[] {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length === 0) {
    return [
      {
        title: `${stockName || "해당 종목"} 거래량 급증`,
        url: "manual://strategy/sample-1",
        publisher: "manual",
        summary: "수급 개선과 업종 모멘텀이 동시에 관찰됐다.",
      },
    ];
  }
  return lines.map((line, index) => ({
    title: line,
    url: `manual://strategy/${index + 1}`,
    publisher: "manual",
    summary: line,
  }));
}

function StrategyContent() {
  const params = useSearchParams();
  const [tradeDate, setTradeDate] = useState(params.get("trade_date") || todayStr());
  const [stockCode, setStockCode] = useState(params.get("stock_code") || "005930");
  const [stockName, setStockName] = useState(params.get("stock_name") || "삼성전자");
  const [eventType, setEventType] = useState(params.get("event_type") || "HIGH_VOLUME");
  const [price, setPrice] = useState(Number(params.get("price") || 75000));
  const [changeRate, setChangeRate] = useState(Number(params.get("change_rate") || 3.2));
  const [volume, setVolume] = useState(Number(params.get("volume") || 20_000_000));
  const [articleText, setArticleText] = useState("");
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [canslim, setCanslim] = useState<CanSlimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const candles = useMemo(() => sampleCandles(tradeDate), [tradeDate]);

  async function handleAnalyze() {
    const event: StockEvent = {
      trade_date: tradeDate,
      stock: { code: stockCode, name: stockName },
      event_types: [eventType],
      price,
      change_rate: changeRate,
      volume,
      source: "frontend",
    };

    setLoading(true);
    setError(null);
    try {
      const res = await analyzeCausality({
        event,
        articles: parseArticles(articleText, stockName),
        candles,
      });
      setReport(res.report);
      setCanslim(res.canslim);
    } catch (e) {
      setError(e instanceof Error ? e.message : "전략 분석 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <h1>전략 에이전트</h1>
        <p className="muted">특징주 이벤트와 기사, 차트 데이터를 합쳐 인과관계를 분석합니다.</p>
      </div>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>거래일</label>
            <input type="date" value={tradeDate} onChange={(e) => setTradeDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>종목코드</label>
            <input value={stockCode} onChange={(e) => setStockCode(e.target.value)} />
          </div>
          <div className="form-group">
            <label>종목명</label>
            <input value={stockName} onChange={(e) => setStockName(e.target.value)} />
          </div>
          <div className="form-group">
            <label>이벤트</label>
            <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
              <option value="HIGH_VOLUME">거래량 급증</option>
              <option value="UPPER_LIMIT">상한가</option>
              <option value="CONDITION_MATCH">조건식 매칭</option>
            </select>
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>가격</label>
            <input type="number" value={price} onChange={(e) => setPrice(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>등락률</label>
            <input
              type="number"
              step="0.1"
              value={changeRate}
              onChange={(e) => setChangeRate(Number(e.target.value))}
            />
          </div>
          <div className="form-group">
            <label>거래량</label>
            <input type="number" value={volume} onChange={(e) => setVolume(Number(e.target.value))} />
          </div>
          <button type="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? "분석 중..." : "인과분석 실행"}
          </button>
        </div>
        <label className="muted" htmlFor="strategy-articles">
          참고 기사
        </label>
        <textarea
          id="strategy-articles"
          value={articleText}
          onChange={(e) => setArticleText(e.target.value)}
          placeholder="한 줄에 기사나 관찰 내용을 하나씩 입력"
        />
      </div>

      {error && <p className="error">{error}</p>}

      {(report || canslim) && (
        <div className="grid">
          {report && (
            <div className="card">
              <h2 className="section-title">{report.stock.name || report.stock.code}</h2>
              <span className="badge badge-ok">{report.confidence}</span>
              <p>{report.summary}</p>
              <h3>가능한 이유</h3>
              <ul className="list">
                {report.possible_reasons.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <h3>리스크</h3>
              <ul className="list">
                {report.risks.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {canslim && (
            <div className="card">
              <h2 className="section-title">CAN SLIM 정량</h2>
              <p>
                <span className={`badge ${canslim.passed ? "badge-ok" : "badge-warn"}`}>
                  {canslim.score}/{canslim.max_score}
                </span>
              </p>
              {Object.entries(canslim.checks).map(([key, ok]) => (
                <div className="metric-row" key={key}>
                  <span>{key}</span>
                  <span className={`badge ${ok ? "badge-ok" : "badge-warn"}`}>
                    {ok ? "PASS" : "CHECK"}
                  </span>
                </div>
              ))}
              {canslim.pending_fundamentals.length > 0 && (
                <p className="muted">DART 연동 후 평가: {canslim.pending_fundamentals.join(", ")}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function StrategyPage() {
  return (
    <Suspense fallback={<p className="loading">로딩...</p>}>
      <StrategyContent />
    </Suspense>
  );
}


"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  analyzeCausality,
  searchNews,
  type AnalysisReport,
  type Article,
  type CanSlimResult,
  type StockEvent,
} from "@/lib/api";
import { ReportView } from "@/components/ReportView";
import { CanSlimPanel } from "@/components/CanSlimPanel";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function StrategyContent() {
  const params = useSearchParams();
  const [stockCode, setStockCode] = useState(params.get("stock_code") || "");
  const [stockName, setStockName] = useState(params.get("stock_name") || "");
  const [baseDate, setBaseDate] = useState(params.get("base_date") || todayStr());
  const [volume, setVolume] = useState<string>(params.get("volume") || "");
  const [changeRate, setChangeRate] = useState<string>(params.get("change_rate") || "");
  const [price, setPrice] = useState<string>(params.get("price") || "");
  const initialTypes = (params.get("event_types") || "HIGH_VOLUME").split(",");
  const [highVol, setHighVol] = useState(initialTypes.includes("HIGH_VOLUME"));
  const [upper, setUpper] = useState(initialTypes.includes("UPPER_LIMIT"));
  const [attachNews, setAttachNews] = useState(true);

  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [canslim, setCanslim] = useState<CanSlimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (!stockCode) {
      setError("종목코드를 입력하세요.");
      return;
    }
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const eventTypes: string[] = [];
      if (highVol) eventTypes.push("HIGH_VOLUME");
      if (upper) eventTypes.push("UPPER_LIMIT");

      let articles: Article[] = [];
      if (attachNews) {
        try {
          const res = await searchNews({
            stock_code: stockCode,
            stock_name: stockName || undefined,
            base_date: baseDate,
          });
          articles = res.articles.slice(0, 5);
        } catch {
          // 뉴스 실패해도 분석은 진행(가격/맥락 기반)
        }
      }

      const event: StockEvent = {
        trade_date: baseDate,
        stock: { code: stockCode, name: stockName || undefined },
        event_types: eventTypes,
        volume: volume ? Number(volume) : undefined,
        change_rate: changeRate ? Number(changeRate) : undefined,
        price: price ? Number(price) : undefined,
        source: "manual",
      };

      const res = await analyzeCausality({ event, articles });
      setReport(res.report);
      setCanslim(res.canslim);
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>전략 에이전트 · 인과관계 분석</h1>
      <p className="muted">
        상한가/거래량 폭발 종목의 인과(테마·일정·그룹사)를 정량(CAN SLIM)+맥락+뉴스로 분석합니다.
      </p>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>종목코드</label>
            <input value={stockCode} onChange={(e) => setStockCode(e.target.value)} placeholder="005930" />
          </div>
          <div className="form-group">
            <label>종목명</label>
            <input value={stockName} onChange={(e) => setStockName(e.target.value)} />
          </div>
          <div className="form-group">
            <label>관찰일</label>
            <input type="date" value={baseDate} onChange={(e) => setBaseDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>거래량</label>
            <input type="number" value={volume} onChange={(e) => setVolume(e.target.value)} />
          </div>
          <div className="form-group">
            <label>등락률(%)</label>
            <input type="number" value={changeRate} onChange={(e) => setChangeRate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>종가</label>
            <input type="number" value={price} onChange={(e) => setPrice(e.target.value)} />
          </div>
        </div>
        <div className="form-row">
          <label>
            <input type="checkbox" checked={highVol} onChange={(e) => setHighVol(e.target.checked)} /> 거래량
          </label>
          <label>
            <input type="checkbox" checked={upper} onChange={(e) => setUpper(e.target.checked)} /> 상한가
          </label>
          <label>
            <input type="checkbox" checked={attachNews} onChange={(e) => setAttachNews(e.target.checked)} /> 관련 기사 자동 첨부
          </label>
          <button type="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? "분석 중..." : "분석 실행"}
          </button>
        </div>
        <p className="notice">CAN SLIM 정량평가는 일봉 데이터 연동 시 활성화됩니다(현재는 가격·맥락·뉴스 기반).</p>
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">LLM 인과분석 생성 중...</p>}

      {report && (
        <>
          <CanSlimPanel canslim={canslim} />
          <ReportView report={report} />
        </>
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

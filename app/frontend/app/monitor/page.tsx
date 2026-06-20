"use client";

import { useState } from "react";
import {
  getScreenerEvents,
  runDailyReport,
  type DailyReportResult,
  type MarketSession,
} from "@/lib/api";
import { RawJsonToggle } from "@/components/RawJsonToggle";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

const SESSIONS: { key: MarketSession; label: string }[] = [
  { key: "KR_DAY", label: "국내장 마감" },
  { key: "US_NIGHT", label: "미국장 마감" },
];

function telegramBadge(status: string) {
  const cls =
    status === "sent" ? "badge-ok" : status === "not_configured" ? "badge-warn" : "badge-warn";
  return <span className={`badge ${cls}`}>텔레그램 {status}</span>;
}

export default function MonitorPage() {
  const [baseDate, setBaseDate] = useState(todayStr());
  const [session, setSession] = useState<MarketSession>("KR_DAY");
  const [pullScreener, setPullScreener] = useState(true);
  const [result, setResult] = useState<DailyReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    setResult(null);
    setNote(null);
    try {
      let events: Awaited<ReturnType<typeof getScreenerEvents>>["events"] = [];
      if (pullScreener) {
        try {
          const res = await getScreenerEvents({
            start_date: baseDate,
            end_date: baseDate,
            min_volume: 10_000_000,
            include_upper_limit: true,
          });
          events = res.events;
          setNote(`스크리너 특징주 ${events.length}건을 로그로 첨부했습니다.`);
        } catch {
          setNote("스크리너 조회 실패 — 빈 로그로 진행합니다(KIS 미설정 가능).");
        }
      }
      const res = await runDailyReport({ base_date: baseDate, session, events });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "리포트 생성 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>모니터링 에이전트 · 장마감 일일 리포트</h1>
      <p className="muted">
        특징주 로그 → Gemini 일일 종합시황 → 맥락 저장소 역기록 → 텔레그램 발송.
      </p>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>기준일</label>
            <input type="date" value={baseDate} onChange={(e) => setBaseDate(e.target.value)} />
          </div>
        </div>
        <div className="tabs">
          {SESSIONS.map((s) => (
            <button
              key={s.key}
              type="button"
              className={`tab ${session === s.key ? "active" : ""}`}
              onClick={() => setSession(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
        <div className="form-row" style={{ marginTop: "1rem" }}>
          <label>
            <input
              type="checkbox"
              checked={pullScreener}
              onChange={(e) => setPullScreener(e.target.checked)}
            />{" "}
            스크리너 특징주 자동 첨부
          </label>
          <button type="button" onClick={handleRun} disabled={loading}>
            {loading ? "생성 중..." : "일일 리포트 실행"}
          </button>
        </div>
        {note && <p className="notice">{note}</p>}
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">일일 리포트 생성 중...</p>}

      {result && (
        <div className="card">
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <span className="muted">
              {result.digest.digest_date} · {result.digest.session}
            </span>
            {telegramBadge(result.telegram?.status || "unknown")}
            <span className={`badge ${result.persisted ? "badge-ok" : "badge-warn"}`}>
              {result.persisted ? "맥락저장소 기록됨" : "미저장"}
            </span>
          </div>
          <h2 style={{ marginBottom: "0.25rem" }}>{result.digest.title}</h2>
          <p>{result.digest.summary}</p>
          {result.digest.key_themes.length > 0 && (
            <p className="muted">테마: {result.digest.key_themes.join(", ")}</p>
          )}
          <RawJsonToggle data={result} />
          <p className="disclaimer">
            생성된 종합시황은 맥락 저장소에 기록되어 다음 거래일 브리핑·전략 분석에 주입됩니다.
          </p>
        </div>
      )}
    </div>
  );
}

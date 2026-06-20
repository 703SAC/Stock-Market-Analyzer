"use client";

import { useState } from "react";
import {
  getContextOverview,
  getStockContext,
  type CalendarEvent,
  type MarketContext,
  type MarketDigest,
  type MarketSession,
  type NarrativeMemory,
} from "@/lib/api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function ContextPage() {
  const [baseDate, setBaseDate] = useState(todayStr());
  const [session, setSession] = useState<MarketSession | "">("");
  const [stockCode, setStockCode] = useState("005930");
  const [digests, setDigests] = useState<MarketDigest[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [narratives, setNarratives] = useState<NarrativeMemory[]>([]);
  const [stockContext, setStockContext] = useState<MarketContext | null>(null);
  const [promptBlock, setPromptBlock] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadOverview() {
    setLoading(true);
    setError(null);
    try {
      const res = await getContextOverview({ base_date: baseDate, session });
      setDigests(res.digests);
      setEvents(res.events);
      setNarratives(res.narratives);
    } catch (e) {
      setError(e instanceof Error ? e.message : "맥락 조회 실패");
    } finally {
      setLoading(false);
    }
  }

  async function loadStockContext() {
    setLoading(true);
    setError(null);
    try {
      const res = await getStockContext({ base_date: baseDate, stock_code: stockCode });
      setStockContext(res.context);
      setPromptBlock(res.prompt_block);
    } catch (e) {
      setError(e instanceof Error ? e.message : "종목 맥락 조회 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <h1>맥락 저장소</h1>
        <p className="muted">모니터링이 쓴 기록이 브리핑과 전략 분석에 어떻게 재사용되는지 확인합니다.</p>
      </div>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>기준일</label>
            <input type="date" value={baseDate} onChange={(e) => setBaseDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>세션</label>
            <select value={session} onChange={(e) => setSession(e.target.value as MarketSession | "")}>
              <option value="">전체</option>
              <option value="KR_DAY">KR_DAY</option>
              <option value="US_NIGHT">US_NIGHT</option>
              <option value="GLOBAL">GLOBAL</option>
            </select>
          </div>
          <button type="button" onClick={loadOverview} disabled={loading}>
            개요 조회
          </button>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>종목코드</label>
            <input value={stockCode} onChange={(e) => setStockCode(e.target.value)} />
          </div>
          <button className="btn-secondary" type="button" onClick={loadStockContext} disabled={loading}>
            종목 맥락 조회
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="grid">
        <div className="card">
          <h2 className="section-title">종합시황</h2>
          {digests.length === 0 && <p className="loading">기록 없음</p>}
          <ul className="list">
            {digests.map((digest) => (
              <li key={digest.id || `${digest.digest_date}-${digest.session}`}>
                <strong>{digest.title || digest.digest_date}</strong>
                <br />
                <span className="muted">
                  {digest.digest_date} · {digest.session} · {digest.key_themes.join(", ") || "-"}
                </span>
                <br />
                {digest.summary}
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2 className="section-title">일정</h2>
          {events.length === 0 && <p className="loading">기록 없음</p>}
          <ul className="list">
            {events.map((event) => (
              <li key={event.id || `${event.event_date}-${event.title}`}>
                <strong>{event.title}</strong>
                <br />
                <span className="muted">
                  {event.event_date} · {event.category} · {event.stock_code || "시장"}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2 className="section-title">내러티브</h2>
          {narratives.length === 0 && <p className="loading">기록 없음</p>}
          <ul className="list">
            {narratives.map((narrative) => (
              <li key={narrative.id || narrative.topic}>
                <strong>{narrative.topic}</strong>
                <br />
                <span className="muted">
                  {narrative.as_of_date} · {narrative.importance} · {narrative.stock_codes.join(", ") || "시장"}
                </span>
                <br />
                {narrative.narrative}
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2 className="section-title">종목 맥락</h2>
          {!stockContext && <p className="loading">종목 맥락을 조회하세요.</p>}
          {stockContext && (
            <>
              <p>
                <strong>{stockContext.stock_code}</strong> · {stockContext.base_date}
              </p>
              <p className="muted">
                그룹: {stockContext.group?.group_name || "-"} · 피어 {stockContext.peer_group.length}개
              </p>
              <pre className="result-block">{promptBlock}</pre>
            </>
          )}
        </div>
      </div>
    </div>
  );
}


"use client";

import { useState } from "react";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { runDailyReport, type MarketDigest, type MarketSession, type StockEvent } from "@/lib/api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function defaultEvent(baseDate: string): StockEvent {
  return {
    trade_date: baseDate,
    stock: { code: "005930", name: "삼성전자" },
    event_types: ["HIGH_VOLUME"],
    price: 75000,
    change_rate: 3.2,
    volume: 20_000_000,
    source: "manual",
  };
}

function MonitorContent() {
  const params = useSearchParams();
  const initialDate = params.get("trade_date") || todayStr();
  const [baseDate, setBaseDate] = useState(initialDate);
  const [session, setSession] = useState<MarketSession>("KR_DAY");
  const [events, setEvents] = useState<StockEvent[]>([
    {
      ...defaultEvent(initialDate),
      stock: {
        code: params.get("stock_code") || "005930",
        name: params.get("stock_name") || "삼성전자",
      },
      event_types: [params.get("event_type") || "HIGH_VOLUME"],
      price: Number(params.get("price") || 75000),
      change_rate: Number(params.get("change_rate") || 3.2),
      volume: Number(params.get("volume") || 20_000_000),
    },
  ]);
  const [digest, setDigest] = useState<MarketDigest | null>(null);
  const [telegram, setTelegram] = useState<Record<string, unknown> | null>(null);
  const [persisted, setPersisted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateEvent(index: number, patch: Partial<StockEvent>) {
    setEvents((current) =>
      current.map((event, i) => (i === index ? { ...event, ...patch } : event))
    );
  }

  function updateStock(index: number, patch: Partial<StockEvent["stock"]>) {
    setEvents((current) =>
      current.map((event, i) =>
        i === index ? { ...event, stock: { ...event.stock, ...patch } } : event
      )
    );
  }

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const normalized = events.map((event) => ({ ...event, trade_date: baseDate }));
      const res = await runDailyReport({ base_date: baseDate, session, events: normalized });
      setDigest(res.digest);
      setTelegram(res.telegram);
      setPersisted(res.persisted);
    } catch (e) {
      setError(e instanceof Error ? e.message : "일일 리포트 생성 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <h1>모니터링 에이전트</h1>
        <p className="muted">특징주 로그를 장마감 종합시황으로 저장하고 알림 결과를 확인합니다.</p>
      </div>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>기준일</label>
            <input type="date" value={baseDate} onChange={(e) => setBaseDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>세션</label>
            <select value={session} onChange={(e) => setSession(e.target.value as MarketSession)}>
              <option value="KR_DAY">국장 마감</option>
              <option value="US_NIGHT">미장 마감</option>
              <option value="GLOBAL">글로벌</option>
            </select>
          </div>
          <button type="button" onClick={handleRun} disabled={loading}>
            {loading ? "생성 중..." : "일일 리포트 생성"}
          </button>
          <button
            className="btn-secondary"
            type="button"
            onClick={() => setEvents((current) => [...current, defaultEvent(baseDate)])}
          >
            이벤트 추가
          </button>
        </div>
      </div>

      <div className="card">
        <h2 className="section-title">특징주 이벤트</h2>
        <table>
          <thead>
            <tr>
              <th>코드</th>
              <th>종목명</th>
              <th>조건</th>
              <th>가격</th>
              <th>등락률</th>
              <th>거래량</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {events.map((event, index) => (
              <tr key={`${event.stock.code}-${index}`}>
                <td>
                  <input value={event.stock.code} onChange={(e) => updateStock(index, { code: e.target.value })} />
                </td>
                <td>
                  <input value={event.stock.name || ""} onChange={(e) => updateStock(index, { name: e.target.value })} />
                </td>
                <td>
                  <select
                    value={event.event_types[0] || "HIGH_VOLUME"}
                    onChange={(e) => updateEvent(index, { event_types: [e.target.value] })}
                  >
                    <option value="HIGH_VOLUME">거래량</option>
                    <option value="UPPER_LIMIT">상한가</option>
                    <option value="CONDITION_MATCH">조건식</option>
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    value={event.price || 0}
                    onChange={(e) => updateEvent(index, { price: Number(e.target.value) })}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    step="0.1"
                    value={event.change_rate || 0}
                    onChange={(e) => updateEvent(index, { change_rate: Number(e.target.value) })}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={event.volume || 0}
                    onChange={(e) => updateEvent(index, { volume: Number(e.target.value) })}
                  />
                </td>
                <td>
                  <button
                    className="btn-secondary"
                    type="button"
                    onClick={() => setEvents((current) => current.filter((_, i) => i !== index))}
                    disabled={events.length === 1}
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {error && <p className="error">{error}</p>}

      {digest && (
        <div className="grid">
          <div className="card">
            <h2 className="section-title">{digest.title || "일일 리포트"}</h2>
            <p className="muted">
              {digest.digest_date} · {digest.session} ·{" "}
              <span className={`badge ${persisted ? "badge-ok" : "badge-warn"}`}>
                {persisted ? "저장됨" : "미저장"}
              </span>
            </p>
            <p>{digest.summary}</p>
            <p className="muted">테마: {digest.key_themes.join(", ") || "-"}</p>
          </div>
          <div className="card">
            <h2 className="section-title">Telegram</h2>
            <pre className="result-block">{JSON.stringify(telegram, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MonitorPage() {
  return (
    <Suspense fallback={<p className="loading">로딩...</p>}>
      <MonitorContent />
    </Suspense>
  );
}

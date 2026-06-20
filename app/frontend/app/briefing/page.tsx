"use client";

import { useState } from "react";
import { createBriefing, type MarketBriefing } from "@/lib/api";
import { ConfidenceBadge, SourceChips } from "@/components/ConfidenceBadge";
import { RawJsonToggle } from "@/components/RawJsonToggle";

type Timeline = "PRE_MARKET" | "INTRADAY" | "CLOSE";
const TABS: { key: Timeline; label: string }[] = [
  { key: "PRE_MARKET", label: "장 시작 전" },
  { key: "INTRADAY", label: "장중" },
  { key: "CLOSE", label: "장 마감" },
];

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function List({ title, items }: { title: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <>
      <h3>{title}</h3>
      <ul className="list-tight">
        {items.map((p, i) => (
          <li key={i}>{p}</li>
        ))}
      </ul>
    </>
  );
}

export default function BriefingPage() {
  const [baseDate, setBaseDate] = useState(todayStr());
  const [timeline, setTimeline] = useState<Timeline>("CLOSE");
  const [briefing, setBriefing] = useState<MarketBriefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setBriefing(null);
    try {
      const res = await createBriefing({ base_date: baseDate, timeline });
      setBriefing(res.briefing);
    } catch (e) {
      setError(e instanceof Error ? e.message : "브리핑 생성 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>시장 판단 에이전트 · 메가 내러티브 브리핑</h1>
      <p className="muted">
        누적 맥락(종합시황·일정·그룹사·내러티브)을 주입해 타임라인별 &lsquo;숲&rsquo;을 봅니다.
      </p>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>기준일</label>
            <input type="date" value={baseDate} onChange={(e) => setBaseDate(e.target.value)} />
          </div>
        </div>
        <div className="tabs">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              className={`tab ${timeline === t.key ? "active" : ""}`}
              onClick={() => setTimeline(t.key)}
            >
              {t.label}
            </button>
          ))}
          <button type="button" onClick={handleGenerate} disabled={loading}>
            {loading ? "생성 중..." : "브리핑 생성"}
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">브리핑 생성 중...</p>}

      {briefing && (
        <div className="card">
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <span className="muted">
              {briefing.label} · {briefing.base_date}
            </span>
            <ConfidenceBadge value={briefing.content.confidence} />
          </div>
          <h2 style={{ marginBottom: "0.25rem" }}>{briefing.content.headline}</h2>
          <p>{briefing.content.market_summary}</p>

          <List title="핵심 내러티브" items={briefing.content.key_narratives} />
          <List title="섹터 하이라이트" items={briefing.content.sector_highlights} />
          <List title="점검 포인트" items={briefing.content.watch_items} />
          <List title="리스크" items={briefing.content.risks} />

          <div style={{ marginTop: "0.5rem" }}>
            <SourceChips sources={briefing.sources} />
          </div>
          <RawJsonToggle data={briefing} />
          <p className="disclaimer">투자 조언이 아닌 관찰 브리핑입니다.</p>
        </div>
      )}
    </div>
  );
}

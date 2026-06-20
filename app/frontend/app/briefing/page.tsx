"use client";

import { useState } from "react";
import { createBriefing, type Article, type MarketBriefing } from "@/lib/api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

const sampleArticles: Article[] = [
  {
    title: "반도체 대형주 중심 수급 개선",
    url: "https://example.com/semiconductor",
    publisher: "sample",
    summary: "외국인 매수와 AI 투자 기대가 반도체 업종에 집중됐다.",
  },
  {
    title: "환율 변동성 확대",
    url: "https://example.com/fx",
    publisher: "sample",
    summary: "원/달러 환율 변동성이 수출주와 성장주 밸류에이션에 부담으로 작용했다.",
  },
];

export default function BriefingPage() {
  const [baseDate, setBaseDate] = useState(todayStr());
  const [timeline, setTimeline] = useState<"PRE_MARKET" | "INTRADAY" | "CLOSE">("CLOSE");
  const [articleText, setArticleText] = useState("");
  const [briefing, setBriefing] = useState<MarketBriefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function articlesFromText(): Article[] {
    const custom = articleText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line, index) => ({
        title: line,
        url: `manual://briefing/${index + 1}`,
        publisher: "manual",
        summary: line,
      }));
    return custom.length > 0 ? custom : sampleArticles;
  }

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    try {
      const res = await createBriefing({
        base_date: baseDate,
        timeline,
        articles: articlesFromText(),
      });
      setBriefing(res.briefing);
    } catch (e) {
      setError(e instanceof Error ? e.message : "브리핑 생성 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <h1>시장판단 브리핑</h1>
        <p className="muted">장전, 장중, 마감 관점으로 시장 내러티브를 정리합니다.</p>
      </div>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>기준일</label>
            <input type="date" value={baseDate} onChange={(e) => setBaseDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>타임라인</label>
            <select value={timeline} onChange={(e) => setTimeline(e.target.value as typeof timeline)}>
              <option value="PRE_MARKET">장전</option>
              <option value="INTRADAY">장중</option>
              <option value="CLOSE">마감</option>
            </select>
          </div>
          <button type="button" onClick={handleSubmit} disabled={loading}>
            {loading ? "생성 중..." : "브리핑 생성"}
          </button>
        </div>
        <label className="muted" htmlFor="briefing-articles">
          참고 기사
        </label>
        <textarea
          id="briefing-articles"
          value={articleText}
          onChange={(e) => setArticleText(e.target.value)}
          placeholder="한 줄에 기사나 시장 관찰 내용을 하나씩 입력"
        />
      </div>

      {error && <p className="error">{error}</p>}

      {briefing && (
        <div className="grid">
          <div className="card">
            <h2 className="section-title">{briefing.content.headline}</h2>
            <p className="muted">
              {briefing.label} · {briefing.base_date} · {briefing.content.confidence}
            </p>
            <p>{briefing.content.market_summary}</p>
          </div>
          <div className="card">
            <h2 className="section-title">핵심 내러티브</h2>
            <ul className="list">
              {briefing.content.key_narratives.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h2 className="section-title">섹터</h2>
            <ul className="list">
              {briefing.content.sector_highlights.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h2 className="section-title">관찰/리스크</h2>
            <ul className="list">
              {[...briefing.content.watch_items, ...briefing.content.risks].map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}


"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getHealth, type HealthResponse } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e) => setError(e.message));
  }, []);

  const kisBadge = () => {
    if (!health) return null;
    const s = health.kis?.smoke?.status || health.kis?.status;
    if (s === "ok" || health.kis?.configured) {
      return <span className="badge badge-ok">KIS {s || "configured"}</span>;
    }
    return <span className="badge badge-warn">KIS not_configured</span>;
  };

  return (
    <div>
      <h1>Stock Market Analyzer</h1>
      <p style={{ color: "var(--muted)" }}>
        거래량·상한가 스크리너 → 뉴스 검색 → LLM 정형 보고서
      </p>

      <div className="card">
        <h2>백엔드 상태</h2>
        {error && <p className="error">{error}</p>}
        {health && (
          <>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <span
                className={`badge ${
                  health.status === "ok" ? "badge-ok" : "badge-warn"
                }`}
              >
                API {health.status}
              </span>
              <span
                className={`badge ${
                  health.database === "ok" ? "badge-ok" : "badge-err"
                }`}
              >
                DB {health.database}
              </span>
              {kisBadge()}
              <span
                className={`badge ${
                  health.news_configured ? "badge-ok" : "badge-warn"
                }`}
              >
                Naver {health.news_configured ? "ok" : "missing"}
              </span>
              <span
                className={`badge ${
                  health.llm_configured ? "badge-ok" : "badge-warn"
                }`}
              >
                LLM {health.llm?.provider || "openai"}{" "}
                {health.llm_configured ? "ok" : "missing"}
              </span>
            </div>
            {health.llm?.roles && (
              <p className="muted" style={{ marginBottom: 0 }}>
                flash {health.llm.roles.flash} · pro {health.llm.roles.pro} · formatter{" "}
                {health.llm.roles.formatter}
              </p>
            )}
          </>
        )}
        {!health && !error && <p className="loading">연결 중...</p>}
      </div>

      <div className="grid">
        <div className="card">
          <h2>스크리너</h2>
          <p className="muted">KIS 거래량/상한가 이벤트를 찾고 뉴스·전략 분석으로 이어갑니다.</p>
          <button type="button" onClick={() => router.push("/screener")}>
            열기
          </button>
        </div>
        <div className="card">
          <h2>시장판단</h2>
          <p className="muted">장전, 장중, 마감 브리핑을 생성합니다.</p>
          <button type="button" onClick={() => router.push("/briefing")}>
            열기
          </button>
        </div>
        <div className="card">
          <h2>전략</h2>
          <p className="muted">특징주 이벤트의 인과관계와 CAN SLIM 정량 조건을 확인합니다.</p>
          <button type="button" onClick={() => router.push("/strategy")}>
            열기
          </button>
        </div>
        <div className="card">
          <h2>모니터링</h2>
          <p className="muted">일일 마감 리포트를 생성하고 맥락 저장소에 기록합니다.</p>
          <button type="button" onClick={() => router.push("/monitor")}>
            열기
          </button>
        </div>
      </div>
    </div>
  );
}

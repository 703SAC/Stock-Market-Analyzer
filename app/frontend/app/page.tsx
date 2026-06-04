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
        )}
        {!health && !error && <p className="loading">연결 중...</p>}
      </div>

      <button type="button" onClick={() => router.push("/screener")}>
        스크리너 시작
      </button>
    </div>
  );
}

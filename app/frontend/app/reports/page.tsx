"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getReport, type AnalysisReport } from "@/lib/api";

function ReportsContent() {
  const params = useSearchParams();
  const reportId = params.get("id");
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    setLoading(true);
    getReport(reportId)
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [reportId]);

  if (!reportId) {
    return (
      <div>
        <h1>보고서</h1>
        <p className="loading">
          뉴스 페이지에서 기사를 선택한 뒤 LLM 보고서를 생성하세요.
        </p>
      </div>
    );
  }

  if (loading) return <p className="loading">보고서 로딩...</p>;
  if (error) return <p className="error">{error}</p>;
  if (!report) return null;

  const confClass =
    report.confidence === "HIGH"
      ? "badge-ok"
      : report.confidence === "LOW"
        ? "badge-warn"
        : "badge-ok";

  return (
    <div>
      <h1>LLM 분석 보고서</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>
          {report.stock.name || report.stock.code} ({report.stock.code})
        </h2>
        <p style={{ color: "var(--muted)" }}>
          관찰일: {report.base_date} ·{" "}
          <span className={`badge ${confClass}`}>{report.confidence}</span>
        </p>
        <p style={{ fontSize: "1.1rem" }}>{report.summary}</p>

        <h3>핵심 포인트</h3>
        <ul>
          {report.key_points.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>

        <h3>가능한 이유</h3>
        <ul>
          {report.possible_reasons.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>

        <h3>주의점</h3>
        <ul>
          {report.risks.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>

        {report.article_urls.length > 0 && (
          <>
            <h3>근거 기사</h3>
            <ul>
              {report.article_urls.map((url, i) => (
                <li key={i}>
                  <a href={url} target="_blank" rel="noreferrer">
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          </>
        )}

        <p style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
          출처: {report.sources.join(", ")} · 투자 조언이 아닌 관찰 보고서입니다.
        </p>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<p className="loading">로딩...</p>}>
      <ReportsContent />
    </Suspense>
  );
}

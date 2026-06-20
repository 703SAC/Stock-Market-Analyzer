import type { AnalysisReport } from "@/lib/api";
import { ConfidenceBadge, SourceChips } from "./ConfidenceBadge";
import { RawJsonToggle } from "./RawJsonToggle";

function Section({ title, items }: { title: string; items: string[] }) {
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

export function ReportView({ report }: { report: AnalysisReport }) {
  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>
        {report.stock.name || report.stock.code} ({report.stock.code})
      </h2>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
        <span className="muted">
          관찰일 {report.base_date} · {report.report_type}
        </span>
        <ConfidenceBadge value={report.confidence} />
      </div>
      <p style={{ fontSize: "1.05rem" }}>{report.summary}</p>

      <Section title="핵심 포인트" items={report.key_points} />
      <Section title="가능한 이유" items={report.possible_reasons} />
      <Section title="주의점" items={report.risks} />

      {report.article_urls.length > 0 && (
        <>
          <h3>근거 기사</h3>
          <ul className="list-tight">
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

      <div style={{ marginTop: "0.5rem" }}>
        <SourceChips sources={report.sources} />
      </div>
      <RawJsonToggle data={report} />
      <p className="disclaimer">투자 조언이 아닌 관찰 보고서입니다.</p>
    </div>
  );
}

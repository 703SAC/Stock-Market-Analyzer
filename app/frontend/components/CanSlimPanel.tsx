import type { CanSlimResult } from "@/lib/api";

const LABELS: Record<string, string> = {
  trend_up: "중기 추세 상승",
  above_ma20: "20일선 상회",
  near_high: "신고가 근접",
  vol_surge: "거래량 급증",
  momentum: "구간 모멘텀",
};

export function CanSlimPanel({ canslim }: { canslim: CanSlimResult | null }) {
  if (!canslim) {
    return (
      <div className="card">
        <h3 style={{ marginTop: 0 }}>CAN SLIM 정량 스크리닝</h3>
        <p className="muted">
          일봉(candles) 미제공 → 정량 평가 생략. 차트 일봉 연동 시 활성화됩니다.
        </p>
      </div>
    );
  }
  const entries = Object.entries(canslim.checks);
  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>
        CAN SLIM 정량 스크리닝{" "}
        <span className={`badge ${canslim.passed ? "badge-ok" : "badge-warn"}`}>
          {canslim.score}/{canslim.max_score} {canslim.passed ? "통과" : "미달"}
        </span>
      </h3>
      <table>
        <tbody>
          {entries.map(([k, ok]) => (
            <tr key={k}>
              <td>{LABELS[k] || k}</td>
              <td style={{ color: ok ? "var(--success)" : "var(--danger)" }}>
                {ok ? "✓ 충족" : "✗ 미충족"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {Object.keys(canslim.metrics).length > 0 && (
        <p className="notice">
          지표:{" "}
          {Object.entries(canslim.metrics)
            .map(([k, v]) => `${k}=${v}`)
            .join(" · ")}
        </p>
      )}
      <p className="notice">
        펀더멘털 미평가(데이터 부재): {canslim.pending_fundamentals.join(", ")}
      </p>
    </div>
  );
}

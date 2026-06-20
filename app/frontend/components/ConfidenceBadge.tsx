export function ConfidenceBadge({ value }: { value?: string }) {
  const cls =
    value === "HIGH" ? "badge-ok" : value === "LOW" ? "badge-err" : "badge-warn";
  return <span className={`badge ${cls}`}>신뢰도 {value || "?"}</span>;
}

export function SourceChips({ sources }: { sources?: string[] }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
      {sources.map((s) => (
        <span key={s} className="badge" style={{ background: "var(--border)", color: "var(--muted)" }}>
          {s}
        </span>
      ))}
    </div>
  );
}

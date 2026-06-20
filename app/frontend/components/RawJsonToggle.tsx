"use client";

import { useState } from "react";

// 품질 검증용: LLM 원본 출력을 그대로 확인(환각/근거 점검)
export function RawJsonToggle({ data, label = "원본 JSON 보기" }: { data: unknown; label?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ marginTop: "0.75rem" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{ background: "var(--border)", color: "var(--muted)", fontSize: "0.8rem" }}
      >
        {open ? "원본 JSON 닫기" : label}
      </button>
      {open && (
        <pre
          style={{
            marginTop: "0.5rem",
            padding: "0.75rem",
            background: "var(--bg)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            fontSize: "0.78rem",
            overflowX: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

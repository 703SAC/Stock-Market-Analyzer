"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getDigests,
  getEvents,
  getGroup,
  getNarratives,
  seedEvent,
  seedGroup,
  type CalendarEvent,
  type GroupMapEntry,
  type MarketDigest,
  type NarrativeMemory,
} from "@/lib/api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}
function addDays(s: string, d: number) {
  const dt = new Date(s);
  dt.setDate(dt.getDate() + d);
  return dt.toISOString().slice(0, 10);
}

type Tab = "digests" | "events" | "group" | "narratives";
const TABS: { key: Tab; label: string }[] = [
  { key: "digests", label: "종합시황" },
  { key: "events", label: "일정" },
  { key: "group", label: "그룹사·테마" },
  { key: "narratives", label: "누적 내러티브" },
];

export default function ContextPage() {
  const [tab, setTab] = useState<Tab>("digests");
  const [error, setError] = useState<string | null>(null);

  const [digests, setDigests] = useState<MarketDigest[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [group, setGroup] = useState<GroupMapEntry | null>(null);
  const [narratives, setNarratives] = useState<NarrativeMemory[]>([]);

  const [groupCode, setGroupCode] = useState("005930");

  // seed forms
  const [evForm, setEvForm] = useState({ event_date: todayStr(), title: "", category: "EARNINGS", stock_code: "" });
  const [grForm, setGrForm] = useState({ stock_code: "", stock_name: "", group_name: "", themes: "" });

  const load = useCallback(async () => {
    setError(null);
    try {
      if (tab === "digests") setDigests(await getDigests({ before: todayStr(), limit: 20 }));
      else if (tab === "events")
        setEvents(await getEvents({ start: addDays(todayStr(), -14), end: addDays(todayStr(), 14) }));
      else if (tab === "group") setGroup(await getGroup(groupCode));
      else if (tab === "narratives") setNarratives(await getNarratives({ before: todayStr(), limit: 20 }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "조회 실패");
    }
  }, [tab, groupCode]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSeedEvent() {
    try {
      await seedEvent({
        event_date: evForm.event_date,
        title: evForm.title,
        category: evForm.category as CalendarEvent["category"],
        stock_code: evForm.stock_code || undefined,
        importance: "MEDIUM",
      });
      setEvForm({ ...evForm, title: "" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "일정 추가 실패");
    }
  }

  async function handleSeedGroup() {
    try {
      await seedGroup({
        stock_code: grForm.stock_code,
        stock_name: grForm.stock_name || undefined,
        group_name: grForm.group_name || undefined,
        themes: grForm.themes ? grForm.themes.split(",").map((t) => t.trim()).filter(Boolean) : [],
        related_codes: [],
      });
      setGrForm({ stock_code: "", stock_name: "", group_name: "", themes: "" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "그룹 추가 실패");
    }
  }

  return (
    <div>
      <h1>메가 내러티브 맥락 저장소</h1>
      <p className="muted">에이전트들이 read/write로 공유하는 누적 맥락. 일정·그룹을 시드하면 브리핑·전략 분석에 주입됩니다.</p>

      <div className="card">
        <div className="tabs">
          {TABS.map((t) => (
            <button key={t.key} type="button" className={`tab ${tab === t.key ? "active" : ""}`} onClick={() => setTab(t.key)}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {tab === "digests" && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>최근 종합시황 ({digests.length})</h3>
          {digests.length === 0 ? (
            <p className="muted">기록된 종합시황이 없습니다. 모니터링 일일 리포트를 실행해 보세요.</p>
          ) : (
            <table>
              <thead>
                <tr><th>날짜</th><th>세션</th><th>제목</th><th>테마</th></tr>
              </thead>
              <tbody>
                {digests.map((d) => (
                  <tr key={d.id || `${d.digest_date}-${d.session}`}>
                    <td>{d.digest_date}</td>
                    <td>{d.session}</td>
                    <td>{d.title}<div className="muted" style={{ fontSize: "0.8rem" }}>{d.summary}</div></td>
                    <td>{d.key_themes.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === "events" && (
        <>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>일정 추가(시드)</h3>
            <div className="form-row">
              <div className="form-group">
                <label>날짜</label>
                <input type="date" value={evForm.event_date} onChange={(e) => setEvForm({ ...evForm, event_date: e.target.value })} />
              </div>
              <div className="form-group">
                <label>제목</label>
                <input value={evForm.title} onChange={(e) => setEvForm({ ...evForm, title: e.target.value })} placeholder="삼성 실적발표" />
              </div>
              <div className="form-group">
                <label>분류</label>
                <select value={evForm.category} onChange={(e) => setEvForm({ ...evForm, category: e.target.value })}>
                  {["EARNINGS", "MACRO", "DIVIDEND", "IPO", "POLICY", "OTHER"].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>종목코드(선택)</label>
                <input value={evForm.stock_code} onChange={(e) => setEvForm({ ...evForm, stock_code: e.target.value })} />
              </div>
              <button type="button" onClick={handleSeedEvent} disabled={!evForm.title}>추가</button>
            </div>
          </div>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>일정 (±14일, {events.length})</h3>
            {events.length === 0 ? (
              <p className="muted">등록된 일정이 없습니다.</p>
            ) : (
              <table>
                <thead><tr><th>날짜</th><th>분류</th><th>제목</th><th>종목</th><th>중요도</th></tr></thead>
                <tbody>
                  {events.map((ev) => (
                    <tr key={ev.id || `${ev.event_date}-${ev.title}`}>
                      <td>{ev.event_date}</td><td>{ev.category}</td><td>{ev.title}</td>
                      <td>{ev.stock_code || "-"}</td><td>{ev.importance}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {tab === "group" && (
        <>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>그룹·테마 추가(시드)</h3>
            <div className="form-row">
              <div className="form-group"><label>종목코드</label><input value={grForm.stock_code} onChange={(e) => setGrForm({ ...grForm, stock_code: e.target.value })} /></div>
              <div className="form-group"><label>종목명</label><input value={grForm.stock_name} onChange={(e) => setGrForm({ ...grForm, stock_name: e.target.value })} /></div>
              <div className="form-group"><label>그룹명</label><input value={grForm.group_name} onChange={(e) => setGrForm({ ...grForm, group_name: e.target.value })} placeholder="삼성" /></div>
              <div className="form-group"><label>테마(쉼표)</label><input value={grForm.themes} onChange={(e) => setGrForm({ ...grForm, themes: e.target.value })} placeholder="반도체, AI" /></div>
              <button type="button" onClick={handleSeedGroup} disabled={!grForm.stock_code}>추가</button>
            </div>
          </div>
          <div className="card">
            <div className="form-row">
              <div className="form-group"><label>조회 종목코드</label><input value={groupCode} onChange={(e) => setGroupCode(e.target.value)} /></div>
              <button type="button" onClick={load}>조회</button>
            </div>
            {group ? (
              <div>
                <p><b>{group.stock_name || group.stock_code}</b> ({group.stock_code}) · 그룹: {group.group_name || "-"}</p>
                <p className="muted">테마: {group.themes.join(", ") || "-"} · 연관: {group.related_codes.join(", ") || "-"}</p>
              </div>
            ) : (
              <p className="muted">해당 종목의 그룹/테마 매핑이 없습니다.</p>
            )}
          </div>
        </>
      )}

      {tab === "narratives" && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>누적 내러티브 ({narratives.length})</h3>
          {narratives.length === 0 ? (
            <p className="muted">누적 내러티브가 없습니다.</p>
          ) : (
            <ul className="list-tight">
              {narratives.map((n) => (
                <li key={n.id || n.topic}>
                  <b>[{n.as_of_date}] {n.topic}</b>
                  {n.stock_codes.length > 0 && <span className="muted"> ({n.stock_codes.join(", ")})</span>}: {n.narrative}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

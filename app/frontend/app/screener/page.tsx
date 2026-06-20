"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getHealth,
  getScreenerEvents,
  screenerCsvUrl,
  type StockEvent,
} from "@/lib/api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function ScreenerPage() {
  const [startDate, setStartDate] = useState(todayStr());
  const [endDate, setEndDate] = useState(todayStr());
  const [minVolume, setMinVolume] = useState(10_000_000);
  const [includeUpper, setIncludeUpper] = useState(true);
  const [events, setEvents] = useState<StockEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [kisConfigured, setKisConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    getHealth()
      .then((h) => setKisConfigured(Boolean(h.kis?.configured)))
      .catch(() => setKisConfigured(null));
  }, []);

  async function handleSearch() {
    setLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const res = await getScreenerEvents({
        start_date: startDate,
        end_date: endDate,
        min_volume: minVolume,
        include_upper_limit: includeUpper,
      });
      setEvents(res.events);
    } catch (e) {
      setError(e instanceof Error ? e.message : "조회 실패");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  const csvUrl = screenerCsvUrl({
    start_date: startDate,
    end_date: endDate,
    min_volume: minVolume,
    include_upper_limit: includeUpper,
  });

  return (
    <div>
      <h1>거래량 / 상한가 스크리너</h1>

      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>시작일</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>종료일</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>최소 거래량</label>
            <input
              type="number"
              value={minVolume}
              onChange={(e) => setMinVolume(Number(e.target.value))}
            />
          </div>
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={includeUpper}
                onChange={(e) => setIncludeUpper(e.target.checked)}
              />{" "}
              상한가 포함
            </label>
          </div>
          <button type="button" onClick={handleSearch} disabled={loading}>
            {loading ? "조회 중..." : "조회"}
          </button>
          <a href={csvUrl} className="btn" download>
            CSV
          </a>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {events.length === 0 && !loading && !error && (
        <p className="loading">
          {hasSearched
            ? "조회 결과가 없습니다. 날짜 범위를 넓히거나 최소 거래량을 낮춰보세요."
            : "조건을 입력하고 조회하세요."}
        </p>
      )}

      {hasSearched && events.length === 0 && !loading && !error && kisConfigured === false && (
        <p className="error" style={{ marginTop: "0.5rem" }}>
          KIS 설정이 완료되지 않아 실데이터 조회가 비어 있을 수 있습니다. 먼저 /api/health의 KIS 상태를 확인하세요.
        </p>
      )}

      {events.length > 0 && (
        <div className="card">
          <p style={{ color: "var(--muted)", marginTop: 0 }}>
            {events.length}건
          </p>
          <table>
            <thead>
              <tr>
                <th>날짜</th>
                <th>종목</th>
                <th>코드</th>
                <th>조건</th>
                <th>거래량</th>
                <th>등락률</th>
                <th>종가</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id || `${ev.trade_date}-${ev.stock.code}`}>
                  <td>{ev.trade_date}</td>
                  <td>{ev.stock.name || "-"}</td>
                  <td>{ev.stock.code}</td>
                  <td>{ev.event_types.join(", ")}</td>
                  <td>{ev.volume?.toLocaleString() ?? "-"}</td>
                  <td>
                    {ev.change_rate != null ? `${ev.change_rate}%` : "-"}
                  </td>
                  <td>{ev.price?.toLocaleString() ?? "-"}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <Link
                      href={`/news?stock_code=${ev.stock.code}&stock_name=${encodeURIComponent(ev.stock.name || "")}&base_date=${ev.trade_date}`}
                    >
                      기사
                    </Link>
                    {" · "}
                    <Link
                      href={`/strategy?stock_code=${ev.stock.code}&stock_name=${encodeURIComponent(ev.stock.name || "")}&base_date=${ev.trade_date}&event_types=${encodeURIComponent(ev.event_types.join(","))}&volume=${ev.volume ?? ""}&change_rate=${ev.change_rate ?? ""}&price=${ev.price ?? ""}`}
                    >
                      인과분석
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

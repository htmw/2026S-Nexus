import React, { useEffect, useMemo, useState } from "react";
import "./PastEntries.css";
import { checkinAPI } from "../services/api";

function formatLongDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return dt.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function toISODate(d) {
  const y  = d.getFullYear();
  const m  = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

function sameMonth(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth();
}

function getMonthGrid(viewDate) {
  const year  = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const first = new Date(year, month, 1);
  const startDay  = first.getDay();
  const gridStart = new Date(year, month, 1 - startDay);
  const cells = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart);
    d.setDate(gridStart.getDate() + i);
    cells.push(d);
  }
  return cells;
}

function moodLabelFromNumber(mood) {
  const map = { 0: "Awful", 1: "Awful", 2: "Bad", 3: "Meh", 4: "Good", 5: "Great" };
  return map[mood] ?? "Unknown";
}

function moodColorFromLabel(label) {
  const map = {
    Awful: "#e07b7b",
    Bad:   "#d4956a",
    Meh:   "#b0a96a",
    Good:  "#6aab84",
    Great: "#6c8fc6",
  };
  return map[label] ?? "#9ba8b0";
}

function titleFromReflection(reflection) {
  if (!reflection || !reflection.trim()) return "No reflection";
  const firstLine = reflection.split("\n").find((l) => l.trim())?.trim() ?? "No reflection";
  return firstLine.length > 60 ? `${firstLine.slice(0, 60)}…` : firstLine;
}

function mapCheckinToEntry(checkin, index) {
  const created   = new Date(checkin.created_at);
  const validDate = Number.isNaN(created.getTime()) ? new Date() : created;

  return {
    id:          checkin.id ?? `entry-${index}`,
    date:        toISODate(validDate),
    timeLabel:   validDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }),
    moodLabel:   moodLabelFromNumber(checkin.mood),
    title:       titleFromReflection(checkin.reflection),
    text:        checkin.reflection?.trim() || "",
    suggestion:  checkin.suggestion?.trim() || "",
    createdAtMs: validDate.getTime(),
  };
}

// ── Detail panel ─────────────────────────────────────────────────────────────
function EntryDetail({ entry, date }) {
  if (!entry) {
    return (
      <div className="pe-card pe-detailCard">
        <div className="pe-detailHeader">
          <div className="pe-detailDate">{formatLongDate(date)}</div>
        </div>
        <div className="pe-detailEmpty">No entry selected.</div>
      </div>
    );
  }

  const moodColor = moodColorFromLabel(entry.moodLabel);

  return (
    <div className="pe-card pe-detailCard">
      {/* Header */}
      <div className="pe-detailHeader">
        <div className="pe-detailDate">{formatLongDate(entry.date)}</div>
        <span className="pe-detailMoodBadge" style={{ "--mood-color": moodColor }}>
          {entry.moodLabel}
        </span>
      </div>

      <article className="pe-detailBody">
        {/* <div className="pe-detailMeta">
          <span className="pe-detailTime">{entry.timeLabel}</span>
        </div> */}

        {/* Reflection */}
        {entry.text ? (
          <div className="pe-section">
            <div className="pe-section__label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Reflection
            </div>
            <div className="pe-paper">
              <p className="pe-detailText">{entry.text}</p>
            </div>
          </div>
        ) : (
          <div className="pe-section">
            <div className="pe-section__label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Reflection
            </div>
            <p className="pe-noContent">No reflection written for this entry.</p>
          </div>
        )}

        {/* AI Suggestion */}
        {entry.suggestion ? (
          <div className="pe-section pe-section--suggestion">
            <div className="pe-section__label pe-section__label--suggestion">
              <span className="pe-suggestion-star" aria-hidden="true">✦</span>
              AI Suggestion
            </div>
            <div className="pe-suggestionBox">
              <p className="pe-suggestionText">{entry.suggestion}</p>
            </div>
          </div>
        ) : null}
      </article>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function PastEntries() {
  const [viewDate,       setViewDate]       = useState(() => new Date());
  const [selectedDate,   setSelectedDate]   = useState(() => toISODate(new Date()));
  const [selectedEntryId, setSelectedEntryId] = useState(null);

  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  useEffect(() => {
    let active = true;

    async function fetchEntries() {
      setLoading(true);
      setError("");
      try {
        const res      = await checkinAPI.getAll();
        const checkins = Array.isArray(res.data) ? res.data : [];
        const mapped   = checkins
          .map(mapCheckinToEntry)
          .sort((a, b) => b.createdAtMs - a.createdAtMs);

        if (!active) return;
        setEntries(mapped);

        if (mapped.length > 0) {
          setSelectedDate(mapped[0].date);
          setSelectedEntryId(mapped[0].id);
        } else {
          setSelectedEntryId(null);
        }
      } catch (err) {
        if (!active) return;
        setError(err.response?.data?.detail || "Failed to load past entries.");
        setEntries([]);
        setSelectedEntryId(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    fetchEntries();
    return () => { active = false; };
  }, []);

  const entriesByDate = useMemo(() => {
    const map = new Map();
    for (const e of entries) {
      if (!map.has(e.date)) map.set(e.date, []);
      map.get(e.date).push(e);
    }
    for (const [k, arr] of map.entries()) {
      arr.sort((a, b) => b.createdAtMs - a.createdAtMs);
      map.set(k, arr);
    }
    return map;
  }, [entries]);

  const allEntries        = useMemo(() => entries, [entries]);
  const selectedDayEntries = useMemo(() => entriesByDate.get(selectedDate) ?? [], [entriesByDate, selectedDate]);
  const selectedEntry      = useMemo(
    () => allEntries.find((e) => e.id === selectedEntryId) || allEntries[0] || null,
    [allEntries, selectedEntryId]
  );

  useEffect(() => {
    if (selectedDayEntries.length) setSelectedEntryId(selectedDayEntries[0].id);
  }, [selectedDate]); // eslint-disable-line react-hooks/exhaustive-deps

  const monthLabel = useMemo(
    () => viewDate.toLocaleDateString(undefined, { month: "long", year: "numeric" }),
    [viewDate]
  );
  const cells = useMemo(() => getMonthGrid(viewDate), [viewDate]);

  function goPrevMonth() {
    const d = new Date(viewDate);
    d.setMonth(d.getMonth() - 1);
    setViewDate(d);
  }
  function goNextMonth() {
    const d = new Date(viewDate);
    d.setMonth(d.getMonth() + 1);
    setViewDate(d);
  }

  return (
    <main className="pe-page">
      <div className="pe-inner">
        <div className="pe-layout">

          {/* ── LEFT column ── */}
          <section className="pe-left">

            {/* Calendar */}
            <div className="pe-card pe-calendarCard">
              <div className="pe-calHeader">
                <button className="pe-calNav" onClick={goPrevMonth} aria-label="Previous month">‹</button>
                <div className="pe-calTitle">{monthLabel}</div>
                <button className="pe-calNav" onClick={goNextMonth} aria-label="Next month">›</button>
              </div>

              <div className="pe-dow">
                {["Su","Mo","Tu","We","Th","Fr","Sa"].map((d) => (
                  <div key={d} className="pe-dowCell">{d}</div>
                ))}
              </div>

              <div className="pe-grid">
                {cells.map((d) => {
                  const iso        = toISODate(d);
                  const inMonth    = sameMonth(d, viewDate);
                  const isSelected = iso === selectedDate;
                  const hasEntries = entriesByDate.has(iso);
                  return (
                    <button
                      key={iso}
                      type="button"
                      className={["pe-day", inMonth ? "" : "is-out", isSelected ? "is-selected" : ""].join(" ")}
                      onClick={() => setSelectedDate(iso)}
                      aria-label={`Select ${iso}`}
                    >
                      <span className="pe-dayNum">{d.getDate()}</span>
                      {hasEntries && <span className="pe-dot" aria-hidden="true" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Entry list */}
            <div className="pe-card pe-listCard">
              <div className="pe-listHeader">
                <div className="pe-listTitle">All entries</div>
                <div className="pe-listSub">
                  {allEntries.length
                    ? `${allEntries.length} entr${allEntries.length === 1 ? "y" : "ies"}`
                    : "No entries"}
                </div>
              </div>

              {loading ? (
                <div className="pe-emptyList">Loading entries…</div>
              ) : error ? (
                <div className="pe-emptyList">{error}</div>
              ) : allEntries.length ? (
                <div className="pe-entryList">
                  {allEntries.map((e) => {
                    const active     = e.id === (selectedEntry?.id ?? null);
                    const moodColor  = moodColorFromLabel(e.moodLabel);
                    return (
                      <button
                        key={e.id}
                        type="button"
                        className={`pe-entryRow ${active ? "is-active" : ""}`}
                        onClick={() => { setSelectedEntryId(e.id); setSelectedDate(e.date); }}
                      >
                        <div className="pe-entryRow__top">
                          <span className="pe-time">{formatLongDate(e.date)}</span>
                        {/* </div>
                        <div className="pe-entryRow__top"> */}
                          {/* <span className="pe-time">{e.timeLabel}</span> */}
                          <span
                            className="pe-mood"
                            style={{ color: moodColor }}
                          >
                            {e.moodLabel}
                          </span>
                        </div>
                        <div className="pe-entryRow__title">{e.title}</div>
                        {e.suggestion && (
                          <div className="pe-entryRow__suggestionHint">
                            ✦ AI suggestion available
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="pe-emptyList">No entries found</div>
              )}
            </div>
          </section>

          {/* ── RIGHT column ── */}
          <section className="pe-right">
            <EntryDetail entry={selectedEntry} date={selectedDate} />
          </section>

        </div>
      </div>
    </main>
  );
}
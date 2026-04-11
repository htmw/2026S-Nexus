import React, { useEffect, useMemo, useState, useRef, useCallback } from "react";
import "./PastEntries.css";
import { checkinAPI } from "../services/api";

// ── helpers ──────────────────────────────────────────────────────────────────

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
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

function sameMonth(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth();
}

function getMonthGrid(viewDate) {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const first = new Date(year, month, 1);
  const startDay = first.getDay();
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

function moodColor(mood) {
  const colors = {
    0: "#e74c3c", 1: "#e74c3c", 2: "#e67e22",
    3: "#f1c40f", 4: "#2ecc71", 5: "#27ae60",
  };
  return colors[mood] ?? "#6c8fc6";
}

function titleFromReflection(reflection) {
  if (!reflection || !reflection.trim()) return "No reflection";
  const firstLine = reflection.split("\n").find((l) => l.trim())?.trim() ?? "No reflection";
  return firstLine.length > 60 ? `${firstLine.slice(0, 60)}…` : firstLine;
}

function mapCheckinToEntry(checkin, index) {
  const created = new Date(checkin.created_at);
  const validDate = Number.isNaN(created.getTime()) ? new Date() : created;
  return {
    id: checkin.id ?? `entry-${index}`,
    date: toISODate(validDate),
    timeLabel: validDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }),
    moodLabel: moodLabelFromNumber(checkin.mood),
    moodValue: checkin.mood,
    title: titleFromReflection(checkin.reflection),
    text: checkin.reflection?.trim() || "No reflection text for this entry.",
    suggestion: checkin.suggestion,
    sentimentLabel: checkin.sentiment_label,
    emotionLabel: checkin.emotion_label,
    createdAtMs: validDate.getTime(),
  };
}

const PAGE_SIZE = 3;

// ── component ─────────────────────────────────────────────────────────────────

export default function PastEntries() {
  const [viewDate, setViewDate] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState(() => toISODate(new Date()));
  const [selectedEntryId, setSelectedEntryId] = useState(null);

  const [allEntries, setAllEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Pagination
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [moodFilter, setMoodFilter] = useState("all"); // "all" | "1".."5"

  const listRef = useRef(null);

  // ── fetch ────────────────────────────────────────────────────────────────

  useEffect(() => {
    let active = true;
    async function fetchEntries() {
      setLoading(true);
      setError("");
      try {
        const res = await checkinAPI.getAll();
        const checkins = Array.isArray(res.data) ? res.data : [];
        const mapped = checkins
          .map(mapCheckinToEntry)
          .sort((a, b) => b.createdAtMs - a.createdAtMs);
        if (!active) return;
        setAllEntries(mapped);
        if (mapped.length > 0) {
          setSelectedDate(mapped[0].date);
          setSelectedEntryId(mapped[0].id);
        }
      } catch (err) {
        if (!active) return;
        setError(err.response?.data?.detail || "Failed to load past entries.");
      } finally {
        if (active) setLoading(false);
      }
    }
    fetchEntries();
    return () => { active = false; };
  }, []);

  // ── derived filtered + paginated list ────────────────────────────────────

  const filteredEntries = useMemo(() => {
    let result = allEntries;

    if (moodFilter !== "all") {
      const val = parseInt(moodFilter, 10);
      result = result.filter((e) => e.moodValue === val);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter(
        (e) =>
          e.text.toLowerCase().includes(q) ||
          e.title.toLowerCase().includes(q) ||
          e.date.includes(q)
      );
    }

    return result;
  }, [allEntries, moodFilter, searchQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredEntries.length / PAGE_SIZE));

  const pagedEntries = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredEntries.slice(start, start + PAGE_SIZE);
  }, [filteredEntries, page]);

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [moodFilter, searchQuery]);

  // ── calendar helpers ──────────────────────────────────────────────────────

  const entriesByDate = useMemo(() => {
    const map = new Map();
    for (const e of allEntries) {
      if (!map.has(e.date)) map.set(e.date, []);
      map.get(e.date).push(e);
    }
    return map;
  }, [allEntries]);

  const selectedEntry = useMemo(
    () => allEntries.find((e) => e.id === selectedEntryId) ?? null,
    [allEntries, selectedEntryId]
  );

  // When selected date changes, auto-select the first entry on that date
  useEffect(() => {
    const dayEntries = entriesByDate.get(selectedDate);
    if (dayEntries?.length) {
      setSelectedEntryId(dayEntries[0].id);
      // Also jump to that entry in the list if it's in current filtered set
      const idx = filteredEntries.findIndex((e) => e.id === dayEntries[0].id);
      if (idx >= 0) {
        const targetPage = Math.floor(idx / PAGE_SIZE) + 1;
        setPage(targetPage);
        // Scroll list to top so user sees the entry
        setTimeout(() => listRef.current?.scrollTo({ top: 0, behavior: "smooth" }), 50);
      }
    }
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

  // Navigate calendar to selected entry's month
  const handleEntryClick = useCallback((entry) => {
    setSelectedEntryId(entry.id);
    setSelectedDate(entry.date);
    const entryMonth = new Date(entry.createdAtMs);
    entryMonth.setDate(1);
    setViewDate(entryMonth);
  }, []);

  // ── pagination controls ───────────────────────────────────────────────────

  function goToPage(p) {
    setPage(p);
    listRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ── render ────────────────────────────────────────────────────────────────

  const hasSuggestion = selectedEntry?.suggestion;
  const sentimentBadge = selectedEntry?.sentimentLabel
    ? selectedEntry.sentimentLabel === "POSITIVE" ? "😊 Positive" : "😔 Negative"
    : null;

  return (
    <main className="pe-page">
      <div className="pe-inner">
        <div className="pe-layout">

          {/* ── LEFT COLUMN ──────────────────────────────────────────────── */}
          <section className="pe-left">

            {/* Calendar */}
            <div className="pe-card pe-calendarCard">
              <div className="pe-calHeader">
                <button className="pe-calNav" onClick={goPrevMonth} aria-label="Previous month">‹</button>
                <div className="pe-calTitle">{monthLabel}</div>
                <button className="pe-calNav" onClick={goNextMonth} aria-label="Next month">›</button>
              </div>
              <div className="pe-dow">
                {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((d) => (
                  <div key={d} className="pe-dowCell">{d}</div>
                ))}
              </div>
              <div className="pe-grid">
                {cells.map((d) => {
                  const iso = toISODate(d);
                  const inMonth = sameMonth(d, viewDate);
                  const isSelected = iso === selectedDate;
                  const dayEntries = entriesByDate.get(iso) || [];
                  const hasEntries = dayEntries.length > 0;
                  const avgMood = hasEntries
                    ? dayEntries.reduce((s, e) => s + e.moodValue, 0) / dayEntries.length
                    : null;
                  return (
                    <button
                      key={iso}
                      type="button"
                      className={["pe-day", inMonth ? "" : "is-out", isSelected ? "is-selected" : ""].join(" ")}
                      onClick={() => setSelectedDate(iso)}
                      aria-label={`Select ${iso}`}
                    >
                      <span className="pe-dayNum">{d.getDate()}</span>
                      {hasEntries && (
                        <span
                          className="pe-dot"
                          aria-hidden="true"
                          style={{ background: moodColor(Math.round(avgMood)) }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Entry List */}
            <div className="pe-card pe-listCard">
              <div className="pe-listHeader">
                <div className="pe-listTitle">All entries</div>
                <div className="pe-listSub">
                  {filteredEntries.length
                    ? `${filteredEntries.length} entr${filteredEntries.length === 1 ? "y" : "ies"}`
                    : "No entries"}
                </div>
              </div>

              {loading ? (
                <div className="pe-emptyList">Loading entries…</div>
              ) : error ? (
                <div className="pe-emptyList">{error}</div>
              ) : filteredEntries.length === 0 ? (
                <div className="pe-emptyList">
                  {searchQuery || moodFilter !== "all"
                    ? "No entries match your filter."
                    : "No entries found."}
                </div>
              ) : (
                <>
                  <div className="pe-entryList" ref={listRef}>
                    {pagedEntries.map((e) => {
                      const active = e.id === selectedEntryId;
                      return (
                        <button
                          key={e.id}
                          type="button"
                          className={`pe-entryRow ${active ? "is-active" : ""}`}
                          onClick={() => handleEntryClick(e)}
                        >
                          <div className="pe-entryRow__top">
                            <span className="pe-time">{formatLongDate(e.date)}</span>
                          {/* </div>
                          <div className="pe-entryRow__top">
                            <span className="pe-time">{e.timeLabel}</span> */}
                            <span
                              className="pe-mood"
                              style={{ color: moodColor(e.moodValue) }}
                            >
                              {e.moodLabel}
                            </span>
                          </div>
                          <div className="pe-entryRow__title">{e.title}</div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="pe-pagination">
                      <button
                        className="pe-pageBtn"
                        onClick={() => goToPage(page - 1)}
                        disabled={page === 1}
                        aria-label="Previous page"
                      >
                        ‹
                      </button>
                      <span className="pe-pageInfo">
                        {page} / {totalPages}
                      </span>
                      <button
                        className="pe-pageBtn"
                        onClick={() => goToPage(page + 1)}
                        disabled={page === totalPages}
                        aria-label="Next page"
                      >
                        ›
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>

          {/* ── RIGHT COLUMN ──────────────────────────────────────────────── */}
          <section className="pe-right">
            <div className="pe-card pe-detailCard">
              {selectedEntry ? (
                <>
                  <div className="pe-detailHeader">
                    <div className="pe-detailDate">{formatLongDate(selectedEntry.date)}</div>
                    <div className="pe-detailBadges">
                      <span
                        className="pe-moodBadge"
                        style={{ background: `${moodColor(selectedEntry.moodValue)}22`, color: moodColor(selectedEntry.moodValue) }}
                      >
                        {selectedEntry.moodLabel}
                      </span>
                      {sentimentBadge && (
                        <span className="pe-sentimentBadge">{sentimentBadge}</span>
                      )}
                    </div>
                  </div>

                  <article className="pe-detailBody">
                    <div className="pe-detailMeta">
                      {selectedEntry.emotionLabel && (
                        <span className="pe-emotionTag">
                          Emotion: {selectedEntry.emotionLabel}
                        </span>
                      )}
                    </div>

                    <div className="pe-paper">
                      <p className="pe-detailText">{selectedEntry.text}</p>
                    </div>

                    {/* Suggestion card */}
                    {hasSuggestion && (
                      <div className="pe-suggestionCard">
                        <div className="pe-suggestionLabel">💡 Suggestion</div>
                        <p className="pe-suggestionText">{selectedEntry.suggestion}</p>
                      </div>
                    )}
                  </article>
                </>
              ) : (
                <div className="pe-detailHeader">
                  <div className="pe-detailDate">{formatLongDate(selectedDate)}</div>
                  <div className="pe-detailEmpty" style={{ marginTop: 24 }}>
                    No entry selected. Pick one from the list or tap a date on the calendar.
                  </div>
                </div>
              )}
            </div>
          </section>

        </div>
      </div>
    </main>
  );
}
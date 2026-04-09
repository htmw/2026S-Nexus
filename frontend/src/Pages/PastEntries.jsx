import React, { useEffect, useMemo, useState } from "react";
import "./PastEntries.css";
import { checkinAPI } from "../services/api";

const MOOD_LABELS = {
  0: "Awful",
  1: "Bad",
  2: "Meh",
  3: "Balanced",
  4: "Good",
  5: "Great",
};

function entryTitle(reflection, sentiment) {
  const clean = (reflection || "").trim();
  if (!clean) {
    return sentiment === "NEGATIVE" ? "Low-energy reflection" : "Quick reflection";
  }
  const firstLine = clean.split(/\n+/)[0].trim();
  const compact = firstLine.length > 48 ? `${firstLine.slice(0, 45)}…` : firstLine;
  return compact || "Journal entry";
}

function transformEntry(entry) {
  const createdAt = new Date(entry.created_at);
  return {
    id: entry.id,
    createdAt,
    date: toISODate(createdAt),
    timeLabel: createdAt.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }),
    moodLabel: MOOD_LABELS[entry.mood] || entry.sentiment || "Entry",
    title: entryTitle(entry.reflection, entry.sentiment),
    text: entry.reflection || "",
    sentiment: entry.sentiment,
    suggestion: entry.suggestion,
    predictedMood: entry.predicted_mood,
    confidence: entry.confidence,
  };
}

function formatLongDate(iso) {
  // iso = "YYYY-MM-DD"
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
  // returns array of 42 day-cells (6 rows x 7 cols)
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  const first = new Date(year, month, 1);
  const startDay = first.getDay(); // 0=Sun

  const gridStart = new Date(year, month, 1 - startDay);

  const cells = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart);
    d.setDate(gridStart.getDate() + i);
    cells.push(d);
  }
  return cells;
}

export default function PastEntries() {
  const [viewDate, setViewDate] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState(() => toISODate(new Date()));
  const [selectedEntryId, setSelectedEntryId] = useState(null);
  const [entries, setEntries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadEntries() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const response = await checkinAPI.list();
        const nextEntries = (response.data?.entries || [])
          .map(transformEntry)
          .sort((left, right) => right.createdAt.getTime() - left.createdAt.getTime());
        if (!isMounted) return;
        setEntries(nextEntries);
        if (nextEntries.length) {
          setSelectedDate(nextEntries[0].date);
          setSelectedEntryId(nextEntries[0].id);
        }
      } catch (error) {
        if (!isMounted) return;
        setErrorMessage(error.message || "Could not load saved entries right now.");
        setEntries([]);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadEntries();
    return () => {
      isMounted = false;
    };
  }, []);

  const entriesByDate = useMemo(() => {
    const map = new Map();
    for (const e of entries) {
      if (!map.has(e.date)) map.set(e.date, []);
      map.get(e.date).push(e);
    }
    //sort entries within each day by timeLabel (simple)
    for (const [k, arr] of map.entries()) {
      arr.sort((a, b) => (a.timeLabel > b.timeLabel ? 1 : -1));
      map.set(k, arr);
    }
    return map;
  }, [entries]);

  const selectedDayEntries = useMemo(() => {
    return entriesByDate.get(selectedDate) ?? [];
  }, [entriesByDate, selectedDate]);

  const selectedEntry = useMemo(() => {
    const all = entries;
    const found =
      all.find((e) => e.id === selectedEntryId) ||
      (selectedDayEntries.length ? selectedDayEntries[0] : null);
    return found;
  }, [entries, selectedEntryId, selectedDayEntries]);

  // whenever date changes, default select first entry
  React.useEffect(() => {
    if (selectedDayEntries.length) {
      setSelectedEntryId(selectedDayEntries[0].id);
    } else {
      setSelectedEntryId(null);
    }
  }, [selectedDate]); // eslint-disable-line react-hooks/exhaustive-deps

  const monthLabel = useMemo(() => {
    return viewDate.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  }, [viewDate]);

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
          {/* LEFT */}
          <section className="pe-left">
            <div className="pe-card pe-calendarCard">
              <div className="pe-calHeader">
                <button className="pe-calNav" onClick={goPrevMonth} aria-label="Previous month">
                  ‹
                </button>
                <div className="pe-calTitle">{monthLabel}</div>
                <button className="pe-calNav" onClick={goNextMonth} aria-label="Next month">
                  ›
                </button>
              </div>

              <div className="pe-dow">
                {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((d) => (
                  <div key={d} className="pe-dowCell">
                    {d}
                  </div>
                ))}
              </div>

              <div className="pe-grid">
                {cells.map((d) => {
                  const iso = toISODate(d);
                  const inMonth = sameMonth(d, viewDate);
                  const isSelected = iso === selectedDate;
                  const hasEntries = entriesByDate.has(iso);

                  return (
                    <button
                      key={iso}
                      type="button"
                      className={[
                        "pe-day",
                        inMonth ? "" : "is-out",
                        isSelected ? "is-selected" : "",
                      ].join(" ")}
                      onClick={() => setSelectedDate(iso)}
                      aria-label={`Select ${iso}`}
                    >
                      <span className="pe-dayNum">{d.getDate()}</span>
                      {hasEntries ? <span className="pe-dot" aria-hidden="true" /> : null}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="pe-card pe-listCard">
              <div className="pe-listHeader">
                <div className="pe-listTitle">{formatLongDate(selectedDate)}</div>
                <div className="pe-listSub">
                  {isLoading
                    ? "Loading entries..."
                    : selectedDayEntries.length
                    ? `${selectedDayEntries.length} entr${selectedDayEntries.length === 1 ? "y" : "ies"}`
                    : "No entries"}
                </div>
              </div>

              {errorMessage ? (
                <div className="pe-emptyList">{errorMessage}</div>
              ) : isLoading ? (
                <div className="pe-emptyList">Loading your saved entries…</div>
              ) : selectedDayEntries.length ? (
                <div className="pe-entryList">
                  {selectedDayEntries.map((e) => {
                    const active = e.id === (selectedEntry?.id ?? null);
                    return (
                      <button
                        key={e.id}
                        type="button"
                        className={`pe-entryRow ${active ? "is-active" : ""}`}
                        onClick={() => setSelectedEntryId(e.id)}
                      >
                        <div className="pe-entryRow__top">
                          <span className="pe-time">{e.timeLabel}</span>
                          <span className="pe-mood">{e.moodLabel}</span>
                        </div>
                        <div className="pe-entryRow__title">{e.title}</div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="pe-emptyList">Nothing found</div>
              )}
            </div>
          </section>

          {/* RIGHT */}
          <section className="pe-right">
            <div className="pe-card pe-detailCard">
              <div className="pe-detailHeader">
                <div className="pe-detailDate">{formatLongDate(selectedDate)}</div>
              </div>

              {selectedEntry ? (
                <article className="pe-detailBody">
                  <div className="pe-detailMeta">
                    <span className="pe-detailTime">{selectedEntry.timeLabel}</span>
                    <span className="pe-detailMood">{selectedEntry.moodLabel}</span>
                  </div>

                  <h2 className="pe-detailTitle">{selectedEntry.title}</h2>
                  <div className="pe-paper">
                    <p className="pe-detailText">{selectedEntry.text}</p>
                  </div>
                  {selectedEntry.suggestion ? (
                    <div className="pe-feedbackBox">
                      <div className="pe-feedbackHead">
                        <span className="pe-feedbackLabel">Saved feedback</span>
                        <span className="pe-detailMood">{selectedEntry.sentiment}</span>
                      </div>
                      <p className="pe-feedbackText">{selectedEntry.suggestion}</p>
                    </div>
                  ) : null}
                </article>
              ) : (
                <div className="pe-detailEmpty">
                  Select a day with entries to view your reflection.
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

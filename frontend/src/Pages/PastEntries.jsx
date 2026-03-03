import React, { useMemo, useState } from "react";
import "./PastEntries.css";

/**
 * MOCK DATA (replace later with your real entries)
 * Each entry has: id, date (YYYY-MM-DD), timeLabel, moodLabel, title, text
 */
const MOCK_ENTRIES = [
  {
    id: "e1",
    date: "2026-03-01",
    timeLabel: "9:12 PM",
    moodLabel: "Balanced",
    title: "Long day, calmer ending",
    text:
      "Today I felt unusually calm.🥰 \n\nMaybe it’s because I finally gave myself permission to slow down instead of rushing to check every box on my to-do list. I took a walk without my phone and realized how rarely I let my mind wander freely. There’s something refreshing about not needing to be productive every second — just existing felt enough. \n \nLater in the evening, I reflected on how I tend to measure my worth by what I accomplish. It’s exhausting, honestly. I want to start celebrating smaller moments — like taking care of myself, choosing peace, or saying no when I need to. I think that’s what balance might actually look like for me. \n \nAlso, work has been a rollercoaster lately. Some days I feel like I’m thriving — creative, focused, and full of ideas. But other days, the imposter syndrome creeps in. I catch myself second-guessing my decisions or comparing my progress to others’. I’m trying to remind myself that growth isn’t linear and that confidence is built through consistency, not perfection.",
  },
  {
    id: "e2",
    date: "2026-03-01",
    timeLabel: "11:08 PM",
    moodLabel: "Reflective",
    title: "Thinking about priorities",
    text:
      "Today I felt unusually calm.🥰 \n\nMaybe it’s because I finally gave myself permission to slow down instead of rushing to check every box on my to-do list. I took a walk without my phone and realized how rarely I let my mind wander freely. There’s something refreshing about not needing to be productive every second — just existing felt enough. \n \nLater in the evening, I reflected on how I tend to measure my worth by what I accomplish. It’s exhausting, honestly. I want to start celebrating smaller moments — like taking care of myself, choosing peace, or saying no when I need to. I think that’s what balance might actually look like for me. \n \nAlso, work has been a rollercoaster lately. Some days I feel like I’m thriving — creative, focused, and full of ideas. But other days, the imposter syndrome creeps in. I catch myself second-guessing my decisions or comparing my progress to others’. I’m trying to remind myself that growth isn’t linear and that confidence is built through consistency, not perfection.",
  },
  {
    id: "e3",
    date: "2026-03-02",
    timeLabel: "7:40 AM",
    moodLabel: "Anxious",
    title: "Woke up tense",
    text:
      "Today I felt unusually calm.🥰 \n\nMaybe it’s because I finally gave myself permission to slow down instead of rushing to check every box on my to-do list. I took a walk without my phone and realized how rarely I let my mind wander freely. There’s something refreshing about not needing to be productive every second — just existing felt enough. \n \nLater in the evening, I reflected on how I tend to measure my worth by what I accomplish. It’s exhausting, honestly. I want to start celebrating smaller moments — like taking care of myself, choosing peace, or saying no when I need to. I think that’s what balance might actually look like for me. \n \nAlso, work has been a rollercoaster lately. Some days I feel like I’m thriving — creative, focused, and full of ideas. But other days, the imposter syndrome creeps in. I catch myself second-guessing my decisions or comparing my progress to others’. I’m trying to remind myself that growth isn’t linear and that confidence is built through consistency, not perfection.",
  },
  {
    id: "e4",
    date: "2026-03-01",
    timeLabel: "6:15 PM",
    moodLabel: "Happy",
    title: "Good news!",
    text:
      "Today I felt unusually calm.🥰 \n\nMaybe it’s because I finally gave myself permission to slow down instead of rushing to check every box on my to-do list. I took a walk without my phone and realized how rarely I let my mind wander freely. There’s something refreshing about not needing to be productive every second — just existing felt enough. \n \nLater in the evening, I reflected on how I tend to measure my worth by what I accomplish. It’s exhausting, honestly. I want to start celebrating smaller moments — like taking care of myself, choosing peace, or saying no when I need to. I think that’s what balance might actually look like for me. \n \nAlso, work has been a rollercoaster lately. Some days I feel like I’m thriving — creative, focused, and full of ideas. But other days, the imposter syndrome creeps in. I catch myself second-guessing my decisions or comparing my progress to others’. I’m trying to remind myself that growth isn’t linear and that confidence is built through consistency, not perfection.",
  },
];

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

  const entriesByDate = useMemo(() => {
    const map = new Map();
    for (const e of MOCK_ENTRIES) {
      if (!map.has(e.date)) map.set(e.date, []);
      map.get(e.date).push(e);
    }
    //sort entries within each day by timeLabel (simple)
    for (const [k, arr] of map.entries()) {
      arr.sort((a, b) => (a.timeLabel > b.timeLabel ? 1 : -1));
      map.set(k, arr);
    }
    return map;
  }, []);

  const selectedDayEntries = useMemo(() => {
    return entriesByDate.get(selectedDate) ?? [];
  }, [entriesByDate, selectedDate]);

  const selectedEntry = useMemo(() => {
    const all = MOCK_ENTRIES;
    const found =
      all.find((e) => e.id === selectedEntryId) ||
      (selectedDayEntries.length ? selectedDayEntries[0] : null);
    return found;
  }, [selectedEntryId, selectedDayEntries]);

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
                  {selectedDayEntries.length
                    ? `${selectedDayEntries.length} entr${selectedDayEntries.length === 1 ? "y" : "ies"}`
                    : "No entries"}
                </div>
              </div>

              {selectedDayEntries.length ? (
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
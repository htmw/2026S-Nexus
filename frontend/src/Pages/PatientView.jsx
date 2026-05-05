import React, { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./PatientView.css";
import api from "../services/api";

const SENTIMENT_META = {
  positive: { color: "#62a88e", emoji: "😊", label: "Positive" },
  negative: { color: "#c47a7a", emoji: "😔", label: "Negative" },
  neutral:  { color: "#9aa3ad", emoji: "😐", label: "Neutral" },
  Pending:  { color: "#c8a96a", emoji: "⏳", label: "Pending" },
};

function metaFor(label) {
  return SENTIMENT_META[label] || SENTIMENT_META.neutral;
}

function formatLong(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso || "";
  }
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function PatientView() {
  const { patientId } = useParams();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [entries, setEntries] = useState([]);
  const [moodTrend, setMoodTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("journal"); // "journal" | "mood"

  useEffect(() => {
    let active = true;
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [profileRes, journalRes, moodRes] = await Promise.all([
          api.get(`/therapist/patients/${patientId}/profile`),
          api.get(`/therapist/patients/${patientId}/journal`),
          api.get(`/therapist/patients/${patientId}/mood`),
        ]);
        if (!active) return;
        setProfile(profileRes.data);
        setEntries(journalRes.data.entries || []);
        setMoodTrend(moodRes.data.points || []);
      } catch (err) {
        if (!active) return;
        const status = err.response?.status;
        const detail = err.response?.data?.detail;
        if (status === 403) {
          setError(detail || "This patient has not shared their data with you.");
        } else {
          setError(detail || "Could not load this patient's data.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    fetchData();
    return () => { active = false; };
  }, [patientId]);

  const initials = useMemo(() => {
    return (profile?.name || "?")
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => s[0]?.toUpperCase() ?? "")
      .join("") || "?";
  }, [profile]);

  // Sentiment mix for the mood tab
  const sentimentSummary = useMemo(() => {
    const counts = { positive: 0, neutral: 0, negative: 0 };
    moodTrend.forEach((p) => {
      const k = (p.sentiment_label || "").toLowerCase();
      if (counts[k] !== undefined) counts[k] += 1;
    });
    const total = counts.positive + counts.neutral + counts.negative;
    return { counts, total };
  }, [moodTrend]);

  // Group entries by date (newest first)
  const entriesByDay = useMemo(() => {
    const sorted = [...entries].sort(
      (a, b) => new Date(b.date) - new Date(a.date)
    );
    const groups = new Map();
    sorted.forEach((e) => {
      const key = formatLong(e.date);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(e);
    });
    return groups;
  }, [entries]);

  return (
    <main className="pv-page">
      <div className="pv-inner">

        {/* Back link */}
        <button
          type="button"
          className="pv-back"
          onClick={() => navigate("/therapist/dashboard")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M19 12H5m6-6-6 6 6 6"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Back to all patients
        </button>

        {loading ? (
          <div className="pv-skeletonHeader" />
        ) : error ? (
          <div className="pv-blocked">
            <div className="pv-blocked__icon" aria-hidden="true">🔒</div>
            <h2 className="pv-blocked__title">Access restricted</h2>
            <p className="pv-blocked__text">{error}</p>
            <button
              className="pv-blocked__btn"
              onClick={() => navigate("/therapist/dashboard")}
            >
              Return to dashboard
            </button>
          </div>
        ) : (
          <>
            {/* ── Patient header card ─────────────────────────────── */}
            <section className="pv-header">
              <div className="pv-header__left">
                <div className="pv-header__avatar">{initials}</div>
                <div className="pv-header__info">
                  <h1 className="pv-header__name">{profile?.name}</h1>
                  <p className="pv-header__email">{profile?.email}</p>
                </div>
              </div>

              <div className="pv-header__right">
                <div
                  className={`pv-header__status ${
                    profile?.sharing_enabled ? "is-on" : "is-off"
                  }`}
                >
                  <span className="pv-header__statusDot" />
                  {profile?.sharing_enabled ? "Sharing enabled" : "Sharing paused"}
                </div>
                <div className="pv-header__readonly">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M12 15v2m-7-2a4 4 0 0 1-1-2.6 4 4 0 0 1 4-4h8a4 4 0 0 1 4 4 4 4 0 0 1-1 2.6"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      strokeLinecap="round"
                    />
                    <path
                      d="M12 13v6m-3-9V8a3 3 0 0 1 6 0v2"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      strokeLinecap="round"
                    />
                  </svg>
                  Read-only access
                </div>
              </div>
            </section>

            {/* ── Tab bar ─────────────────────────────────────────── */}
            <div className="pv-tabs">
              <button
                type="button"
                className={`pv-tab ${activeTab === "journal" ? "is-active" : ""}`}
                onClick={() => setActiveTab("journal")}
              >
                <span className="pv-tab__label">Journal entries</span>
                <span className="pv-tab__count">{entries.length}</span>
              </button>
              <button
                type="button"
                className={`pv-tab ${activeTab === "mood" ? "is-active" : ""}`}
                onClick={() => setActiveTab("mood")}
              >
                <span className="pv-tab__label">Mood trend</span>
                <span className="pv-tab__count">{moodTrend.length}</span>
              </button>
            </div>

            {/* ── Tab content ─────────────────────────────────────── */}
            {activeTab === "journal" ? (
              <JournalTab
                entries={entries}
                entriesByDay={entriesByDay}
              />
            ) : (
              <MoodTab
                moodTrend={moodTrend}
                summary={sentimentSummary}
              />
            )}
          </>
        )}
      </div>
    </main>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Journal tab
// ─────────────────────────────────────────────────────────────────────────────

function JournalTab({ entries, entriesByDay }) {
  if (entries.length === 0) {
    return (
      <EmptyCard
        icon="📓"
        title="No shared entries yet"
        hint="This patient hasn't shared any journal entries with you. Entries appear here only when the patient explicitly shares them."
      />
    );
  }

  return (
    <div className="pv-journal">
      {Array.from(entriesByDay.entries()).map(([dayLabel, dayEntries]) => (
        <div key={dayLabel} className="pv-day">
          <div className="pv-day__label">{dayLabel}</div>
          <div className="pv-day__entries">
            {dayEntries.map((entry, idx) => {
              const meta = metaFor(entry.sentiment_label);
              return (
                <article key={`${dayLabel}-${idx}`} className="pv-entry">
                  <header className="pv-entry__header">
                    <span className="pv-entry__time">{formatTime(entry.date)}</span>
                    <span
                      className="pv-entry__sentiment"
                      style={{
                        background: `${meta.color}1F`,
                        color: meta.color,
                      }}
                    >
                      <span aria-hidden="true">{meta.emoji}</span>
                      {meta.label}
                    </span>
                  </header>
                  <p className="pv-entry__text">{entry.text}</p>
                </article>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Mood tab
// ─────────────────────────────────────────────────────────────────────────────

function MoodTab({ moodTrend, summary }) {
  if (moodTrend.length === 0) {
    return (
      <EmptyCard
        icon="📈"
        title="No mood data yet"
        hint="Mood trends will appear once the patient shares journal entries that have been analyzed for sentiment."
      />
    );
  }

  return (
    <div className="pv-mood">
      {/* Summary chips */}
      <div className="pv-moodSummary">
        <SentimentStat
          label="Positive"
          count={summary.counts.positive}
          total={summary.total}
          meta={metaFor("positive")}
        />
        <SentimentStat
          label="Neutral"
          count={summary.counts.neutral}
          total={summary.total}
          meta={metaFor("neutral")}
        />
        <SentimentStat
          label="Negative"
          count={summary.counts.negative}
          total={summary.total}
          meta={metaFor("negative")}
        />
      </div>

      {/* Sentiment chart card */}
      <SentimentChart points={moodTrend} />

      {/* Detailed list */}
      <div className="pv-trendList">
        <div className="pv-trendList__title">Detailed timeline</div>
        {[...moodTrend].reverse().map((p, idx) => {
          const meta = metaFor(p.sentiment_label);
          const conf = Math.round((p.confidence_score || 0) * 100);
          return (
            <div key={idx} className="pv-trendRow">
              <div className="pv-trendRow__date">{formatLong(p.date)}</div>
              <div
                className="pv-trendRow__pill"
                style={{ background: `${meta.color}1F`, color: meta.color }}
              >
                <span aria-hidden="true">{meta.emoji}</span> {meta.label}
              </div>
              <div className="pv-trendRow__bar">
                <div
                  className="pv-trendRow__barFill"
                  style={{ width: `${conf}%`, background: meta.color }}
                />
              </div>
              <div className="pv-trendRow__conf">{conf}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SentimentStat({ label, count, total, meta }) {
  const pct = total ? Math.round((count / total) * 100) : 0;
  return (
    <div className="pv-statCard">
      <div className="pv-statCard__top">
        <div
          className="pv-statCard__icon"
          style={{ background: `${meta.color}1F`, color: meta.color }}
          aria-hidden="true"
        >
          {meta.emoji}
        </div>
        <div className="pv-statCard__label">{label}</div>
      </div>
      <div className="pv-statCard__num">{count}</div>
      <div className="pv-statCard__pct">
        <div className="pv-statCard__bar">
          <div
            className="pv-statCard__barFill"
            style={{ width: `${pct}%`, background: meta.color }}
          />
        </div>
        <span>{pct}%</span>
      </div>
    </div>
  );
}

// Simple inline SVG chart — sentiment over time
function SentimentChart({ points }) {
  // Map sentiment → numeric Y: positive 1, neutral 0, negative -1
  const data = points.map((p) => {
    const label = (p.sentiment_label || "").toLowerCase();
    const y = label === "positive" ? 1 : label === "negative" ? -1 : 0;
    return { y, label, date: p.date };
  });

  const W = 680;
  const H = 200;
  const PAD_X = 20;
  const PAD_Y = 26;
  const innerW = W - PAD_X * 2;
  const innerH = H - PAD_Y * 2;

  const xFor = (i) =>
    data.length === 1
      ? PAD_X + innerW / 2
      : PAD_X + (i / (data.length - 1)) * innerW;

  // Y range -1..1 → top..bottom
  const yFor = (val) => PAD_Y + ((1 - val) / 2) * innerH;

  const linePath = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${xFor(i)} ${yFor(d.y)}`)
    .join(" ");

  return (
    <div className="pv-chartCard">
      <div className="pv-chartCard__head">
        <div className="pv-chartCard__title">Sentiment over time</div>
        <div className="pv-chartCard__sub">
          {points.length} data point{points.length === 1 ? "" : "s"} · positive →
          neutral → negative
        </div>
      </div>

      <div className="pv-chartCard__svgWrap">
        <svg
          className="pv-chartSvg"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          aria-label="Sentiment trend chart"
        >
          {/* Y gridlines */}
          {[1, 0, -1].map((val) => (
            <g key={val}>
              <line
                x1={PAD_X}
                x2={W - PAD_X}
                y1={yFor(val)}
                y2={yFor(val)}
                stroke="rgba(0,0,0,0.06)"
                strokeWidth="1"
                strokeDasharray={val === 0 ? "none" : "4 4"}
              />
              <text
                x={PAD_X - 6}
                y={yFor(val) + 4}
                fontSize="11"
                textAnchor="end"
                fill="#8b94a0"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
              >
                {val === 1 ? "Pos" : val === 0 ? "Neu" : "Neg"}
              </text>
            </g>
          ))}

          {/* Connecting line */}
          {data.length > 1 && (
            <path
              d={linePath}
              fill="none"
              stroke="#6c8fc6"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Points */}
          {data.map((d, i) => {
            const meta = metaFor(d.label);
            return (
              <g key={i}>
                <circle
                  cx={xFor(i)}
                  cy={yFor(d.y)}
                  r="6"
                  fill={meta.color}
                  stroke="#fff"
                  strokeWidth="2"
                />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

function EmptyCard({ icon, title, hint }) {
  return (
    <div className="pv-empty">
      <div className="pv-empty__icon" aria-hidden="true">{icon}</div>
      <div className="pv-empty__title">{title}</div>
      <div className="pv-empty__hint">{hint}</div>
    </div>
  );
}
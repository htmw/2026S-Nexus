import React, { useMemo, useState } from "react";
import "./Insights.css";

const RANGE_OPTIONS = [
  { value: "7d", label: "Last 7 days" },
  { value: "14d", label: "Last 2 weeks" },
  { value: "1m", label: "Last 1 month" },
  { value: "3m", label: "Last 3 months" },
  { value: "custom", label: "Custom range" },
];

function Card({ className = "", children }) {
  return <div className={`ins-card ${className}`}>{children}</div>;
}

function InsightRow({ tone = "blue", text }) {
  return (
    <div className={`ins-insightRow ins-insightRow--${tone}`}>
      <div className="ins-insightRow__icon" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path
            d="M4 5.5C4 4.12 5.12 3 6.5 3h11C18.88 3 20 4.12 20 5.5v8c0 1.38-1.12 2.5-2.5 2.5H10l-4.2 3.1c-.5.37-1.2.02-1.2-.6V16H6.5C5.12 16 4 14.88 4 13.5v-8Z"
            stroke="currentColor"
            strokeWidth="1.6"
          />
          <path
            d="M7.5 7.8h9M7.5 10.8h7"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div className="ins-insightRow__text">{text}</div>
    </div>
  );
}

function MiniLineChart({ title, subtitle, tone = "blue", points, labels }) {
  const { path, areaPath } = useMemo(() => {
    // points: y-values 0..5-ish
    // map to svg coords
    const w = 520;
    const h = 220;
    const padL = 38;
    const padR = 14;
    const padT = 16;
    const padB = 32;

    const innerW = w - padL - padR;
    const innerH = h - padT - padB;

    const maxY = 5;
    const minY = 0;

    const xStep = innerW / (points.length - 1 || 1);

    const xy = points.map((y, i) => {
      const x = padL + i * xStep;
      const t = (y - minY) / (maxY - minY);
      const yy = padT + (1 - t) * innerH;
      return { x, y: yy };
    });

    // build a smooth-ish bezier path
    const d = [];
    d.push(`M ${xy[0].x} ${xy[0].y}`);

    for (let i = 1; i < xy.length; i++) {
      const p0 = xy[i - 1];
      const p1 = xy[i];
      const cx = (p0.x + p1.x) / 2;
      d.push(`C ${cx} ${p0.y} ${cx} ${p1.y} ${p1.x} ${p1.y}`);
    }

    const linePath = d.join(" ");

    // area path (down to baseline)
    const baselineY = padT + innerH;
    const area = [
      linePath,
      `L ${xy[xy.length - 1].x} ${baselineY}`,
      `L ${xy[0].x} ${baselineY}`,
      "Z",
    ].join(" ");

    return { path: linePath, areaPath: area };
  }, [points]);

  return (
    <Card className="ins-chartCard">
      <div className="ins-chartCard__head">
        <div className="ins-chartTitle">{title}</div>
        <div className="ins-chartSubtitle">{subtitle}</div>
      </div>

      <div className="ins-chartWrap">
        <svg className="ins-chart" viewBox="0 0 520 220" role="img" aria-label={title}>
          {/* grid */}
          <g className="ins-grid">
            {/* horizontal lines */}
            {[0, 1, 2, 3, 4, 5].map((i) => {
              const y = 16 + (172 * i) / 5; // innerH=172
              return <line key={`h-${i}`} x1="38" y1={y} x2="506" y2={y} />;
            })}
            {/* vertical lines (5 segments) */}
            {[0, 1, 2, 3, 4].map((i) => {
              const x = 38 + (468 * i) / 4;
              return <line key={`v-${i}`} x1={x} y1="16" x2={x} y2="188" />;
            })}
          </g>

          {/* y-axis labels */}
          <g className="ins-axisLabels">
            {[5, 4, 3, 2].map((val, idx) => {
              const y = 16 + (172 * idx) / 3;
              return (
                <text key={val} x="12" y={y + 4}>
                  {val}
                </text>
              );
            })}
          </g>

          {/* area fill */}
          <path className={`ins-area ins-area--${tone}`} d={areaPath} />

          {/* line */}
          <path className={`ins-line ins-line--${tone}`} d={path} />

          {/* dots */}
          {points.map((_, i) => {
            const x = 38 + (468 * i) / (points.length - 1 || 1);
            // y-value mapping (0..5)
            const t = points[i] / 5;
            const y = 16 + (1 - t) * 172;
            return (
              <circle
                key={i}
                className={`ins-dot ins-dot--${tone}`}
                cx={x}
                cy={y}
                r="4"
              />
            );
          })}

          {/* x-axis labels */}
          <g className="ins-xLabels">
            {labels.map((lab, i) => {
              const x = 38 + (468 * i) / (labels.length - 1 || 1);
              return (
                <text key={lab} x={x} y="214" textAnchor="middle">
                  {lab}
                </text>
              );
            })}
          </g>
        </svg>
      </div>
    </Card>
  );
}

export default function Insights() {
  const [range, setRange] = useState("7d");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");

  // Placeholder data that matches the mock’s “shape”
  const moodPoints = [4.2, 3.3, 3.0, 3.6, 3.2];
  const moodLabels = ["Feb 18", "Feb 19", "Feb 20", "Feb 21", "Feb 24"];

  const intensityPoints = [4.4, 3.7, 3.6, 3.0, 2.0];
  const intensityLabels = ["Feb 18", "Feb 19", "Feb 22", "Feb 24", "Feb 24"];

  return (
    <main className="ins-page">
      <div className="ins-inner">
        {/* Header row */}
        <div className="ins-topRow">
          <div>
            <div className="ins-subtitle">Patterns and reflections from your recent entries.</div>
          </div>

          <div className="ins-range">
            <select
              className="ins-rangeSelect"
              value={range}
              onChange={(e) => setRange(e.target.value)}
              aria-label="Select date range"
            >
              {RANGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>

            {range === "custom" ? (
              <div className="ins-customDates">
                <label className="ins-dateLabel">
                  <span className="ins-dateLabel__txt">From</span>
                  <input
                    className="ins-dateInput"
                    type="date"
                    value={customFrom}
                    onChange={(e) => setCustomFrom(e.target.value)}
                  />
                </label>
                <label className="ins-dateLabel">
                  <span className="ins-dateLabel__txt">To</span>
                  <input
                    className="ins-dateInput"
                    type="date"
                    value={customTo}
                    onChange={(e) => setCustomTo(e.target.value)}
                  />
                </label>
              </div>
            ) : null}
          </div>
        </div>

        {/* Big summary card */}
        <Card className="ins-summaryCard">
          <div className="ins-summaryTitle">Your emotional pattern lately</div>
          <p className="ins-summaryText">
            You&apos;ve been feeling more stable over the past week, though moments of stress
            appeared midweek. Overall, your tone is balanced, with small dips around busy days.
          </p>
        </Card>

        {/* Two charts row */}
        <div className="ins-grid2">
          <MiniLineChart
            title="Mood Trend"
            subtitle="Average mood over time"
            tone="blue"
            points={moodPoints}
            labels={moodLabels}
          />
          <MiniLineChart
            title="Emotional Intensity"
            subtitle=""
            tone="green"
            points={intensityPoints}
            labels={intensityLabels}
          />
        </div>

        {/* What we're noticing */}
        <Card className="ins-noticingCard">
          <div className="ins-noticingTitle">What We’re Noticing</div>

          <div className="ins-noticingList">
            <InsightRow
              tone="blue"
              text={
                <>
                  You tend to feel more <b>anxious on weekdays</b>
                </>
              }
            />
            <InsightRow
              tone="green"
              text={
                <>
                  Your writing is more <b>positive</b> when you mention family
                </>
              }
            />
            <InsightRow
              tone="purple"
              text={<>Entries written at night are more reflective</>}
            />
          </div>
        </Card>

        {/* Personalized suggestion */}
        <Card className="ins-suggestCard">
          <div className="ins-suggestTitle">Personalized Suggestion</div>
          <div className="ins-suggestText">
            Based on your recent tone, consider taking short breaks midweek. Your mood dips around
            workload-heavy days.
          </div>
        </Card>
      </div>
    </main>
  );
}
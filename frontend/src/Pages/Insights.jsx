import React, { useEffect, useMemo, useState } from "react";
import "./Insights.css";
import MoodTrendChart from "./MoodTrendChart";
import { checkinAPI } from "../services/api";

export default function Insights() {
  const [historyPoints, setHistoryPoints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadHistory() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const response = await checkinAPI.history();
        if (!mounted) return;
        setHistoryPoints(response.data?.entries || []);
      } catch {
        if (!mounted) return;
        setErrorMessage("Could not load mood history right now.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    // Initial data hydration.
    loadHistory();

    // Live append after submission from journal page (rapid submissions included).
    function handleSubmitted(event) {
      const payload = event.detail;
      const nextPoint = {
        date: payload.analysed_at || payload.created_at,
        sentiment_label: payload.sentiment_label || "Pending",
        confidence_score: payload.confidence_score ?? null,
      };
      setHistoryPoints((prev) => [...prev, nextPoint]);
    }

    window.addEventListener("journal:submitted", handleSubmitted);
    return () => {
      mounted = false;
      window.removeEventListener("journal:submitted", handleSubmitted);
    };
  }, []);

  const pendingCount = useMemo(
    () => historyPoints.filter((item) => item.sentiment_label === "Pending").length,
    [historyPoints]
  );

  return (
    <main className="ins-page">
      <div className="ins-inner">
        <div className="ins-topRow">
          <div>
            <div className="ins-subtitle">Patterns and reflections from your recent entries.</div>
          </div>
        </div>

        <div className="ins-card ins-summaryCard">
          <div className="ins-summaryTitle">Your emotional pattern lately</div>
          <p className="ins-summaryText">
            {isLoading
              ? "Loading trend data…"
              : `We tracked ${historyPoints.length} entries, including ${pendingCount} pending analyses.`}
          </p>
          {errorMessage ? <p className="ins-summaryText">{errorMessage}</p> : null}
        </div>

        <div className="ins-gridFull">
          <MoodTrendChart points={historyPoints} title="Mood Trend" />
        </div>
      </div>
    </main>
  );
}
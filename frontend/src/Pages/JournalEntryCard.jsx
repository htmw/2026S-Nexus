import React, { useEffect, useMemo, useState } from "react";
import "./JournalEntryCard.css";
import { checkinAPI } from "../services/api";
import { toast } from "react-hot-toast";

const STORAGE_KEY = "mindmirror:draft";

const MOODS = [
  { key: "awful",  label: "Awful", emoji: "😢" },
  { key: "bad",   label: "Bad",   emoji: "🙁" },
  { key: "meh",   label: "Meh",   emoji: "😐" },
  { key: "good",  label: "Good",  emoji: "😄" },
  { key: "great", label: "Great", emoji: "🤩" },
];

function estimateMood(text, selectedMoodKey) {
  if (selectedMoodKey) {
    const idx = MOODS.findIndex((m) => m.key === selectedMoodKey);
    if (idx !== -1) return { label: MOODS[idx].label, index: idx + 1 };
  }
  return { label: "Neutral", index: 3 };
}

// ── Suggestion card shown after submission ───────────────────────────────────
function SuggestionCard({ suggestion, onDismiss }) {
  return (
    <div className="mm-suggestion-overlay" role="dialog" aria-label="AI Suggestion">
      <div className="mm-suggestion-card">
        <div className="mm-suggestion-card__header">
          <span className="mm-suggestion-card__icon" aria-hidden="true">✦</span>
          <span className="mm-suggestion-card__label">Your personalised suggestion</span>
          <button
            className="mm-suggestion-card__close"
            onClick={onDismiss}
            aria-label="Dismiss suggestion"
          >
            ✕
          </button>
        </div>
        <p className="mm-suggestion-card__text">{suggestion}</p>
        <button className="mm-suggestion-card__btn" onClick={onDismiss}>
          Got it, thanks
        </button>
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function JournalEntryCard({
  title       = "How are you feeling today?",
  subtitle    = "Take a moment to reflect. No format needed — just write naturally.",
  placeholder = "What's on your mind today? How did your day go?",
  maxChars    = 2000,
}) {
  const [text, setText]                 = useState("");
  const [selectedMoodKey, setSelectedMoodKey] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [suggestion, setSuggestion]     = useState(null); // holds suggestion after submit

  const [draftState, setDraftState] = useState({
    loaded: false,
    isDirty: false,
    lastSavedAt: null,
  });

  // Load draft once
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (typeof parsed.text === "string")    setText(parsed.text);
        if (typeof parsed.moodKey === "string") setSelectedMoodKey(parsed.moodKey);
      }
    } catch { /* ignore */ } finally {
      setDraftState((s) => ({ ...s, loaded: true, isDirty: false }));
    }
  }, []);

  // Auto-save draft (debounced)
  useEffect(() => {
    if (!draftState.loaded) return;
    setDraftState((s) => ({ ...s, isDirty: true }));
    const id = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ text, moodKey: selectedMoodKey }));
        setDraftState((s) => ({ ...s, isDirty: false, lastSavedAt: Date.now() }));
      } catch { /* ignore */ }
    }, 400);
    return () => clearTimeout(id);
  }, [text, selectedMoodKey, draftState.loaded]);

  const estimatedMood = useMemo(() => estimateMood(text, selectedMoodKey), [text, selectedMoodKey]);
  const charCount  = text.length;
  const canSubmit  = text.trim().length > 0;

  function handleClear() {
    setText("");
    setSelectedMoodKey(null);
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    setDraftState((s) => ({ ...s, isDirty: false, lastSavedAt: null }));
  }

  async function handleSubmit() {
    if (!canSubmit || isSubmitting) return;
    setIsSubmitting(true);

    try {
      const res = await checkinAPI.create({
        mood:       estimatedMood.index,
        reflection: text.trim() || null,
      });

      // The API returns the full checkin object including the suggestion
      const returnedSuggestion = res?.data?.suggestion;

      handleClear();

      if (returnedSuggestion) {
        // Show the inline suggestion card
        setSuggestion(returnedSuggestion);
      } else {
        toast.success("Entry saved!");
      }
    } catch (err) {
      console.error("Error submitting entry:", err);
      toast.error("Failed to submit entry. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      {/* ── Suggestion overlay ── */}
      {suggestion && (
        <SuggestionCard
          suggestion={suggestion}
          onDismiss={() => setSuggestion(null)}
        />
      )}

      <section className="mm-entry">
        <div className="mm-entry__inner">
          <div className="mm-card">
            <div className="mm-card__header">
              <h2 className="mm-card__title">{title}</h2>
              <p className="mm-card__subtitle">{subtitle}</p>
            </div>

            <textarea
              className="mm-textarea"
              placeholder={placeholder}
              value={text}
              onChange={(e) => {
                const next = e.target.value;
                if (next.length <= maxChars) setText(next);
              }}
            />

            <div className="mm-entry__footer">
              {/* Emoji row + estimated mood */}
              <div className="mm-entry__left">
                <div className="mm-emojiRow" role="group" aria-label="Select mood">
                  {MOODS.map((m) => {
                    const isActive = selectedMoodKey === m.key;
                    return (
                      <button
                        key={m.key}
                        type="button"
                        className={`mm-emojiBtn ${isActive ? "is-active" : ""}`}
                        onClick={() => setSelectedMoodKey((cur) => (cur === m.key ? null : m.key))}
                        aria-pressed={isActive}
                        title={m.label}
                      >
                        <span className="mm-emojiBtn__emoji" aria-hidden="true">{m.emoji}</span>
                      </button>
                    );
                  })}
                </div>
                <div className="mm-estimated">
                  Estimated mood: <span className="mm-estimated__value">{estimatedMood.label}</span>
                </div>
              </div>

              {/* Draft status + char count + actions */}
              <div className="mm-entry__right">
                <div className="mm-metaRow">
                  <span className="mm-metaRow__spacer" aria-hidden="true" />
                  <span className="mm-draft">
                    {draftState.lastSavedAt
                      ? draftState.isDirty ? "Saving…" : "Draft saved"
                      : "Draft not saved yet"}
                  </span>
                  <span className="mm-chars">{charCount} / {maxChars} characters</span>
                </div>

                <div className="mm-actionsRow">
                  <button type="button" className="mm-clear" onClick={handleClear}>
                    Clear draft
                  </button>

                  <button
                    type="button"
                    className={`mm-submit ${canSubmit ? "" : "is-disabled"} ${isSubmitting ? "is-loading" : ""}`}
                    onClick={handleSubmit}
                    disabled={!canSubmit || isSubmitting}
                    aria-label={isSubmitting ? "Submitting entry…" : "Submit Entry"}
                  >
                    <span className="mm-submit__content">
                      <span className="mm-submit__label">Submit Entry</span>
                      <span className="mm-submit__morph" aria-hidden="true">
                        <svg className="mm-submit__writing" viewBox="-2 -1 36 38" fill="none" xmlns="http://www.w3.org/2000/svg">
                        {/* Journal body */}
                        <rect x="1" y="1" width="26" height="34" rx="3" fill="white" fillOpacity="0.15" stroke="white" strokeWidth="1.5"/>
                        {/* Spine */}
                        <line x1="6" y1="1" x2="6" y2="35" stroke="white" strokeWidth="1.3" strokeOpacity="0.5"/>

                        {/* 3 ruled lines — drawn left→right by stroke-dashoffset */}
                        {/* line 1: x 10→24, y=11 */}
                        <line className="mm-jline mm-jline--1" x1="10" y1="11" x2="24" y2="11" stroke="white" strokeWidth="1.3" strokeLinecap="round"/>
                        {/* line 2: x 10→24, y=18 */}
                        <line className="mm-jline mm-jline--2" x1="10" y1="18" x2="24" y2="18" stroke="white" strokeWidth="1.3" strokeLinecap="round"/>
                        {/* line 3: x 10→20, y=25 */}
                        <line className="mm-jline mm-jline--3" x1="10" y1="25" x2="20" y2="25" stroke="white" strokeWidth="1.3" strokeLinecap="round"/>

                        {/*
                          Pen group — the whole pen translates so its tip stays
                          on the line being drawn.
                          Tip of this pen shape is at (0,0) in local coords.
                          We position it so tip = line start, then animate x.
                        */}
                        <g className="mm-pen-group">
                          {/* Pen barrel: tip at local (0,0), barrel extends up-right */}
                          <polygon
                            points="0,0 -2,-3 8,-11 10,-8"
                            fill="white" fillOpacity="0.9"
                            stroke="white" strokeWidth="0.6"
                            strokeLinejoin="round"
                          />
                          {/* Pen clip/top */}
                          <rect x="3" y="-12" width="4" height="5" rx="1"
                            fill="white" fillOpacity="0.5"
                            stroke="white" strokeWidth="0.5"/>
                          {/* Ink nib tip glint */}
                          <circle cx="0" cy="0" r="1" fill="white" fillOpacity="0.95"/>
                        </g>
                      </svg>
                      </span>
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
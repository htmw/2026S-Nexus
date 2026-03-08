import React, { useEffect, useMemo, useState } from "react";
import "./JournalEntryCard.css";
import { checkinAPI } from "../services/api";

const STORAGE_KEY = "mindmirror:draft";

const MOODS = [
  { key: "awful", label: "Awful", emoji: "😢"},
  { key: "bad", label: "Bad", emoji: "🙁"},
  { key: "meh", label: "Meh", emoji: "😐"},
  { key: "good", label: "Good", emoji: "😄"},
  { key: "great", label: "Great", emoji: "🤩"},
];

// function estimateMood(text, selectedMoodKey) {
//   // If user explicitly chose a mood, use it.
//   if (selectedMoodKey) {
//     const found = MOODS.find((m) => m.key === selectedMoodKey);
//     return found ? found.label : "Neutral";
//   }
//   //If not, return neutral
//   return "Neutral";
// }

function estimateMood(text, selectedMoodKey) {
  // If user explicitly chose a mood, use it.
  if (selectedMoodKey) {
    const idx = MOODS.findIndex((m) => m.key === selectedMoodKey);
    if (idx !== -1) {
      return { label: MOODS[idx].label, index: idx + 1 };
    }
  }
  // If not, return neutral.
  return { label: "Neutral", index: 3 };
}

export default function JournalEntryCard({
  title = "How are you feeling today?",
  subtitle = "Take a moment to reflect. No format needed — just write naturally.",
  placeholder = "What's on your mind today? How did your day go?",
  maxChars = 2000,
}) 
{
  const [text, setText] = useState("");
  const [selectedMoodKey, setSelectedMoodKey] = useState(null);

  const [draftState, setDraftState] = useState({
    loaded: false,
    isDirty: false,
    lastSavedAt: null,
  });

  const onSubmitEntry = async (entry) => {
    try {
      await checkinAPI.create({
        mood: entry.mood,
        reflection: entry.text || null,
      });
      alert("Entry submitted successfully!");
    } catch (error) {
      console.error("Error submitting entry:", error);
      alert("Failed to submit entry. Please try again.");
    }
  }

  // Load draft once
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (typeof parsed.text === "string") setText(parsed.text);
        if (typeof parsed.moodKey === "string") setSelectedMoodKey(parsed.moodKey);
      }
    } catch {
      // ignore
    } finally {
      setDraftState((s) => ({ ...s, loaded: true, isDirty: false }));
    }
  }, []);

  // Auto-save draft (debounced-ish)
  useEffect(() => {
    if (!draftState.loaded) return;

    setDraftState((s) => ({ ...s, isDirty: true }));

    const id = setTimeout(() => {
      try {
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ text, moodKey: selectedMoodKey })
        );
        setDraftState((s) => ({
          ...s,
          isDirty: false,
          lastSavedAt: Date.now(),
        }));
      } catch {
        // ignore
      }
    }, 400);

    return () => clearTimeout(id);
  }, [text, selectedMoodKey, draftState.loaded]);

  const estimatedMood = useMemo(
    () => estimateMood(text, selectedMoodKey),
    [text, selectedMoodKey]
  );

  const charCount = text.length;
  const canSubmit = text.trim().length > 0;

  function handleClear() {
    setText("");
    setSelectedMoodKey(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setDraftState((s) => ({ ...s, isDirty: false, lastSavedAt: null }));
  }

  function handleSubmit() {
    if (!canSubmit) return;

    const payload = {
      text: text.trim(),
      mood: estimatedMood.index,
      // createdAt: new Date().toISOString(),
    };
    console.log("Submitting entry:", payload);

    onSubmitEntry(payload);

    // Clear after submit (matches “fresh start”)
    handleClear();
  }

  return (
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
              if (next.length <= maxChars) {
                setText(next);
              }
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
                      onClick={() =>
                        setSelectedMoodKey((cur) => (cur === m.key ? null : m.key))
                      }
                      aria-pressed={isActive}
                      title={m.label}
                    >
                      <span className="mm-emojiBtn__emoji" aria-hidden="true">
                        {m.emoji}
                      </span>
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
                    ? draftState.isDirty
                        ? "Saving…"
                        : "Draft saved"
                    : "Draft not saved yet"}
                </span>
                <span className="mm-chars">
                  {charCount} / {maxChars} characters
                </span>
                </div>

              <div className="mm-actionsRow">
                <button type="button" className="mm-clear" onClick={handleClear}>
                  Clear draft
                </button>
                

                <button
                  type="button"
                  className={`mm-submit ${canSubmit ? "" : "is-disabled"}`}
                  onClick={handleSubmit}
                  disabled={!canSubmit}
                >
                  Submit Entry
                </button>
              </div>

            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
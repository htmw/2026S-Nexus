# Krishna Sprint Tasks

Date updated: 2026-04-10

## Sprint 1 Carry-over (based on current codebase)
This update maps the Sprint 1 task list to what is already implemented in the current backend, frontend, and model pipeline.

### Backend + Model work completed
- Journal submit endpoint exists: `POST /api/checkin` in `backend/app/routes/checkin.py`.
- Pydantic validation exists in `backend/app/schemas/checkin.py`:
  - `mood` constrained to `0..5`
  - `reflection` max length `5000`
- Sentiment service is implemented in `backend/app/services/sentiment_service.py`:
  - local + remote inference fallback
  - label normalization to `POSITIVE/NEUTRAL/NEGATIVE`
  - confidence extraction
  - neutral calibration logic for objective/factual text
- Submission flow integration exists in `backend/app/services/checkin.py`:
  - runs analysis on submit
  - stores `sentiment`, `confidence`, `sentiment_label`, `confidence_score`, `analysed_at`
  - safe fallback when model fails (`analysis_retry_pending` + pending sentiment)
- Mood history for chart exists in `get_mood_history(...)` with pending-safe labels.

### Frontend work completed
- Journal input and submit flow implemented in `frontend/src/Pages/JournalEntryCard.jsx`.
- Validation and UX checks implemented:
  - no empty submission (`canSubmit` requires non-empty trimmed text)
  - max length enforced by textarea and backend schema
- API integration implemented in `frontend/src/services/api.js` and used in `JournalEntryCard.jsx`.
- Success/failure feedback implemented with toast messages (`react-hot-toast`).
- No page reload behavior implemented via event-based update (`journal:submitted`).
- Insights chart implemented in `frontend/src/Pages/MoodTrendChart.jsx` and wired in `frontend/src/Pages/Insights.jsx`.

## User Story status summary

### US1 — Journal input form
- **Status:** Done
- **What is done:** Form UI, mood selector, draft save/clear, submit button and handling in `JournalEntryCard.jsx`.

### US2 — Submit to backend
- **Status:** Done
- **What is done:** `checkinAPI.create(...)` to `POST /api/checkin` and tested in running app flow.

### US3 — Sentiment model integration
- **Status:** Mostly done
- **What is done:** DistilBERT/transformers setup, sentiment function, output mapping, confidence extraction, POST flow integration, persistence in DB/fallback store.
- **Evidence:** `backend/requirements.txt`, `backend/app/services/sentiment_service.py`, `backend/app/services/checkin.py`.

### US4 — Extract confidence probability
- **Status:** Done
- **What is done:** Confidence extracted and normalized; returned and stored as `confidence` and `confidence_score`.

### US5 — Show sentiment + confidence in UI
- **Status:** Done
- **What is done:** UI renders sentiment feedback and confidence in chart tooltip; submit response shown without reload.

### US6 — Charts (explicit update requested)
- **Status:** Done (custom SVG implementation instead of chart library)
- **Whats implemented:**
  - Interactive dual chart modes (mountain + bar) with toggle
  - Dynamic windowing/slider for large datasets
  - Live update after submit via `journal:submitted`
  - Tooltip with date/sentiment/confidence
  - Responsive scaling and overflow handling (clip path + insets)
  - Neutral/positive/negative visual mapping fixes
- **Files:** `frontend/src/Pages/MoodTrendChart.jsx`, `frontend/src/Pages/MoodTrendChart.css`, `frontend/src/Pages/Insights.jsx`.

### US7 — Validation (frontend + backend)
- **Status:** Mostly done
- **What is done:** frontend empty/max checks + backend Pydantic constraints and validation response flow.

### US8 — Success message
- **Status:** Done
- **What is done:** success toast on submit in `JournalEntryCard.jsx`.

### US9 — Error handling
- **Status:** Done
- **What is done:**
  - Model failure fallback handling in backend
  - Network/API error handling in frontend with toast
  - Friendly messages in insights load failure path

### US10 — Clear textarea after submit
- **Status:** Done
- **What is done:** `handleClear()` executed after successful submit flow.

### US11 — Registration
- **Status:** Not implemented in current codebase

### US12 — JWT login/auth flow
- **Status:** Not implemented as JWT (current auth is header-based context for local/dev)

### US13 — Journal history retrieval
- **Status:** Done
- **What is done:** retrieval endpoints and frontend history/insights display are implemented.


## Additional Work Beyond US13 (Sprint 2 / Current)

### US14 — Therapist patient journal access
- **Status:** Done
- **What is done:** Therapist endpoints and access checks are implemented in backend service/route layer and consumed by frontend therapist views.

### US15 — Therapist mood trend access
- **Status:** Done
- **What is done:** Read-only trend retrieval for therapist patient context is implemented and aligned with sharing/authorization checks.

### US16 — Therapist UI pages
- **Status:** Done
- **What is done:** Therapist dashboard + patient detail flows are implemented in frontend routes/components and display patient entries/trend data.

### US17 — Chart stability + responsiveness hardening
- **Status:** Done
- **What is done:**
  - Fixed chart crashes caused by hook-order and browser resize compatibility issues.
  - Added clipping/insets to prevent out-of-bounds rendering.
  - Made chart full-width in insights layout.

### US18 — Advanced chart interactivity
- **Status:** Done
- **What is done:**
  - Dual chart modes (mountain + bar) retained with improved responsiveness.
  - Slider/windowing added for larger datasets.
  - Tooltips and hover/click behavior improved.

### US19 — Neutral sentiment calibration improvement
- **Status:** Done
- **What is done:** Added neutral calibration in sentiment service for objective/factual text and low-confidence polarity outputs.

### US20 — Current ongoing / next tasks
- **Status:** In progress
- **Planned next:**
  - ReUSgistration flow completion (US11)
  - JWT auth flow completion (US12)
  - Retrospective artifacts completion (TASK-R1/TASK-R2)

# Krishna Sprint 2 Task Verification

Date updated: 2026-04-11

This file tracks only the backlog items assigned to **Krishna** from the Sprint 2 task sheet and verifies them against the current repository code.

## Summary

- Krishna-assigned tasks reviewed: **15**
- Completed: **15 / 15**

## Verified Krishna Tasks

### US6

1. **Build backend endpoint for mood history** — **Done**  
   Evidence: `backend/app/routes/mood.py` (`GET /api/mood/history`), `backend/app/services/checkin.py` (`get_mood_history`).

2. **Ensure chart updates after new entry submission** — **Done**  
   Evidence: `frontend/src/Pages/JournalEntryCard.jsx` dispatches `journal:submitted`; `frontend/src/Pages/Insights.jsx` listens and appends a point.

3. **Write unit & integration tests for mood history endpoint** — **Done**  
   Evidence: `backend/tests/test_mood_history_route.py`, `backend/tests/test_mood_history_integration.py`.

### US15

4. **Add sentiment fields to JournalEntry schema** — **Done**  
   Evidence: `backend/migrations/2026_04_10_add_journal_sentiment_fields.py` adds/backfills `sentiment_label`, `confidence_score`, `analysed_at`, plus supporting indexes.

5. **Persist sentiment result after ML analysis** — **Done**  
   Evidence: `backend/app/services/checkin.py` stores `sentiment_label`, `confidence_score`, `analysed_at`, and fallback `analysis_retry_pending`.

6. **Create GET /api/mood/history endpoint returning stored data** — **Done**  
   Evidence: `backend/app/routes/mood.py`, `backend/app/services/checkin.py` (ordered by `created_at`, pending-safe labels).

### US18

7. **Add interactive tooltips to chart data points** — **Done**  
   Evidence: `frontend/src/Pages/MoodTrendChart.jsx` (`mood-tooltip`, hover/click handlers, date/sentiment/confidence display).

8. **Ensure chart is responsive on mobile screens** — **Done**  
   Evidence: `frontend/src/Pages/MoodTrendChart.jsx` (`ResizeObserver`, dynamic visible window sizing by width).

9. **Write visual regression / render tests for chart** — **Done**  
   Evidence: `frontend/src/Pages/__tests__/MoodTrendChart.test.jsx` covers 0, 1, and 10-entry snapshots plus tooltip assertion.

### US24

10. **Build GET /api/therapist/patients/:patientId/journal endpoint** — **Done**  
    Evidence: `backend/app/routes/therapist.py` (`GET /api/therapist/patients/{patient_id}/journal`) + service gating in `backend/app/services/checkin.py`.

11. **Build GET /api/therapist/patients/:patientId/mood endpoint** — **Done**  
    Evidence: `backend/app/routes/therapist.py` (`GET /api/therapist/patients/{patient_id}/mood`) + trend service query in `backend/app/services/checkin.py`.

12. **Build patient detail view UI for therapist** — **Done**  
    Evidence: `frontend/src/Pages/PatientDetail.jsx` loads profile, journal entries, and mood chart (read-only).

13. **Display sharing-off message** — **Done**  
    Evidence: `frontend/src/Pages/PatientDetail.jsx` renders: “This patient has not shared their data with you.” on 403.

14. **Ensure therapist cannot edit/delete patient data** — **Done**  
    Evidence: `backend/app/auth.py` `reject_therapist_mutations(...)` blocks therapist mutating methods on `/api/therapist/patients*` with 403.

15. **Write end-to-end tests for therapist data access** — **Done**  
    Evidence:
    - `backend/tests/test_therapist_access.py` (route-level scenarios)
    - `backend/tests/test_therapist_access_integration.py` (integration scenarios using real test DB when `TEST_MONGODB_URI` is set).

## Notes

- Backward-compatible aliases are still available for prior frontend usage:
  - `/api/therapist/patients/{patient_id}/journal-entries`
  - `/api/therapist/patients/{patient_id}/mood-trend`
- Canonical US24 paths are now implemented and available:
  - `/api/therapist/patients/{patient_id}/journal`
  - `/api/therapist/patients/{patient_id}/mood`

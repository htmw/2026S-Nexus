import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.schemas.checkin import (
    ChartData,
    ChartDataset,
    CheckinResponse,
    InsightResponse,
)
from app.services.auth import get_current_user_id
from app.services.checkin import get_checkins_by_user

router = APIRouter(tags=["Insight"])


def _date_key(dt: datetime) -> date:
    """Normalize to date in UTC for grouping."""
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).date()
    return dt.date()


def _as_utc(dt: datetime) -> datetime:
    """Return datetime as timezone-aware UTC (assume naive datetimes are UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _mood_consistency_score(moods: list[float]) -> float | None:
    """
    Return 0–100 consistency score; higher = more consistent.
    Based on inverse of standard deviation (mood scale 0–5).
    """
    if len(moods) < 2:
        return 100.0 if moods else None
    n = len(moods)
    mean = sum(moods) / n
    variance = sum((x - mean) ** 2 for x in moods) / n
    stdev = math.sqrt(variance)
    # stdev 0 -> 100, stdev ~2.5 -> ~37, stdev 4 -> 0
    score = max(0.0, min(100.0, 100.0 - stdev * 25.0))
    return round(score, 1)


def _weekly_summary(
    recent: list[dict],
    mood_avg_7d: float | None,
    sentiment_avg_7d: float | None,
    consistency: float | None,
) -> str:
    """Generate a short weekly summary sentence."""
    n = len(recent)
    if n == 0:
        return (
            "No check-ins in the last 7 days. "
            "Add a check-in to see your weekly summary here."
        )
    parts = [f"This week you had {n} check-in{'s' if n != 1 else ''}."]
    if mood_avg_7d is not None:
        parts.append(f" Your mood averaged {mood_avg_7d:.1f} out of 5.")
    if consistency is not None:
        if consistency >= 70:
            parts.append(" Your mood was quite consistent.")
        elif consistency >= 40:
            parts.append(" Your mood showed some variation.")
        else:
            parts.append(" Your mood varied noticeably—consider what’s influencing the swings.")
    if sentiment_avg_7d is not None and n > 0:
        parts.append(f" Reflection sentiment averaged {sentiment_avg_7d:.1f}.")
    return "".join(parts).strip()


def _build_chart_data(
    docs: list[dict],
) -> tuple[ChartData | None, ChartData | None, ChartData | None]:
    """
    Build mood trend, sentiment trend, and 7-day rolling average
    as Chart.js-ready structures. Uses daily aggregation.
    """
    if not docs:
        return None, None, None

    # Group by date (UTC)
    by_date: dict[date, list[tuple[float, float | None]]] = defaultdict(list)
    for doc in docs:
        d = _date_key(doc["created_at"])
        sentiment = doc.get("sentiment_score")
        by_date[d].append((float(doc["mood"]), sentiment))

    dates_sorted = sorted(by_date.keys())

    # Daily averages for mood and sentiment
    mood_by_date = []
    sentiment_by_date = []
    for d in dates_sorted:
        moods = [m for m, _ in by_date[d]]
        mood_by_date.append(round(sum(moods) / len(moods), 2))
        sents = [s for _, s in by_date[d] if s is not None]
        sentiment_by_date.append(
            round(sum(sents) / len(sents), 2) if sents else None
        )

    labels = [d.isoformat() for d in dates_sorted]

    mood_trend = ChartData(
        labels=labels,
        datasets=[ChartDataset(label="Mood", data=mood_by_date)],
    )

    # Sentiment trend: only include dates that have at least one sentiment
    sent_labels = []
    sent_data = []
    for i, s in enumerate(sentiment_by_date):
        if s is not None:
            sent_labels.append(labels[i])
            sent_data.append(s)
    sentiment_trend = (
        ChartData(
            labels=sent_labels,
            datasets=[ChartDataset(label="Sentiment", data=sent_data)],
        )
        if sent_labels
        else None
    )

    # 7-day rolling average: for each date, average over that day and previous 6
    date_list = list(dates_sorted)
    mood_rolling = []
    sentiment_rolling = []
    for i in range(len(date_list)):
        start_idx = max(0, i - 6)
        window_dates = date_list[start_idx : i + 1]
        window_moods = []
        window_sents = []
        for d in window_dates:
            for m, s in by_date[d]:
                window_moods.append(m)
                if s is not None:
                    window_sents.append(s)
        mood_rolling.append(
            round(sum(window_moods) / len(window_moods), 2)
            if window_moods
            else None
        )
        sentiment_rolling.append(
            round(sum(window_sents) / len(window_sents), 2)
            if window_sents
            else None
        )

    rolling_average_7d = ChartData(
        labels=labels,
        datasets=[
            ChartDataset(label="Mood (7-day avg)", data=mood_rolling),
            ChartDataset(label="Sentiment (7-day avg)", data=sentiment_rolling),
        ],
    )

    return mood_trend, sentiment_trend, rolling_average_7d


@router.get(
    "/insight",
    response_model=InsightResponse,
    summary="Get user insight with check-in history and trends",
)
async def get_insight(user_id: str = Depends(get_current_user_id)):
    docs = await get_checkins_by_user(user_id)

    checkins = [
        CheckinResponse(
            id=doc["_id"],
            user_id=doc["user_id"],
            mood=doc["mood"],
            reflection=doc.get("reflection"),
            sentiment_score=doc.get("sentiment_score"),
            sentiment_label=doc.get("sentiment_label"),
            sentiment_confidence=doc.get("sentiment_confidence"),
            emotion_label=doc.get("emotion_label"),
            emotion_confidence=doc.get("emotion_confidence"),
            suggestion=doc.get("suggestion"),
            created_at=doc["created_at"],
        )
        for doc in docs
    ]

    # Chart.js-ready trend and rolling average data
    mood_trend, sentiment_trend, rolling_average_7d = _build_chart_data(docs)

    # Scalar 7-day averages (last 7 days from now)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = [
        doc
        for doc in docs
        if _as_utc(doc["created_at"]) >= seven_days_ago
    ]

    mood_avg_7d = None
    sentiment_avg_7d = None

    mood_consistency_score = None
    if recent:
        moods = [doc["mood"] for doc in recent]
        mood_avg_7d = round(sum(moods) / len(moods), 2)
        mood_consistency_score = _mood_consistency_score(moods)

        sentiments = [
            doc["sentiment_score"]
            for doc in recent
            if doc.get("sentiment_score") is not None
        ]
        if sentiments:
            sentiment_avg_7d = round(sum(sentiments) / len(sentiments), 2)

    weekly_summary = _weekly_summary(
        recent,
        mood_avg_7d,
        sentiment_avg_7d,
        mood_consistency_score,
    )
    suggestion = docs[0].get("suggestion")

    return InsightResponse(
        checkins=checkins,
        mood_average_7d=mood_avg_7d,
        sentiment_average_7d=sentiment_avg_7d,
        mood_consistency_score=mood_consistency_score,
        weekly_summary=weekly_summary,
        mood_trend=mood_trend,
        sentiment_trend=sentiment_trend,
        rolling_average_7d=rolling_average_7d,
        suggestion=suggestion,
    )

from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def dashboard():
    return {
        "today_visitors": 0,
        "weekly_visitors": 0,
        "total_visitors": 0,
        "satisfaction_rate": 0.0,
        "hot_questions": [],
        "trend_data": [],
    }


@router.get("/reports/sentiment")
async def sentiment_report(days: int = 7):
    return {
        "period": f"last_{days}_days",
        "positive_ratio": 0.0,
        "negative_ratio": 0.0,
        "neutral_ratio": 0.0,
        "trend": [],
        "hot_topics": [],
        "suggestions": [],
    }


@router.get("/interactions")
async def interaction_logs(page: int = 1, size: int = 20):
    return {"page": page, "size": size, "total": 0, "items": []}

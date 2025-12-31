from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel
from typing import List

from api.auth import get_current_admin
from services.supabase_service import SupabaseService
from services.analytics import AnalyticsService

router = APIRouter()

# Initialize services
supabase_service = SupabaseService()
analytics_service = AnalyticsService()


class DashboardSummary(BaseModel):
    total_users: int
    completed_users: int
    completion_rate: float
    avg_depression_score: float
    avg_anxiety_score: float


class TrendItem(BaseModel):
    date: str
    new_users: int
    completions: int


class ActivityItem(BaseModel):
    user_id: str
    user_name: str
    username: Optional[str]
    event_type: str
    phase: Optional[str]
    timestamp: str


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(current_admin: dict = Depends(get_current_admin)):
    """
    Get key dashboard metrics
    """
    stats = await supabase_service.get_dashboard_stats()
    return DashboardSummary(
        total_users=stats.get('total_users', 0),
        completed_users=stats.get('completed_users', 0),
        completion_rate=stats.get('completion_rate', 0),
        avg_depression_score=stats.get('avg_depression_score', 0),
        avg_anxiety_score=stats.get('avg_anxiety_score', 0)
    )


@router.get("/trends", response_model=List[TrendItem])
async def get_daily_trends(
    days: int = Query(default=30, ge=1, le=90),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get daily user and completion trends
    """
    trends = await analytics_service.get_daily_stats(days)
    return [TrendItem(**t) for t in trends]


@router.get("/recent", response_model=List[ActivityItem])
async def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get recent user activity
    """
    activity = await analytics_service.get_recent_activity(limit)
    return [ActivityItem(**a) for a in activity]

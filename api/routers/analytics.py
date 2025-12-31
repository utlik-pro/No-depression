from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel

from api.auth import get_current_admin
from services.supabase_service import SupabaseService
from services.analytics import AnalyticsService

router = APIRouter()

# Initialize services
supabase_service = SupabaseService()
analytics_service = AnalyticsService()


class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float


class QuestionDropoff(BaseModel):
    question_index: int
    question_type: str
    reached: int
    dropped: int


class ScoreDistribution(BaseModel):
    depression: Dict[str, int]
    anxiety: Dict[str, int]


class DemographicsStats(BaseModel):
    gender: Dict[str, int]
    age: Dict[str, int]
    location: Dict[str, int]


@router.get("/funnel", response_model=List[FunnelStage])
async def get_funnel_analytics(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get conversion funnel data showing dropoff at each stage
    """
    funnel_data = await supabase_service.get_funnel_data()

    return [FunnelStage(
        stage=item.get('stage', ''),
        count=item.get('count', 0),
        percentage=item.get('percentage', 0)
    ) for item in funnel_data]


@router.get("/question-dropoff", response_model=List[QuestionDropoff])
async def get_question_dropoff(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get per-question dropoff analysis
    Shows which questions users drop off at most frequently
    """
    dropoff_data = await analytics_service.get_question_dropoff_stats()

    return [QuestionDropoff(
        question_index=item.get('index', 0),
        question_type=item.get('type', ''),
        reached=item.get('reached', 0),
        dropped=item.get('dropped', 0)
    ) for item in dropoff_data]


@router.get("/scores", response_model=ScoreDistribution)
async def get_score_distribution(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get score distribution for depression and anxiety tests
    """
    distribution = await supabase_service.get_score_distribution()

    return ScoreDistribution(
        depression=distribution.get('depression', {}),
        anxiety=distribution.get('anxiety', {})
    )


@router.get("/demographics", response_model=DemographicsStats)
async def get_demographics(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get demographic breakdown of completed tests
    """
    demographics = await supabase_service.get_demographics_stats()

    return DemographicsStats(
        gender=demographics.get('gender', {}),
        age=demographics.get('age', {}),
        location=demographics.get('location', {})
    )

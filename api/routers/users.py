from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
import io
import csv

from api.auth import get_current_admin
from services.supabase_service import SupabaseService
from services.analytics import AnalyticsService

router = APIRouter()

# Initialize services
supabase_service = SupabaseService()
analytics_service = AnalyticsService()


class UserSummary(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    gender: Optional[str]
    age_group: Optional[str]
    location: Optional[str]
    current_phase: Optional[str]
    test_completed: Optional[bool]
    depression_score: Optional[int]
    anxiety_score: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


class UserDetail(UserSummary):
    url: Optional[str]
    consent_given: Optional[bool]
    current_question: Optional[int]
    demographic_question: Optional[int]
    completed_at: Optional[str]


class UserEvent(BaseModel):
    id: Optional[str]
    event_type: str
    phase: Optional[str]
    question_index: Optional[int]
    question_type: Optional[str]
    metadata: Optional[str]
    created_at: str


class PaginatedUsers(BaseModel):
    users: List[UserSummary]
    total: int
    page: int
    limit: int


@router.get("/", response_model=PaginatedUsers)
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    status: Optional[str] = Query(default=None, description="Filter by status: completed, in_progress, dropped"),
    search: Optional[str] = Query(default=None, description="Search by name or username"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get paginated list of users with optional filters
    """
    result = await supabase_service.get_users_paginated(page, limit, status, search)

    users = [UserSummary(
        id=u.get('id', ''),
        first_name=u.get('first_name'),
        last_name=u.get('last_name'),
        username=u.get('username'),
        gender=u.get('gender'),
        age_group=u.get('age_group'),
        location=u.get('location'),
        current_phase=u.get('current_phase'),
        test_completed=u.get('test_completed'),
        depression_score=u.get('depression_score'),
        anxiety_score=u.get('anxiety_score'),
        created_at=u.get('created_at'),
        updated_at=u.get('updated_at')
    ) for u in result.get('users', [])]

    return PaginatedUsers(
        users=users,
        total=result.get('total', 0),
        page=page,
        limit=limit
    )


@router.get("/export")
async def export_users(
    status: Optional[str] = Query(default=None),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Export users to CSV
    """
    # Get all users (up to 10000)
    result = await supabase_service.get_users_paginated(1, 10000, status)
    users = result.get('users', [])

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'ID', 'Имя', 'Фамилия', 'Username', 'Пол', 'Возраст',
        'Регион', 'Статус', 'Депрессия', 'Тревога', 'Дата'
    ])

    # Data
    for user in users:
        writer.writerow([
            user.get('id', ''),
            user.get('first_name', ''),
            user.get('last_name', ''),
            user.get('username', ''),
            user.get('gender', ''),
            user.get('age_group', ''),
            user.get('location', ''),
            'Завершен' if user.get('test_completed') else 'В процессе',
            user.get('depression_score', ''),
            user.get('anxiety_score', ''),
            user.get('created_at', '')[:10] if user.get('created_at') else ''
        ])

    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )


@router.get("/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get detailed user information
    """
    user = await supabase_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return UserDetail(
        id=user.get('id', ''),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        username=user.get('username'),
        url=user.get('url'),
        gender=user.get('gender'),
        age_group=user.get('age_group'),
        location=user.get('location'),
        current_phase=user.get('current_phase'),
        test_completed=user.get('test_completed'),
        consent_given=user.get('consent_given'),
        current_question=user.get('current_question'),
        demographic_question=user.get('demographic_question'),
        depression_score=user.get('depression_score'),
        anxiety_score=user.get('anxiety_score'),
        created_at=user.get('created_at'),
        updated_at=user.get('updated_at'),
        completed_at=user.get('completed_at')
    )


@router.get("/{user_id}/events", response_model=List[UserEvent])
async def get_user_events(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get user event timeline
    """
    events = await analytics_service.get_user_events(user_id)

    return [UserEvent(
        id=e.get('id'),
        event_type=e.get('event_type', ''),
        phase=e.get('phase'),
        question_index=e.get('question_index'),
        question_type=e.get('question_type'),
        metadata=e.get('metadata'),
        created_at=e.get('created_at', '')
    ) for e in events]

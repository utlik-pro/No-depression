from datetime import datetime
import json
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from utils import logger


class AnalyticsService:
    """
    Service for tracking user analytics events
    Events are stored in the analytics_events table for detailed dropoff analysis
    """

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase credentials not configured. Analytics will not work.")
            self.client = None
        else:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Analytics service initialized")

    async def track_event(self, user_id: str, event_type: str, phase: str = None,
                          question_index: int = None, question_type: str = None,
                          metadata: dict = None):
        """
        Track an analytics event

        Args:
            user_id: Telegram user ID
            event_type: Type of event (session_start, phase_start, phase_complete,
                       question_answered, test_completed, dropoff)
            phase: Current phase (consent, demographic, mixed_test)
            question_index: Question number (0-indexed)
            question_type: Type of question (depression, anxiety)
            metadata: Additional event data as dict
        """
        if not self.client:
            return False

        try:
            event_data = {
                'user_id': user_id,
                'event_type': event_type,
                'phase': phase,
                'question_index': question_index,
                'question_type': question_type,
                'metadata': json.dumps(metadata) if metadata else None,
                'created_at': datetime.now().isoformat()
            }

            self.client.table('analytics_events').insert(event_data).execute()
            logger.debug(f"Analytics event tracked: {event_type} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking analytics event: {e}")
            return False

    async def track_session_start(self, user_id: str):
        """Track when user starts a session (sends /start)"""
        return await self.track_event(user_id, 'session_start', phase='consent')

    async def track_consent(self, user_id: str, consented: bool):
        """Track consent decision"""
        return await self.track_event(
            user_id,
            'phase_complete' if consented else 'dropoff',
            phase='consent',
            metadata={'consented': consented}
        )

    async def track_demographic_answer(self, user_id: str, question_index: int, answer: str):
        """Track demographic question answer"""
        return await self.track_event(
            user_id,
            'question_answered',
            phase='demographic',
            question_index=question_index,
            metadata={'answer': answer}
        )

    async def track_demographic_complete(self, user_id: str):
        """Track demographic phase completion"""
        return await self.track_event(user_id, 'phase_complete', phase='demographic')

    async def track_test_answer(self, user_id: str, question_index: int,
                                 question_type: str, score: int, answer: str):
        """Track test question answer"""
        return await self.track_event(
            user_id,
            'question_answered',
            phase='mixed_test',
            question_index=question_index,
            question_type=question_type,
            metadata={'score': score, 'answer': answer}
        )

    async def track_test_complete(self, user_id: str, depression_score: int, anxiety_score: int):
        """Track test completion"""
        return await self.track_event(
            user_id,
            'test_completed',
            phase='mixed_test',
            metadata={
                'depression_score': depression_score,
                'anxiety_score': anxiety_score
            }
        )

    # === Analytics Query Methods ===

    async def get_user_events(self, user_id: str):
        """Get all events for a specific user (timeline)"""
        if not self.client:
            return []

        try:
            result = self.client.table('analytics_events').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=False).execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting user events: {e}")
            return []

    async def get_question_dropoff_stats(self):
        """
        Get statistics about where users drop off in the test
        Returns count of users who answered each question and who stopped at each question
        """
        if not self.client:
            return []

        try:
            # Get all question_answered events for mixed_test phase
            result = self.client.table('analytics_events').select(
                'user_id, question_index, question_type'
            ).eq('event_type', 'question_answered').eq('phase', 'mixed_test').execute()

            # Process data to find last question per user
            user_progress = {}
            for event in result.data:
                user_id = event['user_id']
                q_idx = event['question_index']
                q_type = event['question_type']

                if user_id not in user_progress:
                    user_progress[user_id] = {'max_question': -1, 'questions': set()}

                user_progress[user_id]['questions'].add((q_idx, q_type))
                if q_idx > user_progress[user_id]['max_question']:
                    user_progress[user_id]['max_question'] = q_idx

            # Get completed users
            completed_result = self.client.table('analytics_events').select(
                'user_id'
            ).eq('event_type', 'test_completed').execute()
            completed_users = set(e['user_id'] for e in completed_result.data)

            # Calculate dropoff at each question
            question_stats = {}
            for user_id, data in user_progress.items():
                for q_idx, q_type in data['questions']:
                    key = f"{q_type}_{q_idx}"
                    if key not in question_stats:
                        question_stats[key] = {'reached': 0, 'dropped': 0, 'type': q_type, 'index': q_idx}
                    question_stats[key]['reached'] += 1

                # Check if user dropped at this question
                if user_id not in completed_users:
                    max_q = data['max_question']
                    # Find the type of the max question
                    for q_idx, q_type in data['questions']:
                        if q_idx == max_q:
                            key = f"{q_type}_{q_idx}"
                            question_stats[key]['dropped'] += 1
                            break

            # Convert to list and sort
            stats_list = sorted(question_stats.values(), key=lambda x: x['index'])
            return stats_list

        except Exception as e:
            logger.error(f"Error getting question dropoff stats: {e}")
            return []

    async def get_daily_stats(self, days: int = 30):
        """Get daily user registration and completion stats"""
        if not self.client:
            return []

        try:
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get session starts (new users)
            sessions_result = self.client.table('analytics_events').select(
                'user_id, created_at'
            ).eq('event_type', 'session_start').gte(
                'created_at', start_date.isoformat()
            ).execute()

            # Get completions
            completions_result = self.client.table('analytics_events').select(
                'user_id, created_at'
            ).eq('event_type', 'test_completed').gte(
                'created_at', start_date.isoformat()
            ).execute()

            # Group by date
            daily_data = {}
            for event in sessions_result.data:
                date = event['created_at'][:10]  # YYYY-MM-DD
                if date not in daily_data:
                    daily_data[date] = {'date': date, 'new_users': 0, 'completions': 0}
                daily_data[date]['new_users'] += 1

            for event in completions_result.data:
                date = event['created_at'][:10]
                if date not in daily_data:
                    daily_data[date] = {'date': date, 'new_users': 0, 'completions': 0}
                daily_data[date]['completions'] += 1

            # Sort by date
            return sorted(daily_data.values(), key=lambda x: x['date'])

        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return []

    async def get_recent_activity(self, limit: int = 10):
        """Get recent user activity for dashboard"""
        if not self.client:
            return []

        try:
            result = self.client.table('analytics_events').select(
                'user_id, event_type, phase, created_at'
            ).order('created_at', desc=True).limit(limit).execute()

            # Get user names for the events
            user_ids = list(set(e['user_id'] for e in result.data))
            users_result = self.client.table('users').select(
                'id, first_name, last_name, username'
            ).in_('id', user_ids).execute()

            users_map = {u['id']: u for u in users_result.data}

            # Combine data
            activity = []
            for event in result.data:
                user = users_map.get(event['user_id'], {})
                activity.append({
                    'user_id': event['user_id'],
                    'user_name': user.get('first_name', 'Unknown'),
                    'username': user.get('username'),
                    'event_type': event['event_type'],
                    'phase': event['phase'],
                    'timestamp': event['created_at']
                })

            return activity

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

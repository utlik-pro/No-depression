from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from utils import logger


class SupabaseService:
    """
    Supabase service that mirrors the SQLiteService interface
    for seamless migration from SQLite to Supabase
    """

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase credentials not configured. Service will not work.")
            self.client = None
        else:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized")

    def _get_current_time(self):
        """Get current timestamp in ISO format for Supabase"""
        return datetime.now().isoformat()

    async def save_user(self, user_data):
        """Save user information to Supabase"""
        if not self.client:
            return False

        try:
            current_time = self._get_current_time()

            # Check if user exists
            result = self.client.table('users').select('id').eq('id', user_data['id']).execute()

            if result.data:
                # Update existing user
                self.client.table('users').update({
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'username': user_data['username'],
                    'url': user_data['url'],
                    'current_phase': 'demographic',
                    'demographic_question': 0,
                    'updated_at': current_time
                }).eq('id', user_data['id']).execute()
            else:
                # Insert new user
                self.client.table('users').insert({
                    'id': user_data['id'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'username': user_data['username'],
                    'url': user_data['url'],
                    'current_question': 0,
                    'depression_score': -1,
                    'anxiety_score': -1,
                    'demographic_question': 0,
                    'current_phase': 'demographic',
                    'consent_given': False,
                    'test_completed': False,
                    'created_at': current_time,
                    'updated_at': current_time
                }).execute()

            logger.info(f"User {user_data['id']} saved to Supabase")
            return True

        except Exception as e:
            logger.error(f"Error saving user to Supabase: {e}")
            return False

    async def init_demographic_questions(self, user_id):
        """Initialize the demographic questions phase for a user"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'current_phase': 'demographic',
                'demographic_question': 0,
                'updated_at': self._get_current_time()
            }).eq('id', user_id).execute()

            logger.info(f"Demographic questions initialized for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error initializing demographic questions in Supabase: {e}")
            return False

    async def save_demographic_data(self, user_id, gender, age_group, location):
        """Save demographic data for a user"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'gender': gender,
                'age_group': age_group,
                'location': location,
                'updated_at': self._get_current_time()
            }).eq('id', user_id).execute()

            logger.info(f"Demographic data for user {user_id} saved to Supabase")
            return True

        except Exception as e:
            logger.error(f"Error saving demographic data to Supabase: {e}")
            return False

    async def update_demographic_question(self, user_id, question_num):
        """Update the current demographic question number"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'demographic_question': question_num,
                'updated_at': self._get_current_time()
            }).eq('id', user_id).execute()

            logger.info(f"Demographic question for user {user_id} updated to {question_num}")
            return True

        except Exception as e:
            logger.error(f"Error updating demographic question in Supabase: {e}")
            return False

    async def get_user_gender(self, user_id):
        """Get user's gender from Supabase"""
        if not self.client:
            return None

        try:
            result = self.client.table('users').select('gender').eq('id', user_id).execute()

            if result.data:
                return result.data[0]['gender']
            return None

        except Exception as e:
            logger.error(f"Error getting user gender from Supabase: {e}")
            return None

    async def save_mixed_test_progress(self, progress_data):
        """Save mixed test progress"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'question_order_json': progress_data['question_order_json'],
                'current_question': progress_data['current_question'],
                'current_phase': 'mixed_test',
                'updated_at': self._get_current_time()
            }).eq('id', progress_data['user_id']).execute()

            logger.info(f"Mixed test progress for user {progress_data['user_id']} saved to Supabase")
            return True

        except Exception as e:
            logger.error(f"Error saving mixed test progress to Supabase: {e}")
            return False

    async def update_question_progress(self, user_id, next_question):
        """Update the current question index"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'current_question': next_question,
                'updated_at': self._get_current_time()
            }).eq('id', user_id).execute()

            logger.info(f"Question progress for user {user_id} updated to {next_question}")
            return True

        except Exception as e:
            logger.error(f"Error updating question progress in Supabase: {e}")
            return False

    async def save_test_result(self, user_id, test_type, score):
        """Save test result"""
        if not self.client:
            return False

        try:
            update_data = {'updated_at': self._get_current_time()}

            if test_type == "depression":
                update_data['depression_score'] = score
            elif test_type == "anxiety":
                update_data['anxiety_score'] = score

            self.client.table('users').update(update_data).eq('id', user_id).execute()

            logger.info(f"{test_type.capitalize()} test result for user {user_id} saved to Supabase: {score}")
            return True

        except Exception as e:
            logger.error(f"Error saving test result to Supabase: {e}")
            return False

    async def get_test_progress(self, user_id):
        """Get test progress including question order"""
        if not self.client:
            return None

        try:
            result = self.client.table('users').select(
                'current_question, question_order_json, depression_score, anxiety_score, '
                'gender, current_phase, demographic_question, age_group'
            ).eq('id', user_id).execute()

            if result.data:
                row = result.data[0]
                return {
                    "user_id": user_id,
                    "current_question": row['current_question'],
                    "question_order_json": row['question_order_json'],
                    "depression_score": row['depression_score'],
                    "anxiety_score": row['anxiety_score'],
                    "gender": row['gender'],
                    "current_phase": row['current_phase'],
                    "demographic_question": row['demographic_question'],
                    "age_group": row['age_group']
                }
            return None

        except Exception as e:
            logger.error(f"Error getting test progress from Supabase: {e}")
            return None

    async def reset_test_progress(self, user_id, keep_results=False):
        """Reset test progress, optionally keeping test results"""
        if not self.client:
            return False

        try:
            update_data = {
                'question_order_json': None,
                'current_question': 0,
                'current_phase': 'demographic',
                'demographic_question': 0,
                'test_completed': False,
                'updated_at': self._get_current_time()
            }

            if not keep_results:
                update_data['depression_score'] = -1
                update_data['anxiety_score'] = -1

            self.client.table('users').update(update_data).eq('id', user_id).execute()

            logger.info(f"Test progress for user {user_id} reset in Supabase")
            return True

        except Exception as e:
            logger.error(f"Error resetting test progress in Supabase: {e}")
            return False

    async def save_consent(self, user_id):
        """Save user's consent for data processing"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'consent_given': True,
                'current_phase': 'demographic',
                'updated_at': self._get_current_time()
            }).eq('id', user_id).execute()

            logger.info(f"Consent saved for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving consent in Supabase: {e}")
            return False

    async def get_consent_status(self, user_id):
        """Check if user has given consent"""
        if not self.client:
            return False

        try:
            result = self.client.table('users').select('consent_given').eq('id', user_id).execute()

            if result.data:
                return result.data[0]['consent_given'] == True
            return False

        except Exception as e:
            logger.error(f"Error getting consent status from Supabase: {e}")
            return False

    async def get_all_users(self):
        """Get all user IDs from Supabase"""
        if not self.client:
            return []

        try:
            result = self.client.table('users').select('id').execute()
            return [row['id'] for row in result.data]

        except Exception as e:
            logger.error(f"Error getting users from Supabase: {e}")
            return []

    async def mark_test_completed(self, user_id):
        """Mark test as completed"""
        if not self.client:
            return False

        try:
            self.client.table('users').update({
                'test_completed': True,
                'completed_at': self._get_current_time(),
                'updated_at': self._get_current_time()
            }).eq('id', user_id).execute()

            logger.info(f"Test marked as completed for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error marking test as completed in Supabase: {e}")
            return False

    # === Admin Panel Methods ===

    async def get_users_paginated(self, page=1, limit=25, status=None, search=None):
        """Get paginated list of users for admin panel"""
        if not self.client:
            return {'users': [], 'total': 0, 'page': page}

        try:
            query = self.client.table('users').select('*', count='exact')

            # Apply filters
            if status == 'completed':
                query = query.eq('test_completed', True)
            elif status == 'in_progress':
                query = query.eq('test_completed', False).neq('current_phase', 'consent')
            elif status == 'dropped':
                query = query.eq('test_completed', False).eq('consent_given', False)

            if search:
                query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,username.ilike.%{search}%")

            # Pagination
            offset = (page - 1) * limit
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)

            result = query.execute()

            return {
                'users': result.data,
                'total': result.count if result.count else len(result.data),
                'page': page
            }

        except Exception as e:
            logger.error(f"Error getting paginated users from Supabase: {e}")
            return {'users': [], 'total': 0, 'page': page}

    async def get_user_by_id(self, user_id):
        """Get full user details by ID"""
        if not self.client:
            return None

        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting user by ID from Supabase: {e}")
            return None

    async def get_dashboard_stats(self):
        """Get dashboard statistics"""
        if not self.client:
            return {}

        try:
            # Total users
            total_result = self.client.table('users').select('id', count='exact').execute()
            total_users = total_result.count or 0

            # Completed users
            completed_result = self.client.table('users').select('id', count='exact').eq('test_completed', True).execute()
            completed_users = completed_result.count or 0

            # Average scores for completed users
            scores_result = self.client.table('users').select(
                'depression_score, anxiety_score'
            ).eq('test_completed', True).execute()

            avg_depression = 0
            avg_anxiety = 0
            if scores_result.data:
                dep_scores = [r['depression_score'] for r in scores_result.data if r['depression_score'] >= 0]
                anx_scores = [r['anxiety_score'] for r in scores_result.data if r['anxiety_score'] >= 0]
                avg_depression = sum(dep_scores) / len(dep_scores) if dep_scores else 0
                avg_anxiety = sum(anx_scores) / len(anx_scores) if anx_scores else 0

            return {
                'total_users': total_users,
                'completed_users': completed_users,
                'completion_rate': (completed_users / total_users * 100) if total_users > 0 else 0,
                'avg_depression_score': round(avg_depression, 1),
                'avg_anxiety_score': round(avg_anxiety, 1)
            }

        except Exception as e:
            logger.error(f"Error getting dashboard stats from Supabase: {e}")
            return {}

    async def get_funnel_data(self):
        """Get funnel analytics data"""
        if not self.client:
            return []

        try:
            # Get counts for each phase
            total_result = self.client.table('users').select('id', count='exact').execute()
            consent_result = self.client.table('users').select('id', count='exact').eq('consent_given', True).execute()
            demographic_done = self.client.table('users').select('id', count='exact').neq('current_phase', 'consent').neq('current_phase', 'demographic').execute()
            completed_result = self.client.table('users').select('id', count='exact').eq('test_completed', True).execute()

            total = total_result.count or 0
            consented = consent_result.count or 0
            started_test = demographic_done.count or 0
            completed = completed_result.count or 0

            return [
                {'stage': 'Начали', 'count': total, 'percentage': 100},
                {'stage': 'Дали согласие', 'count': consented, 'percentage': round(consented / total * 100) if total > 0 else 0},
                {'stage': 'Прошли демографию', 'count': started_test, 'percentage': round(started_test / total * 100) if total > 0 else 0},
                {'stage': 'Завершили тест', 'count': completed, 'percentage': round(completed / total * 100) if total > 0 else 0}
            ]

        except Exception as e:
            logger.error(f"Error getting funnel data from Supabase: {e}")
            return []

    async def get_demographics_stats(self):
        """Get demographics breakdown"""
        if not self.client:
            return {}

        try:
            result = self.client.table('users').select('gender, age_group, location').eq('test_completed', True).execute()

            gender_counts = {}
            age_counts = {}
            location_counts = {}

            for row in result.data:
                # Gender
                g = row.get('gender')
                if g:
                    gender_counts[g] = gender_counts.get(g, 0) + 1

                # Age
                a = row.get('age_group')
                if a:
                    age_counts[a] = age_counts.get(a, 0) + 1

                # Location
                l = row.get('location')
                if l:
                    location_counts[l] = location_counts.get(l, 0) + 1

            return {
                'gender': gender_counts,
                'age': age_counts,
                'location': location_counts
            }

        except Exception as e:
            logger.error(f"Error getting demographics stats from Supabase: {e}")
            return {}

    async def get_score_distribution(self):
        """Get score distribution for charts"""
        if not self.client:
            return {}

        try:
            result = self.client.table('users').select(
                'depression_score, anxiety_score'
            ).eq('test_completed', True).execute()

            depression_dist = {}
            anxiety_dist = {}

            for row in result.data:
                # Depression score buckets
                d = row.get('depression_score', -1)
                if d >= 0:
                    bucket = self._get_score_bucket(d, 'depression')
                    depression_dist[bucket] = depression_dist.get(bucket, 0) + 1

                # Anxiety score buckets
                a = row.get('anxiety_score', -1)
                if a >= 0:
                    bucket = self._get_score_bucket(a, 'anxiety')
                    anxiety_dist[bucket] = anxiety_dist.get(bucket, 0) + 1

            return {
                'depression': depression_dist,
                'anxiety': anxiety_dist
            }

        except Exception as e:
            logger.error(f"Error getting score distribution from Supabase: {e}")
            return {}

    def _get_score_bucket(self, score, test_type):
        """Get score severity bucket"""
        if test_type == 'depression':
            if score <= 7:
                return 'Норма (0-7)'
            elif score <= 10:
                return 'Субклинический (8-10)'
            else:
                return 'Клинический (11+)'
        else:  # anxiety
            if score <= 9:
                return 'Норма (0-9)'
            elif score <= 18:
                return 'Умеренный (10-18)'
            elif score <= 29:
                return 'Средний (19-29)'
            else:
                return 'Высокий (30+)'

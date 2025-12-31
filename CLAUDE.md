# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram mental health assessment bot (nodepressionbot) that administers combined HADS depression and BAI anxiety screening tests in Russian, stores results in SQLite + Google Sheets, and provides promotional recommendations for META CLINIC.

## Running the Bot

```bash
pip install -r requirements.txt
python main.py
```

## Environment Variables

Required in `.env`:
- `TOKEN` - Telegram bot token
- `ADMIN` - Telegram user ID for admin commands (`/news` broadcast)

Optional (for admin panel with Supabase):
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `ADMIN_PASSWORD` - Password for admin panel (default: admin123)
- `JWT_SECRET` - Secret key for JWT tokens
- `API_PORT` - Port for admin panel API (default: 8000)
- `OPENAI_API_KEY` - Imported but currently unused in code

## Architecture

```
main.py (entry point)
  ├── Bot & Dispatcher (aiogram)
  ├── Services Layer
  │   ├── SheetsService - Google Sheets integration
  │   ├── SQLiteService - Local database operations
  │   ├── StartService - Test orchestration & recommendations
  │   └── NewsService - Broadcasting messages
  └── TelegramRouter (handlers.py) - Command & message handling
```

### Core Components

- **handlers.py** - Routes `/start` (demographic → mixed test) and `/news` (admin broadcast), handles button responses with gender-aware Russian text formatting
- **services/start.py** - Orchestrates test with 14 randomized questions (7 depression + 7 anxiety), generates recommendations based on score thresholds
- **db.py** - SQLite abstraction for `users` table tracking phases, progress, and scores
- **google_sheets.py** - User registry sheet + per-user message history sheets (credentials: `nodepressionbot-59c72a15d0fd.json`)

### Data Flow

1. `/start` → reset progress, save user to SQLite + Sheets
2. Demographic phase (3 questions: gender, age, location)
3. Mixed test (14 shuffled questions from depression + anxiety)
4. Each answer → score calculated, saved to both stores
5. Completion → generate recommendation, reset progress

### Gender-Specific Text Formatting

Russian grammar requires verb conjugation by gender. Uses `{{gender_suffix}}` markers in `config.py`:
- `стал{{gender_suffix}}` → "стал" (male) / "стала" (female)
- Applied via `format_gender_specific_text()` to depression test questions/options

## Database Schema

**SQLite (`nodepressionbot.db`) - users table:**
- `id` (TEXT PK), `first_name`, `last_name`, `username`, `url`
- `gender`, `age_group`, `location` - Demographics
- `current_phase` - 'demographic' or 'mixed_test'
- `demographic_question` (0-2), `current_question` (1-indexed)
- `question_order_json` - JSON array of shuffled question refs
- `depression_score`, `anxiety_score` - Running totals (-1 = not started, 0+ = in progress)

**Google Sheets:**
- Main sheet: User registry with hyperlinks to per-user history sheets
- Per-user sheets: Timestamp, From (user/bot), Message, Score

## Key Implementation Details

### Test Progression State Machine

**Demographic Phase** (`current_phase='demographic'`):
- `demographic_question` tracks progress: 0=gender, 1=age, 2=location
- Gender captured first for subsequent text formatting

**Mixed Test Phase** (`current_phase='mixed_test'`):
- `question_order_json`: shuffled array of `{"test_type": "depression"|"anxiety", "question_idx": 0-6}`
- `current_question` is 1-indexed position in array
- Scores accumulated separately, initialized to 0 when test starts

### Score Thresholds (services/start.py:103-122)

**Depression** (max 21):
- 8-10: subclinical
- >10: clinical

**Anxiety** (max 21):
- 10-18: moderate
- 19-29: medium
- ≥30: high

### Admin Features

`/news <message>` - Broadcasts to all users in Google Sheets (requires `ADMIN` env var match)

## Testing

```bash
python main.py                                    # Run bot
sqlite3 nodepressionbot.db "SELECT * FROM users;" # Check DB state
```

## Common Tasks

**Adding Questions**: Update `config.py` arrays (`DEPRESSION_QUESTIONS`, `OPTIONS`, `SCORES`) - count is dynamic

**Changing Recommendations**: Edit `StartService.get_combined_recommendation()` in `services/start.py`

**Modifying Demographics**: Update `DEMOGRAPHIC_QUESTIONS/OPTIONS` in `config.py`, adjust `TelegramRouter.process_demographic_response()` if order changes

## Known Issues

1. **Service Account Key**: `nodepressionbot-59c72a15d0fd.json` committed to repo
2. **No Error Recovery**: If Sheets API fails mid-test, progress may be inconsistent

---

## Admin Panel (Optional)

### Setup

1. Create Supabase project at supabase.com
2. Run SQL schema from `scripts/migrate_sqlite_to_supabase.py` header
3. Add to `.env`:
   ```
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_KEY=xxx
   ADMIN_PASSWORD=your-secure-password
   JWT_SECRET=your-jwt-secret
   ```
4. Migrate existing data: `python scripts/migrate_sqlite_to_supabase.py --events`
5. Build frontend: `cd frontend && npm install && npm run build`

### Architecture

```
main.py
  ├── Telegram Bot (aiogram)
  └── FastAPI Server (port 8000)
      ├── /api/auth/* - Authentication
      ├── /api/dashboard/* - Dashboard metrics
      ├── /api/users/* - User management
      └── /api/analytics/* - Analytics data
```

### Components

- **api/** - FastAPI backend with JWT auth
- **services/supabase_service.py** - Supabase database operations
- **services/analytics.py** - Event tracking service
- **frontend/** - React + Tailwind admin panel

### API Endpoints

**Auth**: POST `/api/auth/login`, GET `/api/auth/me`
**Dashboard**: GET `/api/dashboard/summary`, `/trends`, `/recent`
**Users**: GET `/api/users/`, `/api/users/{id}`, `/api/users/{id}/events`, `/api/users/export`
**Analytics**: GET `/api/analytics/funnel`, `/question-dropoff`, `/scores`, `/demographics`

### Event Tracking

Analytics events are tracked automatically:
- `session_start` - User sends /start
- `phase_complete` - User completes consent/demographic/test phase
- `question_answered` - User answers a question
- `test_completed` - User completes full test

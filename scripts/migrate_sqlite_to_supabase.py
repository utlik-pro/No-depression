#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to Supabase

Usage:
    python scripts/migrate_sqlite_to_supabase.py

Before running:
1. Create Supabase project at supabase.com
2. Run the SQL schema in Supabase SQL Editor (see below)
3. Set SUPABASE_URL and SUPABASE_KEY in .env

SQL Schema to run in Supabase:

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    url TEXT,
    gender TEXT,
    age_group TEXT,
    location TEXT,
    current_question INTEGER DEFAULT 0,
    question_order_json TEXT,
    depression_score INTEGER DEFAULT -1,
    anxiety_score INTEGER DEFAULT -1,
    demographic_question INTEGER DEFAULT 0,
    current_phase TEXT DEFAULT 'consent',
    consent_given BOOLEAN DEFAULT FALSE,
    test_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    phase TEXT,
    question_index INTEGER,
    question_type TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_user ON analytics_events(user_id);
CREATE INDEX idx_events_type ON analytics_events(event_type);
CREATE INDEX idx_events_created ON analytics_events(created_at);

CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Configuration
SQLITE_DB_PATH = "nodepressionbot.db"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def migrate_users():
    """Migrate users from SQLite to Supabase"""

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    # Connect to SQLite
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Error: SQLite database not found: {SQLITE_DB_PATH}")
        return False

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Connect to Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get all users from SQLite
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    print(f"Found {len(users)} users to migrate")

    success_count = 0
    error_count = 0

    for user in users:
        user_dict = dict(user)

        # Convert SQLite data types to Supabase compatible
        supabase_user = {
            'id': user_dict.get('id'),
            'first_name': user_dict.get('first_name'),
            'last_name': user_dict.get('last_name'),
            'username': user_dict.get('username'),
            'url': user_dict.get('url'),
            'gender': user_dict.get('gender'),
            'age_group': user_dict.get('age_group'),
            'location': user_dict.get('location'),
            'current_question': user_dict.get('current_question', 0),
            'question_order_json': user_dict.get('question_order_json'),
            'depression_score': user_dict.get('depression_score', -1),
            'anxiety_score': user_dict.get('anxiety_score', -1),
            'demographic_question': user_dict.get('demographic_question', 0),
            'current_phase': user_dict.get('current_phase', 'consent'),
            'consent_given': bool(user_dict.get('consent_given', 0)),
            'test_completed': user_dict.get('depression_score', -1) >= 0 and user_dict.get('anxiety_score', -1) >= 0,
        }

        # Convert timestamps
        if user_dict.get('created_at'):
            try:
                dt = datetime.strptime(user_dict['created_at'], '%Y-%m-%d %H:%M:%S')
                supabase_user['created_at'] = dt.isoformat()
            except:
                supabase_user['created_at'] = datetime.now().isoformat()

        if user_dict.get('updated_at'):
            try:
                dt = datetime.strptime(user_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
                supabase_user['updated_at'] = dt.isoformat()
            except:
                supabase_user['updated_at'] = datetime.now().isoformat()

        # Set completed_at if test was completed
        if supabase_user['test_completed']:
            supabase_user['completed_at'] = supabase_user.get('updated_at')

        try:
            # Check if user exists
            result = supabase.table('users').select('id').eq('id', supabase_user['id']).execute()

            if result.data:
                # Update existing user
                supabase.table('users').update(supabase_user).eq('id', supabase_user['id']).execute()
                print(f"  Updated user: {supabase_user['id']}")
            else:
                # Insert new user
                supabase.table('users').insert(supabase_user).execute()
                print(f"  Inserted user: {supabase_user['id']}")

            success_count += 1

        except Exception as e:
            print(f"  Error migrating user {supabase_user['id']}: {e}")
            error_count += 1

    conn.close()

    print(f"\nMigration complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")

    return error_count == 0


def generate_synthetic_events():
    """
    Generate synthetic analytics events based on current user state
    This helps populate the analytics_events table for existing users
    """

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get all users
    result = supabase.table('users').select('*').execute()
    users = result.data

    print(f"Generating synthetic events for {len(users)} users")

    for user in users:
        user_id = user['id']
        created_at = user.get('created_at') or datetime.now().isoformat()

        events_to_insert = []

        # Session start event
        events_to_insert.append({
            'user_id': user_id,
            'event_type': 'session_start',
            'phase': 'consent',
            'created_at': created_at
        })

        # If consent was given
        if user.get('consent_given'):
            events_to_insert.append({
                'user_id': user_id,
                'event_type': 'phase_complete',
                'phase': 'consent',
                'metadata': '{"consented": true}',
                'created_at': created_at
            })

        # If demographic phase was completed (has gender, age, location)
        if user.get('gender') and user.get('age_group') and user.get('location'):
            events_to_insert.append({
                'user_id': user_id,
                'event_type': 'phase_complete',
                'phase': 'demographic',
                'created_at': created_at
            })

        # If test was completed
        if user.get('test_completed'):
            events_to_insert.append({
                'user_id': user_id,
                'event_type': 'test_completed',
                'phase': 'mixed_test',
                'metadata': f'{{"depression_score": {user.get("depression_score", 0)}, "anxiety_score": {user.get("anxiety_score", 0)}}}',
                'created_at': user.get('completed_at') or user.get('updated_at') or created_at
            })

        # Insert events
        try:
            for event in events_to_insert:
                supabase.table('analytics_events').insert(event).execute()
            print(f"  Created {len(events_to_insert)} events for user {user_id}")
        except Exception as e:
            print(f"  Error creating events for user {user_id}: {e}")

    print("Synthetic events generation complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate data from SQLite to Supabase')
    parser.add_argument('--events', action='store_true', help='Generate synthetic analytics events')
    args = parser.parse_args()

    print("=" * 50)
    print("SQLite to Supabase Migration")
    print("=" * 50)

    if migrate_users():
        print("\nUser migration successful!")

        if args.events:
            print("\n" + "=" * 50)
            print("Generating Synthetic Events")
            print("=" * 50)
            generate_synthetic_events()
    else:
        print("\nMigration failed!")
        sys.exit(1)

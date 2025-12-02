#!/usr/bin/env python3
"""Quick test script to verify analytics database schema and data"""

import sqlite3
import json

# Connect to database
conn = sqlite3.connect('analytics.db')
cursor = conn.cursor()

# Check schema
print("=" * 60)
print("DATABASE SCHEMA")
print("=" * 60)
cursor.execute('PRAGMA table_info(events)')
for row in cursor.fetchall():
    print(f"  {row[1]:20} {row[2]:10} {'NOT NULL' if row[3] else 'NULL'}")

# Check last 3 events
print("\n" + "=" * 60)
print("LAST 3 EVENTS")
print("=" * 60)
cursor.execute('SELECT id, user_id, session_id, event_type, event_data, created_at FROM events ORDER BY id DESC LIMIT 3')
for row in cursor.fetchall():
    event_id, user_id, session_id, event_type, event_data, created_at = row
    print(f"\nEvent ID: {event_id}")
    print(f"  User ID: {user_id}")
    print(f"  Session: {session_id}")
    print(f"  Type: {event_type}")
    print(f"  Created: {created_at}")
    if event_data:
        try:
            data = json.loads(event_data)
            print(f"  Data: {json.dumps(data, indent=4)}")
        except:
            print(f"  Data: {event_data}")

# Count events by type
print("\n" + "=" * 60)
print("EVENT COUNTS BY TYPE")
print("=" * 60)
cursor.execute('SELECT event_type, COUNT(*) FROM events GROUP BY event_type')
for row in cursor.fetchall():
    print(f"  {row[0]:20} {row[1]:5} events")

# Total count
cursor.execute('SELECT COUNT(*) FROM events')
total = cursor.fetchone()[0]
print(f"\n  TOTAL: {total} events")

conn.close()

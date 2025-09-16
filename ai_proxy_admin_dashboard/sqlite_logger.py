import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = 'masking_logs.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS masking_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            masked_type TEXT NOT NULL,
            masked_value TEXT NOT NULL,
            count INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def log_masking_event(masked_type: str, masked_value: str, count: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO masking_events (timestamp, masked_type, masked_value, count)
        VALUES (?, ?, ?, ?)
    ''', (datetime.utcnow().isoformat(), masked_type, masked_value, count))
    conn.commit()
    conn.close()

def get_logs(masked_type: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if masked_type:
        c.execute('''SELECT timestamp, masked_type, masked_value, count FROM masking_events WHERE masked_type = ? ORDER BY timestamp DESC''', (masked_type,))
    else:
        c.execute('''SELECT timestamp, masked_type, masked_value, count FROM masking_events ORDER BY timestamp DESC''')
    rows = c.fetchall()
    conn.close()
    return [
        {
            'timestamp': row[0],
            'masked_type': row[1],
            'masked_value': row[2],
            'count': row[3]
        } for row in rows
    ]

def get_masked_types() -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT DISTINCT masked_type FROM masking_events''')
    types = [row[0] for row in c.fetchall()]
    conn.close()
    return types 
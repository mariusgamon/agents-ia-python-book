# watch_monitor.py — production monitoring for the tech-watch agent
# Tracks daily stats, detects silent failures, generates weekly reports

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

DB_PATH = Path("data/watch_stats.db")

@dataclass
class DailyStats:
    date: str
    sources_checked: int
    articles_scanned: int
    articles_retained: int
    alerts_sent: int
    false_positives: int
    tokens_used: int
    cost_usd: float
    errors: list[str]
    duration_seconds: float

def init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            sources_checked INTEGER,
            articles_scanned INTEGER,
            articles_retained INTEGER,
            alerts_sent INTEGER,
            false_positives INTEGER,
            tokens_used INTEGER,
            cost_usd REAL,
            errors TEXT,
            duration_seconds REAL
        )
    """)
    conn.commit()
    return conn

def record_run(stats: DailyStats):
    """Call at the end of each watch run to persist metrics."""
    conn = init_db()
    conn.execute(
        "INSERT OR REPLACE INTO daily_stats VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            stats.date, stats.sources_checked, stats.articles_scanned,
            stats.articles_retained, stats.alerts_sent, stats.false_positives,
            stats.tokens_used, stats.cost_usd, json.dumps(stats.errors),
            stats.duration_seconds,
        ),
    )
    conn.commit()
    conn.close()

def detect_anomalies(lookback_days: int = 7) -> list[str]:
    """Compare today against rolling average.
    Catches two failure modes:
    - article count drop >50%  -> a source died silently
    - cost spike >3x           -> prompt loop or model regression"""
    conn = init_db()
    rows = conn.execute(
        "SELECT articles_scanned, cost_usd FROM daily_stats "
        "ORDER BY date DESC LIMIT ?",
        (lookback_days,),
    ).fetchall()
    conn.close()

    if len(rows) < 3:
        return []

    today_articles, today_cost = rows[0]
    past = rows[1:]
    avg_articles = sum(r[0] for r in past) / len(past)
    avg_cost = sum(r[1] for r in past) / len(past)

    alerts = []
    if avg_articles > 0 and today_articles < avg_articles * 0.5:
        alerts.append(
            f"Volume drop: {today_articles} vs avg {avg_articles:.0f}. "
            f"A source may be down — check per-source counts."
        )
    if avg_cost > 0 and today_cost > avg_cost * 3:
        alerts.append(
            f"Cost spike: ${today_cost:.2f} vs avg ${avg_cost:.2f}. "
            f"Possible prompt loop — check agent trace."
        )
    return alerts

def weekly_report() -> str:
    """7-day summary. Paste into Slack or email as-is."""
    conn = init_db()
    rows = conn.execute(
        "SELECT * FROM daily_stats ORDER BY date DESC LIMIT 7"
    ).fetchall()
    conn.close()

    if not rows:
        return "No data yet."

    total_scanned = sum(r[2] for r in rows)
    total_retained = sum(r[3] for r in rows)
    total_cost = sum(r[7] for r in rows)
    total_errors = sum(len(json.loads(r[8])) for r in rows)
    signal = (total_retained / total_scanned * 100) if total_scanned else 0

    return (
        f"*Watch Agent — Weekly Report*\n"
        f"- Articles: {total_scanned} scanned -> {total_retained} retained "
        f"({signal:.1f}% signal)\n"
        f"- Cost: ${total_cost:.2f} (${total_cost / 7:.2f}/day)\n"
        f"- Errors: {total_errors}\n"
        f"- Signal quality: "
        + ("Good — filters hold" if signal < 5 else "Review filters — too much noise")
    )

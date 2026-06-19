"""
Temporal analytics: vault activity trends and importance-weighted staleness.

Offline module — queries existing SQLite columns only:
  notes.created_at, notes.modified_at, graph_metrics.pagerank

No new deps, no schema migration required.
"""

import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).parent.parent))

if TYPE_CHECKING:
    from db_manager import DatabaseManager


def _parse_dt(value) -> datetime:
    """Parse a SQLite timestamp string or datetime into an aware UTC datetime."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # Strip fractional seconds and timezone suffix before matching formats
    s = str(value).split('.')[0].rstrip('Z').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {value!r}")


def compute_trends(vault_id: str, db, lookback_days: int = 90):
    """Return a TrendReport with weekly activity buckets.

    Buckets are built from notes.created_at and notes.modified_at.
    Sets insufficient_data=True when fewer than 2 weeks of data exist.
    """
    from ai.models import TrendBucket, TrendReport

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)
    cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

    total_notes = 0
    created_by_week: dict = defaultdict(int)
    modified_by_week: dict = defaultdict(int)

    try:
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM notes WHERE vault_id = ?", (vault_id,)
            ).fetchone()
            total_notes = row[0] if row else 0

            for (ts,) in conn.execute(
                "SELECT created_at FROM notes WHERE vault_id = ? AND created_at >= ?",
                (vault_id, cutoff_str),
            ).fetchall():
                if ts:
                    try:
                        week = _parse_dt(ts).strftime("%Y-W%V")
                        created_by_week[week] += 1
                    except ValueError:
                        pass

            for (ts,) in conn.execute(
                "SELECT modified_at FROM notes WHERE vault_id = ? AND modified_at >= ?",
                (vault_id, cutoff_str),
            ).fetchall():
                if ts:
                    try:
                        week = _parse_dt(ts).strftime("%Y-W%V")
                        modified_by_week[week] += 1
                    except ValueError:
                        pass
    except Exception:
        pass

    all_weeks = sorted(set(list(created_by_week) + list(modified_by_week)))
    buckets = [
        TrendBucket(
            week=w,
            notes_created=created_by_week[w],
            notes_modified=modified_by_week[w],
        )
        for w in all_weeks
    ]

    total_created = sum(b.notes_created for b in buckets)
    velocity = round(total_created / max(len(buckets), 1), 2)

    return TrendReport(
        vault_id=vault_id,
        total_notes=total_notes,
        lookback_days=lookback_days,
        buckets=buckets,
        velocity_notes_per_week=velocity,
        insufficient_data=len(all_weeks) < 2,
    )


def compute_stale(vault_id: str, db, limit: int = 50):
    """Return a StaleReport of notes ranked by importance-weighted age.

    staleness_score = pagerank × (days_since_modified / 365).
    Falls back to date-only sort when graph_metrics has no PageRank data.
    """
    from ai.models import StaleNote, StaleReport

    now = datetime.now(timezone.utc)
    notes = []
    has_graph_metrics = False

    try:
        with db.get_connection() as conn:
            rows = conn.execute("""
                SELECT n.id, n.title, n.path, n.modified_at,
                       COALESCE(gm.pagerank, 0.0) AS pagerank
                FROM notes n
                LEFT JOIN graph_metrics gm ON n.id = gm.note_id
                WHERE n.vault_id = ?
                  AND n.modified_at IS NOT NULL
                ORDER BY n.modified_at ASC
                LIMIT ?
            """, (vault_id, limit * 3)).fetchall()

        has_graph_metrics = any(r[4] > 0.0 for r in rows)

        for note_id, title, path, modified_at_str, pagerank in rows:
            try:
                modified_at = _parse_dt(modified_at_str)
                days_old = (now - modified_at).days
                if has_graph_metrics:
                    score = pagerank * (days_old / 365.0)
                else:
                    score = days_old / 365.0
                notes.append(StaleNote(
                    note_id=str(note_id),
                    title=title or "",
                    path=path or "",
                    days_since_modified=days_old,
                    pagerank=round(pagerank, 6),
                    staleness_score=round(score, 4),
                ))
            except Exception:
                pass
    except Exception:
        pass

    notes.sort(key=lambda n: n.staleness_score, reverse=True)

    return StaleReport(
        vault_id=vault_id,
        notes=notes[:limit],
        has_graph_metrics=has_graph_metrics,
    )

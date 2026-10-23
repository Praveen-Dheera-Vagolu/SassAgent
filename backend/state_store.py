from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional
from backend.models import AgentState, AuditLog, ReductionProposal

DB_PATH = Path(__file__).resolve().parent / "saas_optimizer.db"


class StateStore:
    """
    SQLite-backed thread-safe checkpoint store with interrupt/resume semantics.
    Enables audit-grade state tracking and durable human-in-the-loop gates.
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    run_id TEXT PRIMARY KEY,
                    step_name TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    is_paused INTEGER NOT NULL,
                    is_completed INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    subscription_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    proposal_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def save_checkpoint(self, state: AgentState) -> None:
        state_json = state.model_dump_json()
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (run_id, step_name, subscription_id, is_paused, is_completed, state_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(run_id) DO UPDATE SET
                    step_name=excluded.step_name,
                    subscription_id=excluded.subscription_id,
                    is_paused=excluded.is_paused,
                    is_completed=excluded.is_completed,
                    state_json=excluded.state_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    state.run_id,
                    state.step_name,
                    state.subscription_id,
                    1 if state.is_paused else 0,
                    1 if state.is_completed else 0,
                    state_json,
                ),
            )
            conn.commit()

    def get_checkpoint(self, run_id: str) -> Optional[AgentState]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT state_json FROM checkpoints WHERE run_id = ?", (run_id,)
            ).fetchone()
            if row:
                return AgentState.model_validate_json(row["state_json"])
            return None

    def get_checkpoint_by_proposal(self, proposal_id: str) -> Optional[AgentState]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT state_json FROM checkpoints ORDER BY updated_at DESC").fetchall()
            for row in rows:
                state = AgentState.model_validate_json(row["state_json"])
                if state.proposal and state.proposal.proposal_id == proposal_id:
                    return state
        return None

    def save_proposal(self, proposal: ReductionProposal) -> None:
        proposal_json = proposal.model_dump_json()
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO proposals (proposal_id, subscription_id, status, proposal_json, resolved_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(proposal_id) DO UPDATE SET
                    status=excluded.status,
                    proposal_json=excluded.proposal_json,
                    resolved_at=excluded.resolved_at
                """,
                (
                    proposal.proposal_id,
                    proposal.subscription_id,
                    proposal.status.value,
                    proposal_json,
                    proposal.resolved_at,
                ),
            )
            conn.commit()

    def get_proposal(self, proposal_id: str) -> Optional[ReductionProposal]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT proposal_json FROM proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if row:
                return ReductionProposal.model_validate_json(row["proposal_json"])
            return None

    def list_proposals(self) -> List[ReductionProposal]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT proposal_json FROM proposals ORDER BY created_at DESC").fetchall()
            return [ReductionProposal.model_validate_json(r["proposal_json"]) for r in rows]

    def add_audit_log(self, log: AuditLog) -> None:
        details_json = json.dumps(log.details)
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_logs (id, timestamp, subscription_id, event_type, title, message, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.timestamp,
                    log.subscription_id,
                    log.event_type.value,
                    log.title,
                    log.message,
                    details_json,
                ),
            )
            conn.commit()

    def list_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, timestamp, subscription_id, event_type, title, message, details_json FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            logs = []
            for r in rows:
                logs.append(
                    AuditLog(
                        id=r["id"],
                        timestamp=r["timestamp"],
                        subscription_id=r["subscription_id"],
                        event_type=r["event_type"],
                        title=r["title"],
                        message=r["message"],
                        details=json.loads(r["details_json"]),
                    )
                )
            return logs

    def clear_all(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute("DELETE FROM checkpoints")
            conn.execute("DELETE FROM proposals")
            conn.execute("DELETE FROM audit_logs")
            conn.commit()


state_store = StateStore()

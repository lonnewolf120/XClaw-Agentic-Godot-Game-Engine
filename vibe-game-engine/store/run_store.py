import sqlite3
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from contracts.run_state import RunState, RunStatus, OrchestrationNode
from contracts.base import StrictModel
from contracts.actions import ActionBatch

class AgentProposal(StrictModel):
    proposal_id: str
    workspace_path: str
    action_batch_json: str
    created_at: str
    status: str = "PENDING"

# Thin abstraction wrapper around SQLite to store our RunState

class RunStore:
    def __init__(self, db_path: str = "vibe_runs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT,
                    current_node TEXT,
                    prompt TEXT,
                    workspace_dir TEXT,
                    retry_count INTEGER,
                    state_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS run_messages (
                    id TEXT PRIMARY KEY,
                    run_id TEXT,
                    message_type TEXT,
                    payload_json TEXT,
                    created_at TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS run_artifacts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT,
                    artifact_type TEXT,
                    path TEXT,
                    metadata_json TEXT,
                    created_at TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    workspace_path TEXT,
                    action_batch_json TEXT,
                    status TEXT,
                    created_at TEXT
                )
            ''')
            conn.commit()
            
    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def create_run(self, prompt: str, workspace_dir: str) -> RunState:
        run_id = f"run_{uuid4().hex[:8]}"
        state = RunState(
            run_id=run_id,
            prompt=prompt,
            workspace_dir=workspace_dir,
            status=RunStatus.INTAKE,
            current_node=OrchestrationNode.INTAKE
        )
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO runs (run_id, status, current_node, prompt, workspace_dir, retry_count, state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                state.run_id, state.status.value, state.current_node.value, state.prompt,
                state.workspace_dir, state.retry_count, state.model_dump_json(), self._now(), self._now()
            ))
            conn.commit()
        return state

    def load_run(self, run_id: str) -> Optional[RunState]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT state_json FROM runs WHERE run_id = ?', (run_id,))
            row = c.fetchone()
            if row:
                return RunState.model_validate_json(row[0])
            return None

    def update_run(self, state: RunState):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE runs 
                SET status = ?, current_node = ?, retry_count = ?, state_json = ?, updated_at = ?
                WHERE run_id = ?
            ''', (
                state.status.value, state.current_node.value, state.retry_count,
                state.model_dump_json(), self._now(), state.run_id
            ))
            conn.commit()

    def append_message(self, run_id: str, message_type: str, payload: StrictModel):
        msg_id = f"msg_{uuid4().hex[:8]}"
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO run_messages (id, run_id, message_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                msg_id, run_id, message_type, payload.model_dump_json(), self._now()
            ))
            conn.commit()

    def append_artifact(self, run_id: str, artifact_type: str, path: str, metadata: dict):
        art_id = f"art_{uuid4().hex[:8]}"
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO run_artifacts (id, run_id, artifact_type, path, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                art_id, run_id, artifact_type, path, json.dumps(metadata), self._now()
            ))
            conn.commit()

    def store_proposal(self, workspace_path: str, action_batch: ActionBatch) -> str:
        proposal_id = f"prop_{uuid4().hex[:8]}"
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO proposals (proposal_id, workspace_path, action_batch_json, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                proposal_id, workspace_path, action_batch.model_dump_json(), "PENDING", self._now()
            ))
            conn.commit()
        return proposal_id

    def load_proposal(self, proposal_id: str) -> Optional[AgentProposal]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT proposal_id, workspace_path, action_batch_json, created_at, status FROM proposals WHERE proposal_id = ?', (proposal_id,))
            row = c.fetchone()
            if row:
                return AgentProposal(
                    proposal_id=row[0],
                    workspace_path=row[1],
                    action_batch_json=row[2],
                    created_at=row[3],
                    status=row[4]
                )
            return None
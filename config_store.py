"""Workspace config store.

For production, use Postgres/Supabase. For this repo, a JSON file store keeps
things simple and testable.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

from gtm_os.workspace import WorkspaceConfig


class JSONConfigStore:
    def __init__(self, path: str | None = None):
        default_path = os.getenv("WORKSPACE_CONFIG_PATH", "config/workspaces.json")
        self.path = Path(path or default_path)

    def load_all(self) -> Dict[str, WorkspaceConfig]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text())
        return {k: WorkspaceConfig.model_validate(v) for k, v in data.items()}

    def load(self, workspace_id: str) -> WorkspaceConfig:
        all_cfg = self.load_all()
        if workspace_id not in all_cfg:
            raise KeyError(f"Workspace '{workspace_id}' not found in {self.path}")
        return all_cfg[workspace_id]

    def save(self, cfg: WorkspaceConfig) -> None:
        all_cfg = self.load_all()
        all_cfg[cfg.workspace_id] = cfg
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serial = {k: v.model_dump() for k, v in all_cfg.items()}
        self.path.write_text(json.dumps(serial, indent=2))


__all__ = ["JSONConfigStore"]
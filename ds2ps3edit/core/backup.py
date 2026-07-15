"""Backup a save directory before mutating it."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

BACKUP_ROOT = Path(__file__).resolve().parents[2] / "saves"


def backup_save_dir(save_dir: Path) -> Path:
    """Copy the entire save directory into saves/live-backup-<timestamp>/.

    Returns the backup path. Never overwrites an existing backup.
    """
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_ROOT / f"live-backup-{stamp}"
    if dest.exists():
        raise FileExistsError(f"backup path already exists: {dest}")
    shutil.copytree(save_dir, dest)
    return dest

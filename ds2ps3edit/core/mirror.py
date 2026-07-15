"""Locate a DS2 PS3 save directory and identify the fresh character-slot mirror.

Every character slot on PS3 is stored as three mirror files with a rotating
copy-on-write scheme (see docs/SaveFormat.md). For slot 1:
    01USER.DAT   <- one mirror
    101USER.DAT  <- another mirror
    201USER.DAT  <- another mirror

On any given save state, 2 of the 3 exist on disk; the newest one contains
the current data ("fresh"), the other is the previous-save copy ("stale").
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_RPCS3_SAVE_DIR = Path(
    "~/Library/Application Support/rpcs3/dev_hdd0/home/00000001/savedata/NPUB31358-GAME_000"
).expanduser()

# Names of the three mirror files for slot 1. Extend when we support more slots.
SLOT1_MIRRORS = ("01USER.DAT", "101USER.DAT", "201USER.DAT")


@dataclass
class SlotMirror:
    """A character slot mirror file with liveness metadata."""

    path: Path
    is_fresh: bool  # True for the newest existing mirror

    @property
    def name(self) -> str:
        return self.path.name


def find_save_dir(explicit: Path | None = None) -> Path:
    """Return the save directory. Defaults to RPCS3's standard NPUB31358 path."""
    if explicit is not None:
        return explicit
    return DEFAULT_RPCS3_SAVE_DIR


def list_slot_mirrors(save_dir: Path) -> list[SlotMirror]:
    """Return the mirrors that currently exist for slot 1, freshest flagged.

    Fresh = newest mtime among the mirrors that exist. Ties broken by filename.
    Stale mirrors are listed for optional co-writing (see writer functions).
    """
    existing = [save_dir / n for n in SLOT1_MIRRORS if (save_dir / n).exists()]
    if not existing:
        raise FileNotFoundError(
            f"No slot-1 mirror files found in {save_dir}. "
            f"Expected one or more of {SLOT1_MIRRORS}."
        )
    fresh_path = max(existing, key=lambda p: p.stat().st_mtime)
    return [SlotMirror(path=p, is_fresh=(p == fresh_path)) for p in existing]


def fresh_slot_mirror(save_dir: Path) -> SlotMirror:
    """Return only the fresh mirror for slot 1."""
    for m in list_slot_mirrors(save_dir):
        if m.is_fresh:
            return m
    raise RuntimeError("no fresh mirror found (should be unreachable)")

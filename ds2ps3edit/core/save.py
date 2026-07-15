"""Top-level save handle: read once, edit in memory, commit atomically."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .backup import backup_save_dir
from .inventory import ItemRecord, scan_inventory, set_quantity
from .mirror import SlotMirror, find_save_dir, list_slot_mirrors
from .stats import Stats, read_character_name, read_stats, write_stats


@dataclass
class SaveHandle:
    """Holds the save-dir path and the in-memory bytes of every slot mirror.

    Read once at open. Mutations go through this object's helpers. Commit
    writes all mirrors back and takes a backup first.
    """

    save_dir: Path
    character_name: str
    stats: Stats
    inventory: list[ItemRecord]
    # Internal: mirror path -> bytearray currently in memory
    _mirror_buffers: dict[Path, bytearray] = field(default_factory=dict)
    _fresh_mirror: Path | None = None

    @classmethod
    def open(cls, save_dir: Path | None = None) -> "SaveHandle":
        save_dir = find_save_dir(save_dir)
        mirrors = list_slot_mirrors(save_dir)
        buffers: dict[Path, bytearray] = {m.path: bytearray(m.path.read_bytes()) for m in mirrors}
        fresh = next(m for m in mirrors if m.is_fresh)

        stats = read_stats(bytes(buffers[fresh.path]))
        inventory = list(scan_inventory(bytes(buffers[fresh.path])))
        name = read_character_name(save_dir)

        return cls(
            save_dir=save_dir,
            character_name=name,
            stats=stats,
            inventory=inventory,
            _mirror_buffers=buffers,
            _fresh_mirror=fresh.path,
        )

    @property
    def mirror_names(self) -> list[str]:
        return sorted(p.name for p in self._mirror_buffers)

    def apply_stats(self, new_stats: Stats) -> None:
        """Stage a stats-block update to every mirror."""
        for buf in self._mirror_buffers.values():
            write_stats(buf, new_stats)
        self.stats = new_stats

    def apply_item_qty(self, item_offset: int, new_qty: int) -> None:
        """Stage a quantity change for the item at `item_offset` to every mirror.

        Each mirror is updated independently — some may not contain the record
        at that offset (stale mirrors reflect an older world state); those are
        silently skipped, matching the game's own copy-on-write behavior.
        """
        for buf in self._mirror_buffers.values():
            try:
                set_quantity(buf, item_offset, new_qty)
            except ValueError:
                # Record not present in this mirror (stale) — skip.
                continue
        # Refresh in-memory inventory view from the fresh mirror.
        assert self._fresh_mirror is not None
        self.inventory = list(scan_inventory(bytes(self._mirror_buffers[self._fresh_mirror])))

    def commit(self) -> Path:
        """Backup, then write every dirty mirror to disk. Returns backup path."""
        backup_path = backup_save_dir(self.save_dir)
        for path, buf in self._mirror_buffers.items():
            path.write_bytes(bytes(buf))
        return backup_path

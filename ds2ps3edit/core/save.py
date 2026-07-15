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
        """Stage a stats-block update to every mirror.

        SoulsMemory is derived, not user-set. It represents total souls earned
        for the lifetime of the character and is monotonic in the game (spending
        souls does not decrease it). We enforce that here:
          - If the wallet increases, memory grows by the same delta (as if the
            player earned those souls organically).
          - If the wallet decreases or stays the same, memory is left alone
            (simulating a spend).
          - Any explicit user-supplied SoulsMemory value is discarded to keep
            the field internally consistent — the UI should not expose it.
        """
        adjusted = _reconcile_souls_memory(current=self.stats, requested=new_stats)
        for buf in self._mirror_buffers.values():
            write_stats(buf, adjusted)
        self.stats = adjusted

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


def _reconcile_souls_memory(current: Stats, requested: Stats) -> Stats:
    """Return `requested` with SoulsMemory derived from the wallet delta."""
    wallet_delta = requested.Souls - current.Souls
    new_memory = current.SoulsMemory + max(0, wallet_delta)
    # Never let memory drop below the current wallet (would be nonsensical).
    new_memory = max(new_memory, requested.Souls)
    return Stats(
        VGR=requested.VGR, END=requested.END, VIT=requested.VIT, ATN=requested.ATN,
        STR=requested.STR, DEX=requested.DEX, INT=requested.INT, FTH=requested.FTH,
        ADP=requested.ADP, Level=requested.Level,
        Souls=requested.Souls, SoulsMemory=new_memory,
    )

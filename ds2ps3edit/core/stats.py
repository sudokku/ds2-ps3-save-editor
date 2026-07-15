"""Read and write the character stats block.

Stats block base = file offset 0x20 in the character-slot file.
See docs/CharacterStats.md for full field list and confidence tags.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

STATS_BASE = 0x20

# (name, relative_offset, size_bytes)  — all big-endian, unsigned
STAT_FIELDS: list[tuple[str, int, int]] = [
    ("VGR", 0x00, 2),
    ("END", 0x02, 2),
    ("VIT", 0x04, 2),
    ("ATN", 0x06, 2),
    ("STR", 0x08, 2),
    ("DEX", 0x0A, 2),
    ("INT", 0x0C, 2),
    ("FTH", 0x0E, 2),
    ("ADP", 0x10, 2),
    ("Level", 0x18, 4),
    ("Souls", 0x1C, 4),         # wallet
    ("SoulsMemory", 0x20, 4),   # total earned lifetime
]


@dataclass
class Stats:
    VGR: int
    END: int
    VIT: int
    ATN: int
    STR: int
    DEX: int
    INT: int
    FTH: int
    ADP: int
    Level: int
    Souls: int
    SoulsMemory: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def read_stats(char_slot_bytes: bytes) -> Stats:
    values = {}
    for name, rel, size in STAT_FIELDS:
        raw = char_slot_bytes[STATS_BASE + rel : STATS_BASE + rel + size]
        values[name] = int.from_bytes(raw, "big")
    return Stats(**values)


def write_stats(char_slot_bytes: bytearray, stats: Stats) -> None:
    """In-place update the stats block. Caller is responsible for persisting bytes."""
    for name, rel, size in STAT_FIELDS:
        value = getattr(stats, name)
        max_val = (1 << (size * 8)) - 1
        if not (0 <= value <= max_val):
            raise ValueError(f"{name}={value} out of range for {size}-byte unsigned")
        char_slot_bytes[STATS_BASE + rel : STATS_BASE + rel + size] = value.to_bytes(size, "big")


def read_stats_from_file(path: Path) -> Stats:
    return read_stats(path.read_bytes())


# Character name lives in the root manifest, not the character-slot file.
NAME_LOC_USER_DAT = 0x1EE
NAME_LOC_16USER_DAT = 0x1BA
NAME_MAX_CHARS = 16  # DS2 name length limit


def read_character_name(save_dir: Path) -> str:
    """Read character name from USER.DAT (UTF-16BE, null-terminated)."""
    user_dat = save_dir / "USER.DAT"
    data = user_dat.read_bytes()
    raw = data[NAME_LOC_USER_DAT : NAME_LOC_USER_DAT + NAME_MAX_CHARS * 2]
    text = raw.decode("utf-16-be", errors="replace")
    return text.split("\x00", 1)[0]

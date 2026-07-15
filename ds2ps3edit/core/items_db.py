"""Item ID to display name lookup.

Starter catalog with the four items verified during reverse engineering.
Replace with a scraped community database (see HANDOFF.md next-steps) for
a functional MVP UI.

Item ID formula: save_u32 = GoodsParam_row * 10000.
"""
from __future__ import annotations

# Verified against Archives A..E with known in-game state.
_ITEMS: dict[int, str] = {
    50920000: "Soul of a Giant",
    60010000: "Lifegem",
    60510000: "Rubbish",
    60680000: "Large Soul of a Proud Knight",
}


def name_for(item_id: int) -> str:
    """Return the display name for an item id, or a placeholder if unknown."""
    return _ITEMS.get(item_id, f"Unknown 0x{item_id:08X}")


def is_known(item_id: int) -> bool:
    return item_id in _ITEMS


def item_type_from_id(item_id: int) -> str:
    """Coarse type classification based on Jappi88's range table.

    Only the last 4 decimal digits of the id are the range key.
    Note: Soul-type items (row 5xxx) are outside Jappi88's documented ranges.
    """
    row = item_id // 10000
    if 10 <= row <= 129: return "weapon"
    if 130 <= row <= 139: return "bow"
    if 140 <= row <= 149: return "staff"
    if 150 <= row <= 159: return "shield"
    if 400 <= row <= 499: return "armor"
    if 500 <= row <= 599: return "ring"
    if 600 <= row <= 699: return "arrow"
    if 700 <= row <= 709: return "consumable"
    if 710 <= row <= 719: return "key_item"
    if 720 <= row <= 799: return "material"
    if 800 <= row <= 999: return "spell"
    if 1000 <= row <= 1009: return "gesture"
    if 5000 <= row <= 5999: return "boss_soul"  # empirical (Soul of a Giant = 5092)
    return "unknown"


def is_editable_type(item_id: int) -> bool:
    """MVP: only allow qty edits for stackable/consumable-like items.

    Weapons/armor use bytes 8..15 for durability + upgrade + infusion,
    not quantity, so we keep those read-only until decoded on PS3.
    """
    t = item_type_from_id(item_id)
    return t in {"consumable", "key_item", "material", "arrow", "boss_soul", "unknown"}

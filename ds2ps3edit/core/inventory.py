"""Read and modify inventory item records in a character-slot file.

Every item record is 16 bytes:
    0..3   u32 BE  item id
    4      u8      always 0x00
    5      u8      location: 0x00 = inventory, 0x80 = item box
    6..7   u16     always 0x0000
    8..9   u16 BE  quantity  (weapons store durability/upgrade differently)
    10..15 zeros

See docs/Inventory.md for details and verified item IDs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

# Reference/recipe tables live below 0x1000; skip them when scanning inventory.
INVENTORY_SCAN_START = 0x1000
RECORD_SIZE = 16


@dataclass
class ItemRecord:
    """A single 16-byte inventory record, plus its file offset for writeback."""

    offset: int
    item_id: int
    location: int  # raw byte-5 flag: 0x00 or 0x80
    quantity: int
    raw: bytes

    @property
    def is_in_box(self) -> bool:
        return self.location == 0x80

    @property
    def location_label(self) -> str:
        if self.location == 0x00:
            return "inventory"
        if self.location == 0x80:
            return "item_box"
        return f"unknown(0x{self.location:02x})"


def _is_inventory_shape(rec: bytes) -> bool:
    """Filter: the confirmed 16-byte inventory record shape.

    Structural gate: rec[4]=0, rec[6..7]=00 00, rec[10..15]=00*6, rec[5] in {0x00,0x80}.
    Plus a value gate on the item id: all real DS2 item ids are
    (GoodsParam_row * 10000) + optional 3-digit upgrade/variant suffix, so id % 100 == 0
    and id is at least 100000 (row >= 10). This rules out neighboring tables that
    happen to have plausible byte shapes (float encodings, indices, etc.).
    """
    if (
        len(rec) != RECORD_SIZE
        or rec[4] != 0x00
        or rec[6:8] != b"\x00\x00"
        or rec[10:16] != b"\x00" * 6
        or rec[5] not in (0x00, 0x80)
    ):
        return False
    item_id = int.from_bytes(rec[0:4], "big")
    return 100_000 <= item_id <= 99_999_999 and item_id % 100 == 0


def scan_inventory(char_slot_bytes: bytes) -> Iterator[ItemRecord]:
    """Yield every inventory-shaped record with a non-zero item id and quantity."""
    off = INVENTORY_SCAN_START
    end = len(char_slot_bytes) - RECORD_SIZE
    while off <= end:
        rec = char_slot_bytes[off : off + RECORD_SIZE]
        if _is_inventory_shape(rec):
            item_id = int.from_bytes(rec[0:4], "big")
            quantity = int.from_bytes(rec[8:10], "big")
            if item_id != 0 and quantity != 0:
                yield ItemRecord(
                    offset=off,
                    item_id=item_id,
                    location=rec[5],
                    quantity=quantity,
                    raw=bytes(rec),
                )
        off += 4  # records observed to be 4-byte aligned


def set_quantity(char_slot_bytes: bytearray, record_offset: int, new_qty: int) -> None:
    """In-place quantity update at `record_offset` (u16 BE at offset+8)."""
    if not (0 <= new_qty <= 0xFFFF):
        raise ValueError(f"quantity {new_qty} out of range for u16")
    # Sanity: ensure the record shape still matches at the target offset.
    rec = char_slot_bytes[record_offset : record_offset + RECORD_SIZE]
    if not _is_inventory_shape(bytes(rec)):
        raise ValueError(
            f"no inventory-shaped record at 0x{record_offset:x} — bytes: {bytes(rec).hex()}"
        )
    char_slot_bytes[record_offset + 8 : record_offset + 10] = new_qty.to_bytes(2, "big")

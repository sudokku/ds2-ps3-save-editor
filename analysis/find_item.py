"""Locate item records in a DS2 PS3 character-slot file.

Usage:
    python analysis/find_item.py <path-to-USER.DAT> [--all]

Scans a character-slot file (`01USER.DAT` etc., 111,292 bytes) for item records.
By default lists only records that match the confirmed 16-byte shape.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# GoodsParam row * 10000 = save u32 BE
KNOWN_ITEMS = {
    50920000: "Soul of a Giant",
    60010000: "Lifegem",
    60510000: "Rubbish",
    60680000: "Large Soul of a Proud Knight",
}


def is_inventory_shaped(rec: bytes) -> bool:
    """Filter for the confirmed 16-byte inventory record shape.

    Rejects the recipe/reference rows at 0x1E0 (which end with FF FF FF FF).
    """
    return (
        len(rec) == 16
        and rec[4] == 0x00
        and rec[6:8] == b"\x00\x00"
        and rec[10:16] == b"\x00" * 6
    )


def scan(data: bytes, start: int = 0x1000):
    """Yield (offset, item_id, flag, qty, record) for every inventory-shaped record."""
    off = start
    end = len(data) - 16
    while off <= end:
        rec = data[off : off + 16]
        if is_inventory_shaped(rec):
            item_id = int.from_bytes(rec[0:4], "big")
            flag = rec[5]
            qty = int.from_bytes(rec[8:10], "big")
            if item_id != 0 and qty != 0:
                yield off, item_id, flag, qty, rec
        off += 4  # records are 4-byte aligned in practice


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path)
    ap.add_argument(
        "--all",
        action="store_true",
        help="include records with qty=0 or id=0",
    )
    args = ap.parse_args()

    data = args.path.read_bytes()
    print(f"# {args.path}  ({len(data)} bytes)")
    print(f"# {'offset':>7}  {'item_id':>10}  {'location':>9}  {'qty':>4}  name")

    for off, item_id, flag, qty, _ in scan(data):
        loc = "item_box" if flag == 0x80 else ("inventory" if flag == 0x00 else f"?0x{flag:02x}")
        name = KNOWN_ITEMS.get(item_id, "")
        print(f"  0x{off:04x}   {item_id:>10}  {loc:>9}  {qty:>4}  {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

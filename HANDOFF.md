# Handoff to next session

Read `CLAUDE.md` first. This file is what to do next; `CLAUDE.md` is the ambient orientation.

## Where we left off

An MVP Tkinter editor exists at `ds2ps3edit/`. It:

- Auto-detects the RPCS3 save directory for NPUB31358.
- Reads character name, stats block (VGR/END/VIT/ATN/STR/DEX/INT/FTH/ADP, Level, Souls, SoulsMemory) at file offset `0x20`.
- Scans inventory item records from the fresh mirror (~344 real items on the reference character).
- Backs up the save dir to `saves/live-backup-<timestamp>/` on every commit.
- Writes stat changes and item quantity changes across all mirrors that contain the record.

Confirmed working end-to-end: read path against the live save (`python -m ds2ps3edit` opens the GUI cleanly with correct character name, stats, and known items). **Write path is not yet verified in-game with this codebase** — the manual byte edit we did earlier worked, and the code follows the same procedure, but nobody has run `ds2ps3edit` → save → RPCS3 yet.

## First things to do

### 1. Manually verify the write pipeline end-to-end (30 min, blocks everything else)

Open a save with `python -m ds2ps3edit`. Change something obvious (e.g. Rubbish qty 4 → 5, or Souls wallet 3000 → 30000). Click Save. Confirm:

- A new `saves/live-backup-<ts>/` directory appeared.
- Launch RPCS3, load save, verify in-game state matches the edit.
- If not, restore from backup by copying the backup dir contents over the live save dir.

If this fails, the bug is almost certainly in `ds2ps3edit/core/save.py::commit` or `apply_stats/apply_item_qty`.

### 2. Item name catalog scrape (unblocks the UI's usability)

Right now `ds2ps3edit/core/items_db.py` has 4 items hardcoded. Everything else in the UI shows as `Unknown 0x<id>`. Get a mapping of DS2 (original) GoodsParam row → English name into a JSON/CSV.

Preferred sources:
- `github.com/nemesismonkey/darksouls2` (original DS2 item hex list; used as one of the two sources for our item-id research)
- Any DS2 params dump exposed by DSMapStudio / Yapped forks
- Fextralife / Fandom wiki pages that list item IDs in tables

Load the mapping into `items_db.py` (or a separate `data/items.json` if it's large). Preserve the `save_u32 = row * 10000` formula — the JSON should be keyed on either the row or the u32.

### 3. Stricter type-based edit gating

`items_db.item_type_from_id` covers Jappi88's range table (10..1009) plus an empirical `boss_soul` bucket for 5xxx. Real DS2 has many more categories with high row numbers (the reference character has 290 items classified as `unknown`). Either extend the range table from the scraped item catalog or gate editability differently (e.g. maintain an explicit list of stack-safe item ids).

Currently `is_editable_type` returns True for `unknown` so users can still edit those; keep that fallback until the catalog is trustworthy.

### 4. Multi-character-slot detection (only if needed)

Reference character has one slot (Vanea Zoloncen). If the user or a community member has multiple characters, slot 2 lives in `02USER.DAT` + `102USER.DAT` + `202USER.DAT`, slot 3 in `03USER.DAT` + `103USER.DAT` + `203USER.DAT`, etc. Extend `mirror.list_slot_mirrors` to enumerate slots 1..10, and add a slot picker to the GUI.

Detect "in use" vs "empty slot" by checking whether the character-slot file's stats block has non-zero values (empty slots are all-zero medium-sized files).

## Bigger unlocks (post-MVP)

- **Boss/NPC/event flags** — the ~502 KB progress files (`0BUSER.DAT` etc.) are the frontier. No prior tool touches them. Approach: player quits after killing a boss to make Archive-F, diff progress files, look for single-bit flips in a plausible flag-bit-array region.
- **Weapon/armor decoding on PS3** — verify Jappi88's byte-8..15 layout (durability f32 + upgrade + infusion) with a controlled experiment: reinforce or infuse one weapon in-game, snapshot before/after, diff.
- **The mystery u32 at 0x44** — controlled experiment: spend souls (buy from a vendor), snapshot before/after, see whether the field decreases with the wallet or stays put with SoulsMemory. That disambiguates its semantics.
- **Round-trip tests** — for every archive in `saves/*.zip`, `SaveHandle.open(extracted_dir)` → `.commit()` to a scratch location should produce byte-identical bytes. Write these as pytest tests in `tests/`.

## Gotchas worth internalizing

- **Fresh mirror ≠ `01USER.DAT` always.** It rotates. Always find fresh by mtime (`core/mirror.py` handles this).
- **Reference/recipe tables at `0x1E0` in the character-slot file and `0x128` in the metadata files look like item records but are not.** `inventory._is_inventory_shape` filters them out. If you loosen that filter, you'll get false positives.
- **Item ID divisibility rule (`id % 100 == 0, id >= 100000`) is empirical, not guaranteed by the format.** If a valid item is missing from the scan, revisit the filter first.
- **Jappi88's offsets are relative to a `SaveBlock` data area, not file byte 0.** His `Souls @+0x1C` maps to file byte `0x3C`, i.e. block base = `0x20` (not the `0x24` that a naive read of his code suggests). If porting more fields, verify each with a known ground-truth value.
- **PS3 saves store character name as UTF-16BE with spaces converted to underscores** (empirical; user typed "vanea zoloncen" but the file has `vanea_zoloncen`).
- **RPCS3 must be fully quit** before writing to the live save. The editor doesn't check for this yet — worth adding a pre-flight pid check.

## Reference material

- `docs/SaveFormat.md`, `docs/CharacterStats.md`, `docs/Inventory.md`, `docs/Findings.md` — the ground truth from our RE session.
- `saves/Archive-A..E.zip` — controlled snapshots with documented in-game deltas (see README.md and Findings.md for what each archive represents).
- Jappi88's C# editor at `github.com/Jappi88/Dark-Souls-II-SE` — treat as documentation, not a source of truth. Enums (covenants, classes, infusions) reliable; offsets need verification.
- RPCS3 issue [#9580](https://github.com/RPCS3/rpcs3/issues/9580) — confirms no PFD encryption on emulator saves.

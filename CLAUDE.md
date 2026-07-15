# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Open-source save parser/editor for **Dark Souls II PS3 (PSN Digital, NPUB31358, v1.10)** running under RPCS3. Scope is deliberately narrow: **only this exact platform.** No SOTFS, no Xbox 360, no PC, no real PS3 hardware (PFD-signed saves out of scope). Not a multiplayer cheating tool.

## Repository layout

```
CLAUDE.md            ← you are here
HANDOFF.md           ← where a fresh session should start reading
README.md            ← original problem statement (research-era, kept for context)
pyproject.toml       ← package definition; entry point ds2ps3edit = ds2ps3edit.gui.app:main
docs/                ← reverse-engineering documentation
  SaveFormat.md      ← file classes, mirrors, container header, no-checksum finding
  CharacterStats.md  ← stats block at file 0x20 with verified fields
  Inventory.md       ← 16-byte item record, id formula, edit procedure
  Findings.md        ← chronological RE log with corrections
ds2ps3edit/          ← the Python package (MVP)
  core/              ← format library, no UI dependency
    mirror.py        ← locate save dir; find fresh vs stale mirror
    stats.py         ← read/write stats block; read character name
    inventory.py     ← scan/edit 16-byte item records
    items_db.py      ← id → name lookup (starter; scrape needed)
    backup.py        ← timestamped save-dir copy before mutations
    save.py          ← SaveHandle: open → mutate → commit
  gui/
    app.py           ← Tkinter MVP window
  __main__.py        ← python -m ds2ps3edit
analysis/            ← throwaway analysis scripts (not part of the package)
  find_item.py       ← standalone inventory scanner
saves/               ← reference snapshots (immutable) + timestamped backups
  Archive-A..E.zip   ← controlled snapshots with documented in-game deltas
  live-backup-*/     ← auto-created by the editor before writes; gitignored
work/                ← extracted archives + third-party clones (gitignored)
```

## What's confirmed vs open

**Confirmed** (verified in-game or across ≥2 snapshots):
- Save is unencrypted on RPCS3 (no PFD emulation) and has no application-level checksum.
- Character-slot data lives in a triple-mirror scheme: `01USER.DAT`, `101USER.DAT`, `201USER.DAT`. Two of three exist at any time; the newest-mtime one is fresh.
- Character stats block starts at file offset `0x20` in the character-slot file.
- Item records are 16 bytes: `id_u32_BE | 00 | flag(0x00 inv, 0x80 box) | 00 00 | qty_u16_BE | 00*6`.
- Item id formula: `save_u32 = GoodsParam_row × 10000`, optional 3-digit upgrade suffix for weapons.
- Character name is at `USER.DAT:0x1EE` as UTF-16BE (also mirrored at `16USER.DAT:0x1BA`).
- End-to-end write pipeline works: modifying qty in `01USER.DAT`/`101USER.DAT` and reloading in RPCS3 produces expected in-game inventory. No PARAM.SFO update required.

**Open** (untouched or contradicted):
- Weapon/armor bytes 8..15 (durability + upgrade + infusion) — Jappi88's layout, unverified on PS3. MVP treats these as read-only.
- Boss/NPC/event flags — likely in the 501,928-byte progress file (0BUSER etc.), no offsets known.
- Semantics of the u32 at slot-file 0x44 (Jappi88 labels "SoulsNeeded", but value equals SoulsMemory on PS3 → mislabeled).
- `USER.DAT:0x232-0x233` and `16USER.DAT:0x1FE-0x1FF` change every save (save serial? rotation pointer?) — not a checksum, game accepts unchanged trailer.

## Working principles

- Never edit random bytes. Always backup first via `SaveHandle.commit()` or explicitly through `core.backup`.
- Reference saves in `saves/*.zip` are **immutable**. Extract to `work/extracted/` for analysis.
- Every documented field must record offset, size, purpose, and confidence level (see existing docs).
- Empirically verify offsets against a known snapshot before trusting Jappi88's schema — his `SoulsNeeded` label was wrong on PS3, and his stat block base is off by 4 vs the raw file layout.
- Round-trip test target: any parser we write should decode each archive, re-encode, and produce byte-identical output.

## Common commands

```bash
# Run the GUI against the auto-detected RPCS3 save
python -m ds2ps3edit

# Standalone item scanner on an extracted character-slot file
python analysis/find_item.py work/extracted/Archive-E/101USER.DAT
```

Python 3.12+, no external runtime deps for the MVP (Tkinter ships with Python).

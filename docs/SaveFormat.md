# DS2 PS3 Save Format

Target: **Dark Souls II PS3 (PSN Digital, NPUB31358, v1.10)** under RPCS3.

All confidence tags:
- **Confirmed**: verified against ≥2 controlled snapshots + in-game reload.
- **Strong**: pattern holds across all snapshots, consistent with an external reference.
- **Working**: current best guess; not yet contradicted.
- **Open**: unknown or suspicious.

## Overview

A save is a directory of ~48 `*USER.DAT` files plus `PARAM.SFO` and `ICON0.PNG`. All bytes are **big-endian** (PS3 is PowerPC).

**RPCS3 does not implement PS3 PFD signing** ([rpcs3#9580](https://github.com/RPCS3/rpcs3/issues/9580)), so files land unencrypted on disk. Entropy analysis confirms this: structured files sit at 0.3–1.5 bits/byte. **Confirmed.**

**No application-level checksum exists on PS3.** Jappi88's Xbox 360 branch appends MD5; the PS3 branch does not. Byte flips at `USER.DAT:0x232`/`16USER.DAT:0x1FE` on every save are a save serial / rotation pointer, **not** a validating checksum — the game accepts edits without recomputation. **Confirmed** (edit succeeded in-game with no trailer update).

## File classes by size

| Size | Count | Role | Notes |
|---|---|---|---|
| 5,996 | 1–3 | Slot-index / global header | `USER.DAT`, `1USER.DAT`, `2USER.DAT` — one of each may exist per rotation |
| 13,232 | 1–3 | Metadata mirror | `16USER.DAT`, `116USER.DAT`, `216USER.DAT` — mirrors save-serial byte |
| 111,292 (0x1B2BC) | 10 + rotating | Character slot data | `01`..`0AUSER.DAT` + rotating `1xx`, `2xx` mirrors |
| 501,928 (0x7A8A8) | ~15 | World/progress data | `0B`..`0FUSER`, `10USER`, `10BUSER`, `11`..`14USER`, plus `2xx` mirrors |
| 1,048,576 (1 MB) | 4 | zlib-compressed BND4 slabs | `15USER`, `17USER`, `115USER`, `117USER` |
| 4,880 | 1 | `PARAM.SFO` | Standard PS3 save metadata |
| 21,097 | 1 | `ICON0.PNG` | Save-list icon |

## Container header

Every non-slab file starts with a 16-byte header (big-endian):

```
u32 type_id      # 0, 2, 3, or 4 seen
u32 flag         # 0x64, 0x67, or 0x6F seen — likely schema version tag
u32 payload_sz   # matches file body length
u32 reserved     # always zero
```

`USER.DAT` and `1USER.DAT` share identical headers — same schema, different content role. **Strong.**

## Triple-mirror rotation

Character-slot data is stored in **three physical mirrors**: `01USER.DAT`, `101USER.DAT`, `201USER.DAT` for slot 1 (analogous for other slots). On every save, the game writes to **two of the three** mirrors — the "fresh" pair — and the third stays as the pre-existing stale copy. Which two are fresh rotates over consecutive saves. **Confirmed** across 5 snapshots.

Observations:
- Mirrors can diverge — a stale mirror keeps its old inventory/quantities intact while a fresh one shows the new state.
- The rotation applies to the whole family: `1USER↔2USER`, `16USER↔116USER↔216USER`, `10BUSER↔20BUSER`, etc. rotate together.
- `USER.DAT` byte `0x5C` toggles `0x00 ↔ 0x01` between saves — likely the "active bank" indicator that the game reads first to pick which mirror to load. **Working hypothesis.**

**Practical rule for editors:** when writing, patch the fresh mirror (identified by mtime or by cross-checking observed in-game state). Empirically also patching stale mirrors is safe and cheap; not required — the game overwrote our stale mirror on next save.

## The 1 MB slabs

`15USER.DAT` / `17USER.DAT` / `115USER.DAT` / `117USER.DAT` layout:

```
u32 compressed_size    (BE)
u32 decompressed_size  (BE)
zlib stream (0x78 0x9C header)
```

Decompressed payload starts with `42 4E 44 34` = **"BND4"** — the FromSoft binder format used across DS1–Elden Ring. Existing tools (SoulsFormats library, BinderTool) can parse these. Content unknown; likely bulk assets (face model, appearance render, screenshot). **Confirmed** container, **Open** payload semantics.

## Root file `USER.DAT` (5,996 bytes)

Known bytes:

| Offset | Purpose | Notes |
|---|---|---|
| 0x00–0x0F | Container header | type=3, flag=0x64, payload_sz=0x14 |
| 0x5C | Active bank flag | Toggles 0x00 ↔ 0x01 every save. Working hypothesis: chooses which mirror the game loads. |
| 0x232–0x233 | Save serial / rotation counter | Changes every save. Not a checksum (game accepts unchanged trailer after unrelated edits). |

Same shape mirrored in `1USER.DAT` and `2USER.DAT` — these are alternate "slot index" file names selected by the rotation.

## Small metadata file `16USER.DAT` (13,232 bytes)

Mirrors the bank flag and serial trailer from `USER.DAT`:

| Offset | Purpose |
|---|---|
| 0x28 | Bank flag (mirror of USER.DAT:0x5C) |
| 0x1FE–0x1FF | Save serial trailer |
| 0x128 | Item-reference / recipe table row (see Inventory.md) — starts with `03 93 AE 10 03 9C 87 B0 03 98 F1 B8 FF FF FF FF` |

Mirrored across `116USER.DAT` and `216USER.DAT` via the same rotation.

## Character slot file (`01USER.DAT`, `101USER.DAT`, `201USER.DAT`)

Size 111,292 = **0x1B2BC** bytes. Jappi88 hardcodes `0x1B2BC` as the "main slot save data" size, which matches.

See `CharacterStats.md` for the character stats block and `Inventory.md` for the item table.

## World/progress file (`0BUSER.DAT`, `20BUSER.DAT` etc.)

Size 501,928 = **0x7A8A8** bytes. Jappi88 hardcodes `0x7A8A8` as "slot progress data" size — matches.

Content largely undecoded. B→C diffs of 66 bytes with heavy pointer-shift patterns (many u32s shifting by exactly `+0x640`) suggest an internal indexed table that reallocates when world state changes. Bonfires, boss flags, and event flags almost certainly live here. **Open.**

## PARAM.SFO

Standard Sony PS3 metadata format (`\0PSF` magic). Parseable with any PSF library. Contains title string, subtitle (usually save timestamp text), save size, and `SAVEDATA_DIRECTORY`. Jappi88 reads to validate `TITLE_ID = NPUB31358`; does not modify on save. Empirically not required to touch when editing user data. **Confirmed.**

## Open questions

1. What is the u32 at file `0x44` in the character slot? It equals SoulsMemory (both jumped +3000 in B→C), but at Level 226 the real next-level cost is ~125k–400k, so this is not `SoulsNeeded` as Jappi88's label claims. Possibly a duplicate SoulsMemory or a different cumulative.
2. Where is the actual "souls to next level" value stored, if anywhere? May be computed at runtime.
3. Semantics of the `USER.DAT:0x5C` bank flag under a 3-way rotation (binary flag but 3 mirrors).
4. Meaning of the small unknown u16s at slot-relative `+0x12`, `+0x14`, `+0x16` (values 1, 6, 0 for the reference character — stable across all 5 archives).
5. What the world/progress file (0x7A8A8) actually contains at the record level.
6. Semantics of the `0x1E0` and `0x128` reference tables in the character slot and metadata files.

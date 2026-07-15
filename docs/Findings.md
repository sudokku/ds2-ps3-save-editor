# Reverse Engineering Log

Chronological research log. Each entry lists the action taken, what was learned, and any hypothesis it confirmed or overturned.

## 2026-07-15 — Session 1

### Entry 1: File classification via entropy + magic bytes

Classified all `*USER.DAT` files by size. Six size classes emerged (5,996 / 13,232 / 111,292 / 501,928 / 1,048,576 / 4,880-SFO). Entropy analysis:

- Structured files: 0.3–1.5 bits/byte → not encrypted, not compressed.
- The 1 MB slabs (`15USER`, `17USER`, `115USER`, `117USER`): 7.67 bits/byte → compressed.

Verified zlib on the 1 MB slabs:
```
u32 compressed_size | u32 decompressed_size | 78 9c ... zlib stream
```
Decompressed magic = `42 4E 44 34` = **BND4** (FromSoft binder format). This aligns DS2 saves with the DS1–Elden Ring format lineage.

Conclusion: PS3 saves under RPCS3 are raw structured data — no encryption layer. RPCS3 issue [#9580](https://github.com/RPCS3/rpcs3/issues/9580) confirms PFD signing is not implemented.

### Entry 2: Prior-art audit — Jappi88's editor

Found [Jappi88/Dark-Souls-II-SE](https://github.com/Jappi88/Dark-Souls-II-SE) — a C#/GPL-3.0 editor from 2016 targeting exactly our platform (PS3 original DS2, NPUB31358). It solves stats, souls, inventory, item box, equipment, covenants, and bonfire unlock state. It does NOT solve boss/NPC/event flags, estus allocation, or face/appearance sliders.

Format constants extracted: main slot size `0x1B2BC` (= 111,292 bytes, matches our medium file class); progress data size `0x7A8A8` (= 501,928, matches our large class); PS3 secure file ID for NPUB31358 hardcoded.

Key intelligence: **no application-level checksum on the PS3 branch** — Xbox 360 gets an MD5 trailer, PS3 gets nothing.

### Entry 3: A→B diff overturns two hypotheses

Original README claimed A→B (moved 1 Soul of a Giant to item box) changed only `USER.DAT`, `16USER.DAT`, and `PARAM.SFO` (~2 bytes each). Actual diff:

- `USER.DAT`: byte `0x5C` flipped `0x00 → 0x01`, bytes `0x232-0x233` changed (save-serial-like).
- `16USER.DAT`: same two-change pattern.
- **File presence changed:** A had `0BUSER`, `116USER`, `1USER`, `201USER`; B had `20BUSER`, `216USER`, `2USER`, `101USER` in their place. Same sizes, swapped names.

Hypothesis: **triple-mirror rotation**, not "extra character slot files." Confirmed later.

### Entry 4: Direct item-ID search bypasses pattern hunting

Once the ID formula (`save_u32 = GoodsParam_row × 10000`) and canonical IDs were known:

```
Soul of a Giant       = 0x0308FA40
Lifegem               = 0x0393AE10
Rubbish               = 0x039B4F30
Large Soul of a PK    = 0x039DE740
```

Grepping the archives for these 4-byte patterns immediately revealed all inventory records. Also surfaced a spurious pattern at file offset `0x1E0` that is not an inventory record — it's a 4-item-IDs + `FF FF FF FF` sentinel, likely a recipe or starting-item reference table. Filter: inventory search must start at offset ≥ 0x1000.

### Entry 5: 16-byte record structure confirmed

Across all snapshots, item records have the exact shape:

```
<id_u32 BE> 00 <flag> 00 00 <qty_u16 BE> 00 00 00 00 00 00
```

`flag` = `0x00` (inventory) or `0x80` (item box). Cross-verified with known ground truth (SoG qty 2→1, Lifegem 10→9→8, Rubbish 5→3+box).

### Entry 6: Live edit test — write worked, game accepted it

Backed up live save, wrote `0x02` to file offset `0x39F5` in both fresh (`201USER.DAT`) and stale (`101USER.DAT`) mirrors. Result: game loaded successfully, inventory showed Soul of a Giant ×2 (was ×1) + item box ×1 = 3 total. User then moved the box SoG into inventory (→ merged to 3 in one stack) and saved. Archive-E fresh mirror shows the exact expected state.

**Milestone: end-to-end write pipeline confirmed. No checksum recomputation required. No PARAM.SFO update required.**

### Entry 7: Character stats block located — off-by-4 correction

Initially placed the stats block base at file offset `0x24` by matching Jappi88's `Souls @+0x1C` to a `+3000` delta at file `0x40`. Turned out `file 0x40` is `SoulsMemory (+0x20)`, not `Souls (+0x1C)`. Correct base is **`0x20`**.

Correction found because:
- User reported Souls wallet = 3,000 (not the 6,689,040 I had labeled).
- User reported VGR = 50; scanning for `0x0032` u16 BE placed it at file `0x20`.
- Both fit with base `0x20`.

Root cause: `0x40` and `0x44` both had `+3000` deltas because SoulsMemory and an unknown adjacent u32 were both `6,686,040` in B and both incremented to `6,689,040` in C. The actual wallet field at `0x3C` had `av = 0` and was filtered out by `av != 0` in my first delta scan.

### Entry 8: `SoulsNeeded` mislabeled

Jappi88's schema lists `SoulsNeeded` at relative offset `+0x24` (file `0x44`). Value in our snapshots = `SoulsMemory` (6,689,040). For a Level 226 character the real "souls to next level" is ~125k–400k. Conclusion: this field is not next-level cost; possibly a duplicate SoulsMemory or another cumulative. Semantics **open**.

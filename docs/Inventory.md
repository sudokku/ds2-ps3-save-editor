# Inventory Format

Character-slot file (`01USER.DAT` / `101USER.DAT` / `201USER.DAT`, 111,292 bytes).

## Item record — 16 bytes

**Confirmed** across five snapshots (A→B→C→D→E) via known in-game actions.

```
offset  size  field
0       u32   item_id (big-endian)
4       u8    always 0x00
5       u8    location flag: 0x00 = inventory, 0x80 = item box
6–7     u16   always 0x0000
8       u16   quantity (big-endian)  — for consumables/materials/arrows/spells
10–15   6×u8  always 0x00 (reserved/padding)
```

For weapons/armor the interpretation of bytes 8–15 differs (durability f32, weapon upgrade at +13, infusion at +14). Not yet verified on PS3 saves — extrapolated from Jappi88's PC/Xbox parser.

## Item ID formula

**Confirmed** for the four reference items.

```
save_id_u32 = GoodsParam_row × 10000
```

`GoodsParam` is the game's paramtable row ID; multiplied by 10000 to produce the value stored in the save. Both original DS2 and SOTFS use the same IDs for these core items.

## Verified item IDs

| Item | GoodsParam row | Save u32 (hex BE) | Decimal |
|---|---|---|---|
| Soul of a Giant | 5092 | `03 08 FA 40` | 50,920,000 |
| Lifegem | 6001 | `03 93 AE 10` | 60,010,000 |
| Rubbish | 6051 | `03 9B 4F 30` | 60,510,000 |
| Large Soul of a Proud Knight | 6068 | `03 9D E7 40` | 60,680,000 |

## Item type ranges (from Jappi88)

Only the last 4 digits of the decimal ID matter for typing (the `× 10000` factor is a scale).

| Row-range | Type |
|---|---|
| 10–129 | Weapon |
| 130–139 | Bow |
| 140–149 | Staff |
| 150–159 | Shield |
| 400–499 | Armor (400 head / 410 chest / 420 arms / 430 legs) |
| 500–599 | Ring |
| 600–699 | Arrow |
| 700–709 | Consumable |
| 710–719 | Key item |
| 720–799 | Upgrade material |
| 800–999 | Spell |
| 1000–1009 | Gesture |

Note: Soul of a Giant is row 5092 — outside these ranges, so the range table above is incomplete. Soul-type items live in the 5000s.

## Reference tables — DO NOT parse as inventory

Two locations look like item records but are recipe / starting-inventory lists:

- Character slot file `@0x1E0`: 16-byte rows shaped like `<id> <id> <id> <id> FF FF FF FF` — four u32 item IDs terminated with sentinel.
- Metadata files (`16USER.DAT` etc.) `@0x128`: same shape.

**Any inventory search must start from `offset ≥ 0x1000` to skip these.** Also the metadata files are entirely reference data — do not scan them for the live inventory.

## Verified per-item locations in the reference character

These offsets are stable across all five archives for this specific character. **They are not general** — different characters will have different inventory layouts.

| Item | Inventory record | Item-box record | Notes |
|---|---|---|---|
| Soul of a Giant | `0x39EC` | `0x2DFC` | Same offsets in every mirror where the record exists |
| Rubbish | `0x242C` | `0x368C` (when in box) | Box record offset different from SoG |
| Lifegem | `0x34DC` | — | Ref-table hit at 0x1E0 to ignore |
| Large Soul PK | `0x3A0C` | — | Disappears from record when consumed to zero |

**Working hypothesis:** each item is assigned a fixed offset when first acquired, and that slot persists even if quantity drops to zero (Large Soul PK disappearing in C contradicts this — see Findings.md). Adding a new item type or moving to/from the box allocates a new offset elsewhere in the file.

## Quantity edit — the minimum-diff mutation

Verified process for changing item quantity:

1. Read fresh mirror (newest mtime among `01`, `101`, `201`).
2. Pattern-search for the 4-byte item ID starting at offset `0x1000`.
3. At each hit, confirm shape: bytes `4=0x00, 6-7=0x00 0x00`, and `10-15 = 0x00×6`. This filters out reference-table rows.
4. Modify byte at `hit + 9` (low byte of the qty u16 BE). For quantities > 255 also modify byte at `hit + 8`.
5. Write patched file. No other file needs modification. No checksum. No PARAM.SFO update.

Optional: also patch stale mirrors that contain the same record. **Empirically not needed** — the game overwrote them on the next save automatically.

## Empirical evidence (Archive-E, post-edit)

Fresh mirror `101USER.DAT` after our +1 SoG patch + user moving box items to inventory:

```
SoG     @0x39EC  qty=3  INV       03 08 fa 40 00 00 00 00 00 03 00 00 00 00 00 00
Rubbish @0x242C  qty=4  INV       03 9b 4f 30 00 00 00 00 00 04 00 00 00 00 00 00
Lifegem @0x34DC  qty=8  INV       03 93 ae 10 00 00 00 00 00 08 00 00 00 00 00 00
(no records with flag 0x80 — item box empty)
```

Stale mirror `01USER.DAT` in the same archive still shows our patched pre-move state (SoG=2 INV + 1 BOX), proving the byte we wrote survived unmodified into a subsequent save cycle.

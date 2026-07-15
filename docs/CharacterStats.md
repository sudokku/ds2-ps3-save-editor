# Character Stats Block

Located in the character-slot file (`01USER.DAT` / `101USER.DAT` / `201USER.DAT`).

## Base offset — `0x20`

**Confirmed.** The stats block starts at file offset `0x20` in the character-slot file. This is Jappi88's `SaveBlock[0]` data area on PS3.

Note: Jappi88's C# code implies a 0x24 base if you naively map his relative offsets to file bytes; the correct value on PS3 is 0x20 (the container header appears to be 0x20 bytes, not 0x24). Verified by matching known player VGR=50 to `u16 BE @0x20 = 0x0032`.

## Field layout (all big-endian)

| Rel. offset | File offset | Size | Field | Notes |
|---|---|---|---|---|
| 0x00 | 0x20 | u16 | VGR (Vigor) | |
| 0x02 | 0x22 | u16 | END (Endurance) | |
| 0x04 | 0x24 | u16 | VIT (Vitality) | |
| 0x06 | 0x26 | u16 | ATN (Attunement) | |
| 0x08 | 0x28 | u16 | STR (Strength) | |
| 0x0A | 0x2A | u16 | DEX (Dexterity) | |
| 0x0C | 0x2C | u16 | INT (Intelligence) | |
| 0x0E | 0x2E | u16 | FTH (Faith) | |
| 0x10 | 0x30 | u16 | ADP (Adaptability) | |
| 0x12 | 0x32 | u16 | Unknown1 | Reference character = 1. Stable across all snapshots. |
| 0x14 | 0x34 | u16 | Unknown2 | = 6. Stable. |
| 0x16 | 0x36 | u16 | Unknown3 | = 0. Stable. |
| 0x18 | 0x38 | u32 | Level (Soul Level) | |
| 0x1C | 0x3C | u32 | **Souls (wallet)** | Verified via +3000 signature in B→C. |
| 0x20 | 0x40 | u32 | SoulsMemory | Total souls earned this playthrough. Also +3000 in B→C. |
| 0x24 | 0x44 | u32 | Unknown (was labeled SoulsNeeded by Jappi88 — appears mislabeled on PS3) | Value equal to SoulsMemory in all snapshots. **Open.** |
| 0x28 | 0x48 | u32 | Unknown (Jappi88 label: MaxHealth) | Reference char value = 2298. Not verified as HP. **Working.** |

Further fields per Jappi88 (not yet cross-verified on PS3):

| Rel. offset | Purpose | Status |
|---|---|---|
| 0x9F + i | Covenant membership flag (i = covenant index 0..9) | Extrapolated |
| 0xA9 + i | Covenant rank | Extrapolated |
| 0xC7 | 22 × RGB triplets (appearance colors) | Extrapolated |
| 0x128 | SlotFlag (u8) | Extrapolated |
| 0x15A | Gender (0=Male, 1=Female) | Extrapolated |
| 0x15B | HollowLv | Extrapolated |
| 0x16C | Equipment slot table (0xB0 bytes) | Extrapolated |

## Reference character values

Stable across archives A–E (character was not leveled during experiments):

```
VGR 50   END 40   VIT 20   ATN 25
STR 47   DEX 27   INT 18   FTH 18   ADP 34
Unknown1=1  Unknown2=6  Unknown3=0
Level 226
Souls wallet: A=0, B=0, C/D/E=3000
SoulsMemory:  A/B=6,686,040, C/D/E=6,689,040 (+3000 gained in C)
Unknown@0x44: mirrors SoulsMemory exactly
Unknown@0x48: 2298 (constant)
```

## Editing procedure

Same rules as inventory:

1. Locate fresh mirror.
2. Write BE-encoded value at `file_offset = 0x20 + relative_offset`.
3. No checksum, no other files.
4. Optionally mirror to stale copies.

## Open questions

- The Unknown at `+0x24` (file `0x44`) equals SoulsMemory — is it a duplicate, a "peak souls held" counter, or something else? Trigger to differentiate: spend souls or die.
- The Unknown at `+0x28` (file `0x48`) is 2298 for our character — could be Max HP, cumulative deaths, or a class-based derived stat. Trigger: level VGR.
- Where are HP-current, stamina-current, souls-to-next-level, and playtime? Not obviously in the first 0x50 bytes.
- Which stat block (if any) verifies against a per-character checksum? Assumption is none — but an unrelated field far from stats (e.g. in the world-progress file) could still validate.

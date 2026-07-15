# Dark Souls II PS3 Save Research (RPCS3)

## Objective

Reverse engineer the save format used by the **PlayStation 3 digital version of Dark Souls II (NPUB31358)** running under RPCS3.

The long-term objective is to create an open-source save parser/editor capable of:

- Reading player save data.
- Decoding inventory.
- Decoding storage box.
- Decoding player stats.
- Decoding souls.
- Editing values safely.
- Recalculating all integrity/checksum fields automatically.
- Writing a valid save accepted by the game.

This project is **NOT** intended for multiplayer cheating.

Primary goals:

- Save recovery
- Preservation
- Research
- Offline save editing
- Documentation of an undocumented file format

---

# Platform

**Game:** Dark Souls II

**Platform:** PlayStation 3

**Distribution:** PSN Digital

**Title ID:** NPUB31358

**Running under:** RPCS3

---

# Current Goal

Recover one accidentally consumed **Soul of a Giant**.

The save owner consumed two unique Souls of a Giant during normal gameplay before realizing they permanently affect Vendrick's defenses.

Rather than editing emulator memory, the objective is to understand the save format and restore one missing inventory entry in a generic, reusable manner.

---

# Known Facts

- Platform: RPCS3
- Game: Dark Souls II (PSN Digital)
- Title ID: NPUB31358
- Save format consists of many `.DAT` files rather than a single save.
- `10BUSER.DAT` is currently the strongest candidate for containing character data.
- `USER.DAT` and `16USER.DAT` appear to contain metadata and/or integrity information.
- Archive A, B and C differ **only** by the explicitly documented actions.
- No combat, leveling, equipment changes or travel occurred unless explicitly stated.
- Every snapshot was created by quitting normally through the in-game menu.

---

# Existing Save Snapshots

Three save archives exist.

These are carefully controlled experiments and should be treated as immutable reference snapshots.

## Archive A (Baseline)

Inventory:

- Soul of a Giant ×2
- Rubbish ×5
- Lifegem ×10
- Large Soul of a Proud Knight ×1

Item Box:

- Empty

Player souls unchanged.

---

## Archive B

Starting from Archive A.

Exactly one action:

Move **one Soul of a Giant**

Inventory → Item Box

Final state:

Inventory:

- Soul of a Giant ×1
- Rubbish ×5
- Lifegem ×10
- Large Soul of a Proud Knight ×1

Item Box:

- Soul of a Giant ×1

Nothing else changed.

Saved immediately.

This snapshot is particularly valuable because the same unique item exists simultaneously in inventory and storage.

---

## Archive C

Starting from Archive B.

Performed exactly:

- Consumed 1 Lifegem (10 → 9)
- Consumed 1 Large Soul of a Proud Knight (1 → 0)
- Gained exactly 3000 player souls
- Discarded 1 Rubbish
- Moved 1 Rubbish into the Item Box

Final state:

Inventory:

- Soul of a Giant ×1
- Rubbish ×3
- Lifegem ×9

Item Box:

- Soul of a Giant ×1
- Rubbish ×1

Player Souls:

- +3000

Nothing else changed.

Saved immediately.

---

# Initial Findings

### Archive A → B

Changed files:

- USER.DAT
- 16USER.DAT
- PARAM.SFO

Only two bytes changed inside USER.DAT and 16USER.DAT.

Hypothesis: metadata / integrity information.

### Archive B → C

Changed files:

- USER.DAT
- 16USER.DAT
- 01USER.DAT
- 10BUSER.DAT (~502 KB)
- PARAM.SFO

Hypothesis: `10BUSER.DAT` contains the actual character payload.

---

# Reverse Engineering Strategy

Never edit random bytes.

1. Produce automated binary diffs.
2. Locate changed regions.
3. Identify repeating structures.
4. Determine endianness, alignment and record size.
5. Locate player soul count.
6. Locate inventory.
7. Locate storage.
8. Identify checksum/integrity mechanism.
9. Only then perform edits.

---

# Things To Investigate

## Compression

Determine whether DAT files are:

- Raw
- Compressed
- XOR encoded
- Encrypted
- Chunked

Test:

- zlib
- gzip
- LZ4
- LZO
- custom formats

---

## Entropy

Calculate entropy for every DAT.

---

## Binary Pattern Search

Search for repeating structures of common sizes:

- 16 bytes
- 24 bytes
- 32 bytes
- 64 bytes

---

## Inventory Detection

### Soul of a Giant

Archive A:

Inventory ×2

↓

Archive B:

Inventory ×1

Item Box ×1

Determine whether:

- inventory and storage share a record format
- location is encoded as a flag
- inventory and storage are separate tables
- both reference a common record

### Rubbish

Archive B:

Inventory ×5

↓

Archive C:

Inventory ×3

Item Box ×1

One discarded.

One moved to storage.

### Lifegem

10 → 9

### Large Soul of a Proud Knight

1 → 0

### Player Souls

+3000

---

# Desired Repository Layout

```
analysis/
    compare.py
    entropy.py
    diff_regions.py
    find_records.py
    find_checksums.py
    locate_soul_counter.py
    inventory_detector.py
    storage_detector.py

parser/
    reader.py
    writer.py
    checksum.py
    inventory.py
    player.py
    storage.py

docs/
    SaveFormat.md
    Checksums.md
    Inventory.md
    Storage.md
    Findings.md
```

---

# Coding Guidelines

- Python 3.12+
- Document every discovery.
- No unexplained magic numbers.
- Every field should include:
  - offset
  - size
  - purpose
  - confidence level
- Never overwrite original saves.
- Always write modified saves into a separate output directory.

---

# Success Criteria

Minimum:

- Restore one missing Soul of a Giant.

Better:

- Decode inventory.

Great:

- Produce a reusable parser.

Ultimate:

- Create an open-source save editor for the PS3 version of Dark Souls II compatible with RPCS3.

---

# Philosophy

Treat this as a genuine reverse engineering research project.

Prefer understanding over hacking.

Every hypothesis should be reproducible using the supplied save snapshots.

The end goal is a parser/editor that supports arbitrary saves—not just the author's.

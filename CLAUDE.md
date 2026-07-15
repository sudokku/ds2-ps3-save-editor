# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Reverse engineering research project targeting the **Dark Souls II PS3 (PSN Digital, NPUB31358)** save format as produced by RPCS3. Long-term goal: an open-source parser/editor. Immediate goal: restore one accidentally consumed Soul of a Giant. Not a multiplayer cheating tool.

Read `README.md` for the full problem statement, snapshot inventories, and success criteria — the reference save data described there is the ground truth for every hypothesis.

## Repository state

The repo is currently research-only. `analysis/`, `parser/`, `docs/`, and `findings/` are empty scaffolds matching the layout in `README.md`. The only real content is:

- `saves/Archive-{A,B,C}.zip` — three carefully controlled save snapshots. **Treat these as immutable reference data.** Never modify or re-zip them. Extract to a working directory outside `saves/` if needed.

There is no build, lint, or test tooling yet. Coding target is Python 3.12+.

## Snapshot semantics (critical)

A → B → C is a controlled diff chain. Each transition changed **only** the explicitly documented in-game actions (see README "Existing Save Snapshots"). This is what makes the snapshots useful:

- **A → B**: exactly one action — move 1 Soul of a Giant from inventory to item box. Files changed: `USER.DAT`, `16USER.DAT`, `PARAM.SFO`. Only ~2 bytes differ in the DAT files → likely metadata/integrity.
- **B → C**: several small inventory/soul deltas. `10BUSER.DAT` (~502 KB) changes → likely the character payload. `01USER.DAT` also changes.

Any tool or hypothesis should be reproducible against these three archives.

## Working principles (from README)

- Never edit random bytes; follow the diff → locate → identify structure → checksum → edit pipeline in README "Reverse Engineering Strategy".
- Never overwrite originals; write modified saves to a separate output directory.
- Every documented field must record offset, size, purpose, and confidence level. No unexplained magic numbers.
- Prefer understanding over hacking — every hypothesis reproducible against the three snapshots.

## Desired module layout

The README enumerates the intended file layout under `analysis/` (compare, entropy, diff_regions, find_records, find_checksums, locate_soul_counter, inventory_detector, storage_detector) and `parser/` (reader, writer, checksum, inventory, player, storage), and docs under `docs/`. New code should slot into that structure.

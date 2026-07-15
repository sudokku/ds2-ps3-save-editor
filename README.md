# DS2 PS3 Save Editor

Open-source save editor for **Dark Souls II** on the **PlayStation 3** digital version (`NPUB31358`, v1.10) running under **RPCS3**. Scope is deliberately narrow — no SOTFS, no Xbox, no PC, no real-hardware PS3.

Built after we discovered that no editor targets this specific version anymore. See `docs/Findings.md` for the reverse-engineering log.

**Not a multiplayer cheating tool.** Use it on offline saves for recovery, preservation, and messing around.

---

## Status

**MVP (0.1)**. What works:

- Reads character name, all attributes, level, souls wallet, souls memory
- Reads inventory (~300+ items on a mid-progression character), identifies known items by name
- Edits stat values (attributes, level, souls)
- Edits item quantities for stackable types (consumables, materials, key items, arrows, boss souls)
- Auto-backs up the entire save directory before every write

Not yet: weapon upgrade/infusion editing, boss/NPC/event flags, appearance sliders, multi-character-slot switching, item catalog beyond 4 names (see `HANDOFF.md`).

---

## Requirements

- **Python 3.12+** (Tkinter ships with it — no `pip install` needed for the MVP)
- **RPCS3** with a Dark Souls II NPUB31358 save
- **The game fully quit and RPCS3 closed** before saving edits

Tested on macOS. Should work on Linux and Windows — the save-path auto-detection assumes the macOS RPCS3 layout; on other OSes you'll need to use "Open save…" and pick the directory manually.

---

## Install & run

```bash
git clone https://github.com/sudokku/ds2-ps3-save-editor
cd ds2-ps3-save-editor
python -m ds2ps3edit
```

Or install as a script:

```bash
pip install -e .
ds2ps3edit
```

---

## Usage

1. **Quit RPCS3.** Editing the save while the emulator has it open will get your changes clobbered or, worse, corrupt the save.
2. Launch the editor. On macOS it auto-opens your default save at:
   ```
   ~/Library/Application Support/rpcs3/dev_hdd0/home/00000001/savedata/NPUB31358-GAME_000
   ```
   On other OSes, click **Open save…** and pick that directory manually.
3. The top of the window shows your character name and which mirror files exist (DS2 uses a triple-mirror copy-on-write scheme — see `docs/SaveFormat.md`).
4. **To edit stats:** type new values into the entry boxes. Click **Save (backup + write)** to commit.
5. **To edit item quantities:** find the row, double-click the `qty` column. A prompt appears; enter the new quantity (0–65535). If the item type isn't editable in the MVP (weapon, armor, ring, staff, shield), the app tells you and refuses.
6. Click **Save**. You'll get a popup with the backup path.
7. Launch RPCS3, load the save, verify the change is live.

Rows show columns: file offset, item id, coarse type, name (or `Unknown 0x…` if not in the catalog yet), location (inventory or item box), qty.

---

## Backups & restore

Every save creates `saves/live-backup-<timestamp>/` with a full copy of the save directory. Restore by copying it back:

```bash
cp -R saves/live-backup-<timestamp>/* \
      ~/Library/Application\ Support/rpcs3/dev_hdd0/home/00000001/savedata/NPUB31358-GAME_000/
```

Nothing else in the editor deletes backups — clean them up manually when you're confident.

---

## What NOT to do

- Do NOT run the editor while RPCS3 is open.
- Do NOT edit `saves/Archive-A..E.zip` — these are the reference snapshots the RE work depends on.
- Do NOT max out stats beyond DS2's actual soft caps (99) unless you want to see the game behave weirdly. The editor won't stop you.
- Do NOT set quantities above the real in-game stack cap (usually 99 or 999 depending on item). It probably won't crash but might display badly.

---

## Contributing

The frontier is:

- Item name catalog scrape (biggest impact — see `HANDOFF.md` §2)
- Boss/NPC/event flag decoding (no prior tool has done this)
- Weapon upgrade & infusion editing
- Face/appearance sliders

Format docs live under `docs/`:

- `SaveFormat.md` — file structure, mirrors, no-checksum finding
- `CharacterStats.md` — stats block layout
- `Inventory.md` — item record layout and editing procedure
- `Findings.md` — chronological reverse-engineering log

`HANDOFF.md` is the "next steps" guide for anyone (human or agent) picking up the project.

---

## License

GPL-3.0-or-later. Format knowledge cross-references [Jappi88/Dark-Souls-II-SE](https://github.com/Jappi88/Dark-Souls-II-SE) (also GPL-3.0). Item IDs cross-referenced with community sources documented in `docs/Findings.md`.

---

## Disclaimer

This tool modifies game save files. Save corruption is possible if you edit fields we haven't documented, run it while the emulator is holding the save, or push values outside the game's expected ranges. Backups are automatic but not magic. **Use at your own risk on saves you can afford to lose.**

"""Tkinter MVP: character stats + inventory quantity editor.

Ugly by design. Focus is on the correct read/write pipeline, not looks.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..core.items_db import is_editable_type, item_type_from_id, name_for
from ..core.save import SaveHandle
from ..core.stats import STAT_FIELDS


class EditorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DS2 PS3 Save Editor (MVP)")
        self.root.geometry("900x700")
        self.save: SaveHandle | None = None
        self._stat_vars: dict[str, tk.StringVar] = {}
        self._build_layout()
        self._open_default()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self.root, padding=6)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open save…", command=self._on_open).pack(side="left")
        ttk.Button(toolbar, text="Reload", command=self._on_reload).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Save (backup + write)", command=self._on_save).pack(side="right")

        self.status = tk.StringVar(value="no save loaded")
        ttk.Label(toolbar, textvariable=self.status).pack(side="left", padx=12)

        body = ttk.Frame(self.root, padding=6)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)

        stats_frame = ttk.LabelFrame(body, text="Character stats", padding=6)
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for i, (name, _rel, _size) in enumerate(STAT_FIELDS):
            r, c = divmod(i, 4)
            label_text = f"{name} (auto)" if name == "SoulsMemory" else name
            ttk.Label(stats_frame, text=label_text).grid(row=r * 2, column=c, sticky="w", padx=(6, 0))
            var = tk.StringVar()
            self._stat_vars[name] = var
            entry_state = "readonly" if name == "SoulsMemory" else "normal"
            ttk.Entry(stats_frame, textvariable=var, width=14, state=entry_state).grid(
                row=r * 2 + 1, column=c, padx=(6, 12), pady=(0, 4)
            )

        inv_frame = ttk.LabelFrame(body, text="Inventory  (double-click a qty cell to edit editable items)", padding=6)
        inv_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        inv_frame.rowconfigure(0, weight=1)
        inv_frame.columnconfigure(0, weight=1)

        cols = ("offset", "id", "type", "name", "location", "qty")
        self.tree = ttk.Treeview(inv_frame, columns=cols, show="headings", height=20)
        for c, w in zip(cols, (70, 110, 100, 260, 90, 60)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c == "name" else "center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(inv_frame, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", self._on_tree_double)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _open_default(self) -> None:
        try:
            self.save = SaveHandle.open()
        except Exception as exc:  # noqa: BLE001
            self.status.set(f"couldn't auto-open default save: {exc}")
            return
        self._refresh()

    def _on_open(self) -> None:
        path = filedialog.askdirectory(title="Pick the NPUB31358-GAME_000 save directory")
        if not path:
            return
        try:
            self.save = SaveHandle.open(Path(path))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Failed to open save", str(exc))
            return
        self._refresh()

    def _on_reload(self) -> None:
        if self.save is None:
            return
        self.save = SaveHandle.open(self.save.save_dir)
        self._refresh()

    def _refresh(self) -> None:
        assert self.save is not None
        s = self.save
        self.status.set(
            f"{s.character_name}   ·   {s.save_dir.name}   ·   mirrors: {', '.join(s.mirror_names)}"
        )
        for name, _rel, _size in STAT_FIELDS:
            self._stat_vars[name].set(str(getattr(s.stats, name)))

        self.tree.delete(*self.tree.get_children())
        for rec in s.inventory:
            self.tree.insert(
                "",
                "end",
                iid=str(rec.offset),
                values=(
                    f"0x{rec.offset:04X}",
                    rec.item_id,
                    item_type_from_id(rec.item_id),
                    name_for(rec.item_id),
                    rec.location_label,
                    rec.quantity,
                ),
            )

    def _on_tree_double(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if self.save is None:
            return
        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id or col != "#6":  # only the qty column
            return
        item_offset = int(row_id)
        rec = next((r for r in self.save.inventory if r.offset == item_offset), None)
        if rec is None:
            return
        if not is_editable_type(rec.item_id):
            messagebox.showinfo("Not editable", f"MVP does not edit {item_type_from_id(rec.item_id)} items.")
            return
        # Popup entry
        current = rec.quantity
        new = _prompt_int(self.root, "New quantity", f"{name_for(rec.item_id)}  (current {current})", current)
        if new is None or new == current:
            return
        try:
            self.save.apply_item_qty(item_offset, new)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Edit failed", str(exc))
            return
        self._refresh()

    def _on_save(self) -> None:
        if self.save is None:
            messagebox.showerror("No save", "Open a save first.")
            return
        # Pull stats from entry boxes into the save
        try:
            new_stats = _stats_from_vars(self._stat_vars, self.save.stats)
        except ValueError as exc:
            messagebox.showerror("Invalid stat value", str(exc))
            return
        self.save.apply_stats(new_stats)
        try:
            backup = self.save.commit()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save failed", str(exc))
            return
        # Reflect any derived-field adjustments (e.g. SoulsMemory) back into the UI.
        self._refresh()
        messagebox.showinfo("Saved", f"Backup: {backup}\nWrote {len(self.save.mirror_names)} mirror(s).")


def _prompt_int(parent: tk.Widget, title: str, prompt: str, initial: int) -> int | None:
    win = tk.Toplevel(parent)
    win.title(title)
    win.grab_set()
    ttk.Label(win, text=prompt).pack(padx=12, pady=(12, 4))
    var = tk.StringVar(value=str(initial))
    entry = ttk.Entry(win, textvariable=var)
    entry.pack(padx=12, pady=4)
    entry.focus_set()
    entry.select_range(0, "end")
    result: dict[str, int | None] = {"value": None}

    def ok():
        try:
            v = int(var.get())
            if not (0 <= v <= 0xFFFF):
                raise ValueError("must be 0..65535")
            result["value"] = v
            win.destroy()
        except ValueError as exc:
            messagebox.showerror("Invalid", str(exc), parent=win)

    ttk.Button(win, text="OK", command=ok).pack(pady=(4, 12))
    win.bind("<Return>", lambda _e: ok())
    win.wait_window()
    return result["value"]


def _stats_from_vars(vars_: dict[str, tk.StringVar], baseline) -> "Stats":  # forward-ref string
    from ..core.stats import Stats
    kwargs = {}
    for name, _rel, _size in STAT_FIELDS:
        try:
            kwargs[name] = int(vars_[name].get())
        except ValueError:
            raise ValueError(f"{name}: not an integer")
    return Stats(**kwargs)


def main() -> None:
    root = tk.Tk()
    EditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

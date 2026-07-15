"""Cheap safety net: assert the SaveHandle public surface and core logic.

Run with `python3 -m pytest tests/` or `python3 tests/test_smoke.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script from the repo root without pip-installing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ds2ps3edit.core.save import SaveHandle, _reconcile_souls_memory  # noqa: E402
from ds2ps3edit.core.stats import Stats  # noqa: E402


def _baseline_stats(**overrides) -> Stats:
    defaults = dict(
        VGR=50, END=40, VIT=20, ATN=25,
        STR=47, DEX=27, INT=18, FTH=18, ADP=34,
        Level=226, Souls=3000, SoulsMemory=6689040,
    )
    defaults.update(overrides)
    return Stats(**defaults)


def test_savehandle_public_surface_exists():
    """The three methods called by the GUI must exist on the class itself.

    Regression guard for a refactor that once moved apply_item_qty and commit
    into module-level helper's scope, silently breaking the GUI.
    """
    for name in ("open", "apply_stats", "apply_item_qty", "commit"):
        attr = getattr(SaveHandle, name, None)
        assert callable(attr), f"SaveHandle.{name} missing or not callable"


def test_souls_memory_tracks_wallet_increase():
    cur = _baseline_stats(Souls=3000, SoulsMemory=6689040)
    req = _baseline_stats(Souls=30000, SoulsMemory=999)  # user-supplied memory ignored
    out = _reconcile_souls_memory(cur, req)
    assert out.Souls == 30000
    assert out.SoulsMemory == 6689040 + (30000 - 3000)


def test_souls_memory_unchanged_on_wallet_decrease():
    cur = _baseline_stats(Souls=30000, SoulsMemory=6716040)
    req = _baseline_stats(Souls=1000)
    out = _reconcile_souls_memory(cur, req)
    assert out.Souls == 1000
    assert out.SoulsMemory == 6716040


def test_souls_memory_never_below_wallet():
    cur = _baseline_stats(Souls=0, SoulsMemory=10)
    req = _baseline_stats(Souls=1_000_000)
    out = _reconcile_souls_memory(cur, req)
    assert out.SoulsMemory >= out.Souls


if __name__ == "__main__":
    # Allow running without pytest — useful before the first `pip install pytest`.
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all smoke tests passed")

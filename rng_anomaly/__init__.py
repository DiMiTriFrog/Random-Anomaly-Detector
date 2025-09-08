"""
rng_anomaly package

Organizes the anomaly detector into modules:
- utils: statistical utilities and helpers
- sources: bit streams (device and synthetic)
- tests_online: RCT, APT, SPRT, and online Z
- worker: per-process processing loop
- tui: curses UI and "pretty" output
- cli: orchestration and main CLI
"""

__all__ = [
    "utils",
    "sources",
    "tests_online",
    "worker",
    "tui",
    "cli",
]



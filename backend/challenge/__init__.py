"""
Challenge Mode — a 15-level single-player game built on top of the existing
QKD simulation. Each level is a Mission with randomized parameters drawn from
a difficulty band; the user either plays Detective (guess whether Eve is
present + which attack) or Engineer (configure the QKD link to meet a
constrained objective).

Module map:
    mission_catalog.py — the 15 hardcoded Mission templates
    instantiator.py    — rolls concrete parameters from a template's ranges
    grader.py          — Detective & Engineer scoring logic
    persistence.py     — CRUD over MissionAttempt + UserProgress

This package never duplicates simulation logic — it composes the existing
quantum_logic / classical_processing pipeline by feeding it instantiated
parameters and interpreting the resulting metrics.
"""

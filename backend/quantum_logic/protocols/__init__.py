"""
Multi-protocol QKD support.

This package exposes BB84, B92, SARG04, and E91 protocol implementations
behind a single ``get_protocol(name)`` factory. Each protocol module is
responsible for: random state preparation (Alice + Bob choices), circuit
construction, and the protocol-specific sifting step.

The websocket route dispatches to the appropriate module based on the
``protocol`` config value, while the rest of the post-processing
pipeline (QBER, error correction, privacy amplification) is shared.
"""

from . import bb84, b92, sarg04, e91

_REGISTRY = {
    "bb84": bb84,
    "b92": b92,
    "sarg04": sarg04,
    "e91": e91,
}

SUPPORTED_PROTOCOLS = tuple(_REGISTRY.keys())


def get_protocol(name: str):
    """Return the protocol module for ``name``; falls back to BB84."""
    return _REGISTRY.get(name.lower(), bb84)

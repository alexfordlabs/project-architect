"""Crockford-base32 monotonic ULIDs — stdlib-only.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Reference: https://github.com/ulid/spec
"""

from __future__ import annotations

import os
import threading
import time

# Crockford base-32 alphabet (excludes I, L, O, U to avoid ambiguity).
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_LOOKUP = {c: i for i, c in enumerate(_ALPHABET)}

_lock = threading.Lock()
_last_ms = 0
_last_randomness = 0


def _encode(num: int, length: int) -> str:
    chars: list[str] = []
    for _ in range(length):
        chars.append(_ALPHABET[num & 0x1F])
        num >>= 5
    return "".join(reversed(chars))


def new_ulid(timestamp_ms: int | None = None) -> str:
    """Produce a 26-char Crockford-base32 ULID. Monotonic within the same ms."""
    global _last_ms, _last_randomness
    with _lock:
        ms = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
        if ms == _last_ms:
            _last_randomness += 1
            randomness = _last_randomness
        else:
            _last_ms = ms
            randomness = int.from_bytes(os.urandom(10), "big")
            _last_randomness = randomness
        time_part = _encode(ms, 10)
        random_part = _encode(randomness & ((1 << 80) - 1), 16)
        return time_part + random_part


def ulid_to_ms(u: str) -> int:
    """Recover the millisecond timestamp from a ULID."""
    if len(u) != 26:
        raise ValueError(f"ULID must be 26 chars; got {len(u)}")
    ms = 0
    for c in u[:10]:
        ms = (ms << 5) | _LOOKUP[c.upper()]
    return ms

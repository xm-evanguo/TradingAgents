"""
Session-level in-memory cache for API responses.

Eliminates redundant API calls when analysing multiple tickers in the
same process.  Ticker-independent data (global news, Polymarket macro
queries) is naturally deduplicated because cache keys are derived from
the actual call arguments.

Thread-safe via ``threading.Lock``.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class SessionCache:
    """Process-level singleton cache with per-entry TTL."""

    _instance: SessionCache | None = None
    _lock = threading.Lock()

    # ----- singleton accessor ------------------------------------------------

    @classmethod
    def get_instance(cls) -> SessionCache:
        """Return (or create) the process-wide cache instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # double-checked locking
                    cls._instance = cls()
        return cls._instance

    # ----- lifecycle ---------------------------------------------------------

    def __init__(self) -> None:
        self._store: dict[tuple, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._hits = 0
        self._misses = 0
        self._entry_lock = threading.Lock()

    # ----- public API --------------------------------------------------------

    def get(self, key: tuple) -> Any | None:
        """Retrieve a cached value, or ``None`` on miss / expiry."""
        with self._entry_lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None

            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                self._misses += 1
                return None

            self._hits += 1
            return value

    def put(self, key: tuple, value: Any, ttl_seconds: int = 3600) -> None:
        """Store a value with *ttl_seconds* time-to-live (default 1 h)."""
        with self._entry_lock:
            self._store[key] = (value, time.monotonic() + ttl_seconds)

    def clear(self) -> None:
        """Drop all cached entries and reset counters."""
        with self._entry_lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, int]:
        """Return hit / miss / size counters."""
        with self._entry_lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._store),
            }

    # ----- helpers -----------------------------------------------------------

    @classmethod
    def reset_instance(cls) -> None:
        """Tear down the singleton (useful in tests)."""
        with cls._lock:
            cls._instance = None

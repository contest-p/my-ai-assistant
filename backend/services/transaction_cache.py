"""Single-process transaction snapshot; synchronous routes share one lock."""

from contextlib import contextmanager
from copy import deepcopy
from threading import RLock
from time import monotonic


class TransactionReadError(Exception):
    def __init__(self, quota: bool, retry_after: int):
        self.quota = quota
        self.retry_after = retry_after
        super().__init__("Transaction data unavailable")


class TransactionCache:
    def __init__(self, ttl=3600, cooldown=60, clock=monotonic):
        self.ttl = ttl
        self.cooldown = cooldown
        self.clock = clock
        self._lock = RLock()
        self._records = None
        self._expires = 0
        self._retry_at = 0
        self._quota = False

    def get(self, loader, is_quota_error):
        # Hold through loading: waiting requests reuse success OR failure cooldown.
        # Writes use the same lock, so a pre-write load cannot repopulate after it.
        with self._lock:
            now = self.clock()
            if self._records is not None and now < self._expires:
                return deepcopy(self._records)
            if now < self._retry_at:
                raise TransactionReadError(self._quota, max(1, int(self._retry_at - now + 0.999)))
            self._records = None
            try:
                records = loader()
            except Exception as exc:
                self._quota = is_quota_error(exc)
                self._retry_at = self.clock() + self.cooldown
                raise TransactionReadError(self._quota, self.cooldown) from exc
            self._records = deepcopy(records)
            self._expires = self.clock() + self.ttl
            self._retry_at = 0
            return deepcopy(self._records)

    @contextmanager
    def mutation(self):
        with self._lock:
            try:
                yield
            finally:
                # Also discard on ambiguous write failure or post-write read failure.
                # Keep error cooldown: writing must not bypass read-quota protection.
                self._records = None
                self._expires = 0

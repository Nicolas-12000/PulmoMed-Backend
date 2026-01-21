"""
Simple in-memory rate limiter for async endpoints.
Nota: Es por-proceso; en despliegue distribuido se debe reemplazar por Redis u otro backend.
"""
import time
import asyncio
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, status

_bucket_lock = asyncio.Lock()
_buckets: Dict[str, Deque[float]] = defaultdict(deque)


async def rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """Aplica rate limiting simple tipo sliding window."""
    now = time.time()
    async with _bucket_lock:
        bucket = _buckets[key]
        # Purga timestamps fuera de ventana
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit excedido, intenta más tarde"
            )
        bucket.append(now)

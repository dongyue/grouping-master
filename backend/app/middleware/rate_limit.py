import time
from fastapi import Request, HTTPException, status


class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, tuple[float, int]] = {}

    def _get_key(self, request: Request) -> str:
        ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown")
        )
        return f"{ip}:{request.url.path}"

    async def __call__(self, request: Request):
        now = time.time()
        key = self._get_key(request)
        window_start, count = self._store.get(key, (0, 0))

        if now - window_start > self.window_seconds:
            window_start = now
            count = 0

        if count >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
            )

        self._store[key] = (window_start, count + 1)

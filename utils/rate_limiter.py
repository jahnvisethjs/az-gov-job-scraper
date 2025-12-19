"""
Rate limiter for Gemini API to respect free tier limits.
15 requests/minute, 1500 requests/day.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
import time


class GeminiRateLimiter:
    """
    Rate limiter for Gemini API free tier.
    
    Limits:
    - 15 requests per minute (RPM)
    - 1,500 requests per day (RPD)
    """
    
    def __init__(self, rpm: int = 15, rpd: int = 1500):
        self.rpm = rpm
        self.rpd = rpd
        self.minute_requests: List[datetime] = []
        self.day_requests: List[datetime] = []
    
    async def wait_if_needed(self):
        """Wait if rate limits would be exceeded."""
        now = datetime.now()
        
        # Clean old requests
        self._clean_old_requests(now)
        
        # Check minute limit
        if len(self.minute_requests) >= self.rpm:
            oldest = self.minute_requests[0]
            sleep_time = 60 - (now - oldest).seconds
            if sleep_time > 0:
                print(f"⏳ Rate limit: waiting {sleep_time}s...")
                await asyncio.sleep(sleep_time)
                self._clean_old_requests(datetime.now())
        
        # Check day limit
        if len(self.day_requests) >= self.rpd:
            raise Exception("Daily rate limit reached (1,500 requests). Try again tomorrow.")
        
        # Record this request
        self.minute_requests.append(now)
        self.day_requests.append(now)
    
    def _clean_old_requests(self, now: datetime):
        """Remove requests older than time windows."""
        # Remove requests older than 1 minute
        minute_ago = now - timedelta(minutes=1)
        self.minute_requests = [
            req for req in self.minute_requests
            if req > minute_ago
        ]
        
        # Remove requests older than 1 day
        day_ago = now - timedelta(days=1)
        self.day_requests = [
            req for req in self.day_requests
            if req > day_ago
        ]
    
    def get_stats(self) -> dict:
        """Get current usage statistics."""
        now = datetime.now()
        self._clean_old_requests(now)
        
        return {
            "requests_last_minute": len(self.minute_requests),
            "requests_today": len(self.day_requests),
            "rpm_limit": self.rpm,
            "rpd_limit": self.rpd,
            "rpm_remaining": self.rpm - len(self.minute_requests),
            "rpd_remaining": self.rpd - len(self.day_requests)
        }


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> GeminiRateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = GeminiRateLimiter()
    return _rate_limiter

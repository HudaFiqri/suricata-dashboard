"""
Rate Limiter - Control notification sending rate to avoid API limits
"""
import time
from collections import deque
from threading import Lock


class RateLimiter:
    """Thread-safe rate limiter for notification sending"""

    def __init__(self):
        self.limiters = {}
        self.lock = Lock()

    def can_send(self, integration_name: str, max_messages: int, interval: int) -> bool:
        """
        Check if we can send a message based on rate limits

        Args:
            integration_name: Name of the integration (telegram/discord)
            max_messages: Maximum messages allowed in the interval
            interval: Time interval in seconds

        Returns:
            True if message can be sent, False if rate limited
        """
        with self.lock:
            current_time = time.time()

            # Initialize limiter for this integration if not exists
            if integration_name not in self.limiters:
                self.limiters[integration_name] = deque()

            limiter = self.limiters[integration_name]

            # Remove timestamps outside the interval window
            while limiter and limiter[0] < current_time - interval:
                limiter.popleft()

            # Check if we've exceeded the limit
            if len(limiter) >= max_messages:
                return False

            # Add current timestamp
            limiter.append(current_time)
            return True

    def get_wait_time(self, integration_name: str, max_messages: int, interval: int) -> float:
        """
        Get how long to wait before next message can be sent

        Args:
            integration_name: Name of the integration
            max_messages: Maximum messages allowed in the interval
            interval: Time interval in seconds

        Returns:
            Wait time in seconds (0 if can send immediately)
        """
        with self.lock:
            current_time = time.time()

            if integration_name not in self.limiters:
                return 0.0

            limiter = self.limiters[integration_name]

            # Remove old timestamps
            while limiter and limiter[0] < current_time - interval:
                limiter.popleft()

            # If not at limit, can send immediately
            if len(limiter) < max_messages:
                return 0.0

            # Calculate wait time until oldest message expires
            oldest = limiter[0]
            wait_time = (oldest + interval) - current_time
            return max(0.0, wait_time)

    def reset(self, integration_name: str = None):
        """
        Reset rate limiter for an integration or all integrations

        Args:
            integration_name: Integration to reset, or None to reset all
        """
        with self.lock:
            if integration_name:
                if integration_name in self.limiters:
                    self.limiters[integration_name].clear()
            else:
                self.limiters.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()

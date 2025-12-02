"""
Mempool data collector using mempool.space REST API.
"""

from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import httpx
import pandas as pd
import polars as pl
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from gapless_network_data.exceptions import MempoolHTTPException, MempoolRateLimitException


class MempoolCollector:
    """
    Collector for Bitcoin mempool pressure data from mempool.space.

    Attributes:
        base_url: mempool.space API base URL
        output_dir: Directory for Parquet output (optional)
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        base_url: str = "https://mempool.space/api",
        output_dir: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize mempool collector.

        Args:
            base_url: API base URL (default: https://mempool.space/api)
            output_dir: Optional directory for Parquet output
            timeout: HTTP request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir) if output_dir else None
        self.timeout = timeout

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_snapshot(self) -> dict[str, float | int | str]:
        """
        Collect single mempool snapshot with retry logic.

        Retries up to 3 times on HTTP errors with exponential backoff (1s, 2s, 4s).
        Rate limit errors (429) fail immediately without retry.

        Returns:
            Dictionary with mempool state metrics

        Raises:
            MempoolHTTPException: If API requests fail after retries
            MempoolRateLimitException: If rate limit exceeded (no retry)
        """
        # Configure retry strategy
        retryer = Retrying(
            retry=retry_if_exception_type(MempoolHTTPException),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            reraise=True,
        )

        for attempt in retryer:
            with attempt:
                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        # Fetch mempool state
                        endpoint_mempool = "/mempool"
                        try:
                            mempool_resp = client.get(f"{self.base_url}{endpoint_mempool}")
                            mempool_resp.raise_for_status()
                            mempool = mempool_resp.json()
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                                retry_after = e.response.headers.get("Retry-After")
                                raise MempoolRateLimitException(
                                    endpoint=endpoint_mempool,
                                    retry_after=int(retry_after) if retry_after else None,
                                )
                            raise MempoolHTTPException(
                                message=f"HTTP request failed: {e}",
                                endpoint=endpoint_mempool,
                                http_status=e.response.status_code,
                                retry_count=attempt.retry_state.attempt_number - 1,
                            )

                        # Fetch recommended fees
                        endpoint_fees = "/v1/fees/recommended"
                        try:
                            fees_resp = client.get(f"{self.base_url}{endpoint_fees}")
                            fees_resp.raise_for_status()
                            fees = fees_resp.json()
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                                retry_after = e.response.headers.get("Retry-After")
                                raise MempoolRateLimitException(
                                    endpoint=endpoint_fees,
                                    retry_after=int(retry_after) if retry_after else None,
                                )
                            raise MempoolHTTPException(
                                message=f"HTTP request failed: {e}",
                                endpoint=endpoint_fees,
                                http_status=e.response.status_code,
                                retry_count=attempt.retry_state.attempt_number - 1,
                            )

                        # Combine into snapshot
                        snapshot = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "unconfirmed_count": mempool.get("count", 0),
                            "vsize_mb": mempool.get("vsize", 0) / 1_000_000,
                            "total_fee_btc": mempool.get("total_fee", 0) / 100_000_000,
                            "fastest_fee": fees.get("fastestFee", 0),
                            "half_hour_fee": fees.get("halfHourFee", 0),
                            "hour_fee": fees.get("hourFee", 0),
                            "economy_fee": fees.get("economyFee", 0),
                            "minimum_fee": fees.get("minimumFee", 0),
                        }

                        return snapshot

                except httpx.RequestError as e:
                    # Network errors (connection timeout, DNS, etc.)
                    raise MempoolHTTPException(
                        message=f"Network request failed: {e}",
                        endpoint=str(e.request.url.path) if e.request else "unknown",
                        http_status=None,
                        retry_count=attempt.retry_state.attempt_number - 1,
                    )

        # This line should never be reached due to reraise=True
        raise RuntimeError("Retry loop exited unexpectedly")

    def collect_range(
        self,
        start: datetime,
        end: datetime,
        interval: int = 60,
    ) -> pd.DataFrame:
        """
        Collect mempool snapshots for a time range (forward-collection only).

        IMPORTANT: This method only supports forward collection (real-time).
        Historical data collection is not supported as mempool.space does not
        provide historical snapshot APIs. Use this for collecting data from
        current time forward.

        Args:
            start: Start timestamp (UTC) - must be within 5 minutes of current time
            end: End timestamp (UTC) - must be in the future
            interval: Collection interval in seconds (default: 60)

        Returns:
            DataFrame with snapshots indexed by timestamp

        Raises:
            ValueError: If start >= end, interval <= 0, or start is too far in past
            MempoolHTTPException: If API requests fail
            MempoolRateLimitException: If rate limit exceeded

        Example:
            >>> from datetime import datetime, timedelta, timezone
            >>> collector = MempoolCollector()
            >>> now = datetime.now(timezone.utc)
            >>> # Collect next 5 minutes of data
            >>> df = collector.collect_range(
            ...     start=now,
            ...     end=now + timedelta(minutes=5),
            ...     interval=60
            ... )
        """
        now = datetime.now(timezone.utc)

        if start >= end:
            raise ValueError(f"Start time {start} must be before end time {end}")
        if interval <= 0:
            raise ValueError(f"Interval must be positive, got {interval}")

        # Enforce forward-collection only: start must be recent
        max_past_delta = timedelta(minutes=5)
        if start < now - max_past_delta:
            raise ValueError(
                f"Cannot collect historical data. Start time {start.isoformat()} "
                f"is more than 5 minutes in the past (current time: {now.isoformat()}). "
                f"This tool only supports forward collection from current time. "
                f"For historical data, use a blockchain archive or run this tool "
                f"continuously as a daemon."
            )

        # Generate timestamp range
        timestamps = []
        current = start
        while current <= end:
            timestamps.append(current)
            current += timedelta(seconds=interval)

        # Collect snapshots in real-time
        snapshots = []
        for ts in timestamps:
            # Wait until target timestamp if in future
            now = datetime.now(timezone.utc)
            if ts > now:
                wait_seconds = (ts - now).total_seconds()
                if wait_seconds > 0:
                    import time

                    time.sleep(wait_seconds)

            # Collect live snapshot
            snapshot = self.collect_snapshot()
            snapshots.append(snapshot)

        # Convert to Polars DataFrame
        df_pl = pl.DataFrame(snapshots)

        # Convert timestamp to datetime
        df_pl = df_pl.with_columns(
            pl.col("timestamp").str.to_datetime("%Y-%m-%dT%H:%M:%S%z")
        )

        # Save to Parquet if output_dir specified
        if self.output_dir:
            output_path = self._generate_output_path(start)
            df_pl.write_parquet(output_path, compression="snappy")

        # Convert to pandas with DatetimeIndex
        df = df_pl.to_pandas()
        df = df.set_index("timestamp")

        return df

    def _generate_output_path(self, timestamp: datetime) -> Path:
        """
        Generate output path for Parquet file.

        Args:
            timestamp: Reference timestamp for filename

        Returns:
            Path object for output file
        """
        filename = f"mempool_{timestamp.strftime('%Y%m%d_%H')}.parquet"
        return self.output_dir / filename  # type: ignore[return-value]

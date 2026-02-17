"""Candlestick sync service for background data synchronization."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

# Import with fallback for both relative and absolute imports
try:
    from ..models.trading_models import MarketTypeEnum, IntervalEnum, CandlestickData
    from ..utils.binance_client import BinanceClient
    from ..utils.exceptions import BinanceAPIError, SyncError
    from .database import db
except ImportError:
    from models.trading_models import MarketTypeEnum, IntervalEnum, CandlestickData
    from utils.binance_client import BinanceClient
    from utils.exceptions import BinanceAPIError, SyncError
    from services.database import db

logger = logging.getLogger(__name__)


class CandlestickSyncService:
    """Background service to sync candlestick data from Binance every 60 seconds."""

    SYNC_INTERVAL = 60  # seconds
    RETRY_DELAY = 10  # seconds
    MAX_RETRIES = 3

    def __init__(self):
        self.client: Optional[BinanceClient] = None
        self.is_running = False
        self.last_sync: Optional[datetime] = None
        self.next_sync: Optional[datetime] = None
        self.symbols: List[str] = []
        self.intervals: List[str] = []
        self.market_types: List[str] = []
        self._sync_task: Optional[asyncio.Task] = None

    async def _get_client(self) -> BinanceClient:
        """Get or create Binance client."""
        if not self.client:
            self.client = BinanceClient()
        return self.client

    def _load_config(self):
        """Load configuration from environment variables."""
        # Load symbols
        symbols_env = os.getenv("TRADING_SYMBOLS", "BTCUSDT")
        self.symbols = [s.strip().upper() for s in symbols_env.split(",") if s.strip()]

        # Load intervals (default: 1m, 15m, 1h, 4h, 1d)
        intervals_env = os.getenv("TRADING_INTERVALS", "1m,15m,1h,4h,1d")
        self.intervals = [i.strip() for i in intervals_env.split(",") if i.strip()]

        # Load market types (default: spot, usd_m)
        market_types_env = os.getenv("TRADING_MARKET_TYPES", "spot,usd_m")
        self.market_types = [
            m.strip().lower() for m in market_types_env.split(",") if m.strip()
        ]

        logger.info(
            f"Candlestick sync config loaded: {len(self.symbols)} symbols, "
            f"{len(self.intervals)} intervals, {len(self.market_types)} market types"
        )

    async def start_sync_loop(self):
        """Start the background sync loop (runs indefinitely)."""
        if self.is_running:
            logger.warning("Candlestick sync is already running")
            return

        self._load_config()
        self.is_running = True

        logger.info("Starting candlestick sync service...")

        try:
            while self.is_running:
                self.next_sync = datetime.now() + timedelta(seconds=self.SYNC_INTERVAL)

                try:
                    await self._perform_full_sync()
                    self.last_sync = datetime.now()
                except Exception as e:
                    logger.error(f"Full sync cycle failed: {e}")

                # Wait until next sync time
                wait_seconds = (self.next_sync - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

        except asyncio.CancelledError:
            logger.info("Candlestick sync loop cancelled")
            self.is_running = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error in sync loop: {e}")
            self.is_running = False
            raise

    async def _perform_full_sync(self):
        """Perform sync for all configured symbols, intervals, and market types."""
        for market_type in self.market_types:
            for symbol in self.symbols:
                for interval in self.intervals:
                    if not self.is_running:
                        return

                    success = await self._sync_with_retry(
                        symbol=symbol, market_type=market_type, interval=interval
                    )

                    if not success:
                        logger.error(
                            f"Failed to sync {symbol} {interval} for {market_type} "
                            f"after {self.MAX_RETRIES} retries"
                        )

    async def _sync_with_retry(
        self, symbol: str, market_type: str, interval: str
    ) -> bool:
        """Sync a single symbol/interval with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                await self.sync_symbol_interval(symbol, market_type, interval)
                return True
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    return False

        return False

    async def sync_symbol_interval(
        self, symbol: str, market_type: str, interval: str, limit: int = 100
    ):
        """Fetch and store candlesticks for a single symbol/interval."""
        try:
            client = await self._get_client()

            # Fetch klines from Binance
            klines = await client.get_klines(
                symbol=symbol, market_type=market_type, interval=interval, limit=limit
            )

            if not klines:
                return

            # Transform and store each kline
            for kline in klines:
                candlestick = self._transform_kline(
                    kline=kline,
                    symbol=symbol,
                    market_type=market_type,
                    interval=interval,
                )

                await self._upsert_candlestick(candlestick)

        except BinanceAPIError as e:
            raise SyncError(f"Binance API error: {e}", symbol=symbol, interval=interval)
        except Exception as e:
            raise SyncError(f"Unexpected error: {e}", symbol=symbol, interval=interval)

    def _transform_kline(
        self, kline: List, symbol: str, market_type: str, interval: str
    ) -> CandlestickData:
        """Transform Binance kline array to CandlestickData model."""
        # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
        return CandlestickData(
            symbol=symbol.upper(),
            market_type=market_type.lower(),
            interval=interval,
            open_time=datetime.fromtimestamp(kline[0] / 1000),
            open_price=float(kline[1]),
            high_price=float(kline[2]),
            low_price=float(kline[3]),
            close_price=float(kline[4]),
            volume=float(kline[5]),
            close_time=datetime.fromtimestamp(kline[6] / 1000),
            quote_volume=float(kline[7]),
            trades=int(kline[8]),
            taker_buy_base_volume=float(kline[9]),
            taker_buy_quote_volume=float(kline[10]),
            updated_at=datetime.now(),
        )

    async def _upsert_candlestick(self, candlestick: CandlestickData):
        """Insert or update a single candlestick in the database."""
        query = """
            INSERT INTO candlestick_cache (
                symbol, market_type, interval, open_time, open_price, high_price,
                low_price, close_price, volume, close_time, quote_volume, trades,
                taker_buy_base_volume, taker_buy_quote_volume, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (symbol, market_type, interval, open_time) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                close_time = EXCLUDED.close_time,
                quote_volume = EXCLUDED.quote_volume,
                trades = EXCLUDED.trades,
                taker_buy_base_volume = EXCLUDED.taker_buy_base_volume,
                taker_buy_quote_volume = EXCLUDED.taker_buy_quote_volume,
                updated_at = EXCLUDED.updated_at
        """

        await db.pool.execute(
            query,
            candlestick.symbol,
            candlestick.market_type,
            candlestick.interval,
            candlestick.open_time,
            candlestick.open_price,
            candlestick.high_price,
            candlestick.low_price,
            candlestick.close_price,
            candlestick.volume,
            candlestick.close_time,
            candlestick.quote_volume,
            candlestick.trades,
            candlestick.taker_buy_base_volume,
            candlestick.taker_buy_quote_volume,
            candlestick.updated_at,
        )

    async def get_cached_candles(
        self,
        symbol: str,
        market_type: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CandlestickData]:
        """Query cached candlesticks from database."""
        try:
            conditions = ["symbol = $1", "market_type = $2", "interval = $3"]
            params = [symbol.upper(), market_type.lower(), interval]
            param_idx = 4

            if start_time:
                conditions.append(f"open_time >= ${param_idx}")
                params.append(start_time)
                param_idx += 1

            if end_time:
                conditions.append(f"open_time <= ${param_idx}")
                params.append(end_time)
                param_idx += 1

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT * FROM candlestick_cache
                WHERE {where_clause}
                ORDER BY open_time DESC
                LIMIT ${param_idx}
            """
            params.append(limit)

            rows = await db.pool.fetch(query, *params)

            candles = []
            for row in rows:
                candles.append(
                    CandlestickData(
                        symbol=row["symbol"],
                        market_type=row["market_type"],
                        interval=row["interval"],
                        open_time=row["open_time"],
                        open_price=float(row["open_price"]),
                        high_price=float(row["high_price"]),
                        low_price=float(row["low_price"]),
                        close_price=float(row["close_price"]),
                        volume=float(row["volume"]),
                        close_time=row["close_time"],
                        quote_volume=float(row["quote_volume"]),
                        trades=row["trades"],
                        taker_buy_base_volume=float(row["taker_buy_base_volume"]),
                        taker_buy_quote_volume=float(row["taker_buy_quote_volume"]),
                        updated_at=row["updated_at"],
                    )
                )

            return candles

        except Exception as e:
            logger.error(f"Error fetching cached candles: {e}")
            raise

    async def trigger_sync_now(
        self,
        symbols: Optional[List[str]] = None,
        market_types: Optional[List[str]] = None,
        intervals: Optional[List[str]] = None,
    ):
        """Trigger an immediate sync for specified symbols (or all if not specified)."""
        symbols = symbols or self.symbols
        market_types = market_types or self.market_types
        intervals = intervals or self.intervals

        logger.info(f"Triggering immediate sync for {len(symbols)} symbols...")

        for market_type in market_types:
            for symbol in symbols:
                for interval in intervals:
                    success = await self._sync_with_retry(symbol, market_type, interval)
                    if not success:
                        logger.error(
                            f"Immediate sync failed for {symbol} {interval} {market_type}"
                        )

        self.last_sync = datetime.now()

    def get_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        return {
            "is_running": self.is_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "next_sync": self.next_sync.isoformat() if self.next_sync else None,
            "symbols": self.symbols,
            "intervals": self.intervals,
            "market_types": self.market_types,
            "sync_interval_seconds": self.SYNC_INTERVAL,
            "retry_delay_seconds": self.RETRY_DELAY,
            "max_retries": self.MAX_RETRIES,
        }

    async def stop(self):
        """Stop the sync loop gracefully."""
        if self.is_running:
            logger.info("Stopping candlestick sync service...")
            self.is_running = False

            if self._sync_task and not self._sync_task.done():
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass

            if self.client:
                await self.client.close()

            logger.info("Candlestick sync service stopped")


# Global service instance
candlestick_sync = CandlestickSyncService()

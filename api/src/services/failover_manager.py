import logging
from collections import deque
from datetime import datetime
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

RSS_SOURCES = {
    "coindesk": {
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"
    },
    "cointelegraph": {"url": "https://cointelegraph.com/rss"},
    "cryptopotato": {"url": "https://cryptopotato.com/feed/"},
    "cryptoslate": {"url": "https://cryptoslate.com/feed/"},
    "thedefiant": {"url": "https://thedefiant.io/feed/"},
    "bitcoinist": {"url": "https://bitcoinist.com/feed/"},
    "newsbtc": {"url": "https://www.newsbtc.com/feed/"},
    "cryptonews": {"url": "https://cryptonews.com/news/feed/"},
    "smartliquidity": {"url": "https://smartliquidity.info/feed/"},
    "benjaminion": {"url": "https://benjaminion.xyz/newineth2/rss_feed.xml"},
    "yahoo_finance": {"url": "https://finance.yahoo.com/news/rssindex"},
    "cnbc": {"url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"},
    "time_nextadvisor": {"url": "https://time.com/nextadvisor/feed/"},
}


class FailoverManager:
    MAX_ACTIVE = 4
    FAILURE_THRESHOLD = 3

    def __init__(self):
        self.primaries = ["coindesk", "cointelegraph", "cryptopotato", "cryptoslate"]
        self.backup_pool: deque = deque(
            [
                "thedefiant",
                "bitcoinist",
                "newsbtc",
                "cryptonews",
                "smartliquidity",
                "benjaminion",
                "yahoo_finance",
                "cnbc",
                "time_nextadvisor",
            ]
        )
        self.active_sources: Set = set(self.primaries)
        self.consecutive_failures: Dict[str, int] = {s: 0 for s in RSS_SOURCES}
        self.failed_primaries: Dict[str, datetime] = {}
        self.active_backups: Dict[str, str] = {}

    def record_failure(self, source: str) -> None:
        if source not in self.primaries:
            return

        self.consecutive_failures[source] += 1

        if (
            self.consecutive_failures[source] >= self.FAILURE_THRESHOLD
            and source in self.active_sources
        ):
            self._activate_backup(source)

    def record_success(self, source: str) -> None:
        was_failing = self.consecutive_failures.get(source, 0) >= self.FAILURE_THRESHOLD
        self.consecutive_failures[source] = 0

        if was_failing and source in self.primaries and source in self.failed_primaries:
            self._restore_primary(source)

    def _activate_backup(self, failed_primary: str) -> None:
        if not self.backup_pool or failed_primary not in self.active_sources:
            logger.warning(f"No backups available to replace {failed_primary}")
            return

        backup = self.backup_pool.popleft()

        self.active_sources.discard(failed_primary)
        self.active_sources.add(backup)

        self.failed_primaries[failed_primary] = datetime.utcnow()
        self.active_backups[backup] = failed_primary

        logger.warning(
            f"FAILOVER: {failed_primary} -> {backup} | Active sources: {sorted(self.active_sources)}"
        )

    def _restore_primary(self, recovered_primary: str) -> None:
        backup_to_remove = None
        for backup, primary in self.active_backups.items():
            if primary == recovered_primary:
                backup_to_remove = backup
                break

        if not backup_to_remove:
            return

        self.active_sources.discard(backup_to_remove)
        self.active_sources.add(recovered_primary)

        self.backup_pool.append(backup_to_remove)
        del self.active_backups[backup_to_remove]
        del self.failed_primaries[recovered_primary]

        logger.info(
            f"RESTORED: {recovered_primary} <- {backup_to_remove} | Active sources: {sorted(self.active_sources)}"
        )

    def get_active_sources(self) -> List[str]:
        return sorted(list(self.active_sources))

    def get_status(self) -> dict:
        return {
            "active_count": len(self.active_sources),
            "active_sources": self.get_active_sources(),
            "primaries_active": len(
                self.active_sources.intersection(set(self.primaries))
            ),
            "backups_active": len(self.active_backups),
            "failed_primaries": list(self.failed_primaries.keys()),
            "backups_available": len(self.backup_pool),
            "backup_queue": list(self.backup_pool),
            "failure_counts": {
                k: v for k, v in self.consecutive_failures.items() if v > 0
            },
        }

    def get_source_health(self) -> dict:
        return {
            source: {
                "status": "healthy"
                if self.consecutive_failures[source] < self.FAILURE_THRESHOLD
                else "failed",
                "failures": self.consecutive_failures[source],
                "type": "primary" if source in self.primaries else "backup",
            }
            for source in RSS_SOURCES
        }

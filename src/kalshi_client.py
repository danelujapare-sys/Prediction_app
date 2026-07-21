"""
Kalshi API Client for 15-Minute Crypto Prediction Markets.
Handles fetching market settlement candle history across assets with cursor pagination.
"""

import time
import datetime
import requests
from typing import Dict, List, Optional, Tuple, Any

# Primary API endpoints for public market data
KALSHI_API_URLS = [
    "https://api.elections.kalshi.com/trade-api/v2",
    "https://external-api.kalshi.com/trade-api/v2",
]

# Asset symbol to series ticker mapping for 15-minute binary markets
ASSET_SERIES_MAP = {
    "BTC": "KXBTC15M",
    "ETH": "KXETH15M",
    "XRP": "KXXRP15M",
    "SOL": "KXSOL15M",
    "DOGE": "KXDOGE15M",
    "HYPE": "KXHYPE15M",
    "BNB": "KXBNB15M",
}

SERIES_ASSET_MAP = {v: k for k, v in ASSET_SERIES_MAP.items()}


class KalshiClient:
    """API Client for Kalshi 15-Minute Crypto Prediction Markets."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 15):
        self.base_urls = [base_url] if base_url else KALSHI_API_URLS
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "KalshiCryptoStreakAnalyzer/1.0",
        })

    def _request_get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Executes GET request across base URLs with retry."""
        for base_url in self.base_urls:
            url = f"{base_url}{endpoint}"
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException:
                continue
        return None

    def fetch_markets_for_series(
        self,
        series_ticker: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        max_records: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Fetches finalized settlement outcomes for a given series ticker within date boundaries.
        
        Args:
            series_ticker: Ticker of series (e.g. 'KXBTC15M')
            start_date: Datetime lower bound (default: 90 days ago)
            end_date: Datetime upper bound (default: current time)
            max_records: Safety limit on total markets fetched

        Returns:
            List of parsed market dicts with keys:
            ['ticker', 'asset', 'close_time', 'close_timestamp', 'result', 'outcome_marker']
        """
        if not end_date:
            end_date = datetime.datetime.now(datetime.timezone.utc)
        if not start_date:
            start_date = end_date - datetime.timedelta(days=90)

        min_ts = int(start_date.timestamp())
        max_ts = int(end_date.timestamp())

        asset_symbol = SERIES_ASSET_MAP.get(series_ticker, series_ticker)
        all_markets = []
        cursor = None

        while len(all_markets) < max_records:
            params = {
                "series_ticker": series_ticker,
                "min_close_ts": min_ts,
                "max_close_ts": max_ts,
                "limit": 1000,
            }
            if cursor:
                params["cursor"] = cursor

            data = self._request_get("/markets", params)
            if not data or "markets" not in data:
                break

            markets_page = data["markets"]
            if not markets_page:
                break

            for m in markets_page:
                result_str = m.get("result", "").lower()
                status = m.get("status", "").lower()

                # Filter finalized markets or markets with explicit outcome
                if status in ["finalized", "settled", "closed"] or result_str in ["yes", "no"]:
                    if result_str not in ["yes", "no"]:
                        continue

                    # Outcome marker: +1 for Yes (Up), -1 for No (Down)
                    outcome_marker = 1 if result_str == "yes" else -1
                    close_time_str = m.get("close_time") or m.get("expiration_time", "")

                    # Parse close timestamp
                    try:
                        dt = datetime.datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
                        close_ts = int(dt.timestamp())
                    except Exception:
                        close_ts = 0

                    all_markets.append({
                        "ticker": m.get("ticker"),
                        "series_ticker": series_ticker,
                        "asset": asset_symbol,
                        "close_time": close_time_str,
                        "close_timestamp": close_ts,
                        "result": result_str,
                        "outcome_marker": outcome_marker,
                        "title": m.get("title", ""),
                    })

            cursor = data.get("cursor")
            if not cursor:
                break

        # Sort chronologically ascending
        all_markets.sort(key=lambda x: x["close_timestamp"])
        return all_markets

    def fetch_all_assets_history(
        self,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches historical outcome data for all 7 target crypto assets.
        
        Returns:
            Dict mapping asset symbol (e.g. 'BTC') to list of market records.
        """
        result_by_asset = {}
        for asset, series_ticker in ASSET_SERIES_MAP.items():
            markets = self.fetch_markets_for_series(series_ticker, start_date, end_date)
            result_by_asset[asset] = markets
        return result_by_asset

    def fetch_latest_market_per_asset(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches recent finalized/closed markets for real-time monitoring across all assets.
        Returns last 20 settled markets per asset to compute active streak context.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        start_24h = now - datetime.timedelta(hours=24)
        
        latest_by_asset = {}
        for asset, series_ticker in ASSET_SERIES_MAP.items():
            markets = self.fetch_markets_for_series(
                series_ticker, start_date=start_24h, end_date=now, max_records=100
            )
            latest_by_asset[asset] = markets[-20:] if len(markets) >= 20 else markets
        return latest_by_asset

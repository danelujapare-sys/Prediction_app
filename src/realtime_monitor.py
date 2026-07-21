"""
Real-time Crypto Streak Monitor for Kalshi 15-Minute Prediction Markets.

Polls 15-minute interval closes (:00, :15, :30, :45), tracks in-memory trend streaks per asset,
and dispatches highlighted colorama console alerts, Webhooks, and Email alerts (to danelujapare@gmail.com) when streak >= 4.
Designed for 24/7 continuous autonomous execution on cloud infrastructure.
"""

import os
import sys
import time
import datetime
import argparse
import requests
from dotenv import load_dotenv
from colorama import init, Fore, Back, Style

# Initialize colorama for Windows PowerShell/CMD compatibility
init(autoreset=True)

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure local src directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kalshi_client import KalshiClient, ASSET_SERIES_MAP
from streak_engine import extract_streaks_from_markers
from email_notifier import EmailNotifier, DEFAULT_RECIPIENT

# Load environment variables from .env if present
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", DEFAULT_RECIPIENT)
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Global Email Notifier instance
email_notifier = EmailNotifier(default_recipient=RECIPIENT_EMAIL)


def send_discord_webhook(asset: str, streak_length: int, direction: str, ticker: str, close_time: str):
    """Sends alert payload to Discord Webhook."""
    if not DISCORD_WEBHOOK_URL or "YOUR_WEBHOOK" in DISCORD_WEBHOOK_URL:
        return

    color_code = 0x2ECC71 if direction == "Up" else 0xE74C3C
    emoji = "🚀" if direction == "Up" else "🔻"

    payload = {
        "embeds": [
            {
                "title": f"{emoji} STREAK ALERT: {asset} hit {streak_length} consecutive {direction} intervals!",
                "description": f"**Kalshi 15-Minute Crypto Prediction Market**\nAsset `{asset}` has reached a trend streak of **{streak_length}** ({direction}).",
                "color": color_code,
                "fields": [
                    {"name": "Asset", "value": asset, "inline": True},
                    {"name": "Streak Length", "value": str(streak_length), "inline": True},
                    {"name": "Direction", "value": direction, "inline": True},
                    {"name": "Latest Ticker", "value": ticker, "inline": True},
                    {"name": "Close Time", "value": close_time, "inline": True},
                ],
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "footer": {"text": "Kalshi Crypto Streak Monitor"},
            }
        ]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if r.status_code in [200, 204]:
            print(Fore.CYAN + f"[Webhook] Successfully posted alert to Discord for {asset}.")
        else:
            print(Fore.YELLOW + f"[Webhook] Discord returned status {r.status_code}.")
    except Exception as e:
        print(Fore.RED + f"[Webhook] Error sending Discord alert: {e}")


def send_telegram_webhook(asset: str, streak_length: int, direction: str, ticker: str, close_time: str):
    """Sends alert payload to Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or "YOUR_BOT" in TELEGRAM_BOT_TOKEN:
        return

    emoji = "🚀" if direction == "Up" else "🔻"
    message = (
        f"{emoji} *KALSHI STREAK ALERT*\n"
        f"*Asset:* `{asset}`\n"
        f"*Streak Length:* `{streak_length}` consecutive intervals\n"
        f"*Direction:* `{direction}`\n"
        f"*Latest Ticker:* `{ticker}`\n"
        f"*Close Time:* `{close_time}`"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            print(Fore.CYAN + f"[Webhook] Successfully posted alert to Telegram for {asset}.")
        else:
            print(Fore.YELLOW + f"[Webhook] Telegram returned status {r.status_code}.")
    except Exception as e:
        print(Fore.RED + f"[Webhook] Error sending Telegram alert: {e}")


def dispatch_alerts(asset: str, streak_length: int, direction: str, ticker: str, close_time: str):
    """Dispatches console alert, Webhook notifications, and Email alerts."""
    banner_color = Back.GREEN + Fore.BLACK if direction == "Up" else Back.RED + Fore.WHITE
    dir_str = "UP (GREEN)" if direction == "Up" else "DOWN (RED)"

    print("\n" + banner_color + Style.BRIGHT + " " * 80)
    print(
        banner_color
        + Style.BRIGHT
        + f" [!!!] HIGH STREAK ALERT: {asset} HAS REACHED {streak_length} CONSECUTIVE {dir_str} INTERVALS! "
    )
    print(banner_color + Style.BRIGHT + " " * 80 + Style.RESET_ALL)
    print(
        Fore.WHITE
        + Style.BRIGHT
        + f"     Asset: {asset} | Ticker: {ticker} | Direction: {direction} | Close: {close_time}"
    )
    print(Fore.YELLOW + f"     Recipient Email: {RECIPIENT_EMAIL}")
    print(Fore.YELLOW + f"     Conditional Reversal Probability P(Reversal | Streak={streak_length}) is significantly elevated.\n")

    # Send Email Alert
    email_notifier.send_streak_alert(
        asset=asset,
        streak_length=streak_length,
        direction=direction,
        ticker=ticker,
        close_time=close_time,
        recipient=RECIPIENT_EMAIL,
    )

    # Send Webhooks
    send_discord_webhook(asset, streak_length, direction, ticker, close_time)
    send_telegram_webhook(asset, streak_length, direction, ticker, close_time)


class RealtimeStreakMonitor:
    """Real-time monitoring engine for Kalshi 15-minute crypto markets."""

    def __init__(self, client: KalshiClient, alert_threshold: int = 4):
        self.client = client
        self.alert_threshold = alert_threshold
        # Tracks last alerted streak state per asset to prevent spamming duplicate alerts for the same interval
        self.alerted_state = {}

    def poll_once(self) -> dict:
        """Executes a single polling iteration across all 7 crypto assets."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        print(Fore.BLUE + Style.BRIGHT + f"[*] [{now_utc.strftime('%H:%M:%S UTC')}] Polling Kalshi 15m crypto markets...")

        recent_markets_by_asset = self.client.fetch_latest_market_per_asset()
        status_summary = {}

        for asset, markets in recent_markets_by_asset.items():
            if not markets:
                status_summary[asset] = {"length": 0, "direction": None, "last_ticker": "N/A"}
                continue

            markers = [m["outcome_marker"] for m in markets if "outcome_marker" in m]
            _, _, active_streak = extract_streaks_from_markers(markers)

            streak_len = active_streak["length"]
            direction = active_streak["direction"]
            last_market = markets[-1]
            last_ticker = last_market.get("ticker", "N/A")
            last_close = last_market.get("close_time", "N/A")

            status_summary[asset] = {
                "length": streak_len,
                "direction": direction,
                "last_ticker": last_ticker,
                "last_close": last_close,
            }

            # Print status row
            dir_color = Fore.GREEN if direction == "Up" else Fore.RED
            status_symbol = "^" if direction == "Up" else "v"
            print(
                f"    -> {asset:<5}: Streak = {dir_color}{streak_len:<2} {status_symbol} ({direction:<4}){Style.RESET_ALL} | Last Closed: {last_ticker}"
            )

            # Alert evaluation
            if streak_len >= self.alert_threshold:
                alert_key = (asset, last_ticker, streak_len)
                if alert_key not in self.alerted_state:
                    self.alerted_state[alert_key] = True
                    dispatch_alerts(asset, streak_len, direction, last_ticker, last_close)

        return status_summary

    def run_continuous(self, poll_interval_seconds: int = 60):
        """Runs continuous 24/7 monitoring loop with automatic error recovery."""
        print(Fore.CYAN + Style.BRIGHT + f"[+] Starting Kalshi 15m Crypto Real-Time Email Monitor.")
        print(Fore.CYAN + f"    Alert Recipient: {RECIPIENT_EMAIL}")
        print(Fore.CYAN + f"    Alert Threshold: streak >= {self.alert_threshold}")
        print(Fore.CYAN + f"    Polling Interval: {poll_interval_seconds}s")
        print(Fore.CYAN + f"    Mode: Autonomous 24/7 Cloud Loop. Press Ctrl+C to stop.\n")

        while True:
            try:
                self.poll_once()
            except Exception as e:
                print(Fore.RED + f"[!] Runtime Exception caught in polling loop: {e}")
                print(Fore.YELLOW + "    Recovering automatically... Retrying in next interval.")
            
            time.sleep(poll_interval_seconds)


def main():
    global RECIPIENT_EMAIL
    parser = argparse.ArgumentParser(description="Kalshi 15-Minute Crypto 24/7 Real-time Streak Email Monitor")
    parser.add_argument("--threshold", type=int, default=4, help="Streak length threshold for alerts (default: 4)")
    parser.add_argument("--interval", type=int, default=POLL_INTERVAL_SECONDS, help="Polling interval in seconds")
    parser.add_argument("--recipient", type=str, default=RECIPIENT_EMAIL, help="Email recipient address")
    parser.add_argument("--single-pass", action="store_true", help="Run a single poll pass and exit (useful for testing)")
    parser.add_argument("--test-email", action="store_true", help="Send a test verification email to recipient and exit")
    args = parser.parse_args()

    if args.recipient:
        RECIPIENT_EMAIL = args.recipient
        email_notifier.default_recipient = args.recipient

    if args.test_email:
        print(Fore.CYAN + f"[*] Sending test email to '{RECIPIENT_EMAIL}'...")
        email_notifier.send_test_email(recipient=RECIPIENT_EMAIL)
        return

    client = KalshiClient()
    monitor = RealtimeStreakMonitor(client, alert_threshold=args.threshold)

    if args.single_pass:
        print(Fore.CYAN + "[*] Running single pass check...")
        monitor.poll_once()
        print(Fore.GREEN + "[+] Single pass complete.")
    else:
        monitor.run_continuous(poll_interval_seconds=args.interval)


if __name__ == "__main__":
    main()

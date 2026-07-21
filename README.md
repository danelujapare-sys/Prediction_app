# Kalshi Crypto Streak Analyzer & Real-time Monitor

A full-featured Python analytics suite and real-time monitoring system for **15-minute crypto prediction markets on Kalshi**. 

Supported Assets: **BTC, ETH, XRP, SOL, DOGE, HYPE, BNB** (Series tickers: `KXBTC15M`, `KXETH15M`, `KXXRP15M`, `KXSOL15M`, `KXDOGE15M`, `KXHYPE15M`, `KXBNB15M`).

---

## 🌟 Overview & Features

1. **Automated Historical Analyzer (`src/historical_analyzer.py`)**:
   - Queries Kalshi API v2 market settlement candle history across all 7 crypto assets.
   - Maps outcomes to binary markers (`+1` Up/Green, `-1` Down/Red).
   - **Streak Statistics Engine**: Computes Mean, Median, Max Outlier, Std Dev, Skewness, Kurtosis per asset and aggregate combined.
   - **Conditional Reversal Probabilities**: Calculates empirical conditional probability $P(\text{Reversal} \mid \text{Streak} = k)$ for $k \in \{1 \dots 8+\}$.
   - Prints a formatted ASCII Markdown table summary to terminal.
   - Exports high-resolution plots to `outputs/`:
     - `streak_histogram.png`: Combined streak distribution histogram.
     - `streak_outliers_boxplot.png`: Tail-risk boxplot / violin plot across assets.
     - `streak_ecdf.png`: Empirical Cumulative Distribution Function plot.

2. **Real-time Monitor (`src/realtime_monitor.py`)**:
   - Polling loop tracking 15-minute interval closes (:00, :15, :30, :45 past the hour).
   - In-memory real-time tracking of consecutive trend lengths.
   - **Alert Trigger**: Highlights console alerts via `colorama` whenever `streak >= 4`.
   - **Webhook Integration**: Configurable HTTP POST dispatch to Discord and Telegram Webhooks.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Create Virtual Environment & Install Dependencies
Open PowerShell or Terminal in `D:\Vibecoding Antigravity`:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 3. Environment Variables Setup (Optional)
Copy `.env.example` to `.env` to configure Webhook notification alerts:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your Discord/Telegram Webhook credentials:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
POLL_INTERVAL_SECONDS=60
```

---

## 📊 Usage Guide

### Module 1: Run Historical Analysis
Run historical analysis over the default past 90 days:

```powershell
.\.venv\Scripts\python src/historical_analyzer.py
```

Run historical analysis for a custom date range:

```powershell
.\.venv\Scripts\python src/historical_analyzer.py --start-date 2026-05-01 --end-date 2026-07-21
```

Generated plots will be saved in `D:\Vibecoding Antigravity\outputs\`:
- `outputs/streak_histogram.png`
- `outputs/streak_outliers_boxplot.png`
- `outputs/streak_ecdf.png`

---

### Module 2: Run Real-Time Monitor
Start real-time 15-minute monitoring loop (alerts when `streak >= 4`):

```powershell
.\.venv\Scripts\python src/realtime_monitor.py
```

Run with custom streak alert threshold (e.g., alert at streak length $\ge 5$):

```powershell
.\.venv\Scripts\python src/realtime_monitor.py --threshold 5
```

Run a single-pass check (useful for automated verification):

```powershell
.\.venv\Scripts\python src/realtime_monitor.py --single-pass
```

---

## 📁 Directory Structure

```
D:\Vibecoding Antigravity\
├── .env.example                # Template for Webhook tokens
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
├── outputs/                    # Output directory for generated plots
│   ├── streak_histogram.png
│   ├── streak_outliers_boxplot.png
│   └── streak_ecdf.png
└── src/
    ├── __init__.py
    ├── kalshi_client.py        # API client for Kalshi 15m crypto markets
    ├── streak_engine.py        # Statistical streak calculation engine
    ├── historical_analyzer.py  # Module 1: Historical data fetch, stats & plots
    └── realtime_monitor.py     # Module 2: Real-time close tracker & alert system
```

"""
Historical Streak Analyzer for Kalshi 15-Minute Crypto Prediction Markets.

Fetches settlement outcome history across 7 assets, computes directional streak statistics,
calculates conditional reversal probabilities, prints formatted ASCII tables, and generates plots.
"""

import os
import sys
import argparse
import datetime
from typing import Optional, Tuple, Dict, List, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure local src directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kalshi_client import KalshiClient, ASSET_SERIES_MAP
from streak_engine import process_all_assets_streaks, compute_statistics, compute_conditional_reversal_probabilities

# Asset color scheme for premium visual aesthetic
ASSET_COLORS = {
    "BTC": "#F7931A",
    "ETH": "#627EEA",
    "XRP": "#3498DB",
    "SOL": "#14F195",
    "DOGE": "#F1C40F",
    "HYPE": "#9B59B6",
    "BNB": "#F3BA2F",
    "Combined": "#E74C3C",
}


def parse_date_arg(date_str: Optional[str]) -> Optional[datetime.datetime]:
    """Parses date string (YYYY-MM-DD or ISO) into UTC datetime."""
    if not date_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError:
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return dt.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            print(f"Warning: Invalid date format '{date_str}'. Using default.")
            return None


def generate_ascii_tables(
    per_asset_analysis: dict, combined_analysis: dict, start_date: datetime.datetime, end_date: datetime.datetime
) -> str:
    """Generates a formatted ASCII Markdown table summarizing streak metrics and reversal probabilities."""
    output = []
    output.append("\n" + "=" * 95)
    output.append(" KALSHI 15-MINUTE CRYPTO STREAK HISTORICAL ANALYSIS REPORT")
    output.append(f" Time Horizon: {start_date.strftime('%Y-%m-%d %H:%M UTC')} to {end_date.strftime('%Y-%m-%d %H:%M UTC')}")
    output.append("=" * 95 + "\n")

    # Table 1: Descriptive Statistics
    output.append("### 1. DIRECTIONAL STREAK STATISTICAL SUMMARY")
    output.append("| Asset    | Markets | Streaks | Mean Length | Median | Max (Outlier) | Std Dev | Skewness | Kurtosis |")
    output.append("|----------|---------|---------|-------------|--------|---------------|---------|----------|----------|")

    for asset, data in per_asset_analysis.items():
        st = data["stats"]
        output.append(
            f"| {asset:<8} | {data['market_count']:<7} | {st['count']:<7} | {st['mean']:<11.3f} | {st['median']:<6.1f} | {st['max']:<13} | {st['std']:<7.3f} | {st['skew']:<8.3f} | {st['kurtosis']:<8.3f} |"
        )

    # Combined row
    c_st = combined_analysis["stats"]
    output.append("|----------|---------|---------|-------------|--------|---------------|---------|----------|----------|")
    output.append(
        f"| COMBINED | {combined_analysis['total_markets']:<7} | {c_st['count']:<7} | {c_st['mean']:<11.3f} | {c_st['median']:<6.1f} | {c_st['max']:<13} | {c_st['std']:<7.3f} | {c_st['skew']:<8.3f} | {c_st['kurtosis']:<8.3f} |"
    )
    output.append("")

    # Table 2: Conditional Reversal Probabilities P(Reversal | Streak = k)
    output.append("### 2. CONDITIONAL REVERSAL PROBABILITIES P(Reversal | Streak = k)")
    headers = ["Asset", "k=1", "k=2", "k=3", "k=4", "k=5", "k=6", "k=7", "k=8+"]
    hdr_line = "| " + " | ".join(f"{h:<8}" for h in headers) + " |"
    sep_line = "|" + "|".join("----------" for _ in headers) + "|"
    output.append(hdr_line)
    output.append(sep_line)

    for asset, data in per_asset_analysis.items():
        probs = data["conditional_probabilities"]
        row = [f"{asset:<8}"]
        for k_key in ["1", "2", "3", "4", "5", "6", "7", "8+"]:
            p_rev = probs.get(k_key, {}).get("p_reversal", 0.0)
            row.append(f"{p_rev*100:<7.1f}%")
        output.append("| " + " | ".join(row) + " |")

    c_probs = combined_analysis["conditional_probabilities"]
    c_row = ["COMBINED"]
    for k_key in ["1", "2", "3", "4", "5", "6", "7", "8+"]:
        p_rev = c_probs.get(k_key, {}).get("p_reversal", 0.0)
        c_row.append(f"{p_rev*100:<7.1f}%")
    output.append(sep_line)
    output.append("| " + " | ".join(c_row) + " |")
    output.append("\n" + "=" * 95)

    return "\n".join(output)


def plot_streak_histogram(per_asset_analysis: dict, all_lengths: list, output_dir: str):
    """Generates & saves combined histogram plot showing streak lengths before reversal."""
    plt.figure(figsize=(12, 6), dpi=300)
    plt.style.use("dark_background")
    ax = plt.gca()
    ax.set_facecolor("#111827")
    plt.gcf().patch.set_facecolor("#0F172A")

    bins = np.arange(0.5, max(all_lengths) + 1.5, 1)

    # Plot histogram for combined dataset
    n, _, patches = plt.hist(
        all_lengths,
        bins=bins,
        color="#3B82F6",
        edgecolor="#1E40AF",
        alpha=0.85,
        rwidth=0.8,
        label="Combined Streaks",
    )

    # Annotate bar counts
    for count, patch in zip(n, patches):
        if count > 0:
            height = patch.get_height()
            plt.text(
                patch.get_x() + patch.get_width() / 2.0,
                height + (max(n) * 0.01),
                f"{int(count)}",
                ha="center",
                va="bottom",
                color="#F8FAFC",
                fontsize=9,
                fontweight="bold",
            )

    plt.title("Kalshi 15m Crypto Prediction Markets: Streak Length Histogram Before Reversal", fontsize=14, fontweight="bold", color="#F8FAFC", pad=15)
    plt.xlabel("Streak Length N (Consecutive 15-Min Intervals in Same Direction)", fontsize=11, color="#E2E8F0")
    plt.ylabel("Frequency (Count of Streaks)", fontsize=11, color="#E2E8F0")
    plt.xticks(np.arange(1, max(all_lengths) + 1, 1), color="#CBD5E1")
    plt.yticks(color="#CBD5E1")
    plt.grid(axis="y", linestyle="--", alpha=0.3, color="#475569")
    plt.legend(facecolor="#1E293B", edgecolor="#334155", labelcolor="#F8FAFC")
    plt.tight_layout()

    file_path = os.path.join(output_dir, "streak_histogram.png")
    plt.savefig(file_path)
    plt.close()
    print(f"Saved plot: {file_path}")


def plot_streak_boxplots(per_asset_analysis: dict, output_dir: str):
    """Generates & saves outlier boxplot / violin plot displaying tail-risk streak lengths across assets."""
    plt.figure(figsize=(12, 6), dpi=300)
    plt.style.use("dark_background")
    ax = plt.gca()
    ax.set_facecolor("#111827")
    plt.gcf().patch.set_facecolor("#0F172A")

    plot_data = []
    assets = []
    for asset, data in per_asset_analysis.items():
        if data["streak_lengths"]:
            for val in data["streak_lengths"]:
                plot_data.append({"Asset": asset, "Streak Length": val})

    df_plot = pd.DataFrame(plot_data)

    # Violin plot overlaid with boxplot for tail risk analysis
    sns.violinplot(
        data=df_plot,
        x="Asset",
        y="Streak Length",
        hue="Asset",
        legend=False,
        palette=ASSET_COLORS,
        inner=None,
        alpha=0.4,
        ax=ax,
    )
    sns.boxplot(
        data=df_plot,
        x="Asset",
        y="Streak Length",
        width=0.2,
        boxprops=dict(facecolor="none", edgecolor="#F8FAFC", linewidth=1.5),
        whiskerprops=dict(color="#CBD5E1", linewidth=1.5),
        capprops=dict(color="#CBD5E1", linewidth=1.5),
        medianprops=dict(color="#EF4444", linewidth=2.0),
        flierprops=dict(marker="o", markerfacecolor="#EF4444", markeredgecolor="#991B1B", markersize=6),
        ax=ax,
    )

    plt.title("Tail Risk & Outlier Analysis: Streak Length Distribution Across Crypto Assets", fontsize=14, fontweight="bold", color="#F8FAFC", pad=15)
    plt.xlabel("Crypto Asset", fontsize=11, color="#E2E8F0")
    plt.ylabel("Streak Length N", fontsize=11, color="#E2E8F0")
    plt.grid(axis="y", linestyle="--", alpha=0.3, color="#475569")
    plt.tight_layout()

    file_path = os.path.join(output_dir, "streak_outliers_boxplot.png")
    plt.savefig(file_path)
    plt.close()
    print(f"Saved plot: {file_path}")


def plot_streak_ecdf(per_asset_analysis: dict, all_lengths: list, output_dir: str):
    """Generates & saves Empirical Cumulative Distribution Function (ECDF) plot."""
    plt.figure(figsize=(12, 6), dpi=300)
    plt.style.use("dark_background")
    ax = plt.gca()
    ax.set_facecolor("#111827")
    plt.gcf().patch.set_facecolor("#0F172A")

    for asset, data in per_asset_analysis.items():
        lengths = data["streak_lengths"]
        if lengths:
            x = np.sort(lengths)
            y = np.arange(1, len(x) + 1) / len(x)
            color = ASSET_COLORS.get(asset, "#94A3B8")
            plt.step(x, y, where="post", label=f"{asset} (n={len(lengths)})", color=color, linewidth=1.8, alpha=0.85)

    # Plot Combined ECDF
    if all_lengths:
        x_comb = np.sort(all_lengths)
        y_comb = np.arange(1, len(x_comb) + 1) / len(x_comb)
        plt.step(x_comb, y_comb, where="post", label=f"Combined (n={len(all_lengths)})", color="#FFFFFF", linewidth=2.5, linestyle="--")

    plt.title("Empirical Cumulative Distribution Function (ECDF) of Streak Lengths", fontsize=14, fontweight="bold", color="#F8FAFC", pad=15)
    plt.xlabel("Streak Length N", fontsize=11, color="#E2E8F0")
    plt.ylabel("Cumulative Probability P(Streak <= N)", fontsize=11, color="#E2E8F0")
    plt.xticks(np.arange(1, max(all_lengths) + 1 if all_lengths else 10, 1), color="#CBD5E1")
    plt.yticks(np.arange(0, 1.1, 0.1), color="#CBD5E1")
    plt.grid(True, linestyle="--", alpha=0.3, color="#475569")
    plt.legend(facecolor="#1E293B", edgecolor="#334155", labelcolor="#F8FAFC")
    plt.tight_layout()

    file_path = os.path.join(output_dir, "streak_ecdf.png")
    plt.savefig(file_path)
    plt.close()
    print(f"Saved plot: {file_path}")


def run_historical_analysis(
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    output_dir: str = "outputs",
) -> Tuple[dict, dict]:
    """
    Executes end-to-end historical analysis pipeline.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if not end_date:
        end_date = now
    if not start_date:
        start_date = end_date - datetime.timedelta(days=90)

    print(f"[*] Initializing Kalshi API Client...")
    print(f"[*] Fetching historical outcomes from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

    client = KalshiClient()
    asset_markets = client.fetch_all_assets_history(start_date=start_date, end_date=end_date)

    print(f"[*] Processing directional streak statistics and probabilities...")
    per_asset_analysis, combined_analysis, all_lengths = process_all_assets_streaks(asset_markets)

    # Output ASCII Table to terminal
    ascii_table = generate_ascii_tables(per_asset_analysis, combined_analysis, start_date, end_date)
    print(ascii_table)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate Visualization Plots
    print(f"[*] Generating visualization plots in '{output_dir}'...")
    if all_lengths:
        plot_streak_histogram(per_asset_analysis, all_lengths, output_dir)
        plot_streak_boxplots(per_asset_analysis, output_dir)
        plot_streak_ecdf(per_asset_analysis, all_lengths, output_dir)

    print(f"\n[+] Historical analysis completed successfully!")
    return per_asset_analysis, combined_analysis


def main():
    parser = argparse.ArgumentParser(description="Kalshi 15-Minute Crypto Market Streak Historical Analyzer")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD), default: 90 days ago")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), default: now")
    parser.add_argument("--output-dir", type=str, default="outputs", help="Directory to save generated plot images")
    args = parser.parse_args()

    s_date = parse_date_arg(args.start_date)
    e_date = parse_date_arg(args.end_date)

    run_historical_analysis(start_date=s_date, end_date=e_date, output_dir=args.output_dir)


if __name__ == "__main__":
    main()

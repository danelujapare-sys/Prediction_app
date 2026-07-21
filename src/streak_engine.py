"""
Streak Analytics Engine for Kalshi 15-Minute Crypto Markets.
Computes streak length statistics, empirical distributions, and conditional reversal probabilities.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional


def extract_streaks_from_markers(markers: List[int]) -> Tuple[List[int], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extracts directional streak lengths from a chronological sequence of outcome markers (+1 or -1).

    Args:
        markers: List of outcome markers (+1 for Up/Green, -1 for Down/Red)

    Returns:
        Tuple containing:
        - completed_streak_lengths: List of integer streak lengths before a reversal occurred.
        - streak_details: List of dicts with direction, length, start_idx, end_idx.
        - current_active_streak: Dict with current un-reversed streak length and direction.
    """
    if not markers:
        return [], [], {"length": 0, "direction": None, "marker": 0}

    completed_lengths = []
    streak_details = []

    current_marker = markers[0]
    current_len = 1
    start_idx = 0

    for i in range(1, len(markers)):
        marker = markers[i]
        if marker == current_marker:
            current_len += 1
        else:
            # Reversal occurred
            completed_lengths.append(current_len)
            streak_details.append({
                "direction": "Up" if current_marker == 1 else "Down",
                "marker": current_marker,
                "length": current_len,
                "start_idx": start_idx,
                "end_idx": i - 1,
            })
            current_marker = marker
            current_len = 1
            start_idx = i

    # Un-reversed active streak at the tail
    active_streak = {
        "length": current_len,
        "direction": "Up" if current_marker == 1 else "Down",
        "marker": current_marker,
        "start_idx": start_idx,
        "end_idx": len(markers) - 1,
    }

    return completed_lengths, streak_details, active_streak


def compute_statistics(streak_lengths: List[int]) -> Dict[str, Any]:
    """
    Computes statistical metrics for a list of streak lengths:
    Mean, Median, Max Outlier, Std Dev, Skewness, Kurtosis.
    """
    if not streak_lengths:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "max": 0,
            "std": 0.0,
            "skew": 0.0,
            "kurtosis": 0.0,
        }

    arr = np.array(streak_lengths, dtype=float)
    count = len(arr)
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    max_val = int(np.max(arr))
    std_val = float(np.std(arr, ddof=1)) if count > 1 else 0.0

    # Calculate Skewness and Kurtosis using scipy
    if count >= 3 and std_val > 0:
        skew_val = float(stats.skew(arr, bias=False))
        kurt_val = float(stats.kurtosis(arr, bias=False))  # excess kurtosis
    else:
        skew_val = 0.0
        kurt_val = 0.0

    return {
        "count": count,
        "mean": mean_val,
        "median": median_val,
        "max": max_val,
        "std": std_val,
        "skew": skew_val,
        "kurtosis": kurt_val,
    }


def compute_conditional_reversal_probabilities(
    streak_lengths: List[int], max_k: int = 8
) -> Dict[str, Dict[str, float]]:
    """
    Calculates conditional reversal probabilities P(Reversal | Streak = k) for k in {1..8+}.

    P(Reversal | Streak = k) = Count(Streak == k) / Count(Streak >= k)

    Returns dict mapping 'k_str' -> {'p_reversal': float, 'p_continuation': float, 'total_cases': int}
    """
    results = {}
    if not streak_lengths:
        for k in range(1, max_k + 1):
            key = f"{k}" if k < max_k else f"{max_k}+"
            results[key] = {"p_reversal": 0.0, "p_continuation": 0.0, "total_cases": 0}
        return results

    arr = np.array(streak_lengths)

    for k in range(1, max_k):
        at_least_k = np.sum(arr >= k)
        exact_k = np.sum(arr == k)

        if at_least_k > 0:
            p_rev = float(exact_k / at_least_k)
            p_cont = 1.0 - p_rev
        else:
            p_rev = 0.0
            p_cont = 0.0

        results[str(k)] = {
            "p_reversal": p_rev,
            "p_continuation": p_cont,
            "total_cases": int(at_least_k),
            "reversals": int(exact_k),
        }

    # For k = max_k (e.g. 8+)
    at_least_max = np.sum(arr >= max_k)
    exact_max = np.sum(arr == max_k)
    if at_least_max > 0:
        p_rev_max = float(exact_max / at_least_max)
        p_cont_max = 1.0 - p_rev_max
    else:
        p_rev_max = 0.0
        p_cont_max = 0.0

    results[f"{max_k}+"] = {
        "p_reversal": p_rev_max,
        "p_continuation": p_cont_max,
        "total_cases": int(at_least_max),
        "reversals": int(exact_max),
    }

    return results


def process_all_assets_streaks(
    asset_markets_dict: Dict[str, List[Dict[str, Any]]]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], List[int]]:
    """
    Processes market outcomes for all assets to compute:
    1. Per-asset streak stats and conditional probabilities.
    2. Combined aggregate stats and conditional probabilities across all assets.
    3. Flat list of all combined streak lengths.
    """
    per_asset_analysis = {}
    all_combined_streak_lengths = []

    for asset, markets in asset_markets_dict.items():
        markers = [m["outcome_marker"] for m in markets if "outcome_marker" in m]
        completed_lengths, details, active_streak = extract_streaks_from_markers(markers)
        all_combined_streak_lengths.extend(completed_lengths)

        stats_dict = compute_statistics(completed_lengths)
        cond_probs = compute_conditional_reversal_probabilities(completed_lengths, max_k=8)

        per_asset_analysis[asset] = {
            "market_count": len(markets),
            "completed_streaks_count": len(completed_lengths),
            "streak_lengths": completed_lengths,
            "stats": stats_dict,
            "conditional_probabilities": cond_probs,
            "active_streak": active_streak,
        }

    # Compute aggregate stats
    aggregate_stats = compute_statistics(all_combined_streak_lengths)
    aggregate_cond_probs = compute_conditional_reversal_probabilities(
        all_combined_streak_lengths, max_k=8
    )

    combined_analysis = {
        "total_markets": sum(len(m) for m in asset_markets_dict.values()),
        "total_completed_streaks": len(all_combined_streak_lengths),
        "stats": aggregate_stats,
        "conditional_probabilities": aggregate_cond_probs,
    }

    return per_asset_analysis, combined_analysis, all_combined_streak_lengths

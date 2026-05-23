"""Shared helpers for result aggregation scripts across experiment phases."""
from __future__ import annotations
import math
import os
import re
import pandas as pd


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def resolve_project_path(path_value: str) -> str:
    """Resolve a relative path against the project root."""
    if os.path.isabs(path_value):
        return path_value
    normalized = os.path.normpath(path_value)
    if normalized.startswith(".."):
        normalized = normalized[3:] if normalized.startswith(".." + os.sep) else normalized
    return os.path.abspath(os.path.join(PROJECT_ROOT, normalized))


def extract_id_number(testcase_name: str) -> int:
    """Extract the numeric testcase id for stable sorting."""
    match = re.search(r"(\d+)", testcase_name)
    return int(match.group(1)) if match else math.inf


def extract_m_value(testcase_name: str) -> int:
    """Extract M from a testcase name such as '*_M300'."""
    match = re.search(r"_M(\d+)", testcase_name)
    if not match:
        raise ValueError(f"Cannot extract M from testcase name: {testcase_name}")
    return int(match.group(1))


def determine_size_group(testcase_name: str) -> str:
    """Classify a testcase into the general size bucket only."""
    m_value = extract_m_value(testcase_name)
    if m_value <= 20:
        return "small"
    if 50 <= m_value <= 400:
        return "medium"
    if m_value >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m_value}: {testcase_name}")


def testcase_sort_key_by_size(testcase_name: str) -> tuple[int, int, str]:
    """Sort testcase names by size bucket, then numeric id, then name."""
    priority = {"small": 0, "medium": 1, "large": 2}
    return (priority[determine_size_group(testcase_name)], extract_id_number(testcase_name), testcase_name)


def testcase_sort_key_by_prefix(testcase_name: str) -> tuple[int, int, str]:
    """Sort testcase names by prefix family for Phase 1 style outputs."""
    lower = testcase_name.lower()
    if lower.startswith("small"):
        priority = 0
    elif lower.startswith("medium"):
        priority = 1
    elif lower.startswith("large"):
        priority = 2
    elif lower.startswith("edge"):
        priority = 3
    else:
        priority = 4
    return (priority, extract_id_number(testcase_name), testcase_name)


def collect_cost_rows(phase_dir: str, aggregate_filename: str = "aggregate_result.csv") -> list[pd.DataFrame]:
    """Read all algorithm CSV files in a phase directory except the aggregate output."""
    all_dfs = []

    for filename in sorted(os.listdir(phase_dir)):
        if not filename.endswith(".csv") or filename == aggregate_filename:
            continue

        file_path = os.path.join(phase_dir, filename)
        try:
            df = pd.read_csv(file_path, usecols=["testcase", "cost_min"])
            if not df.empty:
                all_dfs.append(df)
                print(f"[INFO] Loaded {len(df)} rows from {filename}")
        except Exception as exc:
            print(f"[WARNING] Failed to read {filename}: {exc}")

    return all_dfs


def build_cost_reference_dataframe(all_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Aggregate the minimum feasible cost per testcase across all algorithms."""
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df["cost_temp"] = combined_df["cost_min"].apply(
        lambda value: float("inf") if value <= 0 else value
    )

    agg_df = combined_df.groupby("testcase", as_index=False)["cost_temp"].min()
    agg_df["cost_reference"] = agg_df["cost_temp"].apply(
        lambda value: -1 if value == float("inf") else int(value)
    )
    agg_df["group"] = agg_df["testcase"].apply(determine_size_group)
    agg_df = agg_df.drop(columns=["cost_temp"])

    records = agg_df.to_dict(orient="records")
    records_sorted = sorted(records, key=lambda row: testcase_sort_key_by_size(row["testcase"]))
    return pd.DataFrame(records_sorted, columns=["testcase", "cost_reference", "group"])

import math
import os
import re

import pandas as pd


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PHASE2_DIR = os.path.join(PROJECT_ROOT, "results", "phase2")
OUTPUT_CSV = os.path.join(PHASE2_DIR, "aggregate_result.csv")


def extract_id_number(testcase_name: str) -> int:
    """Extract numeric testcase id for stable sorting."""
    match = re.search(r"(\d+)", testcase_name)
    return int(match.group(1)) if match else math.inf


def extract_m_value(testcase_name: str) -> int:
    """Extract M from testcase name such as *_M300."""
    match = re.search(r"_M(\d+)", testcase_name)
    if not match:
        raise ValueError(f"Cannot extract M from testcase name: {testcase_name}")
    return int(match.group(1))


def determine_group(testcase_name: str) -> str:
    """Classify testcase into the general size bucket only."""
    m_value = extract_m_value(testcase_name)
    if m_value <= 20:
        return "small"
    if 50 <= m_value <= 400:
        return "medium"
    if m_value >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m_value}: {testcase_name}")


def testcase_sort_key(testcase_name: str) -> tuple[int, int, str]:
    """Sort by general size bucket, then testcase id, then name."""
    group = determine_group(testcase_name)
    priority = {"small": 0, "medium": 1, "large": 2}
    return (priority[group], extract_id_number(testcase_name), testcase_name)


def collect_algorithm_rows() -> list[pd.DataFrame]:
    """Read all algorithm CSV files under results/phase2 except the aggregate output."""
    all_dfs = []

    for filename in sorted(os.listdir(PHASE2_DIR)):
        if not filename.endswith(".csv") or filename == "aggregate_result.csv":
            continue

        file_path = os.path.join(PHASE2_DIR, filename)
        try:
            df = pd.read_csv(file_path, usecols=["testcase", "cost_min"])
            if not df.empty:
                all_dfs.append(df)
                print(f"[INFO] Loaded {len(df)} rows from {filename}")
        except Exception as exc:
            print(f"[WARNING] Failed to read {filename}: {exc}")

    return all_dfs


def build_aggregate_dataframe(all_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Aggregate min feasible cost per testcase across all algorithms."""
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df["cost_temp"] = combined_df["cost_min"].apply(
        lambda value: float("inf") if value <= 0 else value
    )

    agg_df = combined_df.groupby("testcase", as_index=False)["cost_temp"].min()
    agg_df["cost_reference"] = agg_df["cost_temp"].apply(
        lambda value: -1 if value == float("inf") else int(value)
    )
    agg_df["group"] = agg_df["testcase"].apply(determine_group)
    agg_df = agg_df.drop(columns=["cost_temp"])

    records = agg_df.to_dict(orient="records")
    records_sorted = sorted(records, key=lambda row: testcase_sort_key(row["testcase"]))
    return pd.DataFrame(records_sorted, columns=["testcase", "cost_reference", "group"])


def main() -> None:
    print(f"[*] Scanning Phase 2 results at: {PHASE2_DIR}")

    if not os.path.isdir(PHASE2_DIR):
        raise FileNotFoundError(f"Phase 2 directory not found: {PHASE2_DIR}")

    all_dfs = collect_algorithm_rows()
    if not all_dfs:
        raise RuntimeError("No valid algorithm CSV files found in results/phase2.")

    final_df = build_aggregate_dataframe(all_dfs)
    os.makedirs(PHASE2_DIR, exist_ok=True)
    final_df.to_csv(OUTPUT_CSV, index=False)

    print(f"[SUCCESS] Saved aggregate CSV to: {OUTPUT_CSV}")
    print(f"[INFO] Total aggregated testcases: {len(final_df)}")


if __name__ == "__main__":
    main()

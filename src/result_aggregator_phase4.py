"""Build Phase 4 cost_reference.csv from all algorithm Phase 4 summaries."""
import os
from result_aggregator_common import (
    PROJECT_ROOT,
    build_cost_reference_dataframe,
    collect_cost_rows,
)


PHASE4_DIR = os.path.join(PROJECT_ROOT, "results", "phase4")
OUTPUT_CSV = os.path.join(PHASE4_DIR, "cost_reference.csv")
EXCLUDED_FILENAMES = {"cost_reference.csv", "aggregate_result.csv"}


def main() -> None:
    print(f"[*] Scanning Phase 4 results at: {PHASE4_DIR}")

    if not os.path.isdir(PHASE4_DIR):
        raise FileNotFoundError(f"Phase 4 directory not found: {PHASE4_DIR}")

    all_dfs = collect_cost_rows(PHASE4_DIR, excluded_filenames=EXCLUDED_FILENAMES)
    if not all_dfs:
        raise RuntimeError("No valid algorithm CSV files found in results/phase4.")

    final_df = build_cost_reference_dataframe(all_dfs)
    os.makedirs(PHASE4_DIR, exist_ok=True)
    final_df.to_csv(OUTPUT_CSV, index=False)

    print(f"[SUCCESS] Saved cost reference CSV to: {OUTPUT_CSV}")
    print(f"[INFO] Total aggregated testcases: {len(final_df)}")


if __name__ == "__main__":
    main()

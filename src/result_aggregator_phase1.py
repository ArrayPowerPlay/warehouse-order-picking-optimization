"""Aggregate Phase 1 JSON results into a single CSV summary file."""
import os
import json
import math
import pandas as pd
import argparse

from result_aggregator_common import (
    PROJECT_ROOT,
    resolve_project_path,
    testcase_sort_key_by_prefix,
)


BASE_DIR = os.path.join(PROJECT_ROOT, "results")
PHASE_DIR = os.path.join(BASE_DIR, "phase1")
OUTPUT_CSV = os.path.join(PHASE_DIR, "aggregate_results.csv")


def main():
    # Support command line arguments for flexibility
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--phase", type=int, default=1, help="Phase number.")
    arg_parser.add_argument("--output_csv",type=str, default="aggregate_results.csv", help="Output CSV file name.")
    arg_parser.add_argument("--output_dir", type=str, default="../results/phase1", help="Directory to save the output CSV.")
    
    args = arg_parser.parse_args()
    phase_dir = os.path.join(BASE_DIR, f"phase{args.phase}")
    output_dir = resolve_project_path(args.output_dir)
    output_csv = os.path.join(output_dir, args.output_csv)

    if not os.path.isdir(phase_dir):
        raise FileNotFoundError(f"Phase directory not found: {phase_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Get testcase folders
    testcase_dirs = [
        d for d in os.listdir(phase_dir)
        if os.path.isdir(os.path.join(phase_dir, d))
    ]

    testcase_dirs.sort(key=testcase_sort_key_by_prefix)

    # Pass 1: collect all algorithm names
    algorithms = set()

    for testcase in testcase_dirs:
        testcase_path = os.path.join(phase_dir, testcase)

        for filename in os.listdir(testcase_path):
            if filename.endswith(".json"):
                algo_name = os.path.splitext(filename)[0]
                algorithms.add(algo_name)

    algorithms = sorted(algorithms)

    # Build rows
    rows = []

    for testcase in testcase_dirs:
        testcase_path = os.path.join(phase_dir, testcase)

        row = {
            "testcase": testcase
        }

        # Initialize all columns with NaN
        for algo in algorithms:
            row[f"t_best_{algo}"] = math.nan
            row[f"time_limit_{algo}"] = math.nan

        # Read existing json files
        for filename in os.listdir(testcase_path):

            if not filename.endswith(".json"):
                continue

            algo_name = os.path.splitext(filename)[0]
            json_path = os.path.join(testcase_path, filename)

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                row[f"t_best_{algo_name}"] = data.get("t_best", math.nan)
                row[f"time_limit_{algo_name}"] = data.get("time_limit", math.nan)

            except Exception as e:
                print(f"[WARNING] Failed to read {json_path}: {e}")

        rows.append(row)

    # Create dataframe
    df = pd.DataFrame(rows)

    # Save CSV
    df.to_csv(output_csv, index=False)

    print(f"[INFO] Aggregate CSV saved to:")
    print(output_csv)


if __name__ == "__main__":
    main()

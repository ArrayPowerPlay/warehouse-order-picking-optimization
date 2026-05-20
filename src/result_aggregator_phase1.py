import os
import json
import math
import pandas as pd
import re
import argparse

BASE_DIR = "../results"
PHASE_DIR = os.path.join(BASE_DIR, "phase1")
OUTPUT_CSV = os.path.join(PHASE_DIR, "aggregate_results.csv")


def extract_id_number(testcase_name):
    """
    Extract id number of testcase.
    Example:
        small_26_N30_M200 -> 26
    """
    match = re.search(r'(\d+)', testcase_name)
    return int(match.group(1)) if match else math.inf


def testcase_sort_key(name):
    """
    Sorting priority:
        small -> medium -> large -> edge -> others
    Then sort by numeric id.
    Then alphabetical.
    """

    lower = name.lower()

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

    id_number = extract_id_number(name)

    return (priority, id_number, name)


def main():
    # Support command line arguments for flexibility
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--phase", type=int, default=1, help="Phase number.")
    arg_parser.add_argument("--output_csv",type=str, default="aggregate_results.csv", help="Output CSV file name.")
    arg_parser.add_argument("--output_dir", type=str, default="../results/phase1", help="Directory to save the output CSV.")
    
    args = arg_parser.parse_args()
    PHASE_DIR = os.path.join(BASE_DIR, f"phase{args.phase}")
    OUTPUT_CSV = os.path.join(args.output_dir, args.output_csv)
    # Get testcase folders
    testcase_dirs = [
        d for d in os.listdir(PHASE_DIR)
        if os.path.isdir(os.path.join(PHASE_DIR, d))
    ]

    testcase_dirs.sort(key=testcase_sort_key)

    # Pass 1: collect all algorithm names
    algorithms = set()

    for testcase in testcase_dirs:
        testcase_path = os.path.join(PHASE_DIR, testcase)

        for filename in os.listdir(testcase_path):
            if filename.endswith(".json"):
                algo_name = os.path.splitext(filename)[0]
                algorithms.add(algo_name)

    algorithms = sorted(algorithms)

    # Build rows
    rows = []

    for testcase in testcase_dirs:
        testcase_path = os.path.join(PHASE_DIR, testcase)

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
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"[INFO] Aggregate CSV saved to:")
    print(OUTPUT_CSV)


if __name__ == "__main__":
    main()
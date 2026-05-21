import os
import json
import math
import pandas as pd
import re
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "results")
PHASE_DIR = os.path.join(BASE_DIR, "phase1")
OUTPUT_CSV = os.path.join(PHASE_DIR, "aggregate_results.csv")


def resolve_path(path_value: str) -> str:
    """Resolve relative paths against the project root."""
    if os.path.isabs(path_value):
        return path_value
    normalized = os.path.normpath(path_value)
    if normalized.startswith(".."):
        normalized = normalized[3:] if normalized.startswith(".." + os.sep) else normalized
    return os.path.abspath(os.path.join(PROJECT_ROOT, normalized))


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
    phase_dir = os.path.join(BASE_DIR, f"phase{args.phase}")
    output_dir = resolve_path(args.output_dir)
    output_csv = os.path.join(output_dir, args.output_csv)

    if not os.path.isdir(phase_dir):
        raise FileNotFoundError(f"Phase directory not found: {phase_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Get testcase folders
    testcase_dirs = [
        d for d in os.listdir(phase_dir)
        if os.path.isdir(os.path.join(phase_dir, d))
    ]

    testcase_dirs.sort(key=testcase_sort_key)

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

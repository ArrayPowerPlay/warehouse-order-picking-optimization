"""
Configuration settings for all solvers
"""
from pathlib import Path

# Thời gian chạy tối đa (time limit) cho các thuật toán theo kích thước instance (giây)
TIME_LIMIT_TESTING = {
    "small": 30.0,
    "medium": 600.0,
    "large": 900.0,
}

TIME_LIMITS = {
    "small": 18.0,
    "medium": 400.0,
    "large": 700.0
}

DATA_PATH = Path(__file__).resolve().parent.parent

# Số lần chạy độc lập cho mỗi bộ tham số trên 1 testcase
NUM_RUNS_PER_CONFIG = 3
# Các giá trị seed sử dụng cho một thuật toán
SEEDS = [0, 1, 2]

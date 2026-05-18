"""
Configuration settings for all solvers
"""
from pathlib import Path

# Thời gian chạy tối đa (time limit) cho các thuật toán theo kích thước instance (giây)
TIME_LIMIT_TESTING = {
    "small": 100.0,
    "medium": 360.0,
    "large": 900.0,
}

TIME_LIMITS = {
    "small": 20.0,
    "medium": 900.0,
    "large": 900.0
}

DATA_PATH = Path(__file__).resolve().parent.parent

# Số lần chạy độc lập cho mỗi bộ tham số trên 1 testcase
NUM_RUNS_PER_CONFIG = 10
# Các giá trị seed sử dụng cho một thuật toán
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

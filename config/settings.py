"""
Configuration settings for all solvers
"""
from pathlib import Path

# Thời gian chạy tối đa (time limit) cho các thuật toán theo kích thước instance (giây)
TIME_LIMIT_TESTING = {
    "small": 18.0,
    "medium": 360.0,
    "large": 600.0,
}

TIME_LIMITS = {
    "small": 20.0,
    "medium": 720.0,
    "large": 900.0
}

DATA_PATH = Path(__file__).resolve().parent.parent

# Số lần chạy độc lập cho mỗi bộ tham số trên 1 testcase
NUM_RUNS_PER_CONFIG = 5
# Các giá trị seed sử dụng cho một thuật toán
SEEDS = [0, 1, 2, 3, 4]

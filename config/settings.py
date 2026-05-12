"""
Configuration settings for all solvers
"""

# Thời gian chạy tối đa (time limit) cho các thuật toán theo kích thước instance (giây)
TIME_LIMITS = {
    "small": 2.0,
    "medium": 5.0,
    "large": 15.0,
    "edge": 15.0
}

# Số lần chạy độc lập cho mỗi bộ tham số trên 1 testcase
NUM_RUNS_PER_CONFIG = 5

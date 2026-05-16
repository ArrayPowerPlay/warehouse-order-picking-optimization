"""
Configuration settings for all solvers
"""

# Thời gian chạy tối đa (time limit) cho các thuật toán theo kích thước instance (giây)
TIME_LIMIT_TESTING = {
    "small": 60.0,
    "medium": 300.0,
    "large": 900.0,
}

TIME_LIMITS = {
    "small": 0.0,
    "medium": 0.0,
    "large": 0.0
}

# Số lần chạy độc lập cho mỗi bộ tham số trên 1 testcase
NUM_RUNS_PER_CONFIG = 10

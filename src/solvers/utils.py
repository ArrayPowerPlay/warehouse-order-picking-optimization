"""
This file is used for creating some convenient functions that can be used multiple times
by other files.
"""

import sys

def read_input():
    """Input data"""
    input = sys.stdin.readline
    N, M = map(int, input().split())
    Q = [[0] * (M + 1)]

    for _ in range(N):
        row = [0] + list(map(int, input().split()))
        Q.append(row)

    d = []
    for _ in range(M + 1):
        row = list(map(int, input().split()))
        d.append(row)

    q = [0]
    q += list(map(int, input().split()))

    return N, M, Q, d, q


# Code hàm so sánh kết quả của thuật toán hiện tại vs thuật toán giải chính xác
#  (tính toán và so sánh % chênh lệch + thời gian chạy của thuật toán)
def evaluator():
    pass


# code hàm kiểm tra dữ liệu đầu vào có thỏa mãn các ràng buộc hay không ở đây
def validator():
    pass
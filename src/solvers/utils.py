"""
utils.py — Các hàm tiện ích dùng chung cho tất cả solver.

Hàm:
    read_input()  → Đọc input từ stdin theo định dạng bài toán.
    evaluator()   → Tính toán và đánh giá chất lượng một lời giải (route).
    validator()   → Kiểm tra tính hợp lệ của dữ liệu đầu vào.
"""

from __future__ import annotations
import sys


# =============================================================================
# 1. ĐỌC INPUT
# =============================================================================

def read_input(stream=None):
    """
    Đọc dữ liệu vào theo định dạng chuẩn của bài toán.

    Định dạng file .in:
        Dòng 1          : N M
        Dòng 2 .. N+1   : N hàng của ma trận Q (mỗi hàng M số nguyên)
        Dòng N+2..N+M+2 : (M+1) hàng của ma trận khoảng cách d
        Dòng N+M+3      : N số nguyên q[1..N]

    Quy ước index (1-based để khớp với đề bài):
        Q[i][j]  : lượng sản phẩm loại i tại kệ j  (i=1..N, j=1..M)
                   Q[0] là hàng giả — bỏ trống (toàn 0)
                   Q[i][0] là cột giả — bỏ trống (= 0)
        d[i][j]  : khoảng cách từ điểm i đến điểm j  (0=cửa kho, 1..M=kệ)
        q[i]     : số lượng sản phẩm loại i cần thu gom  (i=1..N)
                   q[0] là phần tử giả — bỏ trống (= 0)

    Args:
        stream: file-like object để đọc (mặc định: sys.stdin).

    Returns:
        tuple: (N, M, Q, d, q) theo quy ước index 1-based ở trên.
    """
    if stream is None:
        stream = sys.stdin
    data = stream.read().split()
    it = iter(data)

    N = int(next(it))
    M = int(next(it))

    # Ma trận Q: (N+1) x (M+1), index 1-based
    Q = [[0] * (M + 1) for _ in range(N + 1)]
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            Q[i][j] = int(next(it))

    # Ma trận khoảng cách: (M+1) x (M+1), index 0-based
    d = []
    for _ in range(M + 1):
        row = [int(next(it)) for _ in range(M + 1)]
        d.append(row)

    # Vector nhu cầu: (N+1,), index 1-based
    q = [0] * (N + 1)
    for i in range(1, N + 1):
        q[i] = int(next(it))

    return N, M, Q, d, q


# =============================================================================
# 2. EVALUATOR — Đánh giá chất lượng lời giải
# =============================================================================

def evaluator(
    route: list[int],
    N: int,
    M: int,
    Q: list[list[int]],
    d: list[list[int]],
    q: list[int],
) -> dict:
    """
    Đánh giá một lời giải (route) cho bài toán order picking.

    Một lời giải hợp lệ là một danh sách các kệ cần ghé thăm theo thứ tự,
    sao cho tổng lượng sản phẩm thu được >= nhu cầu đặt hàng cho mọi loại sản phẩm.

    Args:
        route : Danh sách các kệ theo thứ tự ghé thăm (index 1-based, không chứa 0).
                Ví dụ: [3, 7, 2] nghĩa là: cửa kho → kệ 3 → kệ 7 → kệ 2 → cửa kho.
        N     : Số loại sản phẩm.
        M     : Số kệ hàng.
        Q     : Ma trận tài nguyên Q[i][j] — 1-based (Q[0] và Q[i][0] là hàng/cột giả).
        d     : Ma trận khoảng cách d[i][j] — 0-based, d[0] là cửa kho.
        q     : Vector nhu cầu q[i] — 1-based (q[0] là phần tử giả).

    Returns:
        dict với các key:
            "total_distance" (int)   : Tổng khoảng cách đi (cửa → route → cửa).
            "is_valid"       (bool)  : True nếu route thỏa mãn tất cả ràng buộc nhu cầu.
            "is_infeasible"  (bool)  : True nếu bài toán không có nghiệm (tổng kho < nhu cầu).
            "num_shelves"    (int)   : Số kệ được ghé thăm.
            "collected"      (list)  : collected[i] = tổng sản phẩm loại i thu được (1-based).
            "shortage"       (list)  : shortage[i] = max(0, q[i] - collected[i]) (1-based).

    Notes:
        - Route rỗng [] được coi là hợp lệ NẾU q[i] = 0 với mọi i (không cần gì).
        - Route rỗng [] với q[i] > 0 cho một số i → is_valid = False.
        - Nếu bài toán infeasible từ đầu (total supply < demand), hàm vẫn tính
          total_distance theo route được truyền vào, nhưng đánh dấu is_infeasible = True.
    """
    # --- Kiểm tra route có chứa kệ hợp lệ không ---
    is_internal_valid = True
    for shelf in route:
        if not (1 <= shelf <= M):
            is_internal_valid = False
            break
    if is_internal_valid and len(route) != len(set(route)):
        is_internal_valid = False

    # --- Kiểm tra bài toán có khả thi không (tính from scratch) ---
    is_infeasible = False
    for i in range(1, N + 1):
        total_supply = sum(Q[i][j] for j in range(1, M + 1))
        if total_supply < q[i]:
            is_infeasible = True
            break

    # --- Tính tổng khoảng cách ---
    total_distance: int = 0
    if route:
        # Cửa kho (0) → kệ đầu tiên
        total_distance += d[0][route[0]]
        # Giữa các kệ liên tiếp
        for k in range(len(route) - 1):
            total_distance += d[route[k]][route[k + 1]]
        # Kệ cuối → cửa kho (0)
        total_distance += d[route[-1]][0]

    # --- Tính lượng sản phẩm thu gom per route ---
    collected = [0] * (N + 1)   # index 1-based
    for shelf in route:
        for i in range(1, N + 1):
            collected[i] += Q[i][shelf]

    # --- Kiểm tra ràng buộc nhu cầu ---
    shortage = [0] * (N + 1)    # index 1-based
    is_demand_met = True
    for i in range(1, N + 1):
        if collected[i] < q[i]:
            shortage[i] = q[i] - collected[i]
            is_demand_met = False

    is_valid = is_internal_valid and is_demand_met

    # --- Route rỗng nhưng vẫn hợp lệ nếu không cần gì ---
    if not route and is_valid and not is_infeasible:
        total_distance = 0

    return {
        "total_distance": total_distance,
        "is_valid":        is_valid,
        "is_infeasible":   is_infeasible,
        "num_shelves":     len(route),
        "collected":       collected,   # 1-based list
        "shortage":        shortage,    # 1-based list
    }


def compute_route_distance(route: list[int], d: list[list[int]]) -> int:
    """
    Tính nhanh tổng khoảng cách của route (cửa kho → route → cửa kho).

    Tiện dụng khi chỉ cần khoảng cách mà không cần đánh giá đầy đủ.

    Args:
        route : Danh sách kệ (index 1-based).
        d     : Ma trận khoảng cách (index 0-based, d[0] = cửa kho).

    Returns:
        Tổng khoảng cách (int). Trả về 0 nếu route rỗng.
    """
    if not route:
        return 0
    dist = d[0][route[0]]
    for k in range(len(route) - 1):
        dist += d[route[k]][route[k + 1]]
    dist += d[route[-1]][0]
    return dist


# =============================================================================
# 3. VALIDATOR — Kiểm tra tính hợp lệ của dữ liệu đầu vào
# =============================================================================

def validator(
    N: int,
    M: int,
    Q: list[list[int]],
    d: list[list[int]],
    q: list[int],
) -> dict:
    """
    Kiểm tra tính hợp lệ và nhất quán của bộ dữ liệu đầu vào.

    Các ràng buộc được kiểm tra:
        1. Phạm vi N, M: 1 <= N <= 50, 1 <= M <= 1000.
        2. Kích thước ma trận Q: phải là (N+1) x (M+1) (index 1-based).
        3. Giá trị Q[i][j] >= 0 với mọi i, j.
        4. Kích thước ma trận d: phải là (M+1) x (M+1).
        5. Tính đối xứng: d[i][j] == d[j][i] với mọi i, j.
        6. Đường chéo: d[i][i] == 0 với mọi i.
        7. Giá trị d[i][j] >= 0 với mọi i, j.
        8. Kích thước vector q: phải là (N+1) (index 1-based).
        9. Giá trị q[i] >= 0 với mọi i.
       10. Kiểm tra tính khả thi: sum_j Q[i][j] >= q[i] với mọi i
           (thông tin này không phải vi phạm mà là cảnh báo).

    Args:
        N, M, Q, d, q : Dữ liệu theo quy ước 1-based của read_input().

    Returns:
        dict với các key:
            "is_valid"    (bool)  : True nếu không có lỗi nào.
            "is_feasible" (bool)  : True nếu bài toán có khả năng có nghiệm.
    """
    is_valid = True

    # 1. Phạm vi N, M
    if not (1 <= N <= 50) or not (1 <= M <= 1000):
        is_valid = False

    # 2. Kích thước Q
    if is_valid:
        if len(Q) != N + 1:
            is_valid = False
        else:
            for i in range(1, N + 1):
                if len(Q[i]) != M + 1:
                    is_valid = False; break
                for j in range(1, M + 1):
                    if Q[i][j] < 0:
                        is_valid = False; break
                if not is_valid: break

    # 3. Kích thước d
    if is_valid:
        if len(d) != M + 1:
            is_valid = False
        else:
            for i in range(M + 1):
                if len(d[i]) != M + 1:
                    is_valid = False; break
                for j in range(M + 1):
                    if d[i][j] < 0 or (i == j and d[i][j] != 0) or (i != j and d[i][j] != d[j][i]):
                        is_valid = False; break
                if not is_valid: break

    # 4. Kích thước và giá trị q
    if is_valid:
        if len(q) != N + 1:
            is_valid = False
        else:
            for i in range(1, N + 1):
                if q[i] < 0:
                    is_valid = False; break

    # 5. Kiểm tra khả thi
    is_feasible = True
    if is_valid:
        for i in range(1, N + 1):
            total_supply = sum(Q[i][j] for j in range(1, M + 1))
            if total_supply < q[i]:
                is_feasible = False
                break
    else:
        is_feasible = False

    return {
        "is_valid":    is_valid,
        "is_feasible": is_feasible,
    }
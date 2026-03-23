"""
data_generator.py  -  Python >= 3.11  -  Phiên bản 2.0.0
Sinh file input cho bài toán tìm đường đi tối ưu trong kho hàng.

Cấu trúc file .in sinh ra:
  Dòng 1          : N M
  Dòng 2 .. N+1   : ma trận Q  (N hàng x M cột)
  Dòng N+2..N+M+2 : ma trận khoảng cách  ((M+1) hàng x (M+1) cột)
  Dòng N+M+3      : vector q  (N phần tử)
"""

import math
import os
import random
from datetime import datetime

# === Hằng số giới hạn cứng (không thay đổi) ==================================

# Bound tọa độ tối đa tuyệt đối: đảm bảo ceil(khoảng cách Euclidean) luôn
# nằm trong phạm vi số nguyên có dấu 32-bit.
#   Khoảng cách tối đa = 2C * sqrt(2) <= 2^31 - 1
#   => C <= (2^31 - 1) / (2 * sqrt(2)) = 759_250_124
COORD_BOUND_MAX: int = int((2**31 - 1) / (2 * math.sqrt(2)))   # = 759_250_124

MAX_RESOURCE_HARD_CAP: int = 1000   # Trần tuyệt đối của MAX_RESOURCE_I_PER_SHELF


# === Helpers ==================================================================

def _ask_int(prompt: str, lo: int, hi: int, default: int) -> int:
    """Nhắc người dùng nhập số nguyên trong [lo, hi]. Enter -> dùng mặc định."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            print(f"  -> Dùng giá trị mặc định: {default}")
            return default
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
            print(f"  X Giá trị phải nằm trong [{lo}, {hi}]. Vui lòng nhập lại.")
        except ValueError:
            print("  X Không hợp lệ — vui lòng nhập một số nguyên.")


def _ask_bool(prompt: str, default: bool = False) -> bool:
    """
    Nhắc người dùng chọn Y / N (không phân biệt hoa/thường).
      Y  -> True  (số thực)
      N  -> False (số nguyên)  [mặc định]
    """
    while True:
        raw = input(prompt).strip().upper()
        if raw == "":
            label = "số thực (Y)" if default else "số nguyên (N)"
            print(f"  -> Dùng giá trị mặc định: {label}")
            return default
        if raw == "Y":
            return True
        if raw == "N":
            return False
        print("  X Chỉ chấp nhận Y hoặc N. Vui lòng nhập lại.")


def _ask_feasibility(prompt: str) -> str:
    """
    Nhắc người dùng chọn chế độ sinh vector q:
      Y -> đảm bảo bài toán có nghiệm  (feasible)
      N -> đảm bảo bài toán vô nghiệm  (infeasible)
      D -> hoàn toàn ngẫu nhiên         [mặc định]
    Không phân biệt hoa/thường.
    """
    while True:
        raw = input(prompt).strip().upper()
        if raw == "":
            print("  -> Dùng giá trị mặc định: D (hoàn toàn ngẫu nhiên)")
            return "D"
        if raw in ("Y", "N", "D"):
            return raw
        print("  X Chỉ chấp nhận Y, N hoặc D. Vui lòng nhập lại.")


def _fmt(value: float | int, use_float: bool) -> str:
    """Định dạng một giá trị khoảng cách ra chuỗi."""
    if use_float:
        return f"{value:.2f}"
    return str(value)


def _euclidean(x1: int, y1: int, x2: int, y2: int, use_float: bool) -> float | int:
    """Tính khoảng cách Euclidean; làm tròn 2 chữ số thập phân hoặc ceil."""
    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    if use_float:
        return round(dist, 2)
    return math.ceil(dist)


# === Bước 1: Xác nhận tham số đầu vào ========================================

def step1_get_params() -> tuple[int, int, bool, int, int, str]:
    """
    Trả về: (n, m, use_float, coord_bound, max_resource, feasibility)
    """
    print()
    print("=" * 60)
    print("     SINH INPUT BÀI TOÁN TÌM ĐƯỜNG ĐI TỐI ƯU KHO HÀNG")
    print("=" * 60)
    print()

    n: int = _ask_int(
        "Nhập số loại sản phẩm  N  (1 <= N <= 50)    [mặc định = 5]  : ",
        lo=1, hi=50, default=5,
    )
    m: int = _ask_int(
        "Nhập số kệ hàng        M  (1 <= M <= 1000)  [mặc định = 10] : ",
        lo=1, hi=1000, default=10,
    )
    use_float: bool = _ask_bool(
        "Khoảng cách dạng số thực?  Y = số thực / N = số nguyên  [mặc định = N]: ",
        default=False,
    )

    # Giới hạn dưới của COORD_BOUND = m
    # Lý do: với coord_bound >= m, trong không gian [-m, m] x [-m, m] (trừ gốc)
    # tồn tại ít nhất (2m+1)^2 - 1 >= 4m^2 + 4m >= m điểm nguyên hợp lệ,
    # đảm bảo luôn tìm được m điểm phân biệt.
    print(f"\n  (Giới hạn hợp lệ cho COORD_BOUND: [{m}, {COORD_BOUND_MAX}])")
    coord_bound: int = _ask_int(
        f"Nhập COORD_BOUND  (>= M={m}, <= {COORD_BOUND_MAX})  [mặc định = {COORD_BOUND_MAX}]: ",
        lo=m, hi=COORD_BOUND_MAX, default=COORD_BOUND_MAX,
    )

    max_resource: int = _ask_int(
        f"Nhập MAX_RESOURCE_I_PER_SHELF  (1 <= giá trị <= {MAX_RESOURCE_HARD_CAP})  [mặc định = 100]: ",
        lo=1, hi=MAX_RESOURCE_HARD_CAP, default=100,
    )

    feasibility: str = _ask_feasibility(
        "\nChế độ sinh yêu cầu q:\n"
        "  Y = đảm bảo có nghiệm (feasible)\n"
        "  N = đảm bảo vô nghiệm (infeasible)\n"
        "  D = hoàn toàn ngẫu nhiên (mặc định)\n"
        "Lựa chọn [D]: ",
    )

    return n, m, use_float, coord_bound, max_resource, feasibility


# === Bước 2: Sinh ma trận tài nguyên Q  (N hàng x M cột) =====================

def step2_gen_resource_matrix(n: int, m: int, max_resource: int) -> list[list[int]]:
    """
    Q[i][j] trong [0, max_resource]  (số nguyên không âm).
    Hàng i ứng với loại sản phẩm i; cột j ứng với kệ j.
    """
    return [
        [random.randint(0, max_resource) for _ in range(m)]
        for _ in range(n)
    ]


# === Bước 3: Sinh ma trận khoảng cách  ((M+1) x (M+1)) =======================

def step3_gen_distance_matrix(
    m: int,
    use_float: bool,
    coord_bound: int,
) -> list[list[float | int]]:
    """
    Giai đoạn 3a — Sinh tọa độ:
        Sinh m điểm 2D đôi một khác nhau và khác gốc (0, 0).
        Tọa độ trong [-coord_bound, coord_bound].
        Nếu điểm mới trùng với điểm đã sinh hoặc gốc tọa độ, sinh lại.

    Giai đoạn 3b — Tính khoảng cách:
        Khoảng cách Euclidean giữa mọi cặp điểm.
        Kết quả: ma trận đối xứng (M+1) x (M+1), đường chéo = 0.
    """
    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}

    for _ in range(m):
        while True:
            x = random.randint(-coord_bound, coord_bound)
            y = random.randint(-coord_bound, coord_bound)
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break

    # all_points[0] = cửa kho (gốc); all_points[1..M] = kệ 1..M
    all_points: list[tuple[int, int]] = [(0, 0)] + coords

    size = m + 1
    dist_matrix: list[list[float | int]] = [[0] * size for _ in range(size)]

    for i in range(size):
        for j in range(i + 1, size):
            d = _euclidean(*all_points[i], *all_points[j], use_float)
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d

    return dist_matrix


# === Bước 4: Sinh vector yêu cầu  q  (N phần tử) =============================

def step4_gen_demand(
    n: int,
    m: int,
    Q: list[list[int]],
    max_resource: int,
    feasibility: str,
) -> list[int]:
    """
    Sinh q[i] theo ba chế độ:

    "Y" — feasible (có nghiệm):
        q[i] trong [0, sum_j Q[i][j]]
        Đảm bảo với mọi i: tổng tài nguyên loại i trên toàn bộ kệ >= q[i].

    "N" — infeasible (vô nghiệm):
        q[i] > sum_j Q[i][j] với mọi i
        Đảm bảo bài toán chắc chắn không có nghiệm.
        Trường hợp biên khi tổng kho = max_resource * m: cộng thêm [1, 100].

    "D" — default (hoàn toàn ngẫu nhiên):
        q[i] trong [0, max_resource * m]
        Không đảm bảo tính khả thi.
    """
    max_demand: int = max_resource * m

    match feasibility:

        case "Y":
            result: list[int] = []
            for i in range(n):
                supply = sum(Q[i])
                result.append(random.randint(0, supply))
            return result

        case "N":
            result = []
            for i in range(n):
                supply = sum(Q[i])
                lo = supply + 1
                # hi đảm bảo luôn >= lo dù supply đã ở mức tối đa
                hi = max(lo + 99, max_demand)
                result.append(random.randint(lo, hi))
            return result

        case _:   # "D"
            return [random.randint(0, max_demand) for _ in range(n)]


# === Ghi file .in =============================================================

def write_output(
    n: int,
    m: int,
    Q: list[list[int]],
    dist: list[list[float | int]],
    q: list[int],
    use_float: bool,
) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{n}_{m}_{timestamp}.in"
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, filename)

    lines: list[str] = []

    lines.append(f"{n} {m}")

    for row in Q:
        lines.append(" ".join(map(str, row)))

    for row in dist:
        lines.append(" ".join(_fmt(v, use_float) for v in row))

    lines.append(" ".join(map(str, q)))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return out_path


# === Main =====================================================================

def main() -> None:
    n, m, use_float, coord_bound, max_resource, feasibility = step1_get_params()

    print()
    print("Dang sinh du lieu...")

    Q    = step2_gen_resource_matrix(n, m, max_resource)
    dist = step3_gen_distance_matrix(m, use_float, coord_bound)
    q    = step4_gen_demand(n, m, Q, max_resource, feasibility)

    out_path = write_output(n, m, Q, dist, q, use_float)

    dist_type  = "so thuc (lam tron 2 chu so)" if use_float else "so nguyen (ceil)"
    feas_label = {
        "Y": "co nghiem (feasible)",
        "N": "vo nghiem (infeasible)",
        "D": "hoan toan ngau nhien",
    }[feasibility]

    print(f"\nDa tao file thanh cong!")
    print(f"  Ten file      : {os.path.basename(out_path)}")
    print(f"  Duong dan     : {out_path}")
    print(f"  N = {n}, M = {m}")
    print(f"  Khoang cach   : {dist_type}")
    print(f"  COORD_BOUND   : {coord_bound}")
    print(f"  MAX_RESOURCE  : {max_resource}")
    print(f"  Tinh kha thi  : {feas_label}")


if __name__ == "__main__":
    main()

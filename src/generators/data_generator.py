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


def _euclidean(x1: int, y1: int, x2: int, y2: int) -> int:
    """Tính khoảng cách Euclidean và làm tròn lên số nguyên (ceil)."""
    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return math.ceil(dist)


# === Bước 1: Xác nhận tham số đầu vào ========================================

def step1_get_params() -> tuple[int, int, int, int, str]:
    """
    Trả về: (n, m, coord_bound, max_resource, feasibility)
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

    # Giới hạn dưới của COORD_BOUND = m
    # Lý do: với coord_bound >= m, trong không gian [-m, m] x [-m, m] (trừ gốc)
    # tồn tại ít nhất (2m+1)^2 - 1 >= 4m^2 + 4m >= m điểm nguyên hợp lệ,
    # đảm bảo luôn tìm được m điểm phân biệt.
    print("\nCOORD_BOUND xác định kích thước hộp tọa độ để sinh vị trí các kệ.")
    print("Tất cả tọa độ kệ nằm trong [-COORD_BOUND, COORD_BOUND]; giá trị càng lớn thì kệ càng xa nhau.")
    print(f"(Giới hạn hợp lệ cho COORD_BOUND: [{m}, {COORD_BOUND_MAX}])")
    coord_bound: int = _ask_int(
        f"Nhập COORD_BOUND  (>= M={m}, <= {COORD_BOUND_MAX})  [mặc định = {COORD_BOUND_MAX}]: ",
        lo=m, hi=COORD_BOUND_MAX, default=COORD_BOUND_MAX,
    )

    print("\nMAX_RESOURCE_I_PER_SHELF là số lượng tối đa một kệ có thể chứa cho từng loại sản phẩm.")
    max_resource: int = _ask_int(
        f"Nhập MAX_RESOURCE_I_PER_SHELF  (1 <= giá trị <= {MAX_RESOURCE_HARD_CAP})  [mặc định = 100]: ",
        lo=1, hi=MAX_RESOURCE_HARD_CAP, default=100,
    )

    feasibility: str = _ask_feasibility(
        "\nChế độ sinh yêu cầu q:\n"
        "  Y = Đảm bảo có nghiệm (feasible)\n"
        "  N = Đảm bảo vô nghiệm (infeasible)\n"
        "  D = Hoàn toàn ngẫu nhiên (mặc định)\n"
        "Lựa chọn: ",
    )

    return n, m, coord_bound, max_resource, feasibility


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

# --- Các hàm sinh tọa độ theo dạng phân bố -----------------------------------

def _gen_coords_uniform(
    m: int, coord_bound: int,
) -> list[tuple[int, int]]:
    """Phân bố Uniform Random: tọa độ ngẫu nhiên đều trong [-B, B]."""
    B = coord_bound
    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}

    for _ in range(m):
        while True:
            x = random.randint(-B, B)
            y = random.randint(-B, B)
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


def _gen_coords_corner_biased(
    m: int, coord_bound: int,
) -> list[tuple[int, int]]:
    """
    Phân bố Corner Biased: nodes tập trung ở 4 góc của không gian.
    Mỗi node được gán ngẫu nhiên vào 1 trong 4 góc, rồi lệch trong
    phạm vi ±30% coord_bound quanh góc đó.
    """
    B = coord_bound
    corners = [(-B, -B), (-B, B), (B, -B), (B, B)]
    spread = max(1, int(B * 0.3))

    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}

    for _ in range(m):
        while True:
            cx, cy = random.choice(corners)
            x = cx + random.randint(-spread, spread)
            y = cy + random.randint(-spread, spread)
            x = max(-B, min(B, x))
            y = max(-B, min(B, y))
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


def _gen_coords_clustered(
    m: int, coord_bound: int,
) -> list[tuple[int, int]]:
    """
    Phân bố Clustered: nodes chia thành K cụm (K tự động theo M).
    Tâm cụm nằm trong 70% không gian, mỗi node lệch ±15% quanh tâm.
    """
    B = coord_bound
    num_clusters = min(5, max(3, m // 30))

    # Tâm cụm nằm trong vùng 70% để cụm không bị cắt bởi biên
    inner = max(1, int(B * 0.7))
    centers: list[tuple[int, int]] = [
        (random.randint(-inner, inner), random.randint(-inner, inner))
        for _ in range(num_clusters)
    ]
    spread = max(1, int(B * 0.15))

    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}

    for _ in range(m):
        while True:
            cx, cy = random.choice(centers)
            x = cx + random.randint(-spread, spread)
            y = cy + random.randint(-spread, spread)
            x = max(-B, min(B, x))
            y = max(-B, min(B, y))
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


def _gen_coords_diagonal(
    m: int, coord_bound: int,
) -> list[tuple[int, int]]:
    """
    Phân bố Diagonal: nodes phân bố dọc đường chéo chính (y ≈ x).
    Mỗi node có vị trí t trên đường chéo, lệch vuông góc ±15% coord_bound.
    """
    B = coord_bound
    noise = max(1, int(B * 0.15))

    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}

    for _ in range(m):
        while True:
            t = random.randint(-B, B)
            dx = random.randint(-noise, noise)
            dy = random.randint(-noise, noise)
            x = max(-B, min(B, t + dx))
            y = max(-B, min(B, t + dy))
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


# --- Hàm chính sinh ma trận khoảng cách --------------------------------------

def step3_gen_distance_matrix(
    m: int,
    coord_bound: int,
    distribution: str = "uniform",
) -> list[list[int]]:
    """
    Giai đoạn 3a — Sinh tọa độ:
        Sinh m điểm 2D đôi một khác nhau và khác gốc (0, 0).
        Tọa độ trong [-coord_bound, coord_bound].
        Nếu điểm mới trùng với điểm đã sinh hoặc gốc tọa độ, sinh lại.

        Dạng phân bố (distribution):
          - "uniform"        : ngẫu nhiên đều (mặc định, giữ nguyên hành vi cũ)
          - "corner_biased"  : tập trung ở 4 góc
          - "clustered"      : chia thành K cụm
          - "diagonal"       : dọc đường chéo chính (y ≈ x)

    Giai đoạn 3b — Tính khoảng cách:
        Khoảng cách Euclidean giữa mọi cặp điểm.
        Kết quả: ma trận đối xứng (M+1) x (M+1), đường chéo = 0.
        Khoảng cách được làm tròn lên số nguyên bằng math.ceil().
    """
    # Giai đoạn 3a: sinh tọa độ theo dạng phân bố
    coord_generators = {
        "uniform":       _gen_coords_uniform,
        "corner_biased": _gen_coords_corner_biased,
        "clustered":     _gen_coords_clustered,
        "diagonal":      _gen_coords_diagonal,
    }
    gen_fn = coord_generators.get(distribution, _gen_coords_uniform)
    coords = gen_fn(m, coord_bound)

    # all_points[0] = cửa kho (gốc); all_points[1..M] = kệ 1..M
    all_points: list[tuple[int, int]] = [(0, 0)] + coords

    # Giai đoạn 3b: tính ma trận khoảng cách
    size = m + 1
    dist_matrix: list[list[int]] = [[0] * size for _ in range(size)]

    for i in range(size):
        for j in range(i + 1, size):
            d = _euclidean(*all_points[i], *all_points[j])
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
    dist: list[list[int]],
    q: list[int],
) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{n}_{m}_{timestamp}.in"

    # Lưu mọi file sinh ra dưới thư mục data ở root dự án
    # Script nằm tại src/generators/ nên cần lên 2 cấp để tới project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir, "data"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    lines: list[str] = []

    lines.append(f"{n} {m}")

    for row in Q:
        lines.append(" ".join(map(str, row)))

    for row in dist:
        lines.append(" ".join(map(str, row)))

    lines.append(" ".join(map(str, q)))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return out_path


# === Main =====================================================================

def main() -> None:
    n, m, coord_bound, max_resource, feasibility = step1_get_params()

    print()
    print("Đang sinh dữ liệu...")

    Q    = step2_gen_resource_matrix(n, m, max_resource)
    dist = step3_gen_distance_matrix(m, coord_bound)
    q    = step4_gen_demand(n, m, Q, max_resource, feasibility)

    out_path = write_output(n, m, Q, dist, q)

    feas_label = {
        "Y": "Có nghiệm (feasible)",
        "N": "Vô nghiệm (infeasible)",
        "D": "Hoàn toàn ngẫu nhiên",
    }[feasibility]

    print(f"\nĐã tạo file thành công!")
    print(f"  Tên file      : {os.path.basename(out_path)}")
    print(f"  Đường dẫn     : {out_path}")
    print(f"  N = {n}, M = {m}")
    print(f"  COORD_BOUND   : {coord_bound}")
    print(f"  MAX_RESOURCE  : {max_resource}")
    print(f"  Tính khả thi  : {feas_label}")


if __name__ == "__main__":
    main()

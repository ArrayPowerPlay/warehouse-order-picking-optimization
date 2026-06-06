"""
data_generator.py  —  Sinh một testcase .in cho bài toán tìm đường đi tối ưu kho hàng.

Thông thường được import bởi batch_generator.py để sinh hàng loạt testcase.
Cũng có thể chạy trực tiếp (python data_generator.py) với tham số CLI tuỳ chọn
để sinh nhanh một file đơn lẻ mà không cần tương tác.

Cấu trúc file .in sinh ra:
  Dòng 1          : N M
  Dòng 2 .. N+1   : ma trận Q  (N hàng x M cột)
  Dòng N+2..N+M+2 : ma trận khoảng cách  ((M+1) hàng x (M+1) cột)
  Dòng N+M+3      : vector q  (N phần tử)

Quy ước index (1-based, khớp với solver):
  Q[i][j]  — số lượng sản phẩm loại i tại kệ j  (i=1..N, j=1..M)
  d[i][j]  — khoảng cách từ điểm i đến điểm j   (0=cửa kho, 1..M=kệ)
  q[i]     — nhu cầu cần thu gom của sản phẩm i  (i=1..N)
"""

import argparse
import math
import os
import random
from datetime import datetime

# === Hằng số giới hạn cứng ===================================================

# Bound tọa độ tối đa tuyệt đối: đảm bảo ceil(khoảng cách Euclidean) luôn
# nằm trong phạm vi số nguyên có dấu 32-bit.
#   Khoảng cách tối đa = 2C * sqrt(2) <= 2^31 - 1
#   => C <= (2^31 - 1) / (2 * sqrt(2)) = 759_250_124
COORD_BOUND_MAX: int = int((2**31 - 1) / (2 * math.sqrt(2)))   # = 759_250_124

MAX_RESOURCE_HARD_CAP: int = 1000   # Trần tuyệt đối của max_resource_per_shelf


# === Helpers ==================================================================

def _euclidean(x1: int, y1: int, x2: int, y2: int) -> int:
    """Tính khoảng cách Euclidean và làm tròn lên số nguyên (ceil)."""
    return math.ceil(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


# === Bước 1: Sinh ma trận tài nguyên Q  (N hàng x M cột) =====================

def step2_gen_resource_matrix(n: int, m: int, max_resource: int) -> list[list[int]]:
    """
    Sinh ma trận tài nguyên Q kích thước N×M.

    Q[i][j] ~ Uniform[0, max_resource]  (số nguyên không âm).
    Hàng i ứng với loại sản phẩm i (0-indexed trong list nội bộ);
    cột j ứng với kệ j.

    Args:
        n:            Số loại sản phẩm.
        m:            Số kệ.
        max_resource: Số lượng tối đa một kệ có thể chứa cho mỗi loại sản phẩm.

    Returns:
        List 2D kích thước n×m, mỗi phần tử trong [0, max_resource].
    """
    return [
        [random.randint(0, max_resource) for _ in range(m)]
        for _ in range(n)
    ]


# === Bước 2: Sinh ma trận khoảng cách  ((M+1) x (M+1)) =======================

def _gen_coords_uniform(m: int, coord_bound: int) -> list[tuple[int, int]]:
    """
    Phân bố Uniform Random: sinh m tọa độ 2D ngẫu nhiên đều trong [-B, B]×[-B, B].
    Đảm bảo mọi điểm đôi một khác nhau và khác gốc tọa độ (0, 0) — vị trí cửa kho.
    """
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


def _gen_coords_corner_biased(m: int, coord_bound: int) -> list[tuple[int, int]]:
    """
    Phân bố Corner Biased: m điểm tập trung ở 4 góc của không gian [-B, B]×[-B, B].
    Mỗi điểm được gán ngẫu nhiên vào 1 trong 4 góc, rồi lệch trong phạm vi ±30%B.
    """
    B = coord_bound
    corners = [(-B, -B), (-B, B), (B, -B), (B, B)]
    spread = max(1, int(B * 0.3))
    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}
    for _ in range(m):
        while True:
            cx, cy = random.choice(corners)
            x = max(-B, min(B, cx + random.randint(-spread, spread)))
            y = max(-B, min(B, cy + random.randint(-spread, spread)))
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


def _gen_coords_clustered(m: int, coord_bound: int) -> list[tuple[int, int]]:
    """
    Phân bố Clustered: m điểm chia thành K cụm (K tự động theo M).
    Tâm cụm nằm trong 70% không gian trung tâm, mỗi điểm lệch ±15%B quanh tâm.
    """
    B = coord_bound
    num_clusters = min(5, max(3, m // 30))
    inner = max(1, int(B * 0.7))
    centers = [
        (random.randint(-inner, inner), random.randint(-inner, inner))
        for _ in range(num_clusters)
    ]
    spread = max(1, int(B * 0.15))
    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}
    for _ in range(m):
        while True:
            cx, cy = random.choice(centers)
            x = max(-B, min(B, cx + random.randint(-spread, spread)))
            y = max(-B, min(B, cy + random.randint(-spread, spread)))
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


def _gen_coords_diagonal(m: int, coord_bound: int) -> list[tuple[int, int]]:
    """
    Phân bố Diagonal: m điểm phân bố dọc đường chéo chính (y ≈ x).
    Mỗi điểm có vị trí t ngẫu nhiên trên đường chéo, lệch vuông góc ±15%B.
    """
    B = coord_bound
    noise = max(1, int(B * 0.15))
    coords: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = {(0, 0)}
    for _ in range(m):
        while True:
            t = random.randint(-B, B)
            x = max(-B, min(B, t + random.randint(-noise, noise)))
            y = max(-B, min(B, t + random.randint(-noise, noise)))
            if (x, y) not in used:
                coords.append((x, y))
                used.add((x, y))
                break
    return coords


def step3_gen_distance_matrix(
    m: int,
    coord_bound: int,
    distribution: str = "uniform",
) -> list[list[int]]:
    """
    Sinh ma trận khoảng cách đối xứng kích thước (M+1)×(M+1).

    Giai đoạn 3a — Sinh tọa độ:
        Sinh m điểm 2D đôi một khác nhau và khác gốc (0, 0) (= cửa kho).
        Tọa độ nằm trong [-coord_bound, coord_bound].

        Tham số distribution chọn kiểu phân bố:
          - "uniform"        : ngẫu nhiên đều (mặc định)
          - "corner_biased"  : tập trung ở 4 góc
          - "clustered"      : chia thành K cụm
          - "diagonal"       : dọc đường chéo chính (y ≈ x)

    Giai đoạn 3b — Tính khoảng cách:
        Khoảng cách Euclidean giữa mọi cặp điểm, làm tròn lên (math.ceil).
        all_points[0] = cửa kho (0, 0); all_points[1..M] = kệ 1..M.
        Kết quả là ma trận đối xứng, đường chéo = 0.

    Args:
        m:            Số kệ.
        coord_bound:  Biên tọa độ, >= m.
        distribution: Kiểu phân bố tọa độ.

    Returns:
        List 2D kích thước (m+1)×(m+1).
    """
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

    size = m + 1
    dist_matrix: list[list[int]] = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i + 1, size):
            d = _euclidean(*all_points[i], *all_points[j])
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d

    return dist_matrix


# === Bước 3: Sinh vector yêu cầu  q  (N phần tử) =============================

def step4_gen_demand(
    n: int,
    m: int,
    Q: list[list[int]],
    max_resource: int,
    feasibility: str,
) -> list[int]:
    """
    Sinh vector nhu cầu q kích thước N theo ba chế độ.

    "Y" — feasible (có nghiệm):
        q[i] ~ Uniform[0, sum_j Q[i][j]]
        Đảm bảo với mọi i: tổng tài nguyên loại i trên toàn bộ kệ >= q[i].

    "N" — infeasible (vô nghiệm):
        q[i] > sum_j Q[i][j] với mọi i
        Đảm bảo bài toán chắc chắn không có nghiệm.

    "D" — default (hoàn toàn ngẫu nhiên):
        q[i] ~ Uniform[0, max_resource * m]
        Không đảm bảo tính khả thi.

    Args:
        n:            Số loại sản phẩm.
        m:            Số kệ.
        Q:            Ma trận tài nguyên (n×m, 0-indexed nội bộ).
        max_resource: Số lượng tối đa mỗi kệ chứa một loại sản phẩm.
        feasibility:  "Y" | "N" | "D"

    Returns:
        List độ dài n, mỗi phần tử là nhu cầu của sản phẩm tương ứng.
    """
    max_demand: int = max_resource * m

    match feasibility:
        case "Y":
            return [random.randint(0, sum(Q[i])) for i in range(n)]

        case "N":
            result: list[int] = []
            for i in range(n):
                supply = sum(Q[i])
                lo = supply + 1
                hi = max(lo + 99, max_demand)
                result.append(random.randint(lo, hi))
            return result

        case _:   # "D"
            return [random.randint(0, max_demand) for _ in range(n)]


# === Ghi file .in =============================================================

def write_testcase(
    n: int,
    m: int,
    Q: list[list[int]],
    dist: list[list[int]],
    q: list[int],
    out_path: str,
) -> None:
    """
    Ghi một testcase ra file .in theo định dạng chuẩn.

    Định dạng:
      Dòng 1          : N M
      Dòng 2 .. N+1   : ma trận Q (N hàng, mỗi hàng M số nguyên cách nhau bởi dấu cách)
      Dòng N+2..N+M+2 : ma trận d ((M+1) hàng, mỗi hàng (M+1) số nguyên)
      Dòng N+M+3      : vector q (N số nguyên)

    Args:
        n, m:     Kích thước bài toán.
        Q:        Ma trận tài nguyên (n×m).
        dist:     Ma trận khoảng cách ((m+1)×(m+1)).
        q:        Vector nhu cầu (độ dài n).
        out_path: Đường dẫn file đầu ra (thư mục phải tồn tại).
    """
    lines: list[str] = [f"{n} {m}"]
    for row in Q:
        lines.append(" ".join(map(str, row)))
    for row in dist:
        lines.append(" ".join(map(str, row)))
    lines.append(" ".join(map(str, q)))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_single(
    n: int,
    m: int,
    coord_bound: int | None = None,
    max_resource: int = 100,
    feasibility: str = "Y",
    distribution: str = "uniform",
    out_dir: str | None = None,
    filename: str | None = None,
) -> str:
    """
    Sinh một testcase đơn lẻ và ghi ra file .in.

    Args:
        n:            Số loại sản phẩm (1..50).
        m:            Số kệ (1..1000).
        coord_bound:  Biên tọa độ; nếu None thì mặc định = m * 10.
        max_resource: Số lượng tối đa mỗi kệ chứa một loại sản phẩm.
        feasibility:  "Y" (có nghiệm) | "N" (vô nghiệm) | "D" (ngẫu nhiên).
        distribution: "uniform" | "corner_biased" | "clustered" | "diagonal".
        out_dir:      Thư mục lưu file; nếu None thì lưu vào <project_root>/data/.
        filename:     Tên file; nếu None thì tự động tạo theo timestamp.

    Returns:
        Đường dẫn tuyệt đối của file đã ghi.
    """
    if coord_bound is None:
        coord_bound = m * 10

    Q    = step2_gen_resource_matrix(n, m, max_resource)
    dist = step3_gen_distance_matrix(m, coord_bound, distribution)
    q    = step4_gen_demand(n, m, Q, max_resource, feasibility)

    if out_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "data"))
    os.makedirs(out_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_N{n}_M{m}_{timestamp}.in"

    out_path = os.path.join(out_dir, filename)
    write_testcase(n, m, Q, dist, q, out_path)
    return out_path


# === Main (CLI đơn lẻ) ========================================================

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sinh một testcase .in cho bài toán tìm đường đi tối ưu kho hàng.",
    )
    parser.add_argument("--n", type=int, default=5,
                        help="Số loại sản phẩm N (1..50). Mặc định: 5")
    parser.add_argument("--m", type=int, default=10,
                        help="Số kệ M (1..1000). Mặc định: 10")
    parser.add_argument("--coord-bound", type=int, default=None,
                        help="Biên tọa độ (>= M). Mặc định: M * 10")
    parser.add_argument("--max-resource", type=int, default=100,
                        help="Số lượng tối đa mỗi kệ chứa 1 loại sản phẩm. Mặc định: 100")
    parser.add_argument("--feasibility", choices=["Y", "N", "D"], default="Y",
                        help="Chế độ sinh q: Y=có nghiệm, N=vô nghiệm, D=ngẫu nhiên. Mặc định: Y")
    parser.add_argument("--distribution",
                        choices=["uniform", "corner_biased", "clustered", "diagonal"],
                        default="uniform",
                        help="Kiểu phân bố tọa độ kệ. Mặc định: uniform")
    parser.add_argument("--out-dir", type=str, default=None,
                        help="Thư mục lưu file. Mặc định: <project_root>/data/")
    parser.add_argument("--filename", type=str, default=None,
                        help="Tên file .in. Mặc định: tự động theo timestamp")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    out_path = generate_single(
        n=args.n,
        m=args.m,
        coord_bound=args.coord_bound,
        max_resource=args.max_resource,
        feasibility=args.feasibility,
        distribution=args.distribution,
        out_dir=args.out_dir,
        filename=args.filename,
    )

    feas_label = {"Y": "Có nghiệm (feasible)", "N": "Vô nghiệm (infeasible)", "D": "Hoàn toàn ngẫu nhiên"}
    print(f"Đã tạo file thành công!")
    print(f"  Đường dẫn    : {out_path}")
    print(f"  N={args.n}, M={args.m}")
    print(f"  coord_bound  : {args.coord_bound or args.m * 10}")
    print(f"  max_resource : {args.max_resource}")
    print(f"  feasibility  : {feas_label[args.feasibility]}")
    print(f"  distribution : {args.distribution}")


if __name__ == "__main__":
    main()

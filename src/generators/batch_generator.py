"""
batch_generator.py  —  Sinh hàng loạt testcase .in cho cả val_set lẫn test_set.

Script này định nghĩa "công thức" (recipe) của toàn bộ dataset thực nghiệm
và gọi data_generator.py để sinh ra từng file testcase theo cấu hình đó.

Cách chạy:
    python batch_generator.py

Output:
    data/val_set/   — 39 file .in, dùng cho Phase 1 / Phase 2 / Phase 3
    data/test_set/  — 39 file .in cùng cấu trúc N/M nhưng dữ liệu khác,
                      dùng cho Phase 4 / Phase 5

Mỗi entry trong dataset_recipe là một dict với các key:
    prefix   (str)  — tiền tố tên file, xác định nhóm testcase
    N        (int)  — số loại sản phẩm
    M        (int)  — số kệ
    feas     (str)  — "Y"=có nghiệm | "N"=vô nghiệm | "D"=ngẫu nhiên  (mặc định "Y")
    max_res  (int)  — số lượng tối đa mỗi kệ chứa 1 loại sản phẩm     (mặc định 100)
    dist     (str)  — kiểu phân bố tọa độ kệ                           (mặc định "uniform")

Tên file sinh ra: {prefix}_{idx:02d}_N{N}_M{M}.in
    Ví dụ: small_01_N2_M5.in, edge_sparse_27_N40_M800.in
"""

import os
import random
import sys

# Đảm bảo import được data_generator dù script được gọi từ bất kỳ thư mục nào
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from data_generator import (
    step2_gen_resource_matrix,
    step3_gen_distance_matrix,
    step4_gen_demand,
    write_testcase,
)


# === Hàm sinh dataset =========================================================

def generate_dataset(dataset_name: str, configs: list, skip_existing: bool = False) -> None:
    """
    Sinh toàn bộ một dataset theo danh sách cấu hình và lưu vào thư mục tương ứng.

    Thư mục đầu ra: <project_root>/data/<dataset_name>/
    Tên file: {prefix}_{idx:02d}_N{N}_M{M}.in  (idx đếm từ 1 qua toàn bộ configs)

    Quy trình cho mỗi testcase:
      1. Sinh ma trận tài nguyên Q
      2. Sinh ma trận khoảng cách d (theo kiểu phân bố đã chọn)
      3. Sinh vector nhu cầu q      (theo chế độ feasibility đã chọn)
      4. Áp dụng override đặc biệt nếu là edge_sparse hoặc edge_dense
      5. Ghi ra file .in

    Args:
        dataset_name:  Tên thư mục con bên trong data/  (ví dụ: "val_set", "test_set").
        configs:       Danh sách dict cấu hình testcase (xem module docstring).
        skip_existing: Nếu True, bỏ qua file đã tồn tại — chỉ sinh file mới.
    """
    # Thư mục lưu file: <project_root>/data/<dataset_name>/
    base_dir = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", "data", dataset_name))
    os.makedirs(base_dir, exist_ok=True)

    print(f"\n{'='*52}")
    print(f"  ĐANG SINH TẬP DỮ LIỆU: {dataset_name.upper()}")
    print(f"{'='*52}")

    generated = 0
    skipped = 0

    for idx, conf in enumerate(configs, 1):
        n          = conf["N"]
        m          = conf["M"]
        feasibility = conf.get("feas", "Y")
        max_res    = conf.get("max_res", 100)
        prefix     = conf.get("prefix", "test")
        distribution = conf.get("dist", "uniform")

        filename = f"{prefix}_{idx:02d}_N{n}_M{m}.in"
        out_path = os.path.join(base_dir, filename)

        if skip_existing and os.path.exists(out_path):
            print(f"  [{idx:02d}/{len(configs)}] Bỏ qua (đã tồn tại): {filename}")
            skipped += 1
            continue

        # Không gian kho được nới rộng tỷ lệ thuận với số kệ
        coord_bound = m * 10

        # Sinh các thành phần dữ liệu
        Q    = step2_gen_resource_matrix(n, m, max_res)
        dist = step3_gen_distance_matrix(m, coord_bound, distribution)
        q    = step4_gen_demand(n, m, Q, max_res, feasibility)

        # Override đặc biệt cho edge cases
        if prefix == "edge_sparse":
            # Ép 90% kệ trống rỗng; 10% còn lại chứa rất ít hàng
            for i in range(n):
                for j in range(m):
                    Q[i][j] = 0 if random.random() < 0.90 else random.randint(1, 5)
            # Q đã thay đổi → sinh lại q để đảm bảo vẫn CÓ NGHIỆM
            q = step4_gen_demand(n, m, Q, max_res, "Y")

        elif prefix == "edge_dense":
            # Ép tất cả kệ đều đầy hàng; nhu cầu cực nhỏ so với kho
            for i in range(n):
                for j in range(m):
                    Q[i][j] = random.randint(1000, 5000)
            q = [random.randint(10, 20) for _ in range(n)]

        write_testcase(n, m, Q, dist, q, out_path)
        generated += 1
        print(f"  [{idx:02d}/{len(configs)}] Đã sinh: {filename}")

    print(f"\n  → Sinh mới: {generated} | Bỏ qua: {skipped} | Tổng configs: {len(configs)}")


# === Recipe (công thức dataset) ===============================================

#   Tổng cộng 39 testcase cho mỗi tập.
#   Index (số thứ tự trong tên file) chạy liên tục qua toàn bộ danh sách.
#
#   Nhóm     | Prefix        | Số test | Mục đích
#   ---------|---------------|---------|------------------------------------------
#   small    | small         |   5     | Debug logic bằng tay (M ≤ 20)
#   medium   | medium        |  12     | Đánh giá hiệu năng trung bình
#   large    | large         |   5     | Stress test, ép thuật toán tới giới hạn
#   edge     | edge_N1       |   2     | Chỉ 1 loại sản phẩm (gần TSP)
#   edge     | edge_infeas   |   2     | Guaranteed infeasible
#   edge     | edge_sparse   |   2     | 90% kệ trống (override)
#   edge     | edge_dense    |   2     | Kho đầy, nhu cầu nhỏ (override)
#   dist     | dist_corner   |   3     | Tọa độ tập trung ở góc
#   dist     | dist_cluster  |   3     | Tọa độ theo cụm
#   dist     | dist_diagonal |   3     | Tọa độ theo đường chéo

DATASET_RECIPE = [
    # --- NHÓM 1: SMALL (5 test) ------------------------------------------------
    {"prefix": "small", "N": 2,  "M": 5},
    {"prefix": "small", "N": 3,  "M": 10},
    {"prefix": "small", "N": 5,  "M": 10},
    {"prefix": "small", "N": 5,  "M": 20},
    {"prefix": "small", "N": 10, "M": 20},

    # --- NHÓM 2: MEDIUM (12 test) ----------------------------------------------
    {"prefix": "medium", "N": 10, "M": 50},
    {"prefix": "medium", "N": 10, "M": 100},
    {"prefix": "medium", "N": 15, "M": 100},
    {"prefix": "medium", "N": 15, "M": 150},
    {"prefix": "medium", "N": 20, "M": 150},
    {"prefix": "medium", "N": 20, "M": 200},
    {"prefix": "medium", "N": 25, "M": 200},
    {"prefix": "medium", "N": 25, "M": 250},
    {"prefix": "medium", "N": 30, "M": 250},
    {"prefix": "medium", "N": 30, "M": 300},
    {"prefix": "medium", "N": 35, "M": 300},
    {"prefix": "medium", "N": 35, "M": 400},

    # --- NHÓM 3: LARGE (5 test) ------------------------------------------------
    {"prefix": "large", "N": 40, "M": 500},
    {"prefix": "large", "N": 40, "M": 800},
    {"prefix": "large", "N": 50, "M": 800},
    {"prefix": "large", "N": 50, "M": 1000},
    {"prefix": "large", "N": 50, "M": 1000},   # Chạm trần tuyệt đối (M=1000)

    # --- NHÓM 4: EDGE CASES (8 test) -------------------------------------------
    {"prefix": "edge_N1",     "N": 1,  "M": 300},
    {"prefix": "edge_N1",     "N": 1,  "M": 500},
    {"prefix": "edge_infeas", "N": 20, "M": 100,  "feas": "N"},
    {"prefix": "edge_infeas", "N": 30, "M": 200,  "feas": "N"},
    {"prefix": "edge_sparse", "N": 40, "M": 800},   # Override: 90% kệ trống
    {"prefix": "edge_sparse", "N": 50, "M": 1000},
    {"prefix": "edge_dense",  "N": 40, "M": 500},   # Override: kho đầy, nhu cầu nhỏ
    {"prefix": "edge_dense",  "N": 50, "M": 1000},

    # --- NHÓM 5: DISTRIBUTION (9 test) -----------------------------------------
    {"prefix": "dist_corner",   "N": 15, "M": 150, "dist": "corner_biased"},   # Medium
    {"prefix": "dist_corner",   "N": 30, "M": 300, "dist": "corner_biased"},   # Medium
    {"prefix": "dist_corner",   "N": 50, "M": 800, "dist": "corner_biased"},   # Large
    {"prefix": "dist_cluster",  "N": 15, "M": 150, "dist": "clustered"},       # Medium
    {"prefix": "dist_cluster",  "N": 30, "M": 300, "dist": "clustered"},       # Medium
    {"prefix": "dist_cluster",  "N": 50, "M": 800, "dist": "clustered"},       # Large
    {"prefix": "dist_diagonal", "N": 15, "M": 150, "dist": "diagonal"},        # Medium
    {"prefix": "dist_diagonal", "N": 30, "M": 300, "dist": "diagonal"},        # Medium
    {"prefix": "dist_diagonal", "N": 50, "M": 800, "dist": "diagonal"},        # Large
]


# === Main =====================================================================

if __name__ == "__main__":
    # Sinh tập Validation: dùng để grid search / tune hyperparameter (Phase 1-3)
    # skip_existing=True để không ghi đè file cũ đã có — chỉ bổ sung file mới
    generate_dataset("val_set", DATASET_RECIPE, skip_existing=True)

    # Sinh tập Test: dùng để đánh giá cuối (Phase 4-5)
    # Random state của Python tiếp tục chạy nên sinh ra dữ liệu KHÁC val_set
    # dù cấu trúc N, M hoàn toàn giống nhau
    generate_dataset("test_set", DATASET_RECIPE, skip_existing=True)

    print("\n✅ HOÀN TẤT! Kiểm tra thư mục 'data/val_set' và 'data/test_set'.")
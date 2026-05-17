# CONTEXT.md — Warehouse Order Picking Optimization

> File này tổng hợp toàn bộ thông tin về project. Đọc file này trước khi làm việc với bất kỳ phần nào của codebase. Mỗi khi cập nhật 1 thông tin quan trọng cần cho lần đọc tiếp theo, tự động cập nhật file này.

---

## 1. Bài toán (Problem Statement)

**Order Picking Route in Warehouse** (Đại học Bách Khoa Hà Nội)

Một kho hàng có **M kệ** (đánh số 1..M) và **N loại sản phẩm** (đánh số 1..N).

- `Q[i][j]` = số lượng sản phẩm loại `i` được lưu tại kệ `j`
- `q[i]` = tổng số sản phẩm loại `i` mà nhân viên cần thu gom cho đơn hàng
- `d(i, j)` = khoảng cách di chuyển từ điểm `i` đến điểm `j` (0 = cửa kho, 1..M = kệ)

Nhân viên xuất phát từ **cửa kho (điểm 0)**, chọn một chuỗi kệ để ghé thăm (mỗi kệ **tối đa một lần**), thu gom đủ số lượng từng loại sản phẩm theo đơn hàng, rồi **quay lại cửa kho**.

**Mục tiêu:** Tối thiểu hóa **tổng quãng đường di chuyển**.

### Ràng buộc bài toán
- `1 <= N <= 50` (số loại sản phẩm)
- `1 <= M <= 1000` (số kệ hàng)
- Mỗi kệ chỉ được ghé thăm **tối đa 1 lần**
- Phải thu gom **đủ** `q[i]` cho mọi loại sản phẩm `i`
- Không bắt buộc phải thăm toàn bộ kệ (chỉ cần đủ hàng là dừng)

### Lưu ý quan trọng
- **Infeasible instance**: Nếu `sum_j Q[i][j] < q[i]` với một số `i` thì bài toán vô nghiệm.
  Đây là edge case được thiết kế có chủ đích trong dataset.
- Lời giải là **tập con có thứ tự** của các kệ, không phải hoán vị toàn bộ M kệ.

### Contract chung cho mọi solver
- Tất cả các thuật toán phải có **điều kiện dừng theo `time_limit`**.
- Giá trị trả về chuẩn của solver là:
  - `route`: thứ tự các kho/kệ hàng được thăm
  - `total_distance`: độ dài quãng đường
  - `t_best`: thời gian từ lúc bắt đầu chạy đến lúc tìm được nghiệm tốt nhất trong `time_limit`
- Nếu input **vô nghiệm** thì quy ước trả về là:
  - `route = []`
  - `total_distance = -1`
  - `t_best = -1`

---

## 2. Định dạng file dữ liệu (.in)

```
Dòng 1          : N M
Dòng 2 .. N+1   : N hàng của ma trận Q (mỗi hàng M số nguyên, cách bởi dấu cách)
Dòng N+2..N+M+2 : (M+1) hàng của ma trận khoảng cách d  ((M+1) x (M+1) số)
Dòng N+M+3      : N số nguyên q[1], q[2], ..., q[N]
```

**Quy ước index trong code (mixed indexing):**
- `Q[i][j]`: i=1..N (sản phẩm), j=1..M (kệ) — Q[0] và Q[i][0] là hàng/cột giả
- `d[i][j]`: i,j=0..M — `d[0]` là cửa kho (point 0), `d[1..M]` là các kệ
- `q[i]`: i=1..N — q[0] là phần tử giả

**Ví dụ tên file:** `medium_06_N10_M50.in`, `edge_sparse_27_N40_M800.in`

---

## 3. Cấu trúc thư mục

```
warehouse-order-picking-optimization/
├── data/
│   ├── val_set/           (39 file .in: dùng để tune tham số – Grid Search)
│   └── test_set/          (39 file .in: dùng để so sánh cuối cùng – fair comparison)
├── config/
│   └── settings.py            (cấu hình hệ thống: TIME_LIMIT_TESTING, runs)
├── src/
│   ├── generators/
│   │   ├── data_generator.py       (sinh 1 file .in qua CLI tương tác)
│   │   ├── batch_generator.py      (sinh toàn bộ val_set + test_set theo recipe)
│   │   └── DATA_GENERATOR_NOTE.md  (tài liệu chi tiết về data_generator v2.0.0)
│   └── solvers/
│       ├── utils.py                          (read_input, evaluator, validator)
│       ├── greedy.py                         (Greedy heuristic)
│       ├── greedy_pruning_pywrapcp.py        (Greedy + Pruning + GLS)
│       ├── genetic_algorithm.py              (Genetic Algorithm – TODO)
│       ├── OR_Tools_cp_sat.py                (Exact solver CP-SAT)
│       └── simulated_annealing/
│           ├── adaptive_simulated_annealing.py  (Adaptive Simulated Annealing)
│           ├── phase1.py                        (Batch runner cho Phase 1 của ASA)
│           └── ALGORITHM_DESCRIPTION.md         (Mô tả chi tiết thuật toán ASA)
├── notebooks/
│   ├── tuning/
│   │   ├── simulated_annealing_tuning.ipynb
│   │   └── genetic_algorithm_tuning.ipynb
│   └── final_evaluation.ipynb
├── results/
│   ├── phase1/         (kết quả representative long-run để chọn time limit chuẩn)
│   ├── phase2/         (cost reference cho val_set)
│   ├── phase3/         (kết quả tuning hyperparameter)
│   ├── phase4/         (cost reference cho test_set)
│   └── phase5/         (kết quả đánh giá cuối cùng)
├── requirements.txt
├── README.md
└── context.md          (file này)
```

---

## 4. Các thuật toán

### 4.1 Greedy (greedy.py)
**Loại:** Constructive Heuristic
**Ý tưởng:** Mỗi bước chọn kệ chưa thăm có tỷ lệ (hàng hữu ích / khoảng cách) tốt nhất.

```
score(j) = d[cur][j] / useful_amount(j)  -- càng nhỏ càng tốt
useful_amount(j) = Σ_i min(Q[i][j], còn_cần[i])
```

Dừng khi đủ hàng hoặc không còn kệ có ích. Không có tham số tune.

### 4.2 Greedy + Pruning + pywrapcp (greedy_pruning_pywrapcp.py)
**Loại:** Heuristic + Local Search | Pipeline 3 bước:
1. Greedy → lộ trình ban đầu
2. Pruning (duyệt ngược) → loại kệ thừa không ảnh hưởng khả thi
3. OR-Tools pywrapcp (Guided Local Search) → tối ưu thứ tự kệ đã chọn

**Tham số tune:** Dừng theo `time_limit`; khi chạy Phase 1 dùng `TIME_LIMIT_TESTING` trong `config/settings.py`.

### 4.3 Adaptive Simulated Annealing (adaptive_simulated_annealing.py)
**Loại:** Metaheuristic (Nâng cấp từ SA gốc)
**Biểu diễn nghiệm:** Hoán vị đầy đủ M kệ. `evaluate_route()` chuyển permutation → route.
**Hàm lân cận (ALNS):** Swap, Insert, 2-Opt với cơ chế cập nhật trọng số động.
**Điều kiện dừng:** Dựa trên `time_limit`; riêng Phase 1 lấy giá trị từ `TIME_LIMIT_TESTING` theo kích thước testcase.

**Tham số tune (val_set):**
| Tham số | Ý nghĩa | Mặc định tune |
|---|---|---|
| alpha | Hệ số làm lạnh cơ sở | 0.99, 0.995, 0.999 |
| max_no_improve | Vòng không cải thiện để Re-anneal | 1000, 2000, 3000 |
| reheat_ratio | Tỷ lệ phục hồi nhiệt | 0.2, 0.3, 0.5 |

### 4.4 Genetic Algorithm (genetic_algorithm.py)
**Loại:** Metaheuristic | **Trạng thái: TODO – chưa implement**

### 4.5 OR-Tools CP-SAT (OR_Tools_cp_sat.py)
**Loại:** Solver dựa trên mô hình exact (CP-SAT)
**Mô hình:** Biến nhị phân x[j] + arc[i][j] + AddCircuit → chu trình Hamiltonian.
**Ràng buộc:** Σ_j Q[i][j]*x[j] >= q[i] với mọi i.
**Tham số:** max_time_in_seconds = theo `time_limit` được truyền cho solver.
**Lưu ý:** Vì implementation hiện tại vẫn chạy với time limit, CP-SAT có thể trả về nghiệm `FEASIBLE` trước khi chứng minh tối ưu. Do đó không phải mọi lần chạy đều là nghiệm tối ưu tuyệt đối.

---

## 5. Dataset – Phân nhóm test cases

Cả val_set và test_set đều có **39 file** (cùng cấu trúc N/M, số liệu khác hoàn toàn).

**Phân nhóm theo M** (M quyết định độ phức tạp tính toán):
- **Small:** M ≤ 20
- **Medium:** 50 ≤ M ≤ 400
- **Large:** M ≥ 500

| Nhóm | Số test | N/M | Mục đích |
|---|---|---|---|
| small_01..05 | 5 | N=2..10, M=5..20 | Debug logic bằng tay |
| medium_06..17 | 12 | N=10..35, M=50..400 | Đánh giá hiệu năng trung bình |
| large_18..22 | 5 | N=40..50, M=500..1000 | Stress test |
| edge_N1_23..24 | 2 | N=1, M=300/500 | 1 sản phẩm (gần TSP) |
| edge_infeas_25..26 | 2 | N=20..30, M=100..200 | Guaranteed infeasible |
| edge_sparse_27..28 | 2 | N=40..50, M=800..1000 | 90% kệ trống |
| edge_dense_29..30 | 2 | N=40..50, M=500..1000 | Kho đầy, nhu cầu nhỏ |
| dist_corner_31..33 | 3 | N=15..50, M=150..800 | Tọa độ tập trung ở 4 góc |
| dist_cluster_34..36 | 3 | N=15..50, M=150..800 | Tọa độ chia thành K cụm |
| dist_diagonal_37..39 | 3 | N=15..50, M=150..800 | Tọa độ dọc đường chéo chính |

**Cách batch_generator tạo edge cases:**
- edge_sparse: Override 90% Q[i][j]=0, còn lại randint(1,5); sinh lại q với feasibility="Y"
- edge_dense: Override Q[i][j]=randint(1000,5000); q=randint(10,20)
- edge_infeas: feasibility="N" → q[i] > total_supply → guaranteed infeasible

**Cách batch_generator tạo distribution cases:**
- dist_corner: `step3_gen_distance_matrix(m, coord_bound, distribution="corner_biased")`
- dist_cluster: `step3_gen_distance_matrix(m, coord_bound, distribution="clustered")`
- dist_diagonal: `step3_gen_distance_matrix(m, coord_bound, distribution="diagonal")`

---

## 6. Workflow thực nghiệm

```
batch_generator.py
  → sinh val_set/ và test_set/
      ↓
PHASE 1: TÌM TIME LIMIT CHUẨN
  - Chọn representative cases từ các folder hiện có trong results/phase1/
  - Chạy mỗi thuật toán với cấu hình siêu tham số mặc định trên các testcase đại diện này
  - Dùng TIME_LIMIT_TESTING theo kích thước testcase:
      + small: M <= 20
      + medium: 50 <= M <= 400
      + large: M >= 500
  - Quan sát điểm bão hòa để chốt time budget hợp lý cho từng nhóm testcase
  - Output mỗi thuật toán trên mỗi testcase:
      + results/phase1/<testcase>/<algorithm>.json
      + các field gồm: route, total_distance, t_best, time_limit, hyperparameters
      + nếu thuật toán không có hyperparameter thì hyperparameters = {}
      + ASA dùng src/solvers/simulated_annealing/phase1.py để sinh asa.json
      ↓
PHASE 2: FIND BEST KNOWN SOLUTION (BFS) CHO val_set
  - Mục đích: tạo cost reference cho toàn bộ val_set
  - Với small case: dùng nghiệm của OR-Tools CP-SAT làm cost reference
  - Với testcase còn lại: chạy tất cả cấu hình của tất cả thuật toán để lấy BFS_Cost
  - Với thuật toán ngẫu nhiên: mỗi cấu hình chạy k = 10 seed (0..9), chỉ giữ kết quả tốt nhất
  - Output lưu dưới dạng file ở results/phase2/
      ↓
PHASE 3: HYPERPARAMETER TUNING (val_set)
  - Xét từng cấu hình trong lưới siêu tham số của từng thuật toán có tune
  - Nếu thuật toán ngẫu nhiên: mỗi cấu hình chạy k = 10 seed (0..9) trên mỗi testcase
  - Tính min_cost cho từng testcase
  - Dùng cost reference từ Phase 2 để tính RFD
  - Tính avg_RFD trên toàn bộ val_set
  - Chọn cấu hình có avg_RFD nhỏ nhất
  - Output lưu tại results/phase3/<algorithm>.csv
      ↓ bộ tham số tốt nhất
PHASE 4: FIND BEST KNOWN SOLUTION (BFS) CHO test_set
  - Tạo cost reference cho toàn bộ test_set
  - Với small case: dùng nghiệm của OR-Tools CP-SAT
  - Với testcase còn lại: chạy tất cả cấu hình của tất cả thuật toán
  - Với thuật toán ngẫu nhiên: mỗi cấu hình chạy k = 10 seed (0..9), chỉ giữ kết quả tốt nhất
  - Output lưu tại results/phase4/
      ↓
PHASE 5: FINAL EVALUATION
  - Chạy từng thuật toán với cấu hình tốt nhất đã chọn ở Phase 3 trên test_set
  - Với thuật toán ngẫu nhiên: mỗi testcase chạy k = 10 seed (0..9)
  - Tính các metric:
      + min_cost, max_cost, avg_cost, std_cost
      + avg_t_best
      + RFD cho từng testcase
      + avg_RFD theo nhóm testcase và overall
  - Output:
      + results/phase5/evaluation_details.csv
      + results/phase5/summary.csv
```

---

## 7. Hàm utils.py

### read_input(stream=None) -> (N, M, Q, d, q)
Đọc dữ liệu từ stdin hoặc file stream. Trả về theo quy ước 1-based.

### evaluator(route, N, M, Q, d, q) -> dict
Đánh giá chất lượng lời giải. Output dict:
- total_distance: tổng khoảng cách (cửa → route → cửa)
- is_valid: route thu đủ hàng không?
- is_infeasible: bài toán vô nghiệm từ đầu không?
- collected, shortage, errors: chi tiết từng sản phẩm

### compute_route_distance(route, d) -> int
Tính nhanh khoảng cách không cần đánh giá đầy đủ.

### validator(N, M, Q, d, q) -> dict
Kiểm tra tính hợp lệ của input data.
- is_valid: không có lỗi ràng buộc cứng
- is_feasible: bài toán có thể có nghiệm không
- errors, warnings

---

## 8. Cách chạy

```bash
# Chạy solver độc lập (từ src/solvers/)
python greedy.py < ../../data/val_set/small_01_N2_M5.in
python simulated_annealing/adaptive_simulated_annealing.py < ../../data/val_set/medium_06_N10_M50.in
python OR_Tools_cp_sat.py < ../../data/val_set/small_01_N2_M5.in
python simulated_annealing/phase1.py

# Sinh dữ liệu (từ src/generators/)
python data_generator.py     # CLI tương tác
python batch_generator.py    # Sinh toàn bộ val_set + test_set
```

```python
# Dùng trong notebook (từ notebooks/tuning/)
import sys
sys.path.insert(0, '../../src/solvers')
from utils import read_input, evaluator, validator

with open('../../data/val_set/small_01_N2_M5.in') as f:
    N, M, Q, d, q = read_input(f)

result = evaluator(route=[3, 1], N=N, M=M, Q=Q, d=d, q=q)
print(result['total_distance'], result['is_valid'])
```

---

## 9. Dependencies

```
ortools   (CP-SAT và pywrapcp)
Python >= 3.11
```

---

## 10. Trạng thái hiện tại

| Hạng mục | Trạng thái |
|---|---|
| data_generator.py | ✅ Hoàn thiện (v2.0.0) |
| batch_generator.py | ✅ Hoàn thiện |
| greedy.py | ✅ Implement xong |
| greedy_pruning_pywrapcp.py | ✅ Implement xong |
| adaptive_simulated_annealing.py (ASA) | ✅ Implement xong |
| simulated_annealing/phase1.py | ✅ Implement xong |
| genetic_algorithm.py | ❌ Chưa implement |
| OR_Tools_cp_sat.py | ✅ Implement xong (exact solver) |
| utils.py (evaluator, validator) | ✅ Implement xong |
| Phase 2 cost reference script | ⬜ Chưa implement (TODO) |
| Phase 3 tuning script/notebook | ⬜ Chưa điền code |
| Phase 4 cost reference script | ⬜ Chưa implement (TODO) |
| Phase 5 final evaluation script/notebook | ⬜ Chưa điền code |

---

*Cập nhật lần cuối: 2026-05-16*

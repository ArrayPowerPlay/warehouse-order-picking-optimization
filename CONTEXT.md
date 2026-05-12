# context.md — Warehouse Order Picking Optimization

> File này tổng hợp toàn bộ thông tin về project. Đọc file này trước khi làm việc với bất kỳ phần nào của codebase.

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

---

## 2. Định dạng file dữ liệu (.in)

```
Dòng 1          : N M
Dòng 2 .. N+1   : N hàng của ma trận Q (mỗi hàng M số nguyên, cách bởi dấu cách)
Dòng N+2..N+M+2 : (M+1) hàng của ma trận khoảng cách d  ((M+1) x (M+1) số)
Dòng N+M+3      : N số nguyên q[1], q[2], ..., q[N]
```

**Quy ước index trong code (1-based):**
- `Q[i][j]`: i=1..N (sản phẩm), j=1..M (kệ) — Q[0] và Q[i][0] là hàng/cột giả
- `d[i][j]`: i,j=0..M — d[0] là cửa kho (point 0)
- `q[i]`: i=1..N — q[0] là phần tử giả

**Ví dụ tên file:** `medium_06_N10_M50.in`, `edge_sparse_27_N40_M800.in`

---

## 3. Cấu trúc thư mục

```
warehouse-order-picking-optimization/
├── data/
│   ├── val_set/           (30 file .in: dùng để tune tham số – Grid Search)
│   └── test_set/          (30 file .in: dùng để so sánh cuối cùng – fair comparison)
├── src/
│   ├── generators/
│   │   ├── data_generator.py       (sinh 1 file .in qua CLI tương tác)
│   │   ├── batch_generator.py      (sinh toàn bộ val_set + test_set theo recipe)
│   │   └── DATA_GENERATOR_NOTE.md  (tài liệu chi tiết về data_generator v2.0.0)
│   └── solvers/
│       ├── utils.py                    (read_input, evaluator, validator)
│       ├── greedy.py                   (Greedy heuristic)
│       ├── greedy_pruning_pywrapcp.py  (Greedy + Pruning + GLS)
│       ├── simulated_annealing.py      (Simulated Annealing)
│       ├── genetic_algorithm.py        (Genetic Algorithm – TODO)
│       └── OR_Tools_cp_sat.py          (Exact solver CP-SAT)
├── notebooks/
│   ├── tuning/
│   │   ├── simulated_annealing_tuning.ipynb
│   │   └── genetic_algorithm_tuning.ipynb
│   └── final_evaluation.ipynb
├── results/
│   ├── val_results/    (kết quả Grid Search từng thuật toán)
│   └── test_results/   (kết quả so sánh cuối cùng)
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

**Tham số tune:** `time_limit.seconds` (hiện = 2s)

### 4.3 Simulated Annealing (simulated_annealing.py)
**Loại:** Metaheuristic
**Biểu diễn nghiệm:** Hoán vị đầy đủ M kệ. `evaluate_route()` chuyển permutation → route thực tế.
**Hàm lân cận:** Swap ngẫu nhiên 2 vị trí trong permutation.
**Điều kiện dừng:** temp < 0.001 HOẶC no_improve_cnt >= max_num_improves.

**Tham số tune (val_set):**
| Tham số | Ý nghĩa | Mặc định |
|---|---|---|
| T_start | Nhiệt độ ban đầu | 1000.0 |
| alpha | Hệ số làm lạnh | 0.9995 |
| max_num_improves | Số vòng không cải thiện → dừng | 5000 |

### 4.4 Genetic Algorithm (genetic_algorithm.py)
**Loại:** Metaheuristic | **Trạng thái: TODO – chưa implement**

### 4.5 OR-Tools CP-SAT (OR_Tools_cp_sat.py)
**Loại:** Exact Solver
**Mô hình:** Biến nhị phân x[j] + arc[i][j] + AddCircuit → chu trình Hamiltonian.
**Ràng buộc:** Σ_j Q[i][j]*x[j] >= q[i] với mọi i.
**Tham số:** max_time_in_seconds = 2.0

---

## 5. Dataset – Phân nhóm test cases

Cả val_set và test_set đều có 30 file (cùng cấu trúc N/M, số liệu khác hoàn toàn).

| Nhóm | Số test | N/M | Mục đích |
|---|---|---|---|
| small_01..05 | 5 | N=2..10, M=5..20 | Debug logic bằng tay |
| medium_06..17 | 12 | N=10..35, M=50..400 | Đánh giá hiệu năng trung bình |
| large_18..22 | 5 | N=40..50, M=500..1000 | Stress test |
| edge_N1_23..24 | 2 | N=1, M=300/500 | 1 sản phẩm (gần TSP) |
| edge_infeas_25..26 | 2 | N=20..30, M=100..200 | Guaranteed infeasible |
| edge_sparse_27..28 | 2 | N=40..50, M=800..1000 | 90% kệ trống |
| edge_dense_29..30 | 2 | N=40..50, M=500..1000 | Kho đầy, nhu cầu nhỏ |

**Cách batch_generator tạo edge cases:**
- edge_sparse: Override 90% Q[i][j]=0, còn lại randint(1,5); sinh lại q với feasibility="Y"
- edge_dense: Override Q[i][j]=randint(1000,5000); q=randint(10,20)
- edge_infeas: feasibility="N" → q[i] > total_supply → guaranteed infeasible

---

## 6. Workflow thực nghiệm

```
batch_generator.py
  → sinh val_set/ và test_set/
      ↓
PHASE 1: TUNING (val_set)
  notebooks/tuning/*.ipynb
  → Grid Search tham số
  → Lưu kết quả vào results/val_results/
      ↓ bộ tham số tốt nhất
PHASE 2: FINAL EVAL (test_set)
  notebooks/final_evaluation.ipynb
  → So sánh công bằng tất cả thuật toán
  → Lưu vào results/test_results/
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
python simulated_annealing.py < ../../data/val_set/medium_06_N10_M50.in
python OR_Tools_cp_sat.py < ../../data/val_set/small_01_N2_M5.in

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
| simulated_annealing.py | ✅ Implement xong – cần tune tham số |
| genetic_algorithm.py | ❌ Chưa implement |
| OR_Tools_cp_sat.py | ✅ Implement xong (exact solver) |
| utils.py (evaluator, validator) | ✅ Implement xong |
| Notebook SA tuning | ⬜ Chưa điền code |
| Notebook GA tuning | ⬜ Chưa điền code |
| Notebook final evaluation | ⬜ Chưa điền code |

---

*Cập nhật lần cuối: 2026-04-11*

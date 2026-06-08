# CONTEXT.md — Warehouse Order Picking Optimization

> File này tổng hợp thông tin cốt lõi về project, workflow thực nghiệm, và các quyết định phương pháp luận đang áp dụng. Khi logic thực nghiệm thay đổi, cập nhật file này trước.

---

## 1. Bài toán

**Order Picking Route in Warehouse** (Đại học Bách Khoa Hà Nội)

Một kho hàng có `M` kệ và `N` loại sản phẩm.

- `Q[i][j]`: số lượng sản phẩm loại `i` tại kệ `j`
- `q[i]`: nhu cầu cần lấy của sản phẩm `i`
- `d(i, j)`: khoảng cách từ điểm `i` đến điểm `j`

Nhân viên xuất phát từ cửa kho `0`, thăm một dãy kệ, lấy đủ hàng, rồi quay lại cửa kho.

**Mục tiêu:** tối thiểu hóa tổng quãng đường di chuyển.

### Ràng buộc

- `1 <= N <= 50`
- `1 <= M <= 1000`
- Mỗi kệ được ghé tối đa một lần
- Phải thu gom đủ `q[i]` với mọi `i`
- Không cần thăm toàn bộ kệ

### Quy ước infeasible

Nếu tồn tại `i` sao cho `sum_j Q[i][j] < q[i]` thì bài toán vô nghiệm.

Khi solver gặp input vô nghiệm:

- `route = []`
- `total_distance = -1`
- `t_best = -1`

### Contract chung cho solver

Mọi solver phải hỗ trợ `time_limit` và trả về:

- `route`
- `total_distance`
- `t_best`

---

## 2. Định dạng file `.in`

```text
Dòng 1          : N M
Dòng 2 .. N+1   : N hàng của ma trận Q
Dòng N+2..N+M+2 : (M+1) hàng của ma trận khoảng cách d
Dòng N+M+3      : N số nguyên q[1], q[2], ..., q[N]
```

### Quy ước index trong code

- `Q[i][j]`: `i = 1..N`, `j = 1..M`
- `d[i][j]`: `i, j = 0..M`
- `q[i]`: `i = 1..N`

Ví dụ tên file:

- `medium_06_N10_M50.in`
- `edge_sparse_27_N40_M800.in`

---

---

## 3. Thuật toán hiện có

### 3.1 Greedy

**Thư mục:** `src/solvers/greedy/`

**Loại:** Constructive heuristic

Ý tưởng: ở mỗi bước chọn kệ có tỷ lệ `distance / useful_amount` tốt nhất.

Không có hyperparameter để tune.

### 3.2 Greedy + Pruning + pywrapcp

**Thư mục:** `src/solvers/greedy_prunning_pywrapcp/`

Pipeline:

1. Greedy chọn route ban đầu
2. Pruning loại kệ thừa
3. `pywrapcp` tối ưu lại thứ tự route

Không có lưới hyperparameter; chỉ phụ thuộc `time_limit`.

### 3.3 CP-SAT

**Thư mục:** `src/solvers/cp_sat/`

**Loại:** exact solver theo time limit

Lưu ý:

- Có thể trả về nghiệm tốt nhất tìm được trong giới hạn thời gian
- Không phải lúc nào cũng chứng minh tối ưu tuyệt đối nếu hết `time_limit`

### 3.4 Adaptive Simulated Annealing

**Thư mục:** `src/solvers/simulated_annealing/`

**Loại:** metaheuristic

Hyperparameter grid hiện tại:

| Tham số | Giá trị |
|---|---|
| `alpha` | `0.99`, `0.995`, `0.999` |
| `max_no_improve` | `1000`, `2000` |
| `reheat_ratio` | `0.2`, `0.3`, `0.5` |

### 3.5 Genetic Algorithm

**Thư mục:** `src/solvers/genetic_algorithm/`

**Triển khai:** Python wrapper + C++ core

Hyperparameter grid hiện tại:

| Tham số | Giá trị |
|---|---|
| `pop_size` | `100`, `200` |
| `crossover_rate` | `0.7`, `0.8`, `0.9` |
| `mutation_rate` | `0.05`, `0.1`, `0.2` |

### 3.6 Ant Colony Optimization

**Thư mục:** `src/solvers/ant_colony/`

**Triển khai:** Python wrapper + C++ core

Hyperparameter grid hiện tại:

| Tham số | Giá trị |
|---|---|
| `num_ants` | `50`, `100` |
| `alpha` | `1.0`, `2.0` |
| `beta` | `2.0`, `3.0`, `4.0` |
| `rho` | `0.1` |

---

## 4. Dataset và phân nhóm testcase

Cả `val_set` và `test_set` đều có 39 file.

### Nhóm theo `M`

- `small`: `M <= 20`
- `medium`: `50 <= M <= 400`
- `large`: `M >= 500`

### Các họ testcase

| Nhóm | Số test | N/M | Mục đích |
|---|---|---|---|
| `small_01..05` | 5 | N=2..10, M=5..20 | Debug logic |
| `medium_06..17` | 12 | N=10..35, M=50..400 | Đánh giá trung bình |
| `large_18..22` | 5 | N=40..50, M=500..1000 | Stress test |
| `edge_N1_23..24` | 2 | N=1, M=300/500 | Gần TSP |
| `edge_infeas_25..26` | 2 | N=20..30, M=100..200 | Guaranteed infeasible |
| `edge_sparse_27..28` | 2 | N=40..50, M=800..1000 | 90% kệ trống |
| `edge_dense_29..30` | 2 | N=40..50, M=500..1000 | Kho dày |
| `dist_corner_31..33` | 3 | N=15..50, M=150..800 | Tọa độ ở góc |
| `dist_cluster_34..36` | 3 | N=15..50, M=150..800 | Tọa độ theo cụm |
| `dist_diagonal_37..39` | 3 | N=15..50, M=150..800 | Tọa độ theo đường chéo |

---

## 5. Cấu hình thực nghiệm hiện tại

Từ `config/settings.py`:

- `TIME_LIMIT_TESTING`
  - `small = 30.0`
  - `medium = 600.0`
  - `large = 900.0`
- `TIME_LIMITS`
  - `small = 18.0`
  - `medium = 400.0`
  - `large = 700.0`
- `SEEDS = [0, 1, 2]`
- `NUM_RUNS_PER_CONFIG = 3`

Lưu ý:

- Repo hiện tại đang chạy thực tế với `k = len(SEEDS) = 3`


---

## 6. Workflow thực nghiệm

```text
batch_generator.py
  -> sinh val_set/ và test_set/
      ↓
PHASE 1: CHỌN TIME LIMIT
  - Chạy representative cases
  - Quan sát saturation của từng thuật toán
  - Lưu JSON theo từng testcase/algorithm
      ↓
PHASE 2: BUILD COST REFERENCE CHO val_set
  - Mục tiêu: tạo best-known cost reference
  - Small: ưu tiên CP-SAT làm mốc
  - Medium/large: gom kết quả từ nhiều thuật toán/cấu hình
  - Với metaheuristic: chạy nhiều seed, lấy cost_min cho từng (testcase, cấu hình)
  - Aggregator lấy min giữa các thuật toán để tạo cost_reference theo testcase
      ↓
PHASE 3: HYPERPARAMETER TUNING TRÊN val_set
  - Mục tiêu: chọn cấu hình tốt nhất theo hiệu năng kỳ vọng, không theo run may mắn
  - Với mỗi (testcase, cấu hình), chạy nhiều seed
  - Tính ít nhất: min_cost, avg_cost, std_cost, avg_t_best
  - Dùng avg_cost để tính RPD theo cost_reference của Phase 2
  - Chọn cấu hình có avg_RPD nhỏ nhất theo từng nhóm kích thước
  - Tie-break khuyến nghị: std_RPD nhỏ hơn, rồi avg_t_best nhỏ hơn
      ↓
PHASE 4: BUILD COST REFERENCE CHO test_set
  - Mục tiêu: tạo best-known cost reference cho đánh giá cuối
  - Với metaheuristic:
    - Dùng best config theo từng group đã chọn từ Phase 3
    - Chạy nhiều seed trên test_set
    - Lưu detail per-seed gồm ít nhất: cost, t_best
    - Build summary per testcase gồm: cost_min, cost_max, cost_avg, cost_std, t_best_avg
  - Với greedy / pywrapcp / CP-SAT:
    - Chạy trực tiếp trên test_set theo pipeline riêng của từng solver
  - Aggregator lấy min giữa các thuật toán để tạo cost_reference theo testcase
      ↓
PHASE 5: FINAL EVALUATION
  - Dùng cost_reference đã build từ Phase 4
  - Gộp summary của tất cả thuật toán theo từng testcase
  - Chạy result_aggregator_phase5.py để tạo kết quả tổng hợp chi tiết results/phase5/aggregate_result.csv
  - Chạy result_summary_phase5.py để tạo kết quả summary theo group và overall results/phase5/summary.csv
```

### Quy ước phương pháp luận

- **Phase 2/4** là pha xây `cost_reference`, nên dùng `cost_min` là đúng mục tiêu
- **Phase 3** là pha chọn hyperparameter, nên không nên xếp hạng cấu hình bằng `cost_min`
- Nếu Final Evaluation báo cáo `avg_cost/std_cost`, thì Tuning cũng phải dựa trên `avg_cost` để nhất quán
- Ở **Phase 5**, đối tượng được đánh giá cho mỗi metaheuristic là policy:
  - `small -> best_config_small`
  - `medium -> best_config_medium`
  - `large -> best_config_large`
- Vì vậy metric `overall` vẫn hợp lệ nếu được tính trên toàn bộ testcase test_set, dù mỗi group có thể dùng cấu hình khác nhau

---

## 7. Hướng chọn tham số đúng chuẩn cho Phase 3

Đây là hướng khuyến nghị cho mọi metaheuristic như ASA, GA, ACO.

### Mục tiêu

Chọn cấu hình có hiệu năng **tốt trung bình** và **ổn định**, không phải cấu hình có một lần chạy may mắn nhất.

### Quy trình

1. Giữ nguyên `cost_reference` của Phase 2.
2. Với mỗi `(testcase, configuration)`, chạy `k` seed độc lập.
3. Lưu raw result theo seed hoặc ít nhất lưu:
   - `min_cost`
   - `avg_cost`
   - `std_cost`
   - `avg_t_best`
4. Tính:
   - `RPD_case = ((avg_cost - cost_reference) / cost_reference) * 100`
5. Với mỗi configuration, lấy trung bình `RPD_case` trên toàn bộ testcase trong cùng group:
   - `avg_RPD_group`
6. Chọn configuration có `avg_RPD_group` nhỏ nhất.
7. Tie-break:
   - `std_RPD_group nhỏ hơn`
   - `avg_t_best_group nhỏ hơn`

### Không nên làm

- Không dùng `cost_min` để xếp hạng cấu hình ở Phase 3 nếu Phase 5 báo cáo theo `avg_cost`
- Không chọn tham số theo single best run rồi sau đó lại kết luận bằng thống kê trung bình

### Khi nào cần rerun

- Nếu chỉ đổi logic tuning từ `cost_min` sang `avg_cost`:
  - Cần rerun `Phase 3`
  - Nên rerun `Phase 5`
  - Không bắt buộc rerun `Phase 2` và `Phase 4`
- Nếu đổi cả số lượng seed hoặc muốn thay lại `cost_reference`:
  - Cần rerun thêm `Phase 2` và `Phase 4`

---

## 8. Hàm dùng chung trong `utils.py`

### `read_input(stream=None) -> (N, M, Q, d, q)`

Đọc input theo quy ước 1-based.

### `evaluator(route, N, M, Q, d, q) -> dict`

Đánh giá lời giải:

- `total_distance`
- `is_valid`
- `is_infeasible`
- `collected`
- `shortage`
- `errors`

### `compute_route_distance(route, d) -> int`

Tính tổng distance của route.

### `validator(N, M, Q, d, q) -> dict`

Kiểm tra hợp lệ của input.

---

## 9. Trạng thái hiện tại

| Hạng mục | Trạng thái |
|---|---|
| `data_generator.py` | ✅ Hoàn thiện |
| `batch_generator.py` | ✅ Hoàn thiện |
| Greedy | ✅ Implement xong |
| Greedy + Pruning + pywrapcp | ✅ Implement xong |
| ASA core | ✅ Implement xong |
| ASA Phase 1 | ✅ Implement xong |
| ASA Phase 2 | ✅ Implement xong |
| ASA Phase 2 summary | ✅ Implement xong |
| ASA Phase 3 | ✅ Implement xong, tune theo `avg_cost -> avg_RPD` |
| ASA Phase 4 detail | ✅ Implement xong |
| ASA Phase 4 summary | ✅ Implement xong |
| GA core + wrapper | ✅ Implement xong |
| GA Phase 1 | ✅ Implement xong |
| GA Phase 2 | ✅ Implement xong |
| GA Phase 2 summary | ✅ Implement xong |
| GA Phase 3 | ✅ Implement xong, tune theo `avg_cost -> avg_RPD` |
| GA Phase 4 detail | ✅ Implement xong |
| GA Phase 4 summary | ✅ Implement xong |
| ACO core + wrapper | ✅ Implement xong |
| ACO Phase 1 | ✅ Implement xong |
| ACO Phase 2 | ✅ Implement xong |
| ACO Phase 2 summary | ✅ Implement xong |
| ACO Phase 3 | ✅ Implement xong, tune theo `avg_cost -> avg_RPD` |
| ACO Phase 4 detail | ✅ Implement xong |
| ACO Phase 4 summary | ✅ Implement xong |
| CP-SAT core | ✅ Implement xong |
| CP-SAT Phase 1 | ✅ Implement xong |
| CP-SAT Phase 2 | ✅ Có cho `val_set` small/medium |
| CP-SAT Phase 4 | ✅ Có script cho `test_set` small/medium |
| Greedy Phase 4 | ✅ Có script |
| Greedy + pywrapcp Phase 4 | ✅ Có script |
| `result_aggregator_phase2.py` | ✅ Implement xong |
| `result_aggregator_phase4.py` | ✅ Implement xong |
| Phase 5 evaluation pipeline | ✅ Hoàn thiện (Đã có script aggregator và summary) |

### Ghi chú quan trọng

- `PROJECT_ARCHITECTURE.md` và các tài liệu cũ từng mô tả repo theo cấu trúc file phẳng; mô tả đó không còn đúng
- `results/phase4/` hiện dùng mô hình:
  - metaheuristic lưu `*_detail.csv` theo seed
  - `phase4_summary.py` build `*.csv` theo testcase
- `result_aggregator_phase4.py` lấy `cost_min` từ các file summary/classical CSV để build `results/phase4/cost_reference.csv`
- Nếu rerun `phase4.py` cho metaheuristic, cần rerun thêm `phase4_summary.py` trước khi aggregate Phase 4

---

*Cập nhật lần cuối: 2026-06-08*

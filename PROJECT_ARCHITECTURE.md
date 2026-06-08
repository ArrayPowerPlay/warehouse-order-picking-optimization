# Cấu trúc Kiến trúc Dự án (Project Architecture)

Tài liệu này mô tả các thành phần đang thực sự tồn tại trong repo và vai trò của chúng trong pipeline thực nghiệm.

---

## 1. Cấu trúc tổng quan

```text
warehouse-order-picking-optimization/
├── config/
│   └── settings.py
├── data/
│   ├── val_set/
│   └── test_set/
├── results/
│   ├── phase1/
│   ├── phase2/
│   ├── phase3/
│   ├── phase4/
│   └── phase5/
├── src/
│   ├── generators/
│   ├── solvers/
│   ├── result_aggregator_common.py
│   ├── result_aggregator_phase1.py
│   ├── result_aggregator_phase2.py
│   ├── result_aggregator_phase4.py
│   ├── result_aggregator_phase5.py
│   └── result_summary_phase5.py
├── CONTEXT.md
├── PROJECT_ARCHITECTURE.md
├── README.md
├── TESTCASE_CLASSIFICATION.md
└── requirements.txt
```

---

## 2. Cấu hình

### `config/settings.py`

File cấu hình toàn cục cho solver và các phase.

Các biến chính:

- `TIME_LIMIT_TESTING`: time limit cho Phase 1
- `TIME_LIMITS`: time limit chuẩn cho các phase chính
- `DATA_PATH`: đường dẫn gốc project
- `NUM_RUNS_PER_CONFIG`: hiện là `3`
- `SEEDS`: hiện là `[0, 1, 2]`

---

## 3. Dữ liệu

### `data/val_set/`

- Dùng cho Phase 1, Phase 2, Phase 3
- Tên file theo pattern nhóm testcase, ví dụ:
  - `small_01_N2_M5.in`
  - `medium_15_N30_M300.in`
  - `edge_dense_30_N50_M1000.in`

### `data/test_set/`

- Dùng cho Phase 4 và Phase 5
- Cấu trúc tên file tương tự `val_set`

---

## 4. Bộ sinh dữ liệu

### `src/generators/data_generator.py`

- Sinh một testcase `.in`
- Tạo `Q`, `d`, `q` và các phân bố khoảng cách khác nhau

### `src/generators/batch_generator.py`

- Sinh toàn bộ `val_set` và `test_set`
- Định nghĩa các họ testcase: `small`, `medium`, `large`, `edge`, `distribution`

### `src/generators/DATA_GENERATOR_NOTE.md`

- Ghi chú chi tiết về data generator

---

## 5. Solver

### 5.1 File dùng chung

### `src/solvers/utils.py`

Các hàm dùng chung:

- `read_input()`
- `evaluator()`
- `compute_route_distance()`
- `validator()`

### 5.2 Greedy

Thư mục: `src/solvers/greedy/`

#### `greedy.py`

- Greedy cơ bản

#### `phase1_greedy.py`

- Runner Phase 1 cho Greedy

#### `phase2_greedy.py`

- Runner Phase 2 cho Greedy trên `val_set`
- Lưu `cost_min` theo testcase

### 5.3 Greedy + Pruning + pywrapcp

Thư mục: `src/solvers/greedy_prunning_pywrapcp/`

#### `greedy_prunning_pywrapcp.py`

- Pipeline Greedy -> Pruning -> `pywrapcp`

#### `phase1_greedy_prunning_pywrapcp.py`

- Runner Phase 1

#### `phase2_greedy_prunning_pywrapcp.py`

- Runner Phase 2 trên `val_set`
- Lưu `cost_min` theo testcase

### 5.4 CP-SAT

Thư mục: `src/solvers/cp_sat/`

#### `cp_sat.py`

- Solver CP-SAT dùng OR-Tools
- Có kiểm tra infeasible trước khi build model

#### `phase1_cp_sat.py`

- Runner Phase 1

#### `phase2_cp_sat.py`

- Runner Phase 2 cho `val_set`
- Hiện chỉ chạy `small` và `medium`
- Bỏ qua `large`
- Ghi `cpsat.csv` vào `results/phase2/`

### 5.5 Adaptive Simulated Annealing

Thư mục: `src/solvers/simulated_annealing/`

#### `adaptive_simulated_annealing.py`

- Solver ASA
- Dừng theo `time_limit`
- Có cơ chế reheat

#### `phase1.py`

- Runner Phase 1

#### `phase2.py`

- Runner Phase 2 trên `val_set`
- Với mỗi `(testcase, cấu hình, seed)`, ghi detail vào `results/phase2/asa_detail.csv`

#### `phase2_summary.py`

- Build `results/phase2/asa.csv` từ `asa_detail.csv`
- Summary theo `(testcase, configuration)` với `cost_min`, `cost_avg`

#### `phase3.py`

- Tuning tham số ASA trên `val_set`
- Dùng `cost_reference` của Phase 2
- Tính `avg_RPD` từ `cost_avg`
- Chọn best config riêng cho `small`, `medium`, `large`

#### `phase4.py`

- Runner Phase 4 trên `test_set`
- Đọc best config theo group từ `results/phase3/asa.csv`
- Chạy trên toàn bộ `test_set`
- Có hỗ trợ nhiều worker; `--workers 0` nghĩa là auto
- Ghi detail per-seed vào `results/phase4/asa_detail.csv`

#### `phase4_summary.py`

- Build `results/phase4/asa.csv` từ `asa_detail.csv`
- Summary theo testcase với các cột:
  - `cost_min`
  - `cost_max`
  - `cost_avg`
  - `cost_std`
  - `t_best_avg`

#### `ALGORITHM_DESCRIPTION.md`

- Mô tả chi tiết thuật toán ASA

### 5.6 Genetic Algorithm

Thư mục: `src/solvers/genetic_algorithm/`

#### `ga.py`

- Python wrapper cho core GA

#### `ga_core.cpp`

- C++ core của GA

#### `phase1_ga.py`

- Runner Phase 1

#### `phase2.py`

- Runner Phase 2 trên `val_set`
- Với mỗi `(testcase, cấu hình, seed)`, ghi detail vào `results/phase2/ga_detail.csv`

#### `phase2_summary.py`

- Build `results/phase2/ga.csv` từ `ga_detail.csv`
- Summary theo `(testcase, configuration)` với `cost_min`, `cost_avg`

#### `phase3.py`

- Tuning tham số GA trên `val_set`
- Dùng `cost_reference` của Phase 2
- Tính `avg_RPD` từ `cost_avg`
- Chọn best config riêng cho `small`, `medium`, `large`

#### `phase4.py`

- Runner Phase 4 trên `test_set`
- Đọc best config theo group từ `results/phase3/ga.csv`
- Chạy trên toàn bộ `test_set`
- Có hỗ trợ nhiều worker; `--workers 0` nghĩa là auto
- Ghi detail per-seed vào `results/phase4/ga_detail.csv`

#### `phase4_summary.py`

- Build `results/phase4/ga.csv` từ `ga_detail.csv`
- Summary theo testcase với các cột:
  - `cost_min`
  - `cost_max`
  - `cost_avg`
  - `cost_std`
  - `t_best_avg`

### 5.7 Ant Colony Optimization

Thư mục: `src/solvers/ant_colony/`

#### `aco.py`

- Python wrapper cho core ACO

#### `aco_core.cpp`

- C++ core của ACO

#### `phase1_aco.py`

- Runner Phase 1

#### `phase2_aco.py`

- Runner Phase 2 trên `val_set`
- Với mỗi `(testcase, cấu hình, seed)`, ghi detail vào `results/phase2/aco_detail.csv`

#### `phase2_summary.py`

- Build `results/phase2/aco.csv` từ `aco_detail.csv`
- Summary theo `(testcase, configuration)` với `cost_min`, `cost_avg`

#### `phase3.py`

- Tuning tham số ACO trên `val_set`
- Dùng `cost_reference` của Phase 2
- Tính `avg_RPD` từ `cost_avg`
- Chọn best config riêng cho `small`, `medium`, `large`

#### `phase4.py`

- Runner Phase 4 trên `test_set`
- Đọc best config theo group từ `results/phase3/aco.csv`
- Chạy trên toàn bộ `test_set`
- Có hỗ trợ nhiều worker; `--workers 0` nghĩa là auto
- Ghi detail per-seed vào `results/phase4/aco_detail.csv`

#### `phase4_summary.py`

- Build `results/phase4/aco.csv` từ `aco_detail.csv`
- Summary theo testcase với các cột:
  - `cost_min`
  - `cost_max`
  - `cost_avg`
  - `cost_std`
  - `t_best_avg`

---

## 6. Script tổng hợp kết quả

### `src/result_aggregator_common.py`

- Helper dùng chung cho Phase 2 và Phase 4
- Đọc cột `cost_min` từ các file CSV của thuật toán
- Lấy min theo `testcase` để tạo `cost_reference`
- Với các file detail không có cột `cost_min`, script sẽ bỏ qua và in warning

### `src/result_aggregator_phase1.py`

- Tổng hợp các JSON trong `results/phase1/`
- Xuất `aggregate_results.csv`

### `src/result_aggregator_phase2.py`

- Tổng hợp các CSV trong `results/phase2/`
- Xuất `results/phase2/aggregate_result.csv`

### `src/result_aggregator_phase4.py`

- Tổng hợp các CSV trong `results/phase4/`
- Xuất `results/phase4/cost_reference.csv`

### `src/result_aggregator_phase5.py`

- Đọc `results/phase4/cost_reference.csv` làm mốc đánh giá (lọc bỏ các testcase vô nghiệm có `cost_reference = -1`).
- Gộp các kết quả `cost_min`, `cost_max`, `cost_avg`, `t_best_avg` từ các file summary của thuật toán trong `results/phase4/` (bỏ qua file detail và reference).
- Đổi các giá trị `-1` (vô nghiệm của từng thuật toán đơn lẻ) thành NaN.
- Tính chỉ số RPD của từng thuật toán: `((cost_avg - cost_reference) / cost_reference) * 100`.
- Xuất bảng kết quả chi tiết ra `results/phase5/aggregate_result.csv`.

### `src/result_summary_phase5.py`

- Đọc `results/phase5/aggregate_result.csv` và gộp thông tin nhóm kích thước (`group`).
- Tính trung bình RPD và t_best_avg cho từng nhóm (`small`, `medium`, `large`).
- Tính trung bình `overall` cho toàn bộ testcase (chỉ áp dụng đối với các thuật toán chạy đầy đủ cả 3 nhóm).
- Tìm thuật toán tốt nhất (`winner`) cho mỗi hàng dựa trên RPD nhỏ nhất (tiếp tục xét t_best_avg làm tie-breaker).
- Xuất bảng tổng hợp kết quả ra `results/phase5/summary.csv`.

---

## 7. Thư mục kết quả

### `results/phase1/`

- Kết quả representative runs
- Mỗi testcase có một thư mục riêng
- Bên trong chứa JSON theo thuật toán:
  - `greedy.json`
  - `pywrapcp.json`
  - `cpsat.json`
  - `asa.json`
  - `ga.json`
  - `aco.json`
- Có thêm:
  - `aggregate_results.csv`

### `results/phase2/`

- Kết quả Phase 2 trên `val_set`
- Pipeline hiện sinh ra:
  - `greedy.csv`
  - `pywrapcp.csv`
  - `cpsat.csv`
  - `asa_detail.csv`, `asa.csv`
  - `ga_detail.csv`, `ga.csv`
  - `aco_detail.csv`, `aco.csv`
  - `aggregate_result.csv`

### `results/phase3/`

- Kết quả tuning
- Pipeline hiện sinh ra:
  - `asa.csv`
  - `ga.csv`
  - `aco.csv`

### `results/phase4/`

- Kết quả Phase 4 trên `test_set`
- Pipeline hiện sinh ra:
  - `greedy.csv`
  - `pywrapcp.csv`
  - `cpsat.csv`
  - `asa_detail.csv`, `asa.csv`
  - `ga_detail.csv`, `ga.csv`
  - `aco_detail.csv`, `aco.csv`
  - `cost_reference.csv` sau khi chạy `result_aggregator_phase4.py`

Lưu ý:

- `greedy` và `pywrapcp` Phase 4 hiện đang bỏ qua `small`
- `CP-SAT` Phase 4 hiện đang chạy `small` và `medium`, bỏ qua `large`
- Metaheuristic Phase 4 chạy trên tất cả testcase và dùng best config theo group từ Phase 3
- Sau khi rerun metaheuristic Phase 4, cần chạy thêm từng script `phase4_summary.py` trước khi aggregate

### `results/phase5/`

- Kết quả Phase 5 (Final Evaluation) trên `test_set`
- Chứa:
  - `aggregate_result.csv`: Chứa kết quả chi tiết từng testcase (loại bỏ testcase vô nghiệm), cột RPD cho từng thuật toán.
  - `summary.csv`: Bảng tổng hợp theo nhóm kích thước (small, medium, large, overall), kèm theo winner của từng nhóm.

---

## 8. Trạng thái phương pháp luận

### Điều đang đúng

- Phase 2 đang đúng vai trò build **best found solution / best-known reference** trên `val_set`
- Phase 4 đang đúng vai trò build `cost_reference` trên `test_set`
  - Tuy nhiên đây không phải BFS theo nghĩa exhaustive như Phase 2, vì metaheuristic ở Phase 4 chỉ chạy best config đã chọn từ Phase 3, không chạy full hyperparameter grid
- Metaheuristic chạy nhiều seed, lưu detail per-seed, rồi build summary theo testcase
- Aggregator lấy min giữa các thuật toán để tạo `cost_reference`
- Phase 5 đã hoàn thiện với pipeline tổng hợp kết quả (`result_aggregator_phase5.py`) và summary (`result_summary_phase5.py`) tự động tính toán RPD và chọn winner cho từng nhóm kích thước.

### Hướng nên làm ở Phase 3

1. Giữ nguyên `cost_reference` từ Phase 2
2. Với mỗi `(testcase, configuration)`, chạy nhiều seed
3. Tính `avg_cost` và `std_cost`
4. Tính `RPD` bằng `avg_cost` so với `cost_reference`
5. Chọn cấu hình có `avg_RPD` nhỏ nhất theo group
6. Dùng `std_RPD` và `avg_t_best` làm tie-break

Nếu chỉ đổi logic tuning, phần cần rerun trước hết là:

- `Phase 3`
- `Phase 5`

Không bắt buộc rerun `Phase 2` và `Phase 4` nếu vẫn giữ định nghĩa `cost_reference` là best-known cost.

---

*Cập nhật lần cuối: 2026-06-08*

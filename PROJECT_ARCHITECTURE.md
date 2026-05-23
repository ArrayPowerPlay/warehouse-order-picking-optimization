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
├── notebooks/
│   ├── tuning/
│   │   ├── genetic_algorithm_tuning.ipynb
│   │   └── simulated_annealing_tuning.ipynb
│   └── final_evaluation.ipynb
├── results/
│   ├── phase1/
│   ├── phase2/
│   ├── phase3/
│   └── phase4/
├── src/
│   ├── generators/
│   ├── solvers/
│   ├── result_aggregator_common.py
│   ├── result_aggregator_phase1.py
│   ├── result_aggregator_phase2.py
│   └── result_aggregator_phase4.py
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
- Với mỗi `(testcase, cấu hình)`, chạy toàn bộ `SEEDS`
- Lưu `cost_min`

#### `phase3.py`

- Tuning tham số ASA trên `val_set`
- Hiện đang đọc kết quả Phase 2 và tính `avg_RFD` từ `cost_min`
- Đây là điểm cần đổi nếu muốn tune theo hiệu năng trung bình

#### `phase4.py`

- Runner Phase 4 trên `test_set`
- Với mỗi `(testcase, cấu hình)`, chạy toàn bộ `SEEDS`
- Lưu `cost_min`

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
- Với mỗi `(testcase, cấu hình)`, chạy toàn bộ `SEEDS`
- Lưu `cost_min`

#### `phase4.py`

- Runner Phase 4 trên `test_set`
- Với mỗi `(testcase, cấu hình)`, chạy toàn bộ `SEEDS`
- Lưu `cost_min`

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
- Với mỗi `(testcase, cấu hình)`, chạy toàn bộ `SEEDS`
- Lưu `cost_min`

---

## 6. Script tổng hợp kết quả

### `src/result_aggregator_common.py`

- Helper dùng chung cho Phase 2 và Phase 4
- Đọc cột `cost_min` từ các file CSV của thuật toán
- Lấy min theo `testcase` để tạo `cost_reference`

### `src/result_aggregator_phase1.py`

- Tổng hợp các JSON trong `results/phase1/`
- Xuất `aggregate_results.csv`

### `src/result_aggregator_phase2.py`

- Tổng hợp các CSV trong `results/phase2/`
- Xuất `results/phase2/aggregate_result.csv`

### `src/result_aggregator_phase4.py`

- Tổng hợp các CSV trong `results/phase4/`
- Xuất `results/phase4/aggregate_result.csv`

---

## 7. Notebook

### `notebooks/tuning/simulated_annealing_tuning.ipynb`

- Notebook tuning cho ASA

### `notebooks/tuning/genetic_algorithm_tuning.ipynb`

- Notebook tuning cho GA

### `notebooks/final_evaluation.ipynb`

- Notebook phục vụ tổng hợp và trực quan hóa cuối

---

## 8. Thư mục kết quả

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
- Hiện có các file:
  - `greedy.csv`
  - `pywrapcp.csv`
  - `cpsat.csv`
  - `asa.csv`
  - `ga.csv`
  - `aco.csv`
  - `aggregate_result.csv`

### `results/phase3/`

- Kết quả tuning
- Hiện có:
  - `asa.csv`

### `results/phase4/`

- Kết quả Phase 4 trên `test_set`
- Hiện có:
  - `asa.csv`
  - `ga.csv`
  - `aggregate_result.csv`

Lưu ý:

- Phase 4 hiện chưa có pipeline CP-SAT tương ứng cho phần `small` của `test_set`
- Vì vậy `cost_reference` ở `results/phase4/aggregate_result.csv` chưa phản ánh đầy đủ workflow lý tưởng dùng CP-SAT làm mốc cho `small`

---

## 9. Trạng thái phương pháp luận

### Điều đang đúng

- Phase 2 và Phase 4 đang đúng vai trò **best known reference**
- Metaheuristic chạy nhiều seed rồi lưu `cost_min`
- Aggregator lấy min giữa các thuật toán để tạo `cost_reference`

### Điều cần chỉnh

- Phase 3 của ASA hiện đang tune theo `cost_min`
- Nếu mục tiêu Final Evaluation là báo cáo `avg_cost`, `std_cost`, `avg_t_best`, thì tuning bằng `cost_min` là không nhất quán

### Hướng nên làm ở Phase 3

1. Giữ nguyên `cost_reference` từ Phase 2
2. Với mỗi `(testcase, configuration)`, chạy nhiều seed
3. Tính `avg_cost` và `std_cost`
4. Tính `RFD` bằng `avg_cost` so với `cost_reference`
5. Chọn cấu hình có `avg_RFD` nhỏ nhất theo group
6. Dùng `std_RFD` và `avg_t_best` làm tie-break

Nếu chỉ đổi logic tuning, phần cần rerun trước hết là:

- `Phase 3`
- `Phase 5`

Không bắt buộc rerun `Phase 2` và `Phase 4` nếu vẫn giữ định nghĩa `cost_reference` là best-known cost.

# Cấu trúc Kiến trúc Dự án (Project Architecture)

Tài liệu này mô tả cấu trúc thư mục và vai trò của các thành phần đang thực sự tồn tại trong repo **Warehouse Order Picking Optimization**.

---

## 1. Cấu trúc thư mục tổng quan

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
│   └── phase2/
├── src/
│   ├── generators/
│   ├── solvers/
│   └── result_aggregator_phase1.py
├── CONTEXT.md
├── PROJECT_ARCHITECTURE.md
├── README.md
├── TESTCASE_CLASSIFICATION.md
└── requirements.txt
```

---

## 2. Cấu hình (`config/`)

### `config/settings.py`
- File cấu hình toàn cục cho solver và script thực nghiệm.
- Các biến chính đang dùng:
  - `TIME_LIMIT_TESTING`: time limit cho Phase 1 theo nhóm `small`, `medium`, `large`
  - `TIME_LIMITS`: time limit chuẩn cho các pha chạy đầy đủ
  - `DATA_PATH`: đường dẫn gốc project
  - `NUM_RUNS_PER_CONFIG`: số lần chạy lặp cho thuật toán ngẫu nhiên
  - `SEEDS`: danh sách seed mặc định

---

## 3. Dữ liệu (`data/`)

### `data/val_set/`
- Chứa các testcase validation dùng cho Phase 1, Phase 2 và tuning.
- Tên file bám theo nhóm testcase, ví dụ:
  - `small_01_N2_M5.in`
  - `medium_15_N30_M300.in`
  - `edge_dense_30_N50_M1000.in`

### `data/test_set/`
- Chứa các testcase độc lập dùng cho đánh giá cuối.
- Cấu trúc đặt tên giống `val_set`.

---

## 4. Mã nguồn sinh dữ liệu (`src/generators/`)

### `src/generators/data_generator.py`
- Generator sinh một testcase `.in`.
- Hỗ trợ sinh ma trận hàng hóa `Q`, ma trận khoảng cách `d`, nhu cầu `q`, và nhiều kiểu phân bố tọa độ.

### `src/generators/batch_generator.py`
- Sinh hàng loạt testcase cho `val_set` và `test_set`.
- Định nghĩa recipe các nhóm `small`, `medium`, `large`, `edge`, và distribution cases.

### `src/generators/DATA_GENERATOR_NOTE.md`
- Ghi chú chi tiết cho data generator.

---

## 5. Mã nguồn solver (`src/solvers/`)

### 5.1. File dùng chung

### `src/solvers/utils.py`
- Tiện ích chung cho toàn bộ solver.
- Các hàm chính:
  - `read_input()`
  - `evaluator()`
  - `compute_route_distance()`
  - `validator()`

### `src/solvers/phase1_edge_large_cpsat_pywrapcp.py`
- Runner bổ sung cho Phase 1.
- Dùng để chạy:
  - `cpsat` cho representative edge và large cases
  - `pywrapcp` cho representative edge cases
- Đọc input từ `data/val_set/` và ghi đè output vào `results/phase1/<testcase>/`.

### 5.2. Greedy

Thư mục: `src/solvers/greedy/`

### `src/solvers/greedy/greedy.py`
- Thuật toán Greedy cơ bản.
- Xây route bằng cách chọn kệ có tỷ lệ lợi ích/khoảng cách tốt nhất ở mỗi bước.

### `src/solvers/greedy/phase1_greedy.py`
- Runner Phase 1 cho Greedy.
- Ghi kết quả `greedy.json` vào `results/phase1/<testcase>/`.

### 5.3. Greedy + Pruning + pywrapcp

Thư mục: `src/solvers/greedy_prunning_pywrapcp/`

Lưu ý: tên thư mục hiện tại trong code là `prunning` theo chính tả đang dùng của repo.

### `src/solvers/greedy_prunning_pywrapcp/greedy_prunning_pywrapcp.py`
- Pipeline 3 bước:
  - Greedy chọn tập kệ ban đầu
  - Pruning loại kệ thừa
  - `pywrapcp` tối ưu lại thứ tự route bằng Guided Local Search
- Trả về `route`, `total_distance`, `t_best`.

### `src/solvers/greedy_prunning_pywrapcp/phase1_greedy_prunning_pywrapcp.py`
- Runner Phase 1 cho solver pywrapcp.
- Ghi `pywrapcp.json` vào `results/phase1/<testcase>/`.

### 5.4. CP-SAT

Thư mục: `src/solvers/cp_sat/`

### `src/solvers/cp_sat/cp_sat.py`
- Solver CP-SAT dùng OR-Tools.
- Mô hình hóa chọn kệ và chu trình bằng biến nhị phân và `AddCircuit`.
- Có kiểm tra nhanh trường hợp vô nghiệm trước khi build model.

### `src/solvers/cp_sat/phase1_cp_sat.py`
- Runner Phase 1 cho CP-SAT.
- Ghi `cpsat.json` vào `results/phase1/<testcase>/`.

### 5.5. Simulated Annealing

Thư mục: `src/solvers/simulated_annealing/`

### `src/solvers/simulated_annealing/adaptive_simulated_annealing.py`
- Solver Adaptive Simulated Annealing (ASA).
- Dừng theo `time_limit`.
- Có bộ tham số mặc định và cơ chế reheat.

### `src/solvers/simulated_annealing/phase1.py`
- Runner Phase 1 cho ASA.
- Ghi `asa.json` vào `results/phase1/<testcase>/`.

### `src/solvers/simulated_annealing/phase2.py`
- Script phục vụ Phase 2 cho ASA.
- Dùng để chạy trên tập dữ liệu lớn hơn Phase 1, hướng tới thu cost reference.

### `src/solvers/simulated_annealing/ALGORITHM_DESCRIPTION.md`
- Mô tả chi tiết ý tưởng và operator của ASA.

### 5.6. Genetic Algorithm

Thư mục: `src/solvers/genetic_algorithm/`

### `src/solvers/genetic_algorithm/ga.py`
- Python wrapper cho core GA viết bằng C++.
- Gọi file thực thi `ga_core.exe` hoặc `ga_core`.

### `src/solvers/genetic_algorithm/ga_core.cpp`
- C++ core của Genetic Algorithm.

### `src/solvers/genetic_algorithm/phase1_ga.py`
- Runner Phase 1 cho GA.
- Ghi `ga.json` vào `results/phase1/<testcase>/`.

### 5.7. Ant Colony Optimization

Thư mục: `src/solvers/ant_colony/`

### `src/solvers/ant_colony/aco.py`
- Python wrapper cho core ACO viết bằng C++.
- Gọi file thực thi `aco_core.exe` hoặc `aco_core`.

### `src/solvers/ant_colony/aco_core.cpp`
- C++ core của Ant Colony Optimization.

### `src/solvers/ant_colony/phase1_aco.py`
- Runner Phase 1 cho ACO.
- Ghi `aco.json` vào `results/phase1/<testcase>/`.

---

## 6. Script tổng hợp kết quả

### `src/result_aggregator_phase1.py`
- Quét các thư mục con trong `results/phase1/`.
- Đọc các file JSON theo từng thuật toán.
- Tổng hợp `t_best` và `time_limit` thành `results/phase1/aggregate_results.csv`.

---

## 7. Notebooks

### `notebooks/tuning/simulated_annealing_tuning.ipynb`
- Notebook tuning cho ASA trên `val_set`.

### `notebooks/tuning/genetic_algorithm_tuning.ipynb`
- Notebook tuning cho GA.

### `notebooks/final_evaluation.ipynb`
- Notebook phục vụ đánh giá tổng hợp và so sánh cuối cùng.

---

## 8. Kết quả thực nghiệm (`results/`)

### `results/phase1/`
- Đang được dùng để lưu kết quả representative runs cho Phase 1.
- Mỗi testcase có một thư mục riêng, ví dụ:
  - `results/phase1/small_04_N5_M20/`
  - `results/phase1/medium_15_N30_M300/`
  - `results/phase1/large_21_N50_M1000/`
  - `results/phase1/edge_N1_24_N1_M500/`
- Trong mỗi thư mục có các file JSON theo thuật toán:
  - `greedy.json`
  - `pywrapcp.json`
  - `cpsat.json`
  - `asa.json`
  - `ga.json`
  - `aco.json`
- Ngoài ra có:
  - `results/phase1/aggregate_results.csv`

### `results/phase2/`
- Thư mục đã được tạo nhưng hiện chưa thấy file kết quả trong repo.
- Dự kiến dùng để lưu cost reference hoặc kết quả chạy giai đoạn tiếp theo.

---

## 9. Ghi chú về trạng thái hiện tại

- Repo hiện đã tổ chức solver theo từng package con trong `src/solvers/`, không còn cấu trúc file phẳng như một số tài liệu cũ mô tả.
- CP-SAT hiện nằm ở `src/solvers/cp_sat/`, không phải `OR_Tools_cp_sat.py`.
- Greedy hiện nằm ở `src/solvers/greedy/greedy.py`.
- Solver pywrapcp hiện nằm ở `src/solvers/greedy_prunning_pywrapcp/greedy_prunning_pywrapcp.py`.
- `results/` hiện mới có `phase1/` và `phase2/`; các thư mục phase sau chưa xuất hiện trong repo hiện tại.

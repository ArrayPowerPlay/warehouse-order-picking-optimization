# Warehouse Order Picking Optimization

Repo này dùng để sinh dữ liệu, chạy solver, tune tham số, build `cost_reference`, và đánh giá cuối cho bài toán **Order Picking Route in Warehouse**.

## Bài toán

Nhân viên xuất phát từ cửa kho `0`, thăm một tập kệ, lấy đủ đơn hàng rồi quay lại cửa kho.

- Input chính:
  - `Q[i][j]`: lượng sản phẩm `i` tại kệ `j`
  - `q[i]`: nhu cầu sản phẩm `i`
  - `d(i, j)`: khoảng cách giữa hai điểm
- Mục tiêu:
  - tối thiểu hóa tổng quãng đường di chuyển
- Nếu testcase vô nghiệm:
  - solver trả `route = []`, `total_distance = -1`, `t_best = -1`

## Thuật toán hiện có

- `greedy`
- `greedy_prunning_pywrapcp`
- `cp_sat`
- `simulated_annealing` (ASA)
- `genetic_algorithm` (GA)
- `ant_colony` (ACO)

## Cấu trúc repo

```text
warehouse-order-picking-optimization/
├── config/
├── data/
│   ├── val_set/
│   └── test_set/
├── notebooks/
├── results/
│   ├── phase1/
│   ├── phase2/
│   ├── phase3/
│   ├── phase4/
│   └── phase5/
├── src/
│   ├── generators/
│   ├── solvers/
│   ├── result_aggregator_phase1.py
│   ├── result_aggregator_phase2.py
│   └── result_aggregator_phase4.py
├── CONTEXT.md
├── PROJECT_ARCHITECTURE.md
└── README.md
```

## Workflow thực nghiệm

```text
Phase 1: chọn time limit
Phase 2: build cost_reference cho val_set
Phase 3: chọn best config theo group trên val_set
Phase 4: build cost_reference cho test_set
Phase 5: final evaluation trên test_set
```

### Quy ước chính

- `Phase 2` và `Phase 4` dùng `cost_min` để build `cost_reference`
- `Phase 3` và `Phase 5` đánh giá metaheuristic theo `cost_avg`
- Mỗi metaheuristic có thể dùng **best config khác nhau cho `small`, `medium`, `large`**

## Phase 4 hiện tại

### Metaheuristic

`ASA`, `GA`, `ACO` chạy theo 2 bước:

1. `phase4.py`
   - đọc best config theo group từ `results/phase3/*.csv`
   - chạy nhiều seed trên toàn bộ `test_set`
   - ghi detail per-seed vào `results/phase4/*_detail.csv`
2. `phase4_summary.py`
   - build `results/phase4/*.csv` theo testcase
   - các cột chính:
     - `cost_min`
     - `cost_max`
     - `cost_avg`
     - `cost_std`
     - `t_best_avg`

Ví dụ:

```bash
python src/solvers/simulated_annealing/phase4.py --workers 0
python src/solvers/simulated_annealing/phase4_summary.py

python src/solvers/genetic_algorithm/phase4.py --workers 0
python src/solvers/genetic_algorithm/phase4_summary.py

python src/solvers/ant_colony/phase4.py --workers 0
python src/solvers/ant_colony/phase4_summary.py
```

Ghi chú:

- `--workers 0` nghĩa là auto chọn số worker theo `min(cpu_count, total_tasks)`
- `--workers 1` nghĩa là chạy tuần tự

### Classical solver

- `greedy`: `src/solvers/greedy/phase4_greedy.py`
- `greedy_prunning_pywrapcp`: `src/solvers/greedy_prunning_pywrapcp/phase4_greedy_prunning_pywrapcp.py`
- `cp_sat`: `src/solvers/cp_sat/phase4_cp_sat.py`

## Phase 4.2: Build cost reference cho test_set

Chạy:

```bash
python src/result_aggregator_phase4.py
```

Kết quả:

- file output: `results/phase4/cost_reference.csv`
- gồm đúng 3 cột:
  - `testcase`
  - `cost_reference`
  - `group`

`cost_reference(testcase)` được tính bằng:

```text
min(cost_min của tất cả thuật toán trên testcase đó)
```

Aggregator chỉ đọc các file summary có cột `testcase` và `cost_min`, và tự bỏ qua:

- `*_detail.csv`
- `cost_reference.csv`
- `aggregate_result.csv` cũ nếu còn tồn tại

## Gợi ý cho Phase 5

### Bảng testcase-level

Nên gộp theo từng testcase:

- `group`
- `cost_reference`
- với mỗi metaheuristic:
  - `*_cost_min`
  - `*_cost_max`
  - `*_cost_avg`
  - `*_cost_std`
  - `*_t_best_avg`
  - `*_RFD_avg`

Trong đó:

```text
RFD_avg = ((cost_avg - cost_reference) / cost_reference) * 100
```

### Overall chuẩn nhất

Không nên tính `overall` bằng trung bình thường của `small`, `medium`, `large`.

Cách chuẩn nhất là:

- tính trực tiếp trên toàn bộ testcase ở bảng testcase-level
- tức là:

```text
overall_RFD = average(RFD_avg của tất cả testcase)
overall_t_best = average(t_best_avg của tất cả testcase)
```

Cách này vẫn đúng ngay cả khi mỗi group dùng một best config khác nhau, vì ở Phase 5 bạn đang đánh giá một **policy cố định theo group**:

- `small -> best_config_small`
- `medium -> best_config_medium`
- `large -> best_config_large`

## Tài liệu chi tiết

- [CONTEXT.md](./CONTEXT.md)
- [PROJECT_ARCHITECTURE.md](./PROJECT_ARCHITECTURE.md)

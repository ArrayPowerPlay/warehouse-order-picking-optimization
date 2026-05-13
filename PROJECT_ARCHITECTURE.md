# Cấu trúc Kiến trúc Dự án (Project Architecture)

Tài liệu này mô tả chi tiết về cấu trúc thư mục, mục đích của từng file và các tệp cấu hình trong hệ thống **Warehouse Order Picking Optimization**.

---

## 1. Cấu trúc Thư mục Tổng quan

```text
warehouse-order-picking-optimization/
├── config/                 # Thư mục chứa các file cấu hình hệ thống
├── data/                   # Thư mục chứa dữ liệu đầu vào (testcases)
├── notebooks/              # Thư mục chứa các file Jupyter Notebook dùng để tuning và đánh giá
├── results/                # Thư mục chứa kết quả chạy thực nghiệm
├── src/                    # Thư mục chứa mã nguồn chính (sinh dữ liệu, thuật toán)
├── CONTEXT.md              # Tài liệu mô tả bài toán và overview toàn bộ project
├── README.md               # Tài liệu giới thiệu dự án (entry point)
├── requirements.txt        # Các thư viện phụ thuộc (dependencies)
└── TESTCASE_CLASSIFICATION.md  # Tài liệu phân loại chi tiết các testcase
```

---

## 2. Chi tiết cấu hình và mã nguồn (`src/` & `config/`)

Đây là phần lõi của hệ thống, bao gồm cấu hình toàn cục, bộ sinh dữ liệu và các thuật toán giải quyết bài toán.

### 2.1. Cấu hình hệ thống (`config/`)

- **`config/settings.py`**
  - **Mục đích:** File cấu hình toàn cục (Global Configuration) cho tất cả các solver và script đánh giá.
  - **Nội dung chính:**
    - `TIME_LIMITS`: Dictionary định nghĩa thời gian chạy tối đa (time limit) cho các thuật toán Heuristic/Metaheuristic dựa trên quy mô của testcase (small, medium, large, edge). Đảm bảo tính công bằng khi so sánh các thuật toán.
    - `NUM_RUNS_PER_CONFIG`: Số lần chạy lặp lại độc lập cho các thuật toán có yếu tố ngẫu nhiên (như SA, GA) để lấy kết quả trung bình/tốt nhất nhằm triệt tiêu phương sai.

### 2.2. Bộ sinh dữ liệu (`src/generators/`)

Đảm nhiệm việc sinh các file dữ liệu đầu vào (`.in`) với nhiều đặc tả không gian và ràng buộc khác nhau.

- **`data_generator.py`**
  - **Mục đích:** Core engine dùng để sinh một file testcase đơn lẻ thông qua CLI tương tác hoặc được gọi trực tiếp bằng code.
  - **Nội dung chính:**
    - Cấu hình các hằng số toán học (`COORD_BOUND_MAX`, `MAX_RESOURCE_HARD_CAP`).
    - Khả năng sinh ma trận tài nguyên hàng hóa trên kệ ($Q$).
    - Khả năng sinh tọa độ kệ hàng theo 4 phân bố không gian: *Uniform Random*, *Corner Biased* (tập trung 4 góc), *Clustered* (chia cụm), và *Diagonal* (đường chéo).
    - Khả năng sinh nhu cầu ($q$) với các tuỳ chọn đảm bảo bài toán có nghiệm (Feasible) hoặc vô nghiệm (Infeasible).
- **`batch_generator.py`**
  - **Mục đích:** Tự động hóa quá trình sinh tập dữ liệu lớn (`val_set` và `test_set`).
  - **Nội dung chính:** Định nghĩa `dataset_recipe` (công thức sinh 39 testcases cho mỗi tập) với các kịch bản trải dài từ cấu trúc nhỏ (small), cấu trúc lớn (large), các kịch bản góc (edge_dense, edge_sparse) và các phân bố tọa độ.
- **`DATA_GENERATOR_NOTE.md`**
  - **Mục đích:** Tài liệu hướng dẫn sử dụng và giải thích toán học chi tiết về giới hạn tọa độ và cách các generator hoạt động.

### 2.3. Thuật toán tối ưu (`src/solvers/`)

Chứa toàn bộ các thuật toán và hàm hỗ trợ để giải quyết bài toán tìm đường đi thu gom hàng hóa.

- **`utils.py`**
  - **Mục đích:** Module hỗ trợ dùng chung cho tất cả các thuật toán.
  - **Nội dung chính:**
    - `read_input()`: Parser đọc file `.in` và chuyển hóa thành cấu trúc dữ liệu ma trận chuẩn (0-based/1-based routing).
    - `validator()`: Kiểm tra tính hợp lệ về mặt dữ liệu và logic toán học của testcase đầu vào.
    - `evaluator()`: Đánh giá một lộ trình (route) bất kỳ: tính toán tổng quãng đường, số lượng hàng thu gom được và tính hợp lệ của chu trình.
- **`OR_Tools_cp_sat.py`**
  - **Mục đích:** Lời giải chính xác (Exact Solver) sử dụng Google OR-Tools (CP-SAT solver).
  - **Nội dung chính:** Mô hình hóa bài toán thành các biến nhị phân, thiết lập ràng buộc Hamiltonian path và tài nguyên, dùng để tìm ra **Nghiệm tối ưu tuyệt đối** (Optimal Solution) cho các tập nhỏ để làm Ground Truth (Baseline).
- **`greedy.py`**
  - **Mục đích:** Thuật toán Tham lam (Constructive Heuristic).
  - **Nội dung chính:** Tại mỗi bước chọn kệ chưa thăm có tỉ lệ (Hàng hóa hữu ích / Khoảng cách) tốt nhất. Tốc độ cực nhanh nhưng chất lượng nghiệm chỉ ở mức trung bình.
- **`greedy_pruning_pywrapcp.py`**
  - **Mục đích:** Thuật toán lai (Pipeline Heuristic + Local Search).
  - **Nội dung chính:** Kết hợp 3 bước: (1) Khởi tạo lộ trình bằng Greedy, (2) Cắt tỉa (Pruning) các kệ dư thừa, (3) Tối ưu hóa thứ tự chặng đường (Routing) bằng module Guided Local Search (`pywrapcp` của OR-Tools).
- **`simulated_annealing.py`**
  - **Mục đích:** Thuật toán Luyện kim chuẩn (Adaptive Simulated Annealing - ASA).
  - **Nội dung chính:** Ứng dụng Metaheuristic. Sử dụng các cơ chế Lân cận (ALNS - Adaptive Large Neighborhood Search) như Swap, Insert, 2-Opt. Tích hợp cơ chế làm lạnh (cooling schedule) và phục hồi nhiệt (re-annealing) dựa trên số vòng lặp không cải thiện. Dừng theo `TIME_LIMITS`.
- **`genetic_algorithm.py`** (Đang phát triển)
  - **Mục đích:** Thuật toán Di truyền (Metaheuristic).
- **Mã nguồn C++ (`ACO.cpp`, `GA+2opt.cpp`)**
  - **Mục đích:** Các implementation bằng C++ của Ant Colony Optimization và Genetic Algorithm + 2-Opt dùng cho mục đích tham khảo hoặc benchmark tốc độ cấp thấp.

---

## 3. Dữ liệu và Phân tích (`data/`, `notebooks/`, `results/`)

### 3.1. Dữ liệu (`data/`)
- **`val_set/`**: Chứa 39 file dữ liệu dùng cho quá trình Tuning (Grid Search) để tìm ra bộ tham số tốt nhất cho các Metaheuristic.
- **`test_set/`**: Chứa 39 file dữ liệu độc lập dùng để thi đấu, so sánh công bằng hiệu năng (Final Evaluation) giữa các thuật toán.

### 3.2. Quá trình Tuning và Đánh giá (`notebooks/`)
Các file Jupyter Notebook để chạy thực nghiệm tương tác và vẽ đồ thị.
- **`tuning/simulated_annealing_tuning.ipynb`**: Chạy quy trình Grid Search cho thuật toán SA trên tập `val_set`. So sánh RPD (Relative Percentage Deviation) so với nghiệm CP-SAT (Ground truth).
- **`tuning/genetic_algorithm_tuning.ipynb`**: Quy trình Tuning tương tự dành cho thuật toán GA.
- **`final_evaluation.ipynb`**: File tổng hợp. Chạy mọi thuật toán với cấu hình tốt nhất đã tune trên tập `test_set`, thu thập số liệu (thời gian chạy, quãng đường, độ ổn định) và xuất ra báo cáo (bảng biểu, biểu đồ Boxplot/Bar chart).

### 3.3. Kết quả thực nghiệm (`results/`)
- **`val_results/`**: Lưu trữ các file log, CSV, JSON sinh ra từ quá trình tuning. Thường là bảng thành tích của các bộ tham số.
- **`test_results/`**: Lưu trữ kết quả đánh giá cuối cùng để đưa vào báo cáo môn học/nghiên cứu.

# Adaptive Simulated Annealing

File chính: `adaptive_simulated_annealing.py`

## Tóm tắt
- Input: `N, M, Q, d, q` từ `read_input()`
- Output: `route, total_distance, t_best`
- Vô nghiệm: `([], -1, -1)`
- Dừng theo `time_limit`

## Biểu diễn nghiệm
- `state` là hoán vị đầy đủ các kệ `1..M`
- `route` là prefix thực sự cần đi sau khi đã đủ hàng
- `Q` và `q` dùng index 1-based
- `d` dùng node `0` là cửa kho

## Siêu tham số cần tune
- `alpha`: hệ số làm lạnh cơ sở
- `max_no_improve`: số bước không cải thiện trước khi re-anneal
- `reheat_ratio`: mức phục hồi nhiệt so với `T_start`

`seed` chỉ dùng để tái lập thực nghiệm, không xem là hyperparameter cần tune.

## Các bước của thuật toán
### Bước 1. Đọc input và loại sớm case đặc biệt
- Đọc `N, M, Q, d, q`
- Nếu đơn hàng rỗng thì trả `([], 0, 0.0)`
- Nếu tổng cung của một sản phẩm nhỏ hơn nhu cầu thì trả `([], -1, -1)`

### Bước 2. Khởi tạo thời gian
- Đặt `algorithm_start`
- Đặt `deadline = algorithm_start + time_limit`

### Bước 3. Khởi tạo nghiệm ban đầu
- Tạo `current_state = [1, 2, ..., M]`
- Xáo trộn ngẫu nhiên bằng `random.shuffle`
- Gọi `evaluate_route()` để lấy `current_route` và `current_cost`
- Đồng bộ `best_state`, `best_route`, `best_cost`, `t_best`

### Bước 4. Đánh giá một permutation bằng `evaluate_route()`
- Duyệt permutation từ trái sang phải
- Sau mỗi kệ, cập nhật lượng hàng còn thiếu
- Khi đã đủ mọi sản phẩm thì dừng
- Tính quãng đường của prefix đó bằng `compute_route_distance()`

Ý nghĩa:
- phần đầu của permutation quan trọng hơn phần cuối
- thay đổi ở suffix có thể không ảnh hưởng route thực tế

### Bước 5. Warm-up để ước lượng `T_start`
- Sinh các hàng xóm ngẫu nhiên
- Thu các `delta` dương
- Ước lượng:
  - `delta_avg = average(delta)`
  - `T_start = -delta_avg / log(0.8)`
- Nếu không có mẫu phù hợp thì dùng fallback

### Bước 6. Sinh lân cận
Solver hiện dùng 3 operator:
- `op_swap`: đổi chỗ 2 vị trí
- `op_insert`: lấy 1 phần tử và chèn sang vị trí khác
- `op_2opt`: đảo một đoạn con

Các operator được bias vào prefix có ảnh hưởng:
- hoặc chọn **2 vị trí trong prefix**
- hoặc chọn **1 vị trí trong prefix và 1 vị trí trong suffix**
- nếu `len(current_route) < 2` thì fallback về sample toàn cục

### Bước 7. Chấp nhận nghiệm theo SA
- Nếu `neighbor_cost < current_cost` thì chấp nhận luôn
- Nếu không, chấp nhận theo xác suất:
  - `exp(-delta_e / T)`

Điểm operator:
- `5`: tạo `best_cost` mới
- `2`: cải thiện nghiệm hiện tại
- `1`: nghiệm xấu hơn nhưng vẫn được chấp nhận
- `0`: bị từ chối

### Bước 8. Cập nhật trọng số operator theo epoch
- Theo dõi:
  - `op_scores`
  - `op_counts`
  - `epoch_accepted`
- Sau mỗi `epoch_length`, cập nhật lại trọng số của từng operator

Ý nghĩa:
- operator hiệu quả hơn sẽ được chọn nhiều hơn ở các bước sau

### Bước 9. Adaptive cooling
- Tính `R_a = epoch_accepted / epoch_length`
- Nếu `R_a > 0.5`: làm nguội nhanh hơn
- Nếu `R_a < 0.05`: tăng nhẹ nhiệt độ
- Còn lại: dùng `alpha`

### Bước 10. Re-annealing khi bị kẹt
- Nếu `no_improve_cnt >= max_no_improve`
- Đặt lại:
  - `T = T_start * reheat_ratio`
  - `grace_period`
- Quay về `best_state`
- Perturb nhẹ bằng một số swap ngẫu nhiên

## Ghi chú
- Đây là ASA thuần, không có nhánh exact solver riêng cho testcase nhỏ.
- `t_best` là thời điểm tìm thấy nghiệm tốt nhất cuối cùng trong toàn bộ thời gian chạy.

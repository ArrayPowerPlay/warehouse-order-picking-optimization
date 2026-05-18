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

## Lưới siêu tham số cho Phase 2 / Phase 3
- `alpha ∈ {0.99, 0.995, 0.999}`
- `max_no_improve ∈ {1000, 2000}`
- `reheat_ratio ∈ {0.2, 0.3, 0.5}`

`seed` không thuộc lưới tune; Phase 2 / Phase 3 chỉ dùng `seed` để chạy lặp thực nghiệm và lấy thống kê theo nhiều lần chạy độc lập.

## Các bước của thuật toán
### Bước 1. Đọc input và loại sớm case đặc biệt
- Đọc `N, M, Q, d, q`
- Nếu đơn hàng rỗng thì trả `([], 0, 0.0)`
- Nếu tổng cung của một sản phẩm nhỏ hơn nhu cầu thì trả `([], -1, -1)`

### Bước 2. Khởi tạo thời gian
- Đặt `algorithm_start`
- Đặt `deadline = algorithm_start + time_limit`

### Bước 3. Khởi tạo nghiệm ban đầu
- tạo `current_state = list(range(1, M + 1))`
- xáo trộn ngẫu nhiên bằng `random.shuffle(current_state)`
- đánh giá trạng thái ban đầu bằng `evaluate_route()`
- chạy thêm `polish_route()` trên route ban đầu để lấy nghiệm report đầu tiên

Sau đó:
- `best_state = current_state[:]`
- `best_cost = current_report_cost`
- `best_route = current_report_route[:]`
- `t_best` được gán bằng thời gian từ lúc bắt đầu đến thời điểm có nghiệm ban đầu

### Bước 4. Đánh giá một permutation bằng `evaluate_route()`
- Duyệt permutation từ trái sang phải
- Sau mỗi kệ, cập nhật lượng hàng còn thiếu
- Khi đã đủ mọi sản phẩm thì dừng
- Tính quãng đường của prefix đó bằng `compute_route_distance()`

Ý nghĩa:
- nhiệt độ khởi đầu được đặt sao cho một bước đi xấu điển hình có xác suất được chấp nhận khoảng `0.8`

Nếu không thu được mẫu nào:
- `delta_avg = 10.0`
- nếu `T_start <= 0` thì fallback thành `100.0`

### Bước 5. Vòng lặp chính
Trong khi `time.perf_counter() < deadline`, thuật toán:
1. chọn một operator theo roulette wheel từ vector trọng số `w`
2. sinh `neighbor_state`
3. đánh giá `neighbor_cost`, `neighbor_route`
4. quyết định accept/reject theo quy tắc SA
5. cập nhật thống kê theo epoch
6. cập nhật nghiệm tốt nhất nếu có cải thiện
7. khi đủ 1 epoch thì cập nhật trọng số operator và nhiệt độ
8. nếu bị kẹt đủ lâu thì re-anneal

---

## 4. Hàm đánh giá `evaluate_route()`

Đây là phần chuyển từ một hoán vị đầy đủ sang nghiệm thực sự của bài toán.

Luồng đánh giá:
1. `extract_route()` copy nhu cầu còn thiếu sang `remaining_order`
2. tạo `active_items` chỉ chứa các sản phẩm vẫn còn thiếu
3. duyệt lần lượt từng kệ trong permutation
4. với mỗi kệ, chỉ cập nhật các sản phẩm trong `active_items`
5. nếu một sản phẩm vừa đủ, loại nó khỏi vùng active bằng cách swap-compact tại chỗ
6. khi không còn sản phẩm thiếu (`active_count == 0`) thì dừng ngay
7. `evaluate_route()` tính quãng đường của prefix bằng `compute_route_distance(route, d)`

Hệ quả quan trọng:
- phần đầu của permutation có ảnh hưởng mạnh hơn phần cuối
- nhiều biến đổi ở suffix có thể không thay đổi `route` thực tế nếu nhu cầu đã được thỏa mãn từ trước
- implementation hiện tại giảm chi phí đánh giá bằng cách không quét lại các sản phẩm đã đủ

---

## 5. Hàm `polish_route()`

`polish_route()` không thay đổi tập kệ đã chọn, mà chỉ sắp lại thứ tự ghé thăm:
- bước 1: dựng lại route bằng `Nearest Neighbor`
- bước 2: chạy `2-opt` tối đa `MAX_2OPT_PASSES = 1`

Mục tiêu của hàm này là lấy cùng tập kệ nhưng tạo route ngắn hơn để báo cáo `best_route`.

Lưu ý:
- `polish_route()` **không** được gọi cho mọi accepted state
- code hiện tại chỉ gọi `polish_route()` khi `neighbor_cost < current_cost`, tức raw neighbor thực sự cải thiện nghiệm hiện tại

---

## 6. Các toán tử lân cận

Hiện tại solver dùng 3 operator:

### 5.1. `op_swap`
- chọn ngẫu nhiên 2 vị trí `idx1`, `idx2` trong `range(M)`
- hoán đổi hai phần tử ở hai vị trí đó

Ví dụ:
```python
[4, 2, 7, 1] -> swap vị trí 0 và 2 -> [7, 2, 4, 1]
```

### 5.2. `op_insert`
- chọn ngẫu nhiên 2 vị trí
- lấy phần tử ở `idx1`
- bỏ ra khỏi list và chèn lại vào vị trí `idx2`

Ví dụ:
```python
[4, 2, 7, 1] -> lấy 7 ra rồi chèn trước vị trí khác
```

### 5.3. `op_2opt`
- chọn ngẫu nhiên 2 vị trí đã sắp tăng dần
- đảo ngược đoạn con `state[idx1:idx2]`

Ví dụ:
```python
[4, 2, 7, 1, 3] -> đảo đoạn [2, 7, 1] -> [4, 1, 7, 2, 3]
```

Lưu ý:
- cả 3 operator đều dùng `range(M)` vì chúng thao tác trên **vị trí trong list**
- chúng không dùng `range(1, M + 1)` vì đó là không gian giá trị shelf id, không phải index truy cập list Python

---

## 7. Cơ chế chấp nhận nghiệm của SA

Sau khi có `neighbor_cost`, thuật toán tính:
```python
delta_e = neighbor_cost - current_cost
```

### Nếu `delta_e < 0`
Nghiệm raw mới tốt hơn nên được chấp nhận luôn.

Sau khi accept:
- cập nhật `current_state`, `current_cost`, `current_route`
- chạy `polish_route(current_route)`
- nếu polished cost tốt hơn `best_cost` thì:
  - cập nhật nghiệm report tốt nhất
  - operator nhận điểm `5`
- nếu raw neighbor tốt hơn current nhưng polished cost chưa vượt `best_cost` thì:
  - operator nhận điểm `2`

### Nếu `delta_e >= 0`
Nghiệm mới xấu hơn hoặc bằng, thuật toán vẫn có thể chấp nhận theo xác suất:
```python
p = exp(-delta_e / T)
```

Nếu được chấp nhận:
- operator nhận điểm `1`
- không chạy `polish_route()`

Nếu bị từ chối:
- operator nhận điểm `0`

Điều này cho phép:
- giai đoạn đầu khám phá nhiều
- giai đoạn sau dần trở nên tham lam hơn khi nhiệt độ giảm

---

## 8. Cập nhật trọng số operator theo epoch

Thuật toán gom thống kê theo từng epoch:
- `epoch_length = 100`
- `epoch_accepted`: số bước được chấp nhận trong epoch
- `op_scores[i]`: tổng điểm operator `i`
- `op_counts[i]`: số lần operator `i` được chọn

Khi hết epoch, code hiện tại cập nhật:
```python
new_w = (1 - rho) * w[i] + rho * (op_scores[i] / max(1, op_counts[i]))
w[i] = max(new_w, w_min)
```

Trong đó:
- `rho = 0.2` là tốc độ làm mới trọng số
- `w_min = 0.1` là ngưỡng sàn để không operator nào bị loại hoàn toàn

Ý nghĩa:
- operator nào thường tạo improvement hoặc thường được chấp nhận sẽ có điểm trung bình cao hơn
- operator đó sẽ có xác suất được chọn lớn hơn ở các bước tiếp theo

Sau mỗi epoch, các biến thống kê được reset về 0.

---

## 9. Adaptive Cooling hiện tại

Sau mỗi epoch, thuật toán tính:
```python
R_a = epoch_accepted / epoch_length
```

`R_a` là acceptance rate của epoch vừa xong.

Code hiện tại dùng 3 nhánh:
- nếu `grace_period > 0`: dùng `T = T * alpha`
- nếu `R_a > 0.5`: dùng `T = T * 0.9`
- nếu `R_a < 0.05`: dùng `T = T * 1.1`
- còn lại: dùng `T = T * alpha`

Diễn giải:
- `R_a > 0.5`: đang chấp nhận quá dễ, nên làm nguội nhanh hơn
- `R_a < 0.05`: đang gần như bị kẹt, nên tăng nhẹ nhiệt độ để mở rộng khả năng khám phá
- khoảng giữa: dùng tốc độ làm lạnh cơ sở `alpha`

Các giá trị như `0.5`, `0.05`, `0.9`, `1.1` hiện là **heuristic hard-coded** của implementation hiện tại.

---

## 10. Re-annealing khi bị kẹt

Thuật toán theo dõi:
- `no_improve_cnt`: số bước liên tiếp không tạo ra `best_cost` mới

Khi:
```python
no_improve_cnt >= max_no_improve
```

solver thực hiện re-annealing:

### 9.1. Phục hồi nhiệt độ
```python
T = T_start * reheat_ratio
```

Điều này đưa nhiệt độ quay về mức cao hơn so với trạng thái hiện tại.

### 9.2. Bật `grace_period`
```python
grace_period = grace_period_epochs
```

Với:
- `grace_period_epochs = 2`

Trong giai đoạn này, thuật toán dùng lại `T = T * alpha` thay vì áp dụng logic adaptive cooling đầy đủ.

### 9.3. Perturb từ `best_state`
Code hiện tại không reheat trực tiếp từ `current_state`, mà:
1. copy `current_state = best_state[:]`
2. thực hiện số lần swap ngẫu nhiên bằng `max(1, M // 10)`
3. đánh giá lại trạng thái mới

Mục đích của đoạn này:
- bắt đầu lại từ vùng nghiệm tốt đã biết
- nhưng tạo một nhiễu đủ lớn để không quay lại đúng cùng trạng thái cũ

Đây là cơ chế “break best_state to jump out of local optimum” đang có trong implementation hiện tại.

---

## 11. Ý nghĩa của `t_best`

`t_best` là một chỉ số quan trọng cho thực nghiệm, vì nó cho biết:
- thuật toán cần bao lâu để tìm ra nghiệm tốt nhất mà nó đạt được trong `time_limit`

Không phải lúc nào nghiệm tốt nhất cũng xuất hiện ở cuối thời gian chạy.

Trong code hiện tại:
- `t_best` được khởi tạo sau khi có nghiệm report ban đầu
- mỗi lần polished cost tốt hơn `best_cost`, `t_best` được cập nhật
- giá trị cuối cùng phản ánh thời điểm phát hiện nghiệm report tốt nhất cuối cùng

Điều này hữu ích khi so sánh:
- chất lượng nghiệm
- tốc độ hội tụ
- mức độ “tìm nhanh nghiệm tốt” của các cấu hình SA khác nhau

---

## 12. Lưu ý về implementation hiện tại

Tài liệu này mô tả đúng theo code hiện có trong `adaptive_simulated_annealing.py`, không khẳng định rằng mọi lựa chọn heuristic đều là tối ưu.

Các chi tiết hiện đang hard-coded trong implementation:
- `epoch_length = 100`
- `grace_period_epochs = 2`
- `rho = 0.2`
- `w_min = 0.1`
- adaptive cooling dùng các mốc `0.5` và `0.05`
- hệ số làm nguội nhanh `0.9`
- hệ số warm-up `1.1`
- re-annealing perturb bằng khoảng `10%` số vị trí trong permutation

Ngoài ra, vì lời giải thực tế là một prefix của permutation:
- thay đổi ở đầu permutation thường quan trọng hơn
- thay đổi ở cuối permutation có thể không ảnh hưởng gì nếu đơn hàng đã được thỏa mãn trước đó

Đây là điểm rất quan trọng khi phân tích hành vi của các operator và chất lượng perturbation.

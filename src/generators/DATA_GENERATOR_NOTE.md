# data_generator — Bộ sinh dữ liệu đầu vào cho bài toán tối ưu tuyến đường kho hàng

**Phiên bản:** 2.0.0  
**Ngôn ngữ:** Python >= 3.11  
**Phụ thuộc ngoài:** Không có (chỉ dùng thư viện chuẩn)  
**Cập nhật lần cuối:** 2026-03-24

---

## 1. Mô tả bài toán

Một kho hàng có M kệ đánh số từ 1 đến M. Kho lưu N loại sản phẩm; lượng sản phẩm loại i trên kệ j ký hiệu là Q[i][j]. Nhân viên xuất phát từ cửa kho (điểm 0), chọn một chuỗi kệ để ghé thăm (mỗi kệ không quá một lần), thu gom đủ số lượng từng loại sản phẩm theo đơn hàng q[1..N], rồi quay lại cửa. Mục tiêu là tối thiểu tổng quãng đường di chuyển.

`data_generator.py` không giải bài toán này. Nhiệm vụ của nó là sinh ra các file dữ liệu đầu vào hợp lệ theo đúng định dạng yêu cầu, phục vụ việc kiểm thử thuật toán. Người dùng có thể kiểm soát kích thước dữ liệu, không gian tọa độ, mật độ tài nguyên và tính khả thi của bài toán qua giao diện dòng lệnh tương tác.

---

## 2. Định dạng file đầu ra

File được lưu với phần mở rộng `.in`, đặt trong thư mục `data/` (cùng cấp với `src/`). Tên file theo cấu trúc:

```
test_{N}_{M}_{YYYYMMDD_HHMMSS}.in
```

Ví dụ: `test_6_5_20260324_153045.in`

Nội dung bên trong:

```
Dòng 1            : N M
Dòng 2 .. N+1     : N hàng của ma trận Q  (mỗi hàng M số nguyên, cách nhau bởi dấu cách)
Dòng N+2..N+M+2   : (M+1) hàng của ma trận khoảng cách d  ((M+1) x (M+1) số)
Dòng N+M+3        : N số nguyên không âm q[1], q[2], ..., q[N]
```

Hàng đầu tiên của ma trận khoảng cách (dòng N+2) tương ứng với điểm 0 là cửa kho. Các hàng tiếp theo tương ứng với kệ 1, 2, ..., M theo thứ tự.

---

## 3. Cài đặt và chạy

### 3.1. Yêu cầu môi trường

- Python 3.11 trở lên.
- Không cần cài thêm bất kỳ gói nào (`math`, `os`, `random`, `datetime` đều là thư viện chuẩn).

### 3.2. Chạy chương trình

```bash
python data_generator.py
```

Chương trình chạy hoàn toàn qua giao diện dòng lệnh tương tác, hỏi tuần tự các tham số đầu vào theo pipeline 4 bước, sau đó tự động sinh và lưu file.

---

## 4. Hướng dẫn sử dụng từng bước

### Bước 1 — Nhập tham số cấu hình

Chương trình hỏi tuần tự 5 thông tin. Với mỗi câu hỏi, nhấn Enter để chấp nhận giá trị mặc định. Nếu nhập sai kiểu hoặc ngoài phạm vi, chương trình yêu cầu nhập lại ngay tại chỗ.

| Tham số | Kiểu | Ràng buộc | Mặc định |
|---|---|---|---|
| N — số loại sản phẩm | Số nguyên dương | 1 <= N <= 50 | 5 |
| M — số kệ hàng | Số nguyên dương | 1 <= M <= 1000 | 10 |
| COORD_BOUND — biên tọa độ | Số nguyên dương | M <= COORD_BOUND <= 759250124 | 759250124 |
| MAX_RESOURCE_I_PER_SHELF — tồn kho tối đa mỗi kệ | Số nguyên dương | 1 <= giá trị <= 1000 | 100 |
| Chế độ sinh q | Y / N / D | Nhập Y, N hoặc D (có thể gõ chữ thường) | D |

**COORD_BOUND** quyết định kích thước hộp tọa độ trong bước sinh vị trí kệ. Tất cả tọa độ đều nằm trong đoạn $[-\text{COORD\_BOUND}, \text{COORD\_BOUND}]$. Giá trị lớn → kệ phân tán rộng hơn; giá trị nhỏ → kệ gần nhau hơn. Chương trình luôn nhắc rõ phạm vi hợp lệ trước khi yêu cầu nhập.

**MAX_RESOURCE_I_PER_SHELF** là tồn kho tối đa một kệ có thể chứa cho mỗi loại sản phẩm. Nó vừa là biên trên của từng phần tử $Q[i][j]$, vừa quyết định miền giá trị của vector $q$ khi chọn chế độ mặc định (D).

Chi tiết về COORD_BOUND và chế độ tính khả thi được giải thích ở Bước 3 và Bước 4.

### Bước 2 — Sinh ma trận tài nguyên Q (N x M)

Mỗi phần tử Q[i][j] là số nguyên ngẫu nhiên trong [0, MAX_RESOURCE_I_PER_SHELF]. Giá trị 0 được chấp nhận — kệ j có thể không chứa sản phẩm loại i.

### Bước 3 — Sinh ma trận khoảng cách d ((M+1) x (M+1))

Quá trình gồm hai giai đoạn.

**Giai đoạn 3a — Sinh tọa độ 2D:**

Chương trình sinh ngẫu nhiên M cặp số nguyên (x, y) làm tọa độ cho M kệ trong mặt phẳng Oxy. Mỗi điểm phải thoả mãn hai điều kiện: không trùng gốc toạ độ (0, 0) là vị trí cửa kho, và không trùng bất kỳ điểm nào đã sinh trước đó. Nếu trùng, chương trình sinh lại cho đến khi hợp lệ.

Tọa độ được giới hạn trong [-COORD_BOUND, COORD_BOUND] theo hai ràng buộc:

- **Giới hạn trên — 759250124:** Được suy từ điều kiện ceil(khoảng cách Euclidean tối đa) phải nằm trong phạm vi số nguyên có dấu 32-bit. Khoảng cách tối đa giữa hai điểm là `2 * COORD_BOUND * sqrt(2)`; để giá trị này <= 2^31 - 1, cần COORD_BOUND <= (2^31 - 1) / (2 * sqrt(2)) = 759250124.

- **Giới hạn dưới — M:** Đảm bảo không gian tọa độ đủ rộng để luôn tìm được M điểm nguyên phân biệt, tránh vòng lặp sinh lại kéo dài khi M lớn và COORD_BOUND nhỏ.

**Giai đoạn 3b — Tính khoảng cách:**

Khoảng cách Euclidean giữa mọi cặp điểm được tính và luôn được làm tròn lên số nguyên bằng `math.ceil()`. Ma trận kết quả là ma trận đối xứng (M+1) x (M+1), đường chéo bằng 0.

### Bước 4 — Sinh vector yêu cầu q (N phần tử)

Chế độ sinh q được điều khiển bởi tham số feasibility:

**Y — feasible (có nghiệm):**
Với mỗi sản phẩm i, q[i] được chọn ngẫu nhiên trong [0, tổng Q[i][j] trên toàn bộ kệ]. Điều này đảm bảo với mọi i, tổng tài nguyên loại i hiện có trong kho >= q[i], tức bài toán luôn có nghiệm (theo nghĩa đủ hàng, không xét ràng buộc lộ trình).

**N — infeasible (vô nghiệm):**
Với mỗi sản phẩm i, q[i] được chọn ngẫu nhiên trong [tổng Q[i][j] + 1, max(tổng Q[i][j] + 100, max_resource * M)]. Điều này đảm bảo với mọi i, nhu cầu của khách hàng vượt toàn bộ lượng tồn kho loại i, tức bài toán chắc chắn vô nghiệm.

**D — default (hoàn toàn ngẫu nhiên, mặc định):**
q[i] được chọn ngẫu nhiên trong [0, MAX_RESOURCE_I_PER_SHELF * M]. Không có bảo đảm nào về tính khả thi; bài toán có thể có hoặc không có nghiệm.

---

## 5. Tổng hợp các tham số cấu hình

### 5.1. Hằng số cứng trong mã nguồn (không nhập qua giao diện)

| Tên hằng số | Giá trị | Ý nghĩa |
|---|---|---|
| `COORD_BOUND_MAX` | 759250124 | Giới hạn trên tuyệt đối của COORD_BOUND; đảm bảo khoảng cách fit signed 32-bit |
| `MAX_RESOURCE_HARD_CAP` | 1000 | Giới hạn trên tuyệt đối của MAX_RESOURCE_I_PER_SHELF |

### 5.2. Tham số nhập qua giao diện

| Tên tham số | Mặc định | Ảnh hưởng đến |
|---|---|---|
| N | 5 | Số hàng ma trận Q; độ dài vector q |
| M | 10 | Số cột ma trận Q; kích thước ma trận khoảng cách |
| COORD_BOUND | 759250124 | Kích thước vùng đặt tọa độ kệ |
| MAX_RESOURCE_I_PER_SHELF | 100 | Tồn kho tối đa mỗi kệ cho từng loại |
| feasibility | D | Cách sinh vector q |

---

## 6. Cấu trúc mã nguồn

```
data_generator.py
|
+-- Hằng số cứng
|   +-- COORD_BOUND_MAX
|   +-- MAX_RESOURCE_HARD_CAP
|
+-- Helpers
|   +-- _ask_int()          nhập số nguyên có validation + mặc định
|   +-- _ask_feasibility()  nhập Y/N/D (chấp nhận chữ hoa và chữ thường)
|   +-- _euclidean()        tính khoảng cách Euclidean và làm tròn lên số nguyên
|
+-- Pipeline chính
|   +-- step1_get_params()            nhập 6 tham số từ người dùng
|   +-- step2_gen_resource_matrix()   sinh ma trận Q
|   +-- step3_gen_distance_matrix()   sinh tọa độ và ma trận khoảng cách
|   +-- step4_gen_demand()            sinh vector q theo chế độ feasibility
|
+-- write_output()   ghi toàn bộ dữ liệu ra file .in
+-- main()           điều phối pipeline, in tóm tắt kết quả
```

---

## 7. Ví dụ phiên chạy

Phiên chạy dưới đây dùng mọi giá trị mặc định ngoại trừ N và M:

```
============================================================
     SINH INPUT BÀI TOÁN TÌM ĐƯỜNG ĐI TỐI ƯU KHO HÀNG
============================================================

Nhập số loại sản phẩm  N  (1 <= N <= 50)    [mặc định = 5]  : 6
Nhập số kệ hàng        M  (1 <= M <= 1000)  [mặc định = 10] : 5

  (Giới hạn hợp lệ cho COORD_BOUND: [5, 759250124])
Nhập COORD_BOUND  (>= M=5, <= 759250124)  [mặc định = 759250124]:
  -> Dùng giá trị mặc định: 759250124

Nhập MAX_RESOURCE_I_PER_SHELF  (1 <= giá trị <= 1000)  [mặc định = 100]:
  -> Dùng giá trị mặc định: 100

Chế độ sinh yêu cầu q (nhập Y, N hoặc D):
  Y = đảm bảo có nghiệm (feasible)
  N = đảm bảo vô nghiệm (infeasible)
  D = hoàn toàn ngẫu nhiên (mặc định)
Lựa chọn [D]: y

Dang sinh du lieu...

Da tao file thanh cong!
  Ten file      : test_6_5_20260324_153045.in
  Duong dan     : /home/user/project/test_6_5_20260324_153045.in
  N = 6, M = 5
  Khoang cach   : so nguyen (ceil)
  COORD_BOUND   : 759250124
  MAX_RESOURCE  : 100
  Tinh kha thi  : co nghiem (feasible)
```

---

## 8. Lưu ý kỹ thuật

**Tính ngẫu nhiên:** Module `random` được dùng với seed hệ thống — mỗi lần chạy cho kết quả khác nhau. Nếu cần tái lập kết quả để debug, thêm `random.seed(<giá trị>)` vào đầu hàm `main()`.

**Tránh trùng tọa độ:** Chương trình dùng một `set` để kiểm tra va chạm (collision). Với COORD_BOUND lớn (mặc định ~7.59 * 10^8), không gian tọa độ có kích thước ~(1.52 * 10^9)^2, xác suất trùng cực nhỏ nên vòng lặp kiểm tra hầu như luôn chỉ chạy một lần mỗi điểm. Ràng buộc COORD_BOUND >= M là phòng ngừa cho trường hợp người dùng chủ động đặt COORD_BOUND nhỏ.

**Chế độ infeasible và trường hợp biên:** Khi tổng Q[i][j] đã bằng MAX_RESOURCE_I_PER_SHELF * M (kho đầy tối đa), không còn giá trị q[i] nào trong [0, max_demand] lớn hơn tổng kho. Chương trình xử lý bằng cách mở rộng cận trên lên `max(supply + 100, max_demand)`, đảm bảo luôn sinh được q[i] > supply.

**Định dạng số:** File ghi với encoding UTF-8, toàn bộ ma trận khoảng cách đều là số nguyên dương (làm tròn lên) và sử dụng dấu chấm cho bất kỳ giá trị nào cần dấu phân cách thập phân trong tương lai.

**Tính đối xứng ma trận khoảng cách:** d[i][j] = d[j][i] và d[i][i] = 0 với mọi i, j — đúng với khoảng cách Euclidean trong không gian 2D.

**Lưu ý về tên file:** Timestamp đến giây (HHMMSS). Nếu hai file được tạo trong cùng một giây với cùng N và M, tên file sẽ trùng và file sau ghi đè file trước. Trong thực tế điều này không xảy ra vì mỗi phiên tương tác mất ít nhất vài giây.

---

## 9. Hướng phát triển tiếp theo

**9.1. Chế độ batch qua dòng lệnh**  
Thêm argparse để sinh nhiều file cùng lúc mà không cần tương tác, phục vụ pipeline kiểm thử tự động. Ví dụ: `python data_generator.py --n 10 --m 50 --count 20 --feasibility Y`.

**9.2. Tách biệt feasibility từng sản phẩm**  
Hiện tại chế độ Y và N áp dụng đồng đều cho mọi sản phẩm. Có thể bổ sung chế độ "partial" — chỉ một số sản phẩm được đảm bảo, số còn lại random — phục vụ kiểm thử các trường hợp khả thi một phần.

**9.3. Cấu trúc tọa độ có kiểm soát**  
Hiện tại các kệ phân bố ngẫu nhiên đều trong toàn bộ không gian. Có thể thêm tùy chọn sinh theo cụm (cluster), theo lưới đều, hay dọc theo một hành lang để tạo trường hợp kiểm thử có đặc trưng hình học cụ thể, giúp phân tích hành vi thuật toán sâu hơn.

**9.4. Công thức khoảng cách thay thế**  
Hàm `_euclidean()` được thiết kế độc lập. Có thể bổ sung tùy chọn khoảng cách Manhattan hoặc Chebyshev bằng cách thêm tham số `metric` vào Bước 1 và phân nhánh trong hàm tính khoảng cách.

**9.5. Xác nhận và log tự động**  
Thêm bước đọc lại file vừa sinh, kiểm tra tính nhất quán (kích thước ma trận, tính đối xứng, tính khả thi nếu chọn chế độ Y/N) và ghi log tóm tắt ra file `.log` đi kèm mỗi file `.in`.

**9.6. Seed tái lập có thể cấu hình**  
Cho phép người dùng nhập seed ngẫu nhiên qua tham số tương tác hoặc dòng lệnh, tự động ghi seed vào tên file hoặc file log để dễ tái tạo đúng bộ dữ liệu khi cần debug.

---

*Tài liệu này mô tả trạng thái của phiên bản 2.0.0. Mọi thay đổi về hành vi chương trình cần được cập nhật đồng bộ vào tài liệu này.*

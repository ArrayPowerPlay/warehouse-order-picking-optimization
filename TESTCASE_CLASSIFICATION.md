# Phân loại Test Cases theo quy mô

> **Quy tắc phân nhóm:** Dựa trên **M** (số kệ hàng) — yếu tố quyết định độ phức tạp tính toán (ma trận khoảng cách O(M²), không gian tìm kiếm route trên M kệ).

| Nhóm | Điều kiện M | Điều kiện N | Số test |
|---|---|---|---|
| **Small** | M ≤ 20 | N ≤ 10 | 5 |
| **Medium** | 50 ≤ M ≤ 400 | 10 ≤ N ≤ 35 | 21 |
| **Large** | M ≥ 500 | 40 ≤ N ≤ 50 | 13 |

> **Lưu ý:** N thường scale cùng M, nhưng khi N và M rơi vào nhóm khác nhau (ví dụ N=20, M=600), **M quyết định nhóm** → Large.

---

## Small (5 test cases) — M ≤ 20

| # | Tên file | N | M | Loại | Ghi chú |
|---|---|---|---|---|---|
| 01 | `small_01_N2_M5.in` | 2 | 5 | Standard | Debug bằng tay |
| 02 | `small_02_N3_M10.in` | 3 | 10 | Standard | Debug bằng tay |
| 03 | `small_03_N5_M10.in` | 5 | 10 | Standard | Debug bằng tay |
| 04 | `small_04_N5_M20.in` | 5 | 20 | Standard | Debug bằng tay |
| 05 | `small_05_N10_M20.in` | 10 | 20 | Standard | Debug bằng tay |

---

## Medium (21 test cases) — 50 ≤ M ≤ 400

| # | Tên file | N | M | Loại | Ghi chú |
|---|---|---|---|---|---|
| 06 | `medium_06_N10_M50.in` | 10 | 50 | Standard | Uniform Random |
| 07 | `medium_07_N10_M100.in` | 10 | 100 | Standard | Uniform Random |
| 08 | `medium_08_N15_M100.in` | 15 | 100 | Standard | Uniform Random |
| 09 | `medium_09_N15_M150.in` | 15 | 150 | Standard | Uniform Random |
| 10 | `medium_10_N20_M150.in` | 20 | 150 | Standard | Uniform Random |
| 11 | `medium_11_N20_M200.in` | 20 | 200 | Standard | Uniform Random |
| 12 | `medium_12_N25_M200.in` | 25 | 200 | Standard | Uniform Random |
| 13 | `medium_13_N25_M250.in` | 25 | 250 | Standard | Uniform Random |
| 14 | `medium_14_N30_M250.in` | 30 | 250 | Standard | Uniform Random |
| 15 | `medium_15_N30_M300.in` | 30 | 300 | Standard | Uniform Random |
| 16 | `medium_16_N35_M300.in` | 35 | 300 | Standard | Uniform Random |
| 17 | `medium_17_N35_M400.in` | 35 | 400 | Standard | Uniform Random |
| 23 | `edge_N1_23_N1_M300.in` | 1 | 300 | Edge Case | 1 sản phẩm (gần TSP) |
| 25 | `edge_infeas_25_N20_M100.in` | 20 | 100 | Edge Case | Guaranteed infeasible |
| 26 | `edge_infeas_26_N30_M200.in` | 30 | 200 | Edge Case | Guaranteed infeasible |
| 31 | `dist_corner_31_N15_M150.in` | 15 | 150 | Distribution | Corner Biased |
| 32 | `dist_corner_32_N30_M300.in` | 30 | 300 | Distribution | Corner Biased |
| 34 | `dist_cluster_34_N15_M150.in` | 15 | 150 | Distribution | Clustered |
| 35 | `dist_cluster_35_N30_M300.in` | 30 | 300 | Distribution | Clustered |
| 37 | `dist_diagonal_37_N15_M150.in` | 15 | 150 | Distribution | Diagonal |
| 38 | `dist_diagonal_38_N30_M300.in` | 30 | 300 | Distribution | Diagonal |

---

## Large (13 test cases) — M ≥ 500

| # | Tên file | N | M | Loại | Ghi chú |
|---|---|---|---|---|---|
| 18 | `large_18_N40_M500.in` | 40 | 500 | Standard | Uniform Random |
| 19 | `large_19_N40_M800.in` | 40 | 800 | Standard | Uniform Random |
| 20 | `large_20_N50_M800.in` | 50 | 800 | Standard | Uniform Random |
| 21 | `large_21_N50_M1000.in` | 50 | 1000 | Standard | Uniform Random |
| 22 | `large_22_N50_M1000.in` | 50 | 1000 | Standard | Uniform Random (trần tuyệt đối) |
| 24 | `edge_N1_24_N1_M500.in` | 1 | 500 | Edge Case | 1 sản phẩm (gần TSP) |
| 27 | `edge_sparse_27_N40_M800.in` | 40 | 800 | Edge Case | 90% kệ trống |
| 28 | `edge_sparse_28_N50_M1000.in` | 50 | 1000 | Edge Case | 90% kệ trống |
| 29 | `edge_dense_29_N40_M500.in` | 40 | 500 | Edge Case | Kho đầy, nhu cầu nhỏ |
| 30 | `edge_dense_30_N50_M1000.in` | 50 | 1000 | Edge Case | Kho đầy, nhu cầu nhỏ |
| 33 | `dist_corner_33_N50_M800.in` | 50 | 800 | Distribution | Corner Biased |
| 36 | `dist_cluster_36_N50_M800.in` | 50 | 800 | Distribution | Clustered |
| 39 | `dist_diagonal_39_N50_M800.in` | 50 | 800 | Distribution | Diagonal |

---

## Tổng hợp theo loại test case

| Loại | Small | Medium | Large | Tổng |
|---|---|---|---|---|
| Standard (Uniform Random) | 5 | 12 | 5 | 22 |
| Edge Case | 0 | 3 | 5 | 8 |
| Distribution (Corner/Cluster/Diagonal) | 0 | 6 | 3 | 9 |
| **Tổng** | **5** | **21** | **13** | **39** |

---

*Cập nhật lần cuối: 2026-05-14*

import os
import math
import pandas as pd
import re

# 1. Cấu hình PATH (Hard-code theo yêu cầu)
BASE_PATH = "../results/phase2"
OUTPUT_CSV = os.path.join(BASE_PATH, "aggregate_result.csv")


def extract_id_number(testcase_name):
    """
    Trích xuất số ID của testcase để sắp xếp.
    Ví dụ: small_26_N30_M200 -> 26
    """
    match = re.search(r'(\d+)', testcase_name)
    return int(match.group(1)) if match else math.inf


def extract_dist_subgroup(testcase_name):
    """
    Trích xuất nhóm nhỏ (subgroup) của dist_ để sắp xếp theo alphabet.
    Ví dụ: dist_cluster_35_N30 -> 'cluster'
    """
    match = re.match(r'^dist_([a-zA-DR-Z0-9_]+?)(?:_\d+|$)', testcase_name)
    return match.group(1) if match else ""


def testcase_sort_key(name):
    """
    Quy tắc sắp xếp ưu tiên (Hàm mục 4):
    small -> medium -> large -> edge -> dist_ + phân loại (alphabet) -> others
    Trong từng nhóm sắp xếp theo số ID tăng dần.
    """
    id_num = extract_id_number(name)
    
    if name.startswith("small_"):
        return (0, id_num, name)
    elif name.startswith("medium_"):
        return (1, id_num, name)
    elif name.startswith("large_"):
        return (2, id_num, name)
    elif name.startswith("edge_"):
        return (3, id_num, name)
    elif name.startswith("dist_"):
        subgroup = extract_dist_subgroup(name)
        return (4, subgroup, id_num, name)
    else:
        return (5, 0, id_num, name)


def determine_group(name):
    """
    Xác định giá trị cho trường 'group' dựa trên tiền tố của testcase.
    Đối với dist, group sẽ là 'dist_' + phân loại (Ví dụ: dist_cluster, dist_corner)
    """
    if name.startswith("small_"):
        return "small"
    elif name.startswith("medium_"):
        return "medium"
    elif name.startswith("large_"):
        return "large"
    elif name.startswith("edge_"):
        return "edge"
    elif name.startswith("dist_"):
        # Trích xuất "dist_cluster", "dist_corner", "dist_diagonal"
        match = re.match(r'^(dist_[a-zA-Z0-9]+)', name)
        return match.group(1) if match else "dist"
    return "other"


def main():
    print(f"[*] Đang quét và xử lý dữ liệu tại thư mục: {BASE_PATH}")
    
    if not os.path.exists(BASE_PATH):
        print(f"[ERROR] Thư mục {BASE_PATH} không tồn tại!")
        return

    # Danh sách chứa tất cả các dataframe từ các file thuật toán
    all_dfs = []
    
    # Duyệt qua toàn bộ các file .csv trong thư mục base
    for filename in os.listdir(BASE_PATH):
        if not filename.endswith(".csv") or filename == "aggregate_result.csv":
            continue
            
        file_path = os.path.join(BASE_PATH, filename)
        algo_name = os.path.splitext(filename)[0].lower() # Tên thuật toán (ví dụ: cpsat, asa)
        
        try:
            # Đọc file csv, chỉ lấy 2 cột cần thiết để tối ưu hiệu năng
            df = pd.read_csv(file_path, usecols=["testcase", "cost_min"])
            
            # Áp dụng quy tắc lọc dựa trên tài liệu gốc:
            # - cpsat chỉ xử lý cấu hình cho các testcase 'small'
            # - các thuật toán khác xử lý large, medium (và các nhóm dist, edge nếu có)
            if algo_name == "cpsat":
                df = df[df["testcase"].str.startswith("small_")]
            else:
                df = df[~df["testcase"].str.startswith("small_")]
                
            if not df.empty:
                all_dfs.append(df)
                print(f"  [+] Đã đọc thành công {len(df)} bản ghi từ file: {filename}")
                
        except Exception as e:
            print(f"  [WARNING] Lỗi khi đọc file {filename}: {e}")

    if not all_dfs:
        print("[ERROR] Không tìm thấy dữ liệu hợp lệ từ các file csv thuật toán!")
        return

    # Gộp tất cả các bảng dữ liệu lại thành 1 bảng tổng thế
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Xử lý logic tìm cost_reference:
    # 1. Tạo một cột tạm thời để tính toán `min`, đổi các giá trị -1 thành vô cùng (inf) 
    #    để không bị hàm min() chọn nhầm, vì -1 là lỗi/infeasible chứ không phải chi phí tối ưu.
    combined_df["cost_temp"] = combined_df["cost_min"].apply(lambda x: float('inf') if x <= 0 else x)

    # 2. Groupby theo từng testcase và tìm giá trị nhỏ nhất của cost_temp
    agg_df = combined_df.groupby("testcase")["cost_temp"].min().reset_index()

    # 3. Trả ngược lại giá trị -1 cho các trường hợp mà TẤT CẢ các thuật toán đều trả về -1 (giá trị inf)
    agg_df["cost_reference"] = agg_df["cost_temp"].apply(lambda x: -1 if x == float('inf') else int(x))
    
    # Loại bỏ cột phụ tạm thời
    agg_df = agg_df.drop(columns=["cost_temp"])

    # 4. Gán trường 'group' theo quy tắc tự động hóa từ tên testcase
    agg_df["group"] = agg_df["testcase"].apply(determine_group)

    # 5. Thực hiện sắp xếp các hàng theo đúng thứ tự logic đã quy định
    # Chuyển đổi sang danh sách các bản ghi để tận dụng hàm testcase_sort_key đồng nhất với Phase 1
    records = agg_df.to_dict(orient="records")
    records_sorted = sorted(records, key=lambda x: testcase_sort_key(x["testcase"]))
    
    # Chuyển ngược lại thành DataFrame hoàn chỉnh với đúng 3 cột theo cấu trúc yêu cầu
    final_df = pd.DataFrame(records_sorted)[["testcase", "cost_reference", "group"]]

    # 6. Xuất và lưu kết quả cuối cùng
    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[SUCCESS] Đã gộp và lưu file thành công tại: {OUTPUT_CSV}")
    print(f"[#] Tổng số lượng testcase đã tổng hợp: {len(final_df)}")
    


if __name__ == "__main__":
    main()
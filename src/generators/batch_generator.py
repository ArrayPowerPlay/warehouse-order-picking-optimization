import os
import random
from data_generator import (
    step2_gen_resource_matrix,
    step3_gen_distance_matrix,
    step4_gen_demand
)

def generate_dataset(dataset_name: str, configs: list):
    """
    Sinh toàn bộ dataset dựa trên cấu hình (configs) và lưu vào thư mục tương ứng.
    Thư mục sẽ được tự động tạo trong thư mục cha (../data/dataset_name).
    """
    
    # Tạo thư mục lưu trữ (ví dụ: ../data/val_set)
    # Script nằm tại src/generators/ nên cần lên 2 cấp để tới project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir, "data", dataset_name))
    os.makedirs(base_dir, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f" ĐANG SINH TẬP DỮ LIỆU: {dataset_name.upper()}")
    print(f"{'='*50}")
    
    for idx, conf in enumerate(configs, 1):
        n = conf['N']
        m = conf['M']
        feasibility = conf.get('feas', 'Y') # Mặc định là có nghiệm
        max_res = conf.get('max_res', 100)
        prefix = conf.get('prefix', 'test')
        
        # Không gian kho được nới rộng tỷ lệ thuận với số kệ
        coord_bound = m * 10 
        
        # 1. Gọi hàm sinh dữ liệu gốc
        Q = step2_gen_resource_matrix(n, m, max_res)
        dist = step3_gen_distance_matrix(m, coord_bound)
        q = step4_gen_demand(n, m, Q, max_res, feasibility)
        
        # =======================================================
        # BẮT ĐẦU CAN THIỆP (OVERRIDE) ĐỂ TẠO EDGE CASE
        # =======================================================
        if prefix == 'edge_sparse':
            # Ép 90% kệ hàng trống rỗng, 10% có lượng hàng rất nhỏ
            for i in range(n):
                for j in range(m):
                    if random.random() < 0.90:
                        Q[i][j] = 0
                    else:
                        Q[i][j] = random.randint(1, 5)
            # Vì Q đã thay đổi, phải sinh lại q để đảm bảo bài toán vẫn CÓ NGHIỆM
            q = step4_gen_demand(n, m, Q, max_res, "Y")
            
        elif prefix == 'edge_dense':
            # Ép tất cả các kệ đều đầy ắp hàng (nhà kho đại gia)
            for i in range(n):
                for j in range(m):
                    Q[i][j] = random.randint(1000, 5000)
            # Nhu cầu khách hàng lại cực kỳ nhỏ
            q = [random.randint(10, 20) for _ in range(n)]
        # =======================================================
        
        # 2. Định dạng tên file chuẩn (ví dụ: medium_06_N20_M150.in)
        filename = f"{prefix}_{idx:02d}_N{n}_M{m}.in"
        out_path = os.path.join(base_dir, filename)
        
        # 3. Ghi ra file (tái sử dụng logic ghi file nhưng ghi thẳng vào thư mục đích)
        lines = [f"{n} {m}"]
        for row in Q:
            lines.append(" ".join(map(str, row)))
        for row in dist:
            lines.append(" ".join(map(str, row)))
        lines.append(" ".join(map(str, q)))
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
            
        print(f"[{idx:02d}/{len(configs)}] Đã sinh: {filename}")

if __name__ == "__main__":
    # ĐỊNH NGHĨA "CÔNG THỨC" (RECIPE) CHO MỘT TẬP DỮ LIỆU CHUẨN
    dataset_recipe = [
        # --- NHÓM 1: SMALL (5 test) - Dùng để debug logic bằng tay ---
        {'prefix': 'small', 'N': 2, 'M': 5},
        {'prefix': 'small', 'N': 3, 'M': 10},
        {'prefix': 'small', 'N': 5, 'M': 10},
        {'prefix': 'small', 'N': 5, 'M': 20},
        {'prefix': 'small', 'N': 10, 'M': 20},
        
        # --- NHÓM 2: MEDIUM (12 test) - Dùng để đánh giá hiệu năng trung bình ---
        {'prefix': 'medium', 'N': 10, 'M': 50},
        {'prefix': 'medium', 'N': 10, 'M': 100},
        {'prefix': 'medium', 'N': 15, 'M': 100},
        {'prefix': 'medium', 'N': 15, 'M': 150},
        {'prefix': 'medium', 'N': 20, 'M': 150},
        {'prefix': 'medium', 'N': 20, 'M': 200},
        {'prefix': 'medium', 'N': 25, 'M': 200},
        {'prefix': 'medium', 'N': 25, 'M': 250},
        {'prefix': 'medium', 'N': 30, 'M': 250},
        {'prefix': 'medium', 'N': 30, 'M': 300},
        {'prefix': 'medium', 'N': 35, 'M': 300},
        {'prefix': 'medium', 'N': 35, 'M': 400},
        
        # --- NHÓM 3: LARGE (5 test) - Stress test, ép thuật toán tới giới hạn ---
        {'prefix': 'large', 'N': 40, 'M': 500},
        {'prefix': 'large', 'N': 40, 'M': 800},
        {'prefix': 'large', 'N': 50, 'M': 800},
        {'prefix': 'large', 'N': 50, 'M': 1000},
        {'prefix': 'large', 'N': 50, 'M': 1000}, # Chạm trần tuyệt đối
        
        # --- NHÓM 4: EDGE CASES (8 test) - Thử thách các điểm mù của thuật toán ---
        {'prefix': 'edge_N1', 'N': 1, 'M': 300},       # Chỉ order 1 loại (Bài toán TSP)
        {'prefix': 'edge_N1', 'N': 1, 'M': 500}, 
        {'prefix': 'edge_infeas', 'N': 20, 'M': 100, 'feas': 'N'}, # Chắc chắn vô nghiệm
        {'prefix': 'edge_infeas', 'N': 30, 'M': 200, 'feas': 'N'}, 
        {'prefix': 'edge_sparse', 'N': 40, 'M': 800},  # Kho nghèo (Override 90% zero)
        {'prefix': 'edge_sparse', 'N': 50, 'M': 1000}, 
        {'prefix': 'edge_dense', 'N': 40, 'M': 500},   # Kho đặc (Override full hàng)
        {'prefix': 'edge_dense', 'N': 50, 'M': 1000},  
    ]
    
    # 1. Sinh tập Validation (Dùng để Grid Search / Tune tham số)
    generate_dataset("val_set", dataset_recipe)
    
    # 2. Sinh tập Test (Dùng để thi đấu chéo sau khi đã chọn được tham số tốt nhất)
    # Lần gọi này hàm random của Python sẽ tự tiếp tục chạy, 
    # tạo ra số liệu con số HOÀN TOÀN KHÁC với tập val_set, dù cấu trúc M, N giống hệt.
    generate_dataset("test_set", dataset_recipe)
    
    print("\n✅ HOÀN TẤT! Hãy kiểm tra thư mục 'data/val_set' và 'data/test_set'.")
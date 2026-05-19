"""
Genetic Algorithm (GA) wrapper for Warehouse Order Picking Optimization.

The solver stops by time limit and returns:
    route, total_distance, t_best
"""
import argparse
import os
import sys
import subprocess

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Các tham số mặc định cho GA
DEFAULT_TIME_LIMIT = 5.0
DEFAULT_POP_SIZE = 100
DEFAULT_CROSSOVER_RATE = 0.8
DEFAULT_MUTATION_RATE = 0.1

def ga_solver(
    time_limit: float,
    pop_size: int = DEFAULT_POP_SIZE,
    crossover_rate: float = DEFAULT_CROSSOVER_RATE,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
):
    """Run GA (C++ core) and return route, total distance, and t_best."""
    
    # Xác định đường dẫn file thực thi C++ (Nằm cùng thư mục với file ga.py này)
    # Tùy hệ điều hành mà file có đuôi .exe (Windows) hoặc không đuôi (Linux/Mac)
    base_dir = os.path.dirname(__file__)
    cpp_executable = os.path.join(base_dir, "ga_core.exe") 
    if not os.path.exists(cpp_executable):
        cpp_executable = os.path.join(base_dir, "ga_core")
        if not os.path.exists(cpp_executable):
            raise FileNotFoundError(f"Không tìm thấy file thực thi C++: {cpp_executable}. Vui lòng biên dịch trước!")

    # Đọc dữ liệu từ luồng chuẩn (do phase1.py bơm vào)
    input_data = sys.stdin.read()
    
    # Chặn nếu input trống (giống asa_solver)
    if not input_data.strip():
         return [], 0, 0.0

    # Đóng gói tham số truyền qua Command Line cho C++
    args = [
        cpp_executable,
        str(time_limit),
        str(pop_size),
        str(crossover_rate),
        str(mutation_rate)
    ]

    try:
        # Gọi C++, truyền input_data vào luồng stdin của C++, hứng kết quả từ stdout
        result = subprocess.run(args, input=input_data, text=True, capture_output=True, check=True)
        
        # Parse kết quả
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            metrics = lines[0].split()
            total_distance = int(float(metrics[0])) # Chi phí
            t_best = float(metrics[1])              # Thời gian đạt kỷ lục
            
            # Đọc mảng route
            route_str = lines[1].split()
            route = [int(x) for x in route_str]
            
            return route, total_distance, t_best
        else:
             print("Lỗi đọc output từ C++:\n", result.stdout, file=sys.stderr)
             return [], -1, -1.0

    except subprocess.CalledProcessError as e:
        print("Lỗi khi chạy C++ Core:\n", e.stderr, file=sys.stderr)
        return [], -1, -1.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genetic Algorithm Solver")
    parser.add_argument("--time_limit", type=float, default=DEFAULT_TIME_LIMIT)
    parser.add_argument("--pop_size", type=int, default=DEFAULT_POP_SIZE)
    parser.add_argument("--crossover_rate", type=float, default=DEFAULT_CROSSOVER_RATE)
    parser.add_argument("--mutation_rate", type=float, default=DEFAULT_MUTATION_RATE)
    args = parser.parse_args()

    best_route, best_distance, t_best = ga_solver(
        time_limit=args.time_limit,
        pop_size=args.pop_size,
        crossover_rate=args.crossover_rate,
        mutation_rate=args.mutation_rate,
    )

    print(best_route)
    print(best_distance)
    print(t_best)
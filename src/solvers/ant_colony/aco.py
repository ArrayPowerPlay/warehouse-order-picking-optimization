"""
Ant Colony Optimization (ACO) wrapper for Warehouse Order Picking Optimization.

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

# Các tham số mặc định cho ACO
DEFAULT_TIME_LIMIT = 5.0
DEFAULT_NUM_ANTS = 100
DEFAULT_ALPHA = 1.0
DEFAULT_BETA = 3.0
DEFAULT_RHO = 0.1

def aco_solver(
    time_limit: float,
    num_ants: int = DEFAULT_NUM_ANTS,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    rho: float = DEFAULT_RHO,
):
    """Run ACO (C++ core) and return route, total distance, and t_best."""
    
    # Xác định file thực thi C++ (Nằm cùng thư mục với file aco.py này)
    base_dir = os.path.dirname(__file__)
    cpp_executable = os.path.join(base_dir, "aco_core.exe") 
    if not os.path.exists(cpp_executable):
        cpp_executable = os.path.join(base_dir, "aco_core")
        if not os.path.exists(cpp_executable):
            raise FileNotFoundError(f"Không tìm thấy file thực thi C++: {cpp_executable}. Vui lòng biên dịch trước!")

    # Đọc dữ liệu từ luồng chuẩn (do phase1.py bơm vào)
    input_data = sys.stdin.read()
    
    if not input_data.strip():
         return [], 0, 0.0

    # Đóng gói tham số truyền qua Command Line cho C++
    args = [
        cpp_executable,
        str(time_limit),
        str(num_ants),
        str(alpha),
        str(beta),
        str(rho)
    ]

    # Cờ ẩn cửa sổ Command Prompt trên Windows
    creation_flags = 0
    if os.name == 'nt':
        creation_flags = subprocess.CREATE_NO_WINDOW

    try:
        # Gọi C++
        result = subprocess.run(
            args, 
            input=input_data, 
            text=True, 
            capture_output=True, 
            check=True,
            creationflags=creation_flags
        )
        
        # Parse kết quả
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            metrics = lines[0].split()
            total_distance = int(float(metrics[0])) 
            t_best = float(metrics[1])              
            
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
    parser = argparse.ArgumentParser(description="Ant Colony Optimization Solver")
    parser.add_argument("--time_limit", type=float, default=DEFAULT_TIME_LIMIT)
    parser.add_argument("--num_ants", type=int, default=DEFAULT_NUM_ANTS)
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--beta", type=float, default=DEFAULT_BETA)
    parser.add_argument("--rho", type=float, default=DEFAULT_RHO)
    args = parser.parse_args()

    best_route, best_distance, t_best = aco_solver(
        time_limit=args.time_limit,
        num_ants=args.num_ants,
        alpha=args.alpha,
        beta=args.beta,
        rho=args.rho,
    )

    print(best_route)
    print(best_distance)
    print(t_best)
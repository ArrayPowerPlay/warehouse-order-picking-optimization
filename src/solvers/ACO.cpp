#include <bits/stdc++.h>

using namespace std;

//Các tham số
const int NUM_ANTS = 30;         // Số lượng kiến mỗi thế hệ
const int MAX_ITER = 500;        // Số thế hệ tối đa
const double ALPHA = 1.0;        // Trọng số của Pheromone
const double BETA = 3.0;         // Trọng số của Heuristic (Lợi ích/Khoảng cách)
const double RHO = 0.1;          // Tốc độ bay hơi của Pheromone
const double INITIAL_PHERO = 1.0;// Lượng mùi khởi tạo

int N, M;
vector<vector<int>> Q_mat; // Ma trận chứa số lượng sản phẩm
vector<vector<int>> d;     // Ma trận khoảng cách
vector<int> q_req;         // Yêu cầu số lượng từng sản phẩm
vector<vector<double>> phero; // Ma trận mùi

struct Ant {
    vector<int> path;
    long long length;
};

// Cấu trúc lưu kết quả tốt nhất toàn cục
Ant global_best_ant;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    #define Task "B"
    if (fopen(Task".inp", "r")){
        freopen(Task".inp", "r", stdin);
        freopen(Task".out", "w", stdout);
    }

    cin >> N >> M;

    // Khởi tạo kích thước dữ liệu
    Q_mat.assign(N, vector<int>(M + 1, 0));
    for (int i = 0; i < N; ++i) {
        for (int j = 1; j <= M; ++j) {
            cin >> Q_mat[i][j];
        }
    }

    d.assign(M + 1, vector<int>(M + 1, 0));
    for (int i = 0; i <= M; ++i) {
        for (int j = 0; j <= M; ++j) {
            cin >> d[i][j];
        }
    }

    q_req.assign(N, 0);
    for (int i = 0; i < N; ++i) {
        cin >> q_req[i];
    }

    phero.assign(M + 1, vector<double>(M + 1, INITIAL_PHERO));
    global_best_ant.length = 1e18; 

    mt19937 gen(1337); 
    uniform_real_distribution<double> dist_real(0.0, 1.0);

    // --- THÊM VÀO: Mở file CSV để ghi dữ liệu hội tụ ---
    ofstream file_out("aco_convergence.csv");
    file_out << "Iteration,Best_Cost,Average_Cost,Std_Dev\n";

    // --- BẮT ĐẦU VÒNG LẶP ACO ---
    for (int iter = 0; iter < MAX_ITER; ++iter) {
        vector<Ant> ants(NUM_ANTS);
        
        // --- THÊM VÀO: Biến để tính toán thống kê cho thế hệ này ---
        long long current_iteration_best = 1e18; 
        long long total_cost_this_iter = 0;

        for (int k = 0; k < NUM_ANTS; ++k) {
            vector<bool> visited(M + 1, false);
            vector<int> collected(N, 0);
            int current_node = 0;
            ants[k].length = 0;

            visited[0] = true;

            while (true) {
                // Kiểm tra xem kiến đã gom đủ hàng chưa
                bool satisfied = true;
                for (int i = 0; i < N; ++i) {
                    if (collected[i] < q_req[i]) {
                        satisfied = false;
                        break;
                    }
                }
                if (satisfied) break;

                // Tính toán xác suất chuyển trạng thái
                vector<double> probs(M + 1, 0.0);
                double sum_probs = 0.0;

                for (int j = 1; j <= M; ++j) {
                    if (!visited[j]) {
                        double benefit = 0.0;
                        for (int i = 0; i < N; ++i) {
                            int needed = max(0, q_req[i] - collected[i]);
                            benefit += min(needed, Q_mat[i][j]);
                        }

                        if (benefit > 0) {
                            double distance = max(1, d[current_node][j]); 
                            double heuristic = benefit / distance;
                            
                            probs[j] = pow(phero[current_node][j], ALPHA) * pow(heuristic, BETA);
                            sum_probs += probs[j];
                        }
                    }
                }

                if (sum_probs == 0.0) break;

                // Chọn kệ tiếp theo (Roulette Wheel Selection)
                double rand_val = dist_real(gen) * sum_probs;
                double cumulative = 0.0;
                int next_node = -1;

                for (int j = 1; j <= M; ++j) {
                    if (probs[j] > 0) {
                        cumulative += probs[j];
                        if (cumulative >= rand_val) {
                            next_node = j;
                            break;
                        }
                    }
                }
                if (next_node == -1) break;

                // Cập nhật trạng thái
                ants[k].path.push_back(next_node);
                visited[next_node] = true;
                ants[k].length += d[current_node][next_node];
                
                for (int i = 0; i < N; ++i) {
                    collected[i] += Q_mat[i][next_node];
                }
                
                current_node = next_node;
            }

            // Cộng khoảng cách quay về 0
            if (!ants[k].path.empty()) {
                ants[k].length += d[current_node][0];
            }

            // Ghi nhận dữ liệu để tính toán thống kê
            total_cost_this_iter += ants[k].length;
            if (ants[k].length < current_iteration_best && !ants[k].path.empty()) {
                current_iteration_best = ants[k].length;
            }

            // Cập nhật kỷ lục toàn cục
            if (ants[k].length < global_best_ant.length && !ants[k].path.empty()) {
                global_best_ant = ants[k];
            }
        }

        // --- THÊM VÀO: Tính toán Thống kê và Ghi ra file ---
        double avg_cost = (double)total_cost_this_iter / NUM_ANTS;
        
        double variance = 0.0;
        for (int k = 0; k < NUM_ANTS; ++k) {
            variance += (ants[k].length - avg_cost) * (ants[k].length - avg_cost);
        }
        variance /= NUM_ANTS;
        double std_dev = sqrt(variance);

        // Lưu dữ liệu của Iteration hiện tại (Sử dụng global_best_ant để vẽ đường Đỏ liên tục hạ xuống)
        if (iter % 10 == 0 || iter == MAX_ITER - 1) {
            file_out << iter << "," << global_best_ant.length << "," << avg_cost << "," << std_dev << "\n";
        }

        // --- CẬP NHẬT PHEROMONE ---
        for (int i = 0; i <= M; ++i) {
            for (int j = 0; j <= M; ++j) {
                phero[i][j] *= (1.0 - RHO);
                if (phero[i][j] < 0.01) phero[i][j] = 0.01; 
            }
        }

        double Q_deposit = 10000.0; 
        double phero_to_add = Q_deposit / global_best_ant.length;
        
        int curr = 0;
        for (int node : global_best_ant.path) {
            phero[curr][node] += phero_to_add;
            phero[node][curr] += phero_to_add;
            curr = node;
        }
        phero[curr][0] += phero_to_add;
    }

    // --- THÊM VÀO: Đóng file ---
    file_out.close();

    // --- IN KẾT QUẢ ---
    cout << global_best_ant.path.size() << "\n";
    for (int node : global_best_ant.path) {
        cout << node << " ";
    }
    cout << "\n";

    return 0;
}
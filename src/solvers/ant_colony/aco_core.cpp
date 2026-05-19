/*
    Thuật toán Đàn Kiến (ACO) tối ưu hóa lộ trình
*/
#include <bits/stdc++.h>
#include <chrono> // Thêm thư viện đo thời gian

using namespace std;
using namespace std::chrono;

// Các tham số - ĐÃ BỎ CONST ĐỂ NHẬN TỪ PYTHON
int NUM_ANTS = 100;      
// int MAX_ITER = 500; // Không dùng MAX_ITER làm điều kiện dừng chính nữa
double ALPHA = 1.0;      
double BETA = 3.0;       
double RHO = 0.1;        
const double INITIAL_PHERO = 1.0; // Lượng mùi khởi tạo (Giữ nguyên)

// --- THÊM VÀO: Biến lưu giới hạn thời gian ---
double TIME_LIMIT = 900.0; 
// ---------------------------------------------

int N, M;
vector<vector<int>> Q_mat; 
vector<vector<int>> d;     
vector<int> q_req;         
vector<vector<double>> phero; 

struct Ant {
    vector<int> path;
    long long length;
};

Ant global_best_ant;

int main(int argc, char* argv[]) {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    /* --- COMMENT LẠI THEO YÊU CẦU: Nhận tham số kiểu mới từ Python ---
    if (argc >= 6) {
        NUM_ANTS = atoi(argv[1]);
        MAX_ITER = atoi(argv[2]);
        ALPHA = atof(argv[3]);
        BETA = atof(argv[4]);
        RHO = atof(argv[5]);
    }
    ------------------------------------------------------------------*/

    // --- THÊM VÀO: Đọc tham số từ aco.py truyền sang ---
    if (argc >= 6) {
        TIME_LIMIT = atof(argv[1]);
        NUM_ANTS = atoi(argv[2]);
        ALPHA = atof(argv[3]);
        BETA = atof(argv[4]);
        RHO = atof(argv[5]);
    }
    // ---------------------------------------------------

    /* --- COMMENT LẠI THEO YÊU CẦU: Để Python pipe dữ liệu vào cin ---
    #define Task "B"
    if (fopen(Task".inp", "r")){
        freopen(Task".inp", "r", stdin);
        // freopen(Task".out", "w", stdout); 
    }
    -----------------------------------------------------------------*/

    if (!(cin >> N >> M)) return 0; // Check luồng dữ liệu an toàn

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

    mt19937 rng(random_device{}());
    uniform_real_distribution<double> dist_real(0.0, 1.0);

    /* --- COMMENT LẠI THEO YÊU CẦU ---
    ofstream file_out("aco_convergence.csv");
    file_out << "Iteration,Best_Cost,Average_Cost,Std_Dev\n";
    -----------------------------------*/

    auto start_time = high_resolution_clock::now();
    double t_best = 0.0;

    auto initial_time = high_resolution_clock::now();
    t_best = duration<double>(initial_time - start_time).count();

    /* --- COMMENT LẠI: Chuyển sang chạy theo thời gian ---
    for (int iter = 0; iter < MAX_ITER; ++iter) {
    -----------------------------------------------------*/

    // --- THÊM VÀO: Vòng lặp chạy liên tục theo Time Limit ---
    int iter = 0;
    while(true) {
        // Kiểm tra đồng hồ sau mỗi 10 vòng lặp
        if (iter % 10 == 0) {
            auto current_check_time = high_resolution_clock::now();
            double elapsed_check = duration<double>(current_check_time - start_time).count();
            if (elapsed_check >= TIME_LIMIT) {
                break; // Thoát thuật toán khi hết giờ
            }
        }
    // --------------------------------------------------------

        vector<Ant> ants(NUM_ANTS);
        long long current_iteration_best = 1e18; 
        long long total_cost_this_iter = 0;

        for (int k = 0; k < NUM_ANTS; ++k) {
            vector<bool> visited(M + 1, false);
            vector<int> collected(N, 0);
            int current_node = 0;
            ants[k].length = 0;

            visited[0] = true;

            // Cờ bắt lỗi kiến lười (Đã bảo tồn)
            bool is_valid_path = false;

            while (true) {
                bool satisfied = true;
                for (int i = 0; i < N; ++i) {
                    if (collected[i] < q_req[i]) {
                        satisfied = false;
                        break;
                    }
                }
                
                if (satisfied) {
                    is_valid_path = true;
                    break;
                }

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

                double rand_val = dist_real(rng) * sum_probs;
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

                ants[k].path.push_back(next_node);
                visited[next_node] = true;
                ants[k].length += d[current_node][next_node];
                
                for (int i = 0; i < N; ++i) {
                    collected[i] += Q_mat[i][next_node];
                }
                
                current_node = next_node;
            }

            if (!ants[k].path.empty()) {
                ants[k].length += d[current_node][0];
            }

            // --- SỬA Ở ĐÂY: Chỉ cho kiến hợp lệ đua top ---
            if (is_valid_path) {
                total_cost_this_iter += ants[k].length;
                if (ants[k].length < current_iteration_best && !ants[k].path.empty()) {
                    current_iteration_best = ants[k].length;
                }

                if (ants[k].length < global_best_ant.length && !ants[k].path.empty()) {
                    global_best_ant = ants[k];

                    // --- THÊM VÀO: Cập nhật t_best ---
                    auto update_time = high_resolution_clock::now();
                    t_best = duration<double>(update_time - start_time).count();
                    // ---------------------------------
                }
            } else {
                ants[k].length = 1e18; // Kiến lười bị loại
            }
        }

        /* --- COMMENT LẠI THEO YÊU CẦU: Không in file csv/txt mỗi vòng lặp ---
        double avg_cost = (double)total_cost_this_iter / NUM_ANTS;
        double variance = 0.0;
        for (int k = 0; k < NUM_ANTS; ++k) {
            variance += (ants[k].length - avg_cost) * (ants[k].length - avg_cost);
        }
        variance /= NUM_ANTS;
        double std_dev = sqrt(variance);

        if (iter % 10 == 0 || iter == MAX_ITER - 1) {
            file_out << iter << "," << global_best_ant.length << "," << avg_cost << "," << std_dev << "\n";
        }
        ---------------------------------------------------------------------*/

        // Cập nhật Pheromone
        for (int i = 0; i <= M; ++i) {
            for (int j = 0; j <= M; ++j) {
                phero[i][j] *= (1.0 - RHO);
                if (phero[i][j] < 0.01) phero[i][j] = 0.01; 
            }
        }

        if (global_best_ant.length < 1e18) { // Bảo vệ lỗi chia cho vô cực
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

        iter++;
    }

    /* --- COMMENT LẠI THEO YÊU CẦU ---
    file_out.close();
    auto end_total = high_resolution_clock::now();
    auto duration_total = duration_cast<milliseconds>(end_total - start_total).count();
    cout << global_best_ant.length << " " << duration_total << "\n";
    -----------------------------------*/

    // --- THÊM VÀO: IN RA CHUẨN ĐỂ aco.py ĐỌC DỄ DÀNG ---
    // Dòng 1: Cost và t_best
    cout << global_best_ant.length << " " << fixed << setprecision(4) << t_best << "\n";
    
    // Dòng 2: Lộ trình (Route) - Tự động thêm điểm 0 ở đầu và cuối
    cout << "0 ";
    for (size_t i = 0; i < global_best_ant.path.size(); ++i) {
        cout << global_best_ant.path[i] << " ";
    }
    cout << "0\n";
    // ------------------------------------------

    return 0;
}
/*
    Sử dụng thuật toán GA kết hợp 2-opt
    - Mỗi cá thể là một vector độ ưu tiên cho các kệ hàng
    - Chọn các kệ hàng cần đi tới qua độ ưu tiên
    - Xây dựng lộ trình bằng Nearest Neighbor
    - Cải thiện lộ trình bằng 2-opt
*/
#include <bits/stdc++.h>

// --- THÊM VÀO: Thư viện tính thời gian ---
#include <chrono>
// ----------------------------------------

using namespace std;

// Tham số của thuật toán GA
int POP_SIZE = 10; // Kích thước quần thể
int MAX_GEN = 20; // Số thế hệ tối đa
double CROSSOVER_RATE = 0.8; // Tỷ lệ lai ghép
double MUTATION_RATE = 0.1; // Tỷ lệ đột biến

// --- THÊM VÀO: Biến lưu giới hạn thời gian ---
double TIME_LIMIT = 900.0; 
// ---------------------------------------------

int N; // Số loại sản phẩm
int M; // Số kệ hàng
vector<vector<int>> Q; // Q[i][j]: Số lượng sản phẩm i có ở kệ j
vector<vector<int>> d; // Ma trận khoảng cách
vector<int> q; // Số lượng sản phẩm cần lấy

// Bộ sinh số ngẫu nhiên
unsigned int RNG_SEED = static_cast<unsigned int>(random_device{}());
mt19937 rng;
uniform_real_distribution<double> dist_real(0.0, 1.0);

struct Individual
{
    vector<double> gen; // Độ ưu tiên
    vector<int> path;
    long long cost;

    Individual()
    {
        gen.resize(M + 1); // Bỏ qua kệ 0
        cost = 1e18;
    }
};

void apply_2opt(vector<int>& path)
{
    bool flag = true;
    while (flag)
    {
        flag = false;
        for (int i = 0; i < path.size() - 1; i++)
        {
            for (int j = i + 2; j < path.size(); j++)
            {
                int node_a = (i == 0) ? 0 : path[i - 1];
                int node_b = path[i];
                int node_c = path[j - 1];
                int node_d = (j == path.size()) ? 0 : path[j];

                long long cur_dist = d[node_a][node_b] + d[node_c][node_d];
                long long new_dist = d[node_a][node_c] + d[node_b][node_d];

                if (new_dist < cur_dist)
                {
                    reverse(path.begin() + i, path.begin() + j);
                    flag = true;
                }
            }
        }
    }
}

void evaluate(Individual& ind)
{
    vector<pair<double, int>> ranked_shelves;
    for (int j = 1; j <= M; ++j) {
        ranked_shelves.push_back({ind.gen[j], j});
    }
    sort(ranked_shelves.rbegin(), ranked_shelves.rend());

    vector<int> selected_shelves;
    vector<int> collected(N, 0);
    bool flag = false;

    for (auto& item : ranked_shelves)
    {
        int shelf = item.second;
        selected_shelves.push_back(shelf);
        
        flag = true;
        for (int i = 0; i < N; ++i)
        {
            collected[i] += Q[i][shelf];
            if (collected[i] < q[i]) {
                flag = false;
            }
        }
        if (flag) break;
    }

    ind.path.clear();
    vector<bool> visited(M + 1, false);
    int curr = 0;
    
    while (ind.path.size() < selected_shelves.size())
    {
        int best_next = -1;
        long long min_dist = 1e18;
        
        for (int s : selected_shelves)
        {
            if (!visited[s] && d[curr][s] < min_dist)
            {
                min_dist = d[curr][s];
                best_next = s;
            }
        }
        visited[best_next] = true;
        ind.path.push_back(best_next);
        curr = best_next;
    }

    apply_2opt(ind.path);

    ind.cost = 0;
    curr = 0;
    for (int s : ind.path) {
        ind.cost += d[curr][s];
        curr = s;
    }
    ind.cost += d[curr][0];
}

Individual create_random_individual()
{
    Individual ind;
    for (int j = 1; j <= M; ++j) {
        ind.gen[j] = dist_real(rng);
    }
    evaluate(ind);
    return ind;
}

Individual crossover(const Individual& p1, const Individual& p2)
{
    Individual child;
    for (int j = 1; j <= M; ++j)
    {
        if (dist_real(rng) < 0.5)
        {
            child.gen[j] = p1.gen[j];
        } else
        {
            child.gen[j] = p2.gen[j];
        }
    }
    return child;
}

void mutate(Individual& ind)
{
    for (int j = 1; j <= M; ++j)
    {
        if (dist_real(rng) < MUTATION_RATE)
        {
            ind.gen[j] = dist_real(rng);
        }
    }
}

int main(int argc, char* argv[])
{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    /* --- COMMENT LẠI THEO YÊU CẦU: Để Python có thể pipe dữ liệu vào cin ---
    #define Task "A"
    if (fopen(Task".inp", "r")){
        freopen(Task".inp", "r", stdin);
        //freopen(Task".out", "w", stdout);
    }
    --------------------------------------------------------------------------*/

    // --- THÊM VÀO: Đọc tham số từ ga.py truyền sang ---
    if (argc >= 5) {
        TIME_LIMIT = atof(argv[1]);
        POP_SIZE = atoi(argv[2]);
        CROSSOVER_RATE = atof(argv[3]);
        MUTATION_RATE = atof(argv[4]);
    }
    if (argc >= 6) {
        RNG_SEED = static_cast<unsigned int>(strtoul(argv[5], nullptr, 10));
    }
    rng.seed(RNG_SEED);
    // --------------------------------------------------

    if (!(cin >> N >> M)) return 0; // Check luồng dữ liệu an toàn

    Q.assign(N, vector<int>(M + 1, 0));
    for (int i = 0; i < N; ++i)
    {
        for (int j = 1; j <= M; ++j)
        {
            cin >> Q[i][j];
        }
    }

    d.assign(M + 1, vector<int>(M + 1, 0));
    for (int i = 0; i <= M; ++i)
    {
        for (int j = 0; j <= M; ++j)
        {
            cin >> d[i][j];
        }
    }

    q.assign(N, 0);
    for (int i = 0; i < N; ++i)
    {
        cin >> q[i];
    }

    /* --- COMMENT LẠI THEO YÊU CẦU: Không in file txt và csv ---
    ofstream route_file("routes_history.txt");
    route_file << "Generation|Cost|Path\n";
    ofstream file_out("convergence.csv");
    ------------------------------------------------------------*/

    auto start_time = chrono::high_resolution_clock::now();
    double t_best = 0.0;

    // start GA
    vector<Individual> pop(POP_SIZE);

    for (int i = 0; i < POP_SIZE; ++i)
    {
        pop[i] = create_random_individual();
    }

    Individual best_overall = pop[0];
    
    // --- THÊM VÀO: Chốt thời gian khởi tạo ban đầu ---
    auto initial_time = chrono::high_resolution_clock::now();
    t_best = chrono::duration<double>(initial_time - start_time).count();
    // -------------------------------------------------

    /* --- COMMENT LẠI: Chuyển sang chạy theo thời gian ---
    for (int gen_idx = 0; gen_idx < MAX_GEN; ++gen_idx)
    {
    -----------------------------------------------------*/

    // --- THÊM VÀO: Vòng lặp chạy liên tục theo Time Limit ---
    int gen_idx = 0;
    while(true)
    {
        // Kiểm tra đồng hồ sau mỗi 10 thế hệ để tránh overhead việc gọi hàm time
        if (gen_idx % 10 == 0) {
            auto current_check_time = chrono::high_resolution_clock::now();
            double elapsed_check = chrono::duration<double>(current_check_time - start_time).count();
            if (elapsed_check >= TIME_LIMIT) {
                break; // Thoát thuật toán khi hết giờ
            }
        }
    // --------------------------------------------------------

        sort(pop.begin(), pop.end(), [](const Individual& a, const Individual& b)
        {
            return a.cost < b.cost;
        });

        if (pop[0].cost < best_overall.cost)
        {
            best_overall = pop[0];

            // --- THÊM VÀO: Cập nhật t_best ---
            auto update_time = chrono::high_resolution_clock::now();
            t_best = chrono::duration<double>(update_time - start_time).count();
            // ---------------------------------
        }

        /* --- COMMENT LẠI THEO YÊU CẦU: Tắt việc ghi file csv/txt mỗi vòng lặp ---
        long long total_cost = 0;
        for (int i = 0; i < POP_SIZE; ++i) {
            total_cost += pop[i].cost;
        }
        double avg_cost = (double)total_cost / POP_SIZE;

        double variance = 0.0;
        for (int i = 0; i < POP_SIZE; ++i) {
            variance += (pop[i].cost - avg_cost) * (pop[i].cost - avg_cost);
        }
        variance /= POP_SIZE;
        double std_dev = sqrt(variance);

        file_out << gen_idx << "," << best_overall.cost << "," << avg_cost << "," << std_dev << "\n";

        if (gen_idx % 1 == 0 || gen_idx == MAX_GEN - 1)
        {
            route_file << gen_idx << "|" << best_overall.cost << "|";
            route_file << "0"; 
            for (int s : best_overall.path) {
                route_file << "->" << s;
            }
            route_file << "->0\n"; 
        }
        -------------------------------------------------------------------------*/

        vector<Individual> new_pop;

        int elite_count = POP_SIZE * 0.1;
        for (int i = 0; i < elite_count; ++i)
        {
            new_pop.push_back(pop[i]);
        }

        uniform_int_distribution<int> dist_tour(0, POP_SIZE / 2); 
        
        while (new_pop.size() < POP_SIZE)
        {
            Individual parent1 = pop[dist_tour(rng)];
            Individual parent2 = pop[dist_tour(rng)];
            Individual child;

            if (dist_real(rng) < CROSSOVER_RATE)
            {
                child = crossover(parent1, parent2);
            }
            else
            {
                child = parent1; 
            }

            mutate(child);
            evaluate(child);
            new_pop.push_back(child);
        }
        pop = new_pop;
        gen_idx++;
    }

    /* --- COMMENT LẠI THEO YÊU CẦU ---
    route_file.close();
    file_out.close();

    auto end_time = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::milliseconds>(end_time - start_time);
    cout << best_overall.cost << " " << duration.count() << "\n";
    -----------------------------------*/

    // --- THÊM VÀO: IN RA CHUẨN ĐỂ ga.py ĐỌC DỄ DÀNG ---
    // Dòng 1: Cost và t_best
    cout << best_overall.cost << " " << fixed << setprecision(4) << t_best << "\n";
    
    // Dòng 2: Lộ trình (Route) - Tự động thêm điểm 0 ở đầu và cuối
    cout << "0 ";
    for (size_t i = 0; i < best_overall.path.size(); ++i) {
        cout << best_overall.path[i] << " ";
    }
    cout << "0\n";
    // ------------------------------------------

    return 0;
}

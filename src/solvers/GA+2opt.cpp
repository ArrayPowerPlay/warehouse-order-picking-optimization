/*
    Sử dụng thuật toán GA kết hợp 2-opt
    - Mỗi cá thể là một vector độ ưu tiên cho các kệ hàng
    - Chọn các kệ hàng cần đi tới qua độ ưu tiên
    - Xây dựng lộ trình bằng Nearest Neighbor
    - Cải thiện lộ trình bằng 2-opt
*/
#include <bits/stdc++.h>

using namespace std;

// Tham số của thuật toán GA
const int POP_SIZE = 100; // Kích thước quần thể
const int MAX_GEN = 200; // Số thế hệ tối đa
const double CROSSOVER_RATE = 0.8; // Tỷ lệ lai ghép
const double MUTATION_RATE = 0.1; // Tỷ lệ đột biến

int N; // Số loại sản phẩm
int M; // Số kệ hàng
vector<vector<int>> Q; // Q[i][j]: Số lượng sản phẩm i có ở kệ j
vector<vector<int>> d; // Ma trận khoảng cách
vector<int> q; // Số lượng sản phẩm cần lấy

// Bộ sinh số ngẫu nhiên
mt19937 rng(12345);
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

// Tối ưu cục bộ 2-opt để rút ngắn đường đi
// Gỡ các đoạn bị chéo nhau trên đồ thị - Đảo đoạn
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

// Hàm giải mã và đánh giá cá thể
void evaluate(Individual& ind)
{
    // Sắp xếp các kệ theo độ ưu tiên giảm dần
    vector<pair<double, int>> ranked_shelves;
    for (int j = 1; j <= M; ++j) {
        ranked_shelves.push_back({ind.gen[j], j});
    }
    sort(ranked_shelves.rbegin(), ranked_shelves.rend());

    // Chọn kệ cho đến khi đủ hàng
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

    // Xây dựng lộ trình bằng Nearest Neighbor
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

    // 2-opt
    apply_2opt(ind.path);

    // Tính tổng quãng đường
    ind.cost = 0;
    curr = 0;
    for (int s : ind.path) {
        ind.cost += d[curr][s];
        curr = s;
    }
    ind.cost += d[curr][0];
}

// Khởi tạo ngẫu nhiên một cá thể
Individual create_random_individual()
{
    Individual ind;
    for (int j = 1; j <= M; ++j) {
        ind.gen[j] = dist_real(rng);
    }
    evaluate(ind);
    return ind;
}

// Lai ghép đồng nhất (Uniform Crossover)
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

// Đột biến (Mutation)
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

int main()
{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    #define Task "A"
    if (fopen(Task".inp", "r")){
        freopen(Task".inp", "r", stdin);
        freopen(Task".out", "w", stdout);
    }

    cin >> N >> M;

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

    // start GA
    vector<Individual> pop(POP_SIZE);

    for (int i = 0; i < POP_SIZE; ++i)
    {
        pop[i] = create_random_individual();
    }

    Individual best_overall = pop[0];

    for (int gen_idx = 0; gen_idx < MAX_GEN; ++gen_idx)
    {
        // Sắp xếp quần thể để tìm cá thể tốt nhất
        sort(pop.begin(), pop.end(), [](const Individual& a, const Individual& b)
        {
            return a.cost < b.cost;
        });

        if (pop[0].cost < best_overall.cost)
        {
            best_overall = pop[0];
        }

        vector<Individual> new_pop;

        // Giữ lại 10% cá thể tinh hoa (Elitism)
        int elite_count = POP_SIZE * 0.1;
        for (int i = 0; i < elite_count; ++i)
        {
            new_pop.push_back(pop[i]);
        }

        // Lai ghép và đột biến để tạo phần còn lại
        uniform_int_distribution<int> dist_tour(0, POP_SIZE / 2); // Chọn lọc giải đấu thiên vị cá thể tốt
        
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
                child = parent1; // Không lai thì giữ nguyên
            }

            mutate(child);
            evaluate(child);
            new_pop.push_back(child);
        }
        pop = new_pop;
    }


    cout << best_overall.path.size() << endl;
    for (int s : best_overall.path) {
        cout << s << " ";
    }

    return 0;
}
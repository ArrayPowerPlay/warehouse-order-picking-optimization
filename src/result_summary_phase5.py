import os
import sys
import pandas as pd
import numpy as np

# Thiet lap duong dan
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

PHASE4_DIR = os.path.join(project_root, "results", "phase4")
PHASE5_DIR = os.path.join(project_root, "results", "phase5")

def main():
    print("BAT DAU CHAY PHASE 5.2: TONG HOP SUMMARY KET QUA")
    
    agg_path = os.path.join(PHASE5_DIR, "aggregate_result.csv")
    ref_path = os.path.join(PHASE4_DIR, "cost_reference.csv")
    
    if not os.path.exists(agg_path) or not os.path.exists(ref_path):
        print("Loi: Thieu file aggregate_result.csv hoac cost_reference.csv")
        return

    df_agg = pd.read_csv(agg_path)
    df_ref = pd.read_csv(ref_path)
    
    # Ghep cot 'group' (small, medium, large) vao bang aggregate
    df = pd.merge(df_agg, df_ref[['testcase', 'group']], on='testcase', how='left')
    
    # Tu dong nhan dien danh sach cac thuat toan hien co (dua vao tien to cua cot _RPD)
    algos = list(set([col.split('_')[0] for col in df.columns if col.endswith('_RPD')]))
    algos.sort()
    
    results = []
    groups = ['small', 'medium', 'large']
    
    # 1. Tinh trung binh cho tung nhom (Small, Medium, Large)
    for g in groups:
        group_df = df[df['group'] == g]
        row_data = {'group': g}
        for algo in algos:
            rpd_col = f"{algo}_RPD"
            t_col = f"{algo}_t_best_avg"
            
            # Dung mean() de bo qua cac o rong (NaN) tu dong
            row_data[rpd_col] = group_df[rpd_col].mean() if rpd_col in group_df else np.nan
            row_data[t_col] = group_df[t_col].mean() if t_col in group_df else np.nan
        results.append(row_data)
        
    # 2. Tinh trung binh Overall
    overall_data = {'group': 'overall'}
    for algo in algos:
        rpd_col = f"{algo}_RPD"
        t_col = f"{algo}_t_best_avg"
        
        # Kiem tra xem thuat toan nay co chay du 3 nhom (small, medium, large) khong
        # Neu thieu bat ky nhom nao (nhu CP-SAT), danh ranh (NaN) cho overall
        has_all_groups = True
        for g in groups:
            if df[df['group'] == g][rpd_col].isna().all():
                has_all_groups = False
                break
                
        if has_all_groups:
            overall_data[rpd_col] = df[rpd_col].mean()
            overall_data[t_col] = df[t_col].mean()
        else:
            overall_data[rpd_col] = np.nan
            overall_data[t_col] = np.nan
            
    results.append(overall_data)
    
    df_summary = pd.DataFrame(results)
    
    # 3. Thuat toan tim Winner cho tung dong
    def get_winner(row):
        best_rpd = float('inf')
        best_algos = []
        
        # Tim RPD nho nhat
        for algo in algos:
            rpd_val = row.get(f"{algo}_RPD", np.nan)
            if pd.notna(rpd_val):
                if rpd_val < best_rpd:
                    best_rpd = rpd_val
                    best_algos = [algo]
                elif rpd_val == best_rpd:
                    best_algos.append(algo)
                    
        if not best_algos:
            return ""
        if len(best_algos) == 1:
            return best_algos[0]
            
        # Tie-breaker: Neu RPD bang nhau , xet xem chay nhanh hon
        best_t = float('inf')
        winner = best_algos[0]
        for algo in best_algos:
            t_val = row.get(f"{algo}_t_best_avg", np.nan)
            if pd.notna(t_val) and t_val < best_t:
                best_t = t_val
                winner = algo
        return winner

    df_summary['winner'] = df_summary.apply(get_winner, axis=1)
    
    # 4. Sap xep lai cot 
    cols = ['group']
    for algo in algos:
        cols.extend([f"{algo}_RPD", f"{algo}_t_best_avg"])
    cols.append('winner')
    
    df_summary = df_summary[cols]
    
    # Lam tron 2 chu so thap phan 
    df_summary = df_summary.round(2)
    
    # 5. Xuat ket qua
    output_path = os.path.join(PHASE5_DIR, "summary.csv")
    df_summary.to_csv(output_path, index=False, encoding="utf-8", na_rep="")

    print(f"HOAN THANH!")

if __name__ == "__main__":
    main()

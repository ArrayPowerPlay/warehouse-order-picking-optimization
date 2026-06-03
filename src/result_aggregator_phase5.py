import os
import sys
import pandas as pd
import numpy as np

# Thiet lap duong dan tuong doi den thu muc goc cua du an
# Da giu nguyen ban sua loi tu ../.. thanh .. de phu hop khi dat file tai src/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

PHASE4_DIR = os.path.join(project_root, "results", "phase4")
PHASE5_DIR = os.path.join(project_root, "results", "phase5")

def main():
    print("BAT DAU CHAY PHASE 5: TONG HOP KET QUA VA TINH RPD")
    
    # 1. Doc file cost_reference (Anchor)
    ref_path = os.path.join(PHASE4_DIR, "cost_reference.csv")
    if not os.path.exists(ref_path):
        print(f"Loi: Khong tim thay file {ref_path}")
        return

    df_ref = pd.read_csv(ref_path)
    
    # LOC DU LIEU: Bo qua cac testcase vo nghiem (-1) o moc reference 
    initial_count = len(df_ref)
    df_ref = df_ref[df_ref['cost_reference'] != -1].reset_index(drop=True)
    filtered_count = len(df_ref)
    print(f"Da loc bo {initial_count - filtered_count} testcase vo nghiem. Giu lai {filtered_count} testcase hop le.")

    # Khoi tao bang tong hop
    df_agg = df_ref[['testcase', 'cost_reference']].copy()

    # 2. Quet cac file thuat toan trong thu muc Phase 4
    # Loai bo file reference va cac file mang duoi _detail.csv
    algo_files = [f for f in os.listdir(PHASE4_DIR) 
                  if f.endswith('.csv') and f != 'cost_reference.csv' and not f.endswith('_detail.csv')]
    
    print(f"Tim thay {len(algo_files)} file thuat toan can gop: {algo_files}")

    for file in sorted(algo_files):
        algo_name = file.replace('.csv', '').upper()
        filepath = os.path.join(PHASE4_DIR, file)
        
        try:
            df_algo = pd.read_csv(filepath)
        except Exception as e:
            print(f"Loi doc file {file}: {e}")
            continue
            
        cols_to_keep = ['testcase', 'cost_min', 'cost_max', 'cost_avg', 't_best_avg']
        available_cols = [c for c in cols_to_keep if c in df_algo.columns]
        
        df_algo_filtered = df_algo[available_cols].copy()
        
        # Bien cac gia tri -1 phat sinh tai tung thuat toan thanh o trong (NaN)
        df_algo_filtered.replace(-1, np.nan, inplace=True)
        
        # Doi ten cot de chen tien to ten thuat toan
        rename_dict = {col: f"{algo_name}_{col}" for col in available_cols if col != 'testcase'}
        df_algo_filtered.rename(columns=rename_dict, inplace=True)
        
        # Merge vao bang tong hop theo kieu left join (O nao thieu cua CP-SAT se tu dong de trong)
        df_agg = pd.merge(df_agg, df_algo_filtered, on='testcase', how='left')
        
        # 3. Tinh toan chi so RPD 
        avg_col = f"{algo_name}_cost_avg"
        rpd_col = f"{algo_name}_RPD"
        
        if avg_col in df_agg.columns:
            df_agg[rpd_col] = ((df_agg[avg_col] - df_agg['cost_reference']) / df_agg['cost_reference']) * 100
            df_agg[rpd_col] = df_agg[rpd_col].round(2)

    # 4. Sap xep cot de dua cost_reference xuong phia cuoi bang 
    cols = [c for c in df_agg.columns if c != 'cost_reference'] + ['cost_reference']
    df_agg = df_agg[cols]

    # 5. Xuat ket qua ra thu muc phase5
    os.makedirs(PHASE5_DIR, exist_ok=True)
    output_path = os.path.join(PHASE5_DIR, "aggregate_result.csv")
    
    # Ghi file, tham so dam bao cac o rong se duoc de trong hoan toan tren file Excel/CSV
    df_agg.to_csv(output_path, index=False, encoding="utf-8", na_rep="")
    
    print(f"HOAN THANH!")

if __name__ == "__main__":
    main()
import os
import csv
import re
from datetime import datetime
import shutil

def update_csv():
    target_dir = r"C:\Users\kenny\OneDrive\anoano\Ryo_Syu_Syo\202501"
    csv_path = os.path.join(target_dir, "results_RyoSyuSyo.csv")
    
    print("=== CSVファイル更新処理開始 ===")
    
    # バックアップ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{csv_path}_{timestamp}.bak"
    shutil.copy2(csv_path, backup_path)
    print(f"バックアップ作成: {os.path.basename(backup_path)}")
    
    # 現在のファイル一覧を取得
    files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))
             and f.lower().endswith(('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'))]
    
    print(f"\n処理対象ファイル:")
    for f in files:
        print(f"- {f}")
    
    # ファイル名から情報を抽出
    file_info = []
    pattern = r"(\d{4})_(\d{2})_(\d{2})_(.+?)\.[^.]+$"
    
    for file in files:
        match = re.match(pattern, file)
        if match:
            year, month, day, store = match.groups()
            # 2025年のデータのみ処理
            if year == "2025":
                date = f"{year}/{month}/{day}"
                store = store.replace('_', ' ')
                file_info.append([file, date, store, "", ""])  # 商品名と金額は空欄
    
    # CSVファイルを更新
    with open(csv_path, 'w', encoding='shift_jis', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sorted(file_info))  # 日付順にソート
    
    print(f"\n処理完了:")
    print(f"更新されたファイル数: {len(file_info)}")
    print(f"CSVファイルを更新しました: {csv_path}")

if __name__ == "__main__":
    update_csv() 
import os
import csv
import shutil
from datetime import datetime
import re
from typing import Tuple, List, Dict

class FileRenamer:
    def __init__(self, csv_path: str, target_dir: str):
        self.csv_path = csv_path
        self.target_dir = target_dir
        self.renamed_files: Dict[str, str] = {}
        self.errors: List[str] = []
        self.different_year_files: List[tuple[str, str]] = []  # 年が異なるファイルを記録

    def validate_csv_exists(self) -> bool:
        """CSVファイルの存在チェック"""
        return os.path.exists(self.csv_path)

    def check_csv_content(self) -> Tuple[bool, str]:
        """
        CSVファイルの内容をチェック
        Returns:
            Tuple[bool, str]: (エラーあり, エラーメッセージ)
        """
        try:
            encodings = ['shift_jis', 'utf-8']
            for encoding in encodings:
                try:
                    with open(self.csv_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        if "申し訳ありません" in content:
                            return True, "CSVファイルにエラーメッセージが含まれています。\n先にCSVファイルの内容を修正してください。\n\n修正方法：\n1. CSVファイルを開いて、「申し訳ありません」を含む行を削除\n2. または、update_csv.pyを実行してCSVファイルを更新"
                except UnicodeDecodeError:
                    continue
            return False, ""
        except Exception as e:
            return True, f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}"

    def read_csv_with_encoding(self) -> List[List[str]]:
        """
        CSVファイルを適切なエンコーディングで読み込む
        Shift-JISを優先し、失敗した場合はUTF-8を試みる
        """
        encodings = ['shift_jis', 'utf-8']
        for encoding in encodings:
            try:
                with open(self.csv_path, 'r', encoding=encoding) as f:
                    reader = csv.reader(f)
                    # 全行を読み込んでフィルタリング
                    rows = []
                    for row in reader:
                        # 空行をスキップ
                        if not row or not any(row):
                            continue
                        # エラーメッセージを含む行をスキップ
                        if any("申し訳ありません" in col for col in row):
                            continue
                        # 各列の前後の空白を削除
                        row = [col.strip() if col else "" for col in row]
                        if len(row) >= 3:  # 必要な列が存在する場合のみ追加
                            rows.append(row)
                    return rows
            except UnicodeDecodeError:
                continue
        raise ValueError("CSVファイルのエンコーディングが対応していません")

    def sanitize_filename(self, filename: str) -> str:
        """ファイル名から不正な文字を除去"""
        # Windowsで使用できない文字を置換
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '_', filename)
        # 空白文字をアンダースコアに変換
        filename = filename.replace(' ', '_')
        return filename

    def validate_date(self, date: str) -> bool:
        """日付の妥当性をチェック"""
        try:
            # YYYY/MM/DD形式かチェック
            if not re.match(r'^\d{4}/\d{2}/\d{2}$', date):
                return False
                
            # 日付として有効かチェック
            year, month, day = map(int, date.split('/'))
            datetime(year, month, day)
            
            # 現在の年と異なる場合は記録（エラーにはしない）
            current_year = datetime.now().year
            if year != current_year:
                self.different_year_files.append((self.current_file, date))
            
            return True
        except ValueError:
            return False

    def generate_new_filename(self, old_filename: str, date: str, store: str) -> str:
        """新しいファイル名を生成"""
        # 拡張子の取得
        name, ext = os.path.splitext(old_filename)
        # 日付のフォーマット変換（2025/01/12 → 2025_01_12）
        date = date.replace('/', '_')
        # 店舗名のサニタイズ
        store = self.sanitize_filename(store)
        # 新しいファイル名の生成
        new_filename = f"{date}_{store}{ext}"
        
        # 重複チェックと連番付与
        counter = 1
        base_filename = new_filename
        while os.path.exists(os.path.join(self.target_dir, new_filename)):
            name, ext = os.path.splitext(base_filename)
            new_filename = f"{name}({counter}){ext}"
            counter += 1
            
        return new_filename

    def update_csv_with_renamed_files(self) -> None:
        """CSVファイルに新しいファイル名の列を追加"""
        data = self.read_csv_with_encoding()
        
        # 新しい列名を決定
        new_column = "renamed_filename"
        counter = 1
        while f"{new_column}_{counter}" in data[0]:
            counter += 1
        if counter > 1:
            new_column = f"{new_column}_{counter}"
            
        # 新しい列を追加
        for row in data:
            if row[0] in self.renamed_files:
                row.append(self.renamed_files[row[0]])
            else:
                row.append("")
                
        # CSVファイルを更新
        with open(self.csv_path, 'w', encoding='shift_jis', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)

    def rename_files(self) -> Tuple[int, int, List[str]]:
        """
        ファイルのリネーム処理を実行
        Returns:
            Tuple[成功件数, 失敗件数, エラーメッセージリスト]
        """
        if not self.validate_csv_exists():
            return 0, 0, ["CSVファイルが見つかりません"]

        # CSVファイルの内容チェック
        has_error, error_message = self.check_csv_content()
        if has_error:
            return 0, 1, [error_message]

        success_count = 0
        error_count = 0
        
        try:
            data = self.read_csv_with_encoding()
            
            for row in data:
                try:
                    if len(row) < 3:
                        self.errors.append(f"データ不足: {','.join(row)}")
                        error_count += 1
                        continue
                        
                    old_filename, date, store = row[0:3]
                    self.current_file = old_filename  # 現在処理中のファイル名を保存
                    
                    # 日付の妥当性チェック
                    if not self.validate_date(date):
                        self.errors.append(f"無効な日付: {old_filename} - {date}")
                        error_count += 1
                        continue
                    
                    # ファイルの存在確認
                    old_path = os.path.join(self.target_dir, old_filename)
                    if not os.path.exists(old_path):
                        self.errors.append(f"ファイルが見つかりません: {old_filename}")
                        error_count += 1
                        continue
                    
                    # ファイル名変更
                    new_filename = self.generate_new_filename(old_filename, date, store)
                    new_path = os.path.join(self.target_dir, new_filename)
                    os.rename(old_path, new_path)
                    self.renamed_files[old_filename] = new_filename
                    success_count += 1
                    
                except Exception as e:
                    self.errors.append(f"リネーム失敗 {old_filename if 'old_filename' in locals() else '不明'}: {str(e)}")
                    error_count += 1

            # CSVファイルの更新
            if success_count > 0:
                self.update_csv_with_renamed_files()
            
            # 年の違いがあるファイルの報告を追加
            if self.different_year_files:
                self.errors.append("\n※以下のファイルは現在の年と異なる年が設定されています（処理は続行されました）:")
                for file, date in self.different_year_files:
                    self.errors.append(f"- {file}: {date}")
            
            return success_count, error_count, self.errors
            
        except Exception as e:
            return 0, 1, [f"予期せぬエラーが発生しました: {str(e)}"] 
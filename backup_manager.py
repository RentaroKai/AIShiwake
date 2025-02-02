import os
import shutil
import zipfile
from datetime import datetime
from typing import Optional

class BackupManager:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_zip_backup(self) -> Optional[str]:
        """
        対象フォルダのZIPバックアップを作成
        Returns:
            str: バックアップファイルのパス、失敗時はNone
        """
        try:
            # バックアップファイル名の生成
            folder_name = os.path.basename(self.target_dir)
            backup_filename = f"{folder_name}_backup_{self.backup_timestamp}.zip"
            backup_path = os.path.join(os.path.dirname(self.target_dir), backup_filename)

            # ZIPファイルの作成
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.target_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.target_dir)
                        zipf.write(file_path, arcname)

            return backup_path

        except Exception as e:
            print(f"バックアップ作成エラー: {str(e)}")
            return None

    def backup_csv_file(self, csv_path: str) -> Optional[str]:
        """
        CSVファイルのバックアップを作成
        Returns:
            str: バックアップファイルのパス、失敗時はNone
        """
        try:
            # バックアップファイル名の生成
            filename, ext = os.path.splitext(csv_path)
            backup_filename = f"{filename}_{self.backup_timestamp}.bak"

            # ファイルのコピー
            shutil.copy2(csv_path, backup_filename)
            return backup_filename

        except Exception as e:
            print(f"CSVバックアップ作成エラー: {str(e)}")
            return None

    def restore_from_backup(self, backup_path: str) -> bool:
        """
        バックアップから復元（ZIPの場合）
        Returns:
            bool: 復元成功時True
        """
        try:
            if not os.path.exists(backup_path):
                return False

            if backup_path.endswith('.zip'):
                # ZIPファイルからの復元
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(self.target_dir)
            else:
                # 単一ファイルの復元
                filename = os.path.splitext(backup_path)[0]
                shutil.copy2(backup_path, filename)

            return True

        except Exception as e:
            print(f"復元エラー: {str(e)}")
            return False 
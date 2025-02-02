import os
from tkinter import Tk, Label, Button, Entry, StringVar, Frame, BooleanVar, IntVar, ttk
from settings_manager import load_settings, save_settings
from file_handler import select_folder, open_processed_folder
from image_processor import process_images
from ui_components import open_advanced_settings, open_rename_dialog

def main():
    global api_key_var, max_size_var, resize_enabled_var
    settings = load_settings()
    
    root = Tk()
    root.title("AI_レシート一括処理")

    # Add a button to open advanced settings, positioned at the top right
    settings_frame = Frame(root)
    settings_frame.pack(anchor="ne", padx=20, pady=10)
    
    # テンプレート名を表示するラベル
    template_label = Label(settings_frame, text=f"テンプレート：{settings['prompt_templates'][settings['current_template']]['name']}")
    template_label.pack(side="left", padx=(0, 10))
    
    # 詳細設定ボタン
    Button(settings_frame, text="詳細設定", command=lambda: open_advanced_settings(root, template_label, api_key_var, max_size_var, resize_enabled_var)).pack(side="left")

    # Folder path UI
    folder_frame = Frame(root)
    folder_frame.pack(side="top", fill="x", padx=20, pady=10)
    Label(folder_frame, text="folder:").pack(side="left")
    folder_entry = Entry(folder_frame, width=40)
    folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    Button(folder_frame, text="選択", command=lambda: select_folder(folder_entry, settings.get("default_folder_path", os.path.expanduser("~\\Documents")))).pack(side="left")

    # プログレスバーのUIを追加
    progress_var = IntVar()
    progress_bar = ttk.Progressbar(root, maximum=100, variable=progress_var, mode='determinate')
    progress_bar.pack(side="top", fill="x", padx=20, pady=(10, 5))

    # ボタンを配置するフレーム
    button_frame = Frame(root)
    button_frame.pack(side="top", fill="x", padx=20, pady=(0, 10))

    # Start processing button
    process_button = Button(button_frame, text="レシート一括処理開始", command=lambda: process_images(api_key_var.get(), max_size_var.get(), resize_enabled_var.get(), folder_entry, progress_var, root))
    process_button.configure(bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))  # 緑色の背景と白い文字
    process_button.pack(side="left", expand=True, padx=5)

    # フォルダを開くボタン
    Button(button_frame, text="フォルダを開く", command=lambda: open_processed_folder(folder_entry.get())).pack(side="left", expand=True, padx=5)

    # ファイル名変更ボタン
    rename_button = Button(button_frame, text="画像をリネーム", command=lambda: open_rename_dialog(root, folder_entry.get()))
    rename_button.configure(bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))  # 緑色の背景と白い文字
    rename_button.pack(side="left", expand=True, padx=5)

    # API Key UI at the bottom
    api_key_frame = Frame(root)
    api_key_frame.pack(side="bottom", fill="x", padx=20, pady=10)
    Label(api_key_frame, text="APIキー:").pack(side="left")
    api_key_var = StringVar(value=settings["api_key"])
    api_key_entry = Entry(api_key_frame, width=50, textvariable=api_key_var, show="*")
    api_key_entry.pack(side="left", fill="x", expand=True)

    # Initialize max_size_var and resize_enabled_var
    max_size_var = IntVar(value=settings["max_size"])
    resize_enabled_var = BooleanVar(value=settings["resize_enabled"])

    def on_close():
        save_settings(api_key_var.get(), max_size_var.get(), resize_enabled_var.get())
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()

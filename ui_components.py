import os
from tkinter import Tk, Label, Button, Entry, StringVar, Frame, BooleanVar, IntVar, Checkbutton, Toplevel, ttk, Text, Listbox, messagebox, Scrollbar
from text_extractor import get_available_templates, get_current_template, set_template, add_template, remove_template
from settings_manager import load_settings, save_settings
from file_handler import select_folder, open_processed_folder
from file_renamer import FileRenamer
from backup_manager import BackupManager

def open_template_manager(parent_window, template_label):
    """テンプレート管理画面を開く"""
    template_window = Toplevel(parent_window)
    template_window.title("テンプレート管理")
    template_window.geometry("800x500")
    template_window.minsize(800, 500)

    settings = load_settings()
    templates = settings.get("prompt_templates", {})
    
    # メインフレーム（スクロールに対応するため）
    main_frame = Frame(template_window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 左側のフレーム（テンプレート一覧）
    left_frame = Frame(main_frame)
    left_frame.pack(side="left", fill="y", padx=(0, 10))
    
    Label(left_frame, text="テンプレート一覧").pack(side="top", anchor="w")
    
    # テンプレート一覧をリストボックスで表示
    template_listbox = Listbox(left_frame, width=30, height=15)
    template_listbox.pack(side="top", fill="both", expand=True)
    
    for key, value in templates.items():
        template_listbox.insert("end", f"{value['name']} ({key})")
    
    # 右側のフレーム（編集エリア）
    right_frame = Frame(main_frame)
    right_frame.pack(side="left", fill="both", expand=True)
    
    # 編集フォーム
    edit_frame = Frame(right_frame)
    edit_frame.pack(fill="both", expand=True)
    
    Label(edit_frame, text="キー:").pack(anchor="w")
    key_var = StringVar()
    key_entry = Entry(edit_frame, textvariable=key_var, state="readonly")
    key_entry.pack(fill="x", pady=(0, 5))
    
    Label(edit_frame, text="名前:").pack(anchor="w")
    name_var = StringVar()
    name_entry = Entry(edit_frame, textvariable=name_var)
    name_entry.pack(fill="x", pady=(0, 5))
    
    Label(edit_frame, text="テンプレート:").pack(anchor="w")
    template_text = Text(edit_frame, height=12, wrap="word")
    template_text.pack(fill="both", expand=True, pady=(0, 10))
    
    # スクロールバーを追加
    scrollbar = ttk.Scrollbar(edit_frame, orient="vertical", command=template_text.yview)
    scrollbar.pack(side="right", fill="y")
    template_text.config(yscrollcommand=scrollbar.set)

    def update_save_button_state(state):
        if state == "normal":
            save_button.config(state=state, bg="#4CAF50", fg="white")
        else:
            save_button.config(state=state, bg="lightgray", fg="gray")
    
    def on_select(event):
        selection = template_listbox.curselection()
        if not selection:
            return
            
        selected_text = template_listbox.get(selection[0])
        key = selected_text.split(" (")[-1].rstrip(")")
        
        settings = load_settings()
        templates = settings.get("prompt_templates", {})
        template = templates[key]
        
        key_var.set(key)
        name_var.set(template["name"])
        template_text.delete("1.0", "end")
        template_text.insert("1.0", template["template"])
        
        if key == "white_tax":
            name_entry.config(state="disabled")
            template_text.config(state="disabled")
            update_save_button_state("disabled")
        else:
            name_entry.config(state="normal")
            template_text.config(state="normal")
            update_save_button_state("normal")
    
    template_listbox.bind('<<ListboxSelect>>', on_select)
    
    def save_template():
        key = key_var.get()
        if not key:
            return
            
        if key == "white_tax":
            messagebox.showerror("エラー", "デフォルトテンプレートは編集できません")
            return
            
        try:
            add_template(key, name_var.get(), template_text.get("1.0", "end-1c"))
            messagebox.showinfo("成功", "テンプレートを保存しました")
            
            template_listbox.delete(0, "end")
            settings = load_settings()
            templates = settings.get("prompt_templates", {})
            for k, v in templates.items():
                template_listbox.insert("end", f"{v['name']} ({k})")
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
    
    def add_new_template():
        dialog = Toplevel(template_window)
        dialog.title("新規テンプレート")
        dialog.geometry("400x350")
        
        Label(dialog, text="キー（英数字）:").pack(padx=10, pady=5)
        key_var = StringVar()
        Entry(dialog, textvariable=key_var).pack(padx=10, pady=5, fill="x")
        
        Label(dialog, text="名前:").pack(padx=10, pady=5)
        name_var = StringVar()
        Entry(dialog, textvariable=name_var).pack(padx=10, pady=5, fill="x")
        
        Label(dialog, text="テンプレート:").pack(padx=10, pady=5)
        template_text = Text(dialog, height=10, wrap="word")
        template_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        def save():
            key = key_var.get()
            if not key.isalnum():
                messagebox.showerror("エラー", "キーは英数字のみ使用可能です")
                return
            try:
                add_template(key, name_var.get(), template_text.get("1.0", "end-1c"))
                template_listbox.delete(0, "end")
                settings = load_settings()
                templates = settings.get("prompt_templates", {})
                for k, v in templates.items():
                    template_listbox.insert("end", f"{v['name']} ({k})")
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("エラー", str(e))
        
        Button(dialog, text="保存", command=save).pack(padx=10, pady=10)
    
    def remove_selected_template():
        selection = template_listbox.curselection()
        if not selection:
            return
            
        selected_text = template_listbox.get(selection[0])
        key = selected_text.split(" (")[-1].rstrip(")")
        
        if messagebox.askyesno("確認", f"テンプレート '{selected_text}' を削除しますか？"):
            try:
                remove_template(key)
                template_listbox.delete(selection)
                key_var.set("")
                name_var.set("")
                template_text.delete("1.0", "end")
            except ValueError as e:
                messagebox.showerror("エラー", str(e))
    
    # ボタンフレーム
    button_frame = Frame(template_window)
    button_frame.pack(side="bottom", fill="x", padx=20, pady=10)
    
    Button(button_frame, text="新規テンプレート", command=add_new_template).pack(side="left", padx=5)
    Button(button_frame, text="削除", command=remove_selected_template).pack(side="left", padx=5)
    save_button = Button(button_frame, text="保存", command=save_template)
    save_button.pack(side="right", padx=5)
    
    # 初期状態では保存ボタンを無効化
    save_button.config(state="disabled", bg="lightgray")

def open_advanced_settings(parent_window, template_label, api_key_var, max_size_var, resize_enabled_var):
    settings = load_settings()
    
    advanced_settings_window = Toplevel(parent_window)
    advanced_settings_window.title("詳細設定")
    advanced_settings_window.geometry("500x600")

    # テンプレート設定セクション
    template_frame = Frame(advanced_settings_window, relief="groove", borderwidth=1)
    template_frame.pack(side="top", fill="x", padx=20, pady=10)
    
    Label(template_frame, text="テンプレート設定", font=("Helvetica", 10, "bold")).pack(side="top", anchor="w", padx=10, pady=5)
    
    template_select_frame = Frame(template_frame)
    template_select_frame.pack(side="top", fill="x", padx=10, pady=5)
    Label(template_select_frame, text="テンプレート:").pack(side="left")
    templates = get_available_templates(settings)
    current_template_var = StringVar(value=settings["current_template"])
    template_dropdown = ttk.Combobox(template_select_frame, textvariable=current_template_var, values=list(templates.keys()), state="readonly")
    template_dropdown.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # テンプレート管理ボタン
    Button(template_frame, text="テンプレート管理", command=lambda: open_template_manager(advanced_settings_window, template_label)).pack(side="top", fill="x", padx=10, pady=5)
    
    # 現在のテンプレート内容を表示
    Label(template_frame, text="現在のテンプレート内容:").pack(side="top", anchor="w", padx=10, pady=5)
    template_content = Text(template_frame, height=8, wrap="word")
    template_content.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
    template_content.insert("1.0", get_current_template(settings))
    template_content.config(state="disabled")

    # 画像処理設定セクション
    image_frame = Frame(advanced_settings_window, relief="groove", borderwidth=1)
    image_frame.pack(side="top", fill="x", padx=20, pady=10)
    
    Label(image_frame, text="画像処理設定", font=("Helvetica", 10, "bold")).pack(side="top", anchor="w", padx=10, pady=5)
    
    # 最大画像サイズとリサイズ設定を横に並べる
    size_resize_frame = Frame(image_frame)
    size_resize_frame.pack(side="top", fill="x", padx=10, pady=5)
    
    # 最大画像サイズ
    size_frame = Frame(size_resize_frame)
    size_frame.pack(side="left", fill="x", expand=True)
    Label(size_frame, text="最大画像サイズ:").pack(side="left")
    Entry(size_frame, width=8, textvariable=max_size_var).pack(side="left", padx=5)
    
    # リサイズ有効
    resize_frame = Frame(size_resize_frame)
    resize_frame.pack(side="right", fill="x", expand=True)
    Checkbutton(resize_frame, text="リサイズ有効", variable=resize_enabled_var).pack(side="right")

    # デフォルトフォルダ設定セクション
    folder_frame = Frame(advanced_settings_window, relief="groove", borderwidth=1)
    folder_frame.pack(side="top", fill="x", padx=20, pady=10)
    
    Label(folder_frame, text="フォルダ設定", font=("Helvetica", 10, "bold")).pack(side="top", anchor="w", padx=10, pady=5)
    
    folder_input_frame = Frame(folder_frame)
    folder_input_frame.pack(side="top", fill="x", padx=10, pady=(0, 10))
    Label(folder_input_frame, text="デフォルトフォルダ:").pack(side="top", anchor="w")
    
    folder_select_frame = Frame(folder_input_frame)
    folder_select_frame.pack(side="top", fill="x", pady=5)
    default_folder_var = StringVar(value=settings.get("default_folder_path", os.path.expanduser("~\\Documents")))
    folder_entry = Entry(folder_select_frame, textvariable=default_folder_var)
    folder_entry.pack(side="left", fill="x", expand=True)
    
    def select_default_folder():
        from tkinter import filedialog
        folder_path = filedialog.askdirectory(initialdir=default_folder_var.get())
        if folder_path:
            default_folder_var.set(folder_path)
    
    Button(folder_select_frame, text="選択", command=select_default_folder).pack(side="right", padx=(5, 0))

    # 保存して閉じるボタン
    save_button = Button(advanced_settings_window, text="保存して閉じる", 
           command=lambda: save_and_close_advanced_settings(advanced_settings_window, api_key_var.get(), max_size_var.get(), resize_enabled_var.get(), default_folder_var.get()))
    save_button.configure(bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
    save_button.pack(side="bottom", fill="x", padx=20, pady=10)

    def on_template_change(event):
        set_template(template_dropdown.get())
        settings = load_settings()
        template = settings["prompt_templates"][template_dropdown.get()]["template"]
        template_content.config(state="normal")
        template_content.delete("1.0", "end")
        template_content.insert("1.0", template)
        template_content.config(state="disabled")
        template_label.config(text=f"テンプレート：{settings['prompt_templates'][template_dropdown.get()]['name']}")
    
    template_dropdown.bind('<<ComboboxSelected>>', on_template_change)

def save_and_close_advanced_settings(window, api_key, max_size, resize_enabled, default_folder_path):
    save_settings(api_key, max_size, resize_enabled, default_folder_path)
    window.destroy()

def open_rename_dialog(parent_window, target_dir: str):
    # 事前チェック
    csv_path = os.path.join(target_dir, "results_RyoSyuSyo.csv")
    
    # CSVファイルの存在チェック
    if not os.path.exists(csv_path):
        messagebox.showerror("エラー", "CSVファイルが見つかりません")
        return
        
    # CSVファイルのエラーメッセージチェック
    try:
        encodings = ['shift_jis', 'utf-8']
        has_error = False
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    if "申し訳ありません" in content:
                        has_error = True
                        break
            except UnicodeDecodeError:
                continue
                
        if has_error:
            messagebox.showerror("エラー", 
                "CSVファイルにエラーメッセージが含まれています。\n" +
                "先にCSVファイルの内容を修正してください。\n\n" +
                "修正方法：\n" +
                "1. CSVファイルを開いて、「申し訳ありません」を含む行を削除\n" +
                "2. または、update_csv.pyを実行してCSVファイルを更新")
            return
    except Exception as e:
        messagebox.showerror("エラー", f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}")
        return

    # ダイアログの作成
    rename_window = Toplevel(parent_window)
    rename_window.title("ファイル名変更")
    rename_window.geometry("600x400")
    
    # メインフレーム
    main_frame = Frame(rename_window)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # 説明ラベル
    Label(main_frame, text="CSVファイルの内容に基づいてファイル名を変更します。", wraplength=500).pack(side="top", pady=(0, 10))
    
    # 結果表示エリア
    result_frame = Frame(main_frame)
    result_frame.pack(side="top", fill="both", expand=True)
    
    result_text = Text(result_frame, wrap="word", height=15)
    result_text.pack(side="left", fill="both", expand=True)
    
    scrollbar = Scrollbar(result_frame, command=result_text.yview)
    scrollbar.pack(side="right", fill="y")
    result_text.config(yscrollcommand=scrollbar.set)
    
    def update_result(text):
        result_text.insert("end", text + "\n")
        result_text.see("end")

    def execute_rename():
        # バックアップ作成
        backup_manager = BackupManager(target_dir)
        zip_backup = backup_manager.create_zip_backup()
        if not zip_backup:
            messagebox.showerror("エラー", "バックアップの作成に失敗しました")
            return

        csv_backup = backup_manager.backup_csv_file(csv_path)
        if not csv_backup:
            messagebox.showerror("エラー", "CSVファイルのバックアップに失敗しました")
            return

        update_result(f"バックアップを作成しました: {os.path.basename(zip_backup)}")
        update_result(f"CSVバックアップを作成しました: {os.path.basename(csv_backup)}")

        # リネーム処理の実行
        renamer = FileRenamer(csv_path, target_dir)
        success_count, error_count, errors = renamer.rename_files()

        # エラーメッセージの表示
        if errors and "CSVファイルにエラーメッセージが含まれています" in errors[0]:
            messagebox.showwarning("警告", errors[0])
            return

        # 結果の表示
        update_result(f"\n処理結果:")
        update_result(f"成功: {success_count}件")
        update_result(f"失敗: {error_count}件")

        if errors:
            update_result("\nエラー内容:")
            for error in errors:
                update_result(f"- {error}")

            if error_count > 0:
                if messagebox.askyesno("確認", "エラーが発生しました。バックアップから復元しますか？"):
                    if backup_manager.restore_from_backup(zip_backup):
                        update_result("\nバックアップから復元しました")
                    else:
                        update_result("\n復元に失敗しました")

    # ボタンエリア
    button_frame = Frame(main_frame)
    button_frame.pack(side="bottom", fill="x", pady=10)

    Button(button_frame, text="実行", command=execute_rename).pack(side="right", padx=5)
    Button(button_frame, text="閉じる", command=rename_window.destroy).pack(side="right", padx=5) 
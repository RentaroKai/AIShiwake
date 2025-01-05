import os
import json
from tkinter import Tk, Label, Button, Entry, filedialog, StringVar, Frame, BooleanVar, IntVar, Checkbutton, Toplevel, ttk, messagebox, Text
from text_extractor import (gen_chat_response_with_gpt4, get_available_templates, 
                          get_current_template, set_template, add_template, 
                          remove_template, ensure_settings_file)

# グローバル変数として先に宣言
global api_key_var, max_size_var, resize_enabled_var, current_template_var
api_key_var = None
max_size_var = None
resize_enabled_var = None
current_template_var = None

def load_settings():
    return ensure_settings_file()

def save_settings(api_key, max_size, resize_enabled):
    settings = ensure_settings_file()
    settings["api_key"] = api_key
    settings["max_size"] = max_size
    settings["resize_enabled"] = resize_enabled
    with open("settings.json", "w", encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def write_to_text_file(file_path, text):
    with open(file_path, 'a') as file:
        file.write(text + "\n")

    # CSVファイルにも書き込む
    csv_file_path = os.path.splitext(file_path)[0] + '.csv'
    with open(csv_file_path, 'a') as csv_file:
        csv_file.write(text + "\n")

def select_folder(folder_entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, 'end')
        folder_entry.insert(0, folder_path)

def process_images(api_key, max_size, resize_enabled, folder_entry, progress_var, root):
    settings = load_settings()
    folder_path = folder_entry.get()
    if not folder_path:
        print("フォルダが選択されていません。")
        return
    
    # APIキーが空の場合、環境変数から取得を試みる
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            messagebox.showerror("エラー", "APIキーが設定されていません。設定画面でAPIキーを入力するか、環境変数OPENAI_API_KEYを設定してください。")
            return
    
    valid_extensions = ['.jpg', '.jpeg', '.png']
    output_text_file = os.path.join(folder_path, 'results.txt')
    image_files = [f for f in os.listdir(folder_path) if os.path.splitext(f)[1].lower() in valid_extensions]
    total_images = len(image_files)
    
    # 処理開始前にヘッダーを書き込む
    current_template = settings["current_template"]
    template_name = settings["prompt_templates"][current_template]["name"]
    with open(output_text_file, 'w') as f:
        f.write(f"# テンプレート: {template_name}\n")
    
    for index, image_file in enumerate(image_files):
        image_path = os.path.join(folder_path, image_file)
        try:
            process_single_image(image_path, image_file, api_key, output_text_file, max_size, resize_enabled)
            # プログレスバーを更新
            progress_var.set((index + 1) / total_images * 100)
            root.update_idletasks()  # UIを更新
        except Exception as e:
            print(f"Error processing {image_file}: {str(e)}")
            with open(os.path.join(folder_path, 'error_log.txt'), 'a') as log_file:
                log_file.write(f"Error processing {image_file}: {str(e)}\n")
    messagebox.showinfo("完了", "画像の処理が完了しました。")
    return folder_path  # 処理したフォルダのパスを返す

def process_single_image(image_path, image_file, api_key, output_text_file, max_size, resize_enabled):
    from PIL import Image
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()  # 一時ディレクトリを作成
    temp_image_path = os.path.join(temp_dir, image_file)  # 一時ファイルのパス

    with Image.open(image_path) as img:
        if resize_enabled and (img.size[0] > max_size or img.size[1] > max_size):
            img.thumbnail((max_size, max_size))
            img.save(temp_image_path)  # リサイズした画像を一時ファイルに保存
        else:
            shutil.copy(image_path, temp_image_path)  # リサイズ不要の場合、元の画像をコピー

    try:
        # prompt_templateパラメータを削除し、text_extractor側で現在のテンプレートを取得
        result = gen_chat_response_with_gpt4(temp_image_path, api_key)
        write_to_text_file(output_text_file, f"{image_file}, {result}")
    finally:
        shutil.rmtree(temp_dir)  # 一時ディレクトリを削除

def open_template_manager(parent_window):
    """テンプレート管理画面を開く"""
    template_window = Toplevel(parent_window)
    template_window.title("テンプレート管理")
    template_window.geometry("600x400")

    settings = load_settings()
    templates = settings.get("prompt_templates", {})
    
    # テンプレート一覧を表示するTreeview
    tree = ttk.Treeview(template_window, columns=("name", "template"), show="headings")
    tree.heading("name", text="テンプレート名")
    tree.heading("template", text="内容")
    tree.column("name", width=150)
    tree.column("template", width=400)
    
    for key, value in templates.items():
        tree.insert("", "end", values=(value["name"], value["template"]), tags=(key,))
    
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    def add_new_template():
        dialog = Toplevel(template_window)
        dialog.title("新規テンプレート")
        
        Label(dialog, text="キー（英数字）:").pack(padx=10, pady=5)
        key_var = StringVar()
        Entry(dialog, textvariable=key_var).pack(padx=10, pady=5)
        
        Label(dialog, text="名前:").pack(padx=10, pady=5)
        name_var = StringVar()
        Entry(dialog, textvariable=name_var).pack(padx=10, pady=5)
        
        Label(dialog, text="テンプレート:").pack(padx=10, pady=5)
        template_var = StringVar()
        Entry(dialog, textvariable=template_var, width=50).pack(padx=10, pady=5)
        
        def save():
            key = key_var.get()
            if not key.isalnum():
                messagebox.showerror("エラー", "キーは英数字のみ使用可能です")
                return
            try:
                add_template(key, name_var.get(), template_var.get())
                tree.insert("", "end", values=(name_var.get(), template_var.get()), tags=(key,))
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("エラー", str(e))
        
        Button(dialog, text="保存", command=save).pack(padx=10, pady=10)
    
    def remove_selected_template():
        selected = tree.selection()
        if not selected:
            return
        
        item = tree.item(selected[0])
        key = tree.item(selected[0])["tags"][0]
        
        try:
            remove_template(key)
            tree.delete(selected)
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
    
    # ボタンフレーム
    button_frame = Frame(template_window)
    button_frame.pack(fill="x", padx=10, pady=10)
    
    Button(button_frame, text="新規テンプレート", command=add_new_template).pack(side="left", padx=5)
    Button(button_frame, text="削除", command=remove_selected_template).pack(side="left", padx=5)

def open_advanced_settings():
    global current_template_var, max_size_var, resize_enabled_var
    settings = load_settings()
    
    advanced_settings_window = Toplevel()
    advanced_settings_window.title("詳細設定")
    advanced_settings_window.geometry("500x600")

    # テンプレート選択
    template_frame = Frame(advanced_settings_window)
    template_frame.pack(side="top", fill="x", padx=20, pady=10)
    
    Label(template_frame, text="テンプレート:").pack(side="top", anchor="w")
    templates = get_available_templates(settings)
    current_template_var = StringVar(value=settings["current_template"])
    template_dropdown = ttk.Combobox(template_frame, textvariable=current_template_var, values=list(templates.keys()), state="readonly")
    template_dropdown.pack(side="top", fill="x", pady=5)
    
    # 現在のテンプレート内容を表示
    Label(advanced_settings_window, text="現在のテンプレート内容:").pack(side="top", fill="x", padx=20, pady=10)
    template_content = Text(advanced_settings_window, height=10, wrap="word")
    template_content.pack(side="top", fill="both", expand=True, padx=20, pady=10)
    template_content.insert("1.0", get_current_template(settings))
    template_content.config(state="disabled")
    
    def on_template_change(event):
        # テンプレートを変更
        set_template(template_dropdown.get())
        # 表示内容を更新
        settings = load_settings()
        template = settings["prompt_templates"][template_dropdown.get()]["template"]
        template_content.config(state="normal")
        template_content.delete("1.0", "end")
        template_content.insert("1.0", template)
        template_content.config(state="disabled")
    
    template_dropdown.bind('<<ComboboxSelected>>', on_template_change)
    
    # テンプレート管理ボタン
    Button(template_frame, text="テンプレート管理", command=lambda: open_template_manager(advanced_settings_window)).pack(side="top", fill="x", pady=5)

    # 最大画像サイズ
    Label(advanced_settings_window, text="最大画像サイズ:").pack(side="top", fill="x", padx=20, pady=10)
    max_size_var = IntVar(value=settings["max_size"])
    Entry(advanced_settings_window, width=10, textvariable=max_size_var).pack(side="top", fill="x", padx=20, pady=10)

    # リサイズ有効
    resize_enabled_var = BooleanVar(value=settings["resize_enabled"])
    Checkbutton(advanced_settings_window, text="リサイズ有効", variable=resize_enabled_var).pack(side="top", fill="x", padx=20, pady=10)

    Button(advanced_settings_window, text="保存して閉じる", 
           command=lambda: save_and_close_advanced_settings(advanced_settings_window)).pack(side="bottom", fill="x", padx=20, pady=10)

def save_and_close_advanced_settings(window):
    save_settings(api_key_var.get(), max_size_var.get(), resize_enabled_var.get())
    window.destroy()

def open_processed_folder(folder_entry):
    folder_path = folder_entry.get()
    if folder_path and os.path.exists(folder_path):
        os.startfile(folder_path)

def main():
    global api_key_var, prompt_template_var, max_size_var, resize_enabled_var
    settings = load_settings()
    
    root = Tk()
    root.title("AI_レシート一括処理")

    # Add a button to open advanced settings, positioned at the top right
    Button(root, text="詳細設定", command=open_advanced_settings).pack(anchor="ne", padx=20, pady=10)

    # Folder path UI
    folder_frame = Frame(root)
    folder_frame.pack(side="top", fill="x", padx=20, pady=10)
    Label(folder_frame, text="folder:").pack(side="left")
    folder_entry = Entry(folder_frame, width=40)
    folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    Button(folder_frame, text="選択", command=lambda: select_folder(folder_entry)).pack(side="left")

    # プログレスバーのUIを追加
    progress_var = IntVar()
    progress_bar = ttk.Progressbar(root, maximum=100, variable=progress_var, mode='determinate')
    progress_bar.pack(side="top", fill="x", padx=20, pady=(10, 5))

    # ボタンを配置するフレーム
    button_frame = Frame(root)
    button_frame.pack(side="top", fill="x", padx=20, pady=(0, 10))

    # Start processing button
    Button(button_frame, text="レシート一括処理開始", command=lambda: process_images(api_key_var.get(), max_size_var.get(), resize_enabled_var.get(), folder_entry, progress_var, root)).pack(side="left", expand=True, padx=5)

    # フォルダを開くボタン
    Button(button_frame, text="フォルダを開く", command=lambda: open_processed_folder(folder_entry)).pack(side="left", expand=True, padx=5)

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

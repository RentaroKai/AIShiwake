#opneAIとのやり取りの部分
import base64
import json
import os
from openai import OpenAI

SYSTEM_ROLE_CONTENT = "このシステムは提供された画像の内容の説明を生成します。画像を識別し視覚情報をテキスト形式で提供します。"

def ensure_settings_file():
    """設定ファイルが存在しない場合、デフォルト設定で作成する"""
    if not os.path.exists("settings.json"):
        default_settings = {
            "api_key": "",
            "max_size": 1800,
            "resize_enabled": False,
            "current_template": "white_tax",
            "default_folder_path": os.path.expanduser("~\\Documents"),  # デフォルトのフォルダパス
            "prompt_templates": {
                "white_tax": {
                    "name": "白色申告用",
                    "template": "画像から、取引年月日(yyyy/mm/ddのみ時間なし)、店舗名、商品名(要約)、合計金額(通貨記号は削除)、推測される勘定科目名を抽出しカンマ区切り(,)でreturnせよ"
                }
            }
        }
        with open("settings.json", "w", encoding='utf-8') as f:
            json.dump(default_settings, f, indent=4, ensure_ascii=False)
        return default_settings
    
    try:
        with open("settings.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise ValueError("settings.jsonの形式が正しくありません。")

def save_settings(settings):
    """設定を保存する"""
    with open("settings.json", "w", encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def get_current_template(settings):
    """現在選択されているテンプレートを取得"""
    current = settings.get("current_template", "white_tax")
    templates = settings.get("prompt_templates", {})
    if current not in templates:
        current = "white_tax"  # デフォルトに戻す
        settings["current_template"] = current
        save_settings(settings)
    return templates[current]["template"]

def get_available_templates(settings):
    """利用可能なテンプレート一覧を取得"""
    templates = settings.get("prompt_templates", {})
    return {key: value["name"] for key, value in templates.items()}

def set_template(template_key):
    """テンプレートを切り替える"""
    settings = ensure_settings_file()
    if template_key not in settings.get("prompt_templates", {}):
        raise ValueError(f"テンプレート '{template_key}' が見つかりません。")
    settings["current_template"] = template_key
    save_settings(settings)

def add_template(key, name, template):
    """新しいテンプレートを追加"""
    settings = ensure_settings_file()
    settings.setdefault("prompt_templates", {})
    settings["prompt_templates"][key] = {
        "name": name,
        "template": template
    }
    save_settings(settings)

def remove_template(key):
    """テンプレートを削除"""
    settings = ensure_settings_file()
    if key == "white_tax":
        raise ValueError("デフォルトテンプレートは削除できません。")
    if key in settings.get("prompt_templates", {}):
        if settings.get("current_template") == key:
            settings["current_template"] = "white_tax"
        del settings["prompt_templates"][key]
        save_settings(settings)

def get_gpt_openai_apikey():
    # 環境変数からAPIキーを取得
    env_api_key = os.environ.get("OPENAI_API_KEY")
    if env_api_key:
        return env_api_key

    try:
        if not os.path.exists("secret.json"):
            raise FileNotFoundError("secret.jsonファイルが見つかりません。APIキーを設定してください。")
            
        with open("secret.json") as f:
            secret = json.load(f)
            
        if "OPENAI_API_KEY" not in secret:
            raise KeyError("secret.jsonにOPENAI_API_KEYが設定されていません。")
            
        return secret["OPENAI_API_KEY"]
    except json.JSONDecodeError:
        raise ValueError("secret.jsonの形式が正しくありません。")

def create_secret_file(api_key):
    """APIキーを保存するための関数"""
    with open("secret.json", "w") as f:
        json.dump({"OPENAI_API_KEY": api_key}, f, indent=4)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/jpeg;base64,{encoded_string}"

def create_message(system_role, prompt, image_base64):
    message = [
        {
            'role': 'system',
            'content': system_role
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': prompt
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': image_base64
                    }
                },
            ]
        },
    ]
    return message

def gen_chat_response_with_gpt4(image_path, api_key, prompt_template=None):
    openai_client = OpenAI(api_key=api_key)
    image_base64 = encode_image(image_path)
    
    # プロンプトテンプレートが指定されていない場合は現在の設定から取得
    if prompt_template is None:
        settings = ensure_settings_file()
        prompt_template = get_current_template(settings)
    
    messages = create_message(SYSTEM_ROLE_CONTENT, prompt_template, image_base64)

    response = openai_client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        temperature=0,
    )

    if response and response.choices:
        extracted_data = response.choices[0].message.content
    else:
        extracted_data = "No data extracted"

    return extracted_data
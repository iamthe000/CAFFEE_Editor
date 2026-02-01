# CAFFEE プラグイン開発ガイド (PLUGINS_ja.md)

CAFFEEは、Pythonスクリプトを使用してエディタの機能を拡張できる強力なプラグインシステムを備えています。

---

## 1. プラグインの構成

プラグインは `~/.caffee_setting/plugins/` ディレクトリに配置された単一の `.py` ファイルです。
CAFFEEの起動時に、このディレクトリ内の各ファイルがロードされ、定義されている `init(editor)` 関数が呼び出されます。

### 基本構造
```python
def init(editor):
    # ここに拡張処理を記述します
    editor.set_status("My Plugin Loaded!")
```

---

## 2. API リファレンス

`init` 関数に渡される `editor` オブジェクトを通じて、以下のメソッドを利用できます。

### 2.1 キーバインドの登録
- **`bind_key(key_code, func)`**
    - 指定したキーコードに、エディタインスタンスを受け取る関数をバインドします。
    - キーコードは `curses` の定数や、`ord('a')` などの文字コード、または `ctrl('s')` （CAFFEE内部関数）などを利用します。

### 2.2 シンタックスルールの登録
- **`register_syntax_rule(lang_name, rule_dict)`**
    - 新しい言語のシンタックスハイライトを定義します。
    - `rule_dict` には `extensions`（拡張子のリスト）、`keywords`（正規表現）、`comments`、`strings`、`numbers`、`symbol_pattern` を含めます。

### 2.3 ビルドコマンドの登録
- **`register_build_command(extension, command)`**
    - 特定の拡張子のファイルに対するビルド/実行コマンド（`Ctrl+B`で使用）を登録します。
    - `command` 内で `{filename}` や `{base}` などのプレースホルダが使用可能です。

### 2.4 テンプレートの登録
- **`register_template(language, template_string)`**
    - `Ctrl+T` で挿入できる新規ファイル用のテンプレートを登録します。

### 2.5 設定項目の登録
- **`register_config(key, default_value)`**
    - プラグイン独自の設定項目を登録し、`setting.json` で管理できるようにします。

---

## 3. 実践例: 自動保存プラグイン

以下は、一定時間ごとにファイルを自動保存するシンプルなプラグインの例です。

```python
import time

def init(editor):
    def auto_save(editor):
        if editor.modified and editor.filename:
            editor.save_file()
            editor.set_status("Auto-saved.", timeout=2)

    # Ctrl+S 以外に独自に保存ショートカットを追加する例
    # editor.bind_key(20, auto_save) # Ctrl+Tに割り当てるなど
```

---

## 4. プラグインの管理

- **有効化/無効化**: スタート画面（`Ctrl+S`で表示）で `Ctrl+P` を押して `Plugin Manager` を開くことで、各プラグインの有効/無効を切り替えられます。無効化されたプラグインは `plugins/disabled/` サブディレクトリに移動されます。
- **デバッグ**: プラグインでエラーが発生した場合、エディタのステータスバーにエラーメッセージが表示されます。詳細なトレースバックを確認するには、ターミナルで `python3 caffee.py 2> error.log` のように実行して標準エラー出力をキャプチャしてください。

# ☕ CAFFEE コマンドラインテキストエディタ

<a href="README.md">🇬🇧 English README</a>　
<a href="https://github.com/iamthe000/CAFFEE_Editor_Japanese_UI_plugin_Official.git">公式UI日本語化プラグイン</a>　
<a href="Nuitka_Step.md">Nuitkaによる高速化手順</a>　
<a href="Setup_PATH.md">PATHのセットアップ方法</a>

**CAFFEE**は、Pythonで書かれ、cursesライブラリを使用した軽量なターミナルテキストエディタです。シンプルで拡張性があり、効率的な編集体験を、最新のIDE風の機能と共にターミナル内で直接提供することを目指しています。

---

## ✨ v2.0.0の新機能

### 🎨 **モダンなUI機能強化**
- **インタラクティブなスタート画面** - 設定、プラグイン、ファイルエクスプローラーへの素早いアクセス
- **タブバーシステム** - ビジュアルなタブ管理による複数ファイル編集
- **分割パネルレイアウト** - ファイルエクスプローラーと統合ターミナルパネルの切り替え
- **強化されたビジュアルデザイン** - 改善された配色とステータス表示

### 🚀 **生産性向上機能**
- **Git連携** - ヘッダーに現在のGitブランチ名を表示し、各タブでファイルの変更状態（`~`: 変更済み, `+`: 新規/未追跡）を確認
- **統合ファイルエクスプローラー** (`Ctrl+F`) - エディタを離れずにファイルをブラウズ・オープン
- **組み込みターミナル** (`Ctrl+T`) - エディタから直接コマンド実行とコードの実行
- **プラグインマネージャー** (スタート画面から`Ctrl+P`) - ビジュアルインターフェースでプラグインの有効化/無効化
- **ビルド&実行** (`Ctrl+B`) - Python、JavaScript、Go、C/C++、Rust、シェルスクリプトの自動コンパイルと実行
- **スマート横スクロール** - nanoスタイルの長い行に対する滑らかなスクロール
- **全角文字サポート** - 日本語などのワイド文字の適切な処理

### 🎨 **シンタックスハイライト**
- Python、JavaScript、C/C++、Go、Rust、HTML、Markdownに対応
- 設定によるカラースキームのカスタマイズ

### 📑 **マルチタブ編集**
- `Ctrl+S` - 新規タブ作成 / スタート画面に戻る
- `Ctrl+L` - 次のタブに切り替え
- `Ctrl+X` - 現在のタブを閉じる（未保存の場合はプロンプト表示）

---

## 💡 主な機能

- **小型で集中**した編集体験
- 設定可能な制限付きの**Undo/Redo**履歴
- **マークベースの選択**とクリップボード操作（カット/コピー/ペースト）
- **行操作**（削除、コメント/アンコメント、ジャンプ）
- 自動バックアップ作成を伴う**アトミックなファイル保存**
- 拡張性のための**プラグインシステム**
- カスタマイズのための**JSON設定**

---

## 💻 インストール

### 必要要件
- **Python 3.6以上**
- Unix系ターミナル（Linux、macOS、ChromeOS Linuxシェル）
- `curses`ライブラリ（通常Pythonに含まれています）

### クイックスタート

```bash
# リポジトリをダウンロードまたはクローン
git clone <repository-url>
cd CAFFEE_Editor

# 直接実行
python3 caffee.py

# または特定のファイルを開く
python3 caffee.py /path/to/file.py
```

### オプション: Nuitkaによる高速化

起動と実行を大幅に高速化するには、Nuitkaでコンパイル（Debian/Ubuntu）:

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install nuitka
sudo apt install patchelf
python -m nuitka --standalone caffee.py
cd caffee.dist
./caffee.bin
```

詳細な手順とトラブルシューティングは [Nuitka_Step.md](Nuitka_Step.md) を参照してください。

---

## ⌨️ キーバインディング

### ファイル操作
| キー | 動作 |
|-----|------|
| `Ctrl+O` | 現在のファイルを保存 |
| `Ctrl+X` | 現在のタブを閉じる / 終了 |
| `Ctrl+S` | 新規タブ / スタート画面 |
| `Ctrl+L` | 次のタブに切り替え |

### 編集
| キー | 動作 |
|-----|------|
| `Ctrl+Z` | 元に戻す |
| `Ctrl+R` | やり直し |
| `Ctrl+K` | カット（行または選択範囲） |
| `Ctrl+U` | ペースト |
| `Ctrl+C` | 選択範囲をコピー |
| `Ctrl+Y` | 現在の行を削除 |
| `Ctrl+/` | コメント切り替え |

### ナビゲーション & 検索
| キー | 動作 |
|-----|------|
| `Ctrl+W` | 検索（正規表現サポート） |
| `Ctrl+G` | 行番号へジャンプ |
| `Ctrl+E` | 行末へ移動 |
| `Ctrl+A` | 全選択 / 選択解除 |
| `Ctrl+6` | マークを設定/解除（選択開始） |
| 矢印キー | カーソル移動 |
| PageUp/Down | ページスクロール |

### パネル & ツール
| キー | 動作 |
|-----|------|
| `Ctrl+F` | ファイルエクスプローラー切り替え |
| `Ctrl+T` | 統合ターミナル切り替え |
| `Ctrl+B` | 現在のファイルをビルド/実行 |
| `Ctrl+P` | プラグインマネージャー（スタート画面から） |
| `Esc` | パネルからエディタに戻る |

---

## ⚙️ 設定

ユーザー設定は `~/.caffee_setting/setting.json` に保存されます。

### 設定ファイルの例

```json
{
  "tab_width": 4,
  "history_limit": 50,
  "use_soft_tabs": true,
  "backup_subdir": "backup",
  "backup_count": 5,
  
  "show_splash": true,
  "splash_duration": 500,
  "start_screen_mode": true,
  
  "explorer_width": 35,
  "terminal_height": 10,
  "show_explorer_default": false,
  "show_terminal_default": false,
  
  "colors": {
    "header_text": "BLACK",
    "header_bg": "WHITE",
    "error_text": "WHITE",
    "error_bg": "RED",
    "linenum_text": "CYAN",
    "linenum_bg": "DEFAULT",
    "selection_text": "BLACK",
    "selection_bg": "CYAN",
    "keyword": "YELLOW",
    "string": "GREEN",
    "comment": "MAGENTA",
    "number": "BLUE",
    "ui_border": "WHITE",
    "tab_active_bg": "BLUE"
  }
}
```

### 設定オプション

- **エディタ設定**: `tab_width`, `history_limit`, `use_soft_tabs`
- **バックアップ**: `backup_subdir`, `backup_count`（自動バージョン管理バックアップ）
- **起動**: `show_splash`, `splash_duration`, `start_screen_mode`
- **レイアウト**: `explorer_width`, `terminal_height`, パネルのデフォルト表示設定
- **色**: すべてのUI要素の包括的な色カスタマイズ

---

## 🧩 プラグインシステム

プラグインは `~/.caffee_setting/plugins/` 内のPythonファイルです。

### プラグインAPI

プラグインは以下にアクセスできる `init(editor)` 関数を公開できます:

- **カーソル & バッファアクセス**: `get_cursor_position()`, `get_line_content()`, `get_buffer_lines()`
- **編集操作**: `insert_text_at_cursor()`, `delete_range()`, `replace_text()`
- **選択**: `get_selection_text()`, `get_selection_range()`
- **キーバインディング**: `bind_key(key_code, function)`
- **UIフィードバック**: `set_status_message()`, `redraw_screen()`
- **ユーザー入力**: `prompt_user(message, default="")`

### プラグインの例

```python
def init(editor):
    def uppercase_selection(ed):
        text = ed.get_selection_text()
        if text:
            lines = [line.upper() for line in text]
            # 選択範囲を処理...
            ed.set_status_message("大文字に変換しました!")
        else:
            ed.set_status_message("選択範囲がありません")
    
    # Ctrl+Shift+Uにバインド（ターミナルが対応している場合）
    editor.bind_key(21, uppercase_selection)
```

### プラグインマネージャー

スタート画面から `Ctrl+P` でアクセス:
- インストール済みプラグインの表示
- スペースキーでプラグインの有効化/無効化
- 変更はエディタ再起動後に反映

無効化されたプラグインは `~/.caffee_setting/plugins/disabled/` に移動されます。

---

## 🚀 組み込みコマンド

CAFFEEは自動的にファイルタイプを検出し、ビルド/実行コマンドを提供します:

| ファイルタイプ | コマンド |
|-----------|---------|
| `.py` | `python3 <file>` |
| `.js` | `node <file>` |
| `.go` | `go run <file>` |
| `.c` | `gcc <file> -o <o> && ./<o>` |
| `.cpp`, `.cc` | `g++ <file> -o <o> && ./<o>` |
| `.sh` | `bash <file>` |
| `.rs` | `rustc <file> && ./<o>` |

`Ctrl+B` を押すと、現在のファイルを保存して実行します。出力は統合ターミナルに表示されます。

---

## 🛠️ トラブルシューティング

### 表示の問題
- **日本語テキストが文字化け?** ロケール設定については [Nuitka_Step.md](Nuitka_Step.md) を参照
- **色が機能しない?** ターミナルが256色をサポートしていることを確認
- **cursesエラー?** プラットフォームでPythonのcursesライブラリが利用可能か確認

### ファイル操作
- **ディスク上のファイルが変更された**: CAFFEEは外部変更を検出しますが、データ損失を防ぐため自動リロードは行いません
- **バックアップファイル**: タイムスタンプ付きで `~/.caffee_setting/backup/` に配置

### ターミナル統合
- **ターミナルが動作しない?** 統合ターミナルは `pty` サポートが必要です（Unix系システムのみ）
- **ビルドコマンドが失敗する?** 必要なコンパイラ/インタープリターがPATHに含まれていることを確認

---

## 🤝 コントリビューション

コントリビューションを歓迎します！以下をお願いします:

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 焦点を絞った、よく文書化された変更を加える
4. 複数のターミナル環境でテスト
5. 明確な説明付きのプルリクエストを送信

### 開発ガイドライン
- Python 3.6以上との互換性を維持
- ターミナルのリサイズ動作を尊重
- コードベースをシンプルで読みやすく保つ
- 既存のコードスタイルに従う

---

## 📄 ライセンス

MITライセンス - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

## 🙏 謝辞

Pythonの `curses` ライブラリで構築。nano、vim、および最新のコードエディタからインスピレーションを得ています。

**CAFFEE** - *ターミナルでコードを淹れよう* ☕

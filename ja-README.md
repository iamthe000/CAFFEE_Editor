<div align="center">

# ☕ CAFFEE ターミナルテキストエディタ

<img src="preview.png" width="600px">

**ターミナルで動作する、軽量でモダン、そして拡張可能なテキストエディタ。**

</div>

<div align="center">
【祝】PyPI 全期間でのダウンロードが5Kを超えました🎉

[![PyPI Version](https://img.shields.io/pypi/v/caffee.svg)](https://pypi.org/project/caffee/)
[![Python Version](https://img.shields.io/pypi/pyversions/caffee.svg)](https://pypi.org/project/caffee/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[]([![Downloads](https://img.shields.io/pypi/dm/caffee.svg)](https://pypi.org/project/caffee/))
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/caffee?period=total&units=INTERNATIONAL_SYSTEM&left_color=GRAY&right_color=GREEN&left_text=TotalDownloads)](https://pepy.tech/projects/caffee)


</div>

<div align="center">

<a href="README.md">🇬🇧 English</a> | <a href="Nuitka_Step.md">Nuitkaによる高速化手順</a> | <a href="Setup_PATH.md">PATHのセットアップ方法</a> | <a href="https://github.com/iamthe000/CAFFEE_Editor_Japanese_UI_plugin_Official.git">公式UI日本語化プラグイン</a> | <a href="https://github.com/iamthe000/CAFFEETERIA">軽量版(CAFFEETERIA)</a>

</div>

---

**CAFFEE**は、Pythonで書かれたターミナルテキストエディタです。シンプルで拡張性があり、効率的な編集体験を、最新のIDE風の機能と共に提供することを目指しています。

## 目次
- [💡 主な機能](#-主な機能)
- [💻 インストール](#-インストール)
- [⌨️ キーバインディング](#️-キーバインディング)
- [🚀 コマンドモード](#-コマンドモード)
- [⚙️ 設定](#️-設定)
- [🧩 プラグインシステム](#-プラグインシステム)
- [🛠️ トラブルシューティング](#️-トラブルシューティング)
- [🤝 コントリビューション](#-コントリビューション)
- [📄 ライセンス](#-ライセンス)


---

## 💡 主な機能

### 🎨 **モダンなUIとナビゲーション**
- **マルチタブ編集** - タブバーシステムによる複数ファイルの同時編集 (`Ctrl+S`, `Ctrl+L`, `Ctrl+X`)。
- **ブレッドクラムバー** - ファイルパスとコードシンボル（関数/クラス）をリアルタイム表示し、コンテキストを把握しやすく。
- **Vim モード** - オプションのモーダル編集をサポート。高速なナビゲーションとテキスト操作を実現。
- **相対行番号** (`Ctrl+U`) - 相対行番号表示を切り替え、行移動をより効率的に。
- **Nerd Font 統合** - 高品質なアイコン表示に対応。Hack Nerd Font の自動インストールヘルパーも搭載。
- **スマート横スクロール** - nanoスタイルの滑らかなスクロール。

### 🚀 **生産性と編集機能**
- **対話的な検索と置換** (`Ctrl+W`) - VSCode風のインターフェースでテキストを検索・置換。「すべて置換」(`Ctrl+A`) にも対応。
- **システムクリップボード同期** - Windows, macOS, Linux 間でシームレスなコピー＆ペースト同期。
- **予測テキスト** - バッファ内容に基づいたインテリジェントな自動補完。
- **Git 連携** - ブランチ名、ファイル状態マーカー (`~`: 変更あり, `+`: 新規)、および Git Diff 表示 (`Ctrl+D`)。
- **強化されたファイルエクスプローラー** (`Ctrl+F`) - ソート、ワイルドカード検索、フルスクリーンモードを備えた本格的なファイル管理。
- **統合ターミナル** (`Ctrl+N`) - エディタを離れることなくシェルコマンドを実行。
- **CAFFEINE マクロ言語** - 専用のシンプルなマクロ言語で、エディタの操作を自動化。
- **コマンドモード** (`Ctrl+P`) - `:open`, `:saveas`, `:set`, `:delcomm` などの強力なコマンド。

### ⚙️ **拡張性と高度なサポート**
- **ビルド&実行** (`Ctrl+B`) - 20以上の言語に対応した最適化されたテンプレートとビルドコマンド。
- **高度なシンタックスハイライト** - Python, JS/TS, C/C++, Go, Rust, Java, Ruby, Swift などの多数の言語に対応。
- **プラグインシステム** - カスタムPythonスクリプトによる機能拡張。
- **アトミックなファイル保存** - 自動バックアップ作成を伴う安全なファイル保存。
- **Undo/Redo** - 設定可能な制限付きの包括的な履歴管理。

---

## 💻 インストール

### 必要要件
- **Python 3.8以上**
- Unix系ターミナル（Linux、macOS、ChromeOS Linuxシェル）
- `curses`ライブラリ（通常Pythonに含まれています）

### クイックスタート
```bash
# PyPIからインストール
pip install caffee

# エディタを実行
caffee

# または特定のファイルを開く
caffee /path/to/file.py
```

### アップグレード
```bash
pip install caffee --upgrade
```

### オプション: Nuitkaによる高速化
起動を大幅に高速化するには、Nuitkaでコンパイルします。詳細は[Nuitkaによる高速化手順](Nuitka_Step.md)を参照してください。

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
| `Ctrl+V` | ペースト（システムクリップボード同期） |
| `Ctrl+C` | 選択範囲をコピー |
| `Ctrl+U` | 相対行番号表示の切り替え |
| `Ctrl+Y` | 現在の行を削除 |
| `Ctrl+/` | コメント切り替え |

### ナビゲーション & 検索
| キー | 動作 |
|-----|------|
| `Ctrl+W` | 検索（正規表現サポート） |
| `Ctrl+G` | 行番号へジャンプ |
| `Ctrl+E` | 行末へ移動 |
| `Ctrl+A` | 全選択 / 選択解除 |
| `Ctrl+6` | マークを設定/解除 |

### パネル & ツール
| キー | 動作 |
|-----|------|
| `Ctrl+F` | ファイルエクスプローラー切り替え |
| `Ctrl+N` | 統合ターミナル切り替え |
| `Ctrl+U` | 相対行番号表示の切り替え |
| `Ctrl+T` | テンプレートを挿入 |
| `Ctrl+B` | 現在のファイルをビルド/実行 |
| `Ctrl+D` | 現在のファイルのGit差分を表示 |
| `Ctrl+P` | コマンドモードに入る |
| `Esc` | パネルからエディタに戻る |

---

## 🚀 コマンドモード
`Ctrl+P`を押してコマンドモードに入り、コマンドを入力してEnterキーを押します。

| コマンド | エイリアス | 説明 |
|---------|-------|-------------|
| `open <file>`| `o <file>` | 新しいタブでファイルを開く。 |
| `save` | `w` | 現在のファイルを保存する。 |
| `saveas <file>` | | 新しい名前でファイルを保存する。 |
| `copy` | | 選択した範囲をシステムクリップボードにコピーする。 |
| `paste` | | システムクリップボードから内容を貼り付ける。 |
| `close` | `q` | 現在のタブを閉じる。 |
| `quit` | `qa` | エディタを終了する（未保存のファイルは確認）。 |
| `new` | | 新しい空のタブを作成する。 |
| `set <key> <val>` | | 設定を変更する (例: `set tab_width 2`)。 |
| `undo` | | 最後の操作を取り消す。 |
| `redo` | | 取り消した操作をやり直す。 |
| `goto <line>` | | 指定した行番号にジャンプする。 |
| `next` | `tabn` | 次のタブに切り替える。 |
| `prev` | `tabp` | 前のタブに切り替える。 |
| `find <query>` | | 指定したクエリを検索する。 |
| `replace <old> <new>` | | `<old>` を `<new>` に置換する。 |
| `expw <width>` | `explorer_width` | ファイルエクスプローラーの幅を設定する。 |
| `termh <height>` | `terminal_height` | 統合ターミナルの高さを設定する。 |
| `diff` | | 現在のファイルのGit差分を新しいタブで表示。 |
| `delcomm` | | 現在のバッファからすべてのコメントを削除。 |
| `template <lang>` | | 指定した言語のテンプレートを挿入する。 |
| `macro <file>` | | CAFFEINE マクロファイルを実行する。 |

---

## ⚙️ 設定

ユーザー設定は `~/.caffee_setting/setting.json` に保存されます。このファイルを直接編集するか、スタート画面の対話的な設定マネージャー (`Ctrl+S` -> `[2] Choice setting`) を使用できます。

### 設定ファイルの例
```json
{
  "tab_width": 4,
  "history_limit": 50,
  "use_soft_tabs": true,
  "auto_indent": true,
  "backup_count": 5,
  "enable_predictive_text": true,
  
  "templates": {
    "python": "def main():\\n    print(\"Hello, world!\")\\n\\nif __name__ == \"__main__\":\\n    main()",
    "javascript": "function main() {\\n    console.log('Hello, world!');\\n}\\n\\nmain();"
  },

  "start_screen_mode": true,
  "show_explorer_default": true,
  "explorer_show_details": true,
  
  "colors": {
    "header_text": "BLACK",
    "header_bg": "WHITE",
    "keyword": "YELLOW",
    "string": "GREEN",
    "comment": "MAGENTA",
    "number": "BLUE",
    "diff_add": "GREEN",
    "diff_remove": "RED"
  }
}
```

### 主な設定オプション
- **`auto_indent`**: 自動インデントの有効/無効。
- **`enable_predictive_text`**: 自動補完候補の有効/無効。
- **`explorer_show_details`**: エクスプローラーでファイルサイズと更新日時を表示。
- **`displayed_keybindings`**: フッターバーに表示するキーバインドをカスタマイズ。
- **`colors`**: すべてのUI要素の包括的な色カスタマイズ。

---

## ☕ CAFFEINE マクロ言語
CAFFEINEは、CAFFEE専用に設計されたシンプルなマクロ言語です。一連のエディタ操作を定義することで、繰り返しの作業を自動化できます。

### マクロの構文
マクロは `.caffeine` ファイルに保存されます。各行にはコマンド、カーソル移動、またはテキスト挿入を記述できます。

| コマンド | 説明 |
|---------|-------------|
| `# comment` | `#` で始まる行は無視されます。 |
| `:command` | 任意の CAFFEE エディタコマンドを実行します。 |
| `MOVE <y> <x>` | カーソルを指定した行と列に移動します。 |
| `INSERT "text"` | カーソル位置に指定したテキストを挿入します。 |
| `TYPE "text"` | テキストを1文字ずつタイピングするように挿入します。 |
| `WAIT <ms>` | 指定したミリ秒数だけ実行を一時停止します。 |
| `COMMAND "cmd"` | エディタコマンドを実行するための別名です。 |

### 使い方
マクロを実行するには、コマンドモード (`Ctrl+P`) で `:macro <filename>` コマンドを使用します。CAFFEE はカレントディレクトリ、または `~/.caffee_setting/macros/` 内のファイルを探します。

---

## 🧩 プラグインシステム
`~/.caffee_setting/plugins/` にカスタムPythonスクリプトを配置してCAFFEEの機能を拡張します。対話的なプラグインマネージャー（スタート画面 -> `Ctrl+P`）でプラグインの有効/無効を切り替えられます。

### プラグインAPI
プラグインは `init(editor)` エントリポイントを通じてエディタの状態と機能にアクセスでき、以下のことが可能です:
- カスタムキーバインドの登録。
- 新しいシンタックスハイライトルールの登録。
- 新しいビルドコマンドの追加。
- バッファとカーソルの操作。
- ステータスバーへのカスタムメッセージ表示。

---

## 🛠️ トラブルシューティング

- **表示の問題**: 色や特殊文字が正しく表示されない場合、ターミナルが256色とUTF-8をサポートしていることを確認してください。iSHのような環境では、CAFFEEが互換性のある`TERM`変数を自動的に設定しようとします。
- **ファイルアクセス**: ファイルの保存やバックアップ作成でエラーが発生する場合、`~/.caffee_setting/`の権限を確認してください。
- **ターミナルが動作しない**: 統合ターミナルは`pty`サポートが必要です（LinuxとmacOSでは標準）。

---

## 🤝 コントリビューション
コントリビューションを歓迎します！リポジトリをフォークし、機能ブランチで焦点を絞った変更を加え、プルリクエストを送信してください。

---

## 📄 ライセンス
このプロジェクトはGNU General Public License v3の下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

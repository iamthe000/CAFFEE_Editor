#!/usr/bin/env python3
import curses
import sys
import os
import re
import json
import importlib.util
import glob
import datetime
import shutil
import traceback
import unicodedata
import select
import difflib
import subprocess
import time
import urllib.request
import platform

# --- 定数定義 (Key Codes) ---
CTRL_A = 1
CTRL_B = 2  # Build/Run Command
CTRL_C = 3
CTRL_D = 4
CTRL_E = 5
CTRL_F = 6
CTRL_G = 7
CTRL_K = 11
CTRL_L = 12 # Next Tab
CTRL_N = 14
CTRL_O = 15
CTRL_P = 16
CTRL_R = 18
CTRL_S = 19 # New Tab / Start Screen
CTRL_T = 20
CTRL_U = 21
CTRL_V = 22
CTRL_W = 23
CTRL_X = 24 # Close Tab / Exit
CTRL_Y = 25
CTRL_Z = 26
CTRL_MARK = 30
CTRL_SLASH = 31
KEY_TAB = 9
KEY_ENTER = 10
KEY_RETURN = 13
KEY_BACKSPACE = 127
KEY_BACKSPACE2 = 8
KEY_ESC = 27

# OS依存: ptyはUnix系のみ
try:
    import pty
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

# --- デフォルト設定 ---
EDITOR_NAME = "CAFFEE"
VERSION = "2.9.0"
DEFAULT_CONFIG = {
    "tab_width": 4,
    "history_limit": 50,
    "use_soft_tabs": True,
    "auto_indent": True,
    "backup_subdir": "backup",
    "backup_count": 5,
    "enable_predictive_text": True, # 予測変換を有効にするか
    # --- Splash / Start Screen Settings ---
    "show_splash": True,         # スプラッシュ画面を表示するか
    "splash_duration": 500,     # 自動遷移する場合の表示時間(ms)
    "start_screen_mode": True,  # 起動時にスタート画面(インタラクティブ)を有効にするか
    "show_startup_time": False, # 起動時間を表示するか
    # --------------------------
    # --- UI Layout Settings ---
    "explorer_width": 50,
    "terminal_height": 7,
    "explorer_icon_theme": "nerd_font", # "emoji" or "nerd_font"
    "show_explorer_default": True,
    "show_terminal_default": True,
    "explorer_show_details": True, # エクスプローラーで日付やサイズを表示するか
    "show_relative_linenum": False, # 相対行数を表示するか
    "show_breadcrumb": True, # ファイルパスやシンボルを表示するか
    "vim_mode": False, # vimモードを有効にするか
    # --------------------------
    # --- Keybinding Display ---
    "displayed_keybindings": [
        "close_tab", "new_start", "next_tab", "save", "cut", "paste", "search",
        "undo", "redo", "copy", "build", "mark", "select_all", "goto",
        "delete_line", "comment", "explorer", "terminal", "line_end", "command", "template", "relative_linenum"
    ],
    # --------------------------
    "templates": {
        "python": """def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()""",
        "javascript": """function main() {
    console.log('Hello, world!');
}

main();""",
        "c_cpp": """#include <stdio.h>

int main() {
    printf("Hello, world!\\n");
    return 0;
}""",
        "go": """package main

import "fmt"

func main() {
    fmt.Println("Hello, world!")
}""",
        "rust": """fn main() {
    println!("Hello, world!");
}""",
        "html": """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Document</title>
</head>
<body>

</body>
</html>""",
        "markdown": """# Title

## Section

- List item""",
        "java": """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, world!");
    }
}""",
        "ruby": """puts "Hello, world!""",
        "php": """<?php

echo "Hello, world!";
""",
        "typescript": """function main(): void {
    console.log('Hello, world!');
}

main();""",
        "shell": """#!/bin/bash

echo "Hello, world!"
""",
        "css": """body {
    font-family: sans-serif;
}
""",
        "lua": """function main()
    print("Hello, world!")
end

main()""",
        "perl": """#!/usr/bin/perl
use strict;
use warnings;

print "Hello, world!\\n";""",
        "kotlin": """fun main() {
    println("Hello, World!")
}""",
        "swift": """import Swift

print("Hello, world!")""",
        "dart": """void main() {
  print('Hello, World!');
}""",
        "elixir": """defmodule Hello do
  def world do
    IO.puts "Hello, world!"
  end
end

Hello.world()"""
    },
    "colors": {
        "header_text": "BLACK",
        "header_bg": "WHITE",
        "error_text": "WHITE",
        "error_bg": "RED",
        "linenum_text": "CYAN",
        "linenum_bg": "DEFAULT",
        "selection_text": "BLACK",
        "selection_bg": "CYAN",
        # --- Syntax Colors Defaults ---
        "keyword": "YELLOW",
        "string": "GREEN",
        "comment": "MAGENTA",
        "number": "BLUE",
        "zenkaku_bg": "RED",
        # --- UI Colors ---
        "ui_border": "WHITE",
        "explorer_dir": "WHITE",
        "explorer_file": "WHITE",
        "terminal_bg": "DEFAULT",
        "tab_active_text": "WHITE",
        "tab_active_bg": "BLUE",
        "tab_inactive_text": "WHITE",
        "tab_inactive_bg": "DEFAULT",
        # --- Git Diff Colors ---
        "diff_add": "GREEN",
        "diff_remove": "RED",
        # --- Breadcrumb Colors ---
        "breadcrumb_text": "BLACK",
        "breadcrumb_bg": "WHITE",
        # --- Search UI Colors ---
        "search_bg": "WHITE",
        "search_text": "BLACK",
        "search_highlight_bg": "YELLOW",
        "active_search_highlight_bg": "MAGENTA"
    }
}

SETTING_ASSETS = {
    "Color: Default (Coffee)": {
        "colors": {
            "header_text": "BLACK", "header_bg": "WHITE",
            "linenum_text": "CYAN", "selection_bg": "CYAN"
        }
    },
    "Color: Midnight Blue": {
        "colors": {
            "header_text": "WHITE", "header_bg": "BLUE",
            "linenum_text": "BLUE", "selection_bg": "BLUE",
            "keyword": "CYAN", "string": "YELLOW"
        }
    },
    "Color: Emerald Forest": {
        "colors": {
            "header_text": "WHITE", "header_bg": "GREEN",
            "linenum_text": "GREEN", "selection_bg": "GREEN",
            "keyword": "YELLOW", "string": "CYAN"
        }
    },
    "Color: Sakura Pink": {
        "colors": {
            "header_text": "BLACK", "header_bg": "MAGENTA",
            "linenum_text": "MAGENTA", "selection_bg": "MAGENTA",
            "keyword": "RED", "string": "WHITE"
        }
    },
    "Color: High Contrast": {
        "colors": {
            "header_text": "BLACK", "header_bg": "WHITE",
            "linenum_text": "WHITE", "linenum_bg": "BLACK",
            "selection_text": "BLACK", "selection_bg": "WHITE",
            "keyword": "WHITE", "string": "WHITE", "comment": "WHITE"
        }
    },
    "Style: Vim-like": {
        "vim_mode": True,
        "show_relative_linenum": True
    },
    "Style: VSCode-like": {
        "tab_width": 2,
        "show_breadcrumb": True,
        "explorer_width": 30
    }
}

# 色名とcurses定数のマッピング
COLOR_MAP = {
    "BLACK": curses.COLOR_BLACK,
    "BLUE": curses.COLOR_BLUE,
    "CYAN": curses.COLOR_CYAN,
    "GREEN": curses.COLOR_GREEN,
    "MAGENTA": curses.COLOR_MAGENTA,
    "RED": curses.COLOR_RED,
    "WHITE": curses.COLOR_WHITE,
    "YELLOW": curses.COLOR_YELLOW,
    "DEFAULT": -1
}

# --- デフォルトのキーバインディング定義 ---
DEFAULT_KEYBINDINGS = {
    "close_tab": {"key": "^X", "label": "CloseTab"},
    "new_start": {"key": "^S", "label": "New/Start"},
    "next_tab": {"key": "^L", "label": "NextTab"},
    "save": {"key": "^O", "label": "Save"},
    "cut": {"key": "^K", "label": "Cut"},
    "paste": {"key": "^U", "label": "Paste"},
    "search": {"key": "^W", "label": "Search"},
    "undo": {"key": "^Z", "label": "Undo"},
    "redo": {"key": "^R", "label": "Redo"},
    "copy": {"key": "^C", "label": "Copy"},
    "build": {"key": "^B", "label": "Build"},
    "mark": {"key": "^6", "label": "Mark"},
    "select_all": {"key": "^A", "label": "All"},
    "goto": {"key": "^G", "label": "Goto"},
    "delete_line": {"key": "^Y", "label": "DelLine"},
    "comment": {"key": "^/", "label": "Comment"},
    "explorer": {"key": "^F", "label": "Explorer"},
    "terminal": {"key": "^N", "label": "Terminal"},
    "line_end": {"key": "^E", "label": "LineEnd"},
    "command": {"key": "^P", "label": "Command"},
    "diff": {"key": "^D", "label": "Diff"},
    "template": {"key": "^T", "label": "Template"},
    "relative_linenum": {"key": "^V", "label": "RelNum"},
}

# --- File Icons for Explorer ---
EMOJI_ICONS = {
    # Programming languages
    ".py": "🐍", ".pyc": "🐍",
    ".js": "📜", ".mjs": "📜", ".cjs": "📜",
    ".ts": "📜", ".tsx": "📜",
    ".java": "☕", ".class": "☕",
    ".c": "🇨", ".h": "🇭", ".cpp": "🇨", ".hpp": "🇭",
    ".go": "🐹",
    ".rs": "🦀",
    ".rb": "💎",
    ".php": "🐘",
    ".sh": "💲", ".bash": "💲",
    ".lua": "🌙",
    ".pl": "🐪", ".pm": "🐪",
    ".kt": "🇰", ".kts": "🇰",
    ".swift": "🐦",
    ".dart": "🎯",
    ".ex": "💧", ".exs": "💧",
    # Web
    ".html": "🌐", ".htm": "🌐",
    ".css": "🎨",
    ".json": "📦",
    # Markup & Text
    ".md": "📝", ".markdown": "📝",
    ".txt": "📄",
    # Config
    ".toml": "⚙️", ".yaml": "⚙️", ".yml": "⚙️",
    ".ini": "⚙️", ".conf": "⚙️", ".cfg": "⚙️",
    # Git
    ".git": "🌿", ".gitignore": "🌿",
    # Data & Docs
    ".csv": "📊",
    ".pdf": "📕",
    # Compressed
    ".zip": "📦", ".tar": "📦", ".gz": "📦", ".rar": "📦",
    # Images
    ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🖼️", ".svg": "🖼️",
}

NERD_FONT_ICONS = {
    # Default icons
    "file": "",
    "dir": "",
    "up": "",
    # Programming languages
    ".py": "", ".pyc": "",
    ".js": "", ".mjs": "", ".cjs": "",
    ".ts": "", ".tsx": "",
    ".java": "", ".class": "",
    ".c": "", ".h": "", ".cpp": "", ".hpp": "",
    ".go": "",
    ".rs": "",
    ".rb": "",
    ".php": "",
    ".sh": "", ".bash": "",
    ".lua": "",
    ".pl": "", ".pm": "",
    ".kt": "", ".kts": "",
    ".swift": "",
    ".dart": "",
    ".ex": "", ".exs": "",
    # Web
    ".html": "", ".htm": "",
    ".css": "",
    ".json": "",
    # Markup & Text
    ".md": "", ".markdown": "",
    ".txt": "",
    # Config
    ".toml": "", ".yaml": "", ".yml": "",
    ".ini": "", ".conf": "", ".cfg": "",
    # Git
    ".git": "", ".gitignore": "",
    # Data & Docs
    ".csv": "",
    ".pdf": "",
    # Compressed
    ".zip": "", ".tar": "", ".gz": "", ".rar": "",
    # Images
    ".png": "", ".jpg": "", ".jpeg": "", ".gif": "", ".svg": "",
}


# --- デフォルトのシンタックスハイライト定義 ---
DEFAULT_SYNTAX_RULES = {
    "python": {
        "extensions": [".py", ".pyw"],
        "symbol_pattern": r"^\s*(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        "keywords": r"\b(and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|not|or|pass|raise|return|try|while|with|yield|None|True|False|self)\b",
        "comments": r"#.*",
        "line_comment": "#",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "javascript": {
        "extensions": [".js", ".json"],
        "symbol_pattern": r"^\s*(?:function|class|const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?:=|\(|{)",
        "keywords": r"\b(function|return|var|let|const|if|else|for|while|break|switch|case|default|import|export|true|false|null)\b",
        "comments": r"//.*",
        "line_comment": "//",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "c_cpp": {
        "extensions": [".c", ".cpp", ".h", ".hpp", ".cc"],
        "symbol_pattern": r"^\s*(?:[\w\s\*&]+?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{?",
        "keywords": r"\b(int|float|double|char|void|if|else|for|while|return|struct|class|public|private|protected|include)\b",
        "comments": r"//.*",
        "line_comment": "//",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "go": {
        "extensions": [".go"],
        "symbol_pattern": r"^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
        "keywords": r"\b(break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|true|false|nil|append|cap|close|complex|copy|delete|imag|len|make|new|panic|print|println|real|recover|bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr)\b",
        "comments": r"//.*",
        "line_comment": "//",
        "strings": r"(['\"`])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "rust": {
        "extensions": [".rs"],
        "symbol_pattern": r"^\s*(?:fn|struct|enum|trait|impl)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        "keywords": r"\b(as|break|const|continue|crate|else|enum|extern|false|fn|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|struct|super|trait|true|type|unsafe|use|where|while)\b",
        "comments": r"//.*",
        "line_comment": "//",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "html": {
        "extensions": [".html", ".htm"],
        "keywords": r"\b(html|head|body|title|meta|link|script|style|div|span|p|h[1-6]|a|img|ul|ol|li|table|tr|td|th|form|input|button|label|select|option|textarea|br|hr|class|id|src|href|alt|type|value|name|width|height)\b",
        "comments": r"",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "markdown": {
        "extensions": [".md", ".markdown"],
        "keywords": r"(^#+\s+.*)|(^\s*[\-\*+]\s+)",
        "comments": r"^>.*",
        "strings": r"(`[^`]+`|\*\*.*?\*\*)",
        "numbers": r"\[.*?\]"
    },
    "diff": {
        "extensions": [],
        "language_name": "diff"
    },
    "java": {
        "extensions": [".java"],
        "symbol_pattern": r"^\s*(?:public|private|protected)?\s*(?:static\s+)?\w+\s+([a-zA-Z_]\w*)\s*\(",
        "keywords": r"\b(abstract|continue|for|new|switch|assert|default|goto|package|synchronized|boolean|do|if|private|this|break|double|implements|protected|throw|byte|else|import|public|throws|case|enum|instanceof|return|transient|catch|extends|int|short|try|char|final|interface|static|void|class|finally|long|strictfp|volatile|const|float|native|super|while|true|false|null)\b",
        "comments": r"//.*|/\*[\s\S]*?\*/",
        "line_comment": "//",
        "strings": r"(\".*?\")",
        "numbers": r"\b\d+\b"
    },
    "ruby": {
        "extensions": [".rb"],
        "symbol_pattern": r"^\s*(?:def|class|module)\s+([a-zA-Z_]\w*)",
        "keywords": r"\b(BEGIN|END|alias|and|begin|break|case|class|def|defined|do|else|elsif|end|ensure|false|for|if|in|module|next|nil|not|or|redo|rescue|retry|return|self|super|then|true|undef|unless|until|when|while|yield|__FILE__|__LINE__)\b",
        "comments": r"#.*",
        "line_comment": "#",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "php": {
        "extensions": [".php"],
        "symbol_pattern": r"^\s*(?:function|class|trait|interface)\s+([a-zA-Z_]\w*)",
        "keywords": r"\b(abstract|and|array|as|break|case|catch|class|clone|const|continue|declare|default|die|do|echo|else|elseif|empty|enddeclare|endfor|endforeach|endif|endswitch|endwhile|eval|exit|extends|final|for|foreach|function|global|if|implements|include|include_once|instanceof|interface|isset|list|namespace|new|or|print|private|protected|public|require|require_once|return|static|switch|throw|try|unset|use|var|while|xor|__FILE__|__LINE__|__DIR__|__FUNCTION__|__CLASS__|__METHOD__|__NAMESPACE__)\b",
        "comments": r"//.*|#.*|/\*[\s\S]*?\*/",
        "line_comment": "//",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "symbol_pattern": r"^\s*(?:export\s+)?(?:abstract\s+)?(?:async\s+)?(?:function|class|interface|enum|type)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)",
        "keywords": r"\b(break|case|catch|class|const|continue|debugger|default|delete|do|else|enum|export|extends|false|finally|for|function|if|import|in|instanceof|new|null|return|super|switch|this|throw|true|try|typeof|var|void|while|with|as|implements|interface|let|package|private|protected|public|static|yield|any|boolean|constructor|declare|get|module|require|number|set|string|symbol|type|from|of)\b",
        "comments": r"//.*|/\*[\s\S]*?\*/",
        "line_comment": "//",
        "strings": r"(['\"`])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "shell": {
        "extensions": [".sh", ".bash"],
        "keywords": r"\b(if|then|else|elif|fi|case|esac|for|select|while|until|do|done|in|function|time|coproc|true|false|echo|read|unset|export|declare|let|eval|exec|set|shift|trap|exit|return|break|continue)\b",
        "comments": r"#.*",
        "line_comment": "#",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "css": {
        "extensions": [".css"],
        "keywords": r"([a-zA-Z-]+)\s*:",
        "comments": r"/\*[\s\S]*?\*/",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"#[0-9a-fA-F]{3,6}|\b\d+(:?px|em|%|pt|rem)\b"
    },
    "lua": {
        "extensions": [".lua"],
        "keywords": r"\b(and|break|do|else|elseif|end|false|for|function|if|in|local|nil|not|or|repeat|return|then|true|until|while)\b",
        "comments": r"--.*",
        "line_comment": "--",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "perl": {
        "extensions": [".pl", ".pm"],
        "keywords": r"\b(my|our|local|sub|if|else|elsif|for|foreach|while|until|use|require|package|print|say)\b",
        "comments": r"#.*",
        "line_comment": "#",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "kotlin": {
        "extensions": [".kt", ".kts"],
        "keywords": r"\b(fun|val|var|if|else|when|for|while|return|class|interface|package|import|true|false|null|object|is|in)\b",
        "comments": r"//.*|/\*[\s\S]*?\*/",
        "line_comment": "//",
        "strings": r"(\".*?\")",
        "numbers": r"\b\d+\b"
    },
    "swift": {
        "extensions": [".swift"],
        "keywords": r"\b(let|var|func|if|else|for|in|while|switch|case|return|class|struct|enum|protocol|import|true|false|nil|public|private|internal|fileprivate|open)\b",
        "comments": r"//.*|/\*[\s\S]*?\*/",
        "line_comment": "//",
        "strings": r"(\".*?\")",
        "numbers": r"\b\d+\b"
    },
    "dart": {
        "extensions": [".dart"],
        "keywords": r"\b(var|final|const|if|else|for|in|while|do|switch|case|break|continue|return|void|import|as|show|hide|true|false|null|class|extends|with|implements|enum|mixin)\b",
        "comments": r"//.*|/\*[\s\S]*?\*/",
        "line_comment": "//",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "elixir": {
        "extensions": [".ex", ".exs"],
        "keywords": r"\b(def|defmodule|defp|if|else|case|cond|fn|end|true|false|nil|do|require|alias|import|use|with)\b|:\w+",
        "comments": r"#.*",
        "line_comment": "#",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "caffeine": {
        "extensions": [".caffeine"],
        "keywords": r"\b(MOVE|INSERT|WAIT|COMMAND|TYPE)\b",
        "comments": r"#.*",
        "line_comment": "#",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    }
}

DEFAULT_BUILD_COMMANDS = {
    ".py": "python3 \"{filename}\"",
    ".js": "node \"{filename}\"",
    ".go": "go run \"{filename}\"",
    ".c": "gcc \"{filename}\" -o \"{base}\" && \"./{base}\"",
    ".cpp": "g++ \"{filename}\" -o \"{base}\" && \"./{base}\"",
    ".cc": "g++ \"{filename}\" -o \"{base}\" && \"./{base}\"",
    ".sh": "bash \"{filename}\"",
    ".rs": "rustc \"{filename}\" && \"./{base}\"",
    ".java": "javac \"{filename}\" && java \"{base}\"",
    ".rb": "ruby \"{filename}\"",
    ".php": "php -S localhost:8000 \"{filename}\"",
    ".ts": "ts-node \"{filename}\"",
    ".tsx": "ts-node \"{filename}\"",
    ".bash": "bash \"{filename}\"",
    ".lua": "lua \"{filename}\"",
    ".pl": "perl \"{filename}\"",
    ".kt": "kotlinc \"{filename}\" -include-runtime -d \"{base}\".jar && java -jar \"{base}\".jar",
    ".kts": "kotlin \"{filename}\"",
    ".swift": "swift \"{filename}\"",
    ".dart": "dart run \"{filename}\"",
    ".ex": "elixir \"{filename}\"",
    ".exs": "elixir \"{filename}\""
}


def get_config_dir():
    """設定ディレクトリのパスを取得"""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".caffee_setting")

def load_config():
    """ユーザー設定ファイル(setting.json)を読み込む"""
    setting_dir = get_config_dir()
    setting_file = os.path.join(setting_dir, "setting.json")
    user_config = {}
    load_error = None

    try:
        os.makedirs(setting_dir, exist_ok=True)
    except OSError as e:
        load_error = f"Config dir error: {e}"

    if os.path.exists(setting_file):
        try:
            with open(setting_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            load_error = f"Config load error: {e}"
            
    return user_config, load_error

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def strip_ansi(text):
    return ANSI_ESCAPE.sub('', text)

def get_char_width(char):
    """文字の表示幅を返す（半角=1, 全角=2）"""
    return 2 if unicodedata.east_asian_width(char) in ('F', 'W', 'A') else 1

def get_string_display_width(s):
    """文字列の合計表示幅を計算する"""
    return sum(get_char_width(c) for c in s)

def truncate_to_width(s, max_width):
    """文字列を指定された表示幅に切り詰める"""
    if get_string_display_width(s) <= max_width:
        return s
    
    # 省略文字「…」の幅を考慮
    max_width -= 1 
    if max_width < 0: return "…"[:max_width+1]

    current_width = 0
    end_pos = 0
    for char in s:
        char_w = get_char_width(char)
        if current_width + char_w > max_width:
            break
        current_width += char_w
        end_pos += 1
    return s[:end_pos] + "…"

class Buffer:
    """エディタのテキスト内容を保持するクラス"""
    def __init__(self, lines=None):
        self.lines = lines if lines else [""]
    
    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]
    
    def get_content(self):
        return self.lines[:]
    
    def set_content(self, lines):
        self.lines = lines
    
    def clone(self):
        return Buffer([line for line in self.lines])

class MacroManager:
    """CAFFEINE マクロ言語の実行を管理するクラス"""
    def __init__(self, editor):
        self.editor = editor

    def run_file(self, filename):
        """指定された .caffeine ファイルを読み込んで実行する"""
        if not filename:
            self.editor.set_status("Usage: macro <filename>", timeout=3)
            return

        # Try adding extension if not present
        if not os.path.exists(filename) and not filename.endswith(".caffeine"):
            if os.path.exists(filename + ".caffeine"):
                filename += ".caffeine"

        if not os.path.exists(filename):
            # Try ~/.caffee_setting/macros/ if not found
            macro_dir = os.path.join(get_config_dir(), "macros")
            alt_path = os.path.join(macro_dir, filename)
            if not alt_path.endswith(".caffeine"):
                alt_path += ".caffeine"
            
            if os.path.exists(alt_path):
                filename = alt_path
            else:
                self.editor.set_status(f"Macro file not found: {filename}", timeout=4)
                return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.editor.set_status(f"Running macro: {os.path.basename(filename)}...")
            self.editor.draw_ui()
            self.editor.stdscr.refresh()

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 行の先頭が : ならエディタコマンドとして実行
                if line.startswith(':'):
                    self.editor.execute_command(line[1:])
                    continue

                parts = line.split(maxsplit=1)
                cmd = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd == 'MOVE':
                    try:
                        coords = args.split()
                        y = int(coords[0])
                        x = int(coords[1])
                        self.editor.move_cursor_to(y, x)
                    except (ValueError, IndexError):
                        pass
                elif cmd == 'INSERT':
                    text = args
                    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                        text = text[1:-1]
                    # Escape sequences handling
                    text = text.encode('utf-8').decode('unicode_escape')
                    self.editor.insert_text(text)
                elif cmd == 'WAIT':
                    try:
                        ms = int(args)
                        curses.napms(ms)
                        # 待機中に画面を更新して進捗を見せる
                        self.editor.draw_ui()
                        self.editor.draw_content()
                        self.editor.stdscr.refresh()
                    except ValueError:
                        pass
                elif cmd == 'COMMAND':
                    cmd_to_exec = args
                    if (cmd_to_exec.startswith('"') and cmd_to_exec.endswith('"')) or (cmd_to_exec.startswith("'") and cmd_to_exec.endswith("'")):
                        cmd_to_exec = cmd_to_exec[1:-1]
                    self.editor.execute_command(cmd_to_exec)
                elif cmd == 'TYPE':
                    # 1文字ずつタイプする（演出用）
                    text = args
                    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                        text = text[1:-1]
                    text = text.encode('utf-8').decode('unicode_escape')
                    for char in text:
                        self.editor.insert_text(char)
                        self.editor.draw_ui()
                        self.editor.draw_content()
                        self.editor.stdscr.refresh()
                        curses.napms(50)
                
            self.editor.set_status(f"Macro finished: {os.path.basename(filename)}", timeout=3)
        except Exception as e:
            self.editor.set_status(f"Macro Error: {e}", timeout=5)


class PluginManager:
    """プラグインの有効・無効を管理するクラス"""
    def __init__(self, config_dir):
        self.plugin_dir = os.path.join(config_dir, "plugins")
        self.disabled_dir = os.path.join(self.plugin_dir, "disabled")
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        
        # ディレクトリ作成
        if not os.path.exists(self.disabled_dir):
            try:
                os.makedirs(self.disabled_dir, exist_ok=True)
            except OSError: pass
        
        self.refresh_list()

    def refresh_list(self):
        self.items = []
        
        # Active plugins
        if os.path.exists(self.plugin_dir):
            for f in glob.glob(os.path.join(self.plugin_dir, "*.py")):
                if os.path.basename(f).startswith("_"): continue
                self.items.append({
                    "name": os.path.basename(f),
                    "path": f,
                    "enabled": True
                })

        # Disabled plugins
        if os.path.exists(self.disabled_dir):
            for f in glob.glob(os.path.join(self.disabled_dir, "*.py")):
                self.items.append({
                    "name": os.path.basename(f),
                    "path": f,
                    "enabled": False
                })
        
        self.items.sort(key=lambda x: x["name"])
        # インデックス範囲の修正
        if self.selected_index >= len(self.items) and len(self.items) > 0:
            self.selected_index = len(self.items) - 1

    def navigate(self, delta):
        if not self.items: return
        self.selected_index += delta
        if self.selected_index < 0: self.selected_index = 0
        if self.selected_index >= len(self.items): self.selected_index = len(self.items) - 1

    def toggle_current(self):
        if not self.items: return None
        
        item = self.items[self.selected_index]
        src = item["path"]
        
        try:
            if item["enabled"]:
                # Disable it (move to disabled_dir)
                dst = os.path.join(self.disabled_dir, item["name"])
                shutil.move(src, dst)
            else:
                # Enable it (move to plugin_dir)
                dst = os.path.join(self.plugin_dir, item["name"])
                shutil.move(src, dst)
            
            self.refresh_list()
            return "Restart editor to apply changes."
        except OSError as e:
            return f"Error toggling plugin: {e}"

    def draw(self, stdscr, height, width, colors):
        stdscr.erase()
        
        # Header
        header = " Plugin Manager "
        try:
            stdscr.addstr(0, 0, header.ljust(width), colors["header"] | curses.A_BOLD)
            stdscr.addstr(1, 0, " [Space/Enter] Toggle  [Esc] Back ", colors["ui_border"])
            stdscr.addstr(2, 0, "─" * width, colors["ui_border"])
        except curses.error: pass
        
        # List
        list_h = height - 4
        list_start_y = 3
        
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + list_h:
            self.scroll_offset = self.selected_index - list_h + 1

        for i in range(list_h):
            idx = self.scroll_offset + i
            if idx >= len(self.items): break
            
            item = self.items[idx]
            y = list_start_y + i
            
            marker = "[x]" if item["enabled"] else "[ ]"
            prefix = "> " if idx == self.selected_index else "  "
            display_str = f"{prefix}{marker} {item['name']}"
            
            attr = colors["header"] | curses.A_REVERSE if idx == self.selected_index else colors["header"]
            
            try:
                # 名前部分の色分け
                stdscr.addstr(y, 1, display_str.ljust(width-2), attr)
            except curses.error: pass


class KeybindingSettingsManager:
    """フッターに表示するキーバインディングを対話的に編集するクラス"""
    def __init__(self, editor):
        self.editor = editor
        self.config = editor.config
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.refresh_list()

    def refresh_list(self):
        self.items = []
        displayed = self.config.get("displayed_keybindings", [])
        
        # DEFAULT_KEYBINDINGS のキーの順序を保持するために sorted を使う
        for key_id in sorted(DEFAULT_KEYBINDINGS.keys()):
            binding = DEFAULT_KEYBINDINGS[key_id]
            self.items.append({
                "id": key_id,
                "key": binding["key"],
                "label": binding["label"],
                "enabled": key_id in displayed
            })

    def navigate(self, delta):
        if not self.items: return
        self.selected_index += delta
        if self.selected_index < 0: self.selected_index = 0
        if self.selected_index >= len(self.items): self.selected_index = len(self.items) - 1

    def toggle_current(self):
        if not self.items: return None
        
        item = self.items[self.selected_index]
        item["enabled"] = not item["enabled"]
        
        # Update the config list
        displayed_list = self.config.get("displayed_keybindings", [])
        if item["enabled"]:
            if item["id"] not in displayed_list:
                displayed_list.append(item["id"])
        else:
            if item["id"] in displayed_list:
                displayed_list.remove(item["id"])
        
        # Ensure the list in config is updated
        self.config["displayed_keybindings"] = displayed_list
        
        return "Changed. Press ^O in Settings to save."

    def draw(self, stdscr, height, width, colors):
        stdscr.erase()
        
        # Header
        header = " Keybinding Display Settings "
        try:
            stdscr.addstr(0, 0, header.ljust(width), colors["header"] | curses.A_BOLD)
            stdscr.addstr(1, 0, " [Space/Enter] Toggle  [Esc] Back to Settings ".ljust(width), colors["ui_border"])
            stdscr.addstr(2, 0, "─" * width, colors["ui_border"])
        except curses.error: pass
        
        # List
        list_h = height - 4
        list_start_y = 3
        
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + list_h:
            self.scroll_offset = self.selected_index - list_h + 1

        for i in range(list_h):
            idx = self.scroll_offset + i
            if idx >= len(self.items): break
            
            item = self.items[idx]
            y = list_start_y + i
            
            marker = "[x]" if item["enabled"] else "[ ]"
            prefix = "> " if idx == self.selected_index else "  "
            display_str = f"{prefix}{marker} {item['key']} {item['label']}"
            
            attr = colors["header"] | curses.A_REVERSE if idx == self.selected_index else colors["header"]
            
            try:
                stdscr.addstr(y, 1, display_str.ljust(width-2), attr)
            except curses.error: pass


class SettingsManager:
    """設定を対話的に編集するクラス"""
    def __init__(self, config):
        self.config = config
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.edit_mode = False
        self.edit_buffer = ""
        self.refresh_list()

    def refresh_list(self):
        self.items = []
        # settings.jsonに保存したい項目を列挙
        for key, value in self.config.items():
            if key in ["colors", "displayed_keybindings"]: continue
            self.items.append({"key": key, "value": value, "type": "setting"})
        
        # カスタム項目
        self.items.append({"key": "Keybindings...", "value": "", "type": "action"})
        
        self.items.sort(key=lambda x: x["key"])

    def navigate(self, delta):
        if self.edit_mode: return
        self.selected_index = max(0, min(self.selected_index + delta, len(self.items) - 1))

    def get_current_item(self):
        if not self.items: return None
        return self.items[self.selected_index]

    def toggle_bool(self):
        item = self.get_current_item()
        if item and item["type"] == "setting" and isinstance(item["value"], bool):
            item["value"] = not item["value"]
            self.config[item["key"]] = item["value"]
            return "Value changed. Press ^O to save."
        return None

    def start_edit(self, editor):
        item = self.get_current_item()
        if not item: return

        if item["type"] == "action" and item["key"] == "Keybindings...":
            editor.active_pane = 'keybinding_settings'
            return

        if item["type"] == "setting" and isinstance(item["value"], (int, str)):
            self.edit_mode = True
            self.edit_buffer = str(item["value"])

    def handle_edit_input(self, char_code):
        if char_code in (KEY_ENTER, KEY_RETURN):
            self.apply_edit()
        elif char_code in (curses.KEY_BACKSPACE, KEY_BACKSPACE, KEY_BACKSPACE2):
            self.edit_buffer = self.edit_buffer[:-1]
        elif char_code == KEY_ESC:
            self.edit_mode = False
        # Check if it's a printable character
        elif 32 <= char_code <= 126:
            self.edit_buffer += chr(char_code)

    def apply_edit(self):
        item = self.get_current_item()
        if not item or item["type"] != "setting":
            self.edit_mode = False
            return

        try:
            new_value = None
            if isinstance(item["value"], int):
                new_value = int(self.edit_buffer)
            elif isinstance(item["value"], str):
                new_value = self.edit_buffer

            if new_value is not None:
                item["value"] = new_value
                self.config[item["key"]] = new_value
                self.edit_mode = False
                return "Value changed. Press ^O to save."
        except (ValueError, TypeError):
            return "Invalid value for type " + type(item["value"]).__name__
        self.edit_mode = False
        return None

    def save_settings(self):
        setting_dir = get_config_dir()
        setting_file = os.path.join(setting_dir, "setting.json")

        # DEFAULT_CONFIGと比較し、変更された項目のみ保存
        user_config = {}
        for key, value in self.config.items():
            if key in DEFAULT_CONFIG and DEFAULT_CONFIG[key] != value:
                user_config[key] = value
            elif key not in DEFAULT_CONFIG:
                 user_config[key] = value

        try:
            with open(setting_file, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, indent=4)
            return "Settings saved to setting.json"
        except OSError as e:
            return f"Error saving settings: {e}"

    def draw(self, stdscr, height, width, colors):
        stdscr.erase()
        header = " Settings Manager "
        try:
            stdscr.addstr(0, 0, header.ljust(width), colors["header"] | curses.A_BOLD)
            stdscr.addstr(1, 0, " [Enter] Edit  [Space] Toggle Bool  [^O] Save  [Esc] Back ".ljust(width), colors["ui_border"])
            stdscr.addstr(2, 0, "─" * width, colors["ui_border"])
        except curses.error: pass

        list_h = height - 4
        list_start_y = 3

        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + list_h:
            self.scroll_offset = self.selected_index - list_h + 1

        for i in range(list_h):
            idx = self.scroll_offset + i
            if idx >= len(self.items): break

            item = self.items[idx]
            y = list_start_y + i

            prefix = "> " if idx == self.selected_index else "  "
            attr = colors["header"] | curses.A_REVERSE if idx == self.selected_index else colors["header"]

            key_str = f"{item['key']}: "
            val_str = str(item['value'])

            if idx == self.selected_index and self.edit_mode:
                val_str = self.edit_buffer + "_"

            display_str = f"{prefix}{key_str}{val_str}".ljust(width)

            try:
                stdscr.addstr(y, 0, display_str, attr)
            except curses.error: pass


def human_readable_size(size, decimal_places=1):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f}{unit}"


class FileExplorer:
    def __init__(self, editor, start_path="."):
        self.editor = editor
        self.current_path = os.path.abspath(start_path)
        self.files = []
        self.selected_index = 0
        self.scroll_offset = 0

        # --- 機能追加 ---
        self.sort_by = "name" # "name", "mtime", "size"
        self.sort_order = "asc" # "asc", "desc"
        self.show_hidden = False
        self.search_query = ""
        self.show_details = editor.config.get("explorer_show_details", True)
        # -----------------

        self.refresh_list()

    def cycle_sort_mode(self):
        """ソート項目を切り替える"""
        modes = ["name", "mtime", "size"]
        try:
            current_index = modes.index(self.sort_by)
            self.sort_by = modes[(current_index + 1) % len(modes)]
        except ValueError:
            self.sort_by = "name"
        self.refresh_list()
        return f"Sorted by {self.sort_by}"

    def toggle_sort_order(self):
        """ソート順を昇順/降順で切り替える"""
        self.sort_order = "desc" if self.sort_order == "asc" else "asc"
        self.refresh_list()
        return f"Order: {self.sort_order}"

    def toggle_hidden(self):
        """隠しファイルの表示を切り替える"""
        self.show_hidden = not self.show_hidden
        self.refresh_list()
        return f"Show hidden: {self.show_hidden}"

    def set_search_query(self, query):
        """検索クエリを設定する"""
        self.search_query = query if query is not None else ""
        self.refresh_list()

    def refresh_list(self):
        try:
            items = os.listdir(self.current_path)
            
            # --- フィルタリング ---
            if not self.show_hidden:
                items = [f for f in items if not f.startswith('.')]
            if self.search_query:
                try:
                    # 簡易的なワイルドカードをサポート
                    query_re = re.compile(self.search_query.replace('*', '.*'), re.IGNORECASE)
                    items = [f for f in items if query_re.search(f)]
                except re.error:
                    # 無効な正規表現の場合は検索しない
                    pass

            # --- ファイル情報取得 ---
            file_details = []
            for item in items:
                try:
                    path = os.path.join(self.current_path, item)
                    stat = os.stat(path)
                    is_dir = os.path.isdir(path)
                    file_details.append({
                        "name": item,
                        "is_dir": is_dir,
                        "mtime": stat.st_mtime,
                        "size": stat.st_size
                    })
                except OSError:
                    continue # アクセス権がないファイルなどはスキップ

            # --- ソート ---
            is_reverse = (self.sort_order == "desc")

            # ソートキーを選択
            if self.sort_by == "name":
                sort_key_func = lambda f: f["name"].lower()
            elif self.sort_by == "mtime":
                sort_key_func = lambda f: f["mtime"]
            elif self.sort_by == "size":
                sort_key_func = lambda f: f["size"] if not f["is_dir"] else -1 # ディレクトリはサイズでソートされないように
            else:
                sort_key_func = lambda f: f["name"].lower()

            # (is_dir, sort_key)のタプルでソート。not f['is_dir'] はディレクトリでTrue
            sorted_items = sorted(file_details, key=lambda f: (not f['is_dir'], sort_key_func(f)), reverse=is_reverse)


            # self.filesの構造を詳細辞書に変更
            self.files = [{"name": "..", "is_dir": True, "mtime": 0, "size": 0}] + sorted_items

            if self.selected_index >= len(self.files):
                self.selected_index = max(0, len(self.files) - 1)

        except OSError:
            self.files = [{"name": "..", "is_dir": True, "mtime": 0, "size": 0}]

    def navigate(self, delta):
        self.selected_index += delta
        if self.selected_index < 0: self.selected_index = 0
        if self.selected_index >= len(self.files): self.selected_index = len(self.files) - 1

    def enter(self):
        if not self.files: return None
        
        selected_item = self.files[self.selected_index]
        selected_name = selected_item["name"]
        target = os.path.abspath(os.path.join(self.current_path, selected_name))
        
        if selected_item["is_dir"]:
            self.current_path = target
            self.search_query = "" # ディレクトリ移動時に検索をリセット
            self.refresh_list()
            return None
        else:
            return target

    def prompt_for_creation(self):
        """ファイルまたはディレクトリの作成をユーザーに促す"""
        name = self.editor._prompt_for_input("Create (file or dir/): ")
        if not name:
            return "Creation cancelled."

        target_path = os.path.join(self.current_path, name)

        try:
            if name.endswith('/'):
                os.makedirs(target_path)
                msg = f"Directory '{name}' created."
            else:
                with open(target_path, 'w') as f: pass
                msg = f"File '{name}' created."

            self.refresh_list()
            return msg
        except OSError as e:
            return f"Error: {e}"

    def delete_selected(self):
        """選択中のファイルまたはディレクトリを削除する"""
        if not self.files or self.selected_index == 0:
            return "Cannot delete parent directory."

        item = self.files[self.selected_index]
        name = item["name"]

        if not self.editor._prompt_for_confirmation(f"Delete '{name}'? (y/n)"):
             return "Deletion cancelled."

        target_path = os.path.join(self.current_path, name)
        try:
            if item["is_dir"]:
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)

            self.refresh_list()
            # Adjust selection to not go out of bounds
            if self.selected_index >= len(self.files):
                self.selected_index = len(self.files) - 1

            return f"Deleted '{name}'."
        except OSError as e:
            return f"Error: {e}"

    def rename_selected(self):
        """選択中のファイルまたはディレクトリの名前を変更する"""
        if not self.files or self.selected_index == 0:
            return "Cannot rename parent directory."

        item = self.files[self.selected_index]
        old_name = item["name"]

        new_name = self.editor._prompt_for_input(f"Rename '{old_name}' to: ", default_text=old_name)

        if not new_name or new_name == old_name:
            return "Rename cancelled."

        old_path = os.path.join(self.current_path, old_name)
        new_path = os.path.join(self.current_path, new_name)

        try:
            os.rename(old_path, new_path)
            self.refresh_list()
            # Try to re-select the renamed item
            for i, f in enumerate(self.files):
                if f["name"] == new_name:
                    self.selected_index = i
                    break
            return f"Renamed to '{new_name}'."
        except OSError as e:
            return f"Error: {e}"

    def draw(self, stdscr, y, x, h, w, colors):
        # --- 1. ヘッダー情報の準備 ---
        path_str = self.current_path
        if len(path_str) > w - 4:
            path_str = "..." + path_str[-(w - 7):]

        dirs_count = sum(1 for f in self.files if f["is_dir"] and f["name"] != "..")
        files_count = len(self.files) - dirs_count - 1 # -1 for ".."

        sort_indicator = f"{self.sort_by.capitalize()}({self.sort_order})"
        header_l = f" {path_str} [{dirs_count}D/{files_count}F] "
        header_r = f" {sort_indicator} "

        search_info = f" Query: {self.search_query}" if self.search_query else ""

        # --- 2. 描画開始 ---
        try:
            # 枠線
            stdscr.attron(colors["ui_border"])
            for i in range(h):
                stdscr.addstr(y + i, x, " " * w)
                stdscr.addch(y + i, x + w - 1, '│')
            stdscr.attroff(colors["ui_border"])

            # 上部ヘッダー
            stdscr.addstr(y, x, header_l.ljust(w), colors["header"] | curses.A_BOLD)
            stdscr.addstr(y, x + w - len(header_r) - 1, header_r, colors["header"] | curses.A_BOLD)

            # 検索情報と区切り線
            stdscr.addstr(y + 1, x, ("─" * (w-1))[:w-1], colors["ui_border"])
            if search_info:
                stdscr.addstr(y + 1, x + 2, search_info, colors["header"])

        except curses.error: pass

        # --- 3. ファイルリストの描画 ---
        list_h = h - 4 # Header, separator, footer
        list_start_y = y + 2
        
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + list_h:
            self.scroll_offset = self.selected_index - list_h + 1

        # --- Icon Theme Setup (Moved out of loop for performance) ---
        icon_theme = self.editor.config.get("explorer_icon_theme", "emoji")
        icons = self.editor.nerd_font_icons if icon_theme == "nerd_font" else self.editor.emoji_icons

        for i in range(list_h):
            idx = self.scroll_offset + i
            if idx >= len(self.files): break
            
            draw_y = list_start_y + i
            item = self.files[idx]
            f_name = item["name"]
            is_dir = item["is_dir"]
            
            attr = colors["dir"] if is_dir else colors["file"]
            if idx == self.selected_index:
                attr |= curses.A_REVERSE
            
            # --- Icon Logic ---
            icon = ""
            if f_name == "..":
                icon = icons.get("up", "⬆️")
            elif is_dir:
                icon = icons.get("dir", "📁")
            else:
                _, ext = os.path.splitext(f_name)
                # Check for full filename match first (e.g. '.git', '.gitignore')
                if f_name in icons:
                    icon = icons[f_name]
                elif ext and ext.lower() in icons:
                    icon = icons[ext.lower()]
            
            # Fallback to default file icon if no specific icon was found
            if not icon:
                icon = icons.get("file", "📄")


            # --- 各列の情報を準備 ---
            name_col = f" {icon} {f_name}"
            mtime_col = ""
            size_col = ""

            if f_name != "..":
                try:
                    mtime_dt = datetime.datetime.fromtimestamp(item["mtime"])
                    mtime_col = mtime_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    mtime_col = " " * 16

                if not is_dir:
                    size_col = human_readable_size(item["size"])

            # --- 画面幅に応じて表示を調整 ---
            available_w = w - 3 # margins
            display_str = ""

            if self.show_details:
                size_w = 8
                mtime_w = 17
                name_w = available_w

                # 詳細表示のスペースがあれば列を追加
                if available_w > mtime_w:
                    name_w -= mtime_w
                if available_w > mtime_w + size_w:
                    name_w -= size_w

                # 幅に合わせて名前を切り詰め
                truncated_name = truncate_to_width(name_col, name_w)
                
                # ljustがマルチバイト文字でうまく動かない場合があるので、手動でパディング
                padding_size = name_w - get_string_display_width(truncated_name)
                
                display_str = truncated_name + ' ' * padding_size

                if available_w > mtime_w:
                    display_str += mtime_col.rjust(mtime_w)
                if available_w > mtime_w + size_w:
                    display_str += size_col.rjust(size_w)
            else:
                # 詳細非表示の場合は名前のみ
                name_w = available_w
                truncated_name = truncate_to_width(name_col, name_w)
                padding_size = name_w - get_string_display_width(truncated_name)
                display_str = truncated_name + ' ' * padding_size

            try:
                # 画面の端を超えないように最終チェック
                if x + 1 + get_string_display_width(display_str) >= x + w:
                     display_str = truncate_to_width(display_str, w - 2)

                stdscr.addstr(draw_y, x + 1, display_str, attr)
            except curses.error: pass

        # --- 4. フッター (Help) ---
        try:
            footer_y = y + h - 1
            stdscr.addstr(footer_y, x, "─" * (w-1), colors["ui_border"])
            help_text = " [a/d/r]File [s/o]Sort [h]Hid [i]Info [/]Srch [Ent]Open "
            stdscr.addstr(footer_y, x + 2, help_text[:w-3], colors["header"])
        except curses.error: pass


class Terminal:
    def __init__(self, height):
        self.master_fd = None
        self.slave_fd = None
        self.pid = None
        self.lines = []
        self.height = height
        self.scroll_offset = 0
        self.buffer_limit = 1000
        
        if HAS_PTY:
            self.start_shell()
        else:
            self.lines = ["Terminal not supported on this OS (requires pty)."]

    def start_shell(self):
        env = os.environ.copy()
        env["TERM"] = "dumb"
        
        self.pid, self.master_fd = pty.fork()
        if self.pid == 0:
            shell = env.get("SHELL", "/bin/sh")
            try:
                os.execvpe(shell, [shell], env)
            except:
                sys.exit(1)
        else:
            os.set_blocking(self.master_fd, False)

    def write_input(self, data):
        if self.master_fd:
            try:
                os.write(self.master_fd, data.encode('utf-8'))
            except OSError:
                pass

    def read_output(self):
        if not self.master_fd: return False
        try:
            r, _, _ = select.select([self.master_fd], [], [], 0)
            if self.master_fd in r:
                data = os.read(self.master_fd, 1024)
                if not data: return False
                
                text = data.decode('utf-8', errors='replace')
                # iSH環境で発生するNULL文字(\x00)を除去
                text = text.replace('\0', '')
                text = strip_ansi(text)
                
                new_lines = text.replace('\r\n', '\n').split('\n')
                
                if self.lines:
                    self.lines[-1] += new_lines[0]
                else:
                    self.lines.append(new_lines[0])
                
                self.lines.extend(new_lines[1:])
                
                if len(self.lines) > self.buffer_limit:
                    self.lines = self.lines[-self.buffer_limit:]
                
                return True
        except OSError:
            pass
        return False

    def draw(self, stdscr, y, x, h, w, colors):
        try:
            stdscr.addstr(y, x, "─" * w, colors["ui_border"])
            title = " Terminal "
            stdscr.addstr(y, x + 2, title, colors["header"])
        except curses.error: pass
        
        content_h = h - 1
        content_y = y + 1
        
        total_lines = len(self.lines)
        end_idx = total_lines - self.scroll_offset
        start_idx = max(0, end_idx - content_h)
        
        display_lines = self.lines[start_idx:end_idx]
        
        for i, line in enumerate(display_lines):
            draw_line_y = content_y + i
            if draw_line_y >= y + h: break
            try:
                stdscr.addstr(draw_line_y, x, " " * w, colors["bg"])
                stdscr.addstr(draw_line_y, x, line[:w], colors["bg"])
            except curses.error: pass

class EditorTab:
    """単一の編集タブの状態を保持するクラス"""
    def __init__(self, buffer, filename, syntax_rules, mtime):
        self.buffer = buffer
        self.filename = filename
        self.cursor_y = 0
        self.cursor_x = 0
        self.scroll_offset = 0
        self.col_offset = 0
        self.desired_x = 0
        self.history = []
        self.history_index = -1
        self.modified = False
        self.mark_pos = None
        self.file_mtime = mtime
        self.current_syntax_rules = syntax_rules
        self.git_status = None # Can be 'M' (modified), 'A' (added/untracked), or None
        self.read_only = False

class Editor:
    def __init__(self, stdscr, filename=None, start_time=None):
        self.stdscr = stdscr
        self.config = DEFAULT_CONFIG.copy()
        self.syntax_rules = DEFAULT_SYNTAX_RULES.copy()
        self.build_commands = DEFAULT_BUILD_COMMANDS.copy()
        self.emoji_icons = EMOJI_ICONS.copy()
        self.nerd_font_icons = NERD_FONT_ICONS.copy()

        # プラグインをロードして、カスタム設定とシンタックスを登録
        self.load_plugins()

        # ユーザー設定をロード（プラグイン設定を上書き可能）
        user_config, config_error = load_config()
        if "colors" in user_config and isinstance(user_config["colors"], dict):
            self.config["colors"].update(user_config.pop("colors"))
        if "templates" in user_config and isinstance(user_config["templates"], dict):
            self.config["templates"].update(user_config.pop("templates"))
        self.config.update(user_config)

        self.vim_mode = self.config.get("vim_mode", False)
        self.vim_state = 'normal' if self.vim_mode else 'insert'
        self.vim_last_key = None
        self.vim_clipboard_type = 'char' # 'char' or 'line'

        self.git_branch = self._get_git_branch()

        # タブ管理の初期化
        self.tabs = []
        self.active_tab_idx = 0
        
        # 最初のタブを作成
        initial_lines, load_err = self.load_file(filename)
        mtime = None
        if filename and os.path.exists(filename):
            try: mtime = os.path.getmtime(filename)
            except OSError: pass
        
        rules = self.detect_syntax(filename)
        first_tab = EditorTab(Buffer(initial_lines), filename, rules, mtime)
        self._update_tab_git_status(first_tab)
        self.tabs.append(first_tab)
        
        # 最初のタブの履歴初期化
        self.save_history(init=True)

        # レイアウト管理
        self.menu_height = 1
        self.status_height = 1
        self.header_height = 1
        self.tab_bar_height = 1 # タブバー用
        
        # UIパネル状態管理
        self.show_explorer = self.config.get("show_explorer_default", False)
        self.show_terminal = self.config.get("show_terminal_default", False)
        self.explorer_width = self.config.get("explorer_width", 25)
        self.terminal_height = self.config.get("terminal_height", 10)
        
        self.active_pane = 'editor' 
        
        self.explorer = FileExplorer(self, ".")
        self.terminal = Terminal(self.terminal_height)
        self.plugin_manager = PluginManager(get_config_dir())
        self.macro_manager = MacroManager(self)
        self.settings_manager = SettingsManager(self.config)
        self.keybinding_settings_manager = KeybindingSettingsManager(self)
        
        self.status_message = ""
        self.status_expire_time = None
        self.clipboard = []
        
        # --- 予測変換の状態 ---
        self.suggestions = []
        self.suggestion_active = False
        self.selected_suggestion_idx = 0
        self.suggestion_word_start = None # (y, x) 補完中の単語の開始位置

        # --- 検索・置換の状態 ---
        self.search_mode = False
        self.search_query = ""
        self.replace_query = ""
        self.search_results = [] # list of (y, start_x, end_x)
        self.active_search_idx = -1
        self.search_input_focused = "search" # "search" or "replace"

        self.height, self.width = stdscr.getmaxyx()
        
        self.plugin_key_bindings = {}
        self.plugin_commands = {} 
        self.should_exit = False
        self.start_time = start_time
        
        self.commands = {
            'open': self._command_open,
            'o': self._command_open,
            'save': self._command_save,
            'w': self._command_save,
            'saveas': self._command_saveas,
            'copy': self._command_copy,
            'paste': self._command_paste,
            'close': self._command_close,
            'q': self._command_close,
            'quit': self._command_quit,
            'qa': self._command_quit,
            'new': self._command_new,
            'set': self._command_set,
            'diff': self.show_diff,
            'delcomm': self._command_delcomm,
            'deletecomments': self._command_delcomm,
            'undo': self._command_undo,
            'redo': self._command_redo,
            'goto': self._command_goto,
            'next': self.next_tab,
            'prev': self.prev_tab,
            'tabn': self.next_tab,
            'tabp': self.prev_tab,
            'find': self._command_find,
            'replace': self._command_replace,
            'expw': self._command_explorer_width,
            'termh': self._command_terminal_height,
            'explorer_width': self._command_explorer_width,
            'terminal_height': self._command_terminal_height,
            'template': self._command_template,
            'macro': self._command_macro,
        }

        self.init_colors()

        # Check for Nerd Font support after colors are initialized
        self._check_nerd_font_support()

        if config_error:
            self.set_status(config_error, timeout=5)
        elif load_err:
            self.set_status(load_err, timeout=5)

        # --- 起動画面制御 ---
        show_splash = self.config.get("show_splash", True)
        
        if show_splash:
            # 1. ファイルなし & スタートスクリーンモードONの場合 -> インタラクティブ待機
            if not filename and self.config.get("start_screen_mode", False):
                self.run_interactive_start_screen()
            # 2. それ以外 (ファイル指定あり or モードOFF) -> 通常のスプラッシュ (時間指定)
            else:
                duration = self.config.get("splash_duration", 2000)
                # ファイルなしでモードOFFなら待機、ファイルありなら一定時間
                if not filename:
                    self.show_start_screen(duration_ms=None, interactive=False)
                else:
                    self.show_start_screen(duration_ms=duration, interactive=False)

    # --- Properties to proxy current tab state ---
    @property
    def current_tab(self):
        if not self.tabs:
            # Fallback (should not happen in loop)
            return EditorTab(Buffer([""]), None, None, None)
        return self.tabs[self.active_tab_idx]

    @property
    def buffer(self): return self.current_tab.buffer
    @buffer.setter
    def buffer(self, val): self.current_tab.buffer = val

    @property
    def filename(self): return self.current_tab.filename
    @filename.setter
    def filename(self, val): self.current_tab.filename = val

    @property
    def cursor_y(self): return self.current_tab.cursor_y
    @cursor_y.setter
    def cursor_y(self, val): self.current_tab.cursor_y = val

    @property
    def cursor_x(self): return self.current_tab.cursor_x
    @cursor_x.setter
    def cursor_x(self, val): self.current_tab.cursor_x = val

    @property
    def scroll_offset(self): return self.current_tab.scroll_offset
    @scroll_offset.setter
    def scroll_offset(self, val): self.current_tab.scroll_offset = val

    @property
    def col_offset(self): return self.current_tab.col_offset
    @col_offset.setter
    def col_offset(self, val): self.current_tab.col_offset = val

    @property
    def desired_x(self): return self.current_tab.desired_x
    @desired_x.setter
    def desired_x(self, val): self.current_tab.desired_x = val

    @property
    def history(self): return self.current_tab.history
    @history.setter
    def history(self, val): self.current_tab.history = val

    @property
    def history_index(self): return self.current_tab.history_index
    @history_index.setter
    def history_index(self, val): self.current_tab.history_index = val

    @property
    def modified(self): return self.current_tab.modified
    @modified.setter
    def modified(self, val): self.current_tab.modified = val

    @property
    def mark_pos(self): return self.current_tab.mark_pos
    @mark_pos.setter
    def mark_pos(self, val): self.current_tab.mark_pos = val

    @property
    def file_mtime(self): return self.current_tab.file_mtime
    @file_mtime.setter
    def file_mtime(self, val): self.current_tab.file_mtime = val

    @property
    def current_syntax_rules(self): return self.current_tab.current_syntax_rules
    @current_syntax_rules.setter
    def current_syntax_rules(self, val): self.current_tab.current_syntax_rules = val
    # ---------------------------------------------

    def new_tab(self):
        """Open a new empty tab and switch to it"""
        new_tab = EditorTab(Buffer([""]), None, None, None)
        self._update_tab_git_status(new_tab)
        self.tabs.append(new_tab)
        self.active_tab_idx = len(self.tabs) - 1
        self.save_history(init=True)
        self.run_interactive_start_screen()

    def close_current_tab(self):
        """Close current tab. Returns True if exited editor, False if more tabs remain, None if cancelled"""
        if self.modified:
            self.status_message = "Close tab: Save changes? (y/n/Esc)"
            self.draw_ui()
            while True:
                try: ch = self.stdscr.getch()
                except: ch = -1
                if ch in (ord('y'), ord('Y')):
                    self.save_file()
                    break
                elif ch in (ord('n'), ord('N')):
                    break
                elif ch == 27 or ch == CTRL_C:
                    self.status_message = "Cancelled."
                    return None
        
        self.tabs.pop(self.active_tab_idx)
        if not self.tabs:
            return True # No tabs left, exit
        
        if self.active_tab_idx >= len(self.tabs):
            self.active_tab_idx = len(self.tabs) - 1
        return False

    def next_tab(self, *args):
        if not self.tabs: return
        self.active_tab_idx = (self.active_tab_idx + 1) % len(self.tabs)

    def prev_tab(self, *args):
        if not self.tabs: return
        self.active_tab_idx = (self.active_tab_idx - 1 + len(self.tabs)) % len(self.tabs)

    def _get_color(self, color_name):
        return COLOR_MAP.get(color_name.upper(), -1)

    def init_colors(self):
        if curses.has_colors():
            try:
                curses.start_color()
                curses.use_default_colors()
                c = self.config["colors"]
                
                curses.init_pair(1, self._get_color(c["header_text"]), self._get_color(c["header_bg"]))
                curses.init_pair(2, self._get_color(c["error_text"]), self._get_color(c["error_bg"]))
                curses.init_pair(3, self._get_color(c["linenum_text"]), self._get_color(c["linenum_bg"]))
                curses.init_pair(4, self._get_color(c["selection_text"]), self._get_color(c["selection_bg"]))
                
                curses.init_pair(5, self._get_color(c.get("keyword", "YELLOW")), -1)
                curses.init_pair(6, self._get_color(c.get("string", "GREEN")), -1)
                curses.init_pair(7, self._get_color(c.get("comment", "MAGENTA")), -1)
                curses.init_pair(8, self._get_color(c.get("number", "BLUE")), -1)
                curses.init_pair(9, curses.COLOR_WHITE, self._get_color(c.get("zenkaku_bg", "RED")))
                
                curses.init_pair(10, self._get_color(c.get("ui_border", "BLUE")), -1)
                curses.init_pair(11, self._get_color(c.get("explorer_dir", "BLUE")), -1)
                curses.init_pair(12, self._get_color(c.get("explorer_file", "WHITE")), -1)
                curses.init_pair(13, curses.COLOR_WHITE, self._get_color(c.get("terminal_bg", "DEFAULT")))

                # Tab Colors
                curses.init_pair(14, self._get_color(c.get("tab_active_text", "WHITE")), self._get_color(c.get("tab_active_bg", "BLUE")))
                curses.init_pair(15, self._get_color(c.get("tab_inactive_text", "WHITE")), self._get_color(c.get("tab_inactive_bg", "DEFAULT")))

                # Diff Colors
                curses.init_pair(16, self._get_color(c.get("diff_add", "GREEN")), -1)
                curses.init_pair(17, self._get_color(c.get("diff_remove", "RED")), -1)

                # Breadcrumb Color
                curses.init_pair(18, self._get_color(c.get("breadcrumb_text", "BLACK")), self._get_color(c.get("breadcrumb_bg", "WHITE")))

                # Search UI Colors
                curses.init_pair(19, self._get_color(c.get("search_text", "BLACK")), self._get_color(c.get("search_bg", "WHITE")))
                curses.init_pair(20, COLOR_MAP.get("BLACK"), self._get_color(c.get("search_highlight_bg", "YELLOW")))
                curses.init_pair(21, COLOR_MAP.get("BLACK"), self._get_color(c.get("active_search_highlight_bg", "MAGENTA")))

            except curses.error:
                pass

    def detect_syntax(self, filename):
        if not filename: return None
        _, ext = os.path.splitext(filename)
        for lang, rules in self.syntax_rules.items():
            if ext in rules["extensions"]:
                return rules
        return None

    def load_file(self, filename):
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                    return (content if content else [""]), None
            except (OSError, UnicodeDecodeError) as e:
                return [""], f"Error loading file: {e}"
        return [""], None
    
    def load_plugins(self):
        plugin_dir = os.path.join(get_config_dir(), "plugins")
        if not os.path.exists(plugin_dir):
            try: 
                os.makedirs(plugin_dir, exist_ok=True)
            except OSError as e:
                pass 
                return

        plugin_files = glob.glob(os.path.join(plugin_dir, "*.py"))
        loaded_count = 0
        
        for file_path in plugin_files:
            try:
                base = os.path.basename(file_path)
                if base.startswith("_"): continue
                module_name = base[:-3]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'init'):
                        module.init(self)
                        loaded_count += 1
            except Exception as e:
                self.set_status(f"Plugin load error ({os.path.basename(file_path)}): {e}", timeout=5)

        if loaded_count > 0:
            self.set_status(f"Loaded {loaded_count} plugins.", timeout=3)

    def reload_config(self):
        """設定を再読み込みして、関連コンポーネントを更新する"""
        new_config, load_error = load_config()
        if load_error:
            self.set_status(f"Reload Error: {load_error}", timeout=5)
            return

        self.config = new_config

        # Update components
        self.init_colors() # Recalculate color pairs
        self.explorer_width = self.config.get("explorer_width", 25)
        self.terminal_height = self.config.get("terminal_height", 10)

        # Refresh settings manager's view of the config
        self.settings_manager = SettingsManager(self.config)

        self.set_status("Configuration reloaded.", timeout=3)
        self.redraw_screen()

    def bind_key(self, key_code, func):
        self.plugin_key_bindings[key_code] = func

    def register_syntax_rule(self, lang_name, rule_dict):
        """プラグインから新しいシンタックスルールを登録する"""
        if lang_name and isinstance(rule_dict, dict) and "extensions" in rule_dict:
            self.syntax_rules[lang_name] = rule_dict
            self.set_status(f"Syntax for '{lang_name}' registered.", timeout=2)
        else:
            self.set_status(f"Invalid syntax rule for '{lang_name}'.", timeout=4)

    def register_config(self, key, default_value):
        """プラグインから新しい設定項目とデフォルト値を登録する"""
        if key not in self.config:
            self.config[key] = default_value

    # ==========================================
    # --- Plugin API ---
    # ==========================================
    def register_build_command(self, extension, command):
        """プラグインから新しいビルドコマンドを登録する"""
        if extension.startswith('.') and command:
            self.build_commands[extension] = command
            self.set_status(f"Build command for '{extension}' registered.", timeout=2)
        else:
            self.set_status(f"Invalid build command for '{extension}'.", timeout=4)

    def register_template(self, language, template_string):
        """プラグインから新しいテンプレートを登録する"""
        if language and isinstance(template_string, str):
            self.config['templates'][language] = template_string
            self.set_status(f"Template for '{language}' registered.", timeout=2)
        else:
            self.set_status(f"Invalid template for '{language}'.", timeout=4)
            
    def _update_and_save_user_config(self, updates):
        """Updates and saves specific keys to setting.json"""
        setting_dir = get_config_dir()
        setting_file = os.path.join(setting_dir, "setting.json")
        user_config = {}

        if os.path.exists(setting_file):
            try:
                with open(setting_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        user_config.update(updates)

        try:
            with open(setting_file, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, indent=4, ensure_ascii=False)
        except OSError:
            pass

    def _install_nerd_font(self):
        """Downloads and installs Hack Nerd Font for the current user."""
        font_url = "https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/Hack/Regular/HackNerdFont-Regular.ttf"
        font_filename = "HackNerdFont-Regular.ttf"
        system = platform.system()
        font_dir = ""

        if system == "Linux":
            font_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "fonts")
        elif system == "Darwin": # macOS
            font_dir = os.path.join(os.path.expanduser("~"), "Library", "Fonts")
        else:
            self._draw_message("Automatic font installation not supported on this OS.", 5)
            return

        os.makedirs(font_dir, exist_ok=True)
        font_path = os.path.join(font_dir, font_filename)

        self._draw_message(f"Downloading {font_filename}...", delay_seconds=1)
        try:
            with urllib.request.urlopen(font_url) as response, open(font_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            if system == "Linux":
                self._draw_message("Updating font cache...", delay_seconds=1)
                try:
                    subprocess.run(['fc-cache', '-f', '-v'], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self._draw_message("fc-cache failed. Please run it manually.", 5)
            
            self._draw_message("Font installed! Please set it in your terminal settings.", 5)
        except Exception as e:
            self._draw_message(f"Error installing font: {e}", 5)

    def _draw_message(self, message, delay_seconds=0):
        """Helper to draw a centered message and wait."""
        self.stdscr.clear()
        y = self.height // 2
        x = self.width // 2 - len(message) // 2
        try:
            # Use color pair 3 (linenum_text) for visibility
            self.safe_addstr(y, x, message, curses.color_pair(3))
            self.stdscr.refresh()
            if delay_seconds > 0:
                time.sleep(delay_seconds)
        except curses.error:
            pass

    def _check_nerd_font_support(self):
        """Checks for Nerd Font support and offers installation."""
        if self.config.get("nerd_font_check_done"):
            return

        use_nerd_font = self._prompt_for_confirmation("Enable Nerd Font icons? (Requires a Nerd Font installed) (y/n)")
        
        updates_to_save = {"nerd_font_check_done": True}

        if use_nerd_font:
            self.config["explorer_icon_theme"] = "nerd_font"
            updates_to_save["explorer_icon_theme"] = "nerd_font"
        else:
            install_font = self._prompt_for_confirmation("Download and install Hack Nerd Font? (y/n)")
            if install_font:
                self._install_nerd_font()
                self.config["explorer_icon_theme"] = "nerd_font"
                updates_to_save["explorer_icon_theme"] = "nerd_font"
            else:
                self.config["explorer_icon_theme"] = "emoji"
                updates_to_save["explorer_icon_theme"] = "emoji"

        self._update_and_save_user_config(updates_to_save)
        self.stdscr.clear()

    def get_cursor_position(self): return self.cursor_y, self.cursor_x
    def get_line_content(self, y): return self.buffer.lines[y] if 0 <= y < len(self.buffer) else ""
    def get_buffer_lines(self): return self.buffer.get_content()
    def get_line_count(self): return len(self.buffer)
    def get_config_value(self, key): return self.config.get(key)
    def get_filename(self): return self.filename
        
    def get_selection_text(self):
        sel = self.get_selection_range()
        if not sel: return None
        start, end = sel
        text_lines = []
        if start[0] == end[0]:
            text_lines.append(self.buffer.lines[start[0]][start[1]:end[1]])
        else:
            text_lines.append(self.buffer.lines[start[0]][start[1]:])
            for i in range(start[0] + 1, end[0]):
                text_lines.append(self.buffer.lines[i])
            text_lines.append(self.buffer.lines[end[0]][:end[1]])
        return text_lines

    def move_cursor_to(self, y, x):
        self.move_cursor(y, x, update_desired_x=True, check_bounds=True)

    def insert_text_at_cursor(self, text):
        self.insert_text(text)

    def save_current_history(self):
        self.save_history()

    def set_modified(self, state=True):
        self.modified = state

    def delete_range(self, start_pos, end_pos):
        y1, x1 = start_pos
        y2, x2 = end_pos
        if not (0 <= y1 < len(self.buffer) and 0 <= y2 < len(self.buffer)): return
        self.save_history()
        if y1 == y2:
            line = self.buffer.lines[y1]
            x1 = max(0, min(x1, len(line)))
            x2 = max(0, min(x2, len(line)))
            if x1 > x2: x1, x2 = x2, x1
            self.buffer.lines[y1] = line[:x1] + line[x2:]
        else:
            if y1 > y2: y1, y2 = y2, y1; x1, x2 = x2, x1
            line_start = self.buffer.lines[y1][:x1]
            line_end = self.buffer.lines[y2][x2:]
            del self.buffer.lines[y1 + 1 : y2 + 1]
            self.buffer.lines[y1] = line_start + line_end
        self.move_cursor(y1, x1, update_desired_x=True)
        self.modified = True

    def replace_text(self, y, start_x, end_x, new_text):
        if not (0 <= y < len(self.buffer)): return
        self.save_history()
        line = self.buffer.lines[y]
        start_x = max(0, min(start_x, len(line)))
        end_x = max(0, min(end_x, len(line)))
        prefix = line[:start_x]
        suffix = line[end_x:]
        self.buffer.lines[y] = prefix + new_text + suffix
        self.move_cursor(y, start_x + len(new_text), update_desired_x=True)
        self.modified = True

    def set_status_message(self, msg, timeout=3):
        self.set_status(msg, timeout)

    def redraw_screen(self):
        self.stdscr.erase()
        self.draw_ui()
        self.draw_content()
        self.stdscr.refresh()

    def prompt_user(self, prompt_msg, default_value=""):
        return self._prompt_for_input(prompt_msg, default_text=default_value)

    def _get_current_symbol(self):
        """カーソル位置に基づいて現在の関数やクラス名を特定する"""
        if not self.current_syntax_rules:
            return None

        pattern_str = self.current_syntax_rules.get("symbol_pattern")
        if not pattern_str:
            return None

        try:
            pattern = re.compile(pattern_str)
        except re.error:
            return None

        # カーソル行から上に向かってスキャン
        for i in range(self.cursor_y, -1, -1):
            line = self.buffer.lines[i]
            match = pattern.search(line)
            if match:
                # 複数のキャプチャグループがある場合を考慮し、最後のものを優先
                return match.groups()[-1]
        
        return None

    def _get_search_highlight_at(self, y, x):
        """
        Checks if the given coordinate (y, x) is part of a search result.
        Returns:
            - 'active' if it's the currently active highlighted result.
            - 'normal' if it's part of any other search result.
            - None if it's not part of any search result.
        """
        # This check can be slow if there are many results.
        # A more optimized version might use a set or a different data structure.
        for i, (res_y, start, end) in enumerate(self.search_results):
            if y == res_y and start <= x < end:
                if i == self.active_search_idx:
                    return 'active'
                return 'normal'
        return None

    def _find_all_matches(self, jump_to_first=True):
        """Finds all occurrences of self.search_query in the buffer and updates the results."""
        self.search_results = []
        self.active_search_idx = -1
        if not self.search_query:
            self.set_status("Search cleared.", timeout=2)
            return

        try:
            # Case-insensitive search for now, could be made an option
            pattern = re.compile(self.search_query, re.IGNORECASE)
        except re.error as e:
            self.set_status(f"Regex Error: {e}", timeout=4)
            return

        for y, line in enumerate(self.buffer.lines):
            for match in pattern.finditer(line):
                self.search_results.append((y, match.start(), match.end()))
        
        if self.search_results:
            if jump_to_first:
                self.active_search_idx = 0
                # Jump to the first result
                self.move_cursor_to(self.search_results[0][0], self.search_results[0][1])
            self.set_status(f"Found {len(self.search_results)} matches. ({self.active_search_idx + 1}/{len(self.search_results)})", timeout=3)
        else:
            self.set_status(f"No matches for '{self.search_query}'", timeout=3)

    def _prompt_for_input(self, prompt_msg, default_text=""):
        """Draws a prompt on the status bar and waits for user text input."""
        buffer = default_text
        cursor_char = "_"

        while True:
            self.set_status(f"{prompt_msg}{buffer}{cursor_char}", timeout=None)
            self.draw_ui()
            self.stdscr.refresh()

            try:
                key_in = self.stdscr.get_wch()
            except (curses.error, KeyboardInterrupt):
                continue

            key_code = -1
            char_input = None

            if isinstance(key_in, int):
                key_code = key_in
            elif isinstance(key_in, str) and len(key_in) == 1:
                code = ord(key_in)
                if code < 32 or code == 127: key_code = code
                else: char_input = key_in

            if key_code in (KEY_ENTER, KEY_RETURN):
                self.set_status("")
                return buffer
            elif key_code == KEY_ESC or key_code == CTRL_C:
                self.set_status("")
                return None # Cancelled
            elif key_code in (curses.KEY_BACKSPACE, KEY_BACKSPACE, KEY_BACKSPACE2):
                buffer = buffer[:-1]
            elif char_input:
                buffer += char_input

    def _prompt_for_confirmation(self, prompt_msg):
        """Displays a confirmation prompt and waits for 'y' or 'n'."""
        self.set_status(prompt_msg, timeout=None)
        self.draw_ui()
        self.stdscr.refresh()

        while True:
            try:
                ch = self.stdscr.getch()
                if ch in (ord('y'), ord('Y')):
                    self.set_status("")
                    return True
                elif ch in (ord('n'), ord('N'), KEY_ESC, CTRL_C):
                    self.set_status("")
                    return False
            except (curses.error, KeyboardInterrupt):
                self.set_status("")
                return False

    def _get_git_branch(self):
        """現在のGitブランチ名を取得する"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, check=True, cwd=os.getcwd()
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _get_diff(self):
        """
        Generates a diff between the current buffer and the last saved state.
        For git-tracked files, it diffs against HEAD.
        For other files, it diffs against the version on disk.
        For new files, it diffs against an empty state.
        """
        original_lines = []
        is_git_tracked = False

        # 1. Determine if the file is tracked by Git
        if self.filename and self.git_branch and os.path.exists(self.filename):
            try:
                # Check if the file is known to git
                subprocess.run(
                    ['git', 'ls-files', '--error-unmatch', self.filename],
                    stdout=subprocess.DEVNULL, text=True, check=True, stderr=subprocess.DEVNULL
                )
                is_git_tracked = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                is_git_tracked = False
        
        # 2. Get the original content
        if is_git_tracked:
            try:
                # Fetch content from HEAD
                result = subprocess.run(
                    ['git', 'show', f"HEAD:{self.filename}"],
                    capture_output=True, text=True
                )
                # git show can fail for new files that are added but not committed
                if result.returncode == 0:
                    original_lines = result.stdout.splitlines()
                else: # Fallback for added, uncommitted files
                    is_git_tracked = False 
            except (FileNotFoundError):
                 is_git_tracked = False # Git not found
        
        # Fallback for non-git files or git errors
        if not is_git_tracked:
            if self.filename and os.path.exists(self.filename):
                try:
                    with open(self.filename, 'r', encoding='utf-8') as f:
                        original_lines = f.read().splitlines()
                except (OSError, UnicodeDecodeError):
                    return ["Error: Could not read original file from disk."]
            else:
                # This is a new, unsaved buffer. Original is empty.
                original_lines = []

        # 3. Get current buffer content
        current_lines = self.buffer.get_content()

        # 4. Generate the diff
        diff = list(difflib.unified_diff(
            original_lines,
            current_lines,
            fromfile=f"a/{self.filename or 'untitled'}",
            tofile=f"b/{self.filename or 'untitled'}",
            lineterm='' # Avoid adding extra newlines
        ))

        if not diff:
            return ["No changes."]
        
        return diff

    def show_diff(self):
        """Show the git diff for the current file in a new tab."""
        diff_lines = self._get_diff()

        diff_tab_name = f"diff://{os.path.basename(self.filename) if self.filename else 'untitled'}"

        # Check if a diff tab for this file already exists
        for i, tab in enumerate(self.tabs):
            if tab.filename == diff_tab_name:
                self.active_tab_idx = i
                # Optionally refresh content
                tab.buffer = Buffer(diff_lines)
                return

        new_tab = EditorTab(Buffer(diff_lines), diff_tab_name, self.syntax_rules["diff"], None)
        new_tab.read_only = True

        self.tabs.append(new_tab)
        self.active_tab_idx = len(self.tabs) - 1

    def _get_git_file_status(self, filepath):
        """Get the git status for a specific file."""
        if not filepath or not self.git_branch:
            return None

        abs_path = os.path.abspath(filepath)
        if not os.path.exists(abs_path):
            return 'A'

        repo_dir = os.path.dirname(abs_path)

        try:
            subprocess.run(
                ['git', 'ls-files', '--error-unmatch', abs_path],
                stdout=subprocess.DEVNULL, text=True, cwd=repo_dir, check=True, stderr=subprocess.DEVNULL
            )
            diff_proc = subprocess.run(
                ['git', 'diff-index', '--quiet', 'HEAD', '--', abs_path],
                cwd=repo_dir
            )
            return 'M' if diff_proc.returncode == 1 else None
        except FileNotFoundError:
            self.git_branch = None
            return None
        except subprocess.CalledProcessError:
            return 'A'

    def _update_tab_git_status(self, tab):
        """Update the git status for a specific tab."""
        if self.git_branch:
            tab.git_status = self._get_git_file_status(tab.filename)
        else:
            tab.git_status = None

    def _process_vim_input(self, key_code, char_input):
        """vimモードのキー入力を処理する"""
        if self.vim_state == 'normal':
            # Handle 'yy' command
            if self.vim_last_key == 'y' and char_input == 'y':
                line_content = self.buffer.lines[self.cursor_y]
                self._update_clipboard([line_content], is_line=True)
                self.set_status("Yanked 1 line", timeout=2)
                self.vim_last_key = None
                return
            # Handle 'dd' command
            if self.vim_last_key == 'd' and char_input == 'd':
                line_content = self.buffer.lines[self.cursor_y]
                self._update_clipboard([line_content], is_line=True)
                self.delete_line()
                self.vim_last_key = None
                return

            # Reset sequence if another key is pressed
            self.vim_last_key = None

            if char_input == 'h':
                self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
            elif char_input == 'j':
                self.move_cursor(self.cursor_y + 1, self.desired_x)
            elif char_input == 'k':
                self.move_cursor(self.cursor_y - 1, self.desired_x)
            elif char_input == 'l':
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
            elif char_input == 'i':
                self.vim_state = 'insert'
            elif char_input == 'd':
                self.vim_last_key = 'd' # Start of a sequence
            elif char_input == 'y':
                self.vim_last_key = 'y'
            elif char_input == 'x':
                if self.buffer.lines:
                    self.save_history()
                    line = self.buffer.lines[self.cursor_y]
                    if line and self.cursor_x < len(line):
                        char = line[self.cursor_x]
                        self._update_clipboard([char], is_line=False)
                        self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x+1:]
                        self.modified = True
            elif char_input == 'p' or char_input == 'P':
                # システムクリップボードとの同期
                self._sync_from_system_clipboard()

                if self.clipboard:
                    self.save_history()
                    if self.vim_clipboard_type == 'line':
                        # 行単位の貼り付け
                        content_to_insert = self.clipboard[:-1] if self.clipboard and self.clipboard[-1] == '' else self.clipboard
                        insert_y = self.cursor_y + 1 if char_input == 'p' else self.cursor_y
                        self.buffer.lines[insert_y:insert_y] = content_to_insert
                        self.move_cursor(insert_y, 0, update_desired_x=True)
                    else:
                        if char_input == 'p':
                            # charwise p: pastes after cursor
                            line = self.buffer.lines[self.cursor_y]
                            if self.cursor_x < len(line):
                                self.move_cursor(self.cursor_y, self.cursor_x + 1)
                        self.perform_paste()
                    self.modified = True

    def _process_explorer_input(self, key_code, char_input):
        """Handles key presses when the file explorer is active."""
        cmd_key = key_code
        if cmd_key == -1 and char_input:
            try:
                cmd_key = ord(char_input)
            except TypeError:
                return

        if cmd_key == curses.KEY_UP:
            self.explorer.navigate(-1)
        elif cmd_key == curses.KEY_DOWN:
            self.explorer.navigate(1)
        elif cmd_key in (KEY_ENTER, KEY_RETURN):
            res = self.explorer.enter()
            if res:
                new_lines, err = self.load_file(res)
                if not err:
                    self.buffer = Buffer(new_lines)
                    self.filename = res
                    try:
                        self.file_mtime = os.path.getmtime(res)
                    except OSError:
                        self.file_mtime = None
                    self.current_syntax_rules = self.detect_syntax(res)
                    self.cursor_y, self.cursor_x, self.col_offset = 0, 0, 0
                    self.save_history(init=True)
                    self.active_pane = 'editor'
                else:
                    self.set_status(err)
        elif cmd_key == ord('s'):
            msg = self.explorer.cycle_sort_mode()
            self.set_status(msg, timeout=2)
        elif cmd_key == ord('o'):
            msg = self.explorer.toggle_sort_order()
            self.set_status(msg, timeout=2)
        elif cmd_key == ord('h'):
            msg = self.explorer.toggle_hidden()
            self.set_status(msg, timeout=2)
        elif cmd_key == ord('/'):
            query = self._prompt_for_input(f"Search in {os.path.basename(self.explorer.current_path)}/: ", self.explorer.search_query)
            self.explorer.set_search_query(query)
        elif cmd_key == ord('a'):
            msg = self.explorer.prompt_for_creation()
            if msg: self.set_status(msg, timeout=3)
        elif cmd_key == ord('d'):
            msg = self.explorer.delete_selected()
            if msg: self.set_status(msg, timeout=3)
        elif cmd_key == ord('r'):
            msg = self.explorer.rename_selected()
            if msg: self.set_status(msg, timeout=3)
        elif cmd_key == ord('i'):
            self.explorer.show_details = not self.explorer.show_details
            self.set_status(f"Show Details: {self.explorer.show_details}", timeout=2)
        elif cmd_key == KEY_ESC:
            self.active_pane = 'editor'

    def _process_search_input(self, key_code, char_input):
        """Handles key presses when the search UI is active."""
        # Handle text input
        if char_input:
            if self.search_input_focused == "search":
                self.search_query += char_input
                self._find_all_matches() # Live search
            else: # "replace"
                self.replace_query += char_input

        # Handle special keys
        elif key_code in (curses.KEY_BACKSPACE, KEY_BACKSPACE, KEY_BACKSPACE2):
            if self.search_input_focused == "search":
                if self.search_query:
                    self.search_query = self.search_query[:-1]
                    self._find_all_matches() # Live search
            else: # "replace"
                if self.replace_query:
                    self.replace_query = self.replace_query[:-1]

        elif key_code == KEY_TAB:
            self.search_input_focused = "replace" if self.search_input_focused == "search" else "search"

        elif key_code == KEY_ESC:
            self.search_mode = False
            self.search_results = []
            self.active_search_idx = -1
            self.set_status("Search cancelled.", timeout=2)

        elif key_code == curses.KEY_DOWN or (self.search_input_focused == "search" and key_code in (KEY_ENTER, KEY_RETURN)):
            if self.search_results:
                self.active_search_idx = (self.active_search_idx + 1) % len(self.search_results)
                y, x, _ = self.search_results[self.active_search_idx]
                self.move_cursor_to(y, x)
                self.set_status(f"Match {self.active_search_idx + 1}/{len(self.search_results)}", timeout=3)

        elif key_code == curses.KEY_UP:
            if self.search_results:
                self.active_search_idx = (self.active_search_idx - 1 + len(self.search_results)) % len(self.search_results)
                y, x, _ = self.search_results[self.active_search_idx]
                self.move_cursor_to(y, x)
                self.set_status(f"Match {self.active_search_idx + 1}/{len(self.search_results)}", timeout=3)
        
        elif key_code in (KEY_ENTER, KEY_RETURN) and self.search_input_focused == "replace":
            self._replace_current()
        
        elif key_code == CTRL_A: # Ctrl+A for Replace All
            self._replace_all()

    def _replace_current(self):
        """Replaces the currently active search result with the replace_query."""
        if not self.search_results or self.active_search_idx == -1:
            self.set_status("No active match to replace.", timeout=2)
            return

        self.save_history()

        y, start_x, end_x = self.search_results[self.active_search_idx]
        line = self.buffer.lines[y]
        
        # Replace the text
        new_line = line[:start_x] + self.replace_query + line[end_x:]
        self.buffer.lines[y] = new_line
        self.modified = True

        # After replacing, re-run the search but don't jump to the start
        current_index = self.active_search_idx
        self._find_all_matches(jump_to_first=False)

        if self.search_results:
            # Try to keep the same index if it's still valid
            if current_index >= len(self.search_results):
                self.active_search_idx = len(self.search_results) - 1
            else:
                self.active_search_idx = current_index
            
            # Move to the new active match to show the user where they are
            y, x, _ = self.search_results[self.active_search_idx]
            self.move_cursor_to(y, x)
            self.set_status(f"Replaced. Matches: {len(self.search_results)}. ({self.active_search_idx + 1}/{len(self.search_results)})", timeout=3)

    def _replace_all(self):
        """Replaces all occurrences of search_query with replace_query."""
        if not self.search_results:
            self.set_status("No matches to replace.", timeout=2)
            return

        self.save_history()
        replacements_count = len(self.search_results)
        # Iterate backwards to avoid messing up indices
        for y, start_x, end_x in reversed(self.search_results):
            line = self.buffer.lines[y]
            self.buffer.lines[y] = line[:start_x] + self.replace_query + line[end_x:]
        self.modified = True
        self.search_results, self.active_search_idx = [], -1
        self.set_status(f"Replaced {replacements_count} occurrences.", timeout=3)

    def _create_default_settings_file(self):
        """Creates or overwrites the setting.json file with default values."""
        setting_dir = get_config_dir()
        setting_file = os.path.join(setting_dir, "setting.json")

        if os.path.exists(setting_file):
            if not self._prompt_for_confirmation("setting.json already exists. Overwrite? (y/n)"):
                self.set_status("Operation cancelled.", timeout=3)
                return

        try:
            with open(setting_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            self.set_status("Default setting.json created successfully.", timeout=3)
        except OSError as e:
            self.set_status(f"Error creating file: {e}", timeout=5)

    def _select_setting_asset(self):
        """設定アセットを選択して適用する"""
        asset_names = sorted(SETTING_ASSETS.keys())
        selected_index = 0
        scroll_offset = 0

        original_pane = self.active_pane
        # 一時的にパネを切り替え（描画のため）
        self.active_pane = 'asset_selector'

        while True:
            self.height, self.width = self.stdscr.getmaxyx()
            self.stdscr.erase()
            self.draw_tab_bar()
            self.draw_ui()

            max_items = self.height - 8
            if selected_index < scroll_offset:
                scroll_offset = selected_index
            elif selected_index >= scroll_offset + max_items:
                scroll_offset = selected_index - max_items + 1

            title = "--- Select Setting Asset ---"
            box_h = min(len(asset_names) + 4, max_items if max_items > 0 else 1)
            box_w = max(max([len(n) for n in asset_names]) + 6, len(title) + 4)
            box_y = max(0, self.height // 2 - box_h // 2)
            box_x = max(0, self.width // 2 - box_w // 2)

            try:
                for i in range(box_h):
                    self.stdscr.addstr(box_y + i, box_x, " " * box_w, curses.color_pair(1))
                self.safe_addstr(box_y + 1, box_x + (box_w - len(title)) // 2, title, curses.color_pair(1))
            except curses.error: pass

            for i in range(min(len(asset_names), max_items if max_items > 0 else 0)):
                idx = scroll_offset + i
                if idx >= len(asset_names): break
                
                name = asset_names[idx]
                y = box_y + 3 + i
                x = box_x + 2
                
                prefix = "> " if idx == selected_index else "  "
                attr = curses.color_pair(1) | curses.A_REVERSE if idx == selected_index else curses.color_pair(1)
                self.safe_addstr(y, x, prefix + name.ljust(box_w - 6), attr)

            self.stdscr.refresh()

            try:
                ch = self.stdscr.getch()
            except (curses.error, KeyboardInterrupt):
                ch = -1

            if ch == curses.KEY_UP:
                selected_index = (selected_index - 1 + len(asset_names)) % len(asset_names)
            elif ch == curses.KEY_DOWN:
                selected_index = (selected_index + 1) % len(asset_names)
            elif ch in (KEY_ENTER, KEY_RETURN):
                selected_name = asset_names[selected_index]
                self._apply_setting_asset(SETTING_ASSETS[selected_name], selected_name)
                break
            elif ch == KEY_ESC or ch == CTRL_C:
                break

        self.active_pane = original_pane

    def _apply_setting_asset(self, asset_dict, asset_name):
        """設定アセットを適用する"""
        try:
            # 現行の設定を更新
            self.config.update(asset_dict)
            
            # ユーザーの設定ファイルに保存
            setting_dir = get_config_dir()
            setting_file = os.path.join(setting_dir, "setting.json")
            os.makedirs(setting_dir, exist_ok=True)
            
            with open(setting_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.set_status(f"Applied asset '{asset_name}' and saved to setting.json", timeout=5)
        except Exception as e:
            self.set_status(f"Error applying asset: {e}", timeout=5)

    def _select_and_insert_template(self):
        """テンプレート選択メニューを表示し、選択されたテンプレートを挿入する"""
        templates = self.config.get("templates", {})
        if not templates:
            self.set_status("No templates defined.", timeout=3)
            return

        languages = sorted(templates.keys())
        selected_index = 0
        scroll_offset = 0

        original_pane = self.active_pane
        self.active_pane = 'template_selector' # Special pane state

        while True:
            self.stdscr.erase()
            # Draw a minimal background UI
            self.draw_tab_bar()
            self.draw_ui()

            max_items = self.height - 8
            
            if selected_index < scroll_offset:
                scroll_offset = selected_index
            elif selected_index >= scroll_offset + max_items:
                scroll_offset = selected_index - max_items + 1


            title = "--- Select a Template ---"
            
            # Center the box
            box_h = min(len(languages) + 4, max_items)
            box_w = max(len(max(languages, key=len)) + 6, len(title) + 4)
            box_y = self.height // 2 - box_h // 2
            box_x = self.width // 2 - box_w // 2

            # Simple box drawing
            try:
                for i in range(box_h):
                    self.stdscr.addstr(box_y + i, box_x, " " * box_w, curses.color_pair(1))
                self.safe_addstr(box_y + 1, box_x + (box_w - len(title)) // 2, title, curses.color_pair(1))
            except curses.error: pass

            for i in range(max_items):
                idx = scroll_offset + i
                if idx >= len(languages):
                    break
                
                lang = languages[idx]
                y = box_y + 3 + i
                x = box_x + 2
                
                prefix = "> " if idx == selected_index else "  "
                attr = curses.color_pair(1) | curses.A_REVERSE if idx == selected_index else curses.color_pair(1)
                self.safe_addstr(y, x, prefix + lang.ljust(box_w - 6), attr)

            self.stdscr.refresh()

            try:
                ch = self.stdscr.getch()
            except (curses.error, KeyboardInterrupt):
                ch = -1

            if ch == curses.KEY_UP:
                selected_index = (selected_index - 1 + len(languages)) % len(languages)
            elif ch == curses.KEY_DOWN:
                selected_index = (selected_index + 1) % len(languages)
            elif ch in (KEY_ENTER, KEY_RETURN):
                selected_language = languages[selected_index]
                template_string = templates[selected_language]
                self.insert_text(template_string)
                self.set_status(f"Inserted '{selected_language}' template.", timeout=3)
                break
            elif ch == KEY_ESC or ch == CTRL_C:
                self.set_status("Template selection cancelled.", timeout=3)
                break

        self.active_pane = original_pane


    # ==========================================

    def insert_text(self, text):
        self.save_history()
        lines_to_insert = text.split('\n')
        current_line = self.buffer.lines[self.cursor_y]
        prefix = current_line[:self.cursor_x]
        suffix = current_line[self.cursor_x:]
        if len(lines_to_insert) == 1:
            self.buffer.lines[self.cursor_y] = prefix + lines_to_insert[0] + suffix
            self.move_cursor(self.cursor_y, self.cursor_x + len(lines_to_insert[0]))
        else:
            self.buffer.lines[self.cursor_y] = prefix + lines_to_insert[0]
            for i in range(1, len(lines_to_insert) - 1):
                self.buffer.lines.insert(self.cursor_y + i, lines_to_insert[i])
            self.buffer.lines.insert(self.cursor_y + len(lines_to_insert) - 1, lines_to_insert[-1] + suffix)
            new_y = self.cursor_y + len(lines_to_insert) - 1
            new_x = len(lines_to_insert[-1])
            self.move_cursor(new_y, new_x)
        self.modified = True

    def save_history(self, init=False):
        snapshot = (self.buffer.get_content(), self.cursor_y, self.cursor_x)
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        if not init and self.history and self.history[-1][0] == snapshot[0]:
            return
        self.history.append(snapshot)
        self.history_index = len(self.history) - 1
        limit = self.config.get("history_limit", 50)
        if len(self.history) > limit:
            self.history.pop(0)
            self.history_index -= 1
        if not init:
            self.modified = True

    def apply_history(self, index):
        if 0 <= index < len(self.history):
            self.history_index = index
            snapshot = self.history[index]
            self.buffer.set_content(snapshot[0])
            self.move_cursor(snapshot[1], snapshot[2], update_desired_x=True, check_bounds=True)
            self.scroll_offset = max(0, self.cursor_y - self.get_edit_height() // 2)
            self.modified = self.history_index != 0
            self.status_message = f"Applied history state {index+1}/{len(self.history)}"

    def undo(self):
        if self.history_index > 0: self.apply_history(self.history_index - 1)
        else: self.status_message = "Nothing to undo."

    def redo(self):
        if self.history_index < len(self.history) - 1: self.apply_history(self.history_index + 1)
        else: self.status_message = "Nothing to redo."

    def safe_addstr(self, y, x, string, attr=0):
        try:
            if y >= self.height or x >= self.width: return
            available = self.width - x
            if len(string) > available: string = string[:available]

            # Known curses bug: addstr to bottom-right corner raises an error.
            # Use insstr() for this specific case to avoid it.
            if y == self.height - 1 and len(string) == available:
                self.stdscr.insstr(y, x, string, attr)
            else:
                self.stdscr.addstr(y, x, string, attr)
        except curses.error:
            pass

    def run_interactive_start_screen(self):
        """インタラクティブなスタート画面ループ"""
        while True:
            self.height, self.width = self.stdscr.getmaxyx()
            self.show_start_screen(duration_ms=None, interactive=True)
            
            try:
                ch = self.stdscr.getch()
            except KeyboardInterrupt:
                break

            if ch == CTRL_S:
                choice = self.run_settings_menu()
                if choice == 0: # Open setting.json
                    setting_file = os.path.join(get_config_dir(), "setting.json")
                    if not os.path.exists(setting_file):
                        # Create empty file if not exists
                        try:
                            with open(setting_file, 'w') as f:
                                json.dump({}, f)
                        except OSError: pass

                    new_lines, err = self.load_file(setting_file)
                    if not err:
                        self.buffer = Buffer(new_lines)
                        self.filename = setting_file
                        try:
                            self.file_mtime = os.path.getmtime(setting_file)
                        except OSError: self.file_mtime = None
                        self.current_syntax_rules = self.detect_syntax(setting_file)
                        self.save_history(init=True)
                        self.active_pane = 'editor'
                        break
                    else:
                        self.set_status(err)
                elif choice == 1: # Choice setting
                    self.active_pane = 'settings_manager'
                    break
                elif choice == 2: # Create default JSON
                    self._create_default_settings_file()
                    # Stay on the start screen after the operation
                    continue
                elif choice == 3: # Select setting assets
                    self._select_setting_asset()
                    continue
                # if choice is -1, do nothing and stay on start screen

            elif ch == CTRL_P:
                # プラグインマネージャーへ遷移
                self.active_pane = 'plugin_manager'
                break
            elif ch == CTRL_F:
                self.active_pane = 'full_screen_explorer'
                break
            elif ch != -1:
                # 任意のキーでエディタへ
                break

    def run_settings_menu(self):
        """設定メニューを表示し、ユーザーの選択を待つ"""
        menu_items = ["[1] Open setting.json", "[2] Choice setting", "[3] Create default-json", "[4] Select setting assets"]
        selected_index = 0

        while True:
            self.stdscr.erase()
            self.height, self.width = self.stdscr.getmaxyx()

            title = "--- Settings Menu ---"

            title_y = self.height // 2 - 5
            self.safe_addstr(title_y, self.width // 2 - len(title) // 2, title, curses.color_pair(1))

            for i, item in enumerate(menu_items):
                y = title_y + 2 + i
                display_item = ("> " if i == selected_index else "  ") + item
                x = self.width // 2 - len(display_item) // 2
                attr = curses.color_pair(1) | curses.A_REVERSE if i == selected_index else curses.color_pair(1)
                self.safe_addstr(y, x, display_item, attr)

            self.stdscr.refresh()

            try:
                ch = self.stdscr.getch()
            except curses.error:
                ch = -1

            if ch == curses.KEY_UP:
                selected_index = (selected_index - 1) % len(menu_items)
            elif ch == curses.KEY_DOWN:
                selected_index = (selected_index + 1) % len(menu_items)
            elif ch in (KEY_ENTER, KEY_RETURN, ord('1'), ord('2'), ord('3'), ord('4')):
                if ch == ord('1') : selected_index = 0
                if ch == ord('2') : selected_index = 1
                if ch == ord('3') : selected_index = 2
                if ch == ord('4') : selected_index = 3
                return selected_index
            elif ch == KEY_ESC:
                return -1 # Cancel

    def show_start_screen(self, duration_ms=None, interactive=False):
        self.stdscr.clear()
        self.draw_tab_bar()
        # Pair 3 is CYAN (Text)
        logo_attr = curses.color_pair(3) | curses.A_BOLD
        
        logo = [
            "                                         　    ) (",
            "                                         　   (   ) )",
            "                                         　    ) ( (",
            "                                         　  _______)",
            rf"   _________    ________________________　.-'-------|",
            rf"  / ____/   |  / ____/ ____/ ____/ ____/　| CAFFEE  |__",
            rf" / /   / /| | / /_  / /_  / __/ / __/   　| v{VERSION}  |__)",
            rf"/ /___/ ___ |/ __/ / __/ / /___/ /___   　|_________|",
            rf"\____/_/  |_/_/   /_/   /_____/_____/   　 `-------'"
        ]
        my = self.height // 2 - 6
        mx = self.width // 2 
        start_x_offset = 28

        for i, l in enumerate(logo):
            if my + i < self.height - 2:
                self.safe_addstr(my + i, max(0, mx - start_x_offset), l.rstrip(), logo_attr)
                
        self.safe_addstr(my + len(logo) + 1, max(0, mx - 12), f"CAFFEE Editor v{VERSION}", logo_attr)

        if self.config.get("show_startup_time") and self.start_time:
            elapsed = time.time() - self.start_time
            startup_msg = f"Startup time: {elapsed:.3f} seconds"
            self.safe_addstr(my + len(logo) + 2, max(0, mx - len(startup_msg)//2), startup_msg, logo_attr)
        
        # --- インタラクティブモードの場合の表示 ---
        if interactive:
            menu_y = my + len(logo) + 4
            menu_text = "[^F] File Explorer [^S] Settings [^P] Plugins [Any Key] Empty Buffer"
            self.safe_addstr(menu_y, max(0, mx - len(menu_text)//2), menu_text, curses.color_pair(3))
        
        # --- 通常のメッセージ ---
        elif not duration_ms:
            self.safe_addstr(my + len(logo) + 3, max(0, mx - 15), "Press any key to brew...", curses.A_DIM | curses.color_pair(3))
        
        self.stdscr.refresh()
        
        if duration_ms:
             curses.napms(duration_ms)
        elif not interactive:
             self.stdscr.getch()

    def get_selection_range(self):
        if not self.mark_pos: return None
        p1 = self.mark_pos
        p2 = (self.cursor_y, self.cursor_x)
        if p1 > p2: return p2, p1
        return p1, p2

    def is_in_selection(self, y, x):
        sel = self.get_selection_range()
        if not sel: return False
        start, end = sel
        if start[0] == end[0]: return y == start[0] and start[1] <= x < end[1]
        if y == start[0]: return x >= start[1]
        if y == end[0]: return x < end[1]
        return start[0] < y < end[0]

    def get_edit_rect(self):
        breadcrumb_h = 1 if self.config.get("show_breadcrumb", True) else 0
        y = self.tab_bar_height + self.header_height + breadcrumb_h
        x = 0
        h = self.height - self.tab_bar_height - self.header_height - breadcrumb_h - self.status_height - self.menu_height
        w = self.width
        
        if self.show_terminal:
            term_h = min(self.terminal_height, h - 5)
            h -= term_h
            
        if self.show_explorer:
            exp_w = min(self.explorer_width, w - 20)
            w -= exp_w
            
        return y, x, h, w

    def get_explorer_rect(self):
        if not self.show_explorer: return 0,0,0,0
        
        breadcrumb_h = 1 if self.config.get("show_breadcrumb", True) else 0
        y = self.tab_bar_height + self.header_height + breadcrumb_h
        w = min(self.explorer_width, self.width - 20)
        x = self.width - w
        h = self.height - self.tab_bar_height - self.header_height - breadcrumb_h - self.status_height - self.menu_height
        if self.show_terminal:
            term_h = min(self.terminal_height, h - 5)
            h -= term_h
            
        return y, x, h, w

    def get_terminal_rect(self):
        if not self.show_terminal: return 0,0,0,0
        breadcrumb_h = 1 if self.config.get("show_breadcrumb", True) else 0
        edit_y, _, edit_h, _ = self.get_edit_rect()
        y = edit_y + edit_h
        x = 0
        w = self.width
        total_h = self.height - self.tab_bar_height - self.header_height - breadcrumb_h - self.status_height - self.menu_height
        h = min(self.terminal_height, total_h - 5)
        return y, x, h, w

    def get_edit_height(self):
        _, _, h, _ = self.get_edit_rect()
        return max(1, h)

    def draw_content(self):
        # Plugin Manager Draw Handling
        if self.active_pane == 'plugin_manager':
            colors = {
                "header": curses.color_pair(1),
                "ui_border": curses.color_pair(10)
            }
            self.plugin_manager.draw(self.stdscr, self.height, self.width, colors)
            return

        if self.active_pane == 'settings_manager':
            colors = {
                "header": curses.color_pair(1),
                "ui_border": curses.color_pair(10)
            }
            self.settings_manager.draw(self.stdscr, self.height, self.width, colors)
            return

        if self.active_pane == 'keybinding_settings':
            colors = {
                "header": curses.color_pair(1),
                "ui_border": curses.color_pair(10)
            }
            self.keybinding_settings_manager.draw(self.stdscr, self.height, self.width, colors)
            return
            
        if self.active_pane == 'full_screen_explorer':
            colors = {
                "ui_border": curses.color_pair(10),
                "header": curses.color_pair(1),
                "dir": curses.color_pair(11),
                "file": curses.color_pair(12)
            }
            # フルスクリーンなのでy=0, x=0, h=self.height-1, w=self.width
            self.explorer.draw(self.stdscr, 1, 0, self.height - 2, self.width, colors)
            return

        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        edit_y, edit_x, edit_h, edit_w = self.get_edit_rect()
        
        ATTR_NORMAL = 0
        ATTR_KEYWORD = curses.color_pair(5)
        ATTR_STRING = curses.color_pair(6)
        ATTR_COMMENT = curses.color_pair(7)
        ATTR_NUMBER = curses.color_pair(8)
        ATTR_ZENKAKU = curses.color_pair(9)
        ATTR_SELECT = curses.color_pair(4)
        ATTR_DIFF_ADD = curses.color_pair(16)
        ATTR_DIFF_REMOVE = curses.color_pair(17)

        is_diff_view = self.current_syntax_rules and self.current_syntax_rules.get("language_name") == "diff"

        for i in range(edit_h):
            file_line_idx = self.scroll_offset + i
            draw_y = edit_y + i
            
            try:
                self.stdscr.addstr(draw_y, edit_x, " " * edit_w)
            except curses.error: pass
            
            if file_line_idx >= len(self.buffer):
                self.safe_addstr(draw_y, edit_x, "~", curses.color_pair(3))
            else:
                # --- 相対行数表示の処理 ---
                show_relative = self.config.get("show_relative_linenum", False)
                ln_str = ""
                if show_relative:
                    if file_line_idx == self.cursor_y:
                        # カーソル行は絶対行数を表示
                        ln_str = str(file_line_idx + 1).rjust(linenum_width - 1) + " "
                    else:
                        # それ以外は相対行数を表示
                        relative_num = abs(file_line_idx - self.cursor_y)
                        ln_str = str(relative_num).rjust(linenum_width - 1) + " "
                else:
                    # 通常の絶対行数表示
                    ln_str = str(file_line_idx + 1).rjust(linenum_width - 1) + " "
                
                self.safe_addstr(draw_y, edit_x, ln_str, curses.color_pair(3))
                
                line = self.buffer[file_line_idx]
                
                # --- 横スクロール対応: 表示領域に合わせて文字列をスライス ---
                max_content_width = edit_w - linenum_width
                
                # col_offsetに基づいて表示部分を切り出し
                display_line = line[self.col_offset : self.col_offset + max_content_width]
                
                # --- シンタックスハイライト (全体に対して計算し、表示時にシフト) ---
                line_attrs = [ATTR_NORMAL] * len(line)
                
                if is_diff_view:
                    if line.startswith('+'):
                        for j in range(len(line_attrs)): line_attrs[j] = ATTR_DIFF_ADD
                    elif line.startswith('-'):
                        for j in range(len(line_attrs)): line_attrs[j] = ATTR_DIFF_REMOVE
                elif self.current_syntax_rules:
                    if "keywords" in self.current_syntax_rules:
                        for match in re.finditer(self.current_syntax_rules["keywords"], line):
                            for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_KEYWORD
                    if "numbers" in self.current_syntax_rules:
                        for match in re.finditer(self.current_syntax_rules["numbers"], line):
                             for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_NUMBER
                    if "strings" in self.current_syntax_rules:
                        for match in re.finditer(self.current_syntax_rules["strings"], line):
                            for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_STRING
                    if "comments" in self.current_syntax_rules:
                         for match in re.finditer(self.current_syntax_rules["comments"], line):
                            for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_COMMENT

                # --- 描画ループ ---
                base_x = edit_x + linenum_width
                current_screen_x = base_x

                for cx, char in enumerate(display_line):
                    if current_screen_x >= edit_x + edit_w:
                        break

                    # 実際のバッファ上のインデックス
                    real_index = self.col_offset + cx
                    
                    attr = ATTR_NORMAL
                    if real_index < len(line_attrs):
                        attr = line_attrs[real_index]

                    # Apply search highlighting, but allow selection to override it
                    highlight_type = self._get_search_highlight_at(file_line_idx, real_index)
                    if highlight_type == 'active':
                        attr = curses.color_pair(21)
                    elif highlight_type == 'normal':
                        attr = curses.color_pair(20)
                    
                    if self.is_in_selection(file_line_idx, real_index):
                        attr = ATTR_SELECT

                    char_width = get_char_width(char)
                    
                    if current_screen_x + char_width > edit_x + edit_w:
                        break

                    if char == '\u3000':
                        self.safe_addstr(draw_y, current_screen_x, "　", ATTR_ZENKAKU)
                    else:
                        self.safe_addstr(draw_y, current_screen_x, char, attr)

                    current_screen_x += char_width

        # --- Explorer & Terminal Draw ---
        if self.show_explorer:
            ey, ex, eh, ew = self.get_explorer_rect()
            colors = {
                "ui_border": curses.color_pair(10),
                "header": curses.color_pair(1),
                "dir": curses.color_pair(11),
                "file": curses.color_pair(12)
            }
            if self.active_pane == 'explorer':
                colors["ui_border"] = colors["ui_border"] | curses.A_BOLD
            self.explorer.draw(self.stdscr, ey, ex, eh, ew, colors)

        if self.show_terminal:
            ty, tx, th, tw = self.get_terminal_rect()
            colors = {
                "ui_border": curses.color_pair(10),
                "header": curses.color_pair(1),
                "bg": curses.color_pair(13)
            }
            if self.active_pane == 'terminal':
                colors["ui_border"] = colors["ui_border"] | curses.A_BOLD
            self.terminal.draw(self.stdscr, ty, tx, th, tw, colors)

    def _draw_suggestions(self):
        """Draw the predictive text suggestions box if active."""
        if not self.suggestion_active or not self.suggestions:
            return

        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        edit_y, edit_x, _, _ = self.get_edit_rect()
        
        # Calculate screen position of the cursor
        screen_y = self.cursor_y - self.scroll_offset + edit_y
        
        screen_x = edit_x + linenum_width
        if self.cursor_y < len(self.buffer):
            if self.cursor_x >= self.col_offset:
                visible_segment = self.buffer.lines[self.cursor_y][self.col_offset : self.cursor_x]
                for char in visible_segment:
                    screen_x += get_char_width(char)

        # Basic layout for the suggestion box
        popup_y = screen_y + 1
        popup_x = screen_x
        
        max_len = max(len(s) for s in self.suggestions)
        popup_width = max_len + 2 # padding

        # Adjust position if it goes off-screen
        if popup_x + popup_width >= self.width:
            popup_x = self.width - popup_width - 1
        if popup_y + len(self.suggestions) >= self.height - self.menu_height - self.status_height:
             popup_y = screen_y - len(self.suggestions)


        for i, suggestion in enumerate(self.suggestions):
            y = popup_y + i
            if y >= self.height - self.menu_height - self.status_height:
                break
            
            attr = curses.A_REVERSE if i == self.selected_suggestion_idx else curses.A_NORMAL
            
            # Use a color pair that stands out, e.g., header colors
            bg_attr = curses.color_pair(1)
            
            display_str = f" {suggestion.ljust(max_len)} "
            self.safe_addstr(y, popup_x, display_str, attr | bg_attr)

    def draw_search_ui(self):
        """Draws the search/replace UI at the bottom of the screen."""
        if not self.search_mode:
            return

        # 検索UIはフッターメニューの上に2行表示
        ui_h = 2
        start_y = self.height - self.menu_height - self.status_height - ui_h
        
        search_label = "Search: "
        replace_label = "Replace: "
        
        # 検索ボックス
        self.safe_addstr(start_y, 0, " " * self.width, curses.color_pair(19))
        self.safe_addstr(start_y, 0, search_label, curses.color_pair(19))
        self.safe_addstr(start_y, len(search_label), self.search_query, curses.color_pair(19))
        if self.search_input_focused == "search":
            self.safe_addstr(start_y, len(search_label) + len(self.search_query), "_", curses.color_pair(19) | curses.A_BLINK)

        # 置換ボックス
        self.safe_addstr(start_y + 1, 0, " " * self.width, curses.color_pair(19))
        self.safe_addstr(start_y + 1, 0, replace_label, curses.color_pair(19))
        self.safe_addstr(start_y + 1, len(replace_label), self.replace_query, curses.color_pair(19))
        if self.search_input_focused == "replace":
            self.safe_addstr(start_y + 1, len(replace_label) + len(self.replace_query), "_", curses.color_pair(19) | curses.A_BLINK)

    def draw_ui(self):
        # Plugin Manager Mode doesn't use standard UI
        if self.active_pane in ('plugin_manager', 'settings_manager'):
            return
            
        if self.active_pane == 'full_screen_explorer':
            # This pane now uses the explorer's own draw method which includes headers/footers
            return

        # --- Tab Bar Drawing ---
        self.draw_tab_bar()
        
        # --- Breadcrumb ---
        self.draw_breadcrumb()

        mark_status = "[MARK]" if self.mark_pos else ""
        menu_lines = []

        if self.search_mode:
            self.draw_search_ui()
            self.menu_height = 0 # 検索UIが表示されている間はキーバインドヒントを非表示
        else:
            current_line_text = ""
            
            displayed_ids = self.config.get("displayed_keybindings", [])
            
            for binding_id in displayed_ids:
                binding_info = DEFAULT_KEYBINDINGS.get(binding_id)
                if not binding_info: continue

                key_str = binding_info["key"]
                label = binding_info["label"]
                item_str = f"{key_str} {label}  "
                if len(current_line_text) + len(item_str) > self.width:
                    menu_lines.append(current_line_text)
                    current_line_text = item_str
                else:
                    current_line_text += item_str
            if current_line_text:
                menu_lines.append(current_line_text)

            self.menu_height = len(menu_lines)
            
            for i, line in enumerate(reversed(menu_lines)):
                y = self.height - 1 - i
                self.safe_addstr(y, 0, line.ljust(self.width), curses.color_pair(1))

        mod_char = " *" if self.modified else ""
        syntax_name = "Text"
        if self.current_syntax_rules:
            ext_list = self.current_syntax_rules.get("extensions", [])
            if ext_list: syntax_name = ext_list[0].upper().replace(".", "")

        focus_map = {'editor': 'EDT', 'explorer': 'EXP', 'terminal': 'TRM', 'full_screen_explorer': 'F-EXP'}
        focus_str = f"[{focus_map.get(self.active_pane, '---')}]"

        branch_info = f" ({self.git_branch})" if self.git_branch else ""
        header = f" {EDITOR_NAME} v{VERSION}{branch_info} | {self.filename or 'New Buffer'} {mod_char} | {syntax_name} | {focus_str} {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(1, 0, header, curses.color_pair(1) | curses.A_BOLD)
        self.header_height = 1
        self.status_height = 1

        status_y = self.height - self.menu_height - 1
        
        now = datetime.datetime.now()
        display_msg = ""
        if self.status_message:
            if not self.status_expire_time or now <= self.status_expire_time:
                display_msg = self.status_message
            else:
                self.status_message = ""
                self.status_expire_time = None
        
        pos_info = f" {self.cursor_y + 1}:{self.cursor_x + 1} "
        
        vim_status_str = ""
        if self.vim_mode:
            vim_status_str = f" -- {self.vim_state.upper()} -- "

        max_msg_len = self.width - len(pos_info) - len(vim_status_str) - 1
        if len(display_msg) > max_msg_len:
            display_msg = display_msg[:max_msg_len]
            
        self.safe_addstr(status_y, 0, " " * self.width, curses.color_pair(2))
        self.safe_addstr(status_y, 0, display_msg, curses.color_pair(2))
        
        # Draw vim status then position
        right_status_x = self.width - len(pos_info)
        self.safe_addstr(status_y, right_status_x, pos_info, curses.color_pair(1))
        
        if vim_status_str:
            right_status_x -= len(vim_status_str)
            self.safe_addstr(status_y, right_status_x, vim_status_str, curses.color_pair(1))

    def draw_tab_bar(self):
        """Draws the tab bar at the top of the screen"""
        self.safe_addstr(0, 0, " " * self.width, curses.color_pair(10))
        current_x = 0
        for i, tab in enumerate(self.tabs):
            name = os.path.basename(tab.filename) if tab.filename else "untitled"
            mod = "*" if tab.modified else ""

            git_mod = ""
            if tab.git_status == 'M': git_mod = "~"
            elif tab.git_status == 'A': git_mod = "+"

            display = f" {i+1}:{name}{mod}{git_mod} "
            
            pair = curses.color_pair(14) if i == self.active_tab_idx else curses.color_pair(15)
            self.safe_addstr(0, current_x, display, pair)
            current_x += len(display)
            if current_x >= self.width: break

    def draw_breadcrumb(self):
        """Draws the breadcrumb bar below the header"""
        if not self.config.get("show_breadcrumb", True):
            return

        breadcrumb_y = self.tab_bar_height + self.header_height

        path_str = self.filename or "untitled"
        
        # パスを読みやすくする
        home = os.path.expanduser("~")
        if self.filename and self.filename.startswith(home):
            path_str = os.path.join("~", os.path.relpath(self.filename, home))

        path_parts = path_str.split(os.sep)
        breadcrumb_text = " › ".join(path_parts)

        symbol = self._get_current_symbol()
        if symbol:
            breadcrumb_text += f" › {symbol}"

        # 描画属性を新しいカラーペアに設定
        breadcrumb_attr = curses.color_pair(18)
        
        # 背景をクリアし、テキストを描画
        self.safe_addstr(breadcrumb_y, 0, " " * self.width, breadcrumb_attr)
        self.safe_addstr(breadcrumb_y, 0, f" {truncate_to_width(breadcrumb_text, self.width - 2)}", breadcrumb_attr)

    def move_cursor(self, y, x, update_desired_x=False, check_bounds=False):
        new_y = max(0, min(y, len(self.buffer) - 1))
        line_len = len(self.buffer[new_y])
        new_x = max(0, min(x, line_len))
        
        if check_bounds:
            if new_x > line_len: new_x = line_len
            if new_y >= len(self.buffer): new_y = max(0, len(self.buffer) - 1)
        
        self.cursor_y = new_y
        self.cursor_x = new_x
        if update_desired_x: self.desired_x = self.cursor_x

        edit_height = self.get_edit_height()
        
        # 縦スクロール調整
        if self.cursor_y < self.scroll_offset:
            self.scroll_offset = self.cursor_y
        elif self.cursor_y >= self.scroll_offset + edit_height:
            self.scroll_offset = self.cursor_y - edit_height + 1

        # 横スクロール調整 (nano風: カーソルが画面端に行くとスクロール)
        edit_w = self.get_edit_rect()[3]
        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        actual_edit_w = edit_w - linenum_width

        if self.cursor_x < self.col_offset:
            self.col_offset = self.cursor_x
        elif self.cursor_x >= self.col_offset + actual_edit_w:
            # 右端に到達した場合、見える範囲を右にシフト
            self.col_offset = self.cursor_x - actual_edit_w + 1

    def _update_clipboard(self, lines, is_line=False):
        """内部クリップボードとシステムクリップボードを更新する"""
        self.clipboard = lines
        self.vim_clipboard_type = 'line' if is_line else 'char'
        text = "\n".join(lines)
        if is_line and not text.endswith('\n'):
            text += '\n'
        self._set_system_clipboard(text)

    def _sync_from_system_clipboard(self):
        """システムクリップボードから内部クリップボードを同期する"""
        sys_clip = self._get_system_clipboard()
        if sys_clip is not None:
            if sys_clip == "":
                self.clipboard = []
            else:
                self.clipboard = sys_clip.splitlines()
                if sys_clip.endswith('\n'):
                    self.clipboard.append('')
                    self.vim_clipboard_type = 'line'
                else:
                    self.vim_clipboard_type = 'char'
        return self.clipboard

    def _set_system_clipboard(self, text):
        """システムクリップボードにテキストを設定する"""
        system = platform.system()
        try:
            if system == "Windows":
                # PowerShellを使用してUTF-8対応で設定
                subprocess.run(['powershell.exe', '-NoProfile', '-Command', 
                                '[Console]::InputEncoding = [System.Text.Encoding]::UTF8; $input | Set-Clipboard'], 
                               input=text.encode('utf-8'), check=True, capture_output=True)
            elif system == "Darwin":
                subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True, capture_output=True)
            elif system == "Linux":
                # Wayland (wl-copy) -> xclip -> xsel
                try:
                    subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True, capture_output=True)
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run(['xsel', '--clipboard', '--input'], input=text.encode('utf-8'), check=True, capture_output=True)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        # WSL support: try powershell.exe or clip.exe
                        try:
                            subprocess.run(['powershell.exe', '-NoProfile', '-Command', 
                                            '[Console]::InputEncoding = [System.Text.Encoding]::UTF8; $input | Set-Clipboard'], 
                                           input=text.encode('utf-8'), check=True, capture_output=True)
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            try:
                                subprocess.run(['clip.exe'], input=text.encode('utf-8'), check=True, capture_output=True)
                            except (subprocess.CalledProcessError, FileNotFoundError):
                                if hasattr(self, 'set_status'):
                                    self.set_status("Clipboard tool (wl-copy/xclip/xsel/powershell/clip) not found.", timeout=3)
        except Exception as e:
            if hasattr(self, 'set_status'):
                self.set_status(f"Clipboard Error: {e}", timeout=3)

    def _get_system_clipboard(self):
        """システムクリップボードからテキストを取得する"""
        system = platform.system()
        try:
            if system == "Windows":
                # powershellを使用。UTF-8出力で-Rawで改行などを保持。
                out = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', 
                                              '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw'], 
                                             text=False, stderr=subprocess.DEVNULL)
                return out.decode('utf-8').replace('\r\n', '\n')
            elif system == "Darwin":
                return subprocess.check_output(['pbpaste'], text=True, stderr=subprocess.DEVNULL).replace('\r\n', '\n')
            elif system == "Linux":
                # Wayland (wl-paste) -> xclip -> xsel
                try:
                    return subprocess.check_output(['wl-paste', '--no-newline'], text=True, stderr=subprocess.DEVNULL).replace('\r\n', '\n')
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
                try:
                    return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], text=True, stderr=subprocess.DEVNULL).replace('\r\n', '\n')
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        return subprocess.check_output(['xsel', '--clipboard', '--output'], text=True, stderr=subprocess.DEVNULL).replace('\r\n', '\n')
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        # WSL support: try powershell.exe
                        try:
                            out = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', 
                                                          '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw'], 
                                                         text=False, stderr=subprocess.DEVNULL)
                            return out.decode('utf-8').replace('\r\n', '\n')
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            return None
        except Exception:
            return None

    def perform_copy(self):
        sel = self.get_selection_range()
        if not sel:
            self.status_message = "No selection to copy."
            return
        start, end = sel
        lines = []
        if start[0] == end[0]:
            lines.append(self.buffer.lines[start[0]][start[1]:end[1]])
        else:
            lines.append(self.buffer.lines[start[0]][start[1]:])
            for i in range(start[0] + 1, end[0]):
                lines.append(self.buffer.lines[i])
            lines.append(self.buffer.lines[end[0]][:end[1]])
        
        # 選択範囲全体を1行としてコピーした場合（末尾が空文字なら行単位扱い）
        is_line = len(lines) > 1 and lines[-1] == ''
        self._update_clipboard(lines, is_line)
        self.status_message = f"Copied {len(lines) if not is_line else len(lines)-1} lines."
        self.mark_pos = None

    def perform_cut(self):
        self.save_history()
        sel = self.get_selection_range()
        if not sel:
            if len(self.buffer) > 0:
                line_content = self.buffer.lines.pop(self.cursor_y)
                if not self.buffer.lines: self.buffer.lines = [""]
                self.move_cursor(self.cursor_y, 0)
                self.modified = True
                self.set_status("Cut line.", timeout=2)
                self._update_clipboard([line_content], is_line=True)
            return

        self.perform_copy()
        start, end = sel
        if start[0] == end[0]:
            line = self.buffer.lines[start[0]]
            self.buffer.lines[start[0]] = line[:start[1]] + line[end[1]:]
        else:
            line_start = self.buffer.lines[start[0]][:start[1]]
            line_end = self.buffer.lines[end[0]][end[1]:]
            del self.buffer.lines[start[0]+1:end[0]+1]
            self.buffer.lines[start[0]] = line_start + line_end
        self.move_cursor(start[0], start[1])
        self.mark_pos = None
        self.modified = True
        self.set_status("Cut selection.", timeout=2)

    def perform_paste(self):
        # システムクリップボードとの同期を試みる
        self._sync_from_system_clipboard()

        if not self.clipboard:
            self.status_message = "Clipboard empty."
            return
        
        self.save_history()
        current_line = self.buffer.lines[self.cursor_y]
        prefix = current_line[:self.cursor_x]
        suffix = current_line[self.cursor_x:]
        
        if len(self.clipboard) == 1:
            new_line = prefix + self.clipboard[0] + suffix
            self.buffer.lines[self.cursor_y] = new_line
            self.move_cursor(self.cursor_y, self.cursor_x + len(self.clipboard[0]), update_desired_x=True)
        else:
            self.buffer.lines[self.cursor_y] = prefix + self.clipboard[0]
            for i in range(1, len(self.clipboard) - 1):
                self.buffer.lines.insert(self.cursor_y + i, self.clipboard[i])
            self.buffer.lines.insert(self.cursor_y + len(self.clipboard) - 1, self.clipboard[-1] + suffix)
            new_y = self.cursor_y + len(self.clipboard) - 1
            new_x = len(self.clipboard[-1])
            self.move_cursor(new_y, new_x, update_desired_x=True)
            
        self.modified = True
        self.set_status("Pasted from system clipboard.", timeout=2)

    def _handle_bracketed_paste(self):
        """ブラケットペーストモードでの入力を処理する"""
        text = ""
        self.stdscr.nodelay(True)
        start_time = time.time()
        while time.time() - start_time < 2.0: # 2秒タイムアウト
            try:
                ch = self.stdscr.get_wch()
                if isinstance(ch, str):
                    text += ch
                    if text.endswith("\x1b[201~"):
                        text = text[:-6]
                        break
                start_time = time.time() # 入力がある間はタイムアウトをリセット
            except curses.error:
                time.sleep(0.01)
        self.stdscr.nodelay(False)
        
        if text:
            # 改行コードの正規化
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            self._insert_text_at_cursor(text)

    def _insert_text_at_cursor(self, text):
        """カーソル位置にテキストを挿入する（自動インデントなし）"""
        if not text: return
        self.save_history()
        lines = text.split('\n')
        
        current_line = self.buffer.lines[self.cursor_y]
        prefix = current_line[:self.cursor_x]
        suffix = current_line[self.cursor_x:]
        
        if len(lines) == 1:
            self.buffer.lines[self.cursor_y] = prefix + lines[0] + suffix
            self.move_cursor(self.cursor_y, self.cursor_x + len(lines[0]), update_desired_x=True)
        else:
            self.buffer.lines[self.cursor_y] = prefix + lines[0]
            for i in range(1, len(lines) - 1):
                self.buffer.lines.insert(self.cursor_y + i, lines[i])
            self.buffer.lines.insert(self.cursor_y + len(lines) - 1, lines[-1] + suffix)
            self.move_cursor(self.cursor_y + len(lines) - 1, len(lines[-1]), update_desired_x=True)
            
        self.modified = True
        self.set_status(f"Pasted {len(lines)} lines from terminal.", timeout=2)

    def toggle_comment(self):
        if not self.buffer.lines: return
        
        # Get comment symbol
        rules = self.current_syntax_rules
        symbol = None
        if rules:
            symbol = rules.get("line_comment")
        
        if not symbol:
            symbol = self._prompt_for_input("Comment symbol: ")
            if not symbol:
                self.set_status("Comment aborted.", timeout=2)
                return
            # Cache it in the current syntax rules for the session
            if self.current_tab.current_syntax_rules is None:
                self.current_tab.current_syntax_rules = {"line_comment": symbol}
            else:
                self.current_tab.current_syntax_rules["line_comment"] = symbol
            rules = self.current_tab.current_syntax_rules

        self.save_history()
        sel = self.get_selection_range()
        if sel:
            start, end = sel
            start_y, end_y = start[0], end[0]
            # If selection ends at the beginning of a line, don't include that line
            if end[1] == 0 and end_y > start_y:
                end_y -= 1
        else:
            start_y = end_y = self.cursor_y

        # Determine if we should comment or uncomment
        # Logic: if any line is NOT commented, comment all. Else uncomment all.
        pattern = re.compile(r'^\s*' + re.escape(symbol))
        any_not_commented = False
        for y in range(start_y, end_y + 1):
            if not pattern.match(self.buffer.lines[y]) and self.buffer.lines[y].strip():
                any_not_commented = True
                break
        
        for y in range(start_y, end_y + 1):
            line = self.buffer.lines[y]
            if not line.strip(): continue # Skip empty lines

            if any_not_commented:
                # Commenting: insert symbol after leading whitespace
                m = re.match(r'^(\s*)', line)
                indent_len = len(m.group(1)) if m else 0
                self.buffer.lines[y] = line[:indent_len] + symbol + line[indent_len:]
                if y == self.cursor_y and self.cursor_x >= indent_len:
                    self.cursor_x += len(symbol)
            else:
                # Uncommenting: remove symbol
                match = pattern.match(line)
                if match:
                    # Find where the symbol actually starts (match.end() - len(symbol))
                    symbol_start = match.end() - len(symbol)
                    self.buffer.lines[y] = line[:symbol_start] + line[match.end():]
                    if y == self.cursor_y and self.cursor_x > symbol_start:
                        self.cursor_x = max(symbol_start, self.cursor_x - len(symbol))
        
        self.modified = True
        self.desired_x = self.cursor_x
        self.set_status(("Commented" if any_not_commented else "Uncommented") + " lines.")

    def delete_line(self):
        if not self.buffer.lines: return
        self.save_history()
        if len(self.buffer.lines) > 1:
            del self.buffer.lines[self.cursor_y]
            self.move_cursor(self.cursor_y, 0)
        elif self.buffer.lines and len(self.buffer.lines[0]) > 0:
             self.buffer.lines[0] = ""
             self.move_cursor(0, 0)
        self.modified = True
        self.status_message = "Deleted line."

    def set_status(self, msg, timeout=3):
        self.status_message = msg
        try:
            self.status_expire_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        except Exception:
            self.status_expire_time = None

    def save_file(self):
        if not self.filename:
            fn = self._prompt_for_input("Filename: ")
            if fn is not None and fn.strip():
                self.filename = fn.strip()
            else:
                self.set_status("Aborted", timeout=2)
                return

        try:
            if os.path.exists(self.filename):
                try:
                    setting_dir = get_config_dir()
                    backup_subdir = self.config.get("backup_subdir", "backup")
                    backup_dir = os.path.join(setting_dir, backup_subdir)

                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir, exist_ok=True)

                    safe_filename = self.filename.replace(os.path.sep, '_').replace(':', '_')
                    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    bak_name = os.path.join(backup_dir, f"{safe_filename}.{timestamp}.bak")

                    shutil.copy2(self.filename, bak_name)

                    backup_limit = self.config.get("backup_count", 5)
                    backup_pattern = os.path.join(backup_dir, f"{safe_filename}.*.bak")
                    existing_backups = sorted(glob.glob(backup_pattern))

                    if len(existing_backups) > backup_limit:
                        for old_backup in existing_backups[:-backup_limit]:
                            try: os.remove(old_backup)
                            except OSError: pass
                except (IOError, OSError) as e:
                    self.set_status(f"Backup warning: {e}", timeout=4)

            tmp_name = f"{self.filename}.tmp"
            with open(tmp_name, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.buffer.lines))
            os.replace(tmp_name, self.filename)
            
            try: 
                self.file_mtime = os.path.getmtime(self.filename)
            except OSError: 
                self.file_mtime = None
            
            self.current_syntax_rules = self.detect_syntax(self.filename)
            self.modified = False
            self._update_tab_git_status(self.current_tab)
            self.save_history(init=True)
            self.set_status(f"Saved {len(self.buffer)} lines to {self.filename}.", timeout=3)
        except (IOError, OSError) as e:
            self.set_status(f"Error saving file: {e}", timeout=5)

    def select_all(self):
        if self.mark_pos:
            self.mark_pos = None
            self.set_status("Selection cleared.", timeout=2)
        else:
            last_y = len(self.buffer) - 1
            last_x = len(self.buffer[last_y]) if self.buffer.lines else 0
            self.mark_pos = (0, 0)
            self.move_cursor(last_y, last_x, update_desired_x=True)
            self.set_status("Selected all.", timeout=2)

    def goto_line(self):
        s = self._prompt_for_input("Goto line: ")
        if s is not None:
            try:
                n = int(s.strip())
                self.move_cursor(max(0, min(n - 1, len(self.buffer) - 1)), 0, update_desired_x=True)
                self.set_status(f"Goto {n}", timeout=2)
            except ValueError:
                self.set_status("Invalid line number.", timeout=2)
        else:
            self.set_status("Goto aborted.", timeout=2)

    def toggle_explorer(self):
        if self.show_explorer:
            if self.active_pane == 'explorer':
                self.show_explorer = False
                self.active_pane = 'editor'
            else:
                self.active_pane = 'explorer'
        else:
            self.show_explorer = True
            self.active_pane = 'explorer'
        self.redraw_screen()

    def toggle_terminal(self):
        if self.show_terminal:
            if self.active_pane == 'terminal':
                self.show_terminal = False
                self.active_pane = 'editor'
            else:
                self.active_pane = 'terminal'
        else:
            self.show_terminal = True
            self.active_pane = 'terminal'
        self.redraw_screen()

    def toggle_relative_linenum(self):
        """相対行数表示のオン/オフを切り替える"""
        current_state = self.config.get("show_relative_linenum", False)
        self.config["show_relative_linenum"] = not current_state
        status = "ON" if not current_state else "OFF"
        self.set_status(f"Relative line numbers: {status}", timeout=2)

    def run_build_command(self):
        if not self.filename:
            self.set_status("Cannot run: No filename provided.")
            return
            
        # Run前に自動保存
        if self.modified:
            self.save_file()
            
        ext = os.path.splitext(self.filename)[1].lower()
        base = os.path.splitext(self.filename)[0]

        cmd_template = self.build_commands.get(ext)

        if cmd_template:
            cmd = cmd_template.format(filename=self.filename, base=base)
        else:
            self.set_status(f"No build command defined for {ext}")
            return

        if not self.show_terminal:
            self.toggle_terminal()
            
        self.active_pane = 'terminal'
        self.terminal.write_input(cmd + "\n")

    def enter_command_mode(self):
        """コマンド入力モードを開始する"""
        command_str = self._prompt_for_input(":")
        if command_str is not None:
            self.execute_command(command_str)

    def execute_command(self, command_str):
        """コマンド文字列を解釈して実行する"""
        if not command_str.strip():
            return
            
        parts = command_str.strip().split()
        cmd = parts[0]
        args = parts[1:]

        if cmd in self.commands:
            try:
                # コマンドに対応するメソッドを引数付きで呼び出す
                self.commands[cmd](*args)
            except Exception as e:
                self.set_status(f"Command error: {e}", timeout=4)
        else:
            self.set_status(f"Unknown command: {cmd}", timeout=3)

    # --- Command Methods ---
    def _command_open(self, filename=None):
        """'open'コマンド: 新しいファイルを開く"""
        if not filename:
            self.set_status("Usage: open <filename>", timeout=3)
            return

        # すでに開いているかチェック
        abs_path = os.path.abspath(filename)
        for tab in self.tabs:
            if tab.filename and os.path.abspath(tab.filename) == abs_path:
                self.active_tab_idx = self.tabs.index(tab)
                self.set_status(f"Switched to already open file: {filename}", timeout=3)
                return

        # 新しいタブで開く
        new_lines, err = self.load_file(filename)
        if not err:
            mtime = None
            try: mtime = os.path.getmtime(filename)
            except OSError: pass
            rules = self.detect_syntax(filename)
            new_tab = EditorTab(Buffer(new_lines), filename, rules, mtime)
            self._update_tab_git_status(new_tab)
            self.tabs.append(new_tab)
            self.active_tab_idx = len(self.tabs) - 1
            self.save_history(init=True)
            self.set_status(f"Opened {filename}", timeout=3)
        else:
            self.set_status(err, timeout=4)

    def _command_save(self):
        """'save'コマンド: 現在のファイルを保存"""
        self.save_file()

    def _command_saveas(self, filename=None):
        """'saveas'コマンド: 名前を付けて保存"""
        if not filename:
            self.set_status("Usage: saveas <filename>", timeout=3)
            return
        # Set the new filename for the current tab and then save.
        self.filename = filename
        self.save_file()

    def _command_explorer_width(self, width=None):
        """'expw'コマンド: エクスプローラーの幅を設定"""
        if width is None:
            self.set_status(f"Current explorer_width: {self.explorer_width}", timeout=3)
            return
        try:
            self.explorer_width = int(width)
            self.config["explorer_width"] = self.explorer_width
            self.set_status(f"Explorer width set to {self.explorer_width}")
            self.redraw_screen()
        except ValueError:
            self.set_status("Invalid width value.", timeout=3)

    def _command_terminal_height(self, height=None):
        """'termh'コマンド: ターミナルの高さを設定"""
        if height is None:
            self.set_status(f"Current terminal_height: {self.terminal_height}", timeout=3)
            return
        try:
            self.terminal_height = int(height)
            self.config["terminal_height"] = self.terminal_height
            self.set_status(f"Terminal height set to {self.terminal_height}")
            self.redraw_screen()
        except ValueError:
            self.set_status("Invalid height value.", timeout=3)

    def _command_undo(self, *args):
        """'undo'コマンド: 元に戻す"""
        self.undo()

    def _command_redo(self, *args):
        """'redo'コマンド: やり直し"""
        self.redo()

    def _command_goto(self, line=None, *args):
        """'goto'コマンド: 指定行へ移動"""
        if line is None:
            self.goto_line()
        else:
            try:
                n = int(line)
                self.move_cursor(max(0, min(n - 1, len(self.buffer) - 1)), 0, update_desired_x=True)
                self.set_status(f"Goto {n}", timeout=2)
            except ValueError:
                self.set_status("Invalid line number.", timeout=2)

    def _command_copy(self, *args):
        """'copy'コマンド: 選択範囲をコピー"""
        self.perform_copy()

    def _command_paste(self, *args):
        """'paste'コマンド: クリップボードから貼り付け"""
        self.perform_paste()

    def _command_close(self, *args):
        """'close'コマンド: 現在のタブを閉じる"""
        if self.close_current_tab():
             # This special case should not be hit from command mode,
             # as the loop would exit.
             pass

    def _command_find(self, query=None, *args):
        """'find'コマンド: 検索を開始"""
        self.search_mode = True
        self.search_input_focused = "search"
        if query:
            self.search_query = query
            self._find_all_matches()
        else:
            self.set_status("Search mode enabled. Type query below.", timeout=3)

    def _command_replace(self, old=None, new=None, *args):
        """'replace'コマンド: 置換を開始"""
        self.search_mode = True
        if old:
            self.search_query = old
            self.search_input_focused = "replace"
            if new:
                self.replace_query = new
            self._find_all_matches()
        else:
            self.search_input_focused = "search"
            self.set_status("Replace mode enabled.", timeout=3)

    def _command_delcomm(self, *args):
        """'delcomm' command: Delete all comments in the current buffer."""
        if not self.buffer.lines: return

        self.save_history()
        rules = self.current_syntax_rules
        
        # We try to use the 'comments' regex if available
        comment_regex = None
        if rules and "comments" in rules:
            comment_regex = rules["comments"]
        
        # Fallback to line_comment
        if not comment_regex:
            symbol = rules.get("line_comment") if rules else None
            if not symbol:
                symbol = self._prompt_for_input("Comment symbol (e.g. #): ")
                if not symbol:
                    self.set_status("Operation cancelled.", timeout=2)
                    return
                # Cache it
                if self.current_syntax_rules is None:
                    self.current_syntax_rules = {"line_comment": symbol}
                else:
                    self.current_syntax_rules["line_comment"] = symbol
            comment_regex = re.escape(symbol) + ".*"

        try:
            regex = re.compile(comment_regex)
        except Exception as e:
            self.set_status(f"Invalid comment pattern: {e}", timeout=3)
            return

        new_lines = []
        count = 0
        for line in self.buffer.lines:
            new_line = regex.sub('', line).rstrip()
            if new_line != line.rstrip():
                count += 1
            
            # If the line was entirely a comment (or empty), and we're not keeping empty lines from comments
            if line.strip() and not new_line.strip():
                continue
                
            new_lines.append(new_line)
            
        if not new_lines:
            new_lines = [""]
            
        self.buffer.lines = new_lines
        self.modified = True
        self.set_status(f"Deleted comments from {count} lines.", timeout=3)

    def _command_quit(self):
        """'quit'コマンド: エディタを終了する"""
        # Loop until all tabs are closed or the user cancels.
        while self.tabs:
            result = self.close_current_tab()

            if result is None:
                # User cancelled the save prompt. Abort quitting.
                break

            if result is True:
                # This was the last tab, editor should exit.
                self.should_exit = True
                break
            
            # if result is False, a tab was closed, but more remain.
            # The loop will continue.
    
    def _command_new(self):
        """'new'コマンド: 新しい空のタブを作成"""
        self.new_tab()

    def _command_template(self, *args):
        """'template'コマンド: 言語名でテンプレートを挿入するか、選択画面を表示する"""
        lang = args[0] if args else None
        templates = self.config.get("templates", {})
        if not templates:
            self.set_status("テンプレートが定義されていません。", timeout=3)
            return

        if lang:
            if lang in templates:
                self.insert_text(templates[lang])
                self.set_status(f"'{lang}' テンプレートを挿入しました。", timeout=3)
            else:
                self.set_status(f"'{lang}' テンプレートが見つかりません。", timeout=3)
        else:
            self._select_and_insert_template()

    def _command_macro(self, filename=None, *args):
        """'macro'コマンド: .caffeine マクロファイルを実行する"""
        if not filename:
            self.set_status("Usage: macro <filename>", timeout=3)
            return
        self.macro_manager.run_file(filename)

    def _command_set(self, key=None, value=None):
        """'set'コマンド: 設定値を変更"""
        if not key or value is None:
            self.set_status("Usage: set <key> <value>", timeout=3)
            return
        
        if key in self.config:
            current_type = type(self.config[key])
            try:
                # 型を合わせて変換
                if current_type == bool:
                    new_value = value.lower() in ['true', '1', 'yes']
                else:
                    new_value = current_type(value)
                
                self.config[key] = new_value
                self.set_status(f"Set {key} = {new_value}", timeout=3)
                # Some settings require redraw or re-init
                if key == 'tab_width':
                    self.redraw_screen()
                elif key == 'explorer_width':
                    self.explorer_width = new_value
                    self.redraw_screen()
                elif key == 'terminal_height':
                    self.terminal_height = new_value
                    self.redraw_screen()
                if key in self.config.get("colors", {}):
                    self.init_colors()
                    self.redraw_screen()

            except (ValueError, TypeError):
                self.set_status(f"Invalid value type for '{key}'. Expected {current_type.__name__}.", timeout=4)
        else:
            self.set_status(f"Unknown setting: '{key}'", timeout=3)

    # --- Predictive Text Methods ---
    def _update_suggestions(self):
        """カーソル位置に基づいて予測変換の候補を更新する"""
        if not self.config.get("enable_predictive_text", False):
            self.suggestion_active = False
            return

        line = self.buffer.lines[self.cursor_y]
        if self.cursor_x == 0:
            self.suggestion_active = False
            return

        # Find the start of the current word
        start_x = self.cursor_x
        # 英数字かアンダースコアを単語構成文字とみなす
        while start_x > 0 and (line[start_x - 1].isalnum() or line[start_x - 1] == '_'):
            start_x -= 1
        
        current_word = line[start_x:self.cursor_x]

        if len(current_word) < 2: # 2文字以上入力されたら候補を探す
            self.suggestion_active = False
            return

        # Scan buffer for suggestions
        candidates = set()
        # \b is word boundary, re.escape escapes special characters in the word
        pattern = re.compile(r'\b' + re.escape(current_word) + r'\w*\b')
        for buffer_line in self.buffer.lines:
            for match in pattern.finditer(buffer_line):
                # 自分自身は候補に含めない
                if match.group(0) != current_word:
                    candidates.add(match.group(0))
        
        # Sort and limit suggestions
        sorted_candidates = sorted(list(candidates))
        
        if sorted_candidates:
            self.suggestions = sorted_candidates[:5] # 最大5件まで
            self.suggestion_active = True
            self.selected_suggestion_idx = 0
            self.suggestion_word_start = (self.cursor_y, start_x)
        else:
            self.suggestion_active = False
            self.suggestions = []
            self.suggestion_word_start = None

    def _apply_suggestion(self):
        """選択された予測候補を適用する"""
        if not self.suggestion_active or not self.suggestions:
            return

        y, start_x = self.suggestion_word_start
        if y != self.cursor_y:
            self.suggestion_active = False
            return

        line = self.buffer.lines[y]
        current_word = line[start_x:self.cursor_x]
        
        selected_suggestion = self.suggestions[self.selected_suggestion_idx]
        
        # 候補が現在の単語と一致しなくなったらキャンセル
        if not selected_suggestion.startswith(current_word):
            self.suggestion_active = False
            return
            
        text_to_insert = selected_suggestion[len(current_word):]
        
        self.save_history()
        
        # 単語の残りを挿入
        prefix = line[:self.cursor_x]
        suffix = line[self.cursor_x:]
        self.buffer.lines[y] = prefix + text_to_insert + suffix
        
        # カーソルを単語の末尾に移動
        self.move_cursor(y, self.cursor_x + len(text_to_insert), update_desired_x=True)
        self.modified = True
        
        # 候補表示をリセット
        self.suggestion_active = False
        self.suggestions = []
        self.suggestion_word_start = None

    # -----------------------------

    def main_loop(self):
        while not self.should_exit:
            self.stdscr.erase()
            self.height, self.width = self.stdscr.getmaxyx()
            
            if self.filename and os.path.exists(self.filename):
                try:
                    mtime = os.path.getmtime(self.filename)
                    if self.file_mtime and mtime != self.file_mtime:
                        self.set_status("File changed on disk.", timeout=5)
                        self.file_mtime = mtime
                except OSError:
                    pass
            
            if self.show_terminal and self.terminal:
                if self.terminal.read_output():
                    pass

            self.draw_ui()
            self.draw_content()
            self._draw_suggestions()
            
            if self.active_pane == 'editor':
                linenum_width = max(4, len(str(len(self.buffer)))) + 1
                edit_y, edit_x, _, _ = self.get_edit_rect()
                screen_y = self.cursor_y - self.scroll_offset + edit_y
                
                # カーソル表示位置の計算（横スクロール考慮）
                screen_x = edit_x + linenum_width
                
                # col_offset（左端）からcursor_xまでの文字幅を計算して加算
                if self.cursor_y < len(self.buffer):
                    # col_offsetより左にある場合は画面外なので計算しない（ただしロジック上はmove_cursorでクランプされているはず）
                    # cursor_xがcol_offset以上のときのみ描画位置を計算
                    if self.cursor_x >= self.col_offset:
                        visible_segment = self.buffer.lines[self.cursor_y][self.col_offset : self.cursor_x]
                        for char in visible_segment:
                            screen_x += get_char_width(char)
                
                edit_height = self.get_edit_height()
                if edit_y <= screen_y < edit_y + edit_height:
                    try: self.stdscr.move(screen_y, min(screen_x, self.width - 1))
                    except curses.error: pass
                curses.curs_set(1)
            elif self.active_pane == 'explorer':
                curses.curs_set(0)
            elif self.active_pane == 'terminal':
                ty, tx, th, tw = self.get_terminal_rect()
                try: self.stdscr.move(ty + th - 1, tx + 2)
                except curses.error: pass
                curses.curs_set(1)
            elif self.active_pane == 'plugin_manager':
                curses.curs_set(0)
            elif self.active_pane == 'settings_manager':
                curses.curs_set(0)
            elif self.active_pane == 'keybinding_settings':
                curses.curs_set(0)
            elif self.active_pane == 'full_screen_explorer':
                curses.curs_set(0)

            try:
                if self.show_terminal:
                    self.stdscr.timeout(50) 
                else:
                    self.stdscr.timeout(100)
                    
                key_in = self.stdscr.get_wch()
                self.stdscr.timeout(-1)
                
                # ブラケットペースト開始シーケンス \x1b[200~ の検知
                if key_in == '\x1b' or key_in == 27:
                    self.stdscr.nodelay(True)
                    paste_detected = False
                    consumed = []
                    try:
                        seq = ""
                        for _ in range(5):
                            ch = self.stdscr.get_wch()
                            consumed.append(ch)
                            if isinstance(ch, str):
                                seq += ch
                            else:
                                break
                            
                            if seq == "[200~":
                                self._handle_bracketed_paste()
                                paste_detected = True
                                break
                            elif not "[200~".startswith(seq):
                                break
                    except curses.error:
                        pass
                    
                    self.stdscr.nodelay(False)
                    if paste_detected:
                        continue
                    else:
                        # 読みすぎた文字をキューに戻す
                        for ch in reversed(consumed):
                            try: curses.unget_wch(ch)
                            except curses.error: pass

            except KeyboardInterrupt:
                key_in = CTRL_C
            except curses.error: 
                key_in = -1
            
            key_code = -1
            char_input = None

            if isinstance(key_in, int):
                key_code = key_in
            elif isinstance(key_in, str):
                if len(key_in) == 1:
                    code = ord(key_in)
                    if code < 32 or code == 127:
                        key_code = code
                    else:
                        char_input = key_in
            
            if key_code == -1 and char_input is None: continue

            if key_code == CTRL_F:
                self.toggle_explorer()
                continue
            elif key_code == CTRL_N:
                self.toggle_terminal()
                continue
            elif key_code == CTRL_T:
                self._select_and_insert_template()
                continue
            elif key_code == CTRL_B:
                self.run_build_command()
                continue
            elif key_code == CTRL_S:
                self.new_tab()
                continue
            elif key_code == CTRL_V:
                self.perform_paste()
                continue
            elif key_code == CTRL_L:
                self.next_tab()
                continue

            
            # --- Handle Plugin Manager Input ---
            if self.active_pane == 'plugin_manager':
                if key_code == curses.KEY_UP:
                    self.plugin_manager.navigate(-1)
                elif key_code == curses.KEY_DOWN:
                    self.plugin_manager.navigate(1)
                elif key_code in (KEY_ENTER, KEY_RETURN, ord(' ')):
                    msg = self.plugin_manager.toggle_current()
                    if msg: self.set_status(msg, timeout=4)
                elif key_code == KEY_ESC:
                    self.active_pane = 'editor'
                continue

            # --- Handle Keybinding Settings Input ---
            if self.active_pane == 'keybinding_settings':
                if key_code == curses.KEY_UP:
                    self.keybinding_settings_manager.navigate(-1)
                elif key_code == curses.KEY_DOWN:
                    self.keybinding_settings_manager.navigate(1)
                elif key_code in (KEY_ENTER, KEY_RETURN, ord(' ')):
                    msg = self.keybinding_settings_manager.toggle_current()
                    if msg: self.set_status(msg, timeout=3)
                elif key_code == KEY_ESC:
                    self.active_pane = 'settings_manager' # Go back to the main settings
                continue

            # --- Handle Settings Manager Input ---
            if self.active_pane == 'settings_manager':
                if self.settings_manager.edit_mode:
                    if key_code in (KEY_ENTER, KEY_RETURN, KEY_ESC, KEY_BACKSPACE, KEY_BACKSPACE2) or (char_input and ord(char_input) >= 32):
                       res = self.settings_manager.handle_edit_input(key_code if key_code != -1 else ord(char_input))
                       if res: self.set_status(res, timeout=3)
                else:
                    if key_code == curses.KEY_UP:
                        self.settings_manager.navigate(-1)
                    elif key_code == curses.KEY_DOWN:
                        self.settings_manager.navigate(1)
                    elif key_code in (KEY_ENTER, KEY_RETURN):
                        self.settings_manager.start_edit(self)
                    elif key_code == ord(' '):
                        res = self.settings_manager.toggle_bool()
                        if res: self.set_status(res, timeout=3)
                    elif key_code == CTRL_O:
                        res = self.settings_manager.save_settings()
                        self.set_status(res, timeout=3)
                        # Ask to reload
                        if self._prompt_for_confirmation("Reload config to apply changes now? (y/n)"):
                            self.reload_config()

                    elif key_code == KEY_ESC:
                        self.active_pane = 'editor'
                continue
            
            if self.active_pane == 'full_screen_explorer':
                self._process_explorer_input(key_code, char_input)
                continue
            # -----------------------------------

            if self.active_pane == 'explorer':
                self._process_explorer_input(key_code, char_input)
                continue

            if self.search_mode:
                self._process_search_input(key_code, char_input)
                continue

            if self.active_pane == 'terminal':
                if key_code == KEY_ESC:
                    self.active_pane = 'editor'
                    continue
                
                if char_input:
                    self.terminal.write_input(char_input)
                elif key_code == KEY_ENTER or key_code == KEY_RETURN:
                    self.terminal.write_input("\n")
                elif key_code in (curses.KEY_BACKSPACE, KEY_BACKSPACE, KEY_BACKSPACE2):
                    self.terminal.write_input("\x7f") # DEL
                elif key_code == KEY_TAB:
                    self.terminal.write_input("\t")
                elif key_code == CTRL_C:
                    self.terminal.write_input("\x03")
                elif key_code == curses.KEY_UP: self.terminal.write_input("\x1b[A")
                elif key_code == curses.KEY_DOWN: self.terminal.write_input("\x1b[B")
                elif key_code == curses.KEY_RIGHT: self.terminal.write_input("\x1b[C")
                elif key_code == curses.KEY_LEFT: self.terminal.write_input("\x1b[D")
                
                continue

            if self.vim_mode and self.vim_state == 'insert' and key_code == KEY_ESC:
                self.vim_state = 'normal'
                continue

            if self.vim_mode and self.vim_state != 'insert' and self.active_pane == 'editor':
                self._process_vim_input(key_code, char_input)
                continue

            if key_code in self.plugin_key_bindings:
                try: self.plugin_key_bindings[key_code](self)
                except Exception as e: self.set_status(f"Plugin Error: {e}", timeout=5)
                continue

            # Block editing in read-only tabs, but allow navigation/closing
            if self.current_tab.read_only:
                if key_code not in (CTRL_X, CTRL_L, curses.KEY_UP, curses.KEY_DOWN,
                                    curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_PPAGE,
                                    curses.KEY_NPAGE):
                    self.set_status("This is a read-only buffer.", timeout=2)
                    continue

            if key_code == CTRL_D:
                self.show_diff()
            elif key_code == CTRL_C:
                self.perform_copy()
            elif key_code == CTRL_X:
                # Tab Close Logic
                if self.close_current_tab():
                    return
            elif key_code == CTRL_O: self.save_file()
            elif key_code == CTRL_W: 
                self.search_mode = not self.search_mode
                if self.search_mode:
                    self.search_input_focused = "search"
                else:
                    self.search_results = []
                    self.active_search_idx = -1
            elif key_code == CTRL_MARK:
                if self.mark_pos: 
                    self.mark_pos = None
                    self.set_status("Mark Unset", timeout=2)
                else: 
                    self.mark_pos = (self.cursor_y, self.cursor_x)
                    self.set_status("Mark Set", timeout=2)
            elif key_code == CTRL_G: self.goto_line()
            elif key_code == CTRL_A: self.select_all()
            elif key_code == CTRL_E: 
                self.move_cursor(self.cursor_y, len(self.buffer.lines[self.cursor_y]), update_desired_x=True)
            elif key_code == CTRL_SLASH: self.toggle_comment()
            elif key_code == CTRL_Y: self.delete_line()
            elif key_code == CTRL_P: self.enter_command_mode()
            elif key_code == CTRL_K: self.perform_cut()
            elif key_code == CTRL_U: self.toggle_relative_linenum()
            elif key_code == CTRL_Z: self.undo()
            elif key_code == CTRL_R: self.redo()
            elif key_code == curses.KEY_UP:
                if self.suggestion_active:
                    self.selected_suggestion_idx = (self.selected_suggestion_idx - 1 + len(self.suggestions)) % len(self.suggestions)
                else:
                    self.move_cursor(self.cursor_y - 1, self.desired_x)
            elif key_code == curses.KEY_DOWN:
                if self.suggestion_active:
                    self.selected_suggestion_idx = (self.selected_suggestion_idx + 1) % len(self.suggestions)
                else:
                    self.move_cursor(self.cursor_y + 1, self.desired_x)
            elif key_code == curses.KEY_LEFT:
                self.suggestion_active = False
                self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
            elif key_code == curses.KEY_RIGHT:
                self.suggestion_active = False
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
            elif key_code == curses.KEY_PPAGE:
                self.suggestion_active = False
                self.move_cursor(self.cursor_y - self.get_edit_height(), self.cursor_x, update_desired_x=True)
            elif key_code == curses.KEY_NPAGE:
                self.suggestion_active = False
                self.move_cursor(self.cursor_y + self.get_edit_height(), self.cursor_x, update_desired_x=True)
            elif key_code in (curses.KEY_BACKSPACE, KEY_BACKSPACE, KEY_BACKSPACE2):
                if self.mark_pos: self.perform_cut() 
                elif self.cursor_x > 0:
                    self.save_history()
                    line = self.buffer.lines[self.cursor_y]
                    self.buffer.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
                    self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
                    self.modified = True
                elif self.cursor_y > 0:
                    self.save_history()
                    prev_len = len(self.buffer.lines[self.cursor_y - 1])
                    self.buffer.lines[self.cursor_y - 1] += self.buffer.lines[self.cursor_y]
                    del self.buffer.lines[self.cursor_y]
                    self.move_cursor(self.cursor_y - 1, prev_len, update_desired_x=True)
                    self.modified = True
                self._update_suggestions()
            elif key_code == KEY_ENTER or key_code == KEY_RETURN:
                if self.suggestion_active:
                    self._apply_suggestion()
                    continue
                self.suggestion_active = False
                self.save_history()
                line = self.buffer.lines[self.cursor_y]
                indent = ""
                
                if self.config.get("auto_indent", True):
                    # ペースト検知のヒューリスティック：直後に別の入力（バースト）があるか確認
                    self.stdscr.nodelay(True)
                    try:
                        peek = self.stdscr.get_wch()
                        try: curses.unget_wch(peek)
                        except curses.error: pass
                        is_burst = True
                    except curses.error:
                        is_burst = False
                    self.stdscr.nodelay(False)

                    if not is_burst:
                        match = re.match(r'^(\s*)', line)
                        if match:
                            indent = match.group(1)

                self.buffer.lines.insert(self.cursor_y + 1, indent + line[self.cursor_x:])
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x]
                self.move_cursor(self.cursor_y + 1, len(indent), update_desired_x=True)
                self.modified = True
            elif key_code == KEY_TAB:
                if self.suggestion_active:
                    self._apply_suggestion()
                    continue
                self.save_history()
                tab_spaces = " " * self.config.get("tab_width", 4)
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + tab_spaces + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + len(tab_spaces), update_desired_x=True)
                self.modified = True
            
            elif char_input:
                self.save_history()
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + char_input + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
                self.modified = True
                self._update_suggestions()

def main(stdscr, start_time):
    os.environ.setdefault('ESCDELAY', '25')
    curses.raw()
    # ブラケットペーストモードを有効化
    sys.stdout.write("\x1b[?200h")
    sys.stdout.flush()

    fn = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        Editor(stdscr, fn, start_time=start_time).main_loop()
    except Exception as e:
        # Ensure curses is ended before printing
        curses.endwin()
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        # ブラケットペーストモードを無効化
        sys.stdout.write("\x1b[?200l")
        sys.stdout.flush()

def start_app():
    start_time = time.time()
    term = os.environ.get("TERM", "")
    if "ish" in term:
        # Attempt to make iSH compatible by setting a common TERM value
        os.environ['TERM'] = 'xterm'
    elif "dumb" in term:
        print("Caffee editor is not supported in 'dumb' terminal environments.", file=sys.stderr)
        return

    try:
        curses.wrapper(main, start_time)
    except curses.error as e:
        print(f"Failed to start Caffee editor due to a curses error: {e}", file=sys.stderr)
        print("Your terminal might not be fully compatible.", file=sys.stderr)
    except Exception as e:
        # Fallback for other exceptions
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    start_app()


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
import unicodedata  # 追加: 全角文字幅判定用

# --- 定数定義 (Key Codes) ---
CTRL_A = 1
CTRL_C = 3
CTRL_E = 5
CTRL_G = 7
CTRL_K = 11
CTRL_O = 15
CTRL_R = 18
CTRL_U = 21
CTRL_W = 23
CTRL_X = 24
CTRL_Y = 25
CTRL_Z = 26
CTRL_MARK = 30    # Ctrl+6 or Ctrl+^
CTRL_SLASH = 31   # Ctrl+/ (Unit Separator)
KEY_TAB = 9
KEY_ENTER = 10
KEY_RETURN = 13
KEY_BACKSPACE = 127
KEY_BACKSPACE2 = 8

# --- デフォルト設定 ---
EDITOR_NAME = "CAFFEE"
VERSION = "1.2.0" #unreleased now | Currently released latest version - 1.2.0

DEFAULT_CONFIG = {
    "tab_width": 4,
    "history_limit": 50,
    "use_soft_tabs": True,
    "backup_subdir": "backup",
    "backup_count": 5,
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
        "zenkaku_bg": "RED" # 全角スペース背景
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

# --- シンタックスハイライト定義 ---
# 拡張子ごとの簡易的な正規表現ルール
SYNTAX_RULES = {
    "python": {
        "extensions": [".py", ".pyw"],
        "keywords": r"\b(and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|not|or|pass|raise|return|try|while|with|yield|None|True|False|self)\b",
        "comments": r"#.*",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "javascript": {
        "extensions": [".js", ".json"],
        "keywords": r"\b(function|return|var|let|const|if|else|for|while|break|switch|case|default|import|export|true|false|null)\b",
        "comments": r"//.*",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "c_cpp": {
        "extensions": [".c", ".cpp", ".h", ".hpp"],
        "keywords": r"\b(int|float|double|char|void|if|else|for|while|return|struct|class|public|private|protected|include)\b",
        "comments": r"//.*",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "go": {
        "extensions": [".go"],
        # Go keywords + common types + built-in functions
        "keywords": r"\b(break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|true|false|nil|append|cap|close|complex|copy|delete|imag|len|make|new|panic|print|println|real|recover|bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr)\b",
        "comments": r"//.*",
        # Added backtick for raw strings
        "strings": r"(['\"`])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "html": {
        "extensions": [".html", ".htm"],
        # Tags and common attributes treated as keywords
        "keywords": r"\b(html|head|body|title|meta|link|script|style|div|span|p|h[1-6]|a|img|ul|ol|li|table|tr|td|th|form|input|button|label|select|option|textarea|br|hr|class|id|src|href|alt|type|value|name|width|height)\b",
        "comments": r"",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "markdown": {
        "extensions": [".md", ".markdown"],
        # Header (#) and List markers (-, *) -> Keyword Color
        "keywords": r"(^#+\s+.*)|(^\s*[\-\*+]\s+)",
        # Blockquote (>) -> Comment Color
        "comments": r"^>.*",
        # Inline code (`) and Bold (**) -> String Color
        "strings": r"(`[^`]+`|\*\*.*?\*\*)",
        # Link brackets [] -> Number Color
        "numbers": r"\[.*?\]"
    }
}


def get_config_dir():
    """設定ディレクトリのパスを取得"""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".caffee_setting")

def load_config():
    """設定ファイルを読み込み、デフォルト設定とマージする"""
    config = DEFAULT_CONFIG.copy()
    setting_dir = get_config_dir()
    setting_file = os.path.join(setting_dir, "setting.json")
    load_error = None

    try:
        os.makedirs(setting_dir, exist_ok=True)
    except OSError as e:
        load_error = f"Config dir error: {e}"

    if os.path.exists(setting_file):
        try:
            with open(setting_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 再帰的にマージしていないので、colorsだけ特別扱い
                if "colors" in user_config and isinstance(user_config["colors"], dict):
                    config["colors"].update(user_config["colors"])
                    del user_config["colors"]
                
                for key, value in user_config.items():
                    config[key] = value
        except (json.JSONDecodeError, OSError) as e:
            load_error = f"Config load error: {e}"
            
    return config, load_error

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

class Editor:
    def __init__(self, stdscr, filename=None, config=None, config_error=None):
        self.stdscr = stdscr
        self.filename = filename
        self.config = config if config else DEFAULT_CONFIG
        
        # 初期バッファ設定
        initial_lines, load_err = self.load_file(filename)
        self.buffer = Buffer(initial_lines)
        
        # カーソル・表示関連
        self.cursor_y = 0
        self.cursor_x = 0
        self.scroll_offset = 0
        self.desired_x = 0
        
        # レイアウト管理
        self.menu_height = 1
        self.status_height = 1
        self.header_height = 1
        
        # 状態管理
        self.status_message = ""
        self.status_expire_time = None
        self.modified = False
        self.clipboard = []
        
        # 選択モード (Mark)
        self.mark_pos = None
        
        # 履歴管理 (Undo/Redo用)
        self.history = []
        self.history_index = -1
        self.save_history(init=True)
        
        # 画面サイズ
        self.height, self.width = stdscr.getmaxyx()
        
        # プラグイン用キーバインド辞書 {keycode: function}
        self.plugin_key_bindings = {}
        self.plugin_commands = {} 

        # 色設定
        self.init_colors()
        
        # シンタックスルールの決定
        self.current_syntax_rules = self.detect_syntax(filename)

        # ファイル変更検出用タイムスタンプ
        self.file_mtime = None
        if filename and os.path.exists(filename):
            try: 
                self.file_mtime = os.path.getmtime(filename)
            except OSError: 
                self.file_mtime = None

        # プラグイン読み込み
        self.load_plugins()

        # エラーメッセージの表示（優先度順）
        if config_error:
            self.set_status(config_error, timeout=5)
        elif load_err:
            self.set_status(load_err, timeout=5)
        elif not filename or not os.path.exists(filename):
             self.show_start_screen()

    def _get_color(self, color_name):
        return COLOR_MAP.get(color_name.upper(), -1)

    def init_colors(self):
        if curses.has_colors():
            try:
                curses.start_color()
                curses.use_default_colors()
                c = self.config["colors"]
                
                # Basic UI
                curses.init_pair(1, self._get_color(c["header_text"]), self._get_color(c["header_bg"]))
                curses.init_pair(2, self._get_color(c["error_text"]), self._get_color(c["error_bg"]))
                curses.init_pair(3, self._get_color(c["linenum_text"]), self._get_color(c["linenum_bg"]))
                curses.init_pair(4, self._get_color(c["selection_text"]), self._get_color(c["selection_bg"]))
                
                # Syntax Highlighting Colors
                # 5: Keyword, 6: String, 7: Comment, 8: Number
                curses.init_pair(5, self._get_color(c.get("keyword", "YELLOW")), -1)
                curses.init_pair(6, self._get_color(c.get("string", "GREEN")), -1)
                curses.init_pair(7, self._get_color(c.get("comment", "MAGENTA")), -1)
                curses.init_pair(8, self._get_color(c.get("number", "BLUE")), -1)
                
                # Zenkaku Space (Red Background)
                curses.init_pair(9, curses.COLOR_WHITE, self._get_color(c.get("zenkaku_bg", "RED")))
                
            except curses.error:
                pass

    def detect_syntax(self, filename):
        """ファイル名からシンタックスルールを判定"""
        if not filename: return None
        _, ext = os.path.splitext(filename)
        for lang, rules in SYNTAX_RULES.items():
            if ext in rules["extensions"]:
                return rules
        return None

    def load_file(self, filename):
        """ファイルを読み込み、(行リスト, エラーメッセージ) を返す"""
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                    return (content if content else [""]), None
            except (OSError, UnicodeDecodeError) as e:
                return [""], f"Error loading file: {e}"
        return [""], None
    
    # --- プラグインシステム ---
    def load_plugins(self):
        plugin_dir = os.path.join(get_config_dir(), "plugins")
        if not os.path.exists(plugin_dir):
            try: 
                os.makedirs(plugin_dir, exist_ok=True)
            except OSError as e:
                # self.set_status(f"Plugin dir create failed: {e}", timeout=5)
                pass # Silent fail for clean startup
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

    def bind_key(self, key_code, func):
        self.plugin_key_bindings[key_code] = func

    # ==========================================
    # --- Plugin API (Public) ---
    # ==========================================
    def get_cursor_position(self):
        return self.cursor_y, self.cursor_x

    def get_line_content(self, y):
        if 0 <= y < len(self.buffer): return self.buffer.lines[y]
        return ""

    def get_buffer_lines(self):
        return self.buffer.get_content()

    def get_line_count(self):
        return len(self.buffer)

    def get_config_value(self, key):
        return self.config.get(key)

    def get_filename(self):
        return self.filename
        
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
        self.set_status_message(prompt_msg, timeout=60)
        self.draw_ui()
        curses.echo()
        result = None
        try:
            status_y = self.height - self.menu_height - 1
            self.safe_addstr(status_y, 0, prompt_msg.ljust(self.width), curses.color_pair(2))
            start_x = min(len(prompt_msg), self.width - 1)
            inp_bytes = self.stdscr.getstr(status_y, start_x)
            result = inp_bytes.decode('utf-8')
        except Exception:
            result = None
        finally:
            curses.noecho()
            self.status_message = ""
            self.redraw_screen()
        return result
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

    # --- 履歴管理 ---
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

    # --- 描画 ---
    def safe_addstr(self, y, x, string, attr=0):
        try:
            if y >= self.height or x >= self.width: return
            available = self.width - x
            if len(string) > available: string = string[:available]
            self.stdscr.addstr(y, x, string, attr)
        except curses.error:
            pass

    def show_start_screen(self):
        self.stdscr.clear()
        logo = [
            "      )  (  ",
            "     (   ) )",
            "      ) ( ( ",
            "    _______)",
            f" .-'-------|",
            f" | CAFFEE  |__",
            f" |  v{VERSION}  |__)",
            f" |_________|",
            "  `-------' "
        ]
        my = self.height // 2 - 6
        mx = self.width // 2
        for i, l in enumerate(logo):
            if my + i < self.height - 2:
                self.safe_addstr(my + i, max(0, mx - 10), l)
        self.safe_addstr(my + len(logo) + 1, max(0, mx - 12), f"CAFFEE Editor v{VERSION}", curses.A_BOLD)
        self.safe_addstr(my + len(logo) + 3, max(0, mx - 15), "Press any key to brew...", curses.A_DIM)
        self.stdscr.refresh()
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

    def get_edit_height(self):
        """現在のエディタ領域（行番号＋本文）の高さを計算"""
        # Header(1) + Content + Status(1) + Menu(varies)
        return max(1, self.height - self.header_height - self.status_height - self.menu_height)

    def draw_content(self):
        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        edit_height = self.get_edit_height()
        
        # カラーペアID
        ATTR_NORMAL = 0
        ATTR_KEYWORD = curses.color_pair(5)
        ATTR_STRING = curses.color_pair(6)
        ATTR_COMMENT = curses.color_pair(7)
        ATTR_NUMBER = curses.color_pair(8)
        ATTR_ZENKAKU = curses.color_pair(9)
        ATTR_SELECT = curses.color_pair(4)

        for i in range(edit_height):
            file_line_idx = self.scroll_offset + i
            draw_y = i + self.header_height # ヘッダーの分下げる
            
            # 背景クリア
            self.safe_addstr(draw_y, 0, " " * self.width)
            
            if file_line_idx >= len(self.buffer):
                self.safe_addstr(draw_y, 0, "~", curses.color_pair(3))
            else:
                ln_str = str(file_line_idx + 1).rjust(linenum_width - 1) + " "
                self.safe_addstr(draw_y, 0, ln_str, curses.color_pair(3))
                
                line = self.buffer[file_line_idx]
                max_content_width = self.width - linenum_width
                display_line = line[:max_content_width]
                
                # --- シンタックスハイライトの計算 ---
                # 文字ごとの属性マップを作成 (初期値: NORMAL)
                line_attrs = [ATTR_NORMAL] * len(display_line)
                
                if self.current_syntax_rules:
                    # キーワード
                    if "keywords" in self.current_syntax_rules:
                        for match in re.finditer(self.current_syntax_rules["keywords"], display_line):
                            for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_KEYWORD
                    # 数字
                    if "numbers" in self.current_syntax_rules:
                        for match in re.finditer(self.current_syntax_rules["numbers"], display_line):
                             for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_NUMBER
                    # 文字列 (簡易対応: キーワードを上書き)
                    if "strings" in self.current_syntax_rules:
                        for match in re.finditer(self.current_syntax_rules["strings"], display_line):
                            for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_STRING
                    # コメント (最強: 全てを上書き)
                    if "comments" in self.current_syntax_rules:
                         for match in re.finditer(self.current_syntax_rules["comments"], display_line):
                            for j in range(match.start(), match.end()):
                                if j < len(line_attrs): line_attrs[j] = ATTR_COMMENT

                # --- 描画ループ ---
                for cx, char in enumerate(display_line):
                    attr = line_attrs[cx]

                    # 選択範囲の上書き
                    if self.is_in_selection(file_line_idx, cx):
                        attr = ATTR_SELECT
                    
                    # 全角スペースの特別処理 (選択範囲外の場合のみ赤くする、または選択中でも赤くするかはお好みで。ここは赤優先)
                    if char == '\u3000':
                        # VSCode風に全角スペースを強調
                        self.safe_addstr(draw_y, linenum_width + cx, "　", ATTR_ZENKAKU)
                    else:
                        self.safe_addstr(draw_y, linenum_width + cx, char, attr)

    def draw_ui(self):
        # 1. Header
        mark_status = "[MARK]" if self.mark_pos else ""
        mod_char = " *" if self.modified else ""
        syntax_name = "Text"
        if self.current_syntax_rules:
            # 簡易的に拡張子名などを表示したい場合
            ext_list = self.current_syntax_rules.get("extensions", [])
            if ext_list: syntax_name = ext_list[0].upper().replace(".", "")

        header = f" {EDITOR_NAME} v{VERSION} | {self.filename or 'New Buffer'}{mod_char} | {syntax_name}   {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(0, 0, header, curses.color_pair(1) | curses.A_BOLD)
        self.header_height = 1

        # 2. Menu Bar (Dynamic wrapping)
        shortcuts = [
            ("^X", "Exit"), ("^C", "Copy"), ("^O", "Save"), ("^K", "Cut"),
            ("^U", "Paste"), ("^W", "Search"), ("^Z", "Undo"), ("^R", "Redo"),
            ("^6", "Mark"), ("^A", "All"), ("^G", "Goto"), ("^Y", "DelLine"),
            ("^/", "Comment")
        ]

        menu_lines = []
        current_line_text = ""
        
        for key_str, label in shortcuts:
            item_str = f"{key_str} {label}  "
            if len(current_line_text) + len(item_str) > self.width:
                menu_lines.append(current_line_text)
                current_line_text = item_str
            else:
                current_line_text += item_str
        if current_line_text:
            menu_lines.append(current_line_text)

        self.menu_height = len(menu_lines)
        self.status_height = 1

        # メニューの描画（下から順に）
        for i, line in enumerate(reversed(menu_lines)):
            y = self.height - 1 - i
            self.safe_addstr(y, 0, line.ljust(self.width), curses.color_pair(1))

        # 3. Status Bar (Above Menu)
        status_y = self.height - self.menu_height - 1
        
        now = datetime.datetime.now()
        display_msg = ""
        if self.status_message:
            if not self.status_expire_time or now <= self.status_expire_time:
                display_msg = self.status_message
            else:
                self.status_message = ""
                self.status_expire_time = None
        
        # ステータス行の描画
        pos_info = f" {self.cursor_y + 1}:{self.cursor_x + 1} "
        max_msg_len = self.width - len(pos_info) - 1
        if len(display_msg) > max_msg_len:
            display_msg = display_msg[:max_msg_len]
            
        # 行全体を背景色で埋める
        self.safe_addstr(status_y, 0, " " * self.width, curses.color_pair(2))
        self.safe_addstr(status_y, 0, display_msg, curses.color_pair(2))
        self.safe_addstr(status_y, self.width - len(pos_info), pos_info, curses.color_pair(1))


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
        
        # スクロール調整
        if self.cursor_y < self.scroll_offset:
            self.scroll_offset = self.cursor_y
        elif self.cursor_y >= self.scroll_offset + edit_height:
            self.scroll_offset = self.cursor_y - edit_height + 1

    # --- 編集操作 ---
    def perform_copy(self):
        sel = self.get_selection_range()
        if not sel:
            self.status_message = "No selection to copy."
            return
        start, end = sel
        self.clipboard = []
        if start[0] == end[0]:
            self.clipboard.append(self.buffer.lines[start[0]][start[1]:end[1]])
        else:
            self.clipboard.append(self.buffer.lines[start[0]][start[1]:])
            for i in range(start[0] + 1, end[0]):
                self.clipboard.append(self.buffer.lines[i])
            self.clipboard.append(self.buffer.lines[end[0]][:end[1]])
        self.status_message = f"Copied {len(self.clipboard)} lines."
        self.mark_pos = None

    def perform_cut(self):
        self.save_history()
        sel = self.get_selection_range()
        if not sel:
            if len(self.buffer) > 0:
                self.clipboard = [self.buffer.lines.pop(self.cursor_y)]
                if not self.buffer.lines: self.buffer.lines = [""]
                self.move_cursor(self.cursor_y, 0)
                self.modified = True
                self.set_status("Cut line.", timeout=2)
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
            self.move_cursor(self.cursor_y, self.cursor_x + len(self.clipboard[0]))
        else:
            self.buffer.lines[self.cursor_y] = prefix + self.clipboard[0]
            for i in range(1, len(self.clipboard) - 1):
                self.buffer.lines.insert(self.cursor_y + i, self.clipboard[i])
            self.buffer.lines.insert(self.cursor_y + len(self.clipboard) - 1, self.clipboard[-1] + suffix)
            new_y = self.cursor_y + len(self.clipboard) - 1
            new_x = len(self.clipboard[-1])
            self.move_cursor(new_y, new_x)
        self.modified = True
        self.status_message = "Pasted."

    def toggle_comment(self):
        if not self.buffer.lines: return
        self.save_history()
        y = self.cursor_y
        line = self.buffer.lines[y]
        match = re.match(r'^\s*#', line)
        if match:
            comment_pos = match.end() - 1
            self.buffer.lines[y] = line[:comment_pos] + line[comment_pos+1:]
            if self.cursor_x > comment_pos: self.cursor_x -= 1
            self.status_message = "Uncommented line."
        else:
            m = re.match(r'^(\s*)', line)
            indent_len = len(m.group(1)) if m else 0
            self.buffer.lines[y] = line[:indent_len] + "#" + line[indent_len:]
            if self.cursor_x >= indent_len: self.cursor_x += 1
            self.status_message = "Commented line."
        self.modified = True
        self.desired_x = self.cursor_x

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
        
    def search_text(self):
        self.set_status("Search (Regex): ", timeout=30)
        self.draw_ui()
        curses.echo()
        status_y = self.height - self.menu_height - 1
        try: 
            query = self.stdscr.getstr(status_y, len("Search (Regex): ")).decode('utf-8')
        except Exception:
            query = ""
        curses.noecho()
        
        if not query: 
            self.set_status("Search aborted.", timeout=2)
            return

        try:
            pattern = re.compile(query)
        except re.error as e:
            self.set_status(f"Invalid Regex: {e}", timeout=4)
            return

        found = False
        start_y = self.cursor_y
        start_x = self.cursor_x

        line = self.buffer.lines[start_y]
        match = pattern.search(line, start_x + 1)
        if match:
            self.cursor_y, self.cursor_x = start_y, match.start()
            found = True
        else:
            for i in range(start_y + 1, len(self.buffer)):
                match = pattern.search(self.buffer.lines[i])
                if match:
                    self.cursor_y, self.cursor_x = i, match.start()
                    found = True
                    break
            
            if not found:
                for i in range(0, start_y + 1):
                    match = pattern.search(self.buffer.lines[i])
                    if i == start_y:
                        if match and match.start() <= start_x:
                            self.cursor_y, self.cursor_x = i, match.start()
                            found = True
                            break
                    elif match:
                        self.cursor_y, self.cursor_x = i, match.start()
                        found = True
                        break

        if found:
            self.move_cursor(self.cursor_y, self.cursor_x, update_desired_x=True)
            self.set_status(f"Found match.", timeout=3)
        else:
            self.set_status(f"No match for '{query}'", timeout=3)

    def set_status(self, msg, timeout=3):
        self.status_message = msg
        try:
            self.status_expire_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        except Exception:
            self.status_expire_time = None

    def save_file(self):
        if not self.filename:
            self.set_status("Filename: ", timeout=10)
            self.draw_ui()
            curses.echo()
            status_y = self.height - self.menu_height - 1
            try: 
                fn = self.stdscr.getstr(status_y, len("Filename: ")).decode('utf-8')
            except Exception:
                fn = ""
            curses.noecho()
            if fn.strip(): 
                self.filename = fn.strip()
            else: 
                self.set_status("Aborted", timeout=2)
                return

        try:
            # バックアップ作成処理
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

            # Atomic Save: 一時ファイルに書き込んでからリネーム
            tmp_name = f"{self.filename}.tmp"
            with open(tmp_name, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.buffer.lines))
            os.replace(tmp_name, self.filename)
            
            try: 
                self.file_mtime = os.path.getmtime(self.filename)
            except OSError: 
                self.file_mtime = None
            
            # 保存後にファイル名が変わった（新規保存）場合、シンタックス再判定
            self.current_syntax_rules = self.detect_syntax(self.filename)
            
            self.modified = False
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
        self.set_status("Goto line: ", timeout=10)
        self.draw_ui()
        curses.echo()
        status_y = self.height - self.menu_height - 1
        try:
            s = self.stdscr.getstr(status_y, len("Goto line: ")).decode('utf-8')
        except Exception:
            s = ""
        curses.noecho()
        try:
            n = int(s.strip())
            self.move_cursor(max(0, min(n - 1, len(self.buffer) - 1)), 0, update_desired_x=True)
            self.set_status(f"Goto {n}", timeout=2)
        except ValueError:
            self.set_status("Invalid line number.", timeout=2)

    def main_loop(self):
        while True:
            self.stdscr.erase()
            self.height, self.width = self.stdscr.getmaxyx()
            
            # 外部変更の監視
            if self.filename and os.path.exists(self.filename):
                try:
                    mtime = os.path.getmtime(self.filename)
                    if self.file_mtime and mtime != self.file_mtime:
                        self.set_status("File changed on disk.", timeout=5)
                        self.file_mtime = mtime
                except OSError:
                    pass

            self.draw_ui()
            self.draw_content()
            linenum_width = max(4, len(str(len(self.buffer)))) + 1
            
            screen_y = self.cursor_y - self.scroll_offset + self.header_height
            
            # --- カーソル位置の視覚的補正 (全角対応) ---
            # 論理位置 (self.cursor_x) までの文字幅を計算して screen_x を決定
            screen_x = linenum_width
            if self.cursor_y < len(self.buffer):
                current_line_text = self.buffer.lines[self.cursor_y]
                # cursor_xまでの部分文字列の幅を計算
                for char in current_line_text[:self.cursor_x]:
                    w = unicodedata.east_asian_width(char)
                    screen_x += 2 if w in ('F', 'W', 'A') else 1
            
            edit_height = self.get_edit_height()
            
            if 0 < screen_y <= edit_height:
                try: self.stdscr.move(screen_y, min(screen_x, self.width - 1))
                except curses.error: pass
            
            try:
                self.stdscr.timeout(100)
                # getch -> get_wch に変更してマルチバイト入力を受け付ける
                key_in = self.stdscr.get_wch()
                self.stdscr.timeout(-1)
            except KeyboardInterrupt:
                key_in = CTRL_C
            except curses.error: 
                key_in = -1
            
            # 入力処理の振り分け
            key_code = -1
            char_input = None

            if isinstance(key_in, int):
                # 特殊キーやタイムアウトなし(-1)の場合はそのまま
                key_code = key_in
            elif isinstance(key_in, str):
                # 文字入力の場合
                if len(key_in) == 1:
                    code = ord(key_in)
                    # ASCII制御文字 (Ctrl+Key, Tab, Enter, Backspace) のマッピング
                    # Ctrl+A(1) ~ Ctrl+Z(26), Esc(27), etc.
                    if code < 32 or code == 127:
                        key_code = code
                    else:
                        # 通常の文字入力 (a, A, あ, 🍺 など)
                        char_input = key_in
            
            if key_code == -1 and char_input is None: continue

            # --- プラグインフック ---
            if key_code in self.plugin_key_bindings:
                try: 
                    self.plugin_key_bindings[key_code](self)
                except Exception as e:
                    self.set_status(f"Plugin Error: {e}", timeout=5)
                continue

            # --- キーハンドリング (key_codeを使用) ---
            if key_code == CTRL_C:
                self.perform_copy()
            elif key_code == CTRL_X:
                if self.modified:
                    self.status_message = "Save changes? (y/n/Esc)"
                    self.draw_ui()
                    while True:
                        try:
                            ch = self.stdscr.getch() # ここはY/N判定だけなのでgetchでOK
                        except: ch = -1
                        if ch in (ord('y'), ord('Y')): 
                            self.save_file()
                            return
                        elif ch in (ord('n'), ord('N')): 
                            return
                        elif ch == 27 or ch == CTRL_C: 
                            self.status_message = "Cancelled."
                            break
                else: return
            elif key_code == CTRL_O: self.save_file()
            elif key_code == CTRL_W: self.search_text()
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
            elif key_code == CTRL_K: self.perform_cut()
            elif key_code == CTRL_U: self.perform_paste()
            elif key_code == CTRL_Z: self.undo()
            elif key_code == CTRL_R: self.redo()
            elif key_code == curses.KEY_UP: self.move_cursor(self.cursor_y - 1, self.desired_x)
            elif key_code == curses.KEY_DOWN: self.move_cursor(self.cursor_y + 1, self.desired_x)
            elif key_code == curses.KEY_LEFT: self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
            elif key_code == curses.KEY_RIGHT: self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
            elif key_code == curses.KEY_PPAGE: 
                self.move_cursor(self.cursor_y - self.get_edit_height(), self.cursor_x, update_desired_x=True)
            elif key_code == curses.KEY_NPAGE: 
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
            elif key_code == KEY_ENTER or key_code == KEY_RETURN:
                self.save_history()
                line = self.buffer.lines[self.cursor_y]
                indent = ""
                match = re.match(r'^(\s*)', line)
                if match:
                    indent = match.group(1)
                self.buffer.lines.insert(self.cursor_y + 1, indent + line[self.cursor_x:])
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x]
                self.move_cursor(self.cursor_y + 1, len(indent), update_desired_x=True)
                self.modified = True
            elif key_code == KEY_TAB:
                self.save_history()
                tab_spaces = " " * self.config.get("tab_width", 4)
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + tab_spaces + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + len(tab_spaces), update_desired_x=True)
                self.modified = True
            
            # --- 文字入力 (ASCII および マルチバイト) ---
            elif char_input:
                self.save_history()
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + char_input + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
                self.modified = True

def main(stdscr):
    os.environ.setdefault('ESCDELAY', '25') 
    curses.raw()
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    config, config_error = load_config()
    Editor(stdscr, fn, config, config_error).main_loop()

if __name__ == "__main__":
    try: 
        curses.wrapper(main)
    except Exception as e:
        # curses終了後にトレースバックを表示
        traceback.print_exc()

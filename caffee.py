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
import subprocess

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
VERSION = "1.4.0" #unreleased now | Currently released latest version - 1.3.2
DEFAULT_CONFIG = {
    "tab_width": 4,
    "history_limit": 50,
    "use_soft_tabs": True,
    "backup_subdir": "backup",
    "backup_count": 5,
    # --- Splash / Start Screen Settings ---
    "show_splash": True,         # スプラッシュ画面を表示するか
    "splash_duration": 500,     # 自動遷移する場合の表示時間(ms)
    "start_screen_mode": True,  # 起動時にスタート画面(インタラクティブ)を有効にするか
    # --------------------------
    # --- UI Layout Settings ---
    "explorer_width": 35,
    "terminal_height": 10,
    "show_explorer_default": True,
    "show_terminal_default": True,
    # --------------------------
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
        "tab_inactive_bg": "DEFAULT"
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
        "extensions": [".c", ".cpp", ".h", ".hpp", ".cc"],
        "keywords": r"\b(int|float|double|char|void|if|else|for|while|return|struct|class|public|private|protected|include)\b",
        "comments": r"//.*",
        "strings": r"(['\"])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "go": {
        "extensions": [".go"],
        "keywords": r"\b(break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|true|false|nil|append|cap|close|complex|copy|delete|imag|len|make|new|panic|print|println|real|recover|bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr)\b",
        "comments": r"//.*",
        "strings": r"(['\"`])(?:(?<!\\)\1|.)*?\1",
        "numbers": r"\b\d+\b"
    },
    "rust": {
        "extensions": [".rs"],
        "keywords": r"\b(as|break|const|continue|crate|else|enum|extern|false|fn|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|struct|super|trait|true|type|unsafe|use|where|while)\b",
        "comments": r"//.*",
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
                if "colors" in user_config and isinstance(user_config["colors"], dict):
                    config["colors"].update(user_config["colors"])
                    del user_config["colors"]
                for key, value in user_config.items():
                    config[key] = value
        except (json.JSONDecodeError, OSError) as e:
            load_error = f"Config load error: {e}"
            
    return config, load_error

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def strip_ansi(text):
    return ANSI_ESCAPE.sub('', text)

def get_char_width(char):
    """文字の表示幅を返す（半角=1, 全角=2）"""
    return 2 if unicodedata.east_asian_width(char) in ('F', 'W', 'A') else 1

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
            display_str = f" {marker} {item['name']}"
            
            attr = curses.A_NORMAL
            if idx == self.selected_index:
                attr = curses.A_REVERSE
            
            try:
                # 名前部分の色分け
                stdscr.addstr(y, 1, display_str.ljust(width-2), attr)
            except curses.error: pass

class FileExplorer:
    def __init__(self, start_path="."):
        self.current_path = os.path.abspath(start_path)
        self.files = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.refresh_list()

    def refresh_list(self):
        try:
            items = os.listdir(self.current_path)
            dirs = sorted([f for f in items if os.path.isdir(os.path.join(self.current_path, f))])
            files = sorted([f for f in items if not os.path.isdir(os.path.join(self.current_path, f))])
            
            self.files = [".."] + dirs + files
            self.selected_index = 0
            self.scroll_offset = 0
        except OSError:
            self.files = [".."]

    def navigate(self, delta):
        self.selected_index += delta
        if self.selected_index < 0: self.selected_index = 0
        if self.selected_index >= len(self.files): self.selected_index = len(self.files) - 1

    def enter(self):
        if not self.files: return None
        
        selected = self.files[self.selected_index]
        target = os.path.abspath(os.path.join(self.current_path, selected))
        
        if os.path.isdir(target):
            self.current_path = target
            self.refresh_list()
            return None
        else:
            return target

    def draw(self, stdscr, y, x, h, w, colors):
        # 枠線の描画
        for i in range(h):
            try:
                stdscr.addstr(y + i, x, " " * w, colors["ui_border"])
                stdscr.addch(y + i, x + w - 1, '│', colors["ui_border"])
            except curses.error: pass
            
        title = f" {os.path.basename(self.current_path)}/ "
        if len(title) > w - 2: title = title[:w-2]
        try:
            stdscr.addstr(y, x, title, colors["header"] | curses.A_BOLD)
            stdscr.addstr(y + 1, x, "─" * (w-1), colors["ui_border"])
        except curses.error: pass

        list_h = h - 2 # Title + separator
        list_start_y = y + 2
        
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + list_h:
            self.scroll_offset = self.selected_index - list_h + 1

        for i in range(list_h):
            idx = self.scroll_offset + i
            if idx >= len(self.files): break
            
            draw_y = list_start_y + i
            f_name = self.files[idx]
            
            is_dir = os.path.isdir(os.path.join(self.current_path, f_name))
            color = colors["dir"] if is_dir else colors["file"]
            attr = color
            
            prefix = "📁 " if is_dir else "📄 "
            if f_name == "..": prefix = "⬆️  "

            if idx == self.selected_index:
                attr = attr | curses.A_REVERSE

            display_name = (prefix + f_name)[:w-3]
            try:
                stdscr.addstr(draw_y, x + 1, display_name.ljust(w-2), attr)
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

class Editor:
    def __init__(self, stdscr, filename=None, config=None, config_error=None):
        self.stdscr = stdscr
        self.config = config if config else DEFAULT_CONFIG
        
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
        
        self.explorer = FileExplorer(".")
        self.terminal = Terminal(self.terminal_height)
        self.plugin_manager = PluginManager(get_config_dir())
        
        self.status_message = ""
        self.status_expire_time = None
        self.clipboard = []
        
        self.height, self.width = stdscr.getmaxyx()
        
        self.plugin_key_bindings = {}
        self.plugin_commands = {} 

        self.init_colors()
        self.load_plugins()

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
        self.tabs.append(new_tab)
        self.active_tab_idx = len(self.tabs) - 1
        self.save_history(init=True)
        self.run_interactive_start_screen()

    def close_current_tab(self):
        """Close current tab. Returns True if exited editor entirely"""
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
                    return False
        
        self.tabs.pop(self.active_tab_idx)
        if not self.tabs:
            return True # No tabs left, exit
        
        if self.active_tab_idx >= len(self.tabs):
            self.active_tab_idx = len(self.tabs) - 1
        return False

    def next_tab(self):
        if not self.tabs: return
        self.active_tab_idx = (self.active_tab_idx + 1) % len(self.tabs)

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


            except curses.error:
                pass

    def detect_syntax(self, filename):
        if not filename: return None
        _, ext = os.path.splitext(filename)
        for lang, rules in SYNTAX_RULES.items():
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

    def bind_key(self, key_code, func):
        self.plugin_key_bindings[key_code] = func

    # ==========================================
    # --- Plugin API ---
    # ==========================================
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
                # 設定ファイルを開く
                setting_file = os.path.join(get_config_dir(), "setting.json")
                # ロード処理
                new_lines, err = self.load_file(setting_file)
                if not err:
                    self.buffer = Buffer(new_lines)
                    self.filename = setting_file
                    self.file_mtime = os.path.getmtime(setting_file)
                    self.current_syntax_rules = self.detect_syntax(setting_file)
                    self.cursor_y = 0
                    self.cursor_x = 0
                    self.col_offset = 0
                    self.save_history(init=True)
                    self.active_pane = 'editor'
                else:
                    self.set_status(err)
                break
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

    def show_start_screen(self, duration_ms=None, interactive=False):
        self.stdscr.clear()
        # Pair 3 is CYAN (Text)
        logo_attr = curses.color_pair(3) | curses.A_BOLD
        
        logo = [
            "                                         　    ) (",
            "                                         　   (   ) )",
            "                                         　    ) ( (",
            "                                         　  _______)",
            f"   _________    ________________________　.-'-------|",
            f"  / ____/   |  / ____/ ____/ ____/ ____/　| CAFFEE  |__",
            f" / /   / /| | / /_  / /_  / __/ / __/   　| v{VERSION}  |__)",
            f"/ /___/ ___ |/ __/ / __/ / /___/ /___   　|_________|",
            f"\____/_/  |_/_/   /_/   /_____/_____/   　 `-------'"
        ]
        my = self.height // 2 - 6
        mx = self.width // 2 
        start_x_offset = 28

        for i, l in enumerate(logo):
            if my + i < self.height - 2:
                self.safe_addstr(my + i, max(0, mx - start_x_offset), l.rstrip(), logo_attr)
                
        self.safe_addstr(my + len(logo) + 1, max(0, mx - 12), f"CAFFEE Editor v{VERSION}", logo_attr)
        
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
        y = self.tab_bar_height + self.header_height
        x = 0
        h = self.height - self.tab_bar_height - self.header_height - self.status_height - self.menu_height
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
        _, _, edit_h, edit_w = self.get_edit_rect()
        
        y = self.tab_bar_height + self.header_height
        w = min(self.explorer_width, self.width - 20)
        x = self.width - w
        h = self.height - self.tab_bar_height - self.header_height - self.status_height - self.menu_height
        if self.show_terminal:
            term_h = min(self.terminal_height, h - 5)
            h -= term_h
            
        return y, x, h, w

    def get_terminal_rect(self):
        if not self.show_terminal: return 0,0,0,0
        _, _, edit_h, _ = self.get_edit_rect()
        y = self.tab_bar_height + self.header_height + edit_h
        x = 0
        w = self.width
        total_h = self.height - self.tab_bar_height - self.header_height - self.status_height - self.menu_height
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

        for i in range(edit_h):
            file_line_idx = self.scroll_offset + i
            draw_y = edit_y + i
            
            try:
                self.stdscr.addstr(draw_y, edit_x, " " * edit_w)
            except curses.error: pass
            
            if file_line_idx >= len(self.buffer):
                self.safe_addstr(draw_y, edit_x, "~", curses.color_pair(3))
            else:
                ln_str = str(file_line_idx + 1).rjust(linenum_width - 1) + " "
                self.safe_addstr(draw_y, edit_x, ln_str, curses.color_pair(3))
                
                line = self.buffer[file_line_idx]
                
                # --- 横スクロール対応: 表示領域に合わせて文字列をスライス ---
                max_content_width = edit_w - linenum_width
                
                # col_offsetに基づいて表示部分を切り出し
                display_line = line[self.col_offset : self.col_offset + max_content_width]
                
                # --- シンタックスハイライト (全体に対して計算し、表示時にシフト) ---
                line_attrs = [ATTR_NORMAL] * len(line)
                
                # ハイライトは行全体に対して適用（Regex判定のため）
                if self.current_syntax_rules:
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

    def draw_ui(self):
        # Plugin Manager Mode doesn't use standard UI
        if self.active_pane == 'plugin_manager':
            return
            
        if self.active_pane == 'full_screen_explorer':
            self.safe_addstr(0, 0, " CAFFEE File Explorer ".ljust(self.width), curses.color_pair(1) | curses.A_BOLD)
            self.safe_addstr(self.height - 1, 0, " [Enter] Open  [Esc] Back to Editor ".ljust(self.width), curses.color_pair(1))
            return

        # --- Tab Bar Drawing ---
        self.safe_addstr(0, 0, " " * self.width, curses.color_pair(10))
        current_x = 0
        for i, tab in enumerate(self.tabs):
            name = os.path.basename(tab.filename) if tab.filename else "untitled"
            mod = "*" if tab.modified else ""
            display = f" {i+1}:{name}{mod} "
            
            pair = curses.color_pair(14) if i == self.active_tab_idx else curses.color_pair(15)
            self.safe_addstr(0, current_x, display, pair)
            current_x += len(display)
            if current_x >= self.width: break
        
        # --- Header ---
        mark_status = "[MARK]" if self.mark_pos else ""
        mod_char = " *" if self.modified else ""
        syntax_name = "Text"
        if self.current_syntax_rules:
            ext_list = self.current_syntax_rules.get("extensions", [])
            if ext_list: syntax_name = ext_list[0].upper().replace(".", "")

        focus_map = {'editor': 'EDT', 'explorer': 'EXP', 'terminal': 'TRM', 'full_screen_explorer': 'F-EXP'}
        focus_str = f"[{focus_map.get(self.active_pane, '---')}]"

        header = f" {EDITOR_NAME} v{VERSION} | {self.filename or 'New Buffer'} {mod_char} | {syntax_name} | {focus_str} {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(1, 0, header, curses.color_pair(1) | curses.A_BOLD)
        self.header_height = 1

        shortcuts = [
            ("^X", "CloseTab"), ("^S", "New/Start"), ("^L", "NextTab"), ("^O", "Save"),
            ("^K", "Cut"), ("^U", "Paste"), ("^W", "Search"), ("^Z", "Undo"),
            ("^6", "Mark"), ("^A", "All"), ("^G", "Goto"), ("^Y", "DelLine"),
            ("^/", "Comment"), ("^F", "Explorer"), ("^T", "Terminal"), ("^E", "LineEnd")
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

        for i, line in enumerate(reversed(menu_lines)):
            y = self.height - 1 - i
            self.safe_addstr(y, 0, line.ljust(self.width), curses.color_pair(1))

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
        max_msg_len = self.width - len(pos_info) - 1
        if len(display_msg) > max_msg_len:
            display_msg = display_msg[:max_msg_len]
            
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

    def run_build_command(self):
        if not self.filename:
            self.set_status("Cannot run: No filename provided.")
            return
            
        # Run前に自動保存
        if self.modified:
            self.save_file()
            
        ext = os.path.splitext(self.filename)[1].lower()
        base = os.path.splitext(self.filename)[0]
        
        cmd = ""
        if ext == ".py": cmd = f"python3 \"{self.filename}\""
        elif ext == ".js": cmd = f"node \"{self.filename}\""
        elif ext == ".go": cmd = f"go run \"{self.filename}\""
        elif ext == ".c": cmd = f"gcc \"{self.filename}\" -o \"{base}\" && \"./{base}\""
        elif ext in [".cpp", ".cc"]: cmd = f"g++ \"{self.filename}\" -o \"{base}\" && \"./{base}\""
        elif ext == ".sh": cmd = f"bash \"{self.filename}\""
        elif ext == ".rs": cmd = f"rustc \"{self.filename}\" && \"./{base}\""
        else:
            self.set_status(f"No build command defined for {ext}")
            return

        if not self.show_terminal:
            self.toggle_terminal()
            
        self.active_pane = 'terminal'
        self.terminal.write_input(cmd + "\n")

    def main_loop(self):
        while True:
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
            elif self.active_pane == 'full_screen_explorer':
                curses.curs_set(0)

            try:
                if self.show_terminal:
                    self.stdscr.timeout(50) 
                else:
                    self.stdscr.timeout(100)
                    
                key_in = self.stdscr.get_wch()
                self.stdscr.timeout(-1)
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
            elif key_code == CTRL_T:
                self.toggle_terminal()
                continue
            elif key_code == CTRL_B:
                self.run_build_command()
                continue
            elif key_code == CTRL_S:
                self.new_tab()
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
            
            if self.active_pane == 'full_screen_explorer':
                if key_code == curses.KEY_UP:
                    self.explorer.navigate(-1)
                elif key_code == curses.KEY_DOWN:
                    self.explorer.navigate(1)
                elif key_code in (KEY_ENTER, KEY_RETURN):
                    res = self.explorer.enter()
                    if res:
                        new_lines, err = self.load_file(res)
                        if not err:
                            # 最初のタブの内容を更新
                            self.tabs[0].buffer = Buffer(new_lines)
                            self.tabs[0].filename = res
                            self.tabs[0].file_mtime = os.path.getmtime(res)
                            self.tabs[0].current_syntax_rules = self.detect_syntax(res)
                            self.tabs[0].cursor_y = 0
                            self.tabs[0].cursor_x = 0
                            self.tabs[0].col_offset = 0
                            self.tabs[0].save_history(init=True)
                            self.active_tab_idx = 0
                            self.active_pane = 'editor'
                        else:
                            self.set_status(err)
                elif key_code == KEY_ESC:
                    self.active_pane = 'editor'
                continue
            # -----------------------------------

            if self.active_pane == 'explorer':
                if key_code == curses.KEY_UP:
                    self.explorer.navigate(-1)
                elif key_code == curses.KEY_DOWN:
                    self.explorer.navigate(1)
                elif key_code in (KEY_ENTER, KEY_RETURN):
                    res = self.explorer.enter()
                    if res:
                        new_lines, err = self.load_file(res)
                        if not err:
                            self.buffer = Buffer(new_lines)
                            self.filename = res
                            self.file_mtime = os.path.getmtime(res)
                            self.current_syntax_rules = self.detect_syntax(res)
                            self.cursor_y = 0
                            self.cursor_x = 0
                            self.col_offset = 0
                            self.save_history(init=True)
                            self.active_pane = 'editor'
                        else:
                            self.set_status(err)
                elif key_code == KEY_ESC:
                    self.active_pane = 'editor'
                continue

            if self.active_pane == 'terminal':
                if key_code == KEY_ESC:
                    self.active_pane = 'editor'
                    continue
                
                if char_input:
                    self.terminal.write_input(char_input)
                elif key_code == KEY_ENTER or key_code == KEY_RETURN:
                    self.terminal.write_input("\n")
                elif key_code in (KEY_BACKSPACE, KEY_BACKSPACE2):
                    self.terminal.write_input("\x08")
                elif key_code == KEY_TAB:
                    self.terminal.write_input("\t")
                elif key_code == CTRL_C:
                    self.terminal.write_input("\x03")
                elif key_code == curses.KEY_UP: self.terminal.write_input("\x1b[A")
                elif key_code == curses.KEY_DOWN: self.terminal.write_input("\x1b[B")
                elif key_code == curses.KEY_RIGHT: self.terminal.write_input("\x1b[C")
                elif key_code == curses.KEY_LEFT: self.terminal.write_input("\x1b[D")
                
                continue

            if key_code in self.plugin_key_bindings:
                try: self.plugin_key_bindings[key_code](self)
                except Exception as e: self.set_status(f"Plugin Error: {e}", timeout=5)
                continue

            if key_code == CTRL_C:
                self.perform_copy()
            elif key_code == CTRL_X:
                # Tab Close Logic
                if self.close_current_tab():
                    return
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
        traceback.print_exc()

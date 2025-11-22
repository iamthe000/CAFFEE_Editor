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

# --- デフォルト設定 ---
EDITOR_NAME = "CAFFEE"
VERSION = "1.3" #unreleased now | Currently released latest version - 1.1.0

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
        "selection_bg": "CYAN"
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

def get_config_dir():
    """設定ディレクトリのパスを取得"""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".caffee_setting")

def load_config():
    """設定ファイルを読み込み、デフォルト設定とマージする"""
    config = DEFAULT_CONFIG.copy()
    setting_dir = get_config_dir()
    setting_file = os.path.join(setting_dir, "setting.json")

    if not os.path.exists(setting_dir):
        try: os.makedirs(setting_dir)
        except: pass

    if os.path.exists(setting_file):
        try:
            with open(setting_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                for key, value in user_config.items():
                    if key == "colors" and isinstance(value, dict):
                        config["colors"].update(value)
                    else:
                        config[key] = value
        except Exception:
            pass
            
    return config

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
    def __init__(self, stdscr, filename=None, config=None):
        self.stdscr = stdscr
        self.filename = filename
        self.config = config if config else DEFAULT_CONFIG
        
        # 初期バッファ設定
        initial_lines = self.load_file(filename)
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

        # ステータス表示制御（期限付き表示）
        self.status_expire_time = None

        # ファイル変更検出用タイムスタンプ
        self.file_mtime = None
        if filename and os.path.exists(filename):
            try: self.file_mtime = os.path.getmtime(filename)
            except Exception: self.file_mtime = None

        # プラグイン読み込み
        self.load_plugins()

        # 新規ならスタート画面
        if not filename or not os.path.exists(filename):
             self.show_start_screen()

    def _get_color(self, color_name):
        return COLOR_MAP.get(color_name.upper(), -1)

    def init_colors(self):
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            c = self.config["colors"]
            try:
                curses.init_pair(1, self._get_color(c["header_text"]), self._get_color(c["header_bg"]))
                curses.init_pair(2, self._get_color(c["error_text"]), self._get_color(c["error_bg"]))
                curses.init_pair(3, self._get_color(c["linenum_text"]), self._get_color(c["linenum_bg"]))
                curses.init_pair(4, self._get_color(c["selection_text"]), self._get_color(c["selection_bg"]))
            except:
                pass

    def load_file(self, filename):
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                    return content if content else [""]
            except Exception as e:
                self.status_message = f"Error loading file: {e}"
                return [""]
        return [""]
    
    # --- プラグインシステム ---
    def load_plugins(self):
        plugin_dir = os.path.join(get_config_dir(), "plugins")
        if not os.path.exists(plugin_dir):
            try: os.makedirs(plugin_dir)
            except: return

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
                        try:
                            module.init(self)
                            loaded_count += 1
                        except Exception as e:
                            self.set_status(f"Plugin init error ({module_name}): {e}", timeout=5)
            except Exception as e:
                self.set_status(f"Plugin load error ({file_path}): {e}", timeout=5)

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
            f" |  v{VERSION}    |__)",
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
                for cx, char in enumerate(display_line):
                    is_sel = self.is_in_selection(file_line_idx, cx)
                    attr = curses.color_pair(4) if is_sel else 0
                    self.safe_addstr(draw_y, linenum_width + cx, char, attr)

    def draw_ui(self):
        # 1. Header
        mark_status = "[MARK]" if self.mark_pos else ""
        mod_char = " *" if self.modified else ""
        header = f" {EDITOR_NAME} v{VERSION} | {self.filename or 'New Buffer'}{mod_char}   {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(0, 0, header, curses.color_pair(1) | curses.A_BOLD)
        self.header_height = 1

        # 2. Menu Bar (Dynamic wrapping)
        # 全ショートカットの定義
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
        try: query = self.stdscr.getstr(status_y, len("Search (Regex): ")).decode('utf-8')
        except: query = ""
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
            try: fn = self.stdscr.getstr(status_y, len("Filename: ")).decode('utf-8')
            except: fn = ""
            curses.noecho()
            if fn.strip(): self.filename = fn.strip()
            else: self.set_status("Aborted", timeout=2); return

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
                except (IOError, OSError): pass

            tmp_name = f"{self.filename}.tmp"
            with open(tmp_name, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.buffer.lines))
            os.replace(tmp_name, self.filename)
            try: self.file_mtime = os.path.getmtime(self.filename)
            except Exception: self.file_mtime = None

            self.modified = False
            self.save_history(init=True)
            self.set_status(f"Saved {len(self.buffer)} lines to {self.filename}.", timeout=3)
        except Exception as e:
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
        except:
            s = ""
        curses.noecho()
        try:
            n = int(s.strip())
            self.move_cursor(max(0, min(n - 1, len(self.buffer) - 1)), 0, update_desired_x=True)
            self.set_status(f"Goto {n}", timeout=2)
        except Exception:
            self.set_status("Invalid line number.", timeout=2)

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
                except Exception:
                    pass

            self.draw_ui()
            self.draw_content()
            linenum_width = max(4, len(str(len(self.buffer)))) + 1
            
            screen_y = self.cursor_y - self.scroll_offset + self.header_height
            screen_x = self.cursor_x + linenum_width
            
            edit_height = self.get_edit_height()
            
            if 0 < screen_y <= edit_height:
                try: self.stdscr.move(screen_y, min(screen_x, self.width - 1))
                except: pass
            try:
                self.stdscr.timeout(100)
                key = self.stdscr.getch()
                self.stdscr.timeout(-1)
            except KeyboardInterrupt:
                # Ctrl+C is caught here in some environments
                key = 3 
            except curses.error: key = -1
            
            if key == -1: continue

            # --- プラグインフック ---
            if key in self.plugin_key_bindings:
                try: self.plugin_key_bindings[key](self)
                except Exception: pass
                continue

            # --- キーハンドリング ---
            if key == 3:  # Ctrl+C -> COPY
                self.perform_copy()
            elif key == 24: # Ctrl+X -> Exit
                if self.modified:
                    self.status_message = "Save changes? (y/n/Esc)"
                    self.draw_ui()
                    while True:
                        ch = self.stdscr.getch()
                        if ch in (ord('y'), ord('Y')): self.save_file(); return
                        elif ch in (ord('n'), ord('N')): return
                        elif ch == 27 or ch == 3: self.status_message = "Cancelled."; break
                else: return
            elif key == 15: self.save_file() # Ctrl+O
            elif key == 23: self.search_text() # Ctrl+W
            elif key == 30: # Ctrl+6 or Ctrl+^ (Mark)
                if self.mark_pos: self.mark_pos = None; self.set_status("Mark Unset", timeout=2)
                else: self.mark_pos = (self.cursor_y, self.cursor_x); self.set_status("Mark Set", timeout=2)
            elif key == 7: self.goto_line() # Ctrl+G
            elif key == 1: self.select_all() # Ctrl+A
            elif key == 5: self.move_cursor(self.cursor_y, len(self.buffer.lines[self.cursor_y]), update_desired_x=True) # Ctrl+E
            elif key == 31: self.toggle_comment() # Ctrl+/ (Unit Separator)
            elif key == 25: self.delete_line() # Ctrl+Y
            elif key == 11: self.perform_cut() # Ctrl+K
            elif key == 21: self.perform_paste() # Ctrl+U
            elif key == 26: self.undo() # Ctrl+Z
            elif key == 18: self.redo() # Ctrl+R
            elif key == curses.KEY_UP: self.move_cursor(self.cursor_y - 1, self.desired_x)
            elif key == curses.KEY_DOWN: self.move_cursor(self.cursor_y + 1, self.desired_x)
            elif key == curses.KEY_LEFT: self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
            elif key == curses.KEY_RIGHT: self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
            elif key == curses.KEY_PPAGE: 
                self.move_cursor(self.cursor_y - self.get_edit_height(), self.cursor_x, update_desired_x=True)
            elif key == curses.KEY_NPAGE: 
                self.move_cursor(self.cursor_y + self.get_edit_height(), self.cursor_x, update_desired_x=True)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
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
            elif key == 10 or key == 13: # Enter
                self.save_history()
                line = self.buffer.lines[self.cursor_y]
                indent = re.match(r'^(\s*)', line).group(1) if re.match(r'^(\s*)', line) else ""
                self.buffer.lines.insert(self.cursor_y + 1, indent + line[self.cursor_x:])
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x]
                self.move_cursor(self.cursor_y + 1, len(indent), update_desired_x=True)
                self.modified = True
            elif key == 9: # Tab
                self.save_history()
                tab_spaces = " " * self.config.get("tab_width", 4)
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + tab_spaces + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + len(tab_spaces), update_desired_x=True)
                self.modified = True
            elif 32 <= key <= 126:
                self.save_history()
                char = chr(key)
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
                self.modified = True

def main(stdscr):
    os.environ.setdefault('ESCDELAY', '25') 
    curses.raw()
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config()
    Editor(stdscr, fn, config).main_loop()

if __name__ == "__main__":
    try: curses.wrapper(main)
    except Exception as e:
        import traceback; traceback.print_exc()

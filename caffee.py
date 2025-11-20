#!/usr/bin/env python3
import curses
import sys
import os
import re
import json
import importlib.util
import glob
import datetime
import shutil  # 追加: ファイル操作でバックアップを作成

# --- デフォルト設定 ---
EDITOR_NAME = "CAFFEE"
VERSION = "1.1"

DEFAULT_CONFIG = {
    "tab_width": 4,
    "history_limit": 50,
    "use_soft_tabs": True,
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

    # ディレクトリがなければ作成
    if not os.path.exists(setting_dir):
        try:
            os.makedirs(setting_dir)
        except:
            pass

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
        self.plugin_commands = {} # 名前付きコマンド (将来用)

        # 色設定
        self.init_colors()

        # プラグイン読み込み
        self.load_plugins()

        # ステータス表示制御（期限付き表示）
        self.status_expire_time = None

        # ファイル変更検出用タイムスタンプ
        self.file_mtime = None
        if filename and os.path.exists(filename):
            try:
                self.file_mtime = os.path.getmtime(filename)
            except Exception:
                self.file_mtime = None

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
        """~/.caffee_setting/plugins/ からプラグインを読み込む"""
        plugin_dir = os.path.join(get_config_dir(), "plugins")
        if not os.path.exists(plugin_dir):
            try:
                os.makedirs(plugin_dir)
            except:
                return

        plugin_files = glob.glob(os.path.join(plugin_dir, "*.py"))
        loaded_count = 0
        
        for file_path in plugin_files:
            try:
                base = os.path.basename(file_path)
                if base.startswith("_"):  # アンダースコア始まりは無視
                    continue
                module_name = base[:-3]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # init(editor) 関数があれば実行
                    if hasattr(module, 'init'):
                        try:
                            module.init(self)
                            loaded_count += 1
                        except Exception as e:
                            # プラグイン個別エラーは詳細に記録
                            self.set_status(f"Plugin init error ({module_name}): {e}", timeout=5)
            except Exception as e:
                # module_name が未定義でもエラー処理できるように汎用メッセージ
                self.set_status(f"Plugin load error ({file_path}): {e}", timeout=5)

        if loaded_count > 0:
            self.set_status(f"Loaded {loaded_count} plugins.", timeout=3)

    def bind_key(self, key_code, func):
        """プラグインからキーバインドを登録する"""
        self.plugin_key_bindings[key_code] = func

    def insert_text(self, text):
        """現在位置にテキストを挿入するヘルパーメソッド"""
        self.save_history()
        
        # 複数行対応
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
            self.scroll_offset = max(0, self.cursor_y - (self.height - 3) // 2)
            self.modified = self.history_index != 0
            self.status_message = f"Applied history state {index+1}/{len(self.history)}"

    def undo(self):
        if self.history_index > 0:
            self.apply_history(self.history_index - 1)
        else:
            self.status_message = "Nothing to undo."

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.apply_history(self.history_index + 1)
        else:
            self.status_message = "Nothing to redo."

    # --- 描画 ---
    def safe_addstr(self, y, x, string, attr=0):
        try:
            if y >= self.height or x >= self.width: return
            available = self.width - x
            if len(string) > available:
                string = string[:available]
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

    def draw_content(self):
        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        edit_height = self.height - 3
        for i in range(edit_height):
            file_line_idx = self.scroll_offset + i
            draw_y = i + 1
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
        mark_status = "[MARK]" if self.mark_pos else ""
        mod_char = " *" if self.modified else ""
        header = f" {EDITOR_NAME} v{VERSION} | {self.filename or 'New Buffer'}{mod_char}   {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(0, 0, header, curses.color_pair(1) | curses.A_BOLD)

        menu = "^X Exit  ^O Save  ^W Search  ^K Cut  ^U Paste  ^6 Mark  ^Z Undo  ^A All  ^G Goto"
        self.safe_addstr(self.height - 1, 0, menu.ljust(self.width), curses.color_pair(1))

        # ステータス表示（期限付き）
        now = datetime.datetime.now()
        if self.status_message:
            if not self.status_expire_time or now <= self.status_expire_time:
                status_line = self.status_message.ljust(self.width - 10)
                self.safe_addstr(self.height - 2, 0, status_line, curses.color_pair(2))
            else:
                # 期限切れ
                self.status_message = ""
                self.status_expire_time = None

        pos_info = f" {self.cursor_y + 1}:{self.cursor_x + 1} "
        self.safe_addstr(self.height - 2, self.width - len(pos_info), pos_info, curses.color_pair(1))

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

        edit_height = self.height - 3
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
        # 先に選択範囲を取得しておく（perform_copy が mark_pos をクリアするため）
        sel = self.get_selection_range()
        if not sel:
            # 選択がない場合は現在行を切り取る
            if len(self.buffer) > 0:
                self.clipboard = [self.buffer.lines.pop(self.cursor_y)]
                if not self.buffer.lines: self.buffer.lines = [""]
                self.move_cursor(self.cursor_y, 0)
                self.modified = True
                # 状態表示は短時間表示にする
                try:
                    self.set_status("Cut line.", timeout=2)
                except Exception:
                    self.status_message = "Cut line."
            return

        # 選択がある場合はコピーしてから削除処理（copy は mark_pos をクリアする）
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
        try:
            self.set_status("Cut selection.", timeout=2)
        except Exception:
            self.status_message = "Cut selection."

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
        # 既存の簡易検索に加えて、先頭から検索するオプションを保持（変更少）
        self.set_status("Search: ", timeout=30)
        self.draw_ui()
        curses.echo()
        try: query = self.stdscr.getstr(self.height - 2, len("Search: ")).decode('utf-8')
        except: query = ""
        curses.noecho()
        if not query: 
            self.set_status("Search aborted.", timeout=2)
            return
        found = False
        start_y = self.cursor_y
        start_x = self.cursor_x
        line = self.buffer.lines[start_y]
        idx = line.find(query, start_x + 1)
        if idx != -1:
            self.cursor_y, self.cursor_x = start_y, idx
            found = True
        else:
            for i in range(start_y + 1, len(self.buffer)):
                idx = self.buffer.lines[i].find(query)
                if idx != -1:
                    self.cursor_y, self.cursor_x = i, idx
                    found = True
                    break
            if not found:
                for i in range(0, start_y + 1):
                    limit = start_x if i == start_y else len(self.buffer.lines[i])
                    idx = self.buffer.lines[i].find(query)
                    if idx != -1 and idx < limit:
                        self.cursor_y, self.cursor_x = i, idx
                        found = True
                        break
        if found:
            self.move_cursor(self.cursor_y, self.cursor_x, update_desired_x=True)
            self.set_status(f"Found '{query}'", timeout=3)
        else:
            self.set_status(f"Not found '{query}'", timeout=3)

    def set_status(self, msg, timeout=3):
        """ステータスメッセージを一定時間表示する"""
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
            try: fn = self.stdscr.getstr(self.height - 2, len("Filename: ")).decode('utf-8')
            except: fn = ""
            curses.noecho()
            if fn.strip(): self.filename = fn.strip()
            else: self.set_status("Aborted", timeout=2); return

        try:
            # 既存ファイルがあればバックアップを作成
            if os.path.exists(self.filename):
                try:
                    bak_name = f"{self.filename}.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                    shutil.copy2(self.filename, bak_name)
                except Exception:
                    # バックアップ失敗でも保存処理は続ける
                    pass

            tmp_name = f"{self.filename}.tmp"
            with open(tmp_name, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.buffer.lines))
            # 原子的に置換
            os.replace(tmp_name, self.filename)
            # 更新時刻を記録
            try:
                self.file_mtime = os.path.getmtime(self.filename)
            except Exception:
                self.file_mtime = None

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
            # 全選択: 最初から最後までを選択
            last_y = len(self.buffer) - 1
            last_x = len(self.buffer[last_y]) if self.buffer.lines else 0
            self.mark_pos = (0, 0)
            self.move_cursor(last_y, last_x, update_desired_x=True)
            self.set_status("Selected all.", timeout=2)

    def goto_line(self):
        self.set_status("Goto line: ", timeout=10)
        self.draw_ui()
        curses.echo()
        try:
            s = self.stdscr.getstr(self.height - 2, len("Goto line: ")).decode('utf-8')
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
            # 外部でファイルが更新されているか確認（通知のみ）
            if self.filename and os.path.exists(self.filename):
                try:
                    mtime = os.path.getmtime(self.filename)
                    if self.file_mtime and mtime != self.file_mtime:
                        self.set_status("File changed on disk.", timeout=5)
                        # 更新時刻を更新（自動リロードはしない）
                        self.file_mtime = mtime
                except Exception:
                    pass

            self.draw_ui()
            self.draw_content()
            linenum_width = max(4, len(str(len(self.buffer)))) + 1
            screen_y = self.cursor_y - self.scroll_offset + 1
            screen_x = self.cursor_x + linenum_width
            if 0 < screen_y < self.height - 2:
                try: self.stdscr.move(screen_y, min(screen_x, self.width - 1))
                except: pass
            try:
                self.stdscr.timeout(100)
                key = self.stdscr.getch()
                self.stdscr.timeout(-1)
            except curses.error: key = -1
            except KeyboardInterrupt: key = 24
            if key == -1: continue

            # --- プラグインフック ---
            if key in self.plugin_key_bindings:
                try:
                    self.plugin_key_bindings[key](self)
                except Exception as e:
                    self.set_status(f"Plugin Exception: {e}", timeout=5)
                continue

            # --- 標準キー操作 ---
            if key == 24: # Ctrl+X
                if self.modified:
                    self.status_message = "Save changes? (y/n/Esc)"
                    self.draw_ui()
                    while True:
                        ch = self.stdscr.getch()
                        if ch in (ord('y'), ord('Y')): self.save_file(); return
                        elif ch in (ord('n'), ord('N')): return
                        elif ch == 27: self.status_message = "Cancelled."; break
                else: return
            elif key == 15: self.save_file() # Ctrl+O
            elif key == 23: self.search_text() # Ctrl+W
            elif key == 30: # Ctrl+6 (Mark)
                if self.mark_pos: self.mark_pos = None; self.set_status("Mark Unset", timeout=2)
                else: self.mark_pos = (self.cursor_y, self.cursor_x); self.set_status("Mark Set", timeout=2)
            elif key == 7: self.goto_line() # Ctrl+G
            elif key == 1: self.select_all() # Ctrl+A
            elif key == 5: self.move_cursor(self.cursor_y, len(self.buffer.lines[self.cursor_y]), update_desired_x=True) # Ctrl+E
            elif key == 31: self.toggle_comment() # Ctrl+/
            elif key == 25: self.delete_line() # Ctrl+Y
            elif key == 11: self.perform_cut() # Ctrl+K
            elif key == 21: self.perform_paste() # Ctrl+U
            elif key == 26: self.undo() # Ctrl+Z
            elif key == 18: self.redo() # Ctrl+R
            elif key == 27: # Alt
                self.stdscr.nodelay(True)
                next_ch = self.stdscr.getch()
                self.stdscr.nodelay(False)
                if next_ch == ord('6'): self.perform_copy()
                else: pass
            elif key == curses.KEY_UP: self.move_cursor(self.cursor_y - 1, self.desired_x)
            elif key == curses.KEY_DOWN: self.move_cursor(self.cursor_y + 1, self.desired_x)
            elif key == curses.KEY_LEFT: self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
            elif key == curses.KEY_RIGHT: self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
            elif key == curses.KEY_PPAGE: self.move_cursor(self.cursor_y - (self.height - 3), self.cursor_x, update_desired_x=True)
            elif key == curses.KEY_NPAGE: self.move_cursor(self.cursor_y + (self.height - 3), self.cursor_x, update_desired_x=True)
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
    # こちらはそのままでも良いが cbreak を併用して堅牢化できる
    # curses.cbreak()
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config()
    Editor(stdscr, fn, config).main_loop()

if __name__ == "__main__":
    try: curses.wrapper(main)
    except Exception as e:
        import traceback; traceback.print_exc()

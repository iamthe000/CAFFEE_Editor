#!/usr/bin/env python3
import curses
import sys
import os
import re

# --- 設定 ---
EDITOR_NAME = "CAFFEE"
VERSION = "2.0.0 (Barista)"
# タブのスペース数
TAB_WIDTH = 4

class Buffer:
    def __init__(self, lines=None):
        self.lines = lines if lines else [""]
    
    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

class Editor:
    def __init__(self, stdscr, filename=None):
        self.stdscr = stdscr
        self.filename = filename
        self.buffer = Buffer()
        
        # カーソル・表示関連
        self.cursor_y = 0
        self.cursor_x = 0
        self.scroll_offset = 0
        self.desired_x = 0 # 上下移動時の理想的なX位置記憶用
        
        # 状態管理
        self.status_message = ""
        self.modified = False
        self.clipboard = [] # クリップボードはリスト（複数行対応）
        
        # 選択モード (Mark)
        self.mark_pos = None # (y, x) or None
        
        # 画面サイズ
        self.height, self.width = stdscr.getmaxyx()
        
        # 色設定
        self.init_colors()

        # ファイル読み込み
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                    if not content: content = [""]
                    self.buffer.lines = content
            except Exception as e:
                self.status_message = f"Error: {e}"
        
        # 新規ならスタート画面
        if not filename or (filename and not os.path.exists(filename)):
             self.show_start_screen()

    def init_colors(self):
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            try:
                # 1: ヘッダー/フッター (黒文字/白背景)
                curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
                # 2: エラー/通知 (白文字/赤背景)
                curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
                # 3: 行番号 (青文字/デフォルト背景)
                curses.init_pair(3, curses.COLOR_CYAN, -1)
                # 4: 選択範囲 (黒文字/シアン背景)
                curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
            except:
                pass

    def safe_addstr(self, y, x, string, attr=0):
        """安全な描画関数 (右下クラッシュ対策)"""
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
            " .-'-------|",
            " | CAFFEE  |__",
            " |  v1.0   |__)",
            " |_________|",
            "  `-------' "
        ]
        my = self.height // 2 - 6
        mx = self.width // 2
        for i, l in enumerate(logo):
            if my + i < self.height - 2:
                self.safe_addstr(my + i, max(0, mx - 10), l)
        
        self.safe_addstr(my + len(logo) + 1, max(0, mx - 12), "CAFFEE Editor v1.0", curses.A_BOLD)
        self.safe_addstr(my + len(logo) + 3, max(0, mx - 15), "Press any key to brew...", curses.A_DIM)
        self.stdscr.refresh()
        self.stdscr.getch()

    def get_selection_range(self):
        """現在のカーソルとマーク位置から、開始点と終了点を計算"""
        if not self.mark_pos:
            return None
        
        p1 = self.mark_pos
        p2 = (self.cursor_y, self.cursor_x)
        
        # p1がp2より後ろにある場合入れ替え
        if p1 > p2:
            return p2, p1
        return p1, p2

    def is_in_selection(self, y, x):
        """指定座標が選択範囲内か判定"""
        sel = self.get_selection_range()
        if not sel: return False
        start, end = sel
        
        # 現在の座標
        curr = (y, x)
        
        if start[0] == end[0]: # 同じ行の場合
            return y == start[0] and start[1] <= x < end[1]
        
        # 複数行の場合
        if y == start[0]: return x >= start[1]
        if y == end[0]: return x < end[1]
        return start[0] < y < end[0]

    def draw_content(self):
        # 行番号表示のためのマージン計算 (最低4桁)
        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        edit_height = self.height - 3
        
        for i in range(edit_height):
            file_line_idx = self.scroll_offset + i
            draw_y = i + 1
            
            # 行番号エリアのクリア
            self.safe_addstr(draw_y, 0, " " * linenum_width)
            
            if file_line_idx >= len(self.buffer):
                self.safe_addstr(draw_y, 0, "~", curses.color_pair(3))
            else:
                # 行番号描画
                ln_str = str(file_line_idx + 1).rjust(linenum_width - 1) + " "
                self.safe_addstr(draw_y, 0, ln_str, curses.color_pair(3))

                line = self.buffer[file_line_idx]
                # 表示領域の計算
                max_content_width = self.width - linenum_width
                display_line = line[:max_content_width]

                # 1文字ずつ描画 (ハイライト判定のため)
                # 高速化のため、選択モードでないときは一括描画
                if not self.mark_pos:
                    self.safe_addstr(draw_y, linenum_width, display_line)
                else:
                    for cx, char in enumerate(display_line):
                        is_sel = self.is_in_selection(file_line_idx, cx)
                        attr = curses.color_pair(4) if is_sel else 0
                        self.safe_addstr(draw_y, linenum_width + cx, char, attr)

    def draw_ui(self):
        # Header
        mark_status = "[MARK]" if self.mark_pos else ""
        mod_char = " *" if self.modified else ""
        header = f" {EDITOR_NAME} {VERSION} | {self.filename or 'New Buffer'}{mod_char}   {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(0, 0, header, curses.color_pair(1) | curses.A_BOLD)

        # Footer Menu
        menu = "^X Exit  ^O Save  ^W Where  ^K Cut  ^U Paste  ^6 Mark  Alt+6 Copy"
        self.safe_addstr(self.height - 1, 0, menu.ljust(self.width), curses.color_pair(1))

        # Status Bar
        if self.status_message:
            self.safe_addstr(self.height - 2, 0, self.status_message.ljust(self.width), curses.color_pair(2))
            self.status_message = ""

    def move_cursor(self, y, x):
        self.cursor_y = max(0, min(y, len(self.buffer) - 1))
        line_len = len(self.buffer[self.cursor_y])
        self.cursor_x = max(0, min(x, line_len))
        
        # スクロール調整
        edit_height = self.height - 3
        if self.cursor_y < self.scroll_offset:
            self.scroll_offset = self.cursor_y
        elif self.cursor_y >= self.scroll_offset + edit_height:
            self.scroll_offset = self.cursor_y - edit_height + 1

    def perform_copy(self):
        """選択範囲をコピー"""
        sel = self.get_selection_range()
        if not sel:
            self.status_message = "No selection to copy."
            return
        
        start, end = sel
        self.clipboard = []
        
        # 単一行コピー
        if start[0] == end[0]:
            txt = self.buffer.lines[start[0]][start[1]:end[1]]
            self.clipboard.append(txt)
        else:
            # 複数行コピー
            # 最初の行
            self.clipboard.append(self.buffer.lines[start[0]][start[1]:])
            # 中間の行
            for i in range(start[0] + 1, end[0]):
                self.clipboard.append(self.buffer.lines[i])
            # 最後の行
            self.clipboard.append(self.buffer.lines[end[0]][:end[1]])
            
        self.status_message = f"Copied {len(self.clipboard)} lines."
        self.mark_pos = None # コピーしたら選択解除

    def perform_cut(self):
        """選択範囲、または行をカット"""
        if not self.mark_pos:
            # 行カット (通常モード)
            if len(self.buffer) > 0:
                self.clipboard = [self.buffer.lines.pop(self.cursor_y)]
                if not self.buffer.lines: self.buffer.lines = [""]
                self.cursor_y = min(self.cursor_y, len(self.buffer) - 1)
                self.cursor_x = 0
                self.modified = True
                self.status_message = "Cut line."
            return

        # 範囲カット
        self.perform_copy() # まずコピー
        start, end = self.get_selection_range()
        
        # テキスト削除処理
        if start[0] == end[0]:
            line = self.buffer.lines[start[0]]
            self.buffer.lines[start[0]] = line[:start[1]] + line[end[1]:]
        else:
            line_start = self.buffer.lines[start[0]][:start[1]]
            line_end = self.buffer.lines[end[0]][end[1]:]
            # 間の行を削除
            del self.buffer.lines[start[0]:end[0]+1]
            # 結合した行を挿入
            self.buffer.lines.insert(start[0], line_start + line_end)
        
        self.cursor_y, self.cursor_x = start
        self.mark_pos = None
        self.modified = True
        self.status_message = "Cut selection."

    def perform_paste(self):
        """クリップボードの内容をペースト"""
        if not self.clipboard:
            self.status_message = "Clipboard empty."
            return
        
        # カーソル位置の行を分割
        current_line = self.buffer.lines[self.cursor_y]
        prefix = current_line[:self.cursor_x]
        suffix = current_line[self.cursor_x:]
        
        if len(self.clipboard) == 1:
            # 単一行ペースト
            new_line = prefix + self.clipboard[0] + suffix
            self.buffer.lines[self.cursor_y] = new_line
            self.cursor_x += len(self.clipboard[0])
        else:
            # 複数行ペースト
            self.buffer.lines[self.cursor_y] = prefix + self.clipboard[0]
            for i in range(1, len(self.clipboard) - 1):
                self.buffer.lines.insert(self.cursor_y + i, self.clipboard[i])
            self.buffer.lines.insert(self.cursor_y + len(self.clipboard) - 1, self.clipboard[-1] + suffix)
            # カーソル位置更新
            self.cursor_y += len(self.clipboard) - 1
            self.cursor_x = len(self.clipboard[-1])
            
        self.modified = True
        self.status_message = "Pasted."

    def search_text(self):
        """簡易検索"""
        self.status_message = "Search: "
        self.draw_ui()
        curses.echo()
        try:
            query = self.stdscr.getstr(self.height - 2, 8).decode('utf-8')
        except:
            query = ""
        curses.noecho()
        
        if not query: return

        # 現在位置から検索
        found = False
        # 現在行の残りから
        line = self.buffer.lines[self.cursor_y]
        idx = line.find(query, self.cursor_x + 1)
        if idx != -1:
            self.cursor_x = idx
            found = True
        else:
            # 次の行から最後まで
            for i in range(self.cursor_y + 1, len(self.buffer)):
                idx = self.buffer.lines[i].find(query)
                if idx != -1:
                    self.cursor_y = i
                    self.cursor_x = idx
                    found = True
                    break
            # 見つからなければ最初から現在行まで
            if not found:
                for i in range(0, self.cursor_y + 1):
                    idx = self.buffer.lines[i].find(query)
                    if idx != -1:
                        self.cursor_y = i
                        self.cursor_x = idx
                        found = True
                        break
        
        if found:
            self.move_cursor(self.cursor_y, self.cursor_x)
            self.status_message = f"Found '{query}'"
        else:
            self.status_message = "Not found."

    def main_loop(self):
        while True:
            self.stdscr.erase()
            self.height, self.width = self.stdscr.getmaxyx()
            
            self.draw_ui()
            self.draw_content()

            # カーソル位置計算 (行番号分ずらす)
            linenum_width = max(4, len(str(len(self.buffer)))) + 1
            screen_y = self.cursor_y - self.scroll_offset + 1
            screen_x = self.cursor_x + linenum_width
            
            if 0 < screen_y < self.height - 2:
                try:
                    self.stdscr.move(screen_y, min(screen_x, self.width - 1))
                except: pass

            try:
                key = self.stdscr.getch()
            except KeyboardInterrupt:
                key = 24

            # --- キーハンドリング ---
            
            # Exit (Ctrl+X)
            if key == 24:
                if self.modified:
                    self.status_message = "Save changes? (y/n/Esc)"
                    self.draw_ui()
                    while True:
                        ch = self.stdscr.getch()
                        if ch in (ord('y'), ord('Y')):
                            self.save_file(); return
                        elif ch in (ord('n'), ord('N')):
                            return
                        elif ch == 27:
                            self.status_message = "Cancelled."; break
                else:
                    return

            # Save (Ctrl+O)
            elif key == 15: self.save_file()
            
            # Search (Ctrl+W)
            elif key == 23: self.search_text()

            # Mark Set (Ctrl+6 or Ctrl+^)
            elif key == 30: # Ctrl+6 (often sends 30 or ^^)
                if self.mark_pos:
                    self.mark_pos = None
                    self.status_message = "Mark Unset"
                else:
                    self.mark_pos = (self.cursor_y, self.cursor_x)
                    self.status_message = "Mark Set"

            # Copy (Alt+6 or Esc then 6)
            elif key == 27: # ESC sequence
                self.stdscr.nodelay(True)
                next_ch = self.stdscr.getch()
                self.stdscr.nodelay(False)
                if next_ch == ord('6'): # Esc + 6 = Copy
                    self.perform_copy()
                else:
                    # Esc単体の場合は何もしない、あるいはMark解除など
                    pass
            
            # Cut (Ctrl+K)
            elif key == 11: self.perform_cut()
            
            # Paste (Ctrl+U)
            elif key == 21: self.perform_paste()

            # Navigation
            elif key == curses.KEY_UP:
                self.move_cursor(self.cursor_y - 1, self.desired_x)
                self.cursor_x = min(self.cursor_x, len(self.buffer[self.cursor_y]))
            elif key == curses.KEY_DOWN:
                self.move_cursor(self.cursor_y + 1, self.desired_x)
                self.cursor_x = min(self.cursor_x, len(self.buffer[self.cursor_y]))
            elif key == curses.KEY_LEFT:
                self.move_cursor(self.cursor_y, self.cursor_x - 1)
                self.desired_x = self.cursor_x
            elif key == curses.KEY_RIGHT:
                self.move_cursor(self.cursor_y, self.cursor_x + 1)
                self.desired_x = self.cursor_x
            
            # PageUp/Down
            elif key == curses.KEY_PPAGE:
                 self.move_cursor(self.cursor_y - (self.height - 3), self.cursor_x)
            elif key == curses.KEY_NPAGE:
                 self.move_cursor(self.cursor_y + (self.height - 3), self.cursor_x)

            # Editing
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if self.mark_pos: # 選択中にBS押すと選択範囲削除（便利機能）
                    self.perform_cut() # クリップボードには入るが削除動作
                elif self.cursor_x > 0:
                    line = self.buffer.lines[self.cursor_y]
                    self.buffer.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
                    self.move_cursor(self.cursor_y, self.cursor_x - 1)
                    self.modified = True
                elif self.cursor_y > 0:
                    prev_len = len(self.buffer.lines[self.cursor_y - 1])
                    self.buffer.lines[self.cursor_y - 1] += self.buffer.lines[self.cursor_y]
                    del self.buffer.lines[self.cursor_y]
                    self.move_cursor(self.cursor_y - 1, prev_len)
                    self.modified = True

            elif key == 10 or key == 13: # Enter
                line = self.buffer.lines[self.cursor_y]
                # 自動インデント (簡易)
                indent = ""
                m = re.match(r'^(\s+)', line)
                if m: indent = m.group(1)
                
                self.buffer.lines.insert(self.cursor_y + 1, indent + line[self.cursor_x:])
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x]
                self.move_cursor(self.cursor_y + 1, len(indent))
                self.modified = True

            elif 32 <= key <= 126:
                char = chr(key)
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + 1)
                self.modified = True

    def save_file(self):
        if not self.filename:
            self.status_message = "Filename: "
            self.draw_ui()
            curses.echo()
            try: fn = self.stdscr.getstr(self.height - 2, 10).decode('utf-8')
            except: fn = ""
            curses.noecho()
            if fn.strip(): self.filename = fn.strip()
            else: self.status_message = "Aborted"; return

        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.buffer.lines))
            self.modified = False
            self.status_message = f"Saved {len(self.buffer)} lines."
        except Exception as e: self.status_message = f"Error: {e}"

def main(stdscr):
    curses.raw()
    os.environ.setdefault('ESCDELAY', '25')
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    Editor(stdscr, fn).main_loop()

if __name__ == "__main__":
    try: curses.wrapper(main)
    except Exception as e:
        # 重大なエラー時
        import traceback; traceback.print_exc()

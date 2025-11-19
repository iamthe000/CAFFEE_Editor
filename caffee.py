#!/usr/bin/env python3
import curses
import sys
import os
import re

# --- 設定 ---
EDITOR_NAME = "CAFFEE"
VERSION = "1.0"
# タブのスペース数
TAB_WIDTH = 4
# 履歴を保存する最大数
HISTORY_LIMIT = 50

class Buffer:
    """エディタのテキスト内容を保持するクラス"""
    def __init__(self, lines=None):
        self.lines = lines if lines else [""]
    
    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]
    
    def get_content(self):
        """現在の全行リストを返す"""
        return self.lines[:]
    
    def set_content(self, lines):
        """全行リストを設定する"""
        self.lines = lines
    
    def clone(self):
        """内容をディープコピーした新しいバッファインスタンスを返す"""
        return Buffer([line for line in self.lines])

class Editor:
    def __init__(self, stdscr, filename=None):
        self.stdscr = stdscr
        self.filename = filename
        
        # 初期バッファ設定
        initial_lines = self.load_file(filename)
        self.buffer = Buffer(initial_lines)
        
        # カーソル・表示関連
        self.cursor_y = 0
        self.cursor_x = 0
        self.scroll_offset = 0
        self.desired_x = 0 # 上下移動時の理想的なX位置記憶用
        
        # 状態管理
        self.status_message = ""
        self.modified = False
        self.clipboard = []
        
        # 選択モード (Mark)
        self.mark_pos = None # (y, x) or None
        
        # 履歴管理 (Undo/Redo用)
        # 履歴は (lines, cursor_y, cursor_x) のタプルを保存
        self.history = []
        self.history_index = -1
        self.save_history(init=True) # 初期状態を履歴に保存
        
        # 画面サイズ
        self.height, self.width = stdscr.getmaxyx()
        
        # 色設定
        self.init_colors()

        # 新規ならスタート画面
        if not filename or not os.path.exists(filename):
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

    def load_file(self, filename):
        """ファイル読み込み処理を分離"""
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                    return content if content else [""]
            except Exception as e:
                self.status_message = f"Error loading file: {e}"
                return [""]
        return [""]

    def save_history(self, init=False):
        """現在の状態を履歴に保存する"""
        
        # カーソル情報を含むスナップショットを作成
        snapshot = (self.buffer.get_content(), self.cursor_y, self.cursor_x)
        
        # 履歴の末尾を切り捨てる (Redoの破棄)
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
            
        # 履歴が重複する場合は保存しない (例えばカーソル移動のみの場合)
        if not init and self.history and self.history[-1][0] == snapshot[0]:
            return
            
        self.history.append(snapshot)
        self.history_index = len(self.history) - 1

        # 履歴サイズ制限
        if len(self.history) > HISTORY_LIMIT:
            self.history.pop(0)
            self.history_index -= 1
            
        # 履歴に保存されたら modified フラグはリセット（ファイル保存時以外は基本的にTrueに）
        if not init:
            self.modified = True

    def apply_history(self, index):
        """指定された履歴インデックスの状態に戻す"""
        if 0 <= index < len(self.history):
            self.history_index = index
            snapshot = self.history[index]
            
            # バッファ内容の復元
            self.buffer.set_content(snapshot[0])
            
            # カーソル位置の復元と調整
            self.move_cursor(snapshot[1], snapshot[2], update_desired_x=True, check_bounds=True)
            self.scroll_offset = max(0, self.cursor_y - (self.height - 3) // 2)
            
            self.modified = self.history_index != 0
            self.status_message = f"Applied history state {index+1}/{len(self.history)}"

    def undo(self):
        """一つ前の状態に戻す"""
        if self.history_index > 0:
            self.apply_history(self.history_index - 1)
        else:
            self.status_message = "Nothing to undo."

    def redo(self):
        """一つ先の状態に進める"""
        if self.history_index < len(self.history) - 1:
            self.apply_history(self.history_index + 1)
        else:
            self.status_message = "Nothing to redo."

    # --- ユーティリティメソッド (既存の改善) ---
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
        """現在のカーソルとマーク位置から、開始点と終了点を計算"""
        if not self.mark_pos:
            return None
        
        p1 = self.mark_pos
        p2 = (self.cursor_y, self.cursor_x)
        
        if p1 > p2:
            return p2, p1
        return p1, p2

    def is_in_selection(self, y, x):
        """指定座標が選択範囲内か判定"""
        sel = self.get_selection_range()
        if not sel: return False
        start, end = sel
        
        if start[0] == end[0]:
            return y == start[0] and start[1] <= x < end[1]
        
        if y == start[0]: return x >= start[1]
        if y == end[0]: return x < end[1]
        return start[0] < y < end[0]

    def draw_content(self):
        linenum_width = max(4, len(str(len(self.buffer)))) + 1
        edit_height = self.height - 3
        
        for i in range(edit_height):
            file_line_idx = self.scroll_offset + i
            draw_y = i + 1
            
            self.safe_addstr(draw_y, 0, " " * self.width) # 行全体をクリア
            
            if file_line_idx >= len(self.buffer):
                self.safe_addstr(draw_y, 0, "~", curses.color_pair(3))
            else:
                # 行番号描画
                ln_str = str(file_line_idx + 1).rjust(linenum_width - 1) + " "
                self.safe_addstr(draw_y, 0, ln_str, curses.color_pair(3))

                line = self.buffer[file_line_idx]
                max_content_width = self.width - linenum_width
                display_line = line[:max_content_width]

                # 選択範囲のハイライトを考慮した描画
                for cx, char in enumerate(display_line):
                    is_sel = self.is_in_selection(file_line_idx, cx)
                    attr = curses.color_pair(4) if is_sel else 0
                    self.safe_addstr(draw_y, linenum_width + cx, char, attr)

    def draw_ui(self):
        # Header
        mark_status = "[MARK]" if self.mark_pos else ""
        mod_char = " *" if self.modified else ""
        header = f" {EDITOR_NAME} v{VERSION} | {self.filename or 'New Buffer'}{mod_char}   {mark_status}"
        header = header.ljust(self.width)
        self.safe_addstr(0, 0, header, curses.color_pair(1) | curses.A_BOLD)

        # Footer Menu (Undo/Redoを追加)
        menu = "^X Exit  ^O Save  ^W Where  ^K Cut  ^U Paste  ^6 Mark  ^/ Comment  ^Y DelLine  ^E LineEnd  ^Z Undo  ^R Redo"
        self.safe_addstr(self.height - 1, 0, menu.ljust(self.width), curses.color_pair(1))

        # Status Bar
        status_line = self.status_message.ljust(self.width - 10) # 10文字分は位置情報に
        if self.status_message:
            self.safe_addstr(self.height - 2, 0, status_line, curses.color_pair(2))
            self.status_message = ""
            
        # カーソル位置表示 (行:列)
        pos_info = f" {self.cursor_y + 1}:{self.cursor_x + 1} "
        self.safe_addstr(self.height - 2, self.width - len(pos_info), pos_info, curses.color_pair(1))

    def move_cursor(self, y, x, update_desired_x=False, check_bounds=False):
        """カーソル移動とスクロール調整"""
        
        # y座標の調整
        new_y = max(0, min(y, len(self.buffer) - 1))
        
        # x座標の調整
        line_len = len(self.buffer[new_y])
        new_x = max(0, min(x, line_len))
        
        if check_bounds:
            # 履歴適用時など、カーソルが不正な位置にないかチェック
            if new_x > line_len: new_x = line_len
            if new_y >= len(self.buffer): new_y = max(0, len(self.buffer) - 1)
        
        self.cursor_y = new_y
        self.cursor_x = new_x
        
        if update_desired_x:
             self.desired_x = self.cursor_x

        # スクロール調整
        edit_height = self.height - 3
        if self.cursor_y < self.scroll_offset:
            self.scroll_offset = self.cursor_y
        elif self.cursor_y >= self.scroll_offset + edit_height:
            self.scroll_offset = self.cursor_y - edit_height + 1

    # --- 編集/クリップボード (履歴保存を追加) ---
    
    def perform_copy(self):
        """選択範囲をコピー"""
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
        """選択範囲、または行をカットし、履歴に保存"""
        self.save_history()
        
        if not self.mark_pos:
            if len(self.buffer) > 0:
                self.clipboard = [self.buffer.lines.pop(self.cursor_y)]
                if not self.buffer.lines: self.buffer.lines = [""]
                self.move_cursor(self.cursor_y, 0)
                self.modified = True
                self.status_message = "Cut line."
            return

        self.perform_copy() # まずコピー
        start, end = self.get_selection_range()
        
        # テキスト削除処理
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
        self.status_message = "Cut selection."

    def perform_paste(self):
        """クリップボードの内容をペーストし、履歴に保存"""
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
        """現在の行をコメントアウト/解除 (#)し、履歴に保存"""
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
        """現在の行を削除し、クリップボードに入れない (Ctrl+Y)し、履歴に保存"""
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
        """簡易検索ロジック (既存)"""
        self.status_message = "Search: "
        self.draw_ui()
        curses.echo()
        try: query = self.stdscr.getstr(self.height - 2, len("Search: ")).decode('utf-8')
        except: query = ""
        curses.noecho()
        
        if not query: 
            self.status_message = "Search aborted."
            return

        found = False
        start_y = self.cursor_y
        start_x = self.cursor_x

        # 現在位置の次の文字から検索
        line = self.buffer.lines[start_y]
        idx = line.find(query, start_x + 1)

        if idx != -1:
            self.cursor_y, self.cursor_x = start_y, idx
            found = True
        else:
            # 次の行から最後まで
            for i in range(start_y + 1, len(self.buffer)):
                idx = self.buffer.lines[i].find(query)
                if idx != -1:
                    self.cursor_y, self.cursor_x = i, idx
                    found = True
                    break
            # 見つからなければ最初から現在行まで（ラップアラウンド）
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
            self.status_message = f"Found '{query}'"
        else:
            self.status_message = f"Not found '{query}'"

    def main_loop(self):
        while True:
            self.stdscr.erase()
            self.height, self.width = self.stdscr.getmaxyx()
            
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

            # --- キーハンドリング ---
            
            # Exit (Ctrl+X)
            if key == 24:
                if self.modified:
                    self.status_message = "Save changes? (y/n/Esc)"
                    self.draw_ui()
                    while True:
                        ch = self.stdscr.getch()
                        if ch in (ord('y'), ord('Y')): self.save_file(); return
                        elif ch in (ord('n'), ord('N')): return
                        elif ch == 27: self.status_message = "Cancelled."; break
                else: return

            # Save (Ctrl+O)
            elif key == 15: self.save_file()
            
            # Search (Ctrl+W)
            elif key == 23: self.search_text()

            # Mark Set (Ctrl+6 or Ctrl+^)
            elif key == 30:
                if self.mark_pos: self.mark_pos = None; self.status_message = "Mark Unset"
                else: self.mark_pos = (self.cursor_y, self.cursor_x); self.status_message = "Mark Set"
            
            # Line End (Ctrl+E)
            elif key == 5:
                self.move_cursor(self.cursor_y, len(self.buffer.lines[self.cursor_y]), update_desired_x=True)

            # Comment Toggle (Ctrl+/)
            elif key == 31: self.toggle_comment()
            
            # Delete Line (Ctrl+Y)
            elif key == 25: self.delete_line()

            # Cut (Ctrl+K)
            elif key == 11: self.perform_cut()
            
            # Paste (Ctrl+U)
            elif key == 21: self.perform_paste()
            
            # Undo (Ctrl+Z) - 新機能
            elif key == 26: self.undo()
            
            # Redo (Ctrl+R) - 新機能
            elif key == 18: self.redo()

            # Alt+6 (Copy)
            elif key == 27:
                self.stdscr.nodelay(True)
                next_ch = self.stdscr.getch()
                self.stdscr.nodelay(False)
                if next_ch == ord('6'): self.perform_copy()
                else: pass

            # Navigation
            elif key == curses.KEY_UP:
                self.move_cursor(self.cursor_y - 1, self.desired_x)
            elif key == curses.KEY_DOWN:
                self.move_cursor(self.cursor_y + 1, self.desired_x)
            elif key == curses.KEY_LEFT:
                self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
            elif key == curses.KEY_RIGHT:
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
            
            # PageUp/Down
            elif key == curses.KEY_PPAGE:
                 self.move_cursor(self.cursor_y - (self.height - 3), self.cursor_x, update_desired_x=True)
            elif key == curses.KEY_NPAGE:
                 self.move_cursor(self.cursor_y + (self.height - 3), self.cursor_x, update_desired_x=True)

            # Editing (文字入力、改行、BS)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if self.mark_pos:
                    self.perform_cut() 
                elif self.cursor_x > 0:
                    self.save_history() # BS/Delも履歴に保存
                    line = self.buffer.lines[self.cursor_y]
                    self.buffer.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
                    self.move_cursor(self.cursor_y, self.cursor_x - 1, update_desired_x=True)
                    self.modified = True
                elif self.cursor_y > 0:
                    self.save_history() # 行結合も履歴に保存
                    prev_len = len(self.buffer.lines[self.cursor_y - 1])
                    self.buffer.lines[self.cursor_y - 1] += self.buffer.lines[self.cursor_y]
                    del self.buffer.lines[self.cursor_y]
                    self.move_cursor(self.cursor_y - 1, prev_len, update_desired_x=True)
                    self.modified = True

            elif key == 10 or key == 13: # Enter
                self.save_history() # Enterも履歴に保存
                line = self.buffer.lines[self.cursor_y]
                # 自動インデント (簡易)
                indent = re.match(r'^(\s*)', line).group(1) if re.match(r'^(\s*)', line) else ""
                
                self.buffer.lines.insert(self.cursor_y + 1, indent + line[self.cursor_x:])
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x]
                self.move_cursor(self.cursor_y + 1, len(indent), update_desired_x=True)
                self.modified = True

            elif 32 <= key <= 126: # 通常文字入力
                self.save_history() # 文字入力も履歴に保存
                char = chr(key)
                line = self.buffer.lines[self.cursor_y]
                self.buffer.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x:]
                self.move_cursor(self.cursor_y, self.cursor_x + 1, update_desired_x=True)
                self.modified = True

    def save_file(self):
        if not self.filename:
            self.status_message = "Filename: "
            self.draw_ui()
            curses.echo()
            try: fn = self.stdscr.getstr(self.height - 2, len("Filename: ")).decode('utf-8')
            except: fn = ""
            curses.noecho()
            if fn.strip(): self.filename = fn.strip()
            else: self.status_message = "Aborted"; return

        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.buffer.lines))
            self.modified = False
            self.save_history(init=True) # 保存後に履歴をリセット
            self.status_message = f"Saved {len(self.buffer)} lines to {self.filename}."
        except Exception as e: self.status_message = f"Error: {e}"

def main(stdscr):
    os.environ.setdefault('ESCDELAY', '25') 
    curses.raw()
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    Editor(stdscr, fn).main_loop()

if __name__ == "__main__":
    try: curses.wrapper(main)
    except Exception as e:
        import traceback; traceback.print_exc()

## ☕ CAFFEE Editor

CAFFEE is a simple, customizable, and lightweight terminal text editor built with Python's `curses` library, inspired by the classic feel of editors like Nano or Pico.

It focuses on basic text editing functionality while incorporating essential features like syntax highlighting (via color pairs), undo/redo history, and a clear, minimal UI.

### 🌟 Key Features

  * **Minimalistic UI:** A clean interface showing the file content, a header, a status bar, and a helpful footer menu.
  * **Line Numbering:** Displays line numbers for easy navigation.
  * **Undo/Redo History ($\text{Ctrl}+\text{Z}$ / $\text{Ctrl}+\text{R}$):** Stores a fixed number of recent states for robust revision control.
  * **Mark/Selection Mode ($\text{Ctrl}+\text{6}$):** Allows selecting text for cut ($\text{Ctrl}+\text{K}$) and copy (Alt+6) operations.
  * **Basic File Operations:** Load, save ($\text{Ctrl}+\text{O}$), and exit ($\text{Ctrl}+\text{X}$ with modified check).
  * **Navigation & Editing:** Standard cursor movement, page up/down, line end ($\text{Ctrl}+\text{E}$), search ($\text{Ctrl}+\text{W}$), paste ($\text{Ctrl}+\text{U}$), and line deletion ($\text{Ctrl}+\text{Y}$).
  * **Comment Toggling ($\text{Ctrl}+\text{/}$):** Easily comment or uncomment the current line with `#`.
  * **Simple Auto-Indentation:** Preserves existing indentation when pressing Enter.

### 🛠️ Installation and Setup

Since CAFFEE is a single Python script that uses the built-in `curses` library, installation is straightforward.

1.  **Dependencies:** Ensure you have Python 3 installed. The `curses` library is usually available by default on macOS and Linux systems. (It may require a separate installation on Windows, often through the `windows-curses` package: `pip install windows-curses`).
2.  **Save the file:** Save the provided code as `caffee.py`.
3.  **Make it executable (Optional, Linux/macOS):**
    ```bash
    chmod +x caffee.py
    ```

### 🚀 Usage

Run the editor from your terminal:

  * **To open a file:**
    ```bash
    ./caffee.py <filename>
    ```
  * **To start a new buffer:**
    ```bash
    ./caffee.py
    ```

### ⌨️ Keybindings (The Menu)

| Key | Function | Description |
| :--- | :--- | :--- |
| $\text{Ctrl}+\text{X}$ | **Exit** | Prompts to save if changes are unsaved. |
| $\text{Ctrl}+\text{O}$ | **Save** | Writes the buffer content to the file. |
| $\text{Ctrl}+\text{W}$ | **Where** | Simple text search function. |
| $\text{Ctrl}+\text{K}$ | **Cut** | Cuts the selection, or the current line if no selection. |
| $\text{Ctrl}+\text{U}$ | **Paste** | Pastes content from the clipboard. |
| $\text{Ctrl}+\text{6}$ | **Mark** | Toggles selection mode (sets/unsets the selection start). |
| Alt+6 | **Copy** | Copies the currently marked selection. |
| $\text{Ctrl}+\text{/}$ | **Comment** | Toggles line comment (`#`) on the current line. |
| $\text{Ctrl}+\text{Y}$ | **DelLine** | Deletes the entire current line without adding it to the clipboard. |
| $\text{Ctrl}+\text{E}$ | **LineEnd** | Moves the cursor to the end of the current line. |
| $\text{Ctrl}+\text{Z}$ | **Undo** | Reverts to the previous state in the history. |
| $\text{Ctrl}+\text{R}$ | **Redo** | Advances to the next state in the history. |
| $\text{Enter}$ | **Newline** | Inserts a new line, preserving indentation. |
| $\text{Backspace}$ | **Delete** | Deletes the character before the cursor, or joins lines. |

### ⚙️ Configuration

The following parameters can be adjusted directly at the top of the `caffee.py` script:

  * `EDITOR_NAME`: The name displayed in the header (`"CAFFEE"`).
  * `VERSION`: The version string (`"1.0"`).
  * `TAB_WIDTH`: The number of spaces a tab key press should represent (currently unused, as the script doesn't handle $\text{Tab}$ explicitly).
  * `HISTORY_LIMIT`: The maximum number of undo/redo states to store (currently **50**).

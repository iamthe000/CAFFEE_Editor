<div align="center">

# ☕ CAFFEE Terminal Text Editor

<img src="preview.png" width="600px">

**A lightweight, modern, and extensible text editor that runs in your terminal.**

</div>

<div align="center">
【Celebration】 PyPI total downloads exceeded 5K! 🎉
    
[![PyPI Version](https://img.shields.io/pypi/v/caffee.svg)](https://pypi.org/project/caffee/)
[![Python Version](https://img.shields.io/pypi/pyversions/caffee.svg)](https://pypi.org/project/caffee/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
  []([![Downloads](https://img.shields.io/pypi/dm/caffee.svg)](https://pypi.org/project/caffee/))
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/caffee?period=total&units=INTERNATIONAL_SYSTEM&left_color=GRAY&right_color=GREEN&left_text=TotalDownloads)](https://pepy.tech/projects/caffee)

</div>

<div align="center">

<a href="ja-README.md">🇯🇵 日本語</a> | <a href="Nuitka_Step.md">Nuitka Compilation Guide</a> | <a href="Setup_PATH.md">PATH Setup Guide</a> | <a href="https://github.com/iamthe000/CAFFEE_Editor_Japanese_UI_plugin_Official.git">Official Japanese UI Plugin</a> | <a href="https://github.com/iamthe000/CAFFEETERIA">Light version(CAFFEETERIA)</a>

</div>

---

**CAFFEE** is a terminal text editor written in Python, designed for a simple, extensible, and efficient editing experience with modern IDE-like features.

## Table of Contents
- [💡 Features](#-features)
- [💻 Installation](#-installation)
- [⌨️ Keybindings](#️-keybindings)
- [🚀 Command Mode](#-command-mode)
- [⚙️ Configuration](#️-configuration)
- [🧩 Plugin System](#-plugin-system)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)


---

## 💡 Features

### 🎨 **Modern UI & Navigation**
- **Multi-Tab Editing** - Handle multiple files simultaneously with a visual tab system (`Ctrl+S`, `Ctrl+L`, `Ctrl+X`).
- **Breadcrumb Bar** - Real-time display of file paths and code symbols (functions/classes) for better context.
- **Vim Mode** - Optional modal editing support for high-efficiency navigation and text manipulation.
- **Relative Line Numbers** (`Ctrl+U`) - Toggle relative line numbers to speed up navigation.
- **Nerd Font Integration** - High-quality icons with an automated font installation helper.
- **Smart Horizontal Scrolling** - Nano-style smooth scrolling for long lines.

### 🚀 **Productivity & Editing**
- **Interactive Search & Replace** (`Ctrl+W`) - VSCode-style interface for finding and replacing text, including "Replace All" (`Ctrl+A`).
- **System Clipboard Sync** - Seamless copy-paste synchronization across Windows, macOS, and Linux.
- **Predictive Text** - Intelligent auto-completion suggestions powered by buffer content.
- **Git Integration** - View branch names, file status markers (`~`: modified, `+`: new), and unified diffs (`Ctrl+D`).
- **Enhanced File Explorer** (`Ctrl+F`) - Browse and manage files with sorting, wildcard search, and full-screen mode.
- **Integrated Terminal** (`Ctrl+N`) - Execute shell commands directly from the editor.
- **CAFFEINE Macro Language** - Automate editor tasks with a dedicated, simple macro language.
- **Command Mode** (`Ctrl+P`) - Execute powerful commands like `:open`, `:saveas`, `:set`, and `:delcomm`.

### ⚙️ **Extensibility & Advanced Support**
- **Automated Build & Run** (`Ctrl+B`) - Optimized templates and build commands for 20+ programming languages.
- **Advanced Syntax Highlighting** - Support for Python, JS/TS, C/C++, Go, Rust, Java, Ruby, Swift, and more.
- **Plugin System** - Extend functionality with custom Python scripts.
- **Atomic File Saving** - Safe file operations with automatic backup creation.
- **Undo/Redo** - Comprehensive history management with configurable limits.

---

## 💻 Installation

### Requirements
- **Python 3.8+**
- Unix-like terminal (Linux, macOS, ChromeOS Linux shell)
- `curses` library (usually included with Python)

### Quick Start
```bash
# Install from PyPI
pip install caffee

# Run the editor
caffee

# Or open a specific file
caffee /path/to/file.py
```

### Upgrade
```bash
pip install caffee --upgrade
```

### Optional: Speed Up with Nuitka
For significantly faster startup, compile with Nuitka. See the [Nuitka Compilation Guide](Nuitka_Step.md) for detailed instructions.

---

## ⌨️ Keybindings

### File Operations
| Key | Action |
|-----|--------|
| `Ctrl+O` | Save current file |
| `Ctrl+X` | Close current tab / Exit |
| `Ctrl+S` | New tab / Start screen |
| `Ctrl+L` | Switch to next tab |

### Editing
| Key | Action |
|-----|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+R` | Redo |
| `Ctrl+K` | Cut (line or selection) |
| `Ctrl+V` | Paste (System Clipboard Sync) |
| `Ctrl+C` | Copy selection |
| `Ctrl+U` | Toggle relative line numbers |
| `Ctrl+Y` | Delete current line |
| `Ctrl+/` | Toggle comment |

### Navigation & Search
| Key | Action |
|-----|--------|
| `Ctrl+W` | Search (with regex support) |
| `Ctrl+G` | Go to line number |
| `Ctrl+E` | Move to end of line |
| `Ctrl+A` | Select all / Clear selection |
| `Ctrl+6` | Set/Unset mark (selection start) |

### Panels & Tools
| Key | Action |
|-----|--------|
| `Ctrl+F` | Toggle file explorer |
| `Ctrl+N` | Toggle integrated terminal |
| `Ctrl+U` | Toggle relative line numbers |
| `Ctrl+T` | Insert template |
| `Ctrl+B` | Build/Run current file |
| `Ctrl+D` | Show Git diff for the current file |
| `Ctrl+P` | Enter Command Mode |
| `Esc` | Return to editor from panels |

---

## 🚀 Command Mode
Press `Ctrl+P` to enter Command Mode, then type a command and press Enter.

| Command | Alias | Description |
|---------|-------|-------------|
| `open <file>`| `o <file>` | Open a file in a new tab. |
| `save` | `w` | Save the current file. |
| `saveas <file>` | | Save the current file with a new name. |
| `copy` | | Copy the selected range to the system clipboard. |
| `paste` | | Paste content from the system clipboard. |
| `close` | `q` | Close the current tab. |
| `quit` | `qa` | Exit the editor (prompts for unsaved files). |
| `new` | | Create a new empty tab. |
| `set <key> <val>` | | Change a setting (e.g., `set tab_width 2`). |
| `undo` | | Undo the last action. |
| `redo` | | Redo the last undone action. |
| `goto <line>` | | Jump to the specified line number. |
| `next` | `tabn` | Switch to the next tab. |
| `prev` | `tabp` | Switch to the previous tab. |
| `find <query>` | | Search for the specified query. |
| `replace <old> <new>` | | Replace occurrences of `<old>` with `<new>`. |
| `expw <width>` | `explorer_width` | Set the file explorer width. |
| `termh <height>` | `terminal_height` | Set the integrated terminal height. |
| `diff` | | Show a Git diff of the current file in a new tab. |
| `delcomm` | | Remove all comments from the current buffer. |
| `template <lang>` | | Insert a template for the specified language. |
| `macro <file>` | | Execute a CAFFEINE macro file. |

---

## ⚙️ Configuration

User settings are stored in `~/.caffee_setting/setting.json`. You can edit this file directly or use the interactive settings manager from the start screen (`Ctrl+S` -> `[2] Choice setting`).

### Example Configuration

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

### Key Configuration Options
- **`auto_indent`**: Enable/disable automatic indentation.
- **`enable_predictive_text`**: Enable/disable auto-completion suggestions.
- **`explorer_show_details`**: Show file size and modification date in the explorer.
- **`displayed_keybindings`**: Customize which keybindings appear in the footer bar.
- **`colors`**: Comprehensive color customization for all UI elements.

---

## ☕ CAFFEINE Macro Language
CAFFEINE is a simple macro language designed specifically for CAFFEE. Macros allow you to automate repetitive tasks by defining a sequence of editor actions.

### Macro Syntax
Macros are stored in `.caffeine` files. Each line can be a command, a cursor movement, or text insertion.

| Command | Description |
|---------|-------------|
| `# comment` | Lines starting with `#` are ignored. |
| `:command` | Execute any CAFFEE editor command. |
| `MOVE <y> <x>` | Move the cursor to the specified row and column. |
| `INSERT "text"` | Insert the specified text at the cursor position. |
| `TYPE "text"` | Simulate typing text character by character. |
| `WAIT <ms>` | Pause execution for the specified number of milliseconds. |
| `COMMAND "cmd"` | Alias for executing an editor command. |

### Usage
To run a macro, use the `:macro <filename>` command in Command Mode (`Ctrl+P`). CAFFEE will look for the file in the current directory or in `~/.caffee_setting/macros/`.

---

## 🧩 Plugin System
Extend CAFFEE's functionality with custom Python scripts placed in `~/.caffee_setting/plugins/`. Use the interactive Plugin Manager (Start Screen -> `Ctrl+P`) to enable or disable plugins.

### Plugin API
Plugins can access the editor's state and functions via an `init(editor)` entry point, allowing you to:
- Bind custom key combinations.
- Register new syntax highlighting rules.
- Add new build commands.
- Manipulate buffers and the cursor.
- Display custom messages in the status bar.

---

## 🛠️ Troubleshooting

- **Display Issues**: If colors or special characters don't render correctly, ensure your terminal supports 256 colors and UTF-8. For environments like iSH, CAFFEE attempts to set a compatible `TERM` variable automatically.
- **File Access**: If you encounter errors saving files or creating backups, check the permissions for `~/.caffee_setting/`.
- **Terminal Not Working**: The integrated terminal requires `pty` support (standard on Linux and macOS).

---

## 🤝 Contributing
Contributions are welcome! Please fork the repository, make focused changes in a feature branch, and submit a pull request.

---

## 📄 License
This project is licensed under the GNU General Public License v3. See the [LICENSE](LICENSE) file for details.

---

*Made with ☕ and Python.*

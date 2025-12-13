# ☕ CAFFEE Command Line Text Editor

## install
```bash
pip install caffee
```
## upgrade
```bash
pip install caffee --upgrade
```

<a href="ja-README.md">🇯🇵 日本語版README</a>　
<a href="https://github.com/iamthe000/CAFFEE_Editor_Japanese_UI_plugin_Official.git">Official Japanese UI Plugin</a>　
<a href="Nuitka_Step.md">Nuitka Compilation Guide</a>　
<a href="Setup_PATH.md">PATH Setup Guide</a>

**CAFFEE** is a lightweight terminal text editor written in Python using the curses library. It aims to provide a simple, extensible, and efficient editing experience directly in your terminal with modern IDE-like features.

---

## ✨ What's New in v2.4.0

### 🎨 **Modern UI Enhancements**
- **Interactive Start Screen** - Welcome screen with quick access to settings, plugins, and file explorer.
- **Tab Bar System** - Multi-file editing with visual tab management.
- **Split Panel Layout** - Toggle file explorer and integrated terminal panels.
- **Enhanced Visual Design** - Improved color schemes and status indicators.

### 🚀 **Productivity Features**
- **Git Integration** - View the current Git branch, file status in each tab (`~`: modified, `+`: new/untracked), and open a diff view (`Ctrl+D`).
- **Command Mode** (`Ctrl+P`) - Execute commands like `:open`, `:saveas`, `:set`, and `:diff`.
- **Predictive Text** - Get auto-completion suggestions from words in the current buffer.
- **Enhanced File Explorer** (`Ctrl+F`) - Browse and manage files with advanced features:
    - Sort by name, date, or size (`s` key).
    - Toggle ascending/descending order (`o` key).
    - Show/hide hidden files (`h` key).
    - Search with wildcards (`/` key).
    - Create, delete, and rename files/directories (`a`, `d`, `r` keys).
- **Code Templates** (`Ctrl+T`) - Insert language-specific code snippets.
- **Built-in Terminal** (`Ctrl+N`) - Execute commands directly from the editor.
- **Plugin & Settings Manager** - Interactive menus to manage plugins and editor settings.
- **Build & Run** (`Ctrl+B`) - Automatic compilation and execution for various languages.
- **Smart Horizontal Scrolling** - Nano-style smooth scrolling for long lines.
- **Full-Width Character Support** - Proper handling of Japanese and other wide characters.

### 🎨 **Syntax Highlighting**
- Python, JavaScript, C/C++, Go, Rust, HTML, Markdown, and Git Diff support.
- Customizable color schemes via `setting.json`.

### 📑 **Multi-Tab Editing**
- `Ctrl+S` - Create a new tab or return to the start screen.
- `Ctrl+L` - Switch to the next tab.
- `Ctrl+X` - Close the current tab (prompts if unsaved).

---

## 💡 Core Features

- **Small and focused** editing experience.
- **Undo/Redo** history with a configurable limit.
- **Mark-based selection** and clipboard operations (cut/copy/paste).
- **Line operations** (delete, comment/uncomment, goto).
- **Atomic file saving** with automatic backup creation.
- **Extensible plugin system** and JSON configuration.

---

## 💻 Installation

### Requirements
- **Python 3.6+**
- Unix-like terminal (Linux, macOS, ChromeOS Linux shell)
- `curses` library (usually included with Python)

### Quick Start
```bash
# Run the editor
caffee

# Or open a specific file
caffee /path/to/file.py
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
| `Ctrl+U` | Paste |
| `Ctrl+C` | Copy selection |
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
| `close` | `q` | Close the current tab. |
| `quit` | `qa` | Exit the editor (prompts for unsaved files). |
| `new` | | Create a new empty tab. |
| `set <key> <val>` | | Change a setting (e.g., `set tab_width 2`). |
| `diff` | | Show a Git diff of the current file in a new tab. |

---

## ⚙️ Configuration

User settings are stored in `~/.caffee_setting/setting.json`. You can edit this file directly or use the interactive settings manager from the start screen (`Ctrl+S` -> `[2] Choice setting`).

### Example Configuration

```json
{
  "tab_width": 4,
  "history_limit": 50,
  "use_soft_tabs": true,
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
- **`enable_predictive_text`**: Enable/disable auto-completion suggestions.
- **`explorer_show_details`**: Show file size and modification date in the explorer.
- **`displayed_keybindings`**: Customize which keybindings appear in the footer bar.
- **`colors`**: Comprehensive color customization for all UI elements.

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
MIT License - See the [LICENSE](LICENSE) file for details.

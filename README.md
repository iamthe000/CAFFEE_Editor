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

## ✨ What's New in v2.0.0

### 🎨 **Modern UI Enhancements**
- **Interactive Start Screen** - Welcome screen with quick access to settings, plugins, and file explorer
- **Tab Bar System** - Multi-file editing with visual tab management
- **Split Panel Layout** - Toggle file explorer and integrated terminal panels
- **Enhanced Visual Design** - Improved color schemes and status indicators

### 🚀 **Productivity Features**
- **Git Integration** - View the current Git branch in the header and file status in each tab (`~`: modified, `+`: new/untracked).
- **Integrated File Explorer** (`Ctrl+F`) - Browse and open files without leaving the editor
- **Built-in Terminal** (`Ctrl+T`) - Execute commands and run code directly from the editor
- **Plugin Manager** (`Ctrl+P` from start screen) - Enable/disable plugins with visual interface
- **Build & Run** (`Ctrl+B`) - Automatic compilation and execution for Python, JavaScript, Go, C/C++, Rust, and shell scripts
- **Smart Horizontal Scrolling** - Nano-style smooth scrolling for long lines
- **Full-Width Character Support** - Proper handling of Japanese and other wide characters

### 🎨 **Syntax Highlighting**
- Python, JavaScript, C/C++, Go, Rust, HTML, Markdown support
- Customizable color schemes via settings

### 📑 **Multi-Tab Editing**
- `Ctrl+S` - Create new tab or return to start screen
- `Ctrl+L` - Switch to next tab
- `Ctrl+X` - Close current tab (prompts if unsaved)

---

## 💡 Core Features

- **Small and focused** editing experience
- **Undo/Redo** history with configurable limit
- **Mark-based selection** and clipboard operations (cut/copy/paste)
- **Line operations** (delete, comment/uncomment, goto)
- **Atomic file saving** with automatic backup creation
- **Plugin system** for extensibility
- **JSON configuration** for customization

---

## 💻 Installation

### Requirements
- **Python 3.6+**
- Unix-like terminal (Linux, macOS, ChromeOS Linux shell)
- `curses` library (usually included with Python)

### Quick Start

```bash
# Download or clone the repository
git clone <repository-url>
cd CAFFEE_Editor

# Run directly
python3 caffee.py

# Or open a specific file
python3 caffee.py /path/to/file.py
```

### Optional: Speed Up with Nuitka

For significantly faster startup and execution, compile with Nuitka (Debian/Ubuntu):

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install nuitka
sudo apt install patchelf
python -m nuitka --standalone caffee.py
cd caffee.dist
./caffee.bin
```

See [Nuitka_Step.md](Nuitka_Step.md) for detailed instructions and troubleshooting.

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
| Arrow Keys | Navigate cursor |
| PageUp/Down | Scroll by page |

### Panels & Tools
| Key | Action |
|-----|--------|
| `Ctrl+F` | Toggle file explorer |
| `Ctrl+T` | Toggle integrated terminal |
| `Ctrl+B` | Build/Run current file |
| `Ctrl+P` | Plugin manager (from start screen) |
| `Esc` | Return to editor from panels |

---

## ⚙️ Configuration

User settings are stored in `~/.caffee_setting/setting.json`.

### Example Configuration

```json
{
  "tab_width": 4,
  "history_limit": 50,
  "use_soft_tabs": true,
  "backup_subdir": "backup",
  "backup_count": 5,
  
  "show_splash": true,
  "splash_duration": 500,
  "start_screen_mode": true,
  
  "explorer_width": 35,
  "terminal_height": 10,
  "show_explorer_default": false,
  "show_terminal_default": false,
  
  "colors": {
    "header_text": "BLACK",
    "header_bg": "WHITE",
    "error_text": "WHITE",
    "error_bg": "RED",
    "linenum_text": "CYAN",
    "linenum_bg": "DEFAULT",
    "selection_text": "BLACK",
    "selection_bg": "CYAN",
    "keyword": "YELLOW",
    "string": "GREEN",
    "comment": "MAGENTA",
    "number": "BLUE",
    "ui_border": "WHITE",
    "tab_active_bg": "BLUE"
  }
}
```

### Configuration Options

- **Editor Settings**: `tab_width`, `history_limit`, `use_soft_tabs`
- **Backup**: `backup_subdir`, `backup_count` (automatic versioned backups)
- **Startup**: `show_splash`, `splash_duration`, `start_screen_mode`
- **Layout**: `explorer_width`, `terminal_height`, panel visibility defaults
- **Colors**: Comprehensive color customization for all UI elements

---

## 🧩 Plugin System

Plugins are Python files in `~/.caffee_setting/plugins/`.

### Plugin API

Plugins can expose an `init(editor)` function with access to:

- **Cursor & Buffer Access**: `get_cursor_position()`, `get_line_content()`, `get_buffer_lines()`
- **Editing Operations**: `insert_text_at_cursor()`, `delete_range()`, `replace_text()`
- **Selection**: `get_selection_text()`, `get_selection_range()`
- **Key Binding**: `bind_key(key_code, function)`
- **UI Feedback**: `set_status_message()`, `redraw_screen()`
- **User Input**: `prompt_user(message, default="")`

### Example Plugin

```python
def init(editor):
    def uppercase_selection(ed):
        text = ed.get_selection_text()
        if text:
            lines = [line.upper() for line in text]
            # Process selection...
            ed.set_status_message("Converted to uppercase!")
        else:
            ed.set_status_message("No selection")
    
    # Bind to Ctrl+Shift+U (if terminal supports)
    editor.bind_key(21, uppercase_selection)
```

### Plugin Manager

Access via `Ctrl+P` from the start screen:
- View all installed plugins
- Enable/disable plugins with spacebar
- Changes take effect after editor restart

Disabled plugins are moved to `~/.caffee_setting/plugins/disabled/`.

---

## 🚀 Built-in Commands

CAFFEE automatically detects file types and provides build/run commands:

| File Type | Command |
|-----------|---------|
| `.py` | `python3 <file>` |
| `.js` | `node <file>` |
| `.go` | `go run <file>` |
| `.c` | `gcc <file> -o <output> && ./<output>` |
| `.cpp`, `.cc` | `g++ <file> -o <output> && ./<output>` |
| `.sh` | `bash <file>` |
| `.rs` | `rustc <file> && ./<output>` |

Press `Ctrl+B` to save and run the current file. Output appears in the integrated terminal.

---

## 🛠️ Troubleshooting

### Display Issues
- **Japanese text garbled?** See [Nuitka_Step.md](Nuitka_Step.md) for locale configuration
- **Colors not working?** Ensure your terminal supports 256 colors
- **Curses errors?** Verify Python's curses library is available on your platform

### File Operations
- **File changed on disk**: CAFFEE detects external changes but won't auto-reload to prevent data loss
- **Backup files**: Located in `~/.caffee_setting/backup/` with timestamps

### Terminal Integration
- **Terminal not working?** The integrated terminal requires `pty` support (Unix-like systems only)
- **Build command fails?** Ensure required compilers/interpreters are in your PATH

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make focused, well-documented changes
4. Test in multiple terminal environments
5. Submit a pull request with clear descriptions

### Development Guidelines
- Maintain compatibility with Python 3.6+
- Respect terminal resizing behavior
- Keep the codebase simple and readable
- Follow existing code style

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with Python's `curses` library. Inspired by nano, vim, and modern code editors.

**CAFFEE** - *Brew your code in the terminal* ☕

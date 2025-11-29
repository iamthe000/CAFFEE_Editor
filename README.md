# CAFFEE Command Line Text Editor
<a href="ja-README.md">🇯🇵日本語版README</a>
<a href="https://github.com/iamthe000/CAFFEE_Editor_Japanese_UI_plugin_Official.git">公式UI日本語化プラグイン</a>
<a href="Nuitka.md">Steps to speed up with Nuitka</a>

CAFFEE is a lightweight terminal text editor written in Python using the curses library.  
It aims to be simple, extensible via plugins, and suitable for quick edits inside a terminal.

## Features
- Small and focused editing experience
- Undo/redo history
- Mark-based selection and clipboard (cut/copy/paste)
- Line operations (delete, comment/uncomment, goto)
- Atomic file save with backup creation
- Plugin system: load Python files from a user plugins directory
- Configurable tab width and colors via a JSON settings file

## Installation
1. Ensure Python 3 is installed.
2. Place `caffee.py` somewhere in your PATH or run it directly:
   ```
   python3 caffee.py [optional-file-to-open]
   ```

## Usage
- Run `python3 caffee.py` to open a new buffer, or `python3 caffee.py /path/to/file` to edit a file.
- The editor uses a curses-based UI; run it in a terminal emulator.

## Keybindings (common)
- Ctrl+O : Save
- Ctrl+X : Exit (prompts if unsaved changes)
- Ctrl+W : Search
- Ctrl+K : Cut (line or selection)
- Ctrl+U : Paste
- Ctrl+6 : Toggle mark (start/end selection)
- Ctrl+A : Select all / clear selection
- Ctrl+G : Go to line
- Ctrl+E : Move to end of line
- Ctrl+/ : Toggle comment on current line
- Ctrl+Y : Delete line
- Ctrl+Z : Undo
- Ctrl+R : Redo
- Arrow keys / PageUp / PageDown : Navigate

Notes:
- Press Alt then `6` to invoke copy in some terminals (behavior may depend on terminal key mapping).
- Backspace merges lines when at the start of a line.

## Configuration
User settings are stored in `~/.caffee_setting/setting.json`. Example:
```json
{
  "tab_width": 4,
  "history_limit": 100,
  "use_soft_tabs": true,
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
```

## Plugins
Plugins are simple Python files placed in `~/.caffee_setting/plugins/`.  
A plugin may expose an `init(editor)` function which will be called with the Editor instance.  
Use `editor.bind_key(key_code, function)` to register key handlers from a plugin.

Example plugin skeleton:
```python
def init(editor):
    def hello(ed):
        ed.set_status("Hello from plugin!", timeout=2)
    editor.bind_key(9999, hello)
```

## Development
- The main source file is `caffee.py`.
- Tests are not included; run the editor in a terminal for manual testing.
- Keep changes minimal and respect terminal resizing behavior.

## Troubleshooting
- If you encounter curses errors, ensure your terminal supports the required capabilities and that Python's curses library is available on your platform.
- File changes on disk are detected and will notify you; automatic reload is not performed to avoid overwriting local changes.

## Contributing
- Fork the repository, make changes, and submit a pull request.
- Provide small, focused patches and include a clear description of changes.

## License
MIT License.

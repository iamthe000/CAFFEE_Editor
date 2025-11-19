# CAFFEE — Terminal Text Editor
<a href="ja-README.md">🇯🇵日本語版README</a>
CAFFEE is a lightweight, curses-based text editor written in Python.
It aims to be simple, fast, and familiar for anyone comfortable working inside the terminal.

Version: **1.0**

---

## ✨ Features

* **Syntax-free, plain-text editing**
* **Undo / Redo** (Ctrl+Z / Ctrl+R)
* **Copy, Cut, Paste**

  * Mark selection (Ctrl+6)
  * Copy (Alt+6)
  * Cut (Ctrl+K)
  * Paste (Ctrl+U)
* **Line comment toggle** using `#` (Ctrl+/)
* **Search** (Ctrl+W)
* **Delete line** (Ctrl+Y)
* **Line navigation shortcuts**
* **Start-up splash screen**
* **Auto indentation**
* **Clipboard support for multi-line selections**
* **Crash-safe drawing with boundary handling**
* **Basic line numbers and minimal UI**

---

## 🖥️ Keybindings

| Action              | Shortcut              |
| ------------------- | --------------------- |
| Save                | **Ctrl+O**            |
| Exit                | **Ctrl+X**            |
| Undo                | **Ctrl+Z**            |
| Redo                | **Ctrl+R**            |
| Mark selection      | **Ctrl+6**            |
| Copy                | **Alt+6**             |
| Cut                 | **Ctrl+K**            |
| Paste               | **Ctrl+U**            |
| Comment / Uncomment | **Ctrl+/**            |
| Delete line         | **Ctrl+Y**            |
| Move to end of line | **Ctrl+E**            |
| Search              | **Ctrl+W**            |
| Page Up / Down      | **PageUp / PageDown** |
| Arrow keys          | Cursor movement       |

---

## 📦 Installation

Make sure you have Python 3 installed.

```bash
git clone <your-repo-url>
cd <your-project-directory>
```

No external libraries are required—only Python’s built-in `curses` module.

---

## 🚀 Usage

Open a file:

```bash
python3 caffee.py filename.txt
```

Open CAFFEE with an empty buffer:

```bash
python3 caffee.py
```

Your changes will prompt a save confirmation when exiting with **Ctrl+X**.

---

## 📁 File Saving

If you open the editor without a filename, CAFFEE asks for one on save:

```
Filename:
```

Files are saved in UTF-8.

---

## 🛠️ Development Notes

* Undo/Redo history is limited to **50 states**
* All edits (typing, delete, enter, cut, paste) correctly generate history snapshots
* Special care is taken to prevent terminal crashes when drawing at screen edges
* The editor resets history after a successful file save

---

## 📜 License

MIT License (or whichever you plan to use).

## How to Speed Up with Nuitka(debian only　※and chromeOS of Linux-Shell)

```
python3 -m venv myenv
source myenv/bin/activate
pip install nuitka
sudo apt install patchelf
cd CAFFEE_Editor
python -m nuitka --standalone caffee.py
cd caffee.dist
export LANG="C.UTF-8"
./caffee.bin
```

### Troubleshooting: Japanese Text Rendering Issues

If Japanese text appears corrupted or garbled when running the application, the issue may be caused by insufficient locale settings in the environment.

---

## Solution 1: Set Locale at Runtime (Recommended)

The simplest fix is to specify a UTF-8 locale before running the program.

```bash
# Set a general-purpose UTF-8 locale
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"

# Run
./caffee.bin
```

---

## Solution 2: Modify the Source Code (Most Robust)

If the above does not solve the issue, or if you need a more portable binary, embed the locale configuration for `curses` directly into `caffee.py` before recompiling.

Add the following two lines inside the definition of `main(stdscr):`, then compile again with Nuitka:

```python
def main(stdscr):
    import locale  # added
    locale.setlocale(locale.LC_ALL, '')  # added
    os.environ.setdefault('ESCDELAY', '25') 
    curses.raw()
    # ...
```

# 🚀 Setup and PATH Configuration

This section explains how to add the directory containing the `caffee.py` script to your system's `PATH`. This allows you to run the script using just its filename (`caffee.py`) from any directory, without needing the full path or prefixing it with `python3`.

## 1\. Prerequisites (Checklist)

Since `caffee.py` is a Python script, we assume the following is already set up:

  * The script contains the **Shebang line** (`#!/usr/bin/env python3`) as the very first line.
  * The script has **execute permissions** enabled (`chmod +x /path/to/caffee.py`).

## 2\. Adding the Script Directory to PATH

You must add the directory containing `caffee.py` (e.g., `~/CAFFEE_Editor`) to your shell's configuration file.

### 🐧 Linux (Bash/Zsh) & macOS (Zsh/Bash)

Open your primary shell configuration file (`~/.zshrc` for Zsh, or `~/.bashrc`/`~/.bash_profile` for Bash) using a text editor.

1.  **Open the configuration file:**

    ```bash
    nano ~/.zshrc  # Use the file appropriate for your shell```

2.  **Add the following line** to the **end** of the file, replacing `/path/to/CAFFEE_Editor` with the actual directory (e.g., `~/CAFFEE_Editor`). This ensures your script is found **first**, overriding any older versions.

    ```bash
    export PATH=/path/to/CAFFEE_Editor:$PATH```

3.  **Save and apply the changes:**

    ```bash
    source ~/.zshrc  # Use the file you just edited```

4.  **Test the setup:**

    ```bash
    caffee.py```

### 🪟 Windows 10/11

The process is typically done through the graphical user interface.

1.  Search for "**Environment Variables**" in the Start Menu and select "**Edit the system environment variables**."
2.  Click the "**Environment Variables**" button.
3.  In the "User variables for \[Your Username]" section, select the **Path** variable and click "**Edit...**"
4.  Click "**New**" and paste the full path to the `CAFFEE_Editor` directory.
5.  Ensure this new path entry is moved to the **top** of the list to give it the highest priority.
6.  Click **OK** to save and close the windows.
7.  **Test the setup:** Open a new Command Prompt or PowerShell window and type `caffee.py`.

-----

# 🔄 Updating the PATH for a New Version

The method for updating the path depends on where the new version is installed.

## 1\. Case A: New Version Installed in the **Same** Directory

If you download the new version of `caffee.py` and overwrite the old file in the **same directory** that is already configured in your `PATH` (e.g., `~/CAFFEE_Editor`), **no further action is required**.

The system will automatically execute the newly updated file because the path to its directory is still valid.

## 2\. Case B: New Version Installed in a **Different** Directory

If the new version is installed in a completely different location (e.g., `~/CAFFEE_Editor_v2`), you must update your configuration file to point to the new directory.

### 🐧 Linux & macOS

1.  **Open the configuration file** (`~/.zshrc` or `~/.bashrc`) again.
2.  Locate the line you previously added:
    ```bash
    export PATH=/path/to/CAFFEE_Editor:$PATH  # Old path```
3.  **Replace the old path** with the new one:
    ```bash
    export PATH=/path/to/CAFFEE_Editor_v2:$PATH # New path```
4.  **Save and apply the changes:**
    ```bash
    source ~/.zshrc```

### 🪟 Windows

1.  Access the **Environment Variables** editor (as described above).
2.  In the **Path** user variable, select the **old directory entry** for `CAFFEE_Editor`.
3.  Click "**Edit**" and update the path to the new directory (e.g., `C:\Users\User\Documents\CAFFEE_Editor_v2`), or simply delete the old entry and add the new one.
4.  Ensure the new path entry remains at the **top** of the list for priority.

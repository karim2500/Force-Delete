# Permanent Program Deleter

A powerful Windows tool that completely removes programs from your PC, including running processes, registry entries, files, and shortcuts.

## ⚠️ WARNING
This tool is extremely powerful and potentially dangerous. It will:
- Force-kill running processes
- Delete files and folders permanently
- Remove registry entries
- Bypass normal Windows protections

**Use at your own risk!** This tool is designed for personal use only.

## Features

- **Force Process Termination**: Kills running programs even if they're in use
- **Complete File Removal**: Deletes all program files and folders
- **Registry Cleanup**: Removes all registry entries related to the program
- **Shortcut Removal**: Deletes desktop and start menu shortcuts
- **Context Menu Integration**: Right-click "Permanently Delete" option
- **No Confirmation Dialogs**: Direct deletion without multiple prompts

## Installation

1. Install Python 3.7+ if not already installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the installer as Administrator:
   ```
   install_as_admin
   ```
4. Choose option 1 to install the context menu

## Usage

### Method 1: Context Menu (Recommended)
1. Right-click on any executable file (.exe)
2. Select "Permanently Delete" from the context menu
3. The program will be completely removed

### Method 2: Command Line
```
python "Test deleted.py" "C:\path\to\program.exe"
```

## What Gets Deleted

The tool will remove:
- **Process**: All running instances of the program
- **Files**: Program installation directory and related folders
- **Registry**: Uninstall entries and program-specific registry keys
- **Shortcuts**: Desktop shortcuts and Start Menu entries
- **User Data**: Application data in AppData folders (if named after the program)

## Locations Searched

The tool searches these common locations:
- `C:\Program Files\`
- `C:\Program Files (x86)\`
- `%LOCALAPPDATA%`
- `%APPDATA%`
- `%PROGRAMDATA%`
- Desktop shortcuts
- Start Menu shortcuts

## Technical Details

### Process Termination
- Uses `psutil` to find and kill all related processes
- Matches both executable name and full path
- Force-kills processes that don't respond to normal termination

### Registry Cleanup
- Scans uninstall registry keys
- Removes program-specific entries from SOFTWARE keys
- Cleans both HKEY_LOCAL_MACHINE and HKEY_CURRENT_USER

### File Deletion
- Handles locked files by changing permissions
- Uses multiple deletion methods as fallback
- Recursively deletes directories

## Uninstallation

To remove the context menu option:
1. Run `python install_context_menu.py` or `install_as_admin` as Administrator
2. Choose option 2 to uninstall

## Safety Notes

- **Backup Important Data**: This tool permanently deletes files
- **System Files**: Avoid using on system-critical programs
- **Shared Components**: May remove files used by other programs
- **Registry**: Incorrect registry modifications can cause system issues
- **Administrator Rights**: Required for full functionality

## Troubleshooting

### "Access Denied" Errors
- Ensure you're running as Administrator
- Some system files cannot be deleted even with admin rights

### Program Still Appears
- Check if the program has multiple installation locations
- Some programs install services that need separate removal
- Registry entries may be in non-standard locations

### Context Menu Not Appearing
- Restart Windows Explorer or reboot
- Verify the installer ran as Administrator
- Check if antivirus is blocking registry modifications

## Legal Disclaimer

This tool is provided "as is" without warranty. The author is not responsible for any damage caused by its use. This tool is intended for personal use on your own computer only.

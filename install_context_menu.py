import winreg
import os
import sys
from pathlib import Path

class ContextMenuInstaller:
    def __init__(self):
        # Use batch wrapper for better Windows compatibility
        base = Path(__file__).parent.absolute()
        self.wrapper_path = base / "permanent_delete_wrapper.bat"
        self.wrapper_lnk_path = base / "permanent_delete_wrapper_lnk.bat"
        self.python_path = sys.executable
        self.script_path = base / "Test deleted.py"
        print(f"Wrapper path: {self.wrapper_path}")
        print(f".lnk Wrapper path: {self.wrapper_lnk_path}")
        print(f"Wrapper exists: {self.wrapper_path.exists()}")
        print(f"Python path: {self.python_path}")
        print(f"Script path: {self.script_path}")
        
    def install_context_menu(self):
        """Install the 'Permanently Delete' context menu option"""
        try:
            # Registry path for files, executables, shortcuts, and folders
            registry_paths = [
                r"*\shell",       # All files
                r"exefile\shell", # Executable files
                r"lnkfile\shell", # Shortcuts (.lnk)
                r"Directory\shell"# Folders
            ]
            
            for reg_path in registry_paths:
                try:
                    # Create the main menu item
                    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{reg_path}\\PermanentDelete") as key:
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Permanently Delete")
                        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "shell32.dll,-240")  # Delete icon
                        
                    # Create the command using batch wrapper(s)
                    if reg_path.startswith("lnkfile") and self.wrapper_lnk_path.exists():
                        command = f'"{self.wrapper_lnk_path}" "%1"'
                    else:
                        command = f'"{self.wrapper_path}" "%1"'
                    print(f"Installing command: {command}")
                    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{reg_path}\\PermanentDelete\\command") as key:
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
                        
                    print(f"Successfully installed context menu for: {reg_path}")
                    
                except Exception as e:
                    print(f"Error installing for {reg_path}: {e}")
                    
            print("\nContext menu installation completed!")
            print("You should now see 'Permanently Delete' when right-clicking on files and folders.")
            
        except Exception as e:
            print(f"Installation failed: {e}")
            return False
            
        return True
    
    def uninstall_context_menu(self):
        """Remove the 'Permanently Delete' context menu option"""
        try:
            registry_paths = [
                r"*\shell\PermanentDelete",
                r"exefile\shell\PermanentDelete", 
                r"lnkfile\shell\PermanentDelete",
                r"Directory\shell\PermanentDelete",
            ]
            
            for reg_path in registry_paths:
                try:
                    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{reg_path}\\command")
                    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, reg_path)
                    print(f"Removed context menu from: {reg_path}")
                except FileNotFoundError:
                    pass  # Key doesn't exist, which is fine
                except Exception as e:
                    print(f"Error removing {reg_path}: {e}")
                    
            print("Context menu uninstallation completed!")
            
        except Exception as e:
            print(f"Uninstallation failed: {e}")
            return False
            
        return True

def main():
    installer = ContextMenuInstaller()
    
    print("Permanent Delete Context Menu Installer")
    print("=" * 40)
    print("1. Install context menu")
    print("2. Uninstall context menu")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\nInstalling context menu...")
            if installer.install_context_menu():
                print("\n✅ Installation successful!")
                print("Right-click on files/folders to see 'Permanently Delete'.")
            else:
                print("\n❌ Installation failed!")
            break
            
        elif choice == "2":
            print("\nUninstalling context menu...")
            if installer.uninstall_context_menu():
                print("\n✅ Uninstallation successful!")
            else:
                print("\n❌ Uninstallation failed!")
            break
            
        elif choice == "3":
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    # Check if running as administrator
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ This script requires administrator privileges!")
        print("Please run as administrator to install/uninstall context menu options.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    main()

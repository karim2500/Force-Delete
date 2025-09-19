import winreg
import sys
import os

def check_registry_entries():
    """Check what's actually registered in the context menu"""
    registry_paths = [
        r"*\shell\PermanentDelete\command",
        r"exefile\shell\PermanentDelete\command",
        r"Applications\shell\PermanentDelete\command",
    ]
    
    print("Checking registry entries...")
    print("=" * 50)
    
    for reg_path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, reg_path) as key:
                command, _ = winreg.QueryValueEx(key, "")
                print(f"✅ {reg_path}")
                print(f"   Command: {command}")
                print()
        except FileNotFoundError:
            print(f"❌ {reg_path} - NOT FOUND")
        except Exception as e:
            print(f"❌ {reg_path} - ERROR: {e}")

def test_command():
    """Test if the command can be executed"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "Test deleted.py")
    python_path = sys.executable
    
    print("Testing command paths...")
    print("=" * 50)
    print(f"Python executable: {python_path}")
    print(f"Script path: {script_path}")
    print(f"Script exists: {os.path.exists(script_path)}")
    print(f"Python exists: {os.path.exists(python_path)}")
    
    # Test command that would be registered
    test_command = f'"{python_path}" "{script_path}" "test_file.exe"'
    print(f"Full command: {test_command}")

if __name__ == "__main__":
    print("Context Menu Debug Tool")
    print("=" * 50)
    
    check_registry_entries()
    test_command()
    
    input("\nPress Enter to exit...")

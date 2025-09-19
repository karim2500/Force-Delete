import sys
import os
from pathlib import Path

# Add current directory to path so we can import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the module with space in filename
import importlib.util
spec = importlib.util.spec_from_file_location("test_deleted", "Test deleted.py")
test_deleted_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_deleted_module)
PermanentDeleter = test_deleted_module.PermanentDeleter

def test_deletion():
    """Test the permanent deleter with a dummy file"""
    
    # Create a test file
    test_file = Path("test_program.exe")
    test_file.write_text("This is a test executable")
    
    print(f"Created test file: {test_file.absolute()}")
    print(f"File exists: {test_file.exists()}")
    
    # Test the deleter (but don't actually delete, just show what would happen)
    deleter = PermanentDeleter()
    
    # Override the methods to just print what would happen
    original_delete = deleter.delete_files_and_folders
    original_kill = deleter.force_kill_processes
    original_registry = deleter.clean_registry
    original_shortcuts = deleter.clean_shortcuts
    
    def mock_delete(paths):
        print(f"Would delete paths: {[str(p) for p in paths]}")
        return [str(p) for p in paths]
    
    def mock_kill(name):
        print(f"Would kill processes matching: {name}")
        return []
    
    def mock_registry(name):
        print(f"Would clean registry for: {name}")
        return []
    
    def mock_shortcuts(name):
        print(f"Would clean shortcuts for: {name}")
        return []
    
    deleter.delete_files_and_folders = mock_delete
    deleter.force_kill_processes = mock_kill
    deleter.clean_registry = mock_registry
    deleter.clean_shortcuts = mock_shortcuts
    
    # Test without admin elevation
    deleter.elevate_privileges = lambda: None
    
    try:
        deleter.permanent_delete(str(test_file.absolute()))
    except Exception as e:
        print(f"Error during test: {e}")
    
    # Clean up test file
    if test_file.exists():
        test_file.unlink()
        print("Cleaned up test file")

if __name__ == "__main__":
    test_deletion()

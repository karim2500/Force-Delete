import os
import sys
import subprocess
import winreg
import psutil
import shutil
import time
import ctypes
from pathlib import Path
import threading
import logging

class PermanentDeleter:
    def __init__(self):
        self.target_path = None
        self.program_name = None
        
    def is_admin(self):
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def elevate_privileges(self):
        """Restart script with admin privileges if needed"""
        if not self.is_admin():
            # Re-run the program with admin rights
            logging.info("Attempting to elevate privileges via UAC prompt")
            try:
                # Properly quote args for Windows command line
                script_path = str(Path(sys.argv[0]).resolve())
                params_list = [script_path] + sys.argv[1:]
                params = subprocess.list2cmdline(params_list)
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, params, None, 1
                )
            except Exception:
                logging.exception("Elevation failed to start")
            sys.exit()
    
    def force_kill_processes(self, executable_name):
        """Force kill all processes related to the executable"""
        killed_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['exe'] and (
                        executable_name.lower() in proc.info['exe'].lower() or
                        proc.info['name'].lower() == executable_name.lower()
                    ):
                        print(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.kill()
                        killed_processes.append(proc.info['name'])
                        time.sleep(0.1)  # Small delay to ensure process is killed
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"Error killing processes: {e}")
        
        return killed_processes

    def _path_within(self, candidate: str, base_dir: Path) -> bool:
        try:
            return Path(candidate).resolve().is_relative_to(base_dir.resolve())
        except Exception:
            # For Python versions without is_relative_to
            try:
                c = str(Path(candidate).resolve())
                b = str(base_dir.resolve())
                return c.lower().startswith(b.lower() + "\\") or c.lower() == b.lower()
            except Exception:
                return False

    def force_kill_processes_by_folder(self, folder_path: Path):
        """Force kill any process whose exe/cwd/open file or cmdline touches the folder"""
        killed_processes = []
        folder_path = folder_path.resolve()
        logging.info(f"Killing processes locking/within folder: {folder_path}")
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cwd', 'open_files', 'cmdline']):
            try:
                if proc.pid == os.getpid():
                    continue  # never kill self
                touches = False
                if proc.info.get('exe') and self._path_within(proc.info['exe'], folder_path):
                    touches = True
                if not touches and proc.info.get('cwd') and self._path_within(proc.info['cwd'], folder_path):
                    touches = True
                if not touches and proc.info.get('open_files'):
                    for of in proc.info['open_files']:
                        if of and of.path and self._path_within(of.path, folder_path):
                            touches = True
                            break
                if not touches and proc.info.get('cmdline'):
                    for arg in proc.info['cmdline']:
                        if arg and (self._path_within(arg, folder_path)):
                            touches = True
                            break

                if touches:
                    print(f"Killing process: {proc.info.get('name')} (PID: {proc.info.get('pid')})")
                    proc.kill()
                    killed_processes.append(proc.info.get('name') or str(proc.info.get('pid')))
                    time.sleep(0.05)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as exc:
                logging.debug(f"Error while scanning process {proc.pid}: {exc}")
        logging.info(f"Killed {len(killed_processes)} processes for folder")
        return killed_processes
    
    def find_program_files(self, executable_path):
        """Find all files related to the program"""
        files_to_delete = set()
        
        # Add the main executable and its directory, or the folder itself
        exe_path = Path(executable_path)
        if exe_path.exists():
            if exe_path.is_dir():
                files_to_delete.add(exe_path)
            else:
                files_to_delete.add(exe_path.parent)
            
        # Common installation directories
        program_name = exe_path.stem if exe_path.is_file() else exe_path.name
        common_dirs = [
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')),
            Path(os.environ.get('LOCALAPPDATA', '')),
            Path(os.environ.get('APPDATA', '')),
            Path(os.environ.get('PROGRAMDATA', '')),
        ]
        
        for base_dir in common_dirs:
            if base_dir.exists():
                # Look for directories containing the program name
                for item in base_dir.iterdir():
                    if item.is_dir() and program_name.lower() in item.name.lower():
                        files_to_delete.add(item)
        
        return files_to_delete
    
    def clean_registry(self, program_name):
        """Remove registry entries related to the program"""
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes"),
        ]
        
        deleted_keys = []
        
        for hive, base_path in registry_paths:
            try:
                with winreg.OpenKey(hive, base_path, 0, winreg.KEY_ALL_ACCESS) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if program_name.lower() in subkey_name.lower():
                                try:
                                    winreg.DeleteKey(key, subkey_name)
                                    deleted_keys.append(f"{base_path}\\{subkey_name}")
                                    print(f"Deleted registry key: {subkey_name}")
                                except Exception as e:
                                    print(f"Could not delete registry key {subkey_name}: {e}")
                                    i += 1
                            else:
                                i += 1
                        except OSError:
                            break
            except Exception as e:
                continue
        
        return deleted_keys
    
    def delete_files_and_folders(self, paths_to_delete):
        """Delete files and folders, handling locked files"""
        deleted_items = []
        
        for path in paths_to_delete:
            if path.exists():
                try:
                    if path.is_file():
                        # Handle individual files
                        try:
                            path.chmod(0o777)  # Change permissions
                        except Exception:
                            pass
                        path.unlink()
                        deleted_items.append(str(path))
                        print(f"Deleted file: {path}")
                    elif path.is_dir():
                        # Handle directories
                        def handle_remove_readonly(func, p, exc):
                            try:
                                os.chmod(p, 0o777)
                            except Exception:
                                pass
                            try:
                                func(p)
                            except Exception:
                                pass
                        
                        shutil.rmtree(path, onerror=handle_remove_readonly)
                        deleted_items.append(str(path))
                        print(f"Deleted directory: {path}")
                        
                except Exception as e:
                    print(f"Error deleting {path}: {e}")
                    # Try alternative deletion method
                    try:
                        if path.is_dir():
                            # Take ownership & grant rights, then remove via cmd
                            subprocess.run(['cmd','/c',f'takeown /f "{path}" /r /d y & icacls "{path}" /grant administrators:F /t /c & rmdir /s /q "{path}"'], shell=True)
                        else:
                            subprocess.run(['cmd', '/c', f'del /f /s /q "{path}"'], shell=True)
                        if not path.exists():
                            deleted_items.append(str(path))
                        else:
                            # Schedule delete on reboot as last resort
                            try:
                                import ctypes
                                MoveFileExW = ctypes.windll.kernel32.MoveFileExW
                                MOVEFILE_DELAY_UNTIL_REBOOT = 0x4
                                MoveFileExW(str(path), None, MOVEFILE_DELAY_UNTIL_REBOOT)
                                deleted_items.append(str(path) + " (on reboot)")
                                print(f"Scheduled deletion on reboot: {path}")
                            except Exception:
                                print(f"Failed to schedule deletion on reboot: {path}")
                    except:
                        print(f"Failed to delete {path} with all methods")
        
        return deleted_items
    
    def clean_shortcuts(self, program_name):
        """Remove shortcuts from desktop and start menu"""
        shortcut_locations = [
            Path.home() / "Desktop",
            Path(os.environ.get('PUBLIC', '')) / "Desktop",
            Path(os.environ.get('APPDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get('PROGRAMDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]
        
        deleted_shortcuts = []
        
        for location in shortcut_locations:
            if location.exists():
                for shortcut in location.rglob("*.lnk"):
                    if program_name.lower() in shortcut.stem.lower():
                        try:
                            shortcut.unlink()
                            deleted_shortcuts.append(str(shortcut))
                            print(f"Deleted shortcut: {shortcut}")
                        except Exception as e:
                            print(f"Could not delete shortcut {shortcut}: {e}")
        
        return deleted_shortcuts
    
    def permanent_delete(self, target_path):
        """Main deletion function"""
        print(f"Starting permanent deletion of: {target_path}")
        logging.info(f"Starting permanent deletion of: {target_path}")
        
        # Ensure we have admin privileges
        self.elevate_privileges()
        
        self.target_path = Path(target_path)
        self.program_name = self.target_path.stem if self.target_path.is_file() else self.target_path.name
        
        # Step 1: Kill all related processes
        print("Step 1: Terminating related processes...")
        logging.info("Step 1: Terminating related processes...")
        if self.target_path.is_dir():
            killed_processes = self.force_kill_processes_by_folder(self.target_path)
        else:
            killed_processes = self.force_kill_processes(self.program_name)
        
        # Give processes time to fully terminate
        time.sleep(2)
        
        # Step 2: Find all program files
        print("Step 2: Locating program files...")
        logging.info("Step 2: Locating program files...")
        files_to_delete = self.find_program_files(target_path)
        
        # Step 3: Clean registry
        print("Step 3: Cleaning registry...")
        logging.info("Step 3: Cleaning registry...")
        deleted_registry = self.clean_registry(self.program_name)
        
        # Step 4: Delete files and folders
        print("Step 4: Deleting files and folders...")
        logging.info("Step 4: Deleting files and folders...")
        deleted_files = self.delete_files_and_folders(files_to_delete)
        
        # Step 5: Clean shortcuts
        print("Step 5: Removing shortcuts...")
        logging.info("Step 5: Removing shortcuts...")
        deleted_shortcuts = self.clean_shortcuts(self.program_name)
        
        # Summary
        print("\n" + "="*50)
        print("DELETION SUMMARY")
        print("="*50)
        print(f"Program: {self.program_name}")
        print(f"Killed processes: {len(killed_processes)}")
        print(f"Deleted registry keys: {len(deleted_registry)}")
        print(f"Deleted file paths: {len(deleted_files)}")
        print(f"Deleted shortcuts: {len(deleted_shortcuts)}")
        print("\nProgram has been permanently deleted!")
        logging.info(
            f"Summary — program={self.program_name}, killed={len(killed_processes)}, registry={len(deleted_registry)}, files={len(deleted_files)}, shortcuts={len(deleted_shortcuts)}"
        )

def setup_logging():
    try:
        log_dir = os.path.join(os.environ.get('LOCALAPPDATA', str(Path.home())), 'PermanentDeleter')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'deleter.log')
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )
        logging.info("Logger initialized")
    except Exception:
        # Fallback to stderr if logging setup fails
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def resolve_target_path(arg_path: str) -> str:
    """Resolve target path. If a .lnk is passed, resolve to the real target."""
    path = arg_path.strip().strip('"')
    try:
        if path.lower().endswith('.lnk') and os.path.exists(path):
            # Use PowerShell COM to resolve shortcut target
            quoted = path.replace("'", "''")
            cmd = [
                'powershell', '-NoProfile', '-Command',
                f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{quoted}'); Write-Output $s.TargetPath"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                target = result.stdout.strip().strip('"')
                if target and os.path.exists(target):
                    logging.info(f"Resolved shortcut to: {target}")
                    return target
                else:
                    logging.warning(f"Shortcut resolution returned missing target: {target}")
            else:
                logging.error(f"Shortcut resolution failed: {result.stderr}")
        return path
    except Exception as exc:
        logging.exception(f"Failed resolving target path for {path}: {exc}")
        return path

def main():
    setup_logging()
    try:
        logging.info(f"Arguments: {sys.argv}")
        if len(sys.argv) != 2:
            print("Usage: python permanent_deleter.py <path_to_executable>")
            logging.error("Invalid argument count")
            sys.exit(1)
        target_arg = sys.argv[1]
        real_target = resolve_target_path(target_arg)
        logging.info(f"Resolved target: {real_target}")
        deleter = PermanentDeleter()
        deleter.permanent_delete(real_target)
    except Exception as exc:
        logging.exception(f"Unhandled error: {exc}")
        raise

if __name__ == "__main__":
    main()

import sys
import os
import shutil

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_executable_path(name):
    """Get path to bundled executable or fallback to system command"""
    # Map generic name to platform specific name for BUNDLED binaries
    bundled_filename = name
    if name == "ffmpeg":
        if sys.platform == "darwin":
            bundled_filename = "ffmpeg_osx"
        elif sys.platform == "win32":
            bundled_filename = "ffmpeg.exe"
    elif name == "ffprobe":
        if sys.platform == "darwin":
            bundled_filename = "ffprobe_osx"
        elif sys.platform == "win32":
            bundled_filename = "ffprobe.exe"

    # Check bundled location (PyInstaller _MEIPASS or local bin folder)
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    # Check 1: Inside 'bin' subdirectory (dev mode or if added to bin in bundle)
    bundled_path = os.path.join(base_path, "bin", bundled_filename)
    if os.path.exists(bundled_path):
        return bundled_path
        
    # Check 2: Top level (common for PyInstaller onefile if added with '.')
    bundled_path_root = os.path.join(base_path, bundled_filename)
    if os.path.exists(bundled_path_root):
        return bundled_path_root

    # Fallback to system path
    # Use the original name (e.g. "ffmpeg") to search in PATH
    system_path = shutil.which(name)
    if system_path:
        return system_path

    return name

def format_timestamp(ms):
    """Format milliseconds to HH:MM:SS.mmm"""
    seconds = (ms // 1000) % 60
    minutes = (ms // 60000) % 60
    hours = (ms // 3600000)
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

def format_timestamp_for_filename(ms):
    """Format milliseconds to HH.MM.SS.mmm for filenames"""
    seconds = (ms // 1000) % 60
    minutes = (ms // 60000) % 60
    hours = (ms // 3600000)
    milliseconds = ms % 1000
    return f"{hours:02}.{minutes:02}.{seconds:02}.{milliseconds:03}"

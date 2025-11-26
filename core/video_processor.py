import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal
from .utils import get_executable_path

class KeyframeThread(QThread):
    keyframes_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path, start_time=None, end_time=None):
        super().__init__()
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time

    def run(self):
        try:
            ffprobe_cmd = get_executable_path("ffprobe")
            cmd = [
                ffprobe_cmd, 
                "-v", "error", 
                "-select_streams", "v:0", 
                "-skip_frame", "nokey", 
                "-show_entries", "frame=pkt_pts_time", 
                "-of", "csv=p=0"
            ]

            if self.start_time is not None and self.end_time is not None:
                cmd.extend(["-read_intervals", f"{self.start_time}%{self.end_time}"])

            cmd.append(self.file_path)
            
            # Hide console on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # FIX: Use encoding='utf-8' and errors='replace' to handle potential UnicodeDecodeError
            # when reading output that might contain non-standard characters or when system encoding differs.
            # FFmpeg/FFprobe usually output UTF-8.
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo, 
                check=True
            )
            timestamps = [float(line.strip()) for line in result.stdout.splitlines() if line.strip()]
            self.keyframes_loaded.emit(sorted(timestamps))
        except Exception as e:
            self.error_occurred.emit(str(e))

class ExportThread(QThread):
    export_finished = pyqtSignal(str)
    export_error = pyqtSignal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            # Hide console on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # FIX: Use encoding='utf-8' and errors='replace'
            subprocess.run(
                self.cmd, 
                check=True, 
                startupinfo=startupinfo, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self.export_finished.emit("Export Complete")
        except subprocess.CalledProcessError as e:
            self.export_error.emit(f"FFmpeg failed:\n{e.stderr if e.stderr else str(e)}")
        except Exception as e:
            self.export_error.emit(f"An error occurred:\n{str(e)}")

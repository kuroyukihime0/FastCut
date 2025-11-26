import os
import sys
import json
import subprocess
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QComboBox, QStyle, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QIcon, QAction, QDragEnterEvent, QDropEvent
from PyQt6.QtMultimedia import QMediaPlayer

from core.utils import resource_path, get_executable_path, format_timestamp
from core.video_processor import KeyframeThread, ExportThread
from ui.video_player import VideoPlayerWidget
from ui.widgets import RangeSlider

class FastCutApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastCut - Simple Video Clipper")
        self.setWindowIcon(QIcon(resource_path("assets/logo.png")))
        self.resize(1000, 700)
        self.setAcceptDrops(True)

        # State
        self.current_file = None
        self.duration = 0
        self.start_time = 0
        self.end_time = 0
        self.is_playing = False
        # Determine a persistent configuration directory (e.g., %APPDATA%/FastCut)
        self.config_dir = os.path.join(os.getenv('APPDATA', ''), 'FastCut')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.export_dir = ""
        self.playback_speed = "1.0x"
        self.use_keyframe_cut = True  # Default to enabled
        self.is_previewing = False  # Track if we're in preview mode

        # Load Config
        self.load_config()

        # UI Setup
        self.init_ui()
        self.apply_styles()

        # Timer for updating progress
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui_tick)
        self.timer.start()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.export_dir = config.get("export_dir", "")
                    self.playback_speed = config.get("playback_speed", "1.0x")
                    self.use_keyframe_cut = config.get("use_keyframe_cut", True)
        except Exception as e:
            print(f"Failed to load config: {e}")

    def save_config(self):
        try:
            config = {
                "export_dir": self.export_dir,
                "playback_speed": self.playback_speed,
                "use_keyframe_cut": self.use_keyframe_cut
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Video Player
        self.video_player = VideoPlayerWidget()
        self.video_player.media_player.positionChanged.connect(self.on_position_changed)
        self.video_player.media_player.durationChanged.connect(self.on_duration_changed)
        self.video_player.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.video_player.file_dropped.connect(self.load_file)
        self.video_player.double_clicked.connect(self.toggle_play)
        main_layout.addWidget(self.video_player, stretch=1)

        # Controls Area
        controls_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)

        # Timeline / Slider
        self.seek_slider = RangeSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self.set_position)
        self.seek_slider.sliderPressed.connect(self.on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self.on_slider_released)
        self.seek_slider.rangeChanged.connect(self.on_range_changed)
        controls_layout.addWidget(self.seek_slider)

        # Time Labels & Range Controls
        time_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("00:00:00")
        self.current_time_label.setObjectName("timeLabel")
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setObjectName("timeLabel")
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        
        # Range Buttons
        self.btn_set_start = QPushButton("Set Start [C]")
        self.btn_set_start.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_set_start.clicked.connect(self.set_start_mark)
        self.btn_set_end = QPushButton("Set End [V]")
        self.btn_set_end.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_set_end.clicked.connect(self.set_end_mark)
        
        time_layout.addWidget(self.btn_set_start)
        time_layout.addWidget(self.btn_set_end)
        
        # Preview Button
        self.btn_preview = QPushButton("Preview")
        self.btn_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_preview.clicked.connect(self.preview_range)
        time_layout.addWidget(self.btn_preview)
        
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        
        controls_layout.addLayout(time_layout)

        # Menu Bar
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        
        action_select_dir = QAction("Select Export Folder...", self)
        action_select_dir.triggered.connect(self.select_export_dir)
        settings_menu.addAction(action_select_dir)
        
        action_clear_dir = QAction("Reset to Source Folder", self)
        action_clear_dir.triggered.connect(self.clear_export_dir)
        settings_menu.addAction(action_clear_dir)
        
        settings_menu.addSeparator()
        
        self.action_keyframe_cut = QAction("Smart Cut (Keyframe Aligned)", self)
        self.action_keyframe_cut.setCheckable(True)
        self.action_keyframe_cut.setChecked(self.use_keyframe_cut)
        self.action_keyframe_cut.triggered.connect(self.toggle_keyframe_cut)
        settings_menu.addAction(self.action_keyframe_cut)

        help_menu = menubar.addMenu("Help")
        action_about = QAction("About", self)
        action_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(action_about)

        # Playback Controls
        action_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("Open File")
        self.btn_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_open.clicked.connect(self.open_file_dialog)
        
        self.btn_play = QPushButton()
        self.btn_play.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.update_play_button_icon(False)
        self.btn_play.clicked.connect(self.toggle_play)
        
        # Speed controls
        self.btn_speed_down = QPushButton("-")
        self.btn_speed_down.setObjectName("speedBtn")
        self.btn_speed_down.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.btn_speed_down.setFixedSize(25, 25)
        self.btn_speed_down.clicked.connect(self.decrease_speed)
        
        self.speed_combo = QComboBox()
        self.speed_combo.setEditable(True)  # Allow custom speeds to be displayed
        self.speed_combo.lineEdit().setReadOnly(True)  # But don't allow manual editing
        self.speed_combo.setMinimumWidth(70)  # Ensure enough width for "0.00x" format
        self.speed_combo.addItems(["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x", "2.5x", "3.0x"])
        self.speed_combo.setCurrentText(self.playback_speed)
        self.speed_combo.currentTextChanged.connect(self.change_speed)
        
        self.btn_speed_up = QPushButton("+")
        self.btn_speed_up.setObjectName("speedBtn")
        self.btn_speed_up.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.btn_speed_up.setFixedSize(25, 25)
        self.btn_speed_up.clicked.connect(self.increase_speed)
        
        self.btn_export = QPushButton("Export Clip")
        self.btn_export.setObjectName("exportBtn")
        self.btn_export.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_export.clicked.connect(self.export_clip)

        action_layout.addWidget(self.btn_open)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_play)
        action_layout.addWidget(self.btn_speed_down)
        action_layout.addWidget(self.speed_combo)
        action_layout.addWidget(self.btn_speed_up)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_export)
        
        controls_layout.addLayout(action_layout)

        # Status Bar
        self.lbl_export_dir = QLabel(f"Output: {self.export_dir if self.export_dir else 'Source Folder'}")
        self.lbl_export_dir.setStyleSheet("color: #888; font-size: 12px; margin-right: 10px;")
        self.statusBar().addPermanentWidget(self.lbl_export_dir)
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage("Ready. Drag and drop a video file here.")

    def apply_styles(self):
        try:
            styles_file = resource_path("styles.qss")
            with open(styles_file, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"styles.qss not found at {styles_file}")

    def keyPressEvent(self, event):
        # Handle keyboard shortcuts
        if event.key() == Qt.Key.Key_C:
            self.set_start_mark()
        elif event.key() == Qt.Key.Key_V:
            self.set_end_mark()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_play()
        else:
            super().keyPressEvent(event)

    # --- Logic ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_file(files[0])

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.mkv *.avi *.mov)")
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        self.current_file = file_path
        self.video_player.load_video(file_path)
        self.btn_play.setEnabled(True)
        self.setWindowTitle(f"FastCut - {os.path.basename(file_path)}")
        self.statusBar().showMessage(f"Loaded: {file_path}")
        
        # Reset range
        self.start_time = 0
        self.end_time = 0
        self.seek_slider.set_range_pos(0, 0, 0)
        
        # Restore speed
        self.change_speed(self.playback_speed)

        # Auto play
        self.video_player.play()

    def toggle_play(self):
        if self.is_playing:
            self.video_player.pause()
        else:
            self.video_player.play()

    def on_playback_state_changed(self, state):
        self.is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self.update_play_button_icon(self.is_playing)

    def update_play_button_icon(self, is_playing):
        if is_playing:
            self.btn_play.setText("Pause")
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.btn_play.setText("Play")
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def on_duration_changed(self, duration):
        self.duration = duration
        self.seek_slider.setRange(0, duration)
        self.end_time = duration # Default end time is full duration
        self.seek_slider.set_range_pos(self.start_time, self.end_time, self.duration)
        self.duration_label.setText(format_timestamp(duration))

    def on_position_changed(self, position):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.current_time_label.setText(format_timestamp(position))
        
        # Stop playback at end point during preview
        if self.is_previewing and position >= self.end_time:
            self.video_player.pause()
            self.is_previewing = False

    def set_position(self, position):
        self.video_player.set_position(position)

    def on_slider_pressed(self):
        self.was_playing_before_drag = self.is_playing
        self.video_player.pause()

    def on_slider_released(self):
        if self.was_playing_before_drag:
            self.video_player.play()
        self.set_position(self.seek_slider.value())

    def change_speed(self, text):
        speed = float(text.replace("x", ""))
        self.video_player.media_player.setPlaybackRate(speed)
        self.playback_speed = text
        self.save_config()

    def decrease_speed(self):
        """Decrease playback speed by 0.2x"""
        current_speed = float(self.playback_speed.replace("x", ""))
        new_speed = max(0.25, round(current_speed - 0.2, 2))  # Minimum 0.25x
        new_speed_str = f"{new_speed:.2f}x"
        
        # Block signals to prevent triggering change_speed
        self.speed_combo.blockSignals(True)
        
        # Find if this speed exists in the combo box
        index = self.speed_combo.findText(new_speed_str)
        if index >= 0:
            self.speed_combo.setCurrentIndex(index)
        else:
            # For custom speeds, just update the current text
            self.speed_combo.setCurrentText(new_speed_str)
        
        self.speed_combo.blockSignals(False)
        
        # Apply the speed change
        self.playback_speed = new_speed_str
        self.video_player.media_player.setPlaybackRate(new_speed)
        self.save_config()

    def increase_speed(self):
        """Increase playback speed by 0.2x"""
        current_speed = float(self.playback_speed.replace("x", ""))
        new_speed = min(3.0, round(current_speed + 0.2, 2))  # Maximum 3.0x
        new_speed_str = f"{new_speed:.2f}x"
        
        # Block signals to prevent triggering change_speed
        self.speed_combo.blockSignals(True)
        
        # Find if this speed exists in the combo box
        index = self.speed_combo.findText(new_speed_str)
        if index >= 0:
            self.speed_combo.setCurrentIndex(index)
        else:
            # For custom speeds, just update the current text
            self.speed_combo.setCurrentText(new_speed_str)
        
        self.speed_combo.blockSignals(False)
        
        # Apply the speed change
        self.playback_speed = new_speed_str
        self.video_player.media_player.setPlaybackRate(new_speed)
        self.save_config()

    def set_start_mark(self):
        self.start_time = self.video_player.get_position()
        if self.start_time > self.end_time:
            self.end_time = self.duration
        self.update_range_ui()
        self.statusBar().showMessage(f"Start point set to {format_timestamp(self.start_time)}")

    def set_end_mark(self):
        self.end_time = self.video_player.get_position()
        if self.end_time < self.start_time:
            self.start_time = 0
        self.update_range_ui()
        self.statusBar().showMessage(f"End point set to {format_timestamp(self.end_time)}")

    def preview_range(self):
        """Preview the selected range from start to end point"""
        if self.end_time <= self.start_time:
            QMessageBox.warning(self, "Invalid Range", "Please set valid start and end points first.")
            return
        
        # Seek to start position
        self.video_player.set_position(int(self.start_time))
        # Start playing
        self.video_player.play()
        # Set preview flag
        self.is_previewing = True
        self.statusBar().showMessage(f"Previewing from {format_timestamp(self.start_time)} to {format_timestamp(self.end_time)}")

    def update_range_ui(self):
        self.seek_slider.set_range_pos(self.start_time, self.end_time, self.duration)

    def on_range_changed(self, start, end):
        # Determine which handle was dragged by comparing with previous values
        start_changed = (start != self.start_time)
        end_changed = (end != self.end_time)
        
        self.start_time = start
        self.end_time = end
        
        # Seek to the position of the handle being dragged
        if start_changed and not end_changed:
            # Start handle was dragged, seek to start position
            self.video_player.set_position(int(start))
        elif end_changed and not start_changed:
            # End handle was dragged, seek to end position
            self.video_player.set_position(int(end))

    def update_ui_tick(self):
        # Can be used for smoother UI updates if needed
        pass

    def select_export_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder:
            self.export_dir = folder
            self.lbl_export_dir.setText(f"Output: {self.export_dir}")
            self.statusBar().showMessage(f"Export directory set to: {self.export_dir}")
            self.save_config()

    def clear_export_dir(self):
        self.export_dir = ""
        self.lbl_export_dir.setText("Output: Source Folder")
        self.save_config()
        self.statusBar().showMessage("Export directory reset to source folder.")

    def toggle_keyframe_cut(self):
        self.use_keyframe_cut = self.action_keyframe_cut.isChecked()
        self.save_config()
        status = "enabled" if self.use_keyframe_cut else "disabled"
        self.statusBar().showMessage(f"Smart Cut (Keyframe Aligned): {status}")

    def start_keyframe_analysis(self, file_path, start_time, end_time):
        self.progress_dialog = QProgressDialog("Analyzing keyframes...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.keyframe_thread = KeyframeThread(file_path, start_time, end_time)
        self.keyframe_thread.keyframes_loaded.connect(self.on_keyframes_loaded)
        self.keyframe_thread.error_occurred.connect(self.on_keyframe_error)
        self.keyframe_thread.finished.connect(self.progress_dialog.close)
        self.keyframe_thread.start()

    def on_keyframes_loaded(self, keyframes):
        # Continue export process with loaded keyframes
        self.continue_export_with_keyframes(keyframes)

    def on_keyframe_error(self, error_msg):
        print(f"Error getting keyframes: {error_msg}")
        # Fallback to no keyframes or show error? 
        # For now, let's just proceed without keyframe alignment if it fails, or maybe just warn.
        # But to be safe, let's proceed with empty keyframes so export continues.
        self.continue_export_with_keyframes([])

    def export_clip(self):
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please load a video file first.")
            return

        self.export_start_sec = self.start_time / 1000.0
        self.export_end_sec = self.end_time / 1000.0
        
        if self.export_end_sec <= self.export_start_sec:
             QMessageBox.warning(self, "Invalid Range", "End time must be greater than start time.")
             return

        # Ensure video is paused before exporting
        if self.video_player.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.video_player.media_player.pause()
        
        # Only do keyframe alignment if enabled
        if self.use_keyframe_cut:
            # Optimize: Only scan 5 seconds before start point + 5 seconds after
            lookback = 5.0
            search_start = max(0.0, self.export_start_sec - lookback)
            search_end = self.export_start_sec + 5.0
            
            self.start_keyframe_analysis(self.current_file, search_start, search_end)
        else:
            self.continue_export_with_keyframes([])

    def continue_export_with_keyframes(self, keyframes):
        real_start = self.export_start_sec
        real_end = self.export_end_sec

        if self.use_keyframe_cut and keyframes:
            # Find keyframe before or at start_sec
            prev_kf = 0.0
            for kf in keyframes:
                if kf <= self.export_start_sec:
                    prev_kf = kf
                else:
                    break
            real_start = prev_kf
            # Keep end point exact
            real_end = self.export_end_sec
            print(f"Adjusted start: {self.export_start_sec} -> {real_start}, end unchanged: {self.export_end_sec}")

        duration_sec = real_end - real_start

        # Generate output filename
        folder = self.export_dir if self.export_dir else os.path.dirname(self.current_file)
        filename = os.path.basename(self.current_file)
        name, ext = os.path.splitext(filename)
        
        def format_timestamp_for_filename(ms):
            seconds = (ms // 1000) % 60
            minutes = (ms // 60000) % 60
            hours = (ms // 3600000)
            milliseconds = ms % 1000
            return f"{hours:02}.{minutes:02}.{seconds:02}.{milliseconds:03}"

        start_str = format_timestamp_for_filename(int(real_start * 1000))
        end_str = format_timestamp_for_filename(int(real_end * 1000))
        
        output_file = os.path.join(folder, f"{name}-{start_str}-{end_str}{ext}")
        self.current_output_file = output_file # Store for "Open Folder"

        ffmpeg_cmd = get_executable_path("ffmpeg")
        if self.use_keyframe_cut:
            cmd = [
                ffmpeg_cmd, "-y",
                "-i", self.current_file,
                "-ss", str(real_start),
                "-t", str(duration_sec),
                "-map", "0:v:0",
                "-map", "0:a:0",
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                "-async", "1",
                "-shortest",
                output_file
            ]
        else:
            cmd = [
                ffmpeg_cmd, "-y",
                "-ss", str(real_start),
                "-i", self.current_file,
                "-t", str(duration_sec),
                "-map", "0:v:0",
                "-map", "0:a:0",
                "-c", "copy",
                "-async", "1",
                "-shortest",
                output_file
            ]

        self.progress_dialog = QProgressDialog("Exporting clip, please wait...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.export_thread = ExportThread(cmd)
        self.export_thread.export_finished.connect(self.on_export_finished)
        self.export_thread.export_error.connect(self.on_export_error)
        # self.export_thread.finished.connect(self.progress_dialog.close) # Close manually in handlers to ensure dialog stays if error
        self.export_thread.start()

    def on_export_finished(self, message):
        self.progress_dialog.close()
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(f"Clip exported to:\n{self.current_output_file}")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        open_folder_btn = msg_box.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
        msg_box.exec()
        
        if msg_box.clickedButton() == open_folder_btn:
            folder = os.path.dirname(self.current_output_file)
            if os.name == 'nt':
                os.startfile(folder)
            elif os.name == 'posix':
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', folder])
        
        self.statusBar().showMessage("Export Complete.")

    def on_export_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error", error_msg)
        self.statusBar().showMessage("Export Failed.")

    def get_ffmpeg_version(self):
        try:
            ffmpeg_cmd = get_executable_path("ffmpeg")
            # Hide console on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run([ffmpeg_cmd, "-version"], capture_output=True, text=True, startupinfo=startupinfo, check=True)
            # First line usually contains version info
            return result.stdout.splitlines()[0]
        except Exception as e:
            return f"Error detecting FFmpeg: {e}"

    def get_ffprobe_version(self):
        try:
            ffprobe_cmd = get_executable_path("ffprobe")
            # Hide console on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run([ffprobe_cmd, "-version"], capture_output=True, text=True, startupinfo=startupinfo, check=True)
            # First line usually contains version info
            return result.stdout.splitlines()[0]
        except Exception as e:
            return f"Error detecting FFprobe: {e}"

    def show_about_dialog(self):
        version = "1.0.0"
        ffmpeg_version = self.get_ffmpeg_version()
        ffmpeg_path = get_executable_path("ffmpeg")
        ffprobe_version = self.get_ffprobe_version()
        ffprobe_path = get_executable_path("ffprobe")
        
        QMessageBox.about(self, "About FastCut",
            f"FastCut v{version}\n\n"
            f"A simple video clipping tool.\n\n"
            f"FFmpeg Path: {ffmpeg_path}\n"
            f"FFmpeg Version: {ffmpeg_version}\n\n"
            f"FFprobe Path: {ffprobe_path}\n"
            f"FFprobe Version: {ffprobe_version}"
        )

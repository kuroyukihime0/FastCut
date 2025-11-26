from PyQt6.QtWidgets import (QWidget, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class DragDropOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # Transparent background
        self.setStyleSheet("background-color: transparent;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            # Find the VideoPlayerWidget parent and emit its signal
            parent = self.parent()
            while parent:
                if isinstance(parent, VideoPlayerWidget):
                    parent.file_dropped.emit(files[0])
                    break
                parent = parent.parent()

    def mouseDoubleClickEvent(self, event):
        parent = self.parent()
        while parent:
            if isinstance(parent, VideoPlayerWidget):
                parent.double_clicked.emit()
                break
            parent = parent.parent()

class VideoPlayerWidget(QWidget):
    """
    A widget that contains the video output and basic controls.
    """
    file_dropped = pyqtSignal(str)
    double_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAcceptDrops(True)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)
        
        # Set black background for video area
        self.video_widget.setStyleSheet("background-color: black;")

        # Overlay for drag and drop
        self.overlay = DragDropOverlay(self)
        self.overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_dropped.emit(files[0])

    def load_video(self, file_path):
        self.media_player.setSource(QUrl.fromLocalFile(file_path))

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def stop(self):
        self.media_player.stop()
        
    def set_position(self, position):
        self.media_player.setPosition(position)
        
    def get_duration(self):
        return self.media_player.duration()
        
    def get_position(self):
        return self.media_player.position()

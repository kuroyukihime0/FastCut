from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QSlider, QLabel, QStyle, QSizePolicy, QFileDialog, QStyleOptionSlider, QToolTip)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTime, QEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QDragEnterEvent, QDropEvent

class RangeSlider(QSlider):
    rangeChanged = pyqtSignal(int, int) # start, end

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.start_pos = 0
        self.end_pos = 0
        self.duration = 0
        self.setMouseTracking(True)
        self.setMinimumHeight(40) # Ensure space for labels
        
        # Style for the range
        self.range_color = QColor(60, 180, 75, 100)  # Semi-transparent Green
        self.range_border = QColor(60, 180, 75)
        
        # Handle properties
        self.handle_radius = 6
        self.dragging_handle = None # 'start' or 'end' or None

    def set_range_pos(self, start, end, duration):
        self.start_pos = start
        self.end_pos = end
        self.duration = duration
        self.update()

    def mousePressEvent(self, event):
        if self.duration <= 0:
            super().mousePressEvent(event)
            return

        x = event.pos().x()
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
        width = groove_rect.width()
        if width <= 0:
            super().mousePressEvent(event)
            return

        scale = width / self.duration
        x_start = groove_rect.x() + (self.start_pos * scale)
        x_end = groove_rect.x() + (self.end_pos * scale)

        # Check if clicking near handles
        if abs(x - x_start) <= self.handle_radius + 2:
            self.dragging_handle = 'start'
        elif abs(x - x_end) <= self.handle_radius + 2:
            self.dragging_handle = 'end'
        else:
            # Click to seek: calculate position and emit signal
            click_pos = (x - groove_rect.x()) / scale
            click_pos = max(0, min(self.duration, click_pos))
            self.setValue(int(click_pos))
            self.sliderMoved.emit(int(click_pos))
            # Also call parent to ensure proper event handling
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging_handle:
            self.dragging_handle = None
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging_handle:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove_rect = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
            width = groove_rect.width()
            if width > 0:
                scale = width / self.duration
                new_pos = (event.pos().x() - groove_rect.x()) / scale
                new_pos = max(0, min(self.duration, new_pos))

                if self.dragging_handle == 'start':
                    self.start_pos = min(new_pos, self.end_pos)
                elif self.dragging_handle == 'end':
                    self.end_pos = max(new_pos, self.start_pos)
                
                self.rangeChanged.emit(int(self.start_pos), int(self.end_pos))
                self.update()
                
                # Show tooltip for handle
                seconds = (new_pos // 1000) % 60
                minutes = (new_pos // 60000) % 60
                hours = (new_pos // 3600000)
                milliseconds = new_pos % 1000
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
                QToolTip.showText(event.globalPosition().toPoint(), time_str, self)
                return

        super().mouseMoveEvent(event)
        if self.duration > 0:
            val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width())
            
            # Format time
            seconds = (val // 1000) % 60
            minutes = (val // 60000) % 60
            hours = (val // 3600000)
            milliseconds = val % 1000
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
            
            QToolTip.showText(event.globalPosition().toPoint(), time_str, self)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.duration <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate geometry of the groove (approximate, depending on style)
        # We'll draw over the groove
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
        
        # Calculate pixels per unit
        width = groove_rect.width()
        if width <= 0:
            return
            
        scale = width / self.duration
        
        x_start = groove_rect.x() + (self.start_pos * scale)
        x_end = groove_rect.x() + (self.end_pos * scale)
        rect_width = x_end - x_start
        
        # Draw the selection range
        selection_rect = groove_rect
        selection_rect.setX(int(x_start))
        selection_rect.setWidth(int(rect_width))
        
        painter.setBrush(QBrush(self.range_color))
        painter.setPen(QPen(self.range_border, 1))
        painter.drawRect(selection_rect)

        # Draw handles (red dots)
        painter.setBrush(QBrush(Qt.GlobalColor.red))
        painter.setPen(QPen(Qt.GlobalColor.darkRed, 2))
        
        center_start = groove_rect.topLeft()
        center_start.setX(int(x_start))
        center_start.setY(groove_rect.center().y())
        
        center_end = groove_rect.topLeft()
        center_end.setX(int(x_end))
        center_end.setY(groove_rect.center().y())

        painter.drawEllipse(center_start, self.handle_radius, self.handle_radius)
        painter.drawEllipse(center_end, self.handle_radius, self.handle_radius)

        # Draw time labels above handles
        painter.setPen(QPen(Qt.GlobalColor.white))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        def format_ms(ms):
            seconds = (ms // 1000) % 60
            minutes = (ms // 60000) % 60
            hours = (ms // 3600000)
            milliseconds = ms % 1000
            return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

        start_str = format_ms(int(self.start_pos))
        end_str = format_ms(int(self.end_pos))

        # Adjust text position
        text_rect_start = painter.fontMetrics().boundingRect(start_str)
        text_rect_end = painter.fontMetrics().boundingRect(end_str)
        
        # Draw start label
        pos_start_x = int(x_start) - text_rect_start.width() // 2
        pos_start_y = groove_rect.top() - 5
        painter.drawText(pos_start_x, pos_start_y, start_str)

        # Draw end label
        pos_end_x = int(x_end) - text_rect_end.width() // 2
        pos_end_y = groove_rect.top() - 5
        # Prevent overlap if handles are close
        if abs(x_end - x_start) < (text_rect_start.width() + text_rect_end.width()) / 2 + 5:
             # If close, maybe shift one up or down? Or just let them overlap for now/simple logic
             # Let's shift end label down if they overlap? No, slider is small.
             # Let's just draw it.
             pass
        
        painter.drawText(pos_end_x, pos_end_y, end_str)

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
        # self.media_player.play() # Auto play or wait? Let's wait.
        # self.media_player.pause()

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
